// Matlageret: tolker tale og tekst til varer, og finner retter som bruker det man har hjemme.
// Rene funksjoner uten tilstand, så de kan testes med node (tests/pantry_test.js).
(function (root) {
  var NUM = { 'en del': 'en del', en: 1, ett: 1, ei: 1, to: 2, tre: 3, fire: 4, fem: 5, seks: 6, sju: 7, syv: 7, 'åtte': 8, ni: 9, ti: 10, tolv: 12, halvannen: '1½', halv: '½', litt: 'litt', mye: 'mye', noe: 'noe' };
  var UNIT = { kilo: 'kg', kg: 'kg', gram: 'g', g: 'g', hekto: 'hg', liter: 'l', l: 'l', desiliter: 'dl', dl: 'dl', pakke: 'pk', pakker: 'pk', pakka: 'pk', pk: 'pk',
    pose: 'pose', poser: 'poser', boks: 'boks', bokser: 'bokser', stk: 'stk', stykk: 'stk', stykker: 'stk', flaske: 'flaske', flasker: 'flasker',
    glass: 'glass', brett: 'brett', kartong: 'kartong', kartonger: 'kartonger', beger: 'beger', bunt: 'bunt' };
  var NUMRE = '\\d+(?:[.,]\\d+)?|' + Object.keys(NUM).join('|');
  var AMT = '((?:' + NUMRE + ')(?:\\s+(?:' + Object.keys(UNIT).join('|') + ')(?![a-zæøå]))?)';
  var LEAD = new RegExp('^' + AMT + '\\s+(?:med\\s+|av\\s+)?(.+)$', 'i');
  var TRAIL = new RegExp('^(.+?)\\s+' + AMT + '$', 'i');

  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  function amount(a) {
    if (typeof NUM[a.toLowerCase()] === 'string') return NUM[a.toLowerCase()];
    return a.toLowerCase().split(/\s+/).map(function (w, i) { return i === 0 && NUM[w] != null ? String(NUM[w]) : UNIT[w] || w; }).join(' ');
  }
  // «Jeg har to kilo poteter, en liter melk og soyasaus» -> [{n:'Poteter', amt:'2 kg'}, ...]
  function parse(text) {
    return String(text || '').split(/\s*(?:,|;|\n|\.\s|\.$|\bog\b)\s*/i).map(function (x) {
      x = x.trim().replace(/^(?:(?:jeg|vi)\s+har|har|også|i tillegg)\s+/i, '').replace(/[.!?]+$/, '').trim();
      if (!x) return null;
      var m, n = x, amt = '';
      // «tom for melk», «ikke mer ris», «melk er tom», «lite smør igjen»
      if ((m = x.match(/^(?:(?:er\s+)?tomt?\s+for|ikke\s+(?:noe|mer)(?:\s+igjen)?(?:\s+av)?|ingen)\s+(.+)$/i)) || (m = x.match(/^(.+?)\s+er\s+(?:helt\s+)?tomt?$/i))) { amt = 'tomt'; n = m[1]; }
      else if ((m = x.match(/^(?:lite|litt|nesten\s+tom(?:t)?\s+for)\s+(?:igjen\s+)?(?:av\s+)?(.+?)(?:\s+igjen)?$/i)) || (m = x.match(/^(.+?)\s+er\s+(?:snart|nesten)\s+tomt?$/i))) { amt = 'litt'; n = m[1]; }
      else if ((m = x.match(/^(?:mye|masse|nok)\s+(?:av\s+)?(.+)$/i))) { amt = 'mye'; n = m[1]; }
      else if ((m = x.match(LEAD))) { amt = amount(m[1]); n = m[2]; }
      else if ((m = x.match(TRAIL))) { n = m[1]; amt = amount(m[2]); }
      n = n.trim();
      return n ? { n: cap(n), amt: amt } : null;
    }).filter(Boolean);
  }

  // Grov ordstamme, lik på begge sider: «poteter» og «potet» blir begge «potet»
  function stem(w) { var s; while (w.length > 4 && (s = w.replace(/(ene|ane|er|en|et|a|r)$/, '')) !== w) w = s; return w; }
  // Uregelrette flertall: «gulrøtter» -> «gulrot»
  var IRREG = { 'gulrøtt': 'gulrot', 'bønn': 'bønne' };
  function words(s) { return String(s || '').toLowerCase().replace(/\(.*?\)/g, ' ').split(/[^a-zæøå]+/).filter(Boolean).map(function (w) { w = stem(w); return IRREG[w] || w; }); }
  // Samme vare med kjent navn («poteter» -> «Poteter», «gulrot» -> «Gulrøtter»), ellers navnet som det er
  function canon(n, known) { var key = words(n).join(' '); for (var i = 0; i < known.length; i++) if (words(known[i]).join(' ') === key) return known[i]; return n; }
  // Sammensatte ord: «kylling» i «kyllingfilet», «mel» i «hvetemel», «melk» i «lettmelk», men ikke «mel» i «melk».
  // OTHER er sammensetninger som er en helt annen vare.
  var OTHER = /^(hvitløk|kokosmelk)$/;
  function wordHit(a, b) { return a === b || (a.length >= 4 && b.indexOf(a) === 0) || (a.length >= 3 && b.slice(-a.length) === a && !OTHER.test(b)); }
  var SYN = { pasta: ['spaghetti', 'spagetti', 'tagliatelle', 'makaroni', 'penne', 'fusilli', 'lasagneplat'] };
  function same(have, need) {
    var hw = words(have), nw = words(need);
    if (!hw.length || !nw.length) return false;
    if (hw.every(function (h) { return nw.some(function (n) { return wordHit(h, n); }); })) return true;
    return (SYN[String(have).trim().toLowerCase()] || []).some(function (s) { return nw.some(function (n) { return n.indexOf(s) === 0; }); });
  }
  // Varen i matlageret som dekker ingrediensen, eller null
  function find(pantry, names) {
    for (var i = 0; i < pantry.length; i++) for (var j = 0; j < names.length; j++) if (same(pantry[i].n, names[j])) return pantry[i];
    return null;
  }
  // Tilbudet i avisen som passer det brukeren sa: samme navn, ellers det korteste navnet som inneholder alle ordene. -1 = ingen.
  function pick(n, labels) {
    var key = words(n).join(' '), best = -1;
    if (!key) return -1;
    for (var i = 0; i < labels.length; i++) {
      if (words(labels[i]).join(' ') === key) return i;
      if (same(n, labels[i]) && (best < 0 || labels[i].length < labels[best].length)) best = i;
    }
    return best;
  }
  // Salt og pepper har alle, så de teller ikke
  var STAPLE = /^(salt|pepper|vann)$/i;

  // Retter sortert etter hvor mye av matlageret de bruker. ingNames(i) gir navnene en ingrediens kan ha.
  function rank(recipes, pantry, ingNames) {
    if (!pantry.length) return [];
    return recipes.map(function (r) {
      var have = [], miss = [];
      r.ing.forEach(function (i) {
        var names = ingNames(i);
        if (names.some(function (n) { return STAPLE.test(n); })) return;
        var p = find(pantry, names);
        if (p) have.push({ i: i, p: p }); else miss.push(i);
      });
      var total = have.length + miss.length;
      return { r: r, have: have, miss: miss, ratio: total ? have.length / total : 0 };
    }).filter(function (x) { return x.have.length; })
      .sort(function (a, b) { return score(b) - score(a); });
  }
  function score(x) { return x.have.length + x.ratio * 4 + x.have.filter(function (h) { return level(h.p) === 'litt'; }).length * 2; }

  // Mengde: varer man teller (egg, løk …) har antall, resten har nivå Mye, Litt eller Tomt.
  // Eldre lagrede varer har pct (0–100) og gjøres om her.
  var COUNTED = /^(egg|løk|rødløk|sjalottløk|paprik|sitron|lime|agurk|avokado|tomat|eple|epl|banan|purre|squash|appelsin)$/;
  var LEVELS = ['tomt', 'litt', 'mye'];
  function counted(n) { var w = words(n); return w.length === 1 && COUNTED.test(w[0]); }
  function level(x) {
    if (counted(x.n)) { var c = qty(x); return c === 0 ? 'tomt' : c <= 2 ? 'litt' : 'mye'; }
    return x.lvl || (x.pct === 0 ? 'tomt' : x.pct != null && x.pct < 50 ? 'litt' : 'mye');
  }
  function qty(x) { return x.count != null ? x.count : x.pct === 0 ? 0 : /^egg/i.test(x.n) ? 6 : 2; }
  // Bare id, navn og én mengde lagres (Firestore godtar ikke undefined)
  function make(x, m) { var o = { id: x.id, n: x.n }; for (var k in m) o[k] = m[k]; return o; }
  // Ett steg opp (d=1) eller ned (d=-1). Returnerer en ny vare.
  function step(x, d) {
    if (counted(x.n)) return make(x, { count: Math.max(0, Math.min(99, qty(x) + d)) });
    return make(x, { lvl: LEVELS[Math.max(0, Math.min(2, LEVELS.indexOf(level(x)) + d))] });
  }
  // Ny vare eller lagt inn på nytt: antallet eller nivået som ble sagt («litt», «tomt»), ellers Mye
  function fresh(x, amt) {
    var c = parseInt(amt, 10), lv = LEVELS.indexOf(amt) >= 0 ? amt : 'mye';
    if (!counted(x.n)) return make(x, { lvl: lv });
    return make(x, { count: c > 0 ? c : lv === 'tomt' ? 0 : lv === 'litt' ? 1 : qty({ n: x.n }) });
  }

  // Omtrent hvor mye som er hjemme, i varens basisenhet (g, ml, stk). pack = en vanlig pakke, perStk = basisenhet per stk.
  // Til appen vet bedre (amt lagres når en dag er laget) er Mye én pakke og Litt en halv. null = ukjent.
  function have(x, pack, perStk) {
    if (counted(x.n)) return perStk ? qty(x) * perStk : null;
    if (x.amt != null) return x.amt;
    var l = level(x); return l === 'tomt' ? 0 : pack ? (l === 'mye' ? pack : pack / 2) : null;
  }
  // Varen etter at «used» er brukt opp. Nivået følger mengden: under ¾ pakke er Litt.
  function use(x, used, pack, perStk) {
    var h = have(x, pack, perStk); if (h == null) return x;
    var left = Math.max(0, h - used);
    if (counted(x.n)) return make(x, { count: Math.max(0, Math.round(left / perStk)) });
    return make(x, { lvl: left <= 0 ? 'tomt' : left < pack * 0.75 ? 'litt' : 'mye', amt: Math.round(left) });
  }

  // Ukeplan: én rett per dag, grådig etter flest varer fra matlageret som ingen rett i planen bruker ennå.
  // Varer på «Litt» teller mer, så de brukes opp først.
  function week(ranked, n, skip) {
    var used = {}, out = [], left = ranked.filter(function (x) { return !(skip || []).includes(x.r.id); });
    while (out.length < n && left.length) {
      var best = 0, bestV = -1;
      left.forEach(function (x, k) {
        var v = x.have.length + x.ratio * 4;
        x.have.forEach(function (h) { if (!used[h.p.id]) v += level(h.p) === 'litt' ? 6 : 3; });
        if (v > bestV) { bestV = v; best = k; }
      });
      var pick = left.splice(best, 1)[0];
      pick.have.forEach(function (h) { used[h.p.id] = true; });
      out.push(pick);
    }
    return out;
  }

  // Popularitet: nøkkelen en vare telles under, lik for «Poteter» og «potet»
  function key(n) { return words(n).join(' ').slice(0, 60); }
  // Mest brukte først. Under min brukere teller ikke, så standardrekkefølgen gjelder til nok brukere er med.
  function byPop(list, k, counts, min) {
    var c = function (x) { var n = (counts || {})[k(x)] || 0; return n >= min ? n : 0; };
    return list.map(function (x, i) { return [x, c(x), i]; }).sort(function (a, b) { return b[1] - a[1] || a[2] - b[2]; }).map(function (a) { return a[0]; });
  }

  // Tegneseriebilde (emoji) av en vare til søndagskortene. Mer spesifikke treff først («kokosmelk» før «melk»).
  var ART = [[/kokosmelk/, '🥥'], [/hvitløk/, '🧄'], [/løk|purre/, '🧅'], [/mais/, '🌽'], [/paprikapulver|krydder|kanel|salt|pepper/, '🧂'],
    [/hakkede tomater|tomatpur|bønne|kikert|linser|tunfisk|buljong|ketchup/, '🥫'], [/potet/, '🥔'], [/gulr/, '🥕'], [/paprika/, '🫑'],
    [/tomat/, '🍅'], [/agurk|squash/, '🥒'], [/brokkoli|grønnsak/, '🥦'], [/sitron|lime/, '🍋'], [/ingefær/, '🫚'], [/eple/, '🍎'],
    [/banan/, '🍌'], [/avokado/, '🥑'], [/appelsin/, '🍊'], [/tortilla|lefse/, '🫓'], [/melk|fløte|rømme|yoghurt/, '🥛'], [/^egg|\begg\b/, '🥚'],
    [/smør/, '🧈'], [/ost\b/, '🧀'], [/erter/, '🫛'], [/ris\b/, '🍚'], [/nudler/, '🍜'], [/pasta|spaghetti|lasagne|makaroni|penne/, '🍝'],
    [/mel\b|havre|gryn|quinoa|couscous|bulgur|gjær|bakepulver/, '🌾'], [/sukker/, '🍬'], [/olje/, '🫒'], [/honning/, '🍯'], [/saus|sennep/, '🍶'],
    [/kylling/, '🍗'], [/reke/, '🦐'], [/laks|fisk|torsk|sei/, '🐟'], [/kjøtt|deig|bacon|pølse|biff/, '🥩'], [/brød/, '🍞']];
  function art(n) { n = String(n || '').toLowerCase(); for (var i = 0; i < ART.length; i++) if (ART[i][0].test(n)) return ART[i][1]; return '🛒'; }

  // Før-prisen i tilbudsavisen (lest av AI) er butikkens vanlige pris akkurat nå. Den legges til varene for kjeden
  // i data.js, og erstatter gamle (stale) priser der, så vanlig pris på oppskrifter og handleliste blir fersk.
  var COOP = { EXTRA: 1, MEGA: 1, PRIX: 1, OBS: 1, MARKED: 1 };
  function flyerPrices(ings, chains, stores) {
    var n = 0;
    (stores || []).forEach(function (x) {
      var ch = COOP[x.code] ? 'COOP' : x.code;
      if (!x.fromFlyer || chains.indexOf(ch) < 0) return;
      x.offers.forEach(function (o) {
        var ing = ings[o.ing];
        if (!ing || !o.size || !(o.before > o.price)) return;
        var prods = ing.products = ing.products || {};
        prods[ch] = (prods[ch] || []).filter(function (p) { return !p.stale && p.name !== o.name; });
        prods[ch].push({ name: o.name, size: o.size, price: o.before, stale: false, avis: true });
        n++;
      });
    });
    return n;
  }

  root.MatgledePantry = { flyerPrices: flyerPrices, art: art, key: key, byPop: byPop, parse: parse, same: same, find: find, rank: rank, week: week, canon: canon, pick: pick, counted: counted, level: level, qty: qty, step: step, fresh: fresh, have: have, use: use };
})(typeof window !== 'undefined' ? window : globalThis);
