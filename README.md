# Matglede: varedatabase for oppskrifter og handleliste

Prototype på databasen bak oppskriftsappen. Brukeren legger middager i ukeplanen,
og appen lager en handleliste med ekte varer hos Oda, Kiwi, Meny, Rema 1000, Coop,
Spar og Joker.

Produktdataene kommer fra [Kassalapp API](https://kassal.app/api), ikke fra skraping av
oda.no. Odas bruksvilkår forbyr kopiering av innholdet deres uten tillatelse.

## Datamodell

```
oppskrift ──< oppskrift_ingrediens >── ingrediens ──< ingrediens_produkt >── produkt ──< tilbud (pris per kjede)
                                            ^                                                   │
ukeplan ──< ukeplan_middag ── oppskrift     │                                                 kjede
                                            └── handlelisten summerer her og velger produkt per kjede
```

| Tabell | Hva den er |
|---|---|
| `ingredient` | Generisk vare slik oppskriften sier det ("Hakkede tomater"), med basisenhet (g/ml/stk), søkeord, ord som må være med, ord som utelukker et produkt og kategorihint. |
| `product` | Et fysisk produkt. Samme EAN betyr samme produkt i alle kjeder. Noen Oda-varer mangler EAN og får nøkkel `kassal:<id>`. |
| `offer` | Pris, enhetspris, lenke og prisdato for et produkt i en kjede. |
| `ingredient_product` | Kobling med poengsum. `auto` fra matcheren, `verified` når et menneske har godkjent, `rejected` når den er feil. |
| `recipe`, `recipe_ingredient` | Oppskrift med mengde og enhet (g, kg, ml, dl, l, ss, ts, stk). |
| `meal_plan`, `meal_plan_entry` | Ukeplanen: hvilken middag hvilken dag og for hvor mange. |

Skillet mellom ingrediens og produkt gjør at handlelisten fungerer i alle kjeder, også når
kjedene har egne merker (First Price, Rema 1000, Coop) som har forskjellige EAN.

## Slik lages handlelisten

1. Alle middager i ukeplanen skaleres til riktig antall porsjoner.
2. Mengdene regnes om til ingrediensens basisenhet og summeres (2 stk løk blir 240 g).
3. For valgt kjede hentes koblede produkter. Verifiserte koblinger går foran.
4. Blant produktene som er nesten like gode treff velges billigste totalpris
   (antall pakker ganger pris), så 1 kg kjøttdeig kan slå 3 x 400 g.
5. Priser eldre enn 30 dager merkes som gamle.

## Kom i gang

Krever bare Python 3.10 eller nyere, ingen pakker.

```bash
cp .env.example .env               # lim inn KASSAL_API_KEY
python -m matglede init            # lager matglede.db med 129 ingredienser og 6 middager
python -m matglede import          # henter varer fra Kassalapp (ca. 10 min med gratisnøkkel)
python -m matglede demo-plan       # lager en ukeplan med fem middager
python -m matglede compare --plan 1
python -m matglede list --plan 1 --chain ODA
```

Gå gjennom koblingene for en ingrediens og rett opp feil:

```bash
python -m matglede review hvitlok
python -m matglede verify hvitlok 42     # produkt-id fra review
python -m matglede reject hvitlok 17
```

Matcheren treffer bra på de fleste varer, men ikke alle. Verifiserte og avviste koblinger
beholdes når du kjører import på nytt.

Tester: `python -m unittest discover tests`

## Viktig å vite om dataene

- **Oda, Kiwi og Meny** har priser som oppdateres daglig.
- **Rema 1000 og Coop** har i Kassalapp priser som sist ble oppdatert i mai 2024. Varene
  finnes, men prisene er gamle og vises merket som det.
- Coop Extra, Mega, Prix og Obs ligger samlet som `COOP_NO`.
- Gratisnøkkelen (Hobby) gir 60 kall per minutt og er ikke for kommersiell bruk.
  Tjener appen penger, trengs Bedrift-avtalen (750 kr/mnd uten MVA). Lagring og caching er lov.
- Produktbilder er lenker til kjedenes bilder. Avklar bruksrett før de vises i en publisert app.

## Tilbud-siden

Tilbud-siden i appen viser butikkene som logoer. Trykker man på en butikk, får man ukas
mest aktuelle tilbud i en karusell, hele lista over ukas tilbud gruppert etter varegruppe,
og en knapp som åpner kjedens egen tilbudsavis.

```bash
python -m matglede fetch-offers    # skriver app/offers.js (ca. 6 min med gratisnøkkel)
```

- Et tilbud er en vare der dagens pris er minst 10 % og 3 kr lavere enn medianprisen de
  8 til 60 foregående dagene, ut fra prishistorikken i Kassalapp.
- Rema 1000 og Coop-kjedene har ikke ferske priser i Kassalapp, så der viser appen bare
  lenken til avisen.
- Avisen vises inne i appen, hentet rett fra kjedens egen server (`matglede/flyers.py`
  finner adressene, ingenting kopieres). Coop Extra, Mega, Prix og Marked: avissidene som
  bilder. Kiwi og Spar: PDF-en fra kiwi.no og spar.no. Meny og Obs: kjedens iPaper-leser.
  Joker (Flipsnack), Rema 1000 og Bunnpris (Tjek) blokkerer innebygging, så der får man
  en knapp som åpner avisen hos kjeden.
- `.github/workflows/tilbud.yml` kjører hver mandag kl. 12 norsk tid, lagrer `app/offers.js`
  på appgrenen og publiserer appen på gh-pages. Den trenger repo-hemmeligheten
  `KASSAL_API_KEY`, og må ligge på standardgrenen (main) for at GitHub skal kjøre den
  etter tidsplan.

## Neste steg

- Flytte skjemaet til Postgres/Supabase når appen skal ha brukere.
- Et enkelt adminverktøy for å godkjenne koblinger, i stedet for kommandolinjen.
- Nattlig prisoppdatering med `POST /products/prices-bulk` for koblede EAN-er.
- «Send til Oda»: Odas MCP lar en innlogget bruker fylle sin egen handlekurv.

## Populære oppskrifter fra Rema 1000, Aichas Mat og Marit Kolby

`seed/external_recipes.json` har 57 oppskrifter som lastes inn av `init`. For hver oppskrift
lagres bare tittel, porsjoner, ingredienser med mengde og lenke til originalen
(`recipe.source_url`). Fremgangsmåte og bilder er kildens tekst og lagres ikke: appen lenker dit.

| Kilde | Hva "populær" betyr her |
|---|---|
| [rema.no/oppskrifter](https://www.rema.no/oppskrifter/) | Remas egen liste «de mest populære oppskriftene», 24 stk, sortert etter antall stemmer. |
| Hverdag og søndag (oppskrifter fra rema.no) | Rettene fra Ipsos Middagsdagboken 2025 ([NRK](https://www.nrk.no/kultur/xl/noregs-10-mest-populaere-middagar_-2025-1.17497150)) pluss søndagsstek og fårikål. For hver rett er den klassiske hjemmelagde varianten med flest stemmer på rema.no valgt. |
| [aichasmat.no](https://aichasmat.no/) | Bloggens kategori «Populære oppskrifter» (9) og salatene med flest kommentarer (9). |
| [Marit Kolby](https://www.maritkolby.no/) | Ingen populærliste. De tre oppskriftene fra Kokeboka som er publisert gratis hos ARK. |

Råfilene ligger i `seed/sources/`. Etter endringer der, eller i koblingsreglene i
`matglede/recipe_parse.py`:

```bash
python -m matglede build-external   # skriver external_recipes.json og viser hva som mangler
```

Ingredienser som ikke finnes i `ingredients.csv` (vann, ribbe, surkål og lignende) blir
stående i JSON-filen med `"ingredient": null`, men tas ikke med i handlelisten før de legges til.
Salt og pepper "etter smak" (uten mengde) hoppes også over.

Matprat og TINE er ikke brukt: vilkårene deres forbyr å hente oppskrifter til apper uten
skriftlig avtale. DN-serien «Aichas salater» er heller ikke brukt, fordi DN forbyr skraping.

## Appen (app/)

`app/` er appdesignet fra Claude Design koblet til dataene her. Appen viser Matgledes egne
oppskrifter i `seed/app_recipes.json` (17 hverdags-, helge- og søndagsmiddager), ikke
oppskriftene hentet fra nettet og ikke eksempeloppskriftene fra designet. Hver oppskrift har tid,
vanskelighetsgrad (1–5), kategorier, ingredienser og fremgangsmåte.

```bash
python -m matglede export-app      # skriver app/data.js fra app_recipes.json og matglede.db
cd app && python -m http.server    # åpne http://localhost:8000
```

- **Oppskrift**: ingredienser med mengde regnet om til antall personer, tid,
  vanskelighetsgrad og steg for steg. Antall personer velges på hver rett (standarden settes i
  Innstillinger), og handlelisten bruker antallet for hver rett.
- **Ingredienser** kobles til varedatabasen med feltet `slug` (fra `ingredients.csv`). `null`
  betyr at ingrediensen ikke er koblet ennå (buljong, lasagneplater, lammelår og noen få til).
  «1 boks» regnes om med de vanlige pakningsstørrelsene i `recipe_parse.PACK_SIZES`.
- **Pris per rett**: forbrukt andel av pakken for hver ingrediens i valgt butikk.
  «ca. X kr» betyr at alle ingredienser med mengde har pris, «minst X kr» at noen mangler.
- **Handleliste**: ingrediensene i ukeplanen summeres i basisenhet (g/ml/stk), og appen velger
  billigste antall hele pakker blant produktene fra databasen, som `shopping.pick_product`.
- **Tilbud og priser**: ukeplanen priset i hver kjede. Ekte ukestilbud er ikke koblet på ennå.
- Uten `matglede.db` gjenbruker `export-app` prisene i forrige `app/data.js`.
- **Bilder**: feltet `img` i `app_recipes.json` er et filnavn på Wikimedia Commons. Appen henter
  bildet i nettleseren (`Special:FilePath`, 720 px bredt) og viser stripemønsteret mens det laster.
  Lenker til fotograf og lisens for hvert bilde ligger under Innstillinger → Bilder.
- **Innlogging** (`app/auth.js`, `app/auth-config.js`, `firestore.rules`): Google-konto eller
  e-post og passord med Firebase. Favoritter, ukeplan, porsjoner, butikk, avkrysninger og
  oppgaver lagres i Firestore i `users/{uid}`. Uten verdier i `auth-config.js` er innlogging av
  og appen virker uten konto.

### Sette opp innlogging (Firebase)

1. Lag et prosjekt på https://console.firebase.google.com (Google Analytics trengs ikke).
2. Prosjektinnstillinger → Dine apper → Legg til web-app. Kopier `apiKey`, `authDomain`,
   `projectId` og `appId` inn i `app/auth-config.js`. Verdiene er ikke hemmelige.
3. Authentication → Sign-in method: slå på **Google** og **E-post/passord**.
4. Authentication → Settings → Authorized domains: legg til `hakonsolsvik.github.io`
   (`localhost` står der fra før).
5. Firestore Database → Opprett database (produksjonsmodus, region `eur3`).
6. Firestore → Regler: lim inn innholdet i `firestore.rules` og publiser.

Oppskriftene fra Rema 1000, Aichas Mat og Marit Kolby (`seed/external_recipes.json`) ligger
fortsatt i repoet for databasen, men brukes ikke i appen.

`app/support.js` er kjøretiden fra Claude Design, og `app/vendor/` er React 18.3.1 (MIT), så
appen virker uten nett. Bildene er fortsatt designets stripete plassholdere.
