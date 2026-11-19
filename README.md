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
python -m matglede init            # lager matglede.db med 37 ingredienser og 6 middager
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

## Neste steg

- Flytte skjemaet til Postgres/Supabase når appen skal ha brukere.
- Et enkelt adminverktøy for å godkjenne koblinger, i stedet for kommandolinjen.
- Nattlig prisoppdatering med `POST /products/prices-bulk` for koblede EAN-er.
- «Send til Oda»: Odas MCP lar en innlogget bruker fylle sin egen handlekurv.
