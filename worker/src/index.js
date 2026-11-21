// Bildegjenkjenning for «Min beholdning»: tar et bilde av kjøleskap eller skap og svarer med en liste varer.
// Nøkkelen til Claude ligger bare her (secret ANTHROPIC_API_KEY), aldri i appen.
// Bare innloggede brukere i Firebase-prosjektet kan bruke den: appen sender Firebase ID-token som Bearer.
import Anthropic from '@anthropic-ai/sdk';

const JWKS_URL = 'https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com';
const MAX_IMAGE = 4_000_000; // base64-tegn, appen sender ca. 200–400 kB

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
  properties: { items: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['n'], properties: { n: { type: 'string' } } } } }
};
const PROMPT = 'Bildet viser et kjøleskap, et tørrskap eller en matbod. List matvarene du ser som kan brukes til middag: ' +
  'grønnsaker, kjøtt, fisk, meieri (melk, ost, smør, rømme), egg, tørrvarer (ris, pasta, mel, havregryn), hermetikk, sauser og krydder som soyasaus. ' +
  'Bruk korte, vanlige norske navn uten merke, f.eks. «Melk», «Revet ost», «Soyasaus», «Hakkede tomater». Én linje per vare, ingen duplikater. ' +
  'Ta bare med det du faktisk ser. Er du usikker på en vare, la den være ute.';

export default {
  async fetch(req, env) {
    const origin = req.headers.get('Origin') || '';
    const allowed = env.ALLOWED_ORIGINS.split(',').includes(origin);
    const cors = { 'Access-Control-Allow-Origin': allowed ? origin : 'null', 'Access-Control-Allow-Headers': 'Authorization, Content-Type', 'Access-Control-Allow-Methods': 'POST', Vary: 'Origin' };
    const reply = (status, data) => new Response(JSON.stringify(data), { status, headers: { ...cors, 'Content-Type': 'application/json' } });
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (req.method !== 'POST' || !allowed) return reply(405, { error: 'not allowed' });

    try { await verifyToken((req.headers.get('Authorization') || '').replace(/^Bearer\s+/i, ''), env.FIREBASE_PROJECT_ID); }
    catch { return reply(401, { error: 'login required' }); }

    let image;
    try { image = (await req.json()).image; } catch { return reply(400, { error: 'bad json' }); }
    if (typeof image !== 'string' || !image || image.length > MAX_IMAGE || !/^[A-Za-z0-9+/=]+$/.test(image)) return reply(400, { error: 'bad image' });

    const client = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY });
    try {
      const msg = await client.beta.messages.create({
        model: 'claude-opus-5-5',
        max_tokens: 4000,
        betas: ['server-side-fallback-2026-07-01'],
        fallbacks: 'default',
        output_config: { effort: 'low', format: { type: 'json_schema', schema: SCHEMA } },
        messages: [{ role: 'user', content: [
          { type: 'image', source: { type: 'base64', media_type: 'image/jpeg', data: image } },
          { type: 'text', text: PROMPT }
        ] }]
      });
      if (msg.stop_reason === 'refusal') return reply(200, { items: [] });
      const text = msg.content.find(b => b.type === 'text');
      const items = text ? JSON.parse(text.text).items : [];
      return reply(200, { items: items.slice(0, 80).map(x => ({ n: String(x.n).slice(0, 60) })) });
    } catch (e) {
      console.error(e);
      return reply(502, { error: 'ai failed' });
    }
  }
};
