# Testy end-to-end (na działającej aplikacji)

Wymagają uruchomionego backendu (:8000) i frontendu w trybie dev (:5173) — patrz `web/README.md`.

| Plik | Co sprawdza | Uruchomienie |
|---|---|---|
| `fuzz_api.py` | partie z losowymi legalnymi ruchami przez HTTP dla 2–5 graczy × kości × Stwory; po każdym kroku niezmienniki stanu (złoto ≥ 0, ≤ 8 jednostek, spójność właścicieli pól, Kraken, 17 kart Stworów, zwycięzca ma wymagane metropolie) | `web/backend/.venv/bin/python web/e2e/fuzz_api.py 4` |
| `fuzz_negative.py` | zmutowane / cudze / nieaktualne akcje → 409/422 (nigdy 500), stan bez zmian; błędne `new_game`; 404; `ai-step` w turze człowieka | `web/backend/.venv/bin/python web/e2e/fuzz_negative.py` |
| `ui_scenarios.js` | 51 sprawdzeń w przeglądarce: ekran startowy, licytacja (przebicie, 2 graczy), Ares/Posejdon/Zeus/Atena/Apollo, Stwory, obowiązkowa Metropolia, pętla AI z pauzą, koniec gry, odświeżenie, błąd 409, widok 390 px, konsola | funkcja `async (page) => …` dla Playwright (np. narzędzie `browser_run_code_unsafe` z pliku) |

Wynik ostatniego przebiegu (2026-10-02): 64 partie HTTP bez naruszeń niezmienników,
0 odpowiedzi 500, 51/51 scenariuszy UI.
