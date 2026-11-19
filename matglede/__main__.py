"""Kommandolinje: python -m matglede <kommando>"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta

import os

from . import app_export, db, external
from .kassal import KassalClient, load_dotenv
from .importer import import_all
from .shopping import compare_chains, shopping_list


def cmd_init(conn, args):
    db.init_db(conn)
    print(f"Ingredienser: {db.load_ingredients(conn)}, oppskrifter: {db.load_recipes(conn)}")
    n, skipped = external.load(conn)
    print(f"Eksterne oppskrifter: {n} ({skipped} ingredienslinjer uten kobling hoppet over)")


def cmd_external(conn, args):
    data = external.build()
    c = external.coverage(data)
    print(f"Skrev {len(data['recipes'])} oppskrifter til {external.OUT.relative_to(external.ROOT)}")
    print(f"Koblet {c['mapped']} av {c['lines']} ingredienslinjer. Vanligste som mangler i tabellen:")
    for name, count in c["top_missing"]:
        print(f"  {count:>3}  {name}")


def cmd_export_app(conn, args):
    has_db = os.path.exists(args.db)
    data = app_export.build(conn if has_db else None)
    out = app_export.write(data)
    st = data["stats"]
    print(f"Skrev {out.relative_to(app_export.ROOT)}: {st['recipes']} oppskrifter")
    print(f"Koblet til ingrediens: {st['mapped']} av {st['lines']} ingredienslinjer")
    if data["hasPrices"]:
        print(f"Priser funnet for {st['pricedIngredients']} av {st['ingredients']} ingredienser")
    else:
        print("Ingen priser: kjør `init` og `import` først (krever KASSAL_API_KEY)")


def cmd_import(conn, args):
    load_dotenv()
    import_all(conn, KassalClient(), only=args.only, chains=args.chains)


def cmd_demo_plan(conn, args):
    monday = date.today() - timedelta(days=date.today().weekday())
    slugs = [r["slug"] for r in conn.execute("SELECT slug FROM recipe ORDER BY id LIMIT 5")]
    entries = [((monday + timedelta(days=i)).isoformat(), s, args.servings) for i, s in enumerate(slugs)]
    pid = db.create_meal_plan(conn, "Demo-uke", monday.isoformat(), entries)
    print(f"Laget ukeplan {pid}: " + ", ".join(slugs))


def cmd_list(conn, args):
    lines = shopping_list(conn, args.plan, args.chain.upper())
    if args.json:
        json.dump([asdict(l) for l in lines], sys.stdout, ensure_ascii=False, indent=2)
        print()
        return
    total = 0.0
    for l in lines:
        if l.product:
            total += l.total
            flag = "  (gammel pris)" if l.stale else ""
            print(f"{l.ingredient:<22} {l.need:<14} {l.packages} x {l.product[:45]:<45} {l.total:>8.2f} kr{flag}")
        else:
            print(f"{l.ingredient:<22} {l.need:<14} -- ikke funnet i {args.chain.upper()}")
    print(f"{'Sum':<22} {'':<14} {'':<49} {total:>8.2f} kr")


def cmd_compare(conn, args):
    for r in compare_chains(conn, args.plan):
        miss = f", mangler: {', '.join(r['missing'])}" if r["missing"] else ""
        stale = f", {r['stale_prices']} gamle priser" if r["stale_prices"] else ""
        print(f"{r['chain']:<10} {r['total']:>8.2f} kr  ({r['found']} varer{stale}{miss})")


def cmd_review(conn, args):
    rows = conn.execute(
        """SELECT p.id, p.ean, p.name, ip.score, ip.status,
                  GROUP_CONCAT(o.chain_code || ' ' || printf('%.2f', o.price), ', ') AS prices
           FROM ingredient_product ip
           JOIN ingredient i ON i.id = ip.ingredient_id
           JOIN product p ON p.id = ip.product_id
           LEFT JOIN offer o ON o.product_id = p.id
           WHERE i.slug = ? GROUP BY p.id ORDER BY ip.score DESC""",
        (args.ingredient,),
    ).fetchall()
    for r in rows:
        print(f"{r['id']:>6} {r['status']:<8} {r['score']:>5.2f} {r['ean'] or '-':<14} {r['name'][:50]:<50} {r['prices']}")


def cmd_mark(conn, args):
    ing = conn.execute("SELECT id FROM ingredient WHERE slug=?", (args.ingredient,)).fetchone()
    if not ing:
        sys.exit(f"Ukjent ingrediens: {args.ingredient}")
    cur = conn.execute("UPDATE ingredient_product SET status=? WHERE ingredient_id=? AND product_id=?",
                       (args.status, ing["id"], args.product_id))
    conn.commit()
    print("Oppdatert" if cur.rowcount else "Fant ikke koblingen")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="matglede")
    ap.add_argument("--db", default="matglede.db")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Opprett database og last inn startdata").set_defaults(fn=cmd_init)

    sub.add_parser("build-external", help="Tolk seed/sources/*.json til seed/external_recipes.json"
                   ).set_defaults(fn=cmd_external)

    sub.add_parser("export-app", help="Skriv app/data.js med oppskrifter og priser til appen"
                   ).set_defaults(fn=cmd_export_app)

    p = sub.add_parser("import", help="Hent produkter fra Kassalapp")
    p.add_argument("--only", nargs="*", help="Bare disse ingrediens-slugene")
    p.add_argument("--chains", nargs="*", help="Bare disse kjedene (ODA KIWI MENY REMA COOP SPAR JOKER)")
    p.set_defaults(fn=cmd_import)

    p = sub.add_parser("demo-plan", help="Lag en ukeplan med fem middager")
    p.add_argument("--servings", type=int, default=4)
    p.set_defaults(fn=cmd_demo_plan)

    p = sub.add_parser("list", help="Handleliste for en ukeplan i en kjede")
    p.add_argument("--plan", type=int, required=True)
    p.add_argument("--chain", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("compare", help="Sammenlign totalpris mellom kjeder")
    p.add_argument("--plan", type=int, required=True)
    p.set_defaults(fn=cmd_compare)

    p = sub.add_parser("review", help="Vis produktkoblinger for en ingrediens")
    p.add_argument("ingredient")
    p.set_defaults(fn=cmd_review)

    for status in ("verified", "rejected"):
        p = sub.add_parser("verify" if status == "verified" else "reject",
                           help=f"Merk kobling som {status}")
        p.add_argument("ingredient")
        p.add_argument("product_id", type=int)
        p.set_defaults(fn=cmd_mark, status=status)

    args = ap.parse_args(argv)
    if args.cmd == "export-app" and not os.path.exists(args.db):
        args.fn(None, args)  # uten database: ingen priser, ikke lag en tom fil
        return
    conn = db.connect(args.db)
    args.fn(conn, args)


if __name__ == "__main__":
    main()
