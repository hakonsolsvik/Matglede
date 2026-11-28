"""Henter produkter fra Kassalapp for hver ingrediens og kobler dem til ingrediensen."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from .kassal import KassalClient
from .matching import MIN_SCORE, IngredientRule, score_product
from .units import parse_package

TOP_PER_CHAIN = 5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _price_date(p: dict) -> str | None:
    hist = p.get("price_history") or []
    if hist and hist[0].get("date"):
        return hist[0]["date"]
    return p.get("updated_at")


def _categories(p: dict) -> list[str]:
    return [c.get("name", "") for c in (p.get("category") or [])]


def upsert_product(conn: sqlite3.Connection, p: dict) -> int:
    ean = p.get("ean") or None
    key = f"ean:{ean}" if ean else f"kassal:{p['id']}"
    amount, unit = parse_package(p.get("name", ""), p.get("weight"), p.get("weight_unit"))
    conn.execute(
        """INSERT INTO product(ean, source_key, name, brand, vendor, package_amount, package_unit,
                               category, image_url, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(source_key) DO UPDATE SET
             package_amount=COALESCE(excluded.package_amount, product.package_amount),
             package_unit=COALESCE(excluded.package_unit, product.package_unit),
             category=COALESCE(excluded.category, product.category),
             image_url=COALESCE(excluded.image_url, product.image_url),
             brand=COALESCE(excluded.brand, product.brand),
             updated_at=excluded.updated_at""",
        (ean, key, p.get("name", ""), p.get("brand"), p.get("vendor"), amount, unit,
         " > ".join(_categories(p)) or None, p.get("image"), _now()),
    )
    return conn.execute("SELECT id FROM product WHERE source_key=?", (key,)).fetchone()["id"]


def upsert_offer(conn: sqlite3.Connection, product_id: int, chain_code: str, p: dict) -> None:
    conn.execute(
        """INSERT INTO offer(product_id, chain_code, store_name, price, unit_price, url, price_date, fetched_at)
           VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(product_id, chain_code) DO UPDATE SET
             store_name=excluded.store_name, price=excluded.price, unit_price=excluded.unit_price,
             url=excluded.url, price_date=excluded.price_date, fetched_at=excluded.fetched_at""",
        (product_id, chain_code, p.get("name", ""), p.get("current_price"), p.get("current_unit_price"),
         p.get("url"), _price_date(p), _now()),
    )


def link(conn: sqlite3.Connection, ingredient_id: int, product_id: int, score: float) -> None:
    # Manuelt verifiserte eller avviste koblinger beholder status; bare poengsum oppdateres.
    conn.execute(
        """INSERT INTO ingredient_product(ingredient_id, product_id, score) VALUES (?,?,?)
           ON CONFLICT(ingredient_id, product_id) DO UPDATE SET score=excluded.score""",
        (ingredient_id, product_id, score),
    )


def import_ingredient(conn: sqlite3.Connection, client: KassalClient, ing: sqlite3.Row,
                      chains: list[sqlite3.Row], max_terms: int = 2) -> dict[str, int]:
    rule = IngredientRule.from_row(ing)
    raw_terms = [t.strip() for t in ing["search_terms"].split("|") if t.strip()][:max_terms]
    counts: dict[str, int] = {}
    # Fjern gamle automatiske koblinger; verifiserte og avviste beholdes.
    conn.execute("DELETE FROM ingredient_product WHERE ingredient_id=? AND status='auto'", (ing["id"],))
    for chain in chains:
        seen: dict[str, tuple[float, dict]] = {}
        raw: list[dict] = []
        for term in raw_terms:
            for p in client.search_products(term, store=chain["kassal_store"], size=50):
                raw.append(p)
                if p.get("current_price") is None:
                    continue
                amount, _ = parse_package(p.get("name", ""), p.get("weight"), p.get("weight_unit"))
                s = score_product(rule, p.get("name", ""), _categories(p), _price_date(p), amount is not None)
                if s is None or s < MIN_SCORE:
                    continue
                key = p.get("ean") or f"id:{p['id']}"
                if key not in seen or s > seen[key][0]:
                    seen[key] = (s, p)
        best = sorted(seen.values(), key=lambda x: -x[0])[:TOP_PER_CHAIN]
        if not best and raw:
            # Viser i jobbloggen hva Kassalapp fant når ingenting ble godtatt.
            for p in raw[:6]:
                print(f"    0 treff {ing['slug']} {chain['code']}: {p.get('name')} | {', '.join(_categories(p))}")
        for s, p in best:
            pid = upsert_product(conn, p)
            upsert_offer(conn, pid, chain["code"], p)
            link(conn, ing["id"], pid, s)
        counts[chain["code"]] = len(best)
    conn.commit()
    return counts


def import_all(conn: sqlite3.Connection, client: KassalClient, only: list[str] | None = None,
               chains: list[str] | None = None, log=print) -> None:
    chain_rows = conn.execute("SELECT * FROM chain ORDER BY code").fetchall()
    if chains:
        chain_rows = [c for c in chain_rows if c["code"] in chains]
    ings = conn.execute("SELECT * FROM ingredient ORDER BY slug").fetchall()
    if only:
        ings = [i for i in ings if i["slug"] in only]
    for i, ing in enumerate(ings, 1):
        counts = import_ingredient(conn, client, ing, chain_rows)
        log(f"[{i}/{len(ings)}] {ing['name']}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
