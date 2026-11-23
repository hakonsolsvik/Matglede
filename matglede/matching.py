"""Gir hvert produkt en poengsum for hvor godt det passer en generisk ingrediens."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

MIN_SCORE = 2.0
# Bøyningsendelser vi godtar etter et søkeord ("tomat" -> "tomater", "tortilla" -> "tortillas").
_SUFFIX = r"(?:e|r|s|er|en|et|ene|ne)?"


def normalize(text: str) -> str:
    text = (text or "").lower().replace("&", " og ")
    return re.sub(r"[^0-9a-zæøåéü%]+", " ", text).strip()


def split_terms(value: str) -> list[str]:
    return [normalize(t) for t in (value or "").split("|") if t.strip()]


@dataclass
class IngredientRule:
    search_terms: list[str]
    must_include: list[str]
    exclude_terms: list[str]
    category_hints: list[str]

    @classmethod
    def from_row(cls, row) -> "IngredientRule":
        return cls(
            search_terms=split_terms(row["search_terms"]),
            must_include=split_terms(row["must_include"]),
            exclude_terms=split_terms(row["exclude_terms"]),
            category_hints=split_terms(row["category_hints"]),
        )


def _contains_word(haystack: str, needle: str) -> bool:
    # Helt ord med vanlige bøyningsendelser: "tomat" treffer "tomater",
    # men "løk" treffer ikke "hvitløk" og "egg" treffer ikke "eggdeler".
    return re.search(rf"(^|\s){re.escape(needle)}{_SUFFIX}(\s|$)", haystack) is not None


def _contains_anywhere(haystack: str, needle: str) -> bool:
    return needle in haystack


def _excluded(haystack: str, needle: str) -> bool:
    # Lange ord treffer hvor som helst ("pulver" i "hvitløkspulver"),
    # korte ord bare på ordstart, så "is" ikke treffer "pris".
    if len(needle) >= 4:
        return needle in haystack
    return re.search(rf"(^|\s){re.escape(needle)}", haystack) is not None


def excluded_name(rule: IngredientRule, name: str) -> bool:
    """Sant hvis navnet kjeden bruker inneholder et utelukkende ord.

    Samme EAN kan hete "Plantego' Avokado" hos Coop og "Grønnsakspålegg Avokado" hos Meny,
    så hvert tilbud sjekkes mot sitt eget navn, ikke bare navnet som ga treffet.
    """
    n = normalize(name)
    return any(_excluded(n, ex) for ex in rule.exclude_terms)


def score_product(rule: IngredientRule, name: str, categories: list[str], price_date: str | None,
                  has_package: bool, now: datetime | None = None) -> float | None:
    """Returner poengsum, eller None hvis produktet er diskvalifisert."""
    n = normalize(name)
    if any(_excluded(n, ex) for ex in rule.exclude_terms):
        return None
    cats = [normalize(c) for c in categories if c]
    # "fros/fryst" betyr at ett av alternativene må finnes, i navnet eller i en kategori
    # (frossen "Kyllingfilet 1,4kg First Price" sier ikke fryst i navnet).
    where = " ".join([n, *cats])
    if any(not any(_contains_anywhere(where, a) for a in m.split("/")) for m in rule.must_include):
        return None

    score = 0.0
    best_term_tokens = 0
    for term in rule.search_terms:
        tokens = term.split()
        if _contains_word(n, term):
            score = max(score, 3.0)
            best_term_tokens = max(best_term_tokens, len(tokens))
        elif all(_contains_word(n, t) for t in tokens):
            score = max(score, 2.0)
            best_term_tokens = max(best_term_tokens, len(tokens))
    if score == 0:
        return None

    # Ingrediensen som hovedord ("Hvitløk 100g") er bedre enn som smak ("Poteter med hvitløk").
    words = n.split()
    head = " ".join(words[:2])
    if any(_contains_word(head, t) for t in rule.search_terms):
        score += 1.5
    if any(re.search(rf"(^|\s)(med|m|i)\s+(\S+\s+)?{re.escape(t)}", n) for t in rule.search_terms):
        score -= 3.0

    if rule.category_hints and cats:
        if any(h in c for h in rule.category_hints for c in cats):
            score += 2.0
        else:
            score -= 1.5

    # Kortere navn = mer generisk vare ("Kjøttdeig 400g" foran "Kjøttdeig taco krydret ...")
    extra = max(0, len([t for t in n.split() if not t[0].isdigit()]) - best_term_tokens - 2)
    score -= 0.15 * extra

    if has_package:
        score += 0.5

    if price_date:
        try:
            dt = datetime.fromisoformat(price_date.replace("Z", "+00:00"))
            age = ((now or datetime.now(timezone.utc)) - dt).days
            if age <= 60:
                score += 1.0
            elif age > 365:
                score -= 1.0
        except ValueError:
            pass
    return round(score, 3)
