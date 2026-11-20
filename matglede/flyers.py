"""Finn ukas tilbudsavis hos hver kjede, slik at appen kan vise den på butikksiden.

Vi lagrer bare adressene. Appen henter avissidene direkte fra kjedenes egne servere,
så ingenting av avisene kopieres hit.

Typer:
- images: avissider som bilder (Coop Extra, Mega, Prix, Marked)
- pdf:    PDF på kjedens nettside, vises i en innebygd ramme (Kiwi, Spar)
- embed:  kjedens egen avisleser som tillater innebygging (Meny og Obs bruker iPaper)
- link:   avisen kan ikke bygges inn (Joker bruker Flipsnack, Rema 1000 og Bunnpris Tjek)
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

POSTCODE = "0674"  # Oslo. Kiwi, Spar og Meny gir avisen ut fra postnummer
UA = "Mozilla/5.0 (compatible; matglede-tilbud/1.0)"

# Coop: én butikk i Oslo per kjede. Avisen er lik for hele regionen.
COOP_STORE = {"EXTRA": 4077, "MEGA": 4559, "PRIX": 2633, "OBS": 2541, "MARKED": 4256}
NG_SITE = {"KIWI": "https://kiwi.no", "SPAR": "https://spar.no", "MENY": "https://meny.no", "JOKER": "https://joker.no"}
EMBEDDABLE_HOSTS = ("kundeavis.meny.no", "kundeavis-obs.coop.no", "ipaper.io")
LINKS = {
    "ODA": "https://oda.com/no/products/discounts/",
    "REMA": "https://www.rema.no/kampanjer/",
    "BUNNPRIS": "https://mattilbud.no/kundeaviser/bunnpris-no",
}


def _get(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.geturl(), resp.read().decode("utf-8", "replace")


def norgesgruppen(code: str) -> dict:
    base = NG_SITE[code]
    _, body = _get(f"{base}/api/kundeavis?postCode={POSTCODE}")
    url = urllib.parse.urljoin(base, json.loads(body)["url"])
    if "/filer/" in url:
        return {"type": "pdf", "url": url}
    if urllib.parse.urlparse(url).hostname in EMBEDDABLE_HOSTS:
        return {"type": "embed", "url": url}
    return {"type": "link", "url": url}


def coop_pages(html: str, base: str) -> list[str]:
    si_dir = re.search(r"g_cfg\.si_dir\s*=\s*'([^']+)'", html)
    imgs = re.findall(r'"img"\s*:\s*"([^"]+\.jpg[^"]*)"', html)
    if not si_dir or not imgs:
        return []
    return [urllib.parse.urljoin(base, si_dir.group(1) + img) for img in imgs]


def coop(code: str) -> dict:
    final, html = _get(f"https://kundeavis.coop.no/aviser/?id={COOP_STORE[code]}")
    pages = coop_pages(html, final)
    if pages:
        return {"type": "images", "spreads": True, "pages": pages, "url": final}
    host = urllib.parse.urlparse(final).hostname or ""
    if any(host == h or host.endswith("." + h) for h in EMBEDDABLE_HOSTS):
        return {"type": "embed", "url": final}
    return {"type": "link", "url": final}


def flyer_for(code: str, log=print) -> dict | None:
    try:
        if code in NG_SITE:
            return norgesgruppen(code)
        if code in COOP_STORE:
            return coop(code)
    except Exception as e:  # nettsidene endrer seg; da viser appen lenken i stedet
        log(f"  Fant ikke avisen for {code}: {e}")
        return None
    return {"type": "link", "url": LINKS[code]} if code in LINKS else None
