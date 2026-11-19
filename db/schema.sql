-- Matglede varedatabase (SQLite).
-- Kjerneideen: oppskrifter bruker generiske INGREDIENSER, butikker selger PRODUKTER.
-- ingredient_product kobler de to, og offer gir pris per kjede.

PRAGMA foreign_keys = ON;

-- Butikkjeder vi viser i appen, og hvilken butikkode de har hos Kassalapp.
CREATE TABLE IF NOT EXISTS chain (
    code            TEXT PRIMARY KEY,          -- f.eks. 'ODA', 'KIWI'
    name            TEXT NOT NULL,
    kassal_store    TEXT NOT NULL UNIQUE       -- f.eks. 'ODA_NO', 'KIWI'
);

-- Generisk ingrediens slik den står i en oppskrift ("hakkede tomater").
CREATE TABLE IF NOT EXISTS ingredient (
    id              INTEGER PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    category        TEXT,
    base_unit       TEXT NOT NULL CHECK (base_unit IN ('g', 'ml', 'stk')),
    grams_per_piece REAL,                      -- for å regne "2 stk løk" om til gram
    search_terms    TEXT NOT NULL,             -- '|'-separert, brukes mot Kassalapp
    must_include    TEXT NOT NULL DEFAULT '',  -- ord som må finnes i produktnavnet
    exclude_terms   TEXT NOT NULL DEFAULT '',  -- ord som diskvalifiserer et produkt
    category_hints  TEXT NOT NULL DEFAULT ''   -- Kassalapp-kategorier som gir bonus, '|'-separert
);

-- Et fysisk produkt. Samme EAN = samme produkt på tvers av kjeder.
CREATE TABLE IF NOT EXISTS product (
    id              INTEGER PRIMARY KEY,
    ean             TEXT UNIQUE,               -- NULL for noen Oda-varer uten strekkode
    source_key      TEXT NOT NULL UNIQUE,      -- 'ean:<ean>' eller 'kassal:<id>'
    name            TEXT NOT NULL,
    brand           TEXT,
    vendor          TEXT,
    package_amount  REAL,                      -- i package_unit
    package_unit    TEXT CHECK (package_unit IN ('g', 'ml', 'stk')),
    category        TEXT,                      -- Kassalapp-kategori, f.eks. 'Kjøtt > Kjøttdeig'
    image_url       TEXT,
    updated_at      TEXT NOT NULL
);

-- Pris og lenke for et produkt i en kjede.
CREATE TABLE IF NOT EXISTS offer (
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    chain_code      TEXT NOT NULL REFERENCES chain(code),
    store_name      TEXT NOT NULL,             -- navnet kjeden selv bruker
    price           REAL,
    unit_price      REAL,
    url             TEXT,
    price_date      TEXT,                      -- når Kassalapp sist så prisen
    fetched_at      TEXT NOT NULL,
    PRIMARY KEY (product_id, chain_code)
);

-- Kobling ingrediens -> produkt. 'auto' fra matcheren, 'verified' når et menneske har sjekket.
CREATE TABLE IF NOT EXISTS ingredient_product (
    ingredient_id   INTEGER NOT NULL REFERENCES ingredient(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    score           REAL NOT NULL,
    status          TEXT NOT NULL DEFAULT 'auto' CHECK (status IN ('auto', 'verified', 'rejected')),
    PRIMARY KEY (ingredient_id, product_id)
);

CREATE TABLE IF NOT EXISTS recipe (
    id              INTEGER PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    servings        INTEGER NOT NULL CHECK (servings > 0)
);

CREATE TABLE IF NOT EXISTS recipe_ingredient (
    recipe_id       INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    ingredient_id   INTEGER NOT NULL REFERENCES ingredient(id),
    amount          REAL NOT NULL,
    unit            TEXT NOT NULL,             -- g, kg, ml, dl, l, ss, ts, stk, pk
    note            TEXT,
    PRIMARY KEY (recipe_id, ingredient_id)
);

-- Ukeplanleggeren.
CREATE TABLE IF NOT EXISTS meal_plan (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    week_start      TEXT NOT NULL              -- ISO-dato for mandagen
);

CREATE TABLE IF NOT EXISTS meal_plan_entry (
    id              INTEGER PRIMARY KEY,
    meal_plan_id    INTEGER NOT NULL REFERENCES meal_plan(id) ON DELETE CASCADE,
    day             TEXT NOT NULL,             -- ISO-dato
    recipe_id       INTEGER NOT NULL REFERENCES recipe(id),
    servings        INTEGER NOT NULL CHECK (servings > 0)
);

CREATE INDEX IF NOT EXISTS idx_offer_chain ON offer(chain_code);
CREATE INDEX IF NOT EXISTS idx_ip_ingredient ON ingredient_product(ingredient_id, status);
CREATE INDEX IF NOT EXISTS idx_mpe_plan ON meal_plan_entry(meal_plan_id);
