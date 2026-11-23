# AI for «Min beholdning», «Mine oppskrifter» og tilbudsavisene

Liten Cloudflare Worker som spør Claude hvilke matvarer brukeren har, enten fra et bilde av kjøleskapet eller skapet,
eller fra det brukeren sa inn med «Si hva du har». Svaret er en liste varer koblet til navnene appen kjenner, med nivå
(Mye/Litt/Tomt) eller antall når det ble sagt. Den leser også oppskrifter fra bilder (bok, lapp eller skjerm) til «Mine oppskrifter»: navn, porsjoner, tid, ingredienser og steg,
som brukeren ser over og retter før lagring. I tilbudsavisen kobler den det brukeren sier til avisens tilbud. Uten workeren tolker appen talen selv, enklere. Etter endringer i `src/index.js`: kjør `npx wrangler deploy` på nytt. Nøkkelen til Claude ligger bare her, aldri i appen. Bare brukere som er logget inn i appen
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

Pris: ett bilde koster rundt 10 øre én taleinnlegging rundt 3–5 øre og én oppskrift fra bilde rundt 15–25 øre med Claude Opus 5.5 (`model` i `src/index.js`).
