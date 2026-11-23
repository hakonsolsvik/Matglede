// Sjekker at appens kobling for egne oppskrifter (slugOf/toBase i index.html) gir samme svar som Python
// for alle ingredienslinjene i Matgledes oppskrifter. Kjør: node tests/egne_oppskrifter_test.js
const fs = require('fs'), path = require('path'), assert = require('assert');
global.window = {}; require(path.join(__dirname, '../app/data.js'));
const M = window.MATGLEDE_DATA, html = fs.readFileSync(path.join(__dirname, '../app/index.html'), 'utf8');
const o = { D: { M, R: M.recipes, ING: M.ingredients } };
for (const n of ['ALIAS', 'slugOf', 'RU', 'toBase']) {
  const m = html.match(new RegExp('\\n  ' + n + ' = ([\\s\\S]*?);\\n  (?://|[a-zA-Z_]+ = )'));
  o[n] = eval('(function(){ return ' + m[1].replace(/this\./g, 'o.') + '; })')();
}
let n = 0;
for (const r of M.recipes) for (const i of r.ing) {
  if (!i.slug) continue;
  assert.strictEqual(o.slugOf(i.n, i.u), i.slug, `${r.id}: ${i.n}`);
  const b = o.toBase(i.q, i.u, i.slug, i.n);
  assert.ok(i.base == null ? b == null : Math.abs(b - i.base) < 1e-6, `${r.id}: ${i.n} ${b} != ${i.base}`); n++;
}
for (const [name, slug] of [['Melk', 'melk'], ['Spagetti', 'spaghetti'], ['Kyllingbryst', 'kyllingfilet'], ['Torsk', 'torskefilet'], ['Purre', 'purre'], ['Sukker', 'sukker'], ['Fiskekraft', 'kraft']])
  assert.strictEqual(o.slugOf(name), slug, name);
console.log(`egne oppskrifter ok (${n} linjer)`);
{ const m = html.match(/\n  partsOf = ([\s\S]*?);\n  RU = /); o.partsOf = eval('(function(){ return ' + m[1].replace(/this\./g, 'o.') + '; })')();
  assert.deepStrictEqual(o.partsOf('Salt og pepper', '', null), [['Salt', 'salt'], ['Pepper', 'pepper']]);
  assert.deepStrictEqual(o.partsOf('Salt og pepper', 'ts', 1), [['Salt og pepper', 'salt']]);
  assert.deepStrictEqual(o.partsOf('Sitronsaft', '', null), [['Sitronsaft', 'sitron']]);
  assert.strictEqual(o.slugOf('Hvitløksfedd', 'stk'), 'hvitlok');
  console.log('salt og pepper ok'); }
