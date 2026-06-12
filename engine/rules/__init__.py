"""Mechanika gry (Faza 2 — w toku).

Tu trafia czysta logika reguł przeniesiona z game/managers/*, operująca na
GameState bez pygame. Plan portu, per etap:

- roll.py    — aukcja herosów (port RollManager): legal bids, rozstrzygnięcie, kolejność
- board.py   — wystawianie/ruch jednostek, budowa, karty (port BoardManager + sub-managery)
- combat.py  — walka (z losowością — pod chance nodes MCTS)
- scoring.py — warunki końca gry i punktacja (metropolie)
- setup.py   — layout planszy (port BoardConfig/Locations), rozdanie startowe

Dopóki nieprzeniesione, engine.legal_actions/step rzucają NotImplementedError.
"""
