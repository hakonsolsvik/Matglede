"""Populære oppskrifter fra eksterne kilder (Rema 1000, Aichas Mat, Marit Kolby).

Råfilene i seed/sources/ inneholder bare tittel, lenke, porsjoner og ingredienslinjer
slik kilden skrev dem. Vi lagrer ikke fremgangsmåte eller bilder: de er kildens
opphavsrettslige tekst, og appen lenker til originalen i stedet.

`build()` tolker linjene og kobler dem til ingredienstabellen. Resultatet havner i
seed/external_recipes.json, som `load()` legger inn i databasen.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import unicodedata
from pathlib import Path

from .recipe_parse import (is_heading, match_ingredient, normalise_for_ingredient,
                           parse_line, parse_servings, split_combined)

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "seed" / "sources"
OUT = ROOT / "seed" / "external_recipes.json"

SOURCE_INFO = {
    "rema": {
        "name": "REMA 1000",
        "site": "https://www.rema.no/oppskrifter/",
        "popularity": "Listen «de mest populære oppskriftene» øverst på rema.no/oppskrifter. "
                      "Den er sortert etter antall stemmer (ratingCount i schema.org).",
    },
    "aicha": {
        "name": "Aichas Mat (Aicha Bouhlou)",
        "site": "https://aichasmat.no/",
        "popularity": "Gruppe 'populaere': bloggens egen kategori «Populære oppskrifter». "
                      "Gruppe 'salater': salatkategorien sortert etter antall kommentarer "
                      "(bare salater med minst én kommentar). Bloggen har ingen annen populærliste.",
    },
    "kolby": {
        "name": "Marit Kolby og Hanne Fisher",
        "site": "https://www.maritkolby.no/",
        "popularity": "Ingen populærliste finnes. Dette er de tre oppskriftene fra «Kokeboka – "
                      "Hva skal vi spise?» som er publisert gratis hos ARK.",
    },
}

DEFAULT_SERVINGS = 4  # når kilden ikke oppgir porsjoner


def slugify(text: str) -> str:
    t = text.lower().replace("æ", "ae").replace("ø", "o").replace("å", "a")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def _base_units(path: Path = ROOT / "seed" / "ingredients.csv") -> dict[str, str]:
    with open(path, encoding="utf-8", newline="") as f:
        return {r["slug"]: r["base_unit"] for r in csv.DictReader(f)}


def build_recipe(source: str, raw: dict) -> dict:
    items = []
    for line in raw["ingredients"]:
        if is_heading(line):
            continue
        p = parse_line(line)
        for name in split_combined(p.name):
            slug = match_ingredient(name, p.unit)
            amount, unit = normalise_for_ingredient(slug, p.amount, p.unit, name)
            items.append({"raw": line, "name": name, "amount": amount, "unit": unit, "ingredient": slug})
    servings = parse_servings(raw.get("servings"))
    rec = {
        "slug": f"{source}-{slugify(raw['name'])}",
        "name": raw["name"],
        "source": source,
        "source_url": raw["url"],
        "group": raw.get("group"),
        "rank": raw["rank"],
        "servings": servings or DEFAULT_SERVINGS,
        "servings_guessed": servings is None,
        "ingredients": items,
    }
    for key in ("rating", "ratingCount", "comments", "totalTime", "category"):
        if raw.get(key) is not None:
            rec[key] = round(raw[key], 2) if key == "rating" else raw[key]
    return rec


def build(sources: Path = SOURCES, out: Path = OUT) -> dict:
    data = {"sources": SOURCE_INFO, "recipes": []}
    for source in SOURCE_INFO:
        path = sources / f"{source}.json"
        if path.exists():
            for raw in json.loads(path.read_text(encoding="utf-8")):
                data["recipes"].append(build_recipe(source, raw))
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return data


def coverage(data: dict) -> dict:
    """Hvor mange ingredienslinjer som ble koblet, og hvilke navn som mangler oftest."""
    total = mapped = 0
    missing: dict[str, int] = {}
    for r in data["recipes"]:
        for i in r["ingredients"]:
            total += 1
            if i["ingredient"]:
                mapped += 1
            else:
                key = i["name"].lower().split(",")[0].strip()
                missing[key] = missing.get(key, 0) + 1
    return {"lines": total, "mapped": mapped,
            "top_missing": sorted(missing.items(), key=lambda kv: -kv[1])[:25]}


def load(conn: sqlite3.Connection, path: Path = OUT) -> tuple[int, int]:
    """Legg oppskriftene inn. Ingredienser uten kobling eller mengde hoppes over.

    Returnerer (antall oppskrifter, antall ingredienslinjer som ble hoppet over).
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = {r["slug"]: r["id"] for r in conn.execute("SELECT id, slug FROM ingredient")}
    skipped = 0
    for rec in data["recipes"]:
        conn.execute(
            "INSERT INTO recipe(slug, name, servings, source, source_url) VALUES (?,?,?,?,?) "
            "ON CONFLICT(slug) DO UPDATE SET name=excluded.name, servings=excluded.servings, "
            "source=excluded.source, source_url=excluded.source_url",
            (rec["slug"], rec["name"], rec["servings"], rec["source"], rec["source_url"]),
        )
        rid = conn.execute("SELECT id FROM recipe WHERE slug=?", (rec["slug"],)).fetchone()["id"]
        conn.execute("DELETE FROM recipe_ingredient WHERE recipe_id=?", (rid,))
        totals: dict[tuple[str, str], float] = {}
        for item in rec["ingredients"]:
            if not item["ingredient"] or item["amount"] is None or item["ingredient"] not in ids:
                skipped += 1
                continue
            key = (item["ingredient"], item["unit"])
            totals[key] = totals.get(key, 0) + item["amount"]
        seen = set()
        for (slug, unit), amount in totals.items():
            if slug in seen:  # samme ingrediens i to enheter: behold første
                skipped += 1
                continue
            seen.add(slug)
            conn.execute(
                "INSERT INTO recipe_ingredient(recipe_id, ingredient_id, amount, unit) VALUES (?,?,?,?)",
                (rid, ids[slug], amount, unit),
            )
    conn.commit()
    return len(data["recipes"]), skipped
