# AI for «Min beholdning»

Liten Cloudflare Worker som spør Claude hvilke matvarer brukeren har, enten fra et bilde av kjøleskapet eller skapet,
eller fra det brukeren sa inn med «Si hva du har». Svaret er en liste varer koblet til navnene appen kjenner, med nivå
(Mye/Litt/Tomt) eller antall når det ble sagt. Uten workeren tolker appen talen selv, enklere. Nøkkelen til Claude ligger bare her, aldri i appen. Bare brukere som er logget inn i appen
(Firebase-prosjektet `matglede-4dbc5`) kan bruke den.

## Slik slår du den på (ca. 10 min)

1. Lag en API-nøkkel på https://platform.claude.com (Settings → API keys).
2. Lag en gratis konto på https://dash.cloudflare.com.
3. I denne mappen:
   ```
   npm install
   npx wrangler login
   npx wrangler secret put ANTHROPIC_API_KEY   # lim inn nøkkelen
   npx wrangler deploy                          # skriver ut adressen, f.eks. https://matglede-bilde.<navn>.workers.dev
   ```
4. Lim adressen inn i `app/auth-config.js` som `window.MATGLEDE_AI_URL`.

Test av tokensjekken: `npm test`.

Pris: ett bilde koster rundt 10 øre og én taleinnlegging rundt 3–5 øre med Claude Opus 5.5 (`model` i `src/index.js`).
