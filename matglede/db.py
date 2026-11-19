"""Databasetilkobling og innlasting av startdata (kjeder, ingredienser, oppskrifter)."""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "db" / "schema.sql"
SEED = ROOT / "seed"

# Kjedene appen viser. Kassalapp samler Coop-kjedene (Extra, Mega, Prix, Obs) under COOP_NO.
CHAINS = [
    ("ODA", "Oda", "ODA_NO"),
    ("KIWI", "Kiwi", "KIWI"),
    ("MENY", "Meny", "MENY_NO"),
    ("REMA", "Rema 1000", "REMA_1000"),
    ("COOP", "Coop", "COOP_NO"),
    ("SPAR", "Spar", "SPAR_NO"),
    ("JOKER", "Joker", "JOKER_NO"),
]


def connect(path: str | Path = "matglede.db") -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.executemany(
        "INSERT INTO chain(code, name, kassal_store) VALUES (?,?,?) "
        "ON CONFLICT(code) DO UPDATE SET name=excluded.name, kassal_store=excluded.kassal_store",
        CHAINS,
    )
    conn.commit()


def load_ingredients(conn: sqlite3.Connection, path: Path = SEED / "ingredients.csv") -> int:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        conn.execute(
            """INSERT INTO ingredient(slug, name, category, base_unit, grams_per_piece,
                                      search_terms, must_include, exclude_terms, category_hints)
               VALUES (:slug, :name, :category, :base_unit, :grams_per_piece,
                       :search_terms, :must_include, :exclude_terms, :category_hints)
               ON CONFLICT(slug) DO UPDATE SET
                 name=excluded.name, category=excluded.category, base_unit=excluded.base_unit,
                 grams_per_piece=excluded.grams_per_piece, search_terms=excluded.search_terms,
                 must_include=excluded.must_include, exclude_terms=excluded.exclude_terms,
                 category_hints=excluded.category_hints""",
            {**r, "grams_per_piece": float(r["grams_per_piece"]) if r["grams_per_piece"] else None},
        )
    conn.commit()
    return len(rows)


def load_recipes(conn: sqlite3.Connection, path: Path = SEED / "recipes.json") -> int:
    recipes = json.loads(path.read_text(encoding="utf-8"))
    ids = {r["slug"]: r["id"] for r in conn.execute("SELECT id, slug FROM ingredient")}
    for rec in recipes:
        conn.execute(
            "INSERT INTO recipe(slug, name, servings) VALUES (?,?,?) "
            "ON CONFLICT(slug) DO UPDATE SET name=excluded.name, servings=excluded.servings",
            (rec["slug"], rec["name"], rec["servings"]),
        )
        rid = conn.execute("SELECT id FROM recipe WHERE slug=?", (rec["slug"],)).fetchone()["id"]
        conn.execute("DELETE FROM recipe_ingredient WHERE recipe_id=?", (rid,))
        for item in rec["ingredients"]:
            if item["ingredient"] not in ids:
                raise ValueError(f"Ukjent ingrediens i {rec['slug']}: {item['ingredient']}")
            conn.execute(
                "INSERT INTO recipe_ingredient(recipe_id, ingredient_id, amount, unit, note) VALUES (?,?,?,?,?)",
                (rid, ids[item["ingredient"]], item["amount"], item["unit"], item.get("note")),
            )
    conn.commit()
    return len(recipes)


def create_meal_plan(conn: sqlite3.Connection, name: str, week_start: str,
                     entries: list[tuple[str, str, int]]) -> int:
    """entries: (dato, oppskrift-slug, porsjoner)."""
    cur = conn.execute("INSERT INTO meal_plan(name, week_start) VALUES (?,?)", (name, week_start))
    plan_id = cur.lastrowid
    for day, slug, servings in entries:
        row = conn.execute("SELECT id FROM recipe WHERE slug=?", (slug,)).fetchone()
        if row is None:
            raise ValueError(f"Ukjent oppskrift: {slug}")
        conn.execute(
            "INSERT INTO meal_plan_entry(meal_plan_id, day, recipe_id, servings) VALUES (?,?,?,?)",
            (plan_id, day, row["id"], servings),
        )
    conn.commit()
    return plan_id
