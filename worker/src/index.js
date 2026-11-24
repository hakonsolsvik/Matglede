// AI for «Min beholdning»: tolker et bilde av kjøleskap/skap eller det brukeren sa, og svarer med en liste varer.
// Og for «Mine oppskrifter»: leser en oppskrift fra et bilde (bok, lapp, skjerm) og svarer med navn, ingredienser og steg.
// Nøkkelen til Claude ligger bare her (secret ANTHROPIC_API_KEY), aldri i appen.
// Bare innloggede brukere i Firebase-prosjektet kan bruke den: appen sender Firebase ID-token som Bearer.
import Anthropic from '@anthropic-ai/sdk';

const JWKS_URL = 'https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com';
const MAX_IMAGE = 4_000_000; // base64-tegn, appen sender ca. 200–400 kB
const DAILY_LIMIT = 60; // AI-kall per bruker per døgn, så én bruker eller bot ikke kan kjøre opp regningen

// Teller kall per bruker per dag (norsk dato) i KV. Gir false når dagens kvote er brukt opp.
// shortcut: KV er ikke atomisk, så samtidige kall kan slippe et par over grensen; bytt til Durable Object hvis det blir et problem.
export async function underLimit(kv, uid, limit = DAILY_LIMIT, now = new Date()) {
  const key = uid + ':' + now.toLocaleDateString('sv-SE', { timeZone: 'Europe/Oslo' });
  const n = +(await kv.get(key)) || 0;
  if (n >= limit) return false;
  await kv.put(key, String(n + 1), { expirationTtl: 2 * 86400 });
  return true;
}

let jwks = null, jwksAt = 0;
async function googleKeys() {
  if (!jwks || Date.now() - jwksAt > 3600_000) { jwks = (await (await fetch(JWKS_URL)).json()).keys; jwksAt = Date.now(); }
  return jwks;
}
const b64url = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0));
const json = s => JSON.parse(new TextDecoder().decode(b64url(s)));

// Sjekker Firebase ID-token (RS256) og returnerer bruker-id, eller kaster
export async function verifyToken(token, projectId, keys = googleKeys, now = Date.now() / 1000) {
  const [h, p, sig] = String(token || '').split('.');
  if (!sig) throw new Error('bad token');
  const head = json(h), body = json(p);
  const jwk = (await keys()).find(k => k.kid === head.kid);
  if (head.alg !== 'RS256' || !jwk) throw new Error('unknown key');
  const key = await crypto.subtle.importKey('jwk', jwk, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
  if (!await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, b64url(sig), new TextEncoder().encode(h + '.' + p))) throw new Error('bad signature');
  if (body.aud !== projectId || body.iss !== 'https://securetoken.google.com/' + projectId) throw new Error('wrong project');
  if (!(body.exp > now) || !(body.iat <= now + 300) || !body.sub) throw new Error('expired');
  return body.sub;
}

const SCHEMA = {
  type: 'object', additionalProperties: false, required: ['items'],
  properties: { items: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['n', 'lvl', 'count'], properties: {
    n: { type: 'string' },
    lvl: { type: 'string', enum: ['mye', 'litt', 'tomt', ''] },
    count: { type: 'integer' }
  } } } }
};
const FIELDS = 'For hver vare: n = navnet. lvl = «litt» hvis det er lite igjen, «tomt» hvis varen er tom, «mye» hvis det er sagt at det er mye, ellers tom streng. ' +
  'count = antall hvis et antall er sagt (f.eks. 10 egg), ellers 0.';
const TALK = (text, known) => 'Brukeren har sagt hvilke matvarer de har hjemme. Teksten kommer fra talegjenkjenning på norsk og kan ha feilhørte ord, ' +
  'fyllord og omtaler av mengde. Finn varene som ble ment. Bruk navnet fra listen over kjente varer når varen finnes der (også når det ble sagt i entall/flertall ' +
  'eller med et annet ord for det samme), ellers et kort, vanlig norsk navn uten merke. Ikke ta med ting som ikke er mat. ' + FIELDS +
  '\n\nKjente varer: ' + known.join(', ') + '\n\nDet som ble sagt: «' + text + '»';
// Tilbudsavisen: brukeren leser avisen og sier hva de vil kjøpe. n må være et navn fra lista over tilbud.
const SHOP = (text, offers) => 'Brukeren leser ukas tilbudsavis og sier hvilke varer de vil legge i handlelisten. Teksten kommer fra talegjenkjenning ' +
  'på norsk og kan ha feilhørte ord og fyllord. For hver vare som ble ment: n = navnet nøyaktig slik det står i lista over tilbud når varen finnes der ' +
  '(også når det ble sagt kortere, i entall/flertall eller med merket), ellers et kort, vanlig norsk navn. count = antall hvis et antall er sagt, ellers 0. lvl = tom streng.' +
  '\n\nTilbud i avisen:\n' + offers.join('\n') + '\n\nDet som ble sagt: «' + text + '»';
const PROMPT = 'Bildet viser et kjøleskap, et tørrskap eller en matbod. List matvarene du ser som kan brukes til middag: ' +
  'grønnsaker, kjøtt, fisk, meieri (melk, ost, smør, rømme), egg, tørrvarer (ris, pasta, mel, havregryn), hermetikk, sauser og krydder som soyasaus. ' +
  'Bruk korte, vanlige norske navn uten merke, f.eks. «Melk», «Revet ost», «Soyasaus», «Hakkede tomater». Én linje per vare, ingen duplikater. ' +
  'Ta bare med det du faktisk ser. Er du usikker på en vare, la den være ute. ' + FIELDS;

const UNITS = ['', 'g', 'kg', 'dl', 'l', 'ml', 'ss', 'ts', 'stk', 'pk', 'boks', 'fedd', 'klype', 'neve', 'skive'];
const RECIPE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['recipe'],
  properties: { recipe: { type: 'object', additionalProperties: false, required: ['name', 'servings', 'time', 'ing', 'steps'], properties: {
    name: { type: 'string' }, servings: { type: 'integer' }, time: { type: 'integer' },
    ing: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['n', 'q', 'u'], properties: {
      n: { type: 'string' }, q: { type: 'number' }, u: { type: 'string', enum: UNITS } } } },
    steps: { type: 'array', items: { type: 'string' } }
  } } }
};
const RECIPE_PROMPT = 'Bildet viser en matoppskrift, f.eks. fra en kokebok, en håndskrevet lapp eller en skjerm. Les av oppskriften og skriv den på norsk bokmål. ' +
  'name = navnet på retten. servings = antall porsjoner (4 hvis det ikke står). time = omtrent hvor mange minutter det tar, 0 hvis det ikke går an å anslå. ' +
  'ing = ingrediensene i rekkefølge: n = kort navn uten mengde (f.eks. «Kjøttdeig», «Hakkede tomater»), q = mengden som tall (0,5 for en halv, 0 hvis ingen mengde står), ' +
  'u = enheten, en av: ' + UNITS.filter(Boolean).join(', ') + ', eller tom streng. Gjør om ord som «spiseskje» til ss, «teskje» til ts og «stykk» til stk. ' +
  'steps = fremgangsmåten som korte steg, ett per punkt, med teksten slik den står. Ikke finn på noe som ikke står på bildet. ' +
  'Står det ingen oppskrift på bildet, svar med tomt navn og tomme lister.';

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const allowed = env.ALLOWED_ORIGINS.split(',').includes(origin);
    const cors = { 'Access-Control-Allow-Origin': allowed ? origin : 'null', 'Access-Control-Allow-Headers': 'Authorization, Content-Type', 'Access-Control-Allow-Methods': 'POST', Vary: 'Origin' };
    const reply = (status, data) => new Response(JSON.stringify(data), { status, headers: { ...cors, 'Content-Type': 'application/json' } });
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (req.method !== 'POST' || !allowed) return reply(405, { error: 'not allowed' });

    if (+req.headers.get('Content-Length') > MAX_IMAGE + 100_000) return reply(413, { error: 'too large' }); // stopp store kall før JSON leses inn
    let uid;
    try { uid = await verifyToken((req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, ''), env.FIREBASE_PROJECT_ID); }
    catch { return reply(401, { error: 'login required' }); }
    if (!await underLimit(env.LIMITS, uid, +env.DAILY_LIMIT || DAILY_LIMIT)) return reply(429, { error: 'daily limit' });

    let body;
    try { body = await req.json(); } catch { return reply(400, { error: 'bad json' }); }
    let content, schema = SCHEMA;
    if (typeof body.recipe === 'string') {
      // Oppskrift fra bilde
      const image = body.recipe;
      if (!image || image.length > MAX_IMAGE || !/^[A-Za-z0-9+/=]+$/.test(image)) return reply(400, { error: 'bad image' });
      content = [{ type: 'image', source: { type: 'base64', media_type: 'image/jpeg', data: image } }, { type: 'text', text: RECIPE_PROMPT }];
      schema = RECIPE_SCHEMA;
    } else if (typeof body.text === 'string') {
      // Tale: teksten fra talegjenkjenningen og navnene appen kjenner fra før
      const text = body.text.trim().slice(0, 2000);
      const known = (Array.isArray(body.known) ? body.known : []).filter(k => typeof k === 'string').map(k => k.slice(0, 60)).slice(0, 400);
      if (!text) return reply(400, { error: 'empty text' });
      const offers = Array.isArray(body.offers) ? body.offers.filter(k => typeof k === 'string').map(k => k.slice(0, 80)).slice(0, 400) : null;
      content = [{ type: 'text', text: offers ? SHOP(text, offers) : TALK(text, known) }];
    } else {
      const image = body.image;
      if (typeof image !== 'string' || !image || image.length > MAX_IMAGE || !/^[A-Za-z0-9+/=]+$/.test(image)) return reply(400, { error: 'bad image' });
      content = [{ type: 'image', source: { type: 'base64', media_type: 'image/jpeg', data: image } }, { type: 'text', text: PROMPT }];
    }

    const client = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });
    try {
      const msg = await client.beta.messages.create({
        model: 'claude-opus-5-5',
        max_tokens: 4000,
        betas: ['server-side-fallback-2026-07-01'],
        fallbacks: 'default',
        output_config: { effort: 'low', format: { type: 'json_schema', schema } },
        messages: [{ role: 'user', content }]
      });
      if (msg.stop_reason === 'refusal') return reply(200, schema === SCHEMA ? { items: [] } : { recipe: null });
      const text = msg.content.find(b => b.type === 'text');
      if (schema === RECIPE_SCHEMA) return reply(200, { recipe: text ? JSON.parse(text.text).recipe : null });
      const items = text ? JSON.parse(text.text).items : [];
      return reply(200, { items: items.slice(0, 80).map(x => ({ n: String(x.n).slice(0, 80), lvl: x.lvl || '', count: Number.isInteger(x.count) ? x.count : 0 })) });
    } catch (e) {
      console.error(e);
      return reply(502, { error: 'ai failed' });
    }
  }
};
