"""Eksporterer data til appen (app/data.js).

Appen viser Matgledes egne oppskrifter i seed/app_recipes.json, med tid, vanskelighetsgrad
og fremgangsmåte. For hver ingredienslinje tas mengden med i ingrediensens basisenhet
(g/ml/stk), slik at appen kan skalere og summere den. Fra databasen tas produktkandidatene
per kjede med, ferdig filtrert på samme måte som `shopping.pick_product`. Appen velger selv
billigste antall pakker for mengden handlelisten trenger.

Uten database gjenbrukes prisene i forrige app/data.js. Finnes ingen, blir prisene tomme.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .db import CHAINS
from .recipe_parse import normalise_for_ingredient
from .shopping import SCORE_BAND, _is_stale
from .units import to_base

ROOT = Path(__file__).resolve().parent.parent
APP_DATA = ROOT / "app" / "data.js"
MAX_CANDIDATES = 6
RECIPES_JSON = ROOT / "seed" / "app_recipes.json"

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
    """Produktene i en tidligere app/data.js, så oppskriftene kan bygges på nytt uten database."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
    except (OSError, ValueError):
        return {}
    return {slug: ing.get("products") or {} for slug, ing in data.get("ingredients", {}).items()}


def base_amount(row: dict, slug: str, q: float | None, u: str | None, name: str) -> float | None:
    """Mengden i ingrediensens basisenhet. 'boks' behandles som pakke ('1 boks hakkede tomater')."""
    if q is None or not u:
        return None
    amount, unit = normalise_for_ingredient(slug, q, "pk" if u == "boks" else u, name)
    gpp = float(row["grams_per_piece"]) if row["grams_per_piece"] else None
    return to_base(amount, unit, row["base_unit"], gpp)


def build(conn: sqlite3.Connection | None = None, now: datetime | None = None,
          recipes_path: Path = RECIPES_JSON, previous: dict[str, dict] | None = None) -> dict:
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
        for i in r["ing"]:
            slug = i.get("slug")
            if slug and slug not in ing_rows:
                raise ValueError(f"Ukjent ingrediens i {r['id']}: {slug}")
            base = base_amount(ing_rows[slug], slug, i["q"], i["u"], i["n"]) if slug else None
            lines += 1
            if slug:
                mapped += 1
                used.add(slug)
            items.append({"n": i["n"], "q": i["q"], "u": i["u"], "slug": slug,
                          "base": round(base, 3) if base is not None else None})
        recipes.append({
            "id": r["id"], "name": r["name"], "servings": r["servings"], "time": r["time"],
            "diff": r["diff"], "cats": r.get("cats", []), "popular": r.get("popular"),
            "img": r.get("img"),
            "steps": r["steps"], "ing": items,
        })

    ingredients = {}
    priced = 0
    for slug in sorted(used):
        row = ing_rows[slug]
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
                             "products": products}

    return {
        "generated": now.strftime("%Y-%m-%d"),
        "hasPrices": priced > 0,
        "chains": [{"code": code, "name": name, "bg": CHAIN_COLORS[code][0], "fg": CHAIN_COLORS[code][1]}
                   for code, name, _ in CHAINS],
        "ingredients": ingredients,
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
