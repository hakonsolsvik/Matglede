"""Trykkbare aviser: avissidene og hvor hver vare står på siden, i app/aviser.js.

Kilden er Tjek (samme som mattilbud.no). For hver kjede tar vi ukas avis, adressene til
sidebildene og «hotspots»: firkanten rundt hver vare med navn og pris. Appen legger en
usynlig knapp over hver vare, så man kan trykke på varen i avisen og legge den i handlelisten.

Tilbud som gjelder flere varer («Coca-Cola/Fanta/Sprite», «filtermalt/hele bønner») deles
i varianter. Står det bare «hele sortimentet», ser Claude (når ANTHROPIC_API_KEY er satt)
på utsnittet av avisen og lister varene som er avbildet.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .forpriser import _BEFORE, _get, DEALERS, OSLO, CODE

OUT = Path("app/aviser.js")
MULTI = re.compile(r"\balt\b|\bhele\b|sortiment|utvalg|varianter|\d+\s*%\s*(rabatt|på)", re.I)
MAX_AI = 40  # utsnitt Claude ser på per uke


def pick(catalogs: list[dict]) -> dict[str, dict]:
    """Ukas hovedavis per kjede: nyeste startdato, så flest sider (ikke en julekatalog som har gått i ukesvis)."""
    best = {}
    for c in catalogs:
        code = CODE.get(c.get("dealer_id"))
        key = (c.get("run_from") or "", c.get("page_count") or 0)
        if code and (code not in best or key > best[code][0]):
            best[code] = (key, c)
    return {k: v[1] for k, v in best.items()}


def nice(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s[:1] + s[1:].lower() if s.isupper() else s


def variants(heading: str, desc: str) -> list[str]:
    """Varene et tilbud gjelder, når avisen lister dem med skråstrek. Ellers tom liste."""
    split = lambda s: [p.strip(" .") for p in s.split("/") if p.strip(" .")]
    if len(parts := split(heading)) > 1:
        return [nice(p) for p in parts]
    for seg in re.split(r"[,.\n]", desc or ""):
        if "/" in seg and not re.search(r"\d", seg) and len(parts := split(seg)) > 1:
            return [f"{nice(heading)} {p.lower()}" for p in parts]
    return []


def box(poly: list) -> tuple[float, float, float, float]:
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


def build_store(cat: dict, pages: list[dict], hotspots: list[dict], offers: list[dict]) -> dict:
    """Én avis i formen appen bruker. y og h regnes om fra sidebredder til andel av sidehøyden."""
    ratio = (cat.get("dimensions") or {}).get("height") or 1.4
    full = {o["id"]: o for o in offers}
    hot = []
    for h in hotspots:
        if h.get("type") != "offer" or not h.get("offer"):
            continue
        o = {**h["offer"], **full.get(h["id"], {})}
        p = o.get("pricing") or {}
        if not p.get("price"):
            continue
        desc = o.get("description") or ""
        before = p.get("pre_price")
        if not before and (m := _BEFORE.search(desc)):
            before = float(m.group(1).replace(",", "."))
        item = {"n": nice(o.get("heading") or ""), "p": round(float(p["price"]), 2),
                "d": re.sub(r"\s+", " ", desc.split("\n")[0]).strip()[:80]}
        if before and before > item["p"]:
            item["b"] = round(float(before), 2)
        if v := variants(o.get("heading") or "", desc):
            item["v"] = v
        elif MULTI.search(f"{o.get('heading')} {desc}") and (o.get("images") or {}).get("view"):
            item["img"] = o["images"]["view"]  # Claude lister varene på bildet (see_products)
        for pg, poly in (h.get("locations") or {}).items():
            x, y, w, hh = box(poly)
            if w <= 0 or hh <= 0:
                continue
            hot.append({**item, "pg": int(pg) - 1,
                        "r": [round(x, 4), round(y / ratio, 4), round(w, 4), round(hh / ratio, 4)]})
    return {"id": cat["id"], "ratio": round(ratio, 4), "label": cat.get("label") or "",
            "pages": [p.get("view") or p.get("zoom") for p in pages], "hot": hot}


def fetch(get=_get, log=print) -> dict:
    cats = pick(get("catalogs", dealer_ids=",".join(DEALERS.values()), limit=100, **OSLO))
    stores = {}
    for code, cat in sorted(cats.items()):
        try:
            offers = []
            for off in range(0, 2000, 100):
                page = get("offers", catalog_id=cat["id"], limit=100, offset=off)
                offers += page
                if len(page) < 100:
                    break
            stores[code] = build_store(cat, get(f"catalogs/{cat['id']}/pages"),
                                       get(f"catalogs/{cat['id']}/hotspots"), offers)
            log(f"  {code}: {len(stores[code]['pages'])} sider, {len(stores[code]['hot'])} trykkbare varer")
        except Exception as e:  # én kjede som feiler skal ikke stoppe resten
            log(f"  {code}: fikk ikke hentet avisen ({e})")
    return {"stores": stores}


SEE = {"type": "object", "additionalProperties": False, "required": ["items"],
       "properties": {"items": {"type": "array", "items": {"type": "string"}}}}


def see_products(data: dict, client=None, log=print) -> dict:
    """Claude ser på utsnittet av tilbud som «30 % på alt av taco» og lister varene som er avbildet."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic()
    from .flyer_ai import MODEL
    seen, n = {}, 0
    for s in data["stores"].values():
        for h in s["hot"]:
            url = h.pop("img", None)
            if not url:
                continue
            if url not in seen and n < MAX_AI:
                n += 1
                try:
                    msg = client.beta.messages.create(
                        model=MODEL, max_tokens=2000,
                        betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                        output_config={"format": {"type": "json_schema", "schema": SEE}},
                        messages=[{"role": "user", "content": [
                            {"type": "image", "source": {"type": "url", "url": url}},
                            {"type": "text", "text": f"Utsnitt fra en tilbudsavis: «{h['n']}». {h['d']} "
                             "List hver vare du ser avbildet, med merke og variant slik det står på pakken "
                             "(f.eks. «Old El Paso tacoskjell 12 stk»). Bare varer du faktisk ser. Tom liste hvis ingen."}]}])
                    text = next((b.text for b in msg.content if b.type == "text"), "{}")
                    seen[url] = [str(x).strip()[:80] for x in json.loads(text).get("items", []) if str(x).strip()][:30]
                except Exception as e:
                    log(f"  fikk ikke lest «{h['n']}» ({e})")
                    seen[url] = []
            if len(seen.get(url) or []) > 1:
                h["v"] = seen[url]
    log(f"  AI så på {n} tilbud med flere varer")
    return data


def write(data: dict, path: Path = OUT) -> None:
    for s in data["stores"].values():  # bildeadressene til AI skal ikke med i appen
        for h in s["hot"]:
            h.pop("img", None)
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text("// Generert av `python -m matglede fetch-aviser`. Ikke rediger for hånd.\n"
                    f"window.MATGLEDE_AVISER = {body};\n", encoding="utf-8")
