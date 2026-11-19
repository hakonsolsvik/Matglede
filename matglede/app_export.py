"""Eksporterer data til appen (app/data.js).

Appen viser bare de innsamlede oppskriftene i seed/external_recipes.json. For hver
ingredienslinje tas mengden med i ingrediensens basisenhet (g/ml/stk), slik at appen kan
skalere og summere den. Fra databasen tas produktkandidatene per kjede med, ferdig
filtrert på samme måte som `shopping.pick_product`. Appen velger selv billigste antall
pakker for mengden handlelisten trenger.

Uten database (før `import` er kjørt) blir prisene tomme, og appen sier det.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .db import CHAINS
from .external import OUT as RECIPES_JSON, SOURCE_INFO
from .recipe_parse import (GRAMS_PER_CHICKEN_BREAST, GRAMS_PER_CLOVE, PACK_SIZES, RULES,
                           _WHOLE_WORD)
from .shopping import SCORE_BAND, _is_stale
from .units import to_base

ROOT = Path(__file__).resolve().parent.parent
APP_DATA = ROOT / "app" / "data.js"
MAX_CANDIDATES = 6

# Farger fra kjedenes egne profiler, brukt på butikkflisene i appen.
CHAIN_COLORS = {
    "ODA": ("#ff5c5c", "#ffffff"),
    "KIWI": ("#3d9a36", "#ffffff"),
    "MENY": ("#c41f30", "#ffffff"),
    "REMA": ("#16408f", "#ffffff"),
    "COOP": ("#0d5aa7", "#ffffff"),
    "SPAR": ("#d6362a", "#ffffff"),
    "JOKER": ("#ffd23f", "#14306b"),
}


# Logoene Kassalapp viser for kjedene (feltet store.logo i API-svarene). Lastes ned til
# app/logos/ med `python -m matglede fetch-logos`, så appen virker uten nett.
CHAIN_LOGOS = {
    "ODA": "https://kassal.app/logos/Oda.svg",
    "KIWI": "https://kassal.app/logos/Kiwi.svg",
    "MENY": "https://kassal.app/logos/Meny.svg",
    "REMA": "https://kassal.app/logos/Rema-1000.svg",
    "COOP": "https://kassal.app/logos/Coop.svg",
    "SPAR": "https://kassal.app/logos/Spar.svg",
    "JOKER": "https://kassal.app/logos/Joker.svg",
}
LOGO_DIR = ROOT / "app" / "logos"


def fetch_logos(out: Path = LOGO_DIR) -> list[Path]:
    """Last ned kjedelogoene til app/logos/<KODE>.svg."""
    import urllib.request
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for code, url in CHAIN_LOGOS.items():
        req = urllib.request.Request(url, headers={"User-Agent": "matglede/0.1"})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read()
        if not body.lstrip().startswith(b"<svg"):
            raise ValueError(f"{url} ga ikke en SVG")
        path = out / f"{code}.svg"
        path.write_bytes(body)
        written.append(path)
    return written


def _logo(code: str) -> str | None:
    """Relativ sti til logoen hvis den er lastet ned, ellers Kassalapp-URL-en."""
    if (LOGO_DIR / f"{code}.svg").exists():
        return f"logos/{code}.svg"
    return CHAIN_LOGOS.get(code)


def _minutes(iso: str | None) -> int | None:
    """'PT1H20M' eller 'PT80M' -> 80."""
    if not iso or not iso.startswith("PT"):
        return None
    total, num = 0, ""
    for ch in iso[2:]:
        if ch.isdigit():
            num += ch
        elif num:
            total += int(num) * {"H": 60, "M": 1, "S": 0}.get(ch, 0)
            num = ""
    return total or None


def _ingredients_csv(path: Path = ROOT / "seed" / "ingredients.csv") -> dict[str, dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return {r["slug"]: r for r in csv.DictReader(f)}


def _candidates(conn: sqlite3.Connection, slug: str, chain: str, base_unit: str,
                gpp: float | None, now: datetime) -> list[dict]:
    rows = conn.execute(
        """SELECT p.name, p.package_amount, p.package_unit, o.store_name, o.price, o.url,
                  o.price_date, ip.score, ip.status
           FROM ingredient_product ip
           JOIN ingredient i ON i.id = ip.ingredient_id
           JOIN product p ON p.id = ip.product_id
           JOIN offer o ON o.product_id = p.id AND o.chain_code = ?
           WHERE i.slug = ? AND ip.status != 'rejected' AND o.price IS NOT NULL""",
        (chain, slug),
    ).fetchall()
    if not rows:
        return []

    def size(r) -> float | None:
        amt, unit = r["package_amount"], r["package_unit"]
        if not amt:
            return None
        if unit == base_unit:
            return amt
        if gpp and unit == "g" and base_unit == "stk":
            return amt / gpp
        if gpp and unit == "stk" and base_unit == "g":
            return amt * gpp
        if {unit, base_unit} == {"g", "ml"}:
            return amt
        return None

    pool = [r for r in rows if r["status"] == "verified"] or rows
    top = max(r["score"] for r in pool)
    pool = [r for r in pool if r["score"] >= top - SCORE_BAND]
    pool = [r for r in pool if not _is_stale(r["price_date"], now)] or pool
    pool = [r for r in pool if size(r)] or pool
    pool.sort(key=lambda r: (r["price"] / (size(r) or 1), -r["score"]))
    return [{
        "name": r["store_name"] or r["name"],
        "size": round(size(r), 3) if size(r) else None,
        "price": r["price"],
        "url": r["url"],
        "date": (r["price_date"] or "")[:10] or None,
        "stale": _is_stale(r["price_date"], now),
    } for r in pool[:MAX_CANDIDATES]]


def previous_products(path: Path = APP_DATA) -> dict[str, dict]:
    """Produktene fra en tidligere app/data.js, slik at oppskriftene kan bygges på nytt uten database."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
    except (OSError, ValueError):
        return {}
    return {slug: ing.get("products") or {} for slug, ing in data.get("ingredients", {}).items()}


def build(conn: sqlite3.Connection | None = None, now: datetime | None = None,
          recipes_path: Path = RECIPES_JSON, previous: dict[str, dict] | None = None) -> dict:
    """Uten database brukes produktene fra `previous` (typisk forrige app/data.js)."""
    now = now or datetime.now(timezone.utc)
    data = json.loads(recipes_path.read_text(encoding="utf-8"))
    ing_rows = _ingredients_csv()
    has_db = conn is not None and conn.execute(
        "SELECT name FROM sqlite_master WHERE name='offer'").fetchone() is not None

    used: set[str] = set()
    recipes = []
    lines = mapped = 0
    for r in data["recipes"]:
        items = []
        for i in r["ingredients"]:
            slug = i["ingredient"] if i["ingredient"] in ing_rows else None
            base = None
            if slug and i["amount"] is not None and i["unit"]:
                row = ing_rows[slug]
                gpp = float(row["grams_per_piece"]) if row["grams_per_piece"] else None
                base = to_base(i["amount"], i["unit"], row["base_unit"], gpp)
            lines += 1
            if slug:
                mapped += 1
                used.add(slug)
            items.append({"n": i["name"], "q": i["amount"], "u": i["unit"], "slug": slug,
                          "base": round(base, 3) if base is not None else None})
        recipes.append({
            "id": r["slug"], "name": r["name"], "servings": r["servings"],
            "servingsGuessed": r.get("servings_guessed", False),
            "source": r["source"], "url": r["source_url"], "group": r.get("group"),
            "rank": r.get("rank"), "rating": r.get("rating"), "ratingCount": r.get("ratingCount"),
            "comments": r.get("comments"), "category": r.get("category"),
            "dish": r.get("dish") or (r.get("also") or {}).get("dish"),
            "alsoGroup": (r.get("also") or {}).get("group"),
            "time": _minutes(r.get("totalTime")), "ing": items,
        })

    # Alle ingrediensene tas med, også de ingen oppskrift bruker ennå: brukeren kan legge
    # dem til i egne oppskrifter. Søkeordene brukes til å koble fritekst i appen.
    ingredients = {}
    priced = 0
    for slug, row in ing_rows.items():
        gpp = float(row["grams_per_piece"]) if row["grams_per_piece"] else None
        products = {}
        if has_db:
            for code, _, _ in CHAINS:
                c = _candidates(conn, slug, code, row["base_unit"], gpp, now)
                if c:
                    products[code] = c
        elif previous:
            products = previous.get(slug, {})
        priced += bool(products)
        ingredients[slug] = {"name": row["name"], "base": row["base_unit"], "gpp": gpp,
                             "category": row["category"], "used": slug in used, "products": products}

    return {
        "generated": now.strftime("%Y-%m-%d"),
        "hasPrices": priced > 0,
        "sources": {k: {"name": v["name"], "site": v["site"]} for k, v in SOURCE_INFO.items()},
        "chains": [{"code": code, "name": name, "bg": CHAIN_COLORS[code][0], "fg": CHAIN_COLORS[code][1],
                    "logo": _logo(code)}
                   for code, name, _ in CHAINS],
        "ingredients": ingredients,
        "matching": {
            "rules": [[slug, list(needles), list(excl)] for slug, needles, excl in RULES],
            "wholeWord": sorted(_WHOLE_WORD),
            "gramsPerClove": GRAMS_PER_CLOVE,
            "gramsPerChickenBreast": GRAMS_PER_CHICKEN_BREAST,
            "packSizes": {k: list(v) for k, v in PACK_SIZES.items()},
        },
        "recipes": recipes,
        "stats": {"recipes": len(recipes), "lines": lines, "mapped": mapped,
                  "ingredients": len(ingredients), "pricedIngredients": priced},
    }


def write(data: dict, out: Path = APP_DATA) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out.write_text("// Generert av `python -m matglede export-app`. Ikke rediger for hånd.\n"
                   f"window.MATGLEDE_DATA = {body};\n", encoding="utf-8")
    return out
