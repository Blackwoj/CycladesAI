"""LLM-based agents — interfejs niezależny od dostawcy.

Hierarchia klas:
  BaseLLMAgent          — logika wspólna (tryby, ponawianie, metryki, renderowanie stanu)
  ├── AnthropicLLMAgent — Anthropic SDK (claude-*)
  ├── OpenAILLMAgent    — OpenAI SDK z konfigurowalne base_url
  │     Pokrywa też: GPT (openai.com), Qwen (dashscope), MiniMax, każde OpenAI-API-compatible
  ├── OllamaLLMAgent    — lokalny LLaMA / Mistral przez Ollama (OpenAI-compatible localhost)
  └── GeminiLLMAgent    — Google Generative AI SDK (gemini-*)

Tryby eksperymentalne:
  GUIDED    — lista legalnych akcji w prompcie; LLM wybiera indeks.
              Mierzy strategię, nie gramatykę.
  FREE_FORM — LLM proponuje akcję bez listy; walidacja po fakcie.
              Mierzy zdolność generowania poprawnych akcji z opisu zasad.
"""
from __future__ import annotations

import os
import time
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..actions import Action, action_from_dict
from ..rng import Rng
from .base import Agent

try:
    from .llm_schemas import action_from_llm_output, guided_choice_from_llm_output, json_schema_for_hero
    _SCHEMAS_AVAILABLE = True
except ImportError:
    _SCHEMAS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Typy wspólne
# ---------------------------------------------------------------------------

class LLMMode(Enum):
    GUIDED = "guided"
    FREE_FORM = "free_form"


@dataclass
class LLMStats:
    """Metryki zbierane podczas działania (do analizy w pracy mgr)."""
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_illegal: int = 0
    total_fallback: int = 0
    total_decision_ms: float = 0.0

    def record(self, input_tokens: int, output_tokens: int, decision_ms: float) -> None:
        self.total_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_decision_ms += decision_ms

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_illegal": self.total_illegal,
            "total_fallback": self.total_fallback,
            "avg_decision_ms": round(self.total_decision_ms / max(1, self.total_calls), 1),
        }


# ---------------------------------------------------------------------------
# Baza — logika wspólna
# ---------------------------------------------------------------------------

class BaseLLMAgent(Agent):
    """Logika wspólna dla wszystkich agentów LLM.

    Podklasy muszą zaimplementować:
      _call_guided(prompt, num_actions)  -> (idx, input_tok, output_tok)
      _call_free_form(prompt)            -> (raw_dict_or_None, input_tok, output_tok)
    """

    _SYSTEM_PROMPT = """You are an AI player in Cyclades — a 2–5 player strategy board game set in ancient Greece.

═══════════════════════════════════════════════════════
GOAL
═══════════════════════════════════════════════════════
Own the required number of METROPOLISES at the END of a cycle
(2 metropolises; 3 in a 2-player game — see "metros_to_win").
If several players qualify in the same cycle, the richest one (most gold) wins.

═══════════════════════════════════════════════════════
CYCLE
═══════════════════════════════════════════════════════
1. Creature track is refreshed (3 slots costing 4 / 3 / 2 gold).
2. Gods are shuffled into rows; income is paid (1 gold per prosperity marker
   on your islands, trade arrows on your sea tiles and Apollo markers).
3. ROLL — offerings: every marker goes to one god. Outbidding requires a higher
   offer; the outbid player must IMMEDIATELY bid on a DIFFERENT god. Apollo is
   free and holds many players. Cost = offer − your priests (min 1 gold per
   offering); total offerings must be affordable. In a 2-player game each player
   has TWO markers and must offer to two different gods (3 gods + Apollo).
4. BOARD — gods act in row order (row_1 first), Apollo last. Whoever finished
   last bids first in the next cycle.

═══════════════════════════════════════════════════════
GODS (any number of actions, in any order, while you can pay)
═══════════════════════════════════════════════════════
- ARES: recruit troops on your islands (1st free, then 2/3/4 gold, max 4 per
  turn, max 8 on board); move some/all troops from one island to another island
  connected by a CHAIN OF YOUR FLEETS (1 gold); build a FORTRESS (2 gold).
- POSEIDON: recruit fleets on sea next to your islands, empty or your own
  (1st free, then 1/2/3 gold, max 4 per turn, max 8); move fleets from one sea
  tile up to 3 tiles (1 gold, stops on enemy fleets); build a PORT (2 gold).
- ZEUS: 1 free priest (+1 more for 4 gold); build a TEMPLE (2 gold);
  replace a creature on the track with the top card (1 gold).
- ATHENA: 1 free philosopher (+1 more for 4 gold); build a UNIVERSITY (2 gold).
- APOLLO: +1 gold (+4 if you own ≤ 1 island). The FIRST player on Apollo also
  places a +1 prosperity marker on one of their islands (place_income).
  No other actions.
Every god except Apollo may also SUMMON CREATURES from the track (buy_creature).

═══════════════════════════════════════════════════════
BATTLES
═══════════════════════════════════════════════════════
Each round both sides add units (+ die roll if dice are on). Defender adds +1
per fortress on the island (sea: +1 per port on adjacent defender islands;
a metropolis counts as both). Lower total loses 1 unit; a tie costs both sides
1 unit. Repeat until one side is gone. Landing on an enemy island WITHOUT
troops captures it without a fight. You may NOT attack a player's LAST island
unless capturing it wins you the game. Captured islands keep their buildings.

═══════════════════════════════════════════════════════
METROPOLISES (mandatory and immediate)
═══════════════════════════════════════════════════════
- 4th philosopher → discard 4 and place a metropolis on one of your islands.
- One building of each type (fortress, port, temple, university) on your
  islands → they are removed and replaced by a metropolis.
- Or conquer an island that has a metropolis.
When this happens the ONLY legal actions are "build" with hero="metro" — pick
the island. A metropolis has the powers of every building.

═══════════════════════════════════════════════════════
CREATURES (resolve immediately; pick targets with play_card)
═══════════════════════════════════════════════════════
Each temple/metropolis lowers one creature cost by 1 per cycle (min 1 gold).
- Harpy: kill 1 enemy troop. - Pegasus: fly troops from your island to any
  island without fleets (can invade). - Giant: destroy a building (not a
  metropolis). - Siren: replace an isolated enemy fleet with yours.
- Sylph: move your fleets 10 steps in total. - Griffin: take half of a player's
  gold. - Satyr: steal a philosopher. - Dryad: steal a priest.
- Moirai: collect your income again. - Sphinx: sell your units/priests/
  philosophers for 2 gold each. - Cyclopes: swap one of your buildings to
  another type. - Chimera: use the power of a discarded creature.
- Kraken: destroy all fleets on a sea tile (+1 gold per extra tile moved);
  the tile stays blocked for fleets.
- Figures, active until the start of your next turn: Minotaur (+2 defence on
  the island), Chiron (island immune to Pegasus/Harpy/Giant), Medusa (troops
  on the island cannot move), Polyphemus (pushes fleets away from the island).
Use targets=["done"] to finish a creature effect.

═══════════════════════════════════════════════════════
STRATEGIC PRINCIPLES
═══════════════════════════════════════════════════════
- Win the god you need; a lost auction is a wasted cycle.
- Ares/Poseidon expand territory; Zeus/Athena lead to metropolises.
- Apollo is a cheap pass that compounds income.
- Buildings of all four types = a free metropolis — plan them across cycles.
- Protect your islands with fortresses before rivals bring Ares.
- EndTurn is always legal and sometimes optimal (save gold for offerings).
"""

    def __init__(
        self,
        mode: LLMMode = LLMMode.GUIDED,
        max_retries: int = 2,
        fallback_rng: Rng | None = None,
        verbose: bool = False,
    ) -> None:
        self.mode = mode
        self.max_retries = max_retries
        self._fallback_rng = fallback_rng
        self.verbose = verbose
        self.stats = LLMStats()
        # Szczegóły OSTATNIEJ decyzji — czyta je telemetria eksperymentu.
        # Agregaty w self.stats nie wystarczają do wykresów, bo gubią
        # rozkład w czasie (koszt decyzji rośnie wraz z rozmiarem stanu).
        self.last_decision: dict = {}
        self._call_illegal = 0
        self._call_fallback = False
        self._call_reasoning = ""

    # ------------------------------------------------------------------ #
    #   Abstrakcyjny interfejs API — do implementacji w podklasach
    # ------------------------------------------------------------------ #

    @abstractmethod
    def _call_guided(
        self, prompt: str, num_actions: int
    ) -> tuple[int, int, int]:
        """Wywołaj API i zwróć (wybrany_indeks, input_tokens, output_tokens)."""
        ...

    @abstractmethod
    def _call_free_form(
        self, prompt: str, hero: str = "", stage: str = "board"
    ) -> tuple[dict | None, int, int]:
        """Wywołaj API i zwróć (raw_action_dict_or_None, input_tokens, output_tokens).

        hero i stage są opcjonalne — podklasy używają ich do budowania
        węższego (bardziej precyzyjnego) schematu narzędzia per-bóg.
        """
        ...

    # ------------------------------------------------------------------ #
    #   Główna metoda — Agent.choose()
    # ------------------------------------------------------------------ #

    def choose(self, state_view: dict, legal_actions: list[Action]) -> Action:
        if not legal_actions:
            raise ValueError(f"{self.__class__.__name__}.choose: brak legalnych akcji")

        t0 = time.monotonic()
        self._call_illegal = 0
        self._call_fallback = False
        self._call_reasoning = ""

        if self.mode == LLMMode.GUIDED:
            action, input_tok, output_tok = self._run_guided(state_view, legal_actions)
        else:
            action, input_tok, output_tok = self._run_free_form(state_view, legal_actions)

        elapsed_ms = (time.monotonic() - t0) * 1000
        self.stats.record(input_tok, output_tok, elapsed_ms)

        self.last_decision = {
            "model": getattr(self, "model", ""),
            "mode": self.mode.value,
            "input_tokens": input_tok,
            "output_tokens": output_tok,
            "illegal_attempts": self._call_illegal,
            "fallback_used": self._call_fallback,
            "n_legal": len(legal_actions),
            "decision_ms": elapsed_ms,
            "reasoning": self._call_reasoning,
        }

        if self.verbose:
            print(
                f"[{self.__class__.__name__}/{self.mode.value}] action={action} "
                f"tok={input_tok}+{output_tok} time={elapsed_ms:.0f}ms"
            )
        return action

    def _run_guided(
        self, state_view: dict, legal_actions: list[Action]
    ) -> tuple[Action, int, int]:
        prompt = _render_guided(state_view, legal_actions)
        idx, inp, out = self._call_guided(prompt, len(legal_actions))
        idx = max(0, min(idx, len(legal_actions) - 1))
        return legal_actions[idx], inp, out

    def _run_free_form(
        self, state_view: dict, legal_actions: list[Action]
    ) -> tuple[Action, int, int]:
        prompt = _render_free_form(state_view)
        player = state_view.get("me", "")
        hero = state_view.get("act_hero", "") or ""
        stage = state_view.get("stage", "board") or "board"

        total_inp = 0
        total_out = 0

        for attempt in range(self.max_retries + 1):
            raw, inp, out = self._call_free_form(prompt, hero=hero, stage=stage)
            total_inp += inp
            total_out += out

            if raw is None:
                self.stats.total_illegal += 1
                self._call_illegal += 1
                continue

            # Walidacja: najpierw przez Pydantic schema (preferowane), potem fuzzy match
            matched = self._validate_action(raw, player, hero, stage, legal_actions)
            if matched is not None:
                return matched, total_inp, total_out

            self.stats.total_illegal += 1
            self._call_illegal += 1
            if self.verbose:
                print(f"[{self.__class__.__name__}/free_form] attempt {attempt}: illegal {raw}")

        self.stats.total_fallback += 1
        self._call_fallback = True
        return self._fallback(legal_actions), total_inp, total_out

    def _validate_action(
        self,
        raw: dict,
        player: str,
        hero: str,
        stage: str,
        legal_actions: list[Action],
    ) -> Action | None:
        """Waliduj raw dict przez Pydantic (gdy dostępne) lub fuzzy match."""
        if _SCHEMAS_AVAILABLE:
            action = action_from_llm_output(raw, player, hero, stage)
            if action is not None and action in legal_actions:
                return action
        return _match_action(raw, legal_actions)

    def _fallback(self, legal_actions: list[Action]) -> Action:
        if self._fallback_rng is not None:
            return self._fallback_rng.choice(legal_actions)
        import random
        return random.choice(legal_actions)


# ---------------------------------------------------------------------------
# Anthropic — claude-*
# ---------------------------------------------------------------------------

class AnthropicLLMAgent(BaseLLMAgent):
    """Agent korzystający z Anthropic SDK.

    model: np. "claude-haiku-4-5" (tani), "claude-opus-4-8" (najmocniejszy)
    api_key: jeśli None, pobiera z ANTHROPIC_API_KEY
    """

    def __init__(
        self,
        model: str = "claude-haiku-4-5",
        api_key: str | None = None,
        mode: LLMMode = LLMMode.GUIDED,
        max_retries: int = 2,
        fallback_rng: Rng | None = None,
        verbose: bool = False,
    ) -> None:
        super().__init__(mode=mode, max_retries=max_retries,
                         fallback_rng=fallback_rng, verbose=verbose)
        self.model = model

        try:
            import anthropic as _ant
        except ImportError as exc:
            raise ImportError("pip install anthropic") from exc

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise EnvironmentError("Brak ANTHROPIC_API_KEY")
        self._client = _ant.Anthropic(api_key=key)

    def _call_guided(self, prompt: str, num_actions: int) -> tuple[int, int, int]:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=512,
            system=self._SYSTEM_PROMPT,
            tools=[_guided_tool_anthropic()],
            tool_choice={"type": "tool", "name": "choose_action"},
            messages=[{"role": "user", "content": prompt}],
        )
        inp = response.usage.input_tokens
        out = response.usage.output_tokens
        for block in response.content:
            if block.type == "tool_use" and block.name == "choose_action":
                self._call_reasoning = str(block.input.get("reasoning", ""))
                idx = block.input.get("action_index", 0)
                if isinstance(idx, int):
                    return idx, inp, out
        return 0, inp, out

    def _call_free_form(
        self, prompt: str, hero: str = "", stage: str = "board"
    ) -> tuple[dict | None, int, int]:
        tool = (
            _hero_tool_anthropic(hero, stage)
            if _SCHEMAS_AVAILABLE and hero
            else _free_form_tool_anthropic()
        )
        response = self._client.messages.create(
            model=self.model,
            max_tokens=512,
            system=self._SYSTEM_PROMPT,
            tools=[tool],
            tool_choice={"type": "tool", "name": "propose_action"},
            messages=[{"role": "user", "content": prompt}],
        )
        inp = response.usage.input_tokens
        out = response.usage.output_tokens
        for block in response.content:
            if block.type == "tool_use" and block.name == "propose_action":
                # Pydantic-backed schema zwraca flat dict; fallback zwraca action_type+action_data
                data = dict(block.input)
                self._call_reasoning = str(data.get("reasoning", ""))
                if "action_data" in data:
                    atype = data.pop("action_type", "")
                    adata = data.pop("action_data", {})
                    return {"type": atype, **adata}, inp, out
                if "action_type" in data:
                    atype = data.pop("action_type")
                    data["type"] = atype
                return data, inp, out
        return None, inp, out


# ---------------------------------------------------------------------------
# OpenAI-compatible — GPT, Qwen, MiniMax, ...
# ---------------------------------------------------------------------------

class OpenAILLMAgent(BaseLLMAgent):
    """Agent korzystający z OpenAI SDK.

    Obsługuje dowolny dostawca z OpenAI-compatible API przez base_url:
      - OpenAI GPT:   base_url=None,           api_key=OPENAI_API_KEY
      - Qwen:         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
      - MiniMax:      base_url="https://api.minimax.chat/v1"
      - Ollama:       base_url="http://localhost:11434/v1", api_key="ollama"
      - inne          base_url=<endpoint>, api_key=<klucz>

    model: np. "gpt-4o-mini", "qwen-plus", "MiniMax-Text-01", "llama3.2"
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        mode: LLMMode = LLMMode.GUIDED,
        max_retries: int = 2,
        fallback_rng: Rng | None = None,
        verbose: bool = False,
    ) -> None:
        super().__init__(mode=mode, max_retries=max_retries,
                         fallback_rng=fallback_rng, verbose=verbose)
        self.model = model

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("pip install openai") from exc

        key = api_key or os.environ.get("OPENAI_API_KEY", "placeholder")
        self._client = OpenAI(api_key=key, base_url=base_url)

    def _call_guided(self, prompt: str, num_actions: int) -> tuple[int, int, int]:
        from openai import NOT_GIVEN
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            tools=[_guided_tool_openai()],
            tool_choice={"type": "function", "function": {"name": "choose_action"}},
            max_tokens=512,
        )
        usage = response.usage
        inp = usage.prompt_tokens if usage else 0
        out = usage.completion_tokens if usage else 0
        msg = response.choices[0].message
        if msg.tool_calls:
            import json
            args = json.loads(msg.tool_calls[0].function.arguments)
            self._call_reasoning = str(args.get("reasoning", ""))
            idx = args.get("action_index", 0)
            if isinstance(idx, int):
                return idx, inp, out
        return 0, inp, out

    def _call_free_form(
        self, prompt: str, hero: str = "", stage: str = "board"
    ) -> tuple[dict | None, int, int]:
        import json
        tool = (
            _hero_tool_openai(hero, stage)
            if _SCHEMAS_AVAILABLE and hero
            else _free_form_tool_openai()
        )
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": "propose_action"}},
            max_tokens=512,
        )
        usage = response.usage
        inp = usage.prompt_tokens if usage else 0
        out = usage.completion_tokens if usage else 0
        msg = response.choices[0].message
        if msg.tool_calls:
            args = json.loads(msg.tool_calls[0].function.arguments)
            self._call_reasoning = str(args.get("reasoning", ""))
            if "action_data" in args:
                atype = args.pop("action_type", "")
                adata = args.pop("action_data", {})
                return {"type": atype, **adata}, inp, out
            if "action_type" in args:
                atype = args.pop("action_type")
                args["type"] = atype
            return args, inp, out
        return None, inp, out


class OllamaLLMAgent(OpenAILLMAgent):
    """Lokalny LLaMA / Mistral / Qwen przez Ollama (OpenAI-compatible).

    Wymaga działającego serwera: ollama serve
    model: np. "llama3.2", "mistral", "qwen2.5"
    """

    def __init__(
        self,
        model: str = "llama3.2",
        host: str = "http://localhost:11434",
        mode: LLMMode = LLMMode.GUIDED,
        max_retries: int = 2,
        fallback_rng: Rng | None = None,
        verbose: bool = False,
    ) -> None:
        super().__init__(
            model=model,
            api_key="ollama",
            base_url=f"{host}/v1",
            mode=mode,
            max_retries=max_retries,
            fallback_rng=fallback_rng,
            verbose=verbose,
        )


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------

class GeminiLLMAgent(BaseLLMAgent):
    """Agent korzystający z Google Generative AI SDK (gemini-*).

    api_key: jeśli None, pobiera z GOOGLE_API_KEY
    model: np. "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-pro"
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: str | None = None,
        mode: LLMMode = LLMMode.GUIDED,
        max_retries: int = 2,
        fallback_rng: Rng | None = None,
        verbose: bool = False,
    ) -> None:
        super().__init__(mode=mode, max_retries=max_retries,
                         fallback_rng=fallback_rng, verbose=verbose)
        self.model = model

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError("pip install google-generativeai") from exc

        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise EnvironmentError("Brak GOOGLE_API_KEY")
        genai.configure(api_key=key)
        self._genai = genai
        self._client = genai.GenerativeModel(
            model_name=model,
            system_instruction=self._SYSTEM_PROMPT,
        )

    def _call_guided(self, prompt: str, num_actions: int) -> tuple[int, int, int]:
        import json
        tool = self._genai.protos.Tool(
            function_declarations=[_guided_func_declaration_gemini()]
        )
        response = self._client.generate_content(
            prompt,
            tools=[tool],
            tool_config={"function_calling_config": {"mode": "ANY",
                                                      "allowed_function_names": ["choose_action"]}},
            generation_config={"max_output_tokens": 512},
        )
        inp = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
        out = response.usage_metadata.candidates_token_count if response.usage_metadata else 0

        for part in response.parts:
            if part.function_call:
                self._call_reasoning = str(part.function_call.args.get("reasoning", ""))
                idx = int(part.function_call.args.get("action_index", 0))
                return idx, inp, out
        return 0, inp, out

    def _call_free_form(
        self, prompt: str, hero: str = "", stage: str = "board"
    ) -> tuple[dict | None, int, int]:
        tool = self._genai.protos.Tool(
            function_declarations=[_free_form_func_declaration_gemini()]
        )
        response = self._client.generate_content(
            prompt,
            tools=[tool],
            tool_config={"function_calling_config": {"mode": "ANY",
                                                      "allowed_function_names": ["propose_action"]}},
            generation_config={"max_output_tokens": 512},
        )
        inp = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
        out = response.usage_metadata.candidates_token_count if response.usage_metadata else 0

        for part in response.parts:
            if part.function_call:
                fc = part.function_call
                self._call_reasoning = str(fc.args.get("reasoning", ""))
                atype = fc.args.get("action_type", "")
                adata = dict(fc.args.get("action_data", {}))
                if atype:
                    return {"type": atype, **adata}, inp, out
        return None, inp, out


# ---------------------------------------------------------------------------
# Renderowanie stanu
# ---------------------------------------------------------------------------

def _render_guided(state_view: dict, legal_actions: list[Action]) -> str:
    lines = _render_common(state_view)
    lines.append("")
    lines.append("LEGAL ACTIONS (choose one by index):")
    for i, a in enumerate(legal_actions):
        lines.append(f"  [{i}] {_action_summary(a.to_dict())}")
    lines.append("")
    lines.append(f"Choose action index 0–{len(legal_actions)-1}.")
    return "\n".join(lines)


def _render_free_form(state_view: dict) -> str:
    lines = _render_common(state_view)
    lines.append("")
    lines.append("Propose your next action as a structured action object.")
    lines.append("Valid action types: roll_bid, apollon_bid, place_entity, move_entity,")
    lines.append("  build, buy_card, place_income, buy_creature, replace_creature,")
    lines.append("  play_card, end_turn.")
    return "\n".join(lines)


def _render_common(v: dict) -> list[str]:
    me = v.get("me", "?")
    stage = v.get("stage", "?")
    round_no = v.get("round_no", "?")
    act_player = v.get("act_player", "?")
    act_hero = v.get("act_hero", "?")

    lines: list[str] = [
        f"=== CYCLADES — Round {round_no}, Phase {stage.upper()} ===",
        f"You are: {me}  |  Active player: {act_player}  |  Hero: {act_hero}",
        "",
        "PLAYERS:",
    ]
    for pid, pdata in v.get("players", {}).items():
        marker = " ← YOU" if pid == me else ""
        lines.append(
            f"  {pid}{marker}: coins={pdata.get('coins',0)}, "
            f"philosophers={pdata.get('philosophers',0)}, "
            f"priests={pdata.get('priests',0)}"
        )

    opts = v.get("options", {})
    lines.append(f"  metros_to_win={opts.get('metros_to_win', 2)}, combat_dice={opts.get('combat_dice', False)}")
    heroes = v.get("round_heroes") or {}
    if any(heroes.values()):
        lines.append(f"  gods this cycle: {heroes}")

    if stage == "roll":
        roll = v.get("roll", {})
        lines += ["", "OFFERINGS (row: god → current offer):"]
        for row, hero in sorted(roll.get("heros_per_row", {}).items()):
            if hero:
                lines.append(f"  {row}: {hero} → {roll.get('bids', {}).get(row) or 'none'}")
        lines.append(f"  next markers: {roll.get('bid_order', [])}")
        if roll.get("banned", {}).get(me):
            lines.append(f"  you were outbid on {roll['banned'][me]} — choose another god")

    lines += ["", "BOARD:"]
    for fid, fdata in v.get("fields", {}).items():
        owner = fdata.get("owner") or "—"
        ftype = fdata.get("type", "")
        entity = fdata.get("entity")
        buildings = fdata.get("buildings", [])
        metro = " [METROPOLIS]" if fdata.get("is_metropolis") else ""
        unit_str = f" {entity.get('kind','?')}×{entity['quantity']}" if entity and entity.get("quantity") else ""
        bld = [b["hero"] for b in (buildings.values() if isinstance(buildings, dict) else []) if b]
        bld_str = f" buildings={bld}" if bld else ""
        inc = fdata.get("base_income", 0) + (fdata.get("income") or {}).get("quantity", 0)
        inc_str = f" income={inc}" if inc else ""
        nb_str = f" adj={fdata.get('neighbors', [])}" if ftype == "island" else ""
        lines.append(f"  {fid} ({ftype}) owner={owner}{unit_str}{bld_str}{inc_str}{metro}{nb_str}")

    cards = v.get("cards", {})
    if cards.get("track") is not None:
        costs = ["4", "3", "2"]
        track = [f"slot{i}({costs[i]}g)={c}" for i, c in enumerate(cards.get("track", [])) if c]
        lines += ["", f"CREATURE TRACK: {', '.join(track) or 'empty'}"]
        if cards.get("figures"):
            lines.append(f"  figures on board: {cards['figures']}")

    if stage == "board":
        board = v.get("board", {})
        lines += ["", f"YOUR TURN: recruited this turn={board.get('entity_price', 0)}"]
        if board.get("pending"):
            lines.append(f"  PENDING CHOICE (resolve first): {board['pending']}")
    return lines


def _action_summary(d: dict) -> str:
    parts = [d.get("type", "?")]
    parts += [f"{k}={v}" for k, v in d.items() if k != "type"]
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Definicje narzędzi — Anthropic format
# ---------------------------------------------------------------------------

def _guided_tool_anthropic() -> dict:
    return {
        "name": "choose_action",
        "description": "Choose exactly one legal action by its index.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},
                "action_index": {"type": "integer"},
            },
            "required": ["action_index"],
            "additionalProperties": False,
        },
    }


def _free_form_tool_anthropic() -> dict:
    return {
        "name": "propose_action",
        "description": "Propose your next game action.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},
                "action_type": {"type": "string"},
                "action_data": {"type": "object"},
            },
            "required": ["action_type", "action_data"],
            "additionalProperties": False,
        },
    }


# ---------------------------------------------------------------------------
# Definicje narzędzi — OpenAI format
# ---------------------------------------------------------------------------

def _guided_tool_openai() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "choose_action",
            "description": "Choose exactly one legal action by its index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string"},
                    "action_index": {"type": "integer"},
                },
                "required": ["action_index"],
                "additionalProperties": False,
            },
        },
    }


def _free_form_tool_openai() -> dict:
    return {
        "type": "function",
        "function": {
            "name": "propose_action",
            "description": "Propose your next game action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string"},
                    "action_type": {"type": "string"},
                    "action_data": {"type": "object"},
                },
                "required": ["action_type", "action_data"],
                "additionalProperties": False,
            },
        },
    }


# ---------------------------------------------------------------------------
# Definicje funkcji — Gemini format
# ---------------------------------------------------------------------------

def _guided_func_declaration_gemini() -> dict:
    return {
        "name": "choose_action",
        "description": "Choose exactly one legal action by its index.",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},
                "action_index": {"type": "integer"},
            },
            "required": ["action_index"],
        },
    }


def _free_form_func_declaration_gemini() -> dict:
    return {
        "name": "propose_action",
        "description": "Propose your next game action.",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},
                "action_type": {"type": "string"},
                "action_data": {"type": "object"},
            },
            "required": ["action_type", "action_data"],
        },
    }


# ---------------------------------------------------------------------------
# Hero-specific tool builders (używają Pydantic schema gdy dostępne)
# ---------------------------------------------------------------------------

def _hero_tool_anthropic(hero: str, stage: str) -> dict:
    """Zwróć narzędzie Anthropic z precyzyjnym schematem per-bóg."""
    schema = json_schema_for_hero(hero, stage)
    return {
        "name": "propose_action",
        "description": f"Propose your next action as {hero} in the {stage} phase.",
        "input_schema": schema,
    }


def _hero_tool_openai(hero: str, stage: str) -> dict:
    """Zwróć narzędzie OpenAI z precyzyjnym schematem per-bóg."""
    schema = json_schema_for_hero(hero, stage)
    return {
        "type": "function",
        "function": {
            "name": "propose_action",
            "description": f"Propose your next action as {hero} in the {stage} phase.",
            "parameters": schema,
        },
    }


# ---------------------------------------------------------------------------
# Dopasowanie akcji (wspólne)
# ---------------------------------------------------------------------------

def _match_action(raw: dict, legal_actions: list[Action]) -> Action | None:
    try:
        candidate = action_from_dict(raw)
        if candidate in legal_actions:
            return candidate
    except Exception:
        pass

    raw_type = raw.get("type", "")
    for action in legal_actions:
        a_dict = action.to_dict()
        if a_dict.get("type") != raw_type:
            continue
        if all(raw.get(k) == v for k, v in a_dict.items() if k != "type" and k in raw):
            return action
    return None
