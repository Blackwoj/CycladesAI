// Nazwy, kolory i opisy — dane prezentacyjne, zero reguł gry.

export const PLAYER_COLORS = {
  p1: '#e5533d', p2: '#3d8fe5', p3: '#3fbf6f', p4: '#f0c330', p5: '#a66de0',
}

export const HEROES = {
  ares:     { name: 'Ares',     color: '#b83227', desc: 'wojownicy, ruch po lądzie, forteca' },
  posejdon: { name: 'Posejdon', color: '#1c8c8c', desc: 'statki, ruch po morzu, port' },
  atena:    { name: 'Atena',    color: '#5b7da6', desc: 'filozofowie, uniwersytet' },
  zeus:     { name: 'Zeus',     color: '#cf9a12', desc: 'kapłani (zniżka w licytacji), świątynia' },
  apollon:  { name: 'Apollon',  color: '#e57a1f', desc: 'dochód' },
  ap_s:     { name: 'Apollon',  color: '#e57a1f', desc: 'dochód (kolejny gracz)' },
  metro:    { name: 'Metropolia', color: '#c9a84c', desc: '' },
}

export const heroName = (h) => HEROES[h]?.name ?? '—'

// Mitologiczne Stwory — opisy wg książeczki „Potwory” (rebel.pl)
export const CREATURES = {
  syrena:   { name: 'Syrena',   desc: 'zastąp odosobnioną Flotę przeciwnika swoją' },
  pegaz:    { name: 'Pegaz',    desc: 'przenieś Oddziały na dowolną wyspę bez Flot' },
  gigant:   { name: 'Gigant',   desc: 'zniszcz budynek (nie Metropolię)' },
  chimera:  { name: 'Chimera',  desc: 'użyj mocy Stwora ze stosu odrzuconych' },
  cyklopi:  { name: 'Cyklopi',  desc: 'zamień swój budynek na inny typ' },
  sfinks:   { name: 'Sfinks',   desc: 'sprzedaj jednostki i karty po 2 GP' },
  sylfida:  { name: 'Sylfida',  desc: 'przesuń swoje Floty łącznie o 10 pól' },
  harpia:   { name: 'Harpia',   desc: 'usuń Oddział przeciwnika' },
  gryf:     { name: 'Gryf',     desc: 'zabierz połowę złota graczowi' },
  mojry:    { name: 'Mojry',    desc: 'pobierz dochód jeszcze raz' },
  satyr:    { name: 'Satyr',    desc: 'ukradnij Filozofa' },
  driada:   { name: 'Driada',   desc: 'ukradnij Kapłana' },
  kraken:   { name: 'Kraken',   desc: 'zniszcz Floty na polu morza i zablokuj je' },
  minotaur: { name: 'Minotaur', desc: '+2 do obrony wyspy (figurka)' },
  chiron:   { name: 'Chiron',   desc: 'wyspa odporna na Pegaza, Harpię, Giganta (figurka)' },
  meduza:   { name: 'Meduza',   desc: 'Oddziały na wyspie nie mogą się ruszać (figurka)' },
  polifem:  { name: 'Polifem',  desc: 'odpycha Floty od wyspy (figurka)' },
}
export const creatureName = (c) => CREATURES[c]?.name ?? c
export const TRACK_COSTS = [4, 3, 2]

const TARGET_WORDS = { warrior: 'Oddział', ship: 'Flota', priest: 'Kapłan', philosopher: 'Filozof' }

export function describeTargets(a) {
  const t = a.targets ?? []
  if (t[0] === 'done') return 'zakończ efekt'
  switch (a.card_id) {
    case 'pegaz': return `${t[2]} Oddz. z ${t[0]} na ${t[1]}`
    case 'sylfida': return `${t[2]} Flot z ${t[0]} na ${t[1]}`
    case 'gigant': return `zniszcz budynek na ${t[0]}`
    case 'cyklopi': return `${t[0]}: zamień na ${heroName(t[2])}`
    case 'sfinks': return `sprzedaj: ${TARGET_WORDS[t[0]] ?? t[0]}${t[1] ? ` (${t[1]})` : ''}`
    case 'chimera': return `użyj: ${creatureName(t[0])}`
    case 'gryf': case 'satyr': case 'driada': return `cel: ${t[0]}`
    case 'kraken': return `Kraken na ${t[0]}`
    case 'syrena': return `przejmij Flotę na ${t[0]}`
    case 'harpia': return `usuń Oddział z ${t[0]}`
    case 'minotaur': case 'chiron': case 'meduza': case 'polifem': return `postaw na ${t[0]}`
    default: return t.join(' ')
  }
}

export function describeAction(a) {
  switch (a.type) {
    case 'roll_bid': return `licytuje ${a.amount} na ${a.row.replace('row_', 'rząd ')}`
    case 'apollon_bid': return 'wybiera Apollona'
    case 'place_entity': return `wystawia ${a.kind === 'warrior' ? 'wojownika' : 'statek'} na ${a.field_id}`
    case 'move_entity': return `przesuwa ${a.quantity} z ${a.from_field} na ${a.to_field}`
    case 'build': return a.hero === 'metro' ? `buduje metropolię na ${a.field_id}` : `buduje (${heroName(a.hero)}) na ${a.field_id}`
    case 'place_income': return `kładzie znacznik dochodu na ${a.field_id}`
    case 'buy_creature': return `wzywa Stwora z pola ${TRACK_COSTS[a.slot]} GP`
    case 'replace_creature': return `wymienia Stwora z pola ${TRACK_COSTS[a.slot]} GP`
    case 'play_card': return `${creatureName(a.card_id)}: ${describeTargets(a)}`
    case 'buy_card': return `kupuje kartę ${a.hero === 'atena' ? 'filozofa' : 'kapłana'}`
    case 'end_turn': return 'kończy turę'
    default: return a.type
  }
}
