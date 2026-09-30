// Nazwy, kolory i opisy — dane prezentacyjne, zero reguł gry.

export const PLAYER_COLORS = {
  p1: '#e5533d', p2: '#3d8fe5', p3: '#3fbf6f', p4: '#f0c330', p5: '#a66de0',
}

export const HEROES = {
  ares:     { name: 'Ares',     color: '#b83227', desc: 'wojownicy i ruch po lądzie' },
  posejdon: { name: 'Posejdon', color: '#1c8c8c', desc: 'statki i ruch po morzu' },
  atena:    { name: 'Atena',    color: '#5b7da6', desc: 'filozofowie' },
  zeus:     { name: 'Zeus',     color: '#cf9a12', desc: 'kapłani (zniżka w licytacji)' },
  apollon:  { name: 'Apollon',  color: '#e57a1f', desc: 'dochód' },
  ap_s:     { name: 'Apollon',  color: '#e57a1f', desc: 'dochód (kolejny gracz)' },
  metro:    { name: 'Metropolia', color: '#c9a84c', desc: '' },
}

export const heroName = (h) => HEROES[h]?.name ?? '—'

export function describeAction(a) {
  switch (a.type) {
    case 'roll_bid': return `licytuje ${a.amount} na ${a.row.replace('row_', 'rząd ')}`
    case 'apollon_bid': return 'wybiera Apollona'
    case 'place_entity': return `wystawia ${a.kind === 'warrior' ? 'wojownika' : 'statek'} na ${a.field_id}`
    case 'move_entity': return `przesuwa ${a.quantity} z ${a.from_field} na ${a.to_field}`
    case 'build': return a.hero === 'metro' ? `buduje metropolię na ${a.field_id}` : `buduje (${heroName(a.hero)}) na ${a.field_id}`
    case 'place_income': return `kładzie znacznik dochodu na ${a.field_id}`
    case 'buy_card': return `kupuje kartę ${a.hero === 'atena' ? 'filozofa' : 'kapłana'}`
    case 'end_turn': return 'kończy turę'
    default: return a.type
  }
}
