# Wyniki sprzed Fazy 6.1 — NIE UŻYWAĆ jako punktu odniesienia

Wygenerowane na silniku, który:

- odrzucał 6,0% akcji zwróconych przez własne `legal_actions()`,
- stawiał na planszy "graczy-widma" (przy 2 graczach 15 z 22 zajętych pól
  należało do p3/p4/p5 bez agenta),
- pozwalał wojownikom stać na otwartym morzu,
- nie był reprodukowalny między procesami (kolejność akcji zależna
  od `PYTHONHASHSEED`).

Uwaga na niespójność: pliki mają `"steps": 400`, czyli powstały przy
`MAX_STEPS = 400`, mimo że `compare.py` ma dziś `MAX_STEPS = 800`.
Stała została podniesiona bez przegenerowania danych — stąd błędna liczba
"70% truncated przy max_steps=800" w PLAN.md.

Trzymane wyłącznie do porównania "przed/po". Nowe wyniki: katalog wyżej.
