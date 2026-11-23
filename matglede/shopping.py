"""Lager handleliste fra en ukeplan og velger konkrete produkter i en kjede."""
from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .matching import IngredientRule, excluded_name
from .units import to_base

STALE_DAYS = 30
SCORE_BAND = 1.0  # velg billigste blant produkter som er nesten like gode treff
# Et treff som er mye svakere enn det beste for ingrediensen i noen kjede er trolig feil
# ("Pepsi Max Lime" når "Lime pr stk" finnes). Da er det bedre å vise "ikke funnet".
GLOBAL_GAP = 3.0


def score_floor(conn: sqlite3.Connection, ingredient_id: int) -> float:
    row = conn.execute(
        "SELECT MAX(score) AS best FROM ingredient_product WHERE ingredient_id=? AND status != 'rejected'",
        (ingredient_id,),
    ).fetchone()
    return (row["best"] or 0) - GLOBAL_GAP


@dataclass
class Need:
    ingredient_id: int
    name: str
    base_unit: str
    grams_per_piece: float | None = None
    amount: float = 0.0
    unconverted: list[str] = field(default_factory=list)  # mengder vi ikke kunne regne om
    recipes: set[str] = field(default_factory=set)


@dataclass
class Line:
    ingredient: str
    need: str
    product: str | None = None
    packages: int = 0
    price_each: float | None = None
    total: float | None = None
    url: str | None = None
    price_date: str | None = None
    stale: bool = False
    recipes: list[str] = field(default_factory=list)


def aggregate_needs(conn: sqlite3.Connection, meal_plan_id: int) -> list[Need]:
    rows = conn.execute(
        """SELECT i.id, i.name, i.base_unit, i.grams_per_piece, ri.amount, ri.unit,
                  e.servings AS plan_servings, r.servings AS recipe_servings, r.name AS recipe
           FROM meal_plan_entry e
           JOIN recipe r ON r.id = e.recipe_id
           JOIN recipe_ingredient ri ON ri.recipe_id = r.id
           JOIN ingredient i ON i.id = ri.ingredient_id
           WHERE e.meal_plan_id = ?""",
        (meal_plan_id,),
    ).fetchall()
    needs: dict[int, Need] = {}
    for r in rows:
        n = needs.setdefault(r["id"], Need(r["id"], r["name"], r["base_unit"], r["grams_per_piece"]))
        n.recipes.add(r["recipe"])
        amount = r["amount"] * r["plan_servings"] / r["recipe_servings"]
        base = to_base(amount, r["unit"], r["base_unit"], r["grams_per_piece"])
        if base is None:
            n.unconverted.append(f"{amount:g} {r['unit']}")
        else:
            n.amount += base
    return sorted(needs.values(), key=lambda n: n.name)


def _is_stale(price_date: str | None, now: datetime) -> bool:
    if not price_date:
        return True
    try:
        dt = datetime.fromisoformat(price_date.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (now - dt).days > STALE_DAYS


def candidates(conn: sqlite3.Connection, ingredient_id: int, chain_code: str, base_unit: str,
               grams_per_piece: float | None, now: datetime) -> list[tuple[sqlite3.Row, float | None]]:
    """Gode nok treff for ingrediensen i kjeden, med pakningsstørrelse i basisenhet (None hvis ukjent).

    Brukes av både handlelisten og app-eksporten, så de velger blant de samme produktene.
    """
    rows = conn.execute(
        """SELECT p.name, p.package_amount, p.package_unit, o.store_name, o.price, o.url, o.price_date,
                  ip.score, ip.status
           FROM ingredient_product ip
           JOIN product p ON p.id = ip.product_id
           JOIN offer o ON o.product_id = p.id AND o.chain_code = ?
           WHERE ip.ingredient_id = ? AND ip.status != 'rejected' AND o.price IS NOT NULL""",
        (chain_code, ingredient_id),
    ).fetchall()
    rule = IngredientRule.from_row(conn.execute("SELECT * FROM ingredient WHERE id=?", (ingredient_id,)).fetchone())
    rows = [r for r in rows if not excluded_name(rule, r["store_name"] or r["name"])]
    floor = score_floor(conn, ingredient_id)
    rows = [r for r in rows if r["status"] == "verified" or r["score"] >= floor]
    if not rows:
        return []
    pool = [r for r in rows if r["status"] == "verified"] or rows
    top = max(r["score"] for r in pool)
    pool = [r for r in pool if r["score"] >= top - SCORE_BAND]
    pool = [r for r in pool if not _is_stale(r["price_date"], now)] or pool  # ferske priser foran gamle
    sized = [(r, to_base(r["package_amount"], r["package_unit"], base_unit, grams_per_piece)
              if r["package_amount"] else None) for r in pool]
    return [x for x in sized if x[1]] or sized  # kjent pakningsstørrelse går foran


def pick_product(conn: sqlite3.Connection, need: Need, chain_code: str, now: datetime) -> Line:
    need_txt = f"{need.amount:g} {need.base_unit}" if need.amount else ""
    if need.unconverted:
        need_txt = ", ".join(filter(None, [need_txt, *need.unconverted]))
    line = Line(ingredient=need.name, need=need_txt, recipes=sorted(need.recipes))
    pool = candidates(conn, need.ingredient_id, chain_code, need.base_unit, need.grams_per_piece, now)
    if not pool:
        return line

    def packs(size: float | None) -> int:
        if need.amount and size:
            return max(1, math.ceil(need.amount / size - 1e-9))
        return 1

    best, size = min(pool, key=lambda x: (packs(x[1]) * x[0]["price"], -x[0]["score"]))
    n = packs(size)
    line.product = best["store_name"]
    line.packages = n
    line.price_each = best["price"]
    line.total = round(n * best["price"], 2)
    line.url = best["url"]
    line.price_date = best["price_date"]
    line.stale = _is_stale(best["price_date"], now)
    return line


def shopping_list(conn: sqlite3.Connection, meal_plan_id: int, chain_code: str,
                  now: datetime | None = None) -> list[Line]:
    now = now or datetime.now(timezone.utc)
    return [pick_product(conn, n, chain_code, now) for n in aggregate_needs(conn, meal_plan_id)]


def compare_chains(conn: sqlite3.Connection, meal_plan_id: int, now: datetime | None = None) -> list[dict]:
    out = []
    for ch in conn.execute("SELECT code, name FROM chain ORDER BY code"):
        lines = shopping_list(conn, meal_plan_id, ch["code"], now)
        found = [l for l in lines if l.product]
        out.append({
            "chain": ch["name"],
            "code": ch["code"],
            "total": round(sum(l.total for l in found), 2),
            "found": len(found),
            "missing": [l.ingredient for l in lines if not l.product],
            "stale_prices": sum(1 for l in found if l.stale),
        })
    return sorted(out, key=lambda r: (-r["found"], r["total"]))
