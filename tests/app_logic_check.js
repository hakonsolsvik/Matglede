// Sjekker at appens JS-kobling (matchIng, toBase) gir samme svar som Python-koden for alle oppskriftslinjer.
// Kjøres av tests/test_core.py (AppJsTest) når node finnes.
const fs = require('fs');
const html = fs.readFileSync(require('path').join(__dirname, '..', 'app', 'index.html'), 'utf8'), dj = fs.readFileSync(require('path').join(__dirname, '..', 'app', 'data.js'), 'utf8');
const M = JSON.parse(dj.slice(dj.indexOf('{'), dj.lastIndexOf('}') + 1));
const a = html.indexOf('  matchIng = (name, unit) => {'), b = html.indexOf('  // Mengde -> ingrediensens');
const code = html.slice(a, b).trim().replace(/^matchIng = /, '').replace(/;\s*$/, '');
const ctx = { D: { M, ING: M.ingredients } };
const matchIng = (new Function('return ' + code)).call(ctx);
let n = 0, diff = [];
M.recipes.forEach(r => r.ing.forEach(i => { n++; const js = matchIng.call(ctx, i.n, i.u); if ((js || null) !== (i.slug || null)) diff.push([i.n, i.u, i.slug, js]); }));
console.log(n, 'linjer,', diff.length, 'avvik'); if (diff.length) console.log(diff.slice(0, 15));
const a2 = html.indexOf('  RU = {'), b2 = html.indexOf('  hydrate = i =>');
const chunk = html.slice(a2, b2);
const ru = chunk.slice(chunk.indexOf('{'), chunk.indexOf('};') + 1);
ctx.RU = (new Function('return ' + ru))();
const tb = chunk.slice(chunk.indexOf('toBase = ') + 9).trim().replace(/;\s*$/, '');
const toBase = (new Function('return ' + tb)).call(ctx);
let d2 = [];
M.recipes.forEach(r => r.ing.forEach(i => { const v = toBase(i.q, i.u, i.slug, i.n); const pv = i.base; if (!((v == null && pv == null) || (v != null && pv != null && Math.abs(v - pv) < 1e-6))) d2.push([i.n, i.q, i.u, i.slug, pv, v]); }));
console.log('base-avvik', d2.length); if (diff.length || d2.length) { console.log(d2.slice(0, 10)); process.exit(1); }
