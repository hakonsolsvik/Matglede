// Tester tokensjekken med en egen nøkkel. Kjør: node test.js (Node 20+)
import assert from 'assert';
import { verifyToken } from './src/index.js';

const { publicKey, privateKey } = await crypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
const jwk = { ...(await crypto.subtle.exportKey('jwk', publicKey)), kid: 'k1' };
const enc = o => Buffer.from(JSON.stringify(o)).toString('base64url');
const now = Math.floor(Date.now() / 1000);
async function token(body, kid = 'k1') {
  const hp = enc({ alg: 'RS256', kid }) + '.' + enc(body);
  return hp + '.' + Buffer.from(await crypto.subtle.sign('RSASSA-PKCS1-v1_5', privateKey, new TextEncoder().encode(hp))).toString('base64url');
}
const good = { aud: 'p1', iss: 'https://securetoken.google.com/p1', sub: 'u1', iat: now - 10, exp: now + 3600 };
const keys = async () => [jwk];
assert.strictEqual(await verifyToken(await token(good), 'p1', keys), 'u1');
await assert.rejects(verifyToken(await token({ ...good, aud: 'other' }), 'p1', keys));
await assert.rejects(verifyToken(await token({ ...good, exp: now - 1 }), 'p1', keys));
await assert.rejects(verifyToken(await token(good, 'nope'), 'p1', keys));
const t = await token(good); await assert.rejects(verifyToken(t.slice(0, -4) + 'AAAA', 'p1', keys));
console.log('token ok');
