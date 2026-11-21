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
      var m = x.match(LEAD), n = x, amt = '';
      if (m) { amt = amount(m[1]); n = m[2]; }
      else if ((m = x.match(TRAIL))) { n = m[1]; amt = amount(m[2]); }
      n = n.trim();
      return n ? { n: cap(n), amt: amt } : null;
    }).filter(Boolean);
  }

  // Grov ordstamme, lik på begge sider: «poteter» og «potet» blir begge «potet»
  function stem(w) { var s; while (w.length > 4 && (s = w.replace(/(ene|ane|er|en|et|a|r)$/, '')) !== w) w = s; return w; }
  function words(s) { return String(s || '').toLowerCase().replace(/\(.*?\)/g, ' ').split(/[^a-zæøå]+/).filter(Boolean).map(stem); }
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
      .sort(function (a, b) { return (b.have.length + b.ratio * 4) - (a.have.length + a.ratio * 4); });
  }

  // Ukeplan: én rett per dag, grådig etter flest varer fra matlageret som ingen rett i planen bruker ennå
  function week(ranked, n, skip) {
    var used = {}, out = [], left = ranked.filter(function (x) { return !(skip || []).includes(x.r.id); });
    while (out.length < n && left.length) {
      var best = 0, bestV = -1;
      left.forEach(function (x, k) {
        var fresh = x.have.filter(function (h) { return !used[h.p.id]; }).length, v = fresh * 3 + x.have.length + x.ratio * 4;
        if (v > bestV) { bestV = v; best = k; }
      });
      var pick = left.splice(best, 1)[0];
      pick.have.forEach(function (h) { used[h.p.id] = true; });
      out.push(pick);
    }
    return out;
  }

  root.MatgledePantry = { parse: parse, same: same, find: find, rank: rank, week: week };
})(typeof window !== 'undefined' ? window : globalThis);
