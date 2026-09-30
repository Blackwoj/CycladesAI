"""Jedyne miejsce w backendzie, które zna klasy agentów AI.

Specyfikacja agenta z requestu -> instancja `engine.agents.Agent`.
Gracz bez specyfikacji (albo kind="human") jest człowiekiem i nie ma agenta.
"""
from __future__ import annotations

from engine.agents import Agent, MCTSAgent, RandomAgent
from engine.agents.llm_factory import PROVIDERS, make_llm_agent
from engine.rng import Rng

from .schemas import AgentSpec


def build_agent(spec: AgentSpec, rng: Rng) -> Agent | None:
    if spec.kind == "human":
        return None
    if spec.kind == "random":
        return RandomAgent(rng=rng.spawn())
    if spec.kind == "mcts":
        return MCTSAgent(n_simulations=spec.n_simulations, rollout_rng=rng.spawn())
    if spec.kind == "llm":
        return make_llm_agent(spec.provider, spec.model, spec.mode, fallback_rng=rng.spawn())
    raise ValueError(f"nieznany rodzaj agenta: {spec.kind}")


def describe(spec: AgentSpec) -> str:
    if spec.kind == "human":
        return "Człowiek"
    if spec.kind == "random":
        return "Random"
    if spec.kind == "mcts":
        return f"MCTS ({spec.n_simulations})"
    model = spec.model or PROVIDERS[spec.provider][0]
    return f"LLM {model} ({spec.mode})"
