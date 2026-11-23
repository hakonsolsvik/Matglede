"""Ukas tilbud per butikk til Tilbud-siden i appen (app/offers.js).

Kilden er prishistorikken i Kassalapp. En vare regnes som på tilbud når prisen
i dag er minst 10 % og 3 kr lavere enn medianprisen de 8 til 60 foregående dagene.
Selve avisen finnes av flyers.py. Appen viser den fra kjedens egen server, uten
å kopiere den.

Kjøres hver mandag kl. 12 norsk tid av .github/workflows/tilbud.yml.
"""
from __future__ import annotations

import datetime as dt
import json
import statistics
import urllib.error
from zoneinfo import ZoneInfo
from pathlib import Path

from .flyers import flyer_for
from .kassal import KassalClient
from .matching import IngredientRule, score_product
from .units import parse_package, to_base

# code, navn, Kassalapp-butikk (None = ingen ferske priser i Kassalapp), lenke til ukas avis
STORES = [
    ("ODA", "Oda", "ODA_NO", "https://oda.com/no/products/discounts/"),
    ("KIWI", "Kiwi", "KIWI", "https://mattilbud.no/kundeaviser/kiwi-no"),
    ("MENY", "Meny", "MENY_NO", "https://meny.no/kampanjer"),
    ("REMA", "Rema 1000", None, "https://mattilbud.no/kundeaviser/rema-1000-no"),
    ("EXTRA", "Coop Extra", None, "https://mattilbud.no/kundeaviser/extra-no"),
    ("MEGA", "Coop Mega", None, "https://mattilbud.no/kundeaviser/coop-mega-no"),
    ("PRIX", "Coop Prix", None, "https://mattilbud.no/kundeaviser/coop-prix-no"),
    ("OBS", "Coop Obs", None, "https://mattilbud.no/kundeaviser/obs-no"),
    ("MARKED", "Coop Marked", None, "https://mattilbud.no/kundeaviser/coop-marked-no"),
    ("SPAR", "Spar", "SPAR_NO", "https://spar.no/spar-kundeavis"),
    ("JOKER", "Joker", "JOKER_NO", "https://publ.joker.no"),
    ("BUNNPRIS", "Bunnpris", "BUNNPRIS", "https://mattilbud.no/kundeaviser/bunnpris-no"),
]

# Søkeord som dekker det meste av en vanlig handlekurv, gruppert slik avisen viser dem
TERMS = {
    "Kjøtt og kylling": ["kjøttdeig", "kylling", "svinekjøtt", "biff", "pølser", "bacon", "kjøttkaker", "skinke", "ribbe", "lam"],
    "Fisk": ["laks", "torsk", "fiskekaker", "reker", "makrell"],
    "Meieri og egg": ["melk", "ost", "yoghurt", "smør", "rømme", "fløte", "egg"],
    "Frukt og grønt": ["eple", "banan", "tomat", "agurk", "potet", "løk", "paprika", "salat", "appelsin", "druer"],
    "Brød og frokost": ["brød", "knekkebrød", "müsli", "pålegg"],
    "Middag og tørrvarer": ["pasta", "ris", "taco", "pizza", "suppe", "saus", "hermetikk"],
    "Drikke og kaffe": ["kaffe", "juice", "brus", "smoothie"],
    "Snacks og søtt": ["sjokolade", "chips", "iskrem", "kjeks", "godteri"],
    "Hus og hjem": ["vaskemiddel", "tørkerull", "toalettpapir", "tannkrem", "sjampo"],
}

MIN_PCT = 0.10
MIN_KR = 3.0


def _ts(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def offer_from_product(p: dict, now: dt.datetime) -> dict | None:
    hist = sorted(p.get("price_history") or [], key=lambda h: h["date"], reverse=True)
    if not hist or hist[0].get("price") is None or (now - _ts(hist[0]["date"])).days > 8:
        return None
    cur = float(hist[0]["price"])
    ref = [float(h["price"]) for h in hist if h.get("price") and 8 <= (now - _ts(h["date"])).days <= 60]
    if len(ref) < 3:
        return None
    before = statistics.median(ref)
    if cur > before * (1 - MIN_PCT) or before - cur < MIN_KR:
        return None
    return {
        "name": p["name"].strip(),
        "brand": (p.get("brand") or "").strip(),
        "price": round(cur, 2),
        "before": round(before, 2),
        "pct": round((before - cur) / before * 100),
        "url": p.get("url") or "",
        "img": p.get("image") or "",  # vises fra Kassalapps bildeserver, kopieres ikke
    }


def top_category(p: dict) -> str | None:
    """Øverste varegruppe i Kassalapp (laveste depth), f.eks. «Middag» eller «Meieri og egg»."""
    cats = [c for c in (p.get("category") or []) if c.get("name")]
    return min(cats, key=lambda c: c.get("depth", 0))["name"] if cats else None


def week_info(today: dt.date) -> dict:
    monday = today - dt.timedelta(days=today.weekday())
    sunday = monday + dt.timedelta(days=6)
    return {"week": monday.isocalendar()[1], "from": monday.isoformat(), "to": sunday.isoformat()}


def build_offers(client: KassalClient, now: dt.datetime | None = None, log=print) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    stores = []
    for code, name, kassal_code, flyer in STORES:
        offers: dict[str, dict] = {}
        if kassal_code:
            for cat, terms in TERMS.items():
                for term in terms:
                    try:
                        found = client.search_products(term, store=kassal_code, size=100)
                    except urllib.error.HTTPError as e:
                        log(f"  {name}: hoppet over «{term}» ({e.code})")
                        continue
                    for p in found:
                        o = offer_from_product(p, now)
                        key = p.get("ean") or p.get("id")
                        if o and key not in offers:
                            offers[key] = {**o, "cat": top_category(p) or cat}
        ranked = sorted(offers.values(), key=lambda o: (-o["pct"], o["name"]))
        log(f"{name}: {len(ranked)} varer på tilbud")
        view = flyer_for(code, log)
        log(f"  avis: {view['type'] if view else 'ikke funnet'}")
        stores.append({"code": code, "name": name, "flyer": (view or {}).get("url") or flyer, "view": view,
                       "hasData": bool(kassal_code), "offers": ranked})
    return {"generated": now.astimezone(ZoneInfo("Europe/Oslo")).strftime("%Y-%m-%d %H:%M"),
            **week_info(now.astimezone(ZoneInfo("Europe/Oslo")).date()), "stores": stores}


def tag_offers(data: dict, ingredients: dict[str, dict]) -> dict:
    """Merk tilbud som passer en ingrediens med `ing` og pakkestørrelse `size` i basisenhet.

    Sparegrisen i appen bruker dem som billigere varer. Krever et helt ord-treff uten
    utelukkende ord ("Kyllinglår med smør" blir ikke smør) og kjent pakkestørrelse.
    """
    rules = {slug: IngredientRule.from_row(row) for slug, row in ingredients.items()}
    for store in data["stores"]:
        for o in store["offers"]:
            o.pop("ing", None), o.pop("size", None)
            amt, unit = parse_package(o["name"])
            if not amt:
                continue
            hits = [(sc, slug) for slug, rule in rules.items()
                    if (sc := score_product(rule, o["name"], [], None, True)) is not None and sc >= 4.5]
            if not hits:
                continue
            slug = max(hits)[1]
            row = ingredients[slug]
            size = to_base(amt, unit, row["base_unit"], float(row["grams_per_piece"] or 0) or None)
            if size:
                o["ing"], o["size"] = slug, round(size, 3)
    return data


def write_offers_js(data: dict, path: str | Path = "app/offers.js") -> None:
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    Path(path).write_text("// Generert av `python -m matglede fetch-offers`. Ikke rediger for hånd.\n"
                          f"window.MATGLEDE_OFFERS = {body};\n", encoding="utf-8")
