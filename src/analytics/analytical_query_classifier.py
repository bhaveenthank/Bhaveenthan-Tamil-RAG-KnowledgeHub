from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

from retrieval.query_expander import REGISTRY_ORDER, QueryExpander, normalize_text, ordered_unique

DEFAULT_KNOWLEDGE_DIR = Path("data/knowledge")
INTENT_GROUPS = {
    "group_by_author": "author",
    "group_by_work": "work",
    "group_by_category": "category",
    "group_by_record_type": "record_type",
    "compare_sources": "source",
    "term_occurrence": None,
    "unsupported": None,
}
INTENT_KEYWORDS = (
    ("group_by_author", ("ஆசிரியர்", "ஆசிரியர்கள்", "நாயன்மார்", "author", "authors", "poet", "poets")),
    ("group_by_work", ("work", "works", "நூல்", "நூல்கள்", "இலக்கியங்களில்", "பாடல்களில்")),
    ("group_by_category", ("corpus", "category", "collection", "இலக்கியத்தில்", "இலக்கியம்", "தொகுப்பு")),
    ("group_by_record_type", ("record type", "record types", "record_type", "வகை", "பகுதி")),
    ("compare_sources", ("source", "sources", "மூலம்", "ஆதாரம்")),
)
ANALYTICAL_HINTS = ("அதிக", "அதிகம்", "எங்கு", "எந்த", "வருகிறது", "வருகின்றன", "mentions", "most", "count")


def nfc(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value or "").split())


def registry_terms(knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR) -> list[str]:
    expander = QueryExpander(knowledge_dir=knowledge_dir)
    terms: list[str] = []
    for registry_name in REGISTRY_ORDER:
        for record in expander.registries.get(registry_name, []):
            for value in record.values():
                if isinstance(value, str) and any("\u0b80" <= char <= "\u0bff" for char in value):
                    terms.append(normalize_text(value))
                elif isinstance(value, list):
                    terms.extend(
                        normalize_text(str(item))
                        for item in value
                        if isinstance(item, str) and any("\u0b80" <= char <= "\u0bff" for char in item)
                    )
    return sorted(ordered_unique(terms), key=lambda term: (-len(term), term))


def extract_target_term(query: str, terms: list[str] | None = None) -> str:
    normalized = nfc(query)
    for term in terms or registry_terms():
        if term and term in normalized:
            return term
    quoted_start = normalized.find('"')
    quoted_end = normalized.find('"', quoted_start + 1)
    if quoted_start != -1 and quoted_end != -1:
        return normalized[quoted_start + 1 : quoted_end].strip()
    tokens = [
        token.strip(" ?.,:;\"'")
        for token in normalized.split()
        if any("\u0b80" <= char <= "\u0bff" for char in token)
    ]
    stopwords = {"எந்த", "எங்கு", "அதிகம்", "அதிக", "வருகிறது", "வருகின்றன", "இல்", "உள்ள"}
    candidates = [token for token in tokens if token not in stopwords and len(token) > 1]
    return candidates[0] if candidates else ""


def should_expand(query: str, term: str) -> bool:
    normalized = nfc(query)
    if any(keyword in normalized for keyword in ("தொடர்பான", "சார்ந்த", "ஒத்த", "variant", "synonym")):
        return True
    if not term:
        return False
    expansion = QueryExpander().expand(term)
    return bool(expansion["expansion_applied"])


def classify_query(query: str) -> dict[str, Any]:
    normalized = nfc(query)
    lowered = normalized.lower()
    intent = "unsupported"
    for candidate_intent, keywords in INTENT_KEYWORDS:
        if any(keyword.lower() in lowered for keyword in keywords):
            intent = candidate_intent
            break
    if intent == "unsupported" and any(keyword.lower() in lowered for keyword in ANALYTICAL_HINTS):
        intent = "term_occurrence"
    term = extract_target_term(normalized)
    if not term:
        intent = "unsupported"
    return {
        "query": normalized,
        "intent": intent,
        "term": term,
        "expanded": should_expand(normalized, term) if intent != "unsupported" else False,
        "group_by": INTENT_GROUPS[intent],
        "classification_rules": {
            "rule_based": True,
            "llm_calls": 0,
            "matched_group_keywords": [
                keyword
                for candidate_intent, keywords in INTENT_KEYWORDS
                if candidate_intent == intent
                for keyword in keywords
                if keyword.lower() in lowered
            ],
        },
    }
