"""Claude leser ukas tilbudsavis og lister varene med prisene slik de står i avisen.

Brukes av `fetch-offers` når ANTHROPIC_API_KEY er satt. Fungerer for aviser vi har som
bilder (Coop Extra, Mega, Prix, Marked) eller PDF (Kiwi, Spar). For de andre beholdes
prisfallene fra Kassalapp.
"""
from __future__ import annotations

import base64
import json
import urllib.request

from .flyers import UA
from .offers import TERMS

MODEL = "claude-opus-5-5"
MAX_PDF = 24_000_000  # større PDF-er hentes av Claude selv via adressen

ITEM = {
    "type": "object", "additionalProperties": False,
    "required": ["name", "brand", "price", "before", "unit", "deal", "cat"],
    "properties": {
        "name": {"type": "string"},
        "brand": {"type": "string"},
        "price": {"type": "number"},
        "before": {"type": "number"},
        "unit": {"type": "string"},
        "deal": {"type": "string"},
        "cat": {"type": "string", "enum": list(TERMS)},
    },
}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["items"],
          "properties": {"items": {"type": "array", "items": ITEM}}}

PROMPT = (
    "Dette er ukas tilbudsavis fra {store}. List hver vare som har en pris i avisen, én gang per vare. "
    "name: varenavnet slik det står, med pakkestørrelse hvis den står (f.eks. «Kyllingfilet 700 g»). "
    "brand: merket, ellers tom streng. "
    "price: prisen i kroner for én vare slik den er oppgitt (199,- blir 199, 29,90 blir 29.9). Står det «2 for 50», er price 25. "
    "before: førprisen eller veiledende pris hvis den står, ellers 0. "
    "unit: hva prisen gjelder hvis det står, f.eks. «per kg», «per stk», «per pk», ellers tom streng. "
    "deal: kampanjeteksten hvis prisen krever kjøp av flere eller medlemskap, f.eks. «3 for 2», «2 for 50,-», «Trumf-pris», ellers tom streng. "
    "cat: varegruppen som passer best. "
    "Ta bare med det du faktisk kan lese. Er prisen uleselig eller usikker, la varen være ute."
)


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def flyer_content(view: dict | None, get=None) -> list[dict] | None:
    """Avisen som innholdsblokker til Claude, eller None når den ikke kan leses."""
    get = get or _download
    if not view:
        return None
    b64 = lambda raw: base64.standard_b64encode(raw).decode()
    if view.get("type") == "images" and view.get("pages"):
        return [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(get(u))}}
                for u in view["pages"][:90]]
    if view.get("type") == "pdf" and view.get("url"):
        raw = get(view["url"])
        if not raw.startswith(b"%PDF"):
            return None
        if len(raw) > MAX_PDF:
            return [{"type": "document", "source": {"type": "url", "url": view["url"]}}]
        return [{"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64(raw)}}]
    return None


def clean(items: list[dict]) -> list[dict]:
    """Svaret fra Claude til samme form som tilbudene fra Kassalapp, sortert som dem."""
    out, seen = [], set()
    for x in items:
        name = str(x.get("name") or "").strip()[:120]
        try:
            price, before = float(x.get("price") or 0), float(x.get("before") or 0)
        except (TypeError, ValueError):
            continue
        if not name or not 0 < price < 20000 or (name.lower(), price) in seen:
            continue
        seen.add((name.lower(), price))
        before = before if before > price else 0
        out.append({
            "name": name, "brand": str(x.get("brand") or "").strip()[:60],
            "price": round(price, 2), "before": round(before, 2),
            "pct": round((before - price) / before * 100) if before else 0,
            "url": "", "cat": x.get("cat") if x.get("cat") in TERMS else "Middag og tørrvarer",
            "unit": str(x.get("unit") or "").strip()[:30], "deal": str(x.get("deal") or "").strip()[:40], "src": "avis",
        })
    return sorted(out, key=lambda o: (-o["pct"], o["name"]))


def read_flyer(client, store: str, view: dict | None, log=print) -> list[dict] | None:
    content = flyer_content(view)
    if not content:
        return None
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": [*content, {"type": "text", "text": PROMPT.format(store=store)}]}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason != "end_turn":
        log(f"  {store}: AI stoppet ({msg.stop_reason})")
        return None
    text = next((b.text for b in msg.content if b.type == "text"), "")
    return clean(json.loads(text)["items"])


def read_flyers(data: dict, client=None, log=print) -> dict:
    """Bytter ut tilbudene med varene og prisene fra avisen der AI-en klarte å lese den."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic()
    for store in data["stores"]:
        try:
            offers = read_flyer(client, store["name"], store.get("view"), log)
        except Exception as e:  # én avis som feiler skal ikke stoppe resten
            log(f"  {store['name']}: fikk ikke lest avisen med AI ({e})")
            continue
        if offers and len(offers) >= 3:
            store.update(offers=offers, hasData=True, fromFlyer=True)
            log(f"{store['name']}: {len(offers)} varer lest fra avisen")
    return data
