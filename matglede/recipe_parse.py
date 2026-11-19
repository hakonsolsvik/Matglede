"""Tolke ingredienslinjer fra eksterne oppskrifter og koble dem til ingredienstabellen.

Kildene skriver mengder ulikt: Rema bruker schema.org-tekst som "2 spiseskje Salt",
bloggene skriver "1 1/2 ts spisskummen" eller "1 boks (300g) kikerter". Parseren gir
mengde og enhet i appens enheter (g, kg, ml, dl, l, ss, ts, stk, pk). Mengder som
ikke kan handles inn (klype, neve) får enheten beholdt og regnes ikke om.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Kildens enhetsord -> appens enhet. None betyr "ikke en mengde vi kan handle etter".
UNIT_WORDS: dict[str, str | None] = {
    "gram": "g", "g": "g", "gr": "g", "kilogram": "kg", "kg": "kg",
    "milliliter": "ml", "ml": "ml", "centiliter": "cl", "cl": "ml",
    "desiliter": "dl", "dl": "dl", "liter": "l", "l": "l",
    "spiseskje": "ss", "ss": "ss", "teskje": "ts", "ts": "ts",
    "stykk": "stk", "stk": "stk",
    "pakke": "pk", "pk": "pk", "pose": "pk", "glass": "pk", "boks": "pk", "potte": "pk",
    "bunt": "pk", "bundt": "pk",
    "fedd": "fedd",
    "klype": None, "neve": None, "skive": None, "skiver": None,
}
_CL = {"cl": 10.0}

_FRACTIONS = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1 / 3, "⅔": 2 / 3}
_NUM = r"\d+(?:[.,]\d+)?"
_AMOUNT = re.compile(
    rf"^(?:ca\.?\s*)?(?P<a>{_NUM}\s+\d+/\d+|\d+/\d+|{_NUM}|[½¼¾⅓⅔])"
    rf"(?:\s*(?:-|–|til)\s*(?P<b>{_NUM}|\d+/\d+))?\s*",
    re.I,
)
_PAREN_WEIGHT = re.compile(rf"\((?:ca\.?\s*)?({_NUM})\s*(g|gram)\)", re.I)

GRAMS_PER_CLOVE = 5.0  # ett hvitløksfedd
GRAMS_PER_CHICKEN_BREAST = 150.0


def _to_float(s: str) -> float:
    s = s.strip()
    if s in _FRACTIONS:
        return _FRACTIONS[s]
    if " " in s:  # "1 1/2"
        whole, frac = s.split(None, 1)
        return float(whole) + _to_float(frac)
    if "/" in s:
        n, d = s.split("/")
        return float(n) / float(d)
    return float(s.replace(",", "."))


@dataclass
class ParsedLine:
    raw: str
    amount: float | None
    unit: str | None
    name: str


def is_heading(raw: str) -> bool:
    """Underoverskrifter i ingredienslisten ("PESTO:", "Dressing", "-")."""
    s = raw.strip()
    if s in {"", "-", "–"}:
        return True
    if s.endswith(":"):
        return True
    return s.lower() in {"dressing", "sausen", "marinade", "til servering"}


def parse_line(raw: str) -> ParsedLine:
    text = " ".join(raw.replace(" ", " ").split())
    text = text.replace("½", " ½ ").replace("¼", " ¼ ").replace("¾", " ¾ ")
    text = " ".join(text.split())
    m = _AMOUNT.match(text)
    if not m:
        return ParsedLine(raw, None, None, text)
    a = _to_float(m.group("a"))
    if m.group("b"):
        a = (a + _to_float(m.group("b"))) / 2  # "400-500 g" -> 450 g
    rest = text[m.end():]
    # "1 1/2" kan bli fanget som "1" + "1/2" hvis mellomrommet var dobbelt; ok etter normalisering.
    word = re.match(r"([A-Za-zæøåÆØÅ]+)\.?\s*", rest)
    unit = None
    if word and word.group(1).lower() in UNIT_WORDS:
        unit = UNIT_WORDS[word.group(1).lower()]
        rest = rest[word.end():]
        if unit is None:
            return ParsedLine(raw, None, word.group(1).lower(), rest.strip())
        if word.group(1).lower() in _CL:
            a *= _CL[word.group(1).lower()]
    elif re.match(r"store?\s+ss\b", rest, re.I):  # "2 store ss"
        unit, rest = "ss", re.sub(r"^store?\s+ss\s*", "", rest, flags=re.I)
    if unit == "pk":
        pw = _PAREN_WEIGHT.search(rest)
        if pw:  # "1 boks (300g) kikerter" -> 300 g
            a, unit = a * float(pw.group(1).replace(",", ".")), "g"
            rest = _PAREN_WEIGHT.sub("", rest)
    if unit is None:
        # Uten enhet: store tall er gram ("500 poteter"), ellers antall stykk.
        unit = "g" if a >= 50 else "stk"
    return ParsedLine(raw, round(a, 3), unit, rest.strip(" ,"))


# Regler for kobling: (slug, ord som må finnes, ord som utelukker). Første treff vinner,
# så de mest spesifikke står først. Matchen gjøres på hovednavnet (før komma).
RULES: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
    ("hakkede_tomater", ("hakkede tomater", "hakket tomat"), ()),
    ("tomatpure", ("tomatpuré", "tomatpure"), ()),
    ("currypaste", ("rød currypast", "red curry"), ()),
    ("kokosmelk", ("kokosmelk",), ()),
    ("rodlok", ("rødløk", "rød løk"), ("syltet",)),
    ("hvitlok", ("hvitløk", "hviløk"), ("pulver", "olje", "smør")),
    ("lok", ("løk",), ("vårløk", "purre", "pulver", "sjalott", "perleløk", "stekt løk", "sprøstekt")),
    ("kjottdeig", ("kjøttdeig",), ("kylling", "svin")),
    ("kyllingfilet", ("kyllingfilet", "kyllingbryst", "strimlet kyllingfilet"), ("lår",)),
    ("laksefilet", ("laks",), ("røkt", "gravet")),
    ("bacon", ("bacon",), ()),
    ("egg", ("egg", "eggeplomme"), ("nudler", "eggnudler")),
    ("flote", ("fløte",), ("crème", "creme", "sur")),
    ("melk", ("melk", "lettmelk", "helmelk"), ("kokos", "kjerne")),
    ("smor", ("smør", "meierismør"), ("peanøtt", "mandel", "nøtt")),
    ("parmesan", ("parmesan",), ()),
    ("ost_revet", ("revet ost", "gulost", "revet gulost"), ()),
    ("romme", ("rømme",), ()),
    ("potet", ("potet", "poteter", "nypotet"), ("søtpotet", "potetmel")),
    ("gulrot", ("gulrot", "gulrøtter"), ()),
    ("brokkoli", ("brokkoli",), ()),
    ("paprika", ("paprika",), ("pulver", "malt", "hot", "røkt")),
    ("tomat", ("tomat", "tomater", "plommetomat"), ("soltørk", "cherry", "puré", "sylt")),
    ("agurk", ("agurk",), ("sylte",)),
    ("isbergsalat", ("isbergsalat", "issalat"), ()),
    ("sitron", ("sitron",), ("pepper", "gress", "melisse")),
    ("spaghetti", ("spaghetti", "spagetti"), ()),
    ("ris", ("ris", "basmatiris", "jasminris"), ("nudler", "eddik", "vin", "papir", "mel")),
    ("tortilla", ("tortilla",), ("chips",)),
    ("tacokrydder", ("tacokrydder",), ()),
    ("tacosaus", ("tacosaus",), ()),
    ("mais", ("mais", "maiskorn"), ("maisenna", "maismel")),
    ("olivenolje", ("olivenolje", "oliven olje", "oiivenolje"), ()),
    ("salt", ("salt", "flaksalt", "havsalt"), ("usalt", "saltet")),
    ("pepper", ("pepper",), ("kajenne", "cayenne", "chili", "hvit", "sitronpepper", "paprika")),
    ("mel", ("hvetemel", "siktet hvetemel"), ("sammalt", "fullkorn", "grov")),
    ("erter", ("erter",), ("sukker", "kikert")),
]

# Enkelte ord gjelder bare som hele ord (ellers treffer "ris" i "prisbelønt", "egg" i "eggnudler").
_WHOLE_WORD = {"ris", "egg", "salt", "mais", "løk", "laks", "melk", "smør", "tomat", "potet", "pepper"}


def _has(term: str, text: str) -> bool:
    if term in _WHOLE_WORD:
        return re.search(rf"(?<![a-zæøå]){re.escape(term)}(?:er|en|ene)?(?![a-zæøå])", text) is not None
    return term in text


def match_ingredient(name: str, unit: str | None = None) -> str | None:
    """Gi slug for ingrediensen, eller None hvis den ikke finnes i tabellen."""
    head = name.lower().split(",")[0]
    head = re.sub(r"\(.*?\)", "", head)
    for slug, needles, excludes in RULES:
        if any(_has(n, head) for n in needles) and not any(e in head for e in excludes):
            # "2 ts paprika" er krydder, ikke grønnsak.
            if slug == "paprika" and unit in {"ts", "ss"}:
                return None
            return slug
    return None


# Vanlig pakningsstørrelse når oppskriften sier "1 boks" eller "1 glass".
PACK_SIZES: dict[str, tuple[float, str]] = {
    "hakkede_tomater": (400, "g"),
    "kokosmelk": (400, "ml"),
    "currypaste": (110, "g"),
    "mais": (340, "g"),
    "tacosaus": (230, "g"),
    "tacokrydder": (28, "g"),
}


def normalise_for_ingredient(slug: str | None, amount: float | None, unit: str | None,
                             name: str = "") -> tuple[float | None, str | None]:
    """Gjør om enheter som bare gir mening for én ingrediens.

    Fedd hvitløk blir gram (ingrediensen regner 50 g per hode), og "1 boks hakkede
    tomater" blir 400 g.
    """
    if amount is None or unit is None:
        return amount, unit
    if slug == "hvitlok" and (unit == "fedd" or (unit == "stk" and "fedd" in name.lower())):
        return round(amount * GRAMS_PER_CLOVE, 3), "g"
    if unit == "fedd":
        return amount, "stk"
    if slug == "kyllingfilet" and unit == "stk":  # ett kyllingbryst
        return round(amount * GRAMS_PER_CHICKEN_BREAST, 3), "g"
    if slug in PACK_SIZES and unit in {"pk", "stk"}:
        size, u = PACK_SIZES[slug]
        return round(amount * size, 3), u
    return amount, unit


def split_combined(name: str) -> list[str]:
    """'Salt og pepper' er to ingredienser."""
    if re.fullmatch(r"salt og (?:sort |kvernet )?pepper", name.strip().lower()):
        return ["salt", "pepper"]
    return [name]


def parse_servings(text: str | None) -> int | None:
    """'4 porsjoner', 'Personer: 4 - 6' -> 4. Tom tekst gir None."""
    if not text:
        return None
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None
