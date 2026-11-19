"""Enheter: tolke pakningsstørrelser og regne oppskriftsmengder om til basisenhet."""
from __future__ import annotations

import re

# Oppskriftsenhet -> (basisenhet, faktor)
RECIPE_UNITS: dict[str, tuple[str, float]] = {
    "g": ("g", 1.0),
    "kg": ("g", 1000.0),
    "ml": ("ml", 1.0),
    "cl": ("ml", 10.0),
    "dl": ("ml", 100.0),
    "l": ("ml", 1000.0),
    "ss": ("ml", 15.0),
    "ts": ("ml", 5.0),
    "stk": ("stk", 1.0),
    "pk": ("pk", 1.0),
}

_PACK_UNITS = {
    "g": ("g", 1.0), "gr": ("g", 1.0), "kg": ("g", 1000.0),
    "ml": ("ml", 1.0), "cl": ("ml", 10.0), "dl": ("ml", 100.0), "l": ("ml", 1000.0),
    "stk": ("stk", 1.0), "pk": ("stk", 1.0), "piece": ("stk", 1.0),
}

_MULTI = re.compile(r"(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*(kg|gr|g|ml|cl|dl|l)\b", re.I)
_SINGLE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|gr|g|ml|cl|dl|l|stk|pk)\b", re.I)


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def parse_package(name: str, weight=None, weight_unit=None) -> tuple[float | None, str | None]:
    """Finn pakningsstørrelse i basisenhet (g/ml/stk).

    Bruker Kassalapps weight-felt når det finnes, ellers tolkes produktnavnet
    ("Kjøttdeig 400g", "12x400g", "1,5 l").
    """
    if weight and weight_unit and str(weight_unit).lower() in _PACK_UNITS:
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 0.0
        if w > 0:
            unit, factor = _PACK_UNITS[str(weight_unit).lower()]
            return round(w * factor, 3), unit
    m = _MULTI.search(name or "")
    if m:
        unit, factor = _PACK_UNITS[m.group(3).lower()]
        return round(int(m.group(1)) * _num(m.group(2)) * factor, 3), unit
    m = _SINGLE.search(name or "")
    if m:
        unit, factor = _PACK_UNITS[m.group(2).lower()]
        return round(_num(m.group(1)) * factor, 3), unit
    return None, None


def to_base(amount: float, unit: str, base_unit: str, grams_per_piece: float | None = None) -> float | None:
    """Regn en oppskriftsmengde om til ingrediensens basisenhet. None hvis det ikke går."""
    unit = unit.lower()
    if unit not in RECIPE_UNITS:
        return None
    u, factor = RECIPE_UNITS[unit]
    value = amount * factor
    if u == base_unit:
        return value
    if u == "stk" and base_unit == "g" and grams_per_piece:
        return value * grams_per_piece
    if u == "g" and base_unit == "stk" and grams_per_piece:
        return value / grams_per_piece
    if {u, base_unit} == {"g", "ml"}:
        return value  # tilnærming: tetthet 1 (melk, fløte, tomatpuré)
    return None
