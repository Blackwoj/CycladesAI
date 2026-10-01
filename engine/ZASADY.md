# Zgodność silnika z instrukcją Cyclades

Źródła: [instrukcja](https://www.rebel.pl/repository/files/instrukcje/Cyclades.pdf)
(rebel.pl, 8 str.) i [książeczka Stworów](https://files.rebel.pl/files/instrukcje/Cyklady_Potwory.pdf)
(4 str.). Audyt: 2026-10-01. Testy z cytatami zasad: `engine/tests/test_rules_audit.py`,
`engine/tests/test_creatures.py`.

## Naprawione rozbieżności

| Zasada (instrukcja) | Było w silniku | Jest |
|---|---|---|
| Start: 5 GP, 2 wyspy, 2 Oddziały, 2 Floty na gracza (str. 1, 7–8) | p4/p5 10 GP, p5 2 Filozofów; p5 3 wyspy, 6 Oddziałów, 4 Floty (dane testowe z JSON) | wg ilustracji; JSON-y w `game/` nietknięte, poprawka w `setup.py` |
| Dochód na początku każdego cyklu (str. 2) | dopiero po 1. cyklu | także w cyklu 1 (5 + 2 GP) |
| Gra 2-osobowa: 3 bogów + Apollo, 2 znaczniki na gracza, 3 Metropolie (str. 6) | 1 bóg + Apollo, 1 znacznik, 2 Metropolie | zgodnie z instrukcją; gracz ma 2 tury z różnymi bogami |
| Przelicytowany licytuje u INNEGO boga (str. 3) | mógł wrócić do tego samego | zakaz powrotu (`roll.banned`) |
| Ofiar nie wolno składać ponad stan (str. 3) | limit liczony per ofiara | suma kosztów ofiar ≤ złoto |
| Kto skończył akcje ostatni, ten pierwszy składa ofiarę (str. 3) | kolejność losowana co cykl | odwrócona kolejność akcji |
| Rekrutacja: maks. 3 dodatkowe na turę; maks. 8 jednostek (str. 4) | bez limitu na turę; maks. 6 | 4 na turę, 8 na planszy |
| Flota tylko na puste/własne pole przy swojej wyspie (str. 4) | także na pole przeciwnika | poprawione |
| Ruch Floty: 1 GP za maks. 3 pola, stop na wrogich Flotach (str. 4) | 1 pole + „2 darmowe skoki” | BFS ≤ 3 pola |
| Ruch Oddziałów po łańcuchu WŁASNYCH Flot (str. 4) | także przez własne wyspy | tylko łańcuch Flot |
| Pusta wyspa przeciwnika = przejęcie bez walki (str. 4) | — | tak |
| Nie wolno atakować ostatniej wyspy, chyba że daje wygraną (str. 4) | brak | `may_attack_island` |
| Bitwa: rundy, kość + jednostki, przegrany traci 1, remis obaj (str. 5) | jednorazowe odejmowanie liczebności | `rules/combat.py` |
| Forteca / Port / Metropolia: +1 do obrony (str. 4–5) | brak | tak |
| Budynek każdego boga poza Apollem (str. 4) | Atena i Zeus nie budowali | naprawione (Faza 6.2) |
| Metropolia natychmiast i obowiązkowo (str. 4, 6) | opcjonalna akcja; z budynków nieosiągalna | wymuszony wybór wyspy (`board.pending`) |
| Wygrana na KONIEC cyklu, remis → więcej złota (str. 6) | natychmiast po zbudowaniu | koniec cyklu + tie-break |
| Apollo: znacznik dobrobytu dla pierwszego (str. 6) | brak | `PlaceIncome` |
| Mitologiczne Stwory (str. 3–4 + książeczka) | brak | `rules/creatures.py`, 17 kart |

## Świadome uproszczenia (do opisania w pracy)

- **Kości w bitwie** są opcją (`GameOptions.combat_dice`). Domyślnie kość = 0:
  ta sama procedura rund, ale deterministyczna (taniej dla MCTS, łatwiej porównywać).
- **Wycofanie się z bitwy** nie jest modelowane — bitwa toczy się do końca.
- **Plansza** zawsze 5-osobowa (w oryginale 2–3 graczy grają na mniejszej);
  pozycje nieobecnych graczy są neutralne. Patrz PLAN.md, punkt A.
- **Ruch Floty**: przesuwa się grupa z jednego pola; dołączanie i zostawianie
  jednostek po drodze (str. 4) nie jest modelowane.
- **Sloty budynków** wg JSON-ów starego GUI; Metropolia zajmuje całą wyspę
  (dalsze budynki na niej niedozwolone) zamiast jednego „dużego” miejsca.
- **Metropolia z budynków** zdejmuje po 1 budynku każdego typu, najpierw z wyspy
  docelowej — deterministycznie (oryginał: wybór gracza).
- **Bogowie w 3/4-osobowej**: bóg niedostępny w poprzednim cyklu wchodzi jako
  pierwszy; parowanie bogów w grze 3-osobowej (str. 2) jest uproszczone.
- **Stwory** — interpretacje niejednoznacznych opisów są w docstringu
  `rules/creatures.py` (Syrena, Sylfida, Polifem, czas działania figurek).
- Talia ma **17** Stworów: „18 kart” w instrukcji to błąd druku
  ([BGG](https://boardgamegeek.com/thread/495745/17-or-18-mythological-creature-cards)).
