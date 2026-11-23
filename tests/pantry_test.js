// Kjør: node tests/pantry_test.js
const assert = require('assert');
require('../app/pantry.js');
const P = globalThis.MatgledePantry;

assert.deepStrictEqual(P.parse('Jeg har to kilo poteter, en liter melk og soyasaus.'),
  [{ n: 'Poteter', amt: '2 kg' }, { n: 'Melk', amt: '1 l' }, { n: 'Soyasaus', amt: '' }]);
assert.deepStrictEqual(P.parse('ris 1 kg\nmel 2 kilo'), [{ n: 'Ris', amt: '1 kg' }, { n: 'Mel', amt: '2 kg' }]);
assert.deepStrictEqual(P.parse('tomater, 6 egg, en del havregryn'), [{ n: 'Tomater', amt: '' }, { n: 'Egg', amt: '6' }, { n: 'Havregryn', amt: 'en del' }]);

assert(P.same('Poteter', 'Potet'));
assert(P.same('kylling', 'Kyllingfilet'));
assert(P.same('ost', 'Revet ost'));
assert(P.same('pasta', 'Spaghetti'));
assert(!P.same('mel', 'Melk'));
assert(!P.same('løk', 'Hvitløk'));

const R = [
  { id: 'a', ing: [{ n: 'Potet' }, { n: 'Melk' }, { n: 'Smør' }, { n: 'Salt' }] },
  { id: 'b', ing: [{ n: 'Kjøttdeig' }, { n: 'Potet' }, { n: 'Løk' }] },
  { id: 'c', ing: [{ n: 'Ris' }, { n: 'Soyasaus' }, { n: 'Egg' }] },
  { id: 'd', ing: [{ n: 'Laks' }] }
];
const pantry = [{ id: 1, n: 'Poteter' }, { id: 2, n: 'Melk' }, { id: 3, n: 'Smør' }, { id: 4, n: 'Ris' }, { id: 5, n: 'Soyasaus' }];
const ranked = P.rank(R, pantry, i => [i.n]);
assert.deepStrictEqual(ranked.map(x => x.r.id), ['a', 'c', 'b']);
assert.strictEqual(ranked[0].ratio, 1); // salt teller ikke
assert.deepStrictEqual(P.week(ranked, 2).map(x => x.r.id), ['a', 'c']);
assert.deepStrictEqual(P.week(ranked, 3, ['a']).map(x => x.r.id), ['c', 'b']);
assert.deepStrictEqual(P.rank(R, [], i => [i.n]), []);
console.log('pantry ok');
assert(P.same('mel', 'Hvetemel'));
assert(P.same('melk', 'Lettmelk'));
assert(!P.same('melk', 'Kokosmelk'));

// Mengder: nivå for vanlige varer, antall for varer man teller
assert(P.counted('Egg') && P.counted('Tomater') && P.counted('Løk') && !P.counted('Melk') && !P.counted('Revet ost'));
assert.deepStrictEqual(P.fresh({ id: 1, n: 'Egg' }, '10'), { id: 1, n: 'Egg', count: 10 });
assert.deepStrictEqual(P.fresh({ id: 1, n: 'Egg' }), { id: 1, n: 'Egg', count: 6 });
assert.deepStrictEqual(P.fresh({ id: 2, n: 'Melk', pct: 50 }), { id: 2, n: 'Melk', lvl: 'mye' });
assert.strictEqual(P.level({ n: 'Melk', pct: 25 }), 'litt'); // gammel prosent
assert.strictEqual(P.level({ n: 'Melk', pct: 0 }), 'tomt');
assert.strictEqual(P.level(P.step({ id: 2, n: 'Melk', lvl: 'mye' }, -1)), 'litt');
assert.strictEqual(P.step({ id: 2, n: 'Melk', lvl: 'tomt' }, -1).lvl, 'tomt');
assert.strictEqual(P.step({ id: 1, n: 'Egg', count: 1 }, -1).count, 0);
assert.strictEqual(P.level({ n: 'Egg', count: 2 }), 'litt');
// «Litt» brukes opp først: ris på litt gjør at risretten velges før potetretten
const R2 = [{ id: 'pot', ing: [{ n: 'Potet' }, { n: 'Smør' }] }, { id: 'ris', ing: [{ n: 'Ris' }, { n: 'Smør' }] }];
const lowRice = [{ id: 1, n: 'Poteter', lvl: 'mye' }, { id: 2, n: 'Ris', lvl: 'litt' }, { id: 3, n: 'Smør', lvl: 'mye' }];
assert.deepStrictEqual(P.week(P.rank(R2, lowRice, i => [i.n]), 1).map(x => x.r.id), ['ris']);
console.log('mengder ok');

// Omtrentlige mengder: Mye = én pakke, Litt = en halv, og nedtrekk etter middag
const milk = { id: 9, n: 'Melk', lvl: 'litt' };
assert.strictEqual(P.have(milk, 1000), 500);
assert.strictEqual(P.have({ n: 'Melk', lvl: 'tomt' }, 1000), 0);
assert.strictEqual(P.have({ n: 'Soyasaus', lvl: 'mye' }, null), null);
assert.deepStrictEqual(P.use({ id: 9, n: 'Melk', lvl: 'mye' }, 400, 1000), { id: 9, n: 'Melk', lvl: 'litt', amt: 600 });
assert.deepStrictEqual(P.use({ id: 9, n: 'Melk', lvl: 'mye' }, 1500, 1000), { id: 9, n: 'Melk', lvl: 'tomt', amt: 0 });
assert.strictEqual(P.have(P.use({ id: 9, n: 'Melk', lvl: 'mye', amt: 1500 }, 1000, 1000), 1000), 500); // 1,5 l hjemme, 1 l brukt
assert.deepStrictEqual(P.use({ id: 1, n: 'Egg', count: 6 }, 2, null, 1), { id: 1, n: 'Egg', count: 4 });
assert.deepStrictEqual(P.step({ id: 9, n: 'Melk', lvl: 'litt', amt: 300 }, 1), { id: 9, n: 'Melk', lvl: 'mye' }); // eget valg nullstiller mengden
console.log('mengder ok');

// Tale: nivåer og kjente navn
assert.deepStrictEqual(P.parse('tom for melk, lite smør igjen, ris er nesten tom og masse pasta'),
  [{ n: 'Melk', amt: 'tomt' }, { n: 'Smør', amt: 'litt' }, { n: 'Ris', amt: 'litt' }, { n: 'Pasta', amt: 'mye' }]);
assert.deepStrictEqual(P.parse('havregryn er tomt'), [{ n: 'Havregryn', amt: 'tomt' }]);
assert.deepStrictEqual(P.fresh({ id: 1, n: 'Melk' }, 'tomt'), { id: 1, n: 'Melk', lvl: 'tomt' });
assert.deepStrictEqual(P.fresh({ id: 1, n: 'Egg' }, 'tomt'), { id: 1, n: 'Egg', count: 0 });
const KNOWN = ['Poteter', 'Gulrøtter', 'Løk', 'Rødløk', 'Kidneybønner', 'Hvite bønner'];
assert.strictEqual(P.canon('gulrot', KNOWN), 'Gulrøtter');
assert.strictEqual(P.canon('Potet', KNOWN), 'Poteter');
assert.strictEqual(P.canon('rødløk', KNOWN), 'Rødløk');
assert.strictEqual(P.canon('Tahini', KNOWN), 'Tahini');
assert(P.same('gulrot', 'Gulrøtter'));
console.log('tale ok');

// Popularitet: flest brukere først, standardrekkefølge under grensen og ved likt antall
assert.strictEqual(P.key('Poteter'), P.key('potet'));
assert.deepStrictEqual(P.byPop(['a', 'b', 'c', 'd'], x => x, { c: 5, d: 9, b: 2 }, 3), ['d', 'c', 'a', 'b']);
assert.deepStrictEqual(P.byPop(['a', 'b'], x => x, {}, 3), ['a', 'b']);
console.log('popularitet ok');
// Søndagskort: tegneseriebilde per vare
assert.deepStrictEqual(['Egg', 'Melk', 'Kokosmelk', 'Hvitløk', 'Rødløk', 'Revet ost', 'Mel', 'Hakkede tomater', 'Tomater', 'Ris', 'Paprikapulver', 'Noe rart'].map(P.art),
  ['🥚', '🥛', '🥥', '🧄', '🧅', '🧀', '🌾', '🥫', '🍅', '🍚', '🧂', '🛒']);
console.log('art ok');

// Tale i tilbudsavisen: det man sa -> tilbudet i avisen
const L = ['Grandiosa pizza Original, 575 g', 'Laksefilet 4 stk', 'Laks røkt 200 g', 'Lettmelk 1 l'];
assert.strictEqual(P.pick('laks', L), 2);
assert.strictEqual(P.pick('Laksefilet 4 stk', L), 1);
assert.strictEqual(P.pick('grandiosa', L), 0);
assert.strictEqual(P.pick('melk', L), 3);
assert.strictEqual(P.pick('brokkoli', L), -1);
console.log('pick ok');
