"""Før-priser fra kundeavisene til alle kjedene, samlet uke for uke i app/forpriser.js.

Kilden er de samme avisene som mattilbud.no viser (Tjek). Hver vare i avisen har tilbudsprisen
og ofte «Førpris 42,90». Før-prisen er butikkens vanlige pris, og appen bruker den som det
(pantry.js flyerPrices). Arkivet beholder siste kjente før-pris per vare og kjede, så nyeste
avis vinner og historikken vokser hver mandag.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

from .flyers import UA
from .offers import tag_offers

API = "https://squid-api.tjek.com/v2"
OSLO = {"r_lat": "59.9139", "r_lng": "10.7522", "r_radius": "15000"}
# Kjedens code i appen -> forhandler-id hos Tjek
DEALERS = {"KIWI": "257bxm", "REMA": "faa0Ym", "EXTRA": "80742m", "MEGA": "de79dm", "PRIX": "f5d5lm",
           "OBS": "51dawm", "MARKED": "68baam", "SPAR": "c062vm", "MENY": "4333pm", "JOKER": "b3e8Fm",
           "BUNNPRIS": "5b11sm"}
CODE = {v: k for k, v in DEALERS.items()}
OUT = Path("app/forpriser.js")

_BEFORE = re.compile(r"f[øo]r(?:pris)?\s*:?\s*(?:kr\.?\s*)?(\d+(?:[.,]\d+)?)", re.I)
_CUT = re.compile(r"(,?\s*[\d.,/-]+\s*)?\bpr\.?\s+(kg|l|stk|pk)\b|\benh\.?\s*pris|\bf[øo]r(pris)?\s*:?\s*\d", re.I)


def _get(path: str, **params) -> list:
    url = f"{API}/{path}?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch(get=_get) -> list[dict]:
    """Alle varene i kjedenes aviser som gjelder nå, rett fra Tjek."""
    out = []
    for c in get("catalogs", dealer_ids=",".join(DEALERS.values()), limit=100, **OSLO):
        for off in range(0, 2000, 100):
            page = get("offers", catalog_id=c["id"], limit=100, offset=off)
            out += page
            if len(page) < 100:
                break
    return out


def to_offer(raw: dict) -> dict | None:
    """Én avisvare med før-pris, i samme form som tilbudene i offers.js. None uten før-pris."""
    code = CODE.get(raw.get("dealer_id"))
    p = raw.get("pricing") or {}
    price, before = p.get("price"), p.get("pre_price")
    desc = raw.get("description") or ""
    if not before and (m := _BEFORE.search(desc)):
        before = float(m.group(1).replace(",", "."))
    if not code or not price or not before or before <= price:
        return None
    first = desc.split("\n")[0]
    first = first[:m.start()] if (m := _CUT.search(first)) else first
    name = re.sub(r"\s+", " ", f"{raw.get('heading', '')} {first}").strip(" ,.")[:120]
    return {"code": code, "name": name, "price": round(float(price), 2), "before": round(float(before), 2),
            "week": (raw.get("run_from") or "")[:10]}


def merge(archive: dict, raws: list[dict]) -> tuple[dict, list[dict]]:
    """Legg ukas før-priser inn i arkivet. Samme vare i samme kjede: nyeste uke vinner."""
    by = {s["code"]: {o["name"].lower(): o for o in s["offers"]} for s in archive.get("stores", [])}
    new = []
    for raw in raws:
        o = to_offer(raw)
        if not o:
            continue
        code = o.pop("code")
        old = by.setdefault(code, {}).get(o["name"].lower())
        if old and old["week"] > o["week"]:
            continue
        by[code][o["name"].lower()] = o
        new.append({**o, "code": code, "old": old["before"] if old else None})
    stores = [{"code": c, "fromFlyer": True, "offers": sorted(by[c].values(), key=lambda o: o["name"])} for c in sorted(by)]
    return {"stores": stores}, new


def keep_tagged(data: dict, ingredients: dict[str, dict]) -> dict:
    """Merk varene med ingrediens og pakkestørrelse, og behold bare dem appen kan bruke."""
    # shortcut: varer uten ingrediens i dag kastes, så en ny ingrediens får før-priser først fra neste avis
    tag_offers(data, ingredients)
    for s in data["stores"]:
        s["offers"] = [o for o in s["offers"] if o.get("ing")]
    return data


def load(path: Path = OUT) -> dict:
    if not path.exists():
        return {"stores": []}
    s = path.read_text(encoding="utf-8")
    return json.loads(s[s.index("{"):s.rindex("}") + 1])


def write(data: dict, path: Path = OUT) -> None:
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text("// Generert av `python -m matglede fetch-forpriser`. Ikke rediger for hånd.\n"
                    f"window.MATGLEDE_FORPRISER = {body};\n", encoding="utf-8")
