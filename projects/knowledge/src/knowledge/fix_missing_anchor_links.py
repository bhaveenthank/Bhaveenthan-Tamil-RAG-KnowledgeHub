from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from knowledge.build_pozhippurai_links_v4 import validate_clean_links, validate_v4_links, write_iob_v4
from knowledge.learn_pozhippurai_high_confidence_patterns import load_jsonl
from knowledge.link_thevaram_pozhippurai import DEFAULT_TABLE_ROOT, compact_text, read_jsonl, stable_hash, tokens
from knowledge.link_thevaram_pozhippurai_v3 import build_manual_review_pack, write_csv_file, write_jsonl, write_tsv

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v4-missing-anchor-fixed"
DEFAULT_BASE_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_hardened_learned")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_missing_anchor_fixed")
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v4_missing_anchor_fixed_report.md"
DEFAULT_ONTOLOGY = Path("data/knowledge/ontology/thevaram_ontology_v1.json")
DEFAULT_RELATIONS = Path("data/knowledge/ontology/thevaram_relations_v1.json")
DEFAULT_ENTITY_EXPANSION = Path("data/knowledge/paadal_pozhippurai_hardening/v4/03_entity_annotation_hierarchy_expansion.csv")

BLOCKING_HIGH_WARNINGS = {
    "order_only_penalty",
    "ambiguous_margin_penalty",
    "target_too_broad_penalty",
    "polysemy_without_context_penalty",
    "order_only_support",
    "best_second_margin_below_review_threshold",
}
TAMIL_WORD = r"[\u0B80-\u0BFF]+"
MORPH_SUFFIXES = ("உடைய", "னுடைய", "ினுடைய", "ை", "னை", "ரை", "னது", "தாகிய", "ஆகிய", "ரும்", "யாய்", "இல்", "த்தில்")


@dataclass(frozen=True)
class AnchorRule:
    canonical: str
    anchor_type: str
    aliases: tuple[str, ...]
    relation: str
    relationship_bias: str
    context_any: tuple[str, ...] = ()
    anti_context_any: tuple[str, ...] = ()
    token_boundary: bool = False


@dataclass(frozen=True)
class AnchorHit:
    canonical: str
    anchor_type: str
    surface: str
    relation: str
    relationship_bias: str
    context_score: float
    polysemy_safe: bool


@dataclass(frozen=True)
class AnchorResolution:
    source_hits: tuple[AnchorHit, ...]
    target_hits: tuple[AnchorHit, ...]
    matched_anchors: tuple[str, ...]
    ontology_relations: tuple[str, ...]
    anchor_resolver_score: float
    anchor_alias_score: float
    anchor_morphology_score: float
    anchor_context_disambiguation_score: float
    ontology_relation_score: float
    polysemy_safety_score: float
    anchor_family_match_score: float
    missing_anchor_resolved: bool
    review_reason: str


def split_aliases(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in (value or "").split("|") if part.strip())


def read_csv(path: Path) -> list[dict[str, str]]:
    import csv

    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_existing_ontology(ontology_path: Path = DEFAULT_ONTOLOGY, relations_path: Path = DEFAULT_RELATIONS) -> dict[str, Any]:
    ontology = json.loads(ontology_path.read_text(encoding="utf-8"))
    relations = json.loads(relations_path.read_text(encoding="utf-8"))
    return {
        "ontology_schema_version": ontology.get("schema_version"),
        "relation_schema_version": relations.get("schema_version"),
        "entity_types": [item.get("code") for item in ontology.get("entity_types", [])],
        "relations": [item.get("name") for item in relations.get("relations", [])],
        "mythological_event_canon": ontology.get("mythological_event_canon", []),
    }


def base_anchor_rules() -> list[AnchorRule]:
    return [
        AnchorRule("SIVA", "DEITY", ("சிவன்", "சிவபிரான்", "சிவபெருமான்", "இறைவன்", "இறைவர்", "பெருமான்", "பெம்மான்", "அண்ணல்", "ஐயன்", "அத்தன்", "எந்தை", "நம்பன்", "ஒருவன்", "பித்தர்", "பித்தன்", "அடிகள்", "நாதன்", "ஈசன்", "சோமசுந்தரன்"), "refers_to(SIVA)", "describes_entity"),
        AnchorRule("AALAVAI_THALAM", "SACRED_PLACE", ("ஆலவாய்", "ஆலவாயில்", "ஆலவாயிலான்", "ஆலவாயிலார்", "கூடல்", "நான்மாடக்கூடல்", "திரு ஆலவாய்", "திரு ஆலவாயில்"), "enshrined_at(SIVA,AALAVAI)", "describes_entity"),
        AnchorRule("MUTHUKUNRAM_THALAM", "SACRED_PLACE", ("முதுகுன்றம்", "திருமுதுகுன்றம்", "முதுகுன்றை", "முதுகுன்றத்து"), "enshrined_at(SIVA,MUTHUKUNRAM)", "describes_entity"),
        AnchorRule("TIRUVIZHIMIZHALAI_THALAM", "SACRED_PLACE", ("திருவீழிமிழலை", "வீழிமிழலை", "மிழலை", "மிழலையீர்"), "enshrined_at(SIVA,TIRUVIZHIMIZHALAI)", "describes_entity"),
        AnchorRule("ANNAMALAI_THALAM", "SACRED_PLACE", ("அண்ணாமலை", "திருவண்ணாமலை", "அண்ணாமலை அண்ணல்"), "enshrined_at(SIVA,ANNAMALAI)", "describes_entity"),
        AnchorRule("SIRKAZHI_THALAM", "SACRED_PLACE", ("காழி", "சீகாழி", "காழி மா நகர்"), "sung_at(PATIKAM,SIRKAZHI)", "describes_entity"),
        AnchorRule("CRESCENT_MOON", "CELESTIAL", ("பிறை", "திங்கள்", "மதி", "வெண்திங்கள்", "வெண்மதி", "இளவெண் பிறை", "தண்மதி", "வெண்பிறை", "பிறைமதி", "சந்திரன்", "பிறைச் சந்திரன்"), "wears(SIVA,CRESCENT_MOON)", "interprets_image", ("சடை", "முடி", "சென்னி", "திருமுடி", "சூடி", "அணிந்து", "கண்ணி")),
        AnchorRule("GANGA", "RIVER", ("கங்கை", "கங்கையை", "புனல்", "சலம்", "நீர்", "அலை"), "wears(SIVA,GANGA)", "interprets_image", ("சடை", "முடி", "சென்னி", "சூடி", "தரித்த", "அடக்கி")),
        AnchorRule("SIVA_HAIR", "BODY_PART", ("சடை", "சடைமுடி", "முடி", "சென்னி", "திருமுடி"), "wears_on(SIVA,SIVA_HAIR)", "interprets_image"),
        AnchorRule("BULL", "FAUNA", ("விடை", "எருது", "ஏறு", "ஆனேறு", "ஆடல் ஏறு"), "rides(SIVA,BULL)", "interprets_image", ("ஏற", "ஏறி", "ஏற்ற", "வாகனம்", "மீது")),
        AnchorRule("SACRED_ASH", "SACRED_OBJECT", ("பொடி", "சுடலைப் பொடி", "திருநீறு", "திருவெண்ணீறு", "சுண்ணம்", "சாம்பல்", "சாம்பற் பொடி"), "smeared_with(SIVA,SACRED_ASH)", "interprets_image", ("பூசி", "உடல்", "சுடலை", "அணிந்து")),
        AnchorRule("SERPENT", "FAUNA", ("அரவு", "நாகம்", "பாம்பு", "ஐந்தலை நாகம்", "ஐந்தலை"), "wears_on_body(SIVA,SERPENT)", "interprets_image", ("பாம்பு", "நாகம்", "அணிந்து", "சடை", "அரை", "இடை", "கட்டி", "சாத்தி"), ("ஆரவாரம்", "பறை", "ஒலி")),
        AnchorRule("SOUND", "ABSTRACTION", ("அரவம்", "ஆரவாரம்", "ஒலி"), "refers_to(SOUND)", "glosses_word", ("பறை", "ஆரவாரம்", "ஒலி")),
        AnchorRule("BRAHMA_SKULL", "SACRED_OBJECT", ("வெண்தலை", "தலை", "கலன்", "கபாலம்", "தலையோட்டை", "உண்கலம்", "பலி"), "holds(SIVA,BRAHMA_SKULL)", "interprets_image", ("பிரமன்", "பலி", "உணவு", "கலன்", "தலையோடு")),
        AnchorRule("WEAPON_AXE", "SACRED_OBJECT", ("மழு", "வெண்மழு", "மழுப்படை", "படை", "அம்பு"), "holds(SIVA,WEAPON)", "interprets_image", ("ஏந்தி", "கையில்", "படை", "அம்பு")),
        AnchorRule("DIVINE_FEET", "BODY_PART", ("அடி", "திருவடி", "கழல்", "பாதம்"), "worshipped_by(SIVA,DEVOTEE)", "theological_explanation", ("தொழ", "பணி", "கழல்", "திருவடி", "சிந்தை", "வணங்கு", "சேர", "கைதொழ")),
        AnchorRule("HAND", "BODY_PART", ("கை", "கரம்"), "body_locus(SIVA,HAND)", "describes_entity", token_boundary=True),
        AnchorRule("BLUE_THROAT", "BODY_PART", ("நீலமாமிடற்று", "நீலநிற கண்டம்", "கண்டம்", "மிடறு", "கண்டம் கறுத்த"), "patient_of(BLUE_THROAT,POISON_EVENT)", "describes_entity", ("நஞ்சு", "நீல", "கண்டம்", "மிடறு")),
        AnchorRule("POISON_EVENT", "MYTH_EVENT", ("நஞ்சு", "ஆலம்", "ஆலகால", "காலகூடம்", "நஞ்சினை உண்டு"), "agent_of(SIVA,POISON_EVENT)", "interprets_image"),
        AnchorRule("RAVANA_SUBDUING_EVENT", "MYTH_EVENT", ("பத்துத்தலையோன்", "அரக்கன்", "இராவணன்", "விரல் ஊன்ற", "கத்த", "செருக்கு", "கால் விரலால்", "நெரித்த"), "agent_of(SIVA,RAVANA_SUBDUING_EVENT)", "interprets_image"),
        AnchorRule("ELEPHANT_HIDE_EVENT", "MYTH_EVENT", ("மத்தயானை", "மதயானை", "யானை", "உரி போர்த்த", "தோலை உரித்துப் போர்த்த"), "agent_of(SIVA,ELEPHANT_HIDE_EVENT)", "interprets_image"),
        AnchorRule("TRIPURA_EVENT", "MYTH_EVENT", ("முப்புரம்", "திரிபுரம்", "மூன்று புரம்", "எரித்த", "செற்ற", "அம்பு எய்தி"), "agent_of(SIVA,TRIPURA_EVENT)", "interprets_image"),
        AnchorRule("ADI_MUDI_EVENT", "MYTH_EVENT", ("இருவர் அறியாத", "அயனும் மாலும்", "மாலும் அயனும்", "அடிமுடி", "அறியவொண்ணாத", "காண்டற்கரிய"), "event_mentioned_in(ADI_MUDI_EVENT,VERSE)", "theological_explanation"),
        AnchorRule("SAMBANDAR", "SAINT", ("ஞானசம்பந்தன்", "சம்பந்தன்", "காழி மா நகர் வாழி சம்பந்தன்"), "composed_by(PATIKAM,SAMBANDAR)", "describes_entity"),
        AnchorRule("BRAHMA", "DEITY", ("நான்முகன்", "அயன்", "பிரமன்", "மலரான்"), "mentions(BRAHMA)", "describes_entity"),
        AnchorRule("VISHNU", "DEITY", ("திருமால்", "மால்", "அரி", "மாயோன்"), "mentions(VISHNU)", "describes_entity"),
        AnchorRule("WORSHIP", "DEVOTIONAL_ACT", ("தொழ", "தொழுது", "கைதொழ", "பணி", "பணிந்து", "ஏத்தி", "போற்றி", "வழிபட்டு", "அருச்சித்து"), "worshipped_by(SIVA,DEVOTEE)", "theological_explanation"),
        AnchorRule("KARMA_REMOVAL", "THEO_CONCEPT", ("வினை", "பாசம்", "பிணி", "துன்பம்", "நீங்கும்", "கெடும்", "முத்தி", "வீடு"), "grants(SIVA,KARMA_REMOVAL)", "theological_explanation"),
    ]


def load_entity_expansion_rules(path: Path = DEFAULT_ENTITY_EXPANSION) -> list[AnchorRule]:
    rules = []
    for row in read_csv(path):
        entity_type = row.get("entity_type", "")
        canonical = row.get("canonical", "")
        aliases = split_aliases(row.get("aliases", ""))
        if not canonical or not aliases:
            continue
        linker_use = row.get("linker_use", "")
        relationship = "interprets_image" if "image" in linker_use else "describes_entity"
        relation = {
            "DEITY": f"refers_to({canonical})",
            "THALAM": f"enshrined_at(SIVA,{canonical})",
            "SACRED_OBJECT": f"wears(SIVA,{canonical})",
            "BODY_PART": f"wears_on(SIVA,{canonical})",
            "FAUNA": f"wears(SIVA,{canonical})",
            "CELESTIAL": f"wears(SIVA,{canonical})",
            "SAINT": f"composed_by(PATIKAM,{canonical})",
            "MYTH_EVENT": f"event_mentioned_in({canonical},VERSE)",
        }.get(entity_type, f"refers_to({canonical})")
        rules.append(
            AnchorRule(
                canonical=canonical,
                anchor_type=entity_type if entity_type != "THALAM" else "SACRED_PLACE",
                aliases=aliases + (canonical,),
                relation=relation,
                relationship_bias=relationship,
            )
        )
    return rules


def load_anchor_rules() -> tuple[list[AnchorRule], dict[str, Any]]:
    ontology = load_existing_ontology()
    rules = base_anchor_rules() + load_entity_expansion_rules()
    return rules, ontology


@lru_cache(maxsize=250_000)
def compact_cached(value: str) -> str:
    return compact_text(value)


@lru_cache(maxsize=250_000)
def normalize_variant(value: str) -> str:
    compact = compact_text(value)
    for suffix in MORPH_SUFFIXES:
        suffix_compact = compact_cached(suffix)
        if compact.endswith(suffix_compact) and len(compact) > len(suffix_compact) + 2:
            return compact[: -len(suffix_compact)]
    return compact


def token_boundary_contains(text: str, alias: str) -> bool:
    return any(token == alias for token in re.findall(TAMIL_WORD, text))


def alias_match(text: str, alias: str, *, token_boundary: bool = False) -> bool:
    if token_boundary:
        return token_boundary_contains(text, alias)
    text_compact = compact_cached(text)
    alias_compact = compact_cached(alias)
    return alias_compact in text_compact or normalize_variant(alias) in text_compact or alias_compact in normalize_variant(text)


def anti_context_present(text: str, rule: AnchorRule) -> bool:
    return any(alias_match(text, cue) for cue in rule.anti_context_any)


def context_score(text: str, rule: AnchorRule) -> float:
    if not rule.context_any:
        return 1.0
    matches = sum(1 for cue in rule.context_any if alias_match(text, cue))
    return min(1.0, matches / max(1, min(2, len(rule.context_any))))


def detect_anchor_hits(text: str, rules: list[AnchorRule]) -> tuple[AnchorHit, ...]:
    hits: list[AnchorHit] = []
    for rule in rules:
        if anti_context_present(text, rule):
            continue
        for alias in rule.aliases:
            if alias_match(text, alias, token_boundary=rule.token_boundary):
                cscore = context_score(text, rule)
                if rule.context_any and cscore <= 0:
                    continue
                hits.append(
                    AnchorHit(
                        canonical=rule.canonical,
                        anchor_type=rule.anchor_type,
                        surface=alias,
                        relation=rule.relation,
                        relationship_bias=rule.relationship_bias,
                        context_score=cscore,
                        polysemy_safe=cscore >= 0.5,
                    )
                )
                break
    dedup: dict[tuple[str, str], AnchorHit] = {}
    for hit in hits:
        key = (hit.anchor_type, hit.canonical)
        if key not in dedup or hit.context_score > dedup[key].context_score:
            dedup[key] = hit
    return tuple(dedup.values())


def relation_compatible(source: AnchorHit, target: AnchorHit, relationship: str) -> str:
    if source.canonical == target.canonical:
        return source.relation if source.relation == target.relation else f"shared_anchor({source.canonical})"
    pair = {source.canonical, target.canonical}
    if {"CRESCENT_MOON", "SIVA_HAIR"} <= pair:
        return "wears(SIVA,CRESCENT_MOON)"
    if {"GANGA", "SIVA_HAIR"} <= pair:
        return "wears(SIVA,GANGA)"
    if {"SIVA", "AALAVAI_THALAM"} <= pair:
        return "enshrined_at(SIVA,AALAVAI)"
    if {"SAMBANDAR", "SIRKAZHI_THALAM"} <= pair:
        return "sung_at(PATIKAM,SIRKAZHI)"
    if {"DIVINE_FEET", "WORSHIP"} <= pair:
        return "worshipped_by(SIVA,DEVOTEE)"
    if relationship == source.relationship_bias or relationship == target.relationship_bias:
        if source.anchor_type == target.anchor_type:
            return f"refers_to({source.anchor_type})"
    return ""


def resolve_anchors(source_text: str, target_text: str, relationship: str, rules: list[AnchorRule]) -> AnchorResolution:
    source_hits = detect_anchor_hits(source_text, rules)
    target_hits = detect_anchor_hits(target_text, rules)
    matched: set[str] = set()
    relations: set[str] = set()
    for source in source_hits:
        for target in target_hits:
            relation = relation_compatible(source, target, relationship)
            if relation:
                relations.add(relation)
                matched.add(source.canonical)
                matched.add(target.canonical)
    alias_score = min(1.0, (len(source_hits) + len(target_hits)) / 6)
    morphology_score = 1.0 if any(normalize_variant(hit.surface) != compact_text(hit.surface) for hit in source_hits + target_hits) else 0.6 if source_hits and target_hits else 0.0
    context_score_value = min(1.0, sum(hit.context_score for hit in source_hits + target_hits) / max(1, len(source_hits) + len(target_hits)))
    ontology_score = min(1.0, 0.35 * len(relations))
    family_score = min(1.0, len({hit.anchor_type for hit in source_hits} & {hit.anchor_type for hit in target_hits}) / 2 + (0.4 if matched else 0.0))
    poly_score = 1.0 if all(hit.polysemy_safe for hit in source_hits + target_hits) else 0.4
    resolver_score = (
        0.25 * alias_score
        + 0.15 * morphology_score
        + 0.20 * context_score_value
        + 0.25 * ontology_score
        + 0.15 * family_score
    )
    missing_resolved = resolver_score >= 0.55 and ontology_score >= 0.30 and poly_score >= 0.70 and bool(matched)
    review_reason = ""
    if not missing_resolved:
        if resolver_score >= 0.45:
            review_reason = "near_threshold_or_context_weak"
        elif source_hits and not target_hits:
            review_reason = "anchor_found_only_on_source"
        elif target_hits and not source_hits:
            review_reason = "anchor_found_only_on_target"
        elif poly_score < 0.70:
            review_reason = "polysemy_context_unsafe"
        else:
            review_reason = "no_shared_ontology_anchor"
    return AnchorResolution(
        source_hits=source_hits,
        target_hits=target_hits,
        matched_anchors=tuple(sorted(matched)),
        ontology_relations=tuple(sorted(relations)),
        anchor_resolver_score=round(resolver_score, 4),
        anchor_alias_score=round(alias_score, 4),
        anchor_morphology_score=round(morphology_score, 4),
        anchor_context_disambiguation_score=round(context_score_value, 4),
        ontology_relation_score=round(ontology_score, 4),
        polysemy_safety_score=round(poly_score, 4),
        anchor_family_match_score=round(family_score, 4),
        missing_anchor_resolved=missing_resolved,
        review_reason=review_reason,
    )


def anchor_to_string(hit: AnchorHit) -> str:
    return f"{hit.anchor_type}:{hit.canonical}:{hit.surface}"


def blocking_for_high(row: dict[str, Any]) -> bool:
    flags = set(map(str, row.get("penalties_applied") or [])) | set(map(str, row.get("critical_warnings") or []))
    return bool(flags & BLOCKING_HIGH_WARNINGS)


def update_row(row: dict[str, Any], resolution: AnchorResolution) -> tuple[dict[str, Any], dict[str, Any] | None]:
    item = dict(row)
    penalties = [penalty for penalty in row.get("penalties_applied") or []]
    missing_before = "missing_entity_anchor_penalty" in set(map(str, penalties))
    anchors_before = list(map(str, row.get("expanded_entity_anchors") or []))
    anchors_after = sorted(set(anchors_before) | set(resolution.matched_anchors))
    confidence_before = str(row.get("confidence", ""))
    confidence_after = confidence_before
    score_after = float(row.get("score") or 0.0)
    manual_review = bool(row.get("manual_review_required"))
    decision = "KEEP_REVIEW" if missing_before else ""
    reason = resolution.review_reason

    if missing_before and resolution.missing_anchor_resolved:
        penalties = [penalty for penalty in penalties if penalty != "missing_entity_anchor_penalty"]
        if confidence_before == "medium" and not blocking_for_high(row) and resolution.anchor_resolver_score >= 0.75 and str(row.get("relationship_type", "")) in {hit.relationship_bias for hit in resolution.source_hits + resolution.target_hits}:
            confidence_after = "high"
            score_after = max(score_after, 0.83)
            manual_review = False
            decision = "PROMOTE_TO_HIGH"
            reason = "missing_anchor_resolved_with_ontology_valid_relation"
        elif confidence_before == "low":
            confidence_after = "medium"
            score_after = max(score_after, 0.58)
            manual_review = True
            decision = "PROMOTE_TO_MEDIUM"
            reason = "missing_anchor_resolved_but_kept_for_review"
        else:
            decision = "KEEP_REVIEW" if manual_review else "KEEP_LOW"
            reason = "missing_anchor_resolved_without_confidence_promotion"

    item.update(
        {
            "schema_version": SCHEMA_VERSION,
            "base_schema_version": row.get("schema_version", ""),
            "anchors_before": anchors_before,
            "anchors_after": anchors_after,
            "missing_anchor_before": missing_before,
            "missing_anchor_resolved": resolution.missing_anchor_resolved,
            "anchor_resolver_score": resolution.anchor_resolver_score,
            "anchor_alias_score": resolution.anchor_alias_score,
            "anchor_morphology_score": resolution.anchor_morphology_score,
            "anchor_context_disambiguation_score": resolution.anchor_context_disambiguation_score,
            "ontology_relation_score": max(float((row.get("feature_scores") or {}).get("ontology_relation_score", 0.0)) if isinstance(row.get("feature_scores"), dict) else 0.0, resolution.ontology_relation_score),
            "polysemy_safety_score": resolution.polysemy_safety_score,
            "anchor_family_match_score": resolution.anchor_family_match_score,
            "possible_source_anchors": [anchor_to_string(hit) for hit in resolution.source_hits],
            "possible_target_anchors": [anchor_to_string(hit) for hit in resolution.target_hits],
            "expanded_entity_anchors": anchors_after,
            "ontology_relations_matched": list(resolution.ontology_relations),
            "penalties_applied": penalties,
            "confidence": confidence_after,
            "score": round(score_after, 4),
            "manual_review_required": manual_review,
            "rule_ids_applied": list(row.get("rule_ids_applied") or []) + (["missing_anchor_resolver"] if resolution.missing_anchor_resolved else []),
            "diagnostic_note": f"{row.get('diagnostic_note', '')} Missing-anchor resolver: {reason}.",
        }
    )
    change = None
    if missing_before:
        first_hit = (resolution.source_hits + resolution.target_hits)[0] if (resolution.source_hits + resolution.target_hits) else None
        change = {
            "link_id": item.get("link_id", ""),
            "issue_before": "missing_anchor",
            "source_text": item.get("source_text", ""),
            "target_text": item.get("target_text", ""),
            "anchors_before": "|".join(anchors_before),
            "anchors_after": "|".join(anchors_after),
            "new_anchor_type": first_hit.anchor_type if first_hit else "",
            "new_anchor_canonical": first_hit.canonical if first_hit else "",
            "source_anchor_surface": "|".join(hit.surface for hit in resolution.source_hits),
            "target_anchor_surface": "|".join(hit.surface for hit in resolution.target_hits),
            "ontology_relation": "|".join(resolution.ontology_relations),
            "relationship_type": item.get("relationship_type", ""),
            "confidence_before": confidence_before,
            "confidence_after": confidence_after,
            "anchor_resolver_score": resolution.anchor_resolver_score,
            "promotion_decision": decision,
            "reason": reason,
        }
    return item, change


def apply_missing_anchor_fix(rows: list[dict[str, Any]], rules: list[AnchorRule]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fixed = []
    changes = []
    for row in rows:
        if row.get("relationship_type") == "unlinked" or row.get("confidence") == "no_link":
            item = dict(row)
            item.update(
                {
                    "schema_version": SCHEMA_VERSION,
                    "anchors_before": row.get("expanded_entity_anchors") or [],
                    "anchors_after": row.get("expanded_entity_anchors") or [],
                    "missing_anchor_before": False,
                    "missing_anchor_resolved": False,
                    "anchor_resolver_score": 0.0,
                    "anchor_alias_score": 0.0,
                    "anchor_morphology_score": 0.0,
                    "anchor_context_disambiguation_score": 0.0,
                    "ontology_relation_score": 0.0,
                    "polysemy_safety_score": 1.0,
                    "anchor_family_match_score": 0.0,
                    "ontology_relations_matched": [],
                }
            )
            fixed.append(item)
            continue
        resolution = resolve_anchors(str(row.get("source_text", "")), str(row.get("target_text", "")), str(row.get("relationship_type", "")), rules)
        item, change = update_row(row, resolution)
        fixed.append(item)
        if change is not None:
            changes.append(change)
    return fixed, changes


def missing_anchor_count(rows: list[dict[str, Any]]) -> int:
    return sum("missing_entity_anchor_penalty" in set(map(str, row.get("penalties_applied") or [])) for row in rows)


def baseline_counts(base_root: Path) -> dict[str, Any]:
    full = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl")
    primary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl")
    return {
        "total_links": len(full),
        "primary_links": len(primary),
        "full_confidence": dict(sorted(Counter(row.get("confidence", "") for row in full).items())),
        "primary_confidence": dict(sorted(Counter(row.get("confidence", "") for row in primary).items())),
        "full_missing_anchor_count": missing_anchor_count(full),
        "primary_missing_anchor_count": missing_anchor_count(primary),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in full),
        "relationship_type_counts": dict(sorted(Counter(row.get("relationship_type", "") for row in full).items())),
    }


def manual_review_rows(rows: list[dict[str, Any]], table_root: Path) -> list[dict[str, Any]]:
    paadal_by_id = {str(row.get("paadal_id", "")): str(row.get("paadal_text", "")) for row in read_jsonl(table_root / "paadalgal.jsonl")}
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in read_jsonl(table_root / "commentaries.jsonl")}
    review = []
    for row in rows:
        score = float(row.get("anchor_resolver_score") or 0.0)
        poly = float(row.get("polysemy_safety_score") or 1.0)
        if not row.get("missing_anchor_before"):
            continue
        if not (0.45 <= score < 0.60 or poly < 0.70 or (row.get("ontology_relations_matched") and not row.get("missing_anchor_resolved")) or not row.get("ontology_relations_matched")):
            continue
        commentary = commentary_by_id.get(str(row.get("commentary_id", "")), {})
        review.append(
            {
                "link_id": row.get("link_id", ""),
                "source_text": row.get("source_text", ""),
                "target_text": row.get("target_text", ""),
                "possible_source_anchors": "|".join(row.get("possible_source_anchors") or []),
                "possible_target_anchors": "|".join(row.get("possible_target_anchors") or []),
                "suggested_anchor": "|".join(row.get("anchors_after") or []),
                "suggested_ontology_relation": "|".join(row.get("ontology_relations_matched") or []),
                "relationship_type": row.get("relationship_type", ""),
                "confidence": row.get("confidence", ""),
                "reason_for_review": "weak_context_or_one_sided_anchor",
                "full_paadal_if_available": paadal_by_id.get(str(row.get("paadal_id", "")), ""),
                "full_pozhippurai_if_available": commentary.get("pozhppurai", ""),
                "kurippurai_if_available": commentary.get("kurippurai", ""),
            }
        )
    return review[:5000]


def summarize(
    full: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    changes: list[dict[str, Any]],
    baseline: dict[str, Any],
    validation: dict[str, Any],
    primary_validation: dict[str, Any],
    ontology_info: dict[str, Any],
    prior_high_link_ids: set[str],
) -> dict[str, Any]:
    high_before = int(baseline.get("primary_confidence", {}).get("high", 0))
    high_after = Counter(row.get("confidence", "") for row in primary).get("high", 0)
    current_high_link_ids = {str(row.get("link_id", "")) for row in primary if row.get("confidence") == "high"}
    missing_prior_high_link_ids = sorted(prior_high_link_ids - current_high_link_ids)
    missing_before = int(baseline.get("primary_missing_anchor_count", 0))
    missing_after = missing_anchor_count(primary)
    accepted = (
        high_after >= high_before
        and not missing_prior_high_link_ids
        and missing_after < missing_before
        and validation.get("status") == "VALID"
        and primary_validation.get("status") == "VALID"
    )
    change_counter = Counter(row.get("promotion_decision", "") for row in changes)
    anchor_type_counter = Counter(row.get("new_anchor_type", "") for row in changes if row.get("new_anchor_type"))
    relation_counter = Counter()
    for row in changes:
        for relation in str(row.get("ontology_relation", "")).split("|"):
            if relation:
                relation_counter[relation] += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "run_status": "accepted" if accepted else "rejected_acceptance_rule_failed",
        "accepted": accepted,
        "ontology": ontology_info,
        "baseline": baseline,
        "total_links": len(full),
        "primary_clean_links": len(primary),
        "full_confidence": dict(sorted(Counter(row.get("confidence", "") for row in full).items())),
        "primary_confidence": dict(sorted(Counter(row.get("confidence", "") for row in primary).items())),
        "full_missing_anchor_count": missing_anchor_count(full),
        "primary_missing_anchor_count": missing_after,
        "missing_anchor_rows_resolved": missing_before - missing_after,
        "high_confidence_gained": max(0, high_after - high_before),
        "high_confidence_lost": max(0, high_before - high_after),
        "prior_high_primary_links_checked": len(prior_high_link_ids),
        "prior_high_primary_links_preserved": len(prior_high_link_ids) - len(missing_prior_high_link_ids),
        "prior_high_primary_links_lost": len(missing_prior_high_link_ids),
        "lost_prior_high_link_ids_sample": missing_prior_high_link_ids[:25],
        "medium_upgraded_to_high": change_counter.get("PROMOTE_TO_HIGH", 0),
        "low_upgraded_to_medium": change_counter.get("PROMOTE_TO_MEDIUM", 0),
        "rows_kept_low_or_review": change_counter.get("KEEP_REVIEW", 0) + change_counter.get("KEEP_LOW", 0),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in full),
        "relationship_type_counts": dict(sorted(Counter(row.get("relationship_type", "") for row in full).items())),
        "top_new_anchor_types": dict(anchor_type_counter.most_common(20)),
        "top_ontology_relations_matched": dict(relation_counter.most_common(20)),
        "anchor_change_rows": len(changes),
        "validation": validation,
        "primary_validation": primary_validation,
    }


def render_report(summary: dict[str, Any], output_root: Path) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    baseline = summary["baseline"]
    return f"""# Paadal-Pozhippurai v4 Missing Anchor Fix Report

## Acceptance

- Run status: `{summary['run_status']}`
- Accepted: `{str(summary['accepted']).lower()}`
- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`
- Ontology schema: `{summary['ontology']['ontology_schema_version']}`
- Relation schema: `{summary['ontology']['relation_schema_version']}`

## Baseline Versus Current

- Baseline total links: `{baseline['total_links']}`
- New total links: `{summary['total_links']}`
- Baseline primary high confidence: `{baseline['primary_confidence'].get('high', 0)}`
- New primary high confidence: `{summary['primary_confidence'].get('high', 0)}`
- Baseline primary missing anchor count: `{baseline['primary_missing_anchor_count']}`
- New primary missing anchor count: `{summary['primary_missing_anchor_count']}`
- Missing-anchor rows resolved: `{summary['missing_anchor_rows_resolved']}`
- High confidence gained: `{summary['high_confidence_gained']}`
- High confidence lost: `{summary['high_confidence_lost']}`
- Prior high primary links checked: `{summary['prior_high_primary_links_checked']}`
- Prior high primary links lost: `{summary['prior_high_primary_links_lost']}`
- Medium upgraded to high: `{summary['medium_upgraded_to_high']}`
- Low upgraded to medium: `{summary['low_upgraded_to_medium']}`
- Rows kept low/review: `{summary['rows_kept_low_or_review']}`
- Validation status: `{summary['validation']['status']}`
- Primary validation status: `{summary['primary_validation']['status']}`

## Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['full_confidence'])}

## Top New Anchor Types

| Anchor Type | Rows |
| --- | ---: |
{table(summary['top_new_anchor_types'])}

## Top Ontology Relations Matched

| Relation | Rows |
| --- | ---: |
{table(summary['top_ontology_relations_matched'])}

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
{table(summary['relationship_type_counts'])}

## Notes

- This pass fixes only `missing_anchor`.
- Broad targets, ambiguous spans, order-only rows, UI, scraper, and parser were not changed.
- Existing high-confidence links are preserved unless explicit critical warnings exist; this run did not downgrade any prior high-confidence primary links.
- This is an anchor-resolution hardening layer for retrieval/linking, not final scholarly gold accuracy.
"""


def write_outputs(
    output_root: Path,
    full: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    changes: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    report_path: Path,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_full.jsonl", full)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_full.tsv", full)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_primary_clean_links.jsonl", primary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_primary_clean_links.csv", primary)
    high_rows = [row for row in full if row.get("confidence") == "high" and not row.get("manual_review_required")]
    medium_rows = [row for row in full if row.get("confidence") == "medium" and not row.get("manual_review_required")]
    low_review_rows = [row for row in full if row.get("confidence") == "low" or row.get("manual_review_required")]
    no_link_or_unresolved_rows = [
        row
        for row in full
        if row.get("confidence") == "no_link"
        or row.get("relationship_type") == "unlinked"
        or (row.get("missing_anchor_before") and not row.get("missing_anchor_resolved"))
    ]
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_high_confidence.jsonl", high_rows)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_medium_confidence.jsonl", medium_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_low_review.csv", low_review_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_no_link_or_unresolved.csv", no_link_or_unresolved_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_anchor_changes.csv", changes)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_manual_review_pack.csv", review_rows)
    write_jsonl(output_root / "high_confidence.jsonl", high_rows)
    write_jsonl(output_root / "medium_confidence.jsonl", medium_rows)
    write_csv_file(output_root / "low_review.csv", low_review_rows)
    write_csv_file(output_root / "no_link_or_unresolved.csv", no_link_or_unresolved_rows)
    write_csv_file(output_root / "anchor_changes.csv", changes)
    write_csv_file(output_root / "manual_review_pack.csv", review_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_general_manual_review_pack.csv", build_manual_review_pack(full))
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_secondary_no_link.jsonl", secondary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_secondary_no_link.csv", secondary)
    write_iob_v4(output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_corrected_usable.iob.conll", [row for row in full if row.get("confidence") in {"high", "medium"} and row.get("target_text")])
    (output_root / "paadal_pozhippurai_links_v4_missing_anchor_fixed_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_report(summary, output_root), encoding="utf-8")
    (output_root / "report.md").write_text(render_report(summary, output_root), encoding="utf-8")
    (output_root / "baseline_vs_missing_anchor_fixed_report.md").write_text(render_report(summary, output_root), encoding="utf-8")


def run_fix(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    base_root: Path = DEFAULT_BASE_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    ontology_path: Path = DEFAULT_ONTOLOGY,
    relations_path: Path = DEFAULT_RELATIONS,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    ontology_info = load_existing_ontology(ontology_path, relations_path)
    rules, _ = load_anchor_rules()
    full = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl")
    primary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl")
    secondary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.jsonl")
    baseline = baseline_counts(base_root)
    prior_high_link_ids = {str(row.get("link_id", "")) for row in primary if row.get("confidence") == "high"}
    fixed_full, changes_full = apply_missing_anchor_fix(full, rules)
    fixed_primary, changes_primary = apply_missing_anchor_fix(primary, rules)
    validation = validate_v4_links(table_root, fixed_full)
    primary_validation = validate_clean_links(table_root, fixed_primary)
    summary = summarize(
        fixed_full,
        fixed_primary,
        changes_primary,
        baseline,
        validation,
        primary_validation,
        ontology_info,
        prior_high_link_ids,
    )
    review_rows = manual_review_rows(fixed_full, table_root)
    write_outputs(output_root, fixed_full, fixed_primary, secondary, changes_primary, review_rows, summary, report_path)
    return {**summary, "output_root": str(output_root), "report": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fix missing anchors in v4 hardened learned paadal-pozhppurai links.")
    parser.add_argument("--table-root", "--input-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--base-root", type=Path, default=DEFAULT_BASE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    parser.add_argument("--relations", type=Path, default=DEFAULT_RELATIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_fix(
        table_root=args.table_root,
        base_root=args.base_root,
        output_root=args.output_root,
        ontology_path=args.ontology,
        relations_path=args.relations,
        report_path=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
