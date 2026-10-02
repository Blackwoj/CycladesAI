async (page) => {
  const R = [];
  const consoleErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()) });
  page.on('pageerror', (e) => consoleErrors.push('PAGEERROR ' + e.message));
  const sleep = (t) => new Promise((r) => setTimeout(r, t));
  const ok = (name, cond, info = '') => R.push({ name, ok: !!cond, info: cond ? '' : String(info).slice(0, 300) });

  const api = (method, path, body) => page.evaluate(async ([m, p, b]) => {
    const r = await fetch('/api' + p, { method: m, headers: { 'Content-Type': 'application/json' }, body: b ? JSON.stringify(b) : undefined })
    return { status: r.status, data: await r.json() }
  }, [method, path, body ?? null]);
  const step = async (v, a) => {
    const r = await api('POST', `/game/${v.game_id}/step`, { action: a });
    if (r.status !== 200) throw new Error(`step ${r.status} ${JSON.stringify(r.data)} ${JSON.stringify(a)}`);
    return r.data;
  };
  // gra przez API aż do warunku; pick(v) zwraca akcję albo null (=losowa)
  const drive = async (v, until, pick = () => null, max = 3000, seed = 1) => {
    let x = seed;
    const rnd = (n) => { x = (x * 1103515245 + 12345) % 2147483648; return x % n };
    for (let i = 0; i < max; i++) {
      if (until(v)) return v;
      if (v.terminal) return v;
      const a = (pick ? pick(v) : null) ?? v.legal_actions[rnd(v.legal_actions.length)];
      v = await step(v, a);
    }
    return v;
  };
  const open = async (gid) => {
    await page.evaluate((g) => localStorage.setItem('cyklady.game_id', g), gid);
    await page.reload();
    await page.waitForSelector('svg.board', { timeout: 10000 });
    await sleep(300);
  };
  const game = async (gid) => (await api('GET', `/game/${gid}`)).data;
  const clickField = async (id) => { await page.locator(`g.hit[data-field="${id}"]`).first().dispatchEvent('click'); await sleep(250) };
  const clickBtn = async (sel, text) => {
    const b = page.locator(sel, { hasText: text }).first();
    await b.click(); await sleep(500);
  };
  const newGame = async (body) => (await api('POST', '/game/new', body)).data;
  const isHero = (h) => (v) => v.stage === 'board' && v.act_player_is_human && !v.state.board.pending && v.state.act_hero === h;
  // polityka: w licytacji bierz danego boga, potem kończ tury innych
  const wantGod = (h) => (v) => {
    if (v.stage === 'roll') {
      const row = Object.entries(v.state.roll.heros_per_row).find(([, g]) => g === h)?.[0];
      return v.legal_actions.find((a) => a.type === 'roll_bid' && a.row === row) ?? v.legal_actions.find((a) => a.type === 'apollon_bid');
    }
    if (v.state.board.pending) return null;
    return v.legal_actions.find((a) => a.type === 'end_turn') ?? null;
  };

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://localhost:5173');
  await page.evaluate(() => localStorage.clear());
  await page.reload();

  // ---- S1: ekran startowy ----------------------------------------------------
  try {
    await page.waitForSelector('.setup-form');
    ok('S1 4 przyciski liczby graczy', (await page.locator('.seg button').count()) === 4);
    await page.locator('.seg button', { hasText: '4' }).click();
    ok('S1 4 wiersze graczy', (await page.locator('.setup-player').count()) === 4);
    await page.locator('.setup-player select').nth(1).selectOption('llm');
    await sleep(400);
    ok('S1 LLM: wybór dostawcy i trybu', (await page.locator('.llm-spec select').count()) === 2);
    ok('S1 LLM: ostrzeżenie o niedostępności', await page.locator('.warn', { hasText: 'niedostępny' }).count());
    await page.locator('.setup-player select').nth(1).selectOption('random');
    await page.locator('.setup-player select').nth(2).selectOption('mcts');
    ok('S1 MCTS: pole symulacji', await page.locator('.setup-player input[type=number]').count());
    await page.locator('.seg button', { hasText: '2' }).click();
    await page.locator('.check input').nth(1).check();
    await page.locator('input[placeholder="np. 42"]').fill('5');
    await page.locator('.setup-player select').nth(1).selectOption('human');
    await page.locator('button.primary', { hasText: 'Rozpocznij' }).click();
    await page.waitForSelector('svg.board', { timeout: 10000 });
    const top = await page.locator('.topbar').innerText();
    ok('S1 start gry: licytacja, kości, 3 metropolie, seed 5', top.includes('Licytacja') && top.includes('kości') && top.includes('do wygranej: 3') && top.includes('seed 5'), top);
  } catch (e) { ok('S1 wyjątek', false, e.message) }

  // ---- S2: licytacja w UI (2 graczy, przebicie) ------------------------------
  try {
    let v = await newGame({ num_players: 2, seed: 4 });
    await open(v.game_id);
    const rows = await page.locator('.roll-row').count();
    ok('S2 3 bogów + Apollo (2 graczy)', rows === 4, rows);
    const bidder = v.act_player;
    await page.locator('.roll-row').first().locator('.bid-buttons button').first().click(); await sleep(500);
    v = await game(v.game_id);
    ok('S2 oferta zapisana', v.state.roll.bids.row_1?.player === bidder, JSON.stringify(v.state.roll.bids));
    // drugi gracz przebija ten sam rząd
    if (v.act_player !== bidder) {
      await page.locator('.roll-row').first().locator('.bid-buttons button').first().click(); await sleep(600);
      v = await game(v.game_id);
      ok('S2 przelicytowany wraca', v.act_player === bidder, v.act_player);
      ok('S2 komunikat „wybierz innego boga”', await page.locator('.warn', { hasText: 'innego boga' }).count());
      ok('S2 brak przycisków w utraconym rzędzie', (await page.locator('.roll-row').first().locator('.bid-buttons button').count()) === 0);
    } else ok('S2 drugi znacznik tego samego gracza', true);
    // dokończ licytację Apollem w UI
    for (let i = 0; i < 6 && (await game(v.game_id)).stage === 'roll'; i++) {
      const ap = page.locator('.roll-row', { hasText: 'Apollon' }).locator('button');
      if (await ap.count()) await ap.click(); else await page.locator('.bid-buttons button').first().click();
      await sleep(500);
    }
    v = await game(v.game_id);
    ok('S2 koniec licytacji → plansza', v.stage === 'board', v.stage);
    const portraits = await page.locator('.player-row').first().locator('.portraits svg').count();
    ok('S2 2 graczy: 2 portrety bogów', portraits === 2, portraits);
  } catch (e) { ok('S2 wyjątek', false, e.message) }

  // ---- S3: Ares — rekrutacja, budowa, ruch -----------------------------------
  try {
    let v = await newGame({ num_players: 3, seed: 21 });
    v = await drive(v, (x) => isHero('ares')(x) && x.legal_actions.some((a) => a.type === 'build'), wantGod('ares'));
    await open(v.game_id);
    const isl = v.legal_actions.find((a) => a.type === 'place_entity').field_id;
    const before = v.state.fields[isl].entity.quantity;
    await clickField(isl);
    await clickBtn('.action-list button', 'Rekrutuj');
    v = await game(v.game_id);
    ok('S3 Ares rekrutacja', v.state.fields[isl].entity.quantity === before + 1);
    const b = v.legal_actions.find((a) => a.type === 'build');
    await clickField(b.field_id);
    await clickBtn('.action-list button', 'Zbuduj budynek');
    v = await game(v.game_id);
    ok('S3 Ares forteca', Object.values(v.state.fields[b.field_id].buildings).some((x) => x?.hero === 'ares'));
    ok('S3 forteca narysowana', await page.locator('svg.board title', { hasText: 'budynek: Ares' }).count());
  } catch (e) { ok('S3 wyjątek', false, e.message) }

  try {
    let v = await newGame({ num_players: 3, seed: 22 });
    v = await drive(v, (x) => isHero('ares')(x) && x.legal_actions.some((a) => a.type === 'move_entity'), wantGod('ares'), 4000);
    if (!v.legal_actions.some((a) => a.type === 'move_entity')) throw new Error('nie dotarłem do ruchu Aresa');
    await open(v.game_id);
    const m = v.legal_actions.find((a) => a.type === 'move_entity');
    await clickField(m.from_field);
    const btn = page.locator('.action-list button', { hasText: 'Przesuń' });
    if (await btn.count()) { await btn.click(); await sleep(300) }
    const targets = await page.locator('g.hit.target').count();
    ok('S3 ruch: podświetlone cele', targets > 0, targets);
    await clickField(m.to_field);
    const qty = page.locator('.panel .bid-buttons button', { hasText: '1' });
    if (await qty.count()) { await qty.first().click(); await sleep(500) }
    v = await game(v.game_id);
    ok('S3 ruch Oddziałów wykonany', v.log.at(-1).action.type === 'move_entity', JSON.stringify(v.log.at(-1)));
  } catch (e) { ok('S3b wyjątek', false, e.message) }

  // ---- S4: Posejdon — flota, ruch do 3 pól -----------------------------------
  try {
    let v = await newGame({ num_players: 3, seed: 23 });
    v = await drive(v, (x) => isHero('posejdon')(x) && x.legal_actions.some((a) => a.type === 'place_entity'), wantGod('posejdon'));
    await open(v.game_id);
    const pe = v.legal_actions.find((a) => a.type === 'place_entity');
    await clickField(pe.field_id);
    await clickBtn('.action-list button', 'Zbuduj statek');
    v = await game(v.game_id);
    ok('S4 Posejdon rekrutacja floty', v.state.fields[pe.field_id].owner === v.act_player && v.state.fields[pe.field_id].entity.kind === 'ship');
    const m = v.legal_actions.find((a) => a.type === 'move_entity');
    if (m) {
      await clickField(m.from_field);
      const mv = page.locator('.action-list button', { hasText: 'Przesuń' });
      if (await mv.count()) { await mv.click(); await sleep(300) }
      const t = await page.locator('g.hit.target').count();
      ok('S4 flota: więcej celów niż sąsiedzi (zasięg 3)', t > 6, t);
      await clickField(m.to_field);
      const q = page.locator('.panel .bid-buttons button');
      if (await q.count()) { await q.first().click(); await sleep(500) }
      v = await game(v.game_id);
      ok('S4 ruch floty wykonany', v.log.at(-1).action.type === 'move_entity');
    } else ok('S4 brak ruchu floty (brak złota)', true);
  } catch (e) { ok('S4 wyjątek', false, e.message) }

  // ---- S5: Zeus — kapłan, świątynia, wymiana Stwora --------------------------
  try {
    let v = await newGame({ num_players: 3, seed: 24 });
    v = await drive(v, (x) => isHero('zeus')(x) && x.legal_actions.some((a) => a.type === 'replace_creature') && x.state.players[x.act_player].coins >= 5, wantGod('zeus'), 5000);
    if (!isHero('zeus')(v)) throw new Error('nie dotarłem do Zeusa');
    await open(v.game_id);
    const pid = v.act_player, pr = v.state.players[pid].priests;
    const track = JSON.stringify(v.state.cards.track);
    await clickBtn('.track-slot button', 'Wymień');
    v = await game(v.game_id);
    ok('S5 Zeus wymiana Stwora', JSON.stringify(v.state.cards.track) !== track);
    if (v.legal_actions.some((a) => a.type === 'buy_card')) {
      await clickBtn('.action-list.global button', 'kapłana');
      v = await game(v.game_id);
      ok('S5 Zeus kupno kapłana', v.state.players[pid].priests === pr + 1);
    } else ok('S5 kapłan niedostępny (złoto)', true);
    const b = v.legal_actions.find((a) => a.type === 'build');
    if (b) {
      await clickField(b.field_id); await clickBtn('.action-list button', 'Zbuduj budynek');
      v = await game(v.game_id);
      ok('S5 świątynia', Object.values(v.state.fields[b.field_id].buildings).some((x) => x?.hero === 'zeus'));
    }
  } catch (e) { ok('S5 wyjątek', false, e.message) }

  // ---- S6: Atena — filozof ---------------------------------------------------
  try {
    let v = await newGame({ num_players: 3, seed: 25 });
    v = await drive(v, (x) => isHero('atena')(x) && x.legal_actions.some((a) => a.type === 'buy_card'), wantGod('atena'), 5000);
    if (!isHero('atena')(v)) throw new Error('nie dotarłem do Ateny');
    await open(v.game_id);
    const pid = v.act_player, ph = v.state.players[pid].philosophers;
    await clickBtn('.action-list.global button', 'filozofa');
    v = await game(v.game_id);
    ok('S6 Atena kupno filozofa', v.state.players[pid].philosophers === ph + 1 || v.state.board.pending?.kind === 'metropolis');
  } catch (e) { ok('S6 wyjątek', false, e.message) }

  // ---- S7: Apollo — znacznik dobrobytu ---------------------------------------
  try {
    let v = await newGame({ num_players: 3, seed: 26 });
    v = await drive(v, (x) => isHero('apollon')(x) && x.legal_actions.some((a) => a.type === 'place_income'), wantGod('apollon'));
    await open(v.game_id);
    ok('S7 podpowiedź Apollona', await page.locator('.panel', { hasText: 'znacznik dochodu' }).count());
    const a = v.legal_actions.find((x) => x.type === 'place_income');
    await clickField(a.field_id);
    await clickBtn('.action-list button', 'znacznik');
    v = await game(v.game_id);
    ok('S7 znacznik położony', v.state.fields[a.field_id].income.quantity === 1);
    ok('S7 znacznik narysowany', await page.locator('svg.board title', { hasText: 'znacznik dochodu' }).count());
  } catch (e) { ok('S7 wyjątek', false, e.message) }

  // ---- S8: Stwory — wezwanie i cel z planszy ---------------------------------
  const seenCreatures = new Set();
  try {
    for (let seed = 30; seed < 60 && seenCreatures.size < 6; seed++) {
      let v = await newGame({ num_players: 3, seed });
      v = await drive(v, (x) => x.stage === 'board' && x.act_player_is_human && !x.state.board.pending
        && x.legal_actions.some((a) => a.type === 'buy_creature'), null, 3000, seed);
      if (v.terminal) continue;
      const card = v.state.cards.track[v.legal_actions.find((a) => a.type === 'buy_creature').slot];
      if (seenCreatures.has(card) || card === 'mojry') continue;
      await open(v.game_id);
      await clickBtn('.track-slot button', 'Wezwij');
      v = await game(v.game_id);
      if (!v.state.board.pending) continue;
      const shown = await page.locator('.pending h3').innerText();
      const hl = await page.locator('g.hit.legal').count();
      const firstField = v.legal_actions.flatMap((a) => a.targets ?? []).find((t) => typeof t === 'string' && v.state.fields[t]);
      if (firstField) { await clickField(firstField) }
      const btns = page.locator('.pending .action-list button:not(.ghost)');
      if (await btns.count()) await btns.first().click(); else await page.locator('.pending .action-list button').first().click();
      await sleep(500);
      // efekty wieloetapowe kończymy przyciskiem „zakończ efekt”
      for (let k = 0; k < 3; k++) {
        const g = await game(v.game_id);
        if (!g.state.board.pending || g.state.board.pending.kind !== 'creature') break;
        await page.locator('.pending .action-list button', { hasText: 'zakończ' }).click(); await sleep(400);
      }
      v = await game(v.game_id);
      ok(`S8 Stwór ${card}: panel, cele, rozstrzygnięcie`, shown.toLowerCase().includes('stwór') && v.log.some((e) => e.action.type === 'play_card')
        && (!v.state.board.pending || v.state.board.pending.kind === 'metropolis'), `${shown} hl=${hl}`);
      seenCreatures.add(card);
    }
    ok('S8 przetestowano ≥ 5 różnych Stworów', seenCreatures.size >= 5, [...seenCreatures]);
  } catch (e) { ok('S8 wyjątek', false, e.message) }

  // ---- S9: obowiązkowa Metropolia --------------------------------------------
  try {
    let found = null;
    for (let seed = 1; seed < 40 && !found; seed++) {
      let v = await newGame({ num_players: 2, seed: 900 + seed });
      v = await drive(v, (x) => x.state.board.pending?.kind === 'metropolis' && x.act_player_is_human, null, 3000, seed);
      if (v.state.board.pending?.kind === 'metropolis') found = v;
    }
    if (!found) throw new Error('nie dotarłem do metropolii');
    await open(found.game_id);
    ok('S9 panel Metropolii', await page.locator('.pending h3', { hasText: 'Metropolia' }).count());
    ok('S9 brak „Zakończ turę” w trakcie wyboru', (await page.locator('button', { hasText: 'Zakończ turę' }).count()) === 0);
    const site = found.legal_actions[0].field_id;
    await clickField(site);
    await page.locator('.pending .action-list button').first().click(); await sleep(500);
    const v = await game(found.game_id);
    ok('S9 metropolia postawiona', v.state.fields[site].is_metropolis);
    ok('S9 metropolia narysowana', await page.locator('svg.board title', { hasText: 'metropolia' }).count());
  } catch (e) { ok('S9 wyjątek', false, e.message) }

  // ---- S10: pętla AI, pauza, tempo -------------------------------------------
  try {
    const v = await newGame({ num_players: 2, seed: 3, agents: { p1: { kind: 'random' }, p2: { kind: 'random' } } });
    await open(v.game_id);
    await page.locator('.topbar input[type=range]').fill('1500');   // najszybciej
    await sleep(2500);
    const s1 = (await game(v.game_id)).step;
    ok('S10 AI gra samo', s1 > 3, s1);
    await page.locator('.topbar button', { hasText: 'Pauza' }).click();
    await sleep(800);
    const s2 = (await game(v.game_id)).step; await sleep(1500);
    const s3 = (await game(v.game_id)).step;
    ok('S10 pauza zatrzymuje AI', s3 === s2, `${s2}→${s3}`);
    await page.locator('.topbar button', { hasText: 'Wznów' }).click(); await sleep(1500);
    ok('S10 wznowienie', (await game(v.game_id)).step > s3);
    ok('S10 log ma wpisy', (await page.locator('.log li').count()) > 3);
    const pause = page.locator('.topbar button', { hasText: 'Pauza' });
    if (!(await game(v.game_id)).terminal) await pause.click({ timeout: 3000 }).catch(() => {});
  } catch (e) { ok('S10 wyjątek', false, e.message) }

  // ---- S11: koniec gry -------------------------------------------------------
  try {
    let v = await newGame({ num_players: 3, seed: 8 });
    v = await drive(v, (x) => x.terminal, null, 5000, 8);
    await open(v.game_id);
    ok('S11 nakładka końca gry', await page.locator('.overlay', { hasText: 'Zwycięstwo' }).count());
    await page.locator('.overlay button', { hasText: 'Nowa gra' }).click(); await sleep(400);
    ok('S11 „Nowa gra” → ekran startowy', await page.locator('.setup-form').count());
  } catch (e) { ok('S11 wyjątek', false, e.message) }

  // ---- S12: odświeżenie i utracona partia ------------------------------------
  try {
    let v = await newGame({ num_players: 2, seed: 12 });
    v = await drive(v, (x) => x.step >= 5);
    await open(v.game_id);
    await page.reload(); await page.waitForSelector('svg.board'); await sleep(300);
    ok('S12 odświeżenie wraca do partii', (await page.locator('.topbar').innerText()).includes(`krok ${v.step}`));
    await page.evaluate(() => localStorage.setItem('cyklady.game_id', 'nie-ma-takiej'));
    await page.reload(); await sleep(800);
    ok('S12 nieistniejąca partia → ekran startowy', await page.locator('.setup-form').count());
  } catch (e) { ok('S12 wyjątek', false, e.message) }

  // ---- S13: nieaktualny stan (ruch „za plecami” UI) ---------------------------
  try {
    let v = await newGame({ num_players: 2, seed: 13 });
    await open(v.game_id);
    await step(v, v.legal_actions[0]);          // zmiana stanu poza przeglądarką
    await page.locator('.bid-buttons button, .roll-row button').first().click(); await sleep(700);
    const err = await page.locator('.error').count();
    const top = await page.locator('.topbar').innerText();
    ok('S13 błąd 409 pokazany i stan odświeżony', err && top.includes('krok 1'), top);
  } catch (e) { ok('S13 wyjątek', false, e.message) }

  // ---- S14: wąski ekran (telefon) --------------------------------------------
  try {
    const v = await newGame({ num_players: 3, seed: 14 });
    await page.setViewportSize({ width: 390, height: 844 });
    await open(v.game_id);
    const sw = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
    ok('S14 brak poziomego przewijania na 390px', sw[0] <= sw[1] + 1, sw);
    const bw = await page.locator('svg.board').boundingBox();
    ok('S14 plansza widoczna', bw && bw.width > 300, JSON.stringify(bw));
    await page.screenshot({ path: '.playwright-mcp/e2e_mobile.png' });
    await page.setViewportSize({ width: 1440, height: 900 });
  } catch (e) { ok('S14 wyjątek', false, e.message) }

  // ---- S15: konsola ----------------------------------------------------------
  const unexpected = consoleErrors.filter((t) => !/status of 40[049]|Failed to load resource/.test(t));
  ok('S15 brak błędów JS w konsoli', unexpected.length === 0, unexpected.join(' | '));

  return { passed: R.filter((r) => r.ok).length, failed: R.filter((r) => !r.ok), all: R.map((r) => (r.ok ? '✓ ' : '✗ ') + r.name) };
}
