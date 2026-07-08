from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from knowledge.annotate_thevaram_entities import (
    DEFAULT_REVIEW_DIR,
    DEFAULT_SEED_DIR,
    DEFAULT_TABLE_ROOT,
    SeedTerm,
    annotate,
    read_jsonl,
    stable_hash,
    write_jsonl,
)

SCHEMA_VERSION = "thevaram-entity-annotation-v3"
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_entity_annotations_v3")
DEFAULT_REPORT = Path("reports/thevaram-entity-annotation-v3-report.md")


def term_id(entity_type: str, alias: str, canonical_id: str) -> str:
    return "term_" + entity_type.lower() + "_" + stable_hash(alias, canonical_id, length=12)


def curated_term(
    alias: str,
    entity_type: str,
    canonical_id: str,
    canonical_name: str,
    *,
    subtype: str = "",
    confidence: float = 0.86,
    decision: str = "KEEP",
    rule: str = "v3 curated ontology expansion",
    gloss: str = "",
) -> SeedTerm:
    return SeedTerm(
        term_id=term_id(entity_type, alias, canonical_id),
        term=alias,
        entity_type=entity_type,
        canonical_id=canonical_id,
        canonical_name=canonical_name,
        gloss=gloss,
        source_seed_id="v3_" + stable_hash(entity_type, alias, canonical_id, length=10),
        source_file="v3_curated_ontology",
        note=rule,
        confidence=confidence,
        review_decision=decision,
        v2_rule=rule,
        entity_subtype=subtype,
        ontology_source="v3_curated_expansion",
    )


def add_aliases(
    terms: list[SeedTerm],
    aliases: list[str],
    entity_type: str,
    canonical_id: str,
    canonical_name: str,
    *,
    subtype: str = "",
    confidence: float = 0.86,
    decision: str = "KEEP",
    rule: str = "v3 curated ontology expansion",
) -> None:
    for alias in aliases:
        terms.append(
            curated_term(
                alias,
                entity_type,
                canonical_id,
                canonical_name,
                subtype=subtype,
                confidence=confidence,
                decision=decision,
                rule=rule,
            )
        )


def curated_ontology_terms(table_root: Path = DEFAULT_TABLE_ROOT) -> list[SeedTerm]:
    terms: list[SeedTerm] = []

    add_aliases(
        terms,
        [
            "சிவன்",
            "சிவபிரான்",
            "சிவபெருமான்",
            "ஈசன்",
            "ஈசர்",
            "ஹரன்",
            "அரன்",
            "சங்கரன்",
            "மகேசன்",
            "பரமன்",
            "ருத்ரன்",
            "பசுபதி",
            "எம்பெருமான்",
            "இறைவன்",
            "இறைவர்",
            "பெருமான்",
            "அண்ணல்",
        ],
        "DEITY",
        "deity_siva",
        "சிவன்",
        subtype="principal_deity",
        confidence=0.9,
    )
    add_aliases(
        terms,
        ["உமை", "உமையாள்", "உமையம்மை", "பார்வதி", "கௌரி", "அம்பிகை", "மலைமகள்"],
        "DEITY",
        "deity_parvati",
        "பார்வதி/உமை",
        subtype="goddess",
        confidence=0.88,
    )
    add_aliases(
        terms,
        ["பிரமன்", "பிரமா", "நான்முகன்", "அயன்"],
        "DEITY",
        "deity_brahma",
        "பிரமன்/நான்முகன்",
        subtype="deity",
        confidence=0.88,
    )
    add_aliases(
        terms,
        ["விஷ்ணு", "திருமால்", "மால்", "நாராயணன்", "மாயோன்", "அரி"],
        "DEITY",
        "deity_vishnu",
        "விஷ்ணு/திருமால்",
        subtype="deity",
        confidence=0.86,
    )
    add_aliases(
        terms,
        ["கணபதி", "பிள்ளையார்", "விநாயகர்", "கணேசன்"],
        "DEITY",
        "deity_ganapati",
        "கணபதி/பிள்ளையார்",
        subtype="deity",
        confidence=0.88,
    )
    add_aliases(
        terms,
        ["முருகன்", "சுப்பிரமணியன்", "கந்தன்", "வேலவன்", "குமரன்"],
        "DEITY",
        "deity_murugan",
        "முருகன்",
        subtype="deity",
        confidence=0.88,
    )
    add_aliases(
        terms,
        ["காலன்", "யமன்", "எமன்", "கூற்று"],
        "MYTHOLOGICAL_CHARACTER",
        "myth_yama",
        "காலன்/யமன்",
        subtype="death_deity",
        confidence=0.86,
    )
    add_aliases(
        terms,
        ["காமன்", "மன்மதன்", "மலர்க்கணை வேள்"],
        "MYTHOLOGICAL_CHARACTER",
        "myth_kama",
        "காமன்/மன்மதன்",
        subtype="mythic_figure",
        confidence=0.86,
    )
    add_aliases(
        terms,
        ["மார்க்கண்டேயன்", "இராவணன்", "ராவணன்", "இந்திரன்", "அகத்தியர்", "தக்கன்"],
        "MYTHOLOGICAL_CHARACTER",
        "mythic_character_group",
        "புராணப் பாத்திரங்கள்",
        subtype="mythic_figure",
        confidence=0.78,
        decision="CONTEXT_ONLY",
        rule="v3 mythological character; inspect short/common names in context",
    )

    add_aliases(
        terms,
        ["முக்கண்ணன்", "முக்கண்", "நீலகண்டன்", "நீலகண்டம்", "பிறைசூடி", "கங்காதரன்", "பசுபதி"],
        "DIVINE_EPITHET",
        "epithet_siva_iconic",
        "சிவனது திருப்பெயர்கள்",
        subtype="shiva_epithet",
        confidence=0.9,
    )
    add_aliases(
        terms,
        ["நடராசர்", "நடராஜர்", "அர்த்தநாரீஸ்வரர்", "தட்சிணாமூர்த்தி", "லிங்கோத்பவர்"],
        "DIVINE_FORM",
        "form_siva_manifestations",
        "சிவ வடிவங்கள்",
        subtype="shiva_form",
        confidence=0.9,
    )

    add_aliases(
        terms,
        ["திருமேனி", "திருவடி", "திருக்கரம்", "திருக்கண்", "முக்கண்", "நீலகண்டம்", "செஞ்சடை"],
        "BODY_PART",
        "body_part_divine_iconography",
        "தெய்வீக திருமேனி/அங்கங்கள்",
        subtype="divine_body_part",
        confidence=0.84,
    )
    add_aliases(
        terms,
        ["செஞ்சடை", "நீலகண்டம்", "பிறை", "மூன்றாம் கண்", "முக்கண்"],
        "ICONOGRAPHIC_FEATURE",
        "iconographic_siva_features",
        "சிவனது உருவச் சின்னங்கள்",
        subtype="iconographic_feature",
        confidence=0.86,
    )

    add_aliases(
        terms,
        ["காவிரி", "கங்கை", "பொன்னி"],
        "SACRED_RIVER",
        "sacred_rivers",
        "புனித நதிகள்",
        subtype="sacred_river",
        confidence=0.88,
    )
    add_aliases(
        terms,
        ["கயிலை", "கயிலாயம்", "மேரு", "இமயம்"],
        "SACRED_MOUNTAIN",
        "sacred_mountains",
        "புனித மலைகள்",
        subtype="sacred_mountain",
        confidence=0.88,
    )
    add_aliases(
        terms,
        ["கொன்றை", "வில்வம்", "வன்னி", "ஆலம்", "அரசு"],
        "SACRED_TREE",
        "sacred_trees",
        "புனித மரங்கள்",
        subtype="sacred_tree",
        confidence=0.84,
    )
    add_aliases(
        terms,
        ["தாமரை", "செண்பகம்", "மல்லிகை", "அரளி", "தும்பை"],
        "SACRED_FLOWER",
        "sacred_flowers",
        "புனித மலர்கள்",
        subtype="sacred_flower",
        confidence=0.84,
    )
    add_aliases(
        terms,
        ["நந்தி", "விடை", "புலி", "பாம்பு", "மான்", "யானை"],
        "NATURE",
        "nature_animals_iconic",
        "விலங்கு/உருவக இயற்கை",
        subtype="animal",
        confidence=0.8,
    )

    add_aliases(
        terms,
        ["திரிசூலம்", "சூலம்", "மழு", "வில்", "அம்பு"],
        "WEAPON",
        "weapon_siva_mythic",
        "ஆயுதங்கள்",
        subtype="weapon",
        confidence=0.88,
    )
    add_aliases(
        terms,
        ["திரிசூலம்", "சூலம்", "மழு", "வில்", "அம்பு"],
        "SACRED_OBJECT",
        "sacred_object_weapons",
        "திருவாயுதங்கள்",
        subtype="weapon",
        confidence=0.84,
    )
    add_aliases(
        terms,
        ["கொன்றைமாலை", "பிறை", "பாம்பணிவு", "ருத்ராட்சம்", "திருநீறு", "நீறு", "டமரு", "உடுக்கை"],
        "SACRED_OBJECT",
        "sacred_object_iconic_symbols",
        "திருச்சின்னங்கள்/அணிகலன்கள்",
        subtype="ornament_or_symbol",
        confidence=0.84,
    )
    add_aliases(
        terms,
        ["அபிஷேகம்", "அர்ச்சனை", "தீபம்", "வேள்வி", "பூசை", "பலி"],
        "RITUAL",
        "ritual_saiva_practice",
        "சைவ சடங்குகள்",
        subtype="ritual",
        confidence=0.84,
    )
    add_aliases(
        terms,
        ["சிவராத்திரி", "திருவாதிரை", "பிரதோஷம்"],
        "FESTIVAL",
        "festival_saiva",
        "சைவத் திருவிழாக்கள்",
        subtype="festival",
        confidence=0.88,
    )
    add_aliases(
        terms,
        ["யாழ்", "வீணை", "உடுக்கை", "முரசு", "பறை"],
        "MUSICAL_INSTRUMENT",
        "music_instruments",
        "இசைக்கருவிகள்",
        subtype="musical_instrument",
        confidence=0.82,
    )
    add_aliases(
        terms,
        ["கோபுரம்", "விமானம்", "மண்டபம்", "சந்நிதி", "திருக்குளம்", "கோயில்"],
        "TEMPLE_ARCHITECTURE",
        "temple_architecture",
        "கோயில் கட்டமைப்பு",
        subtype="temple_architecture",
        confidence=0.78,
        decision="CONTEXT_ONLY",
        rule="v3 temple architecture; common words require context review",
    )
    add_aliases(
        terms,
        ["அடியார்", "குரு", "சீடன்", "துணைவி", "நாயகி", "நாயகன்"],
        "RELATIONSHIP",
        "devotional_relationships",
        "பக்தி/சம்பந்த உறவுகள்",
        subtype="relationship_role",
        confidence=0.76,
        decision="CONTEXT_ONLY",
    )
    add_aliases(
        terms,
        [
            "பதி",
            "பசு",
            "பாசம்",
            "முத்தி",
            "சிவஞானம்",
            "அருள்",
            "ஆனந்தம்",
            "பிறவி",
            "வினை",
            "மலம்",
            "மாயை",
        ],
        "THEOLOGICAL_CONCEPT",
        "theology_saiva_siddhanta",
        "சைவ சித்தாந்தக் கருத்துகள்",
        subtype="saiva_siddhanta_concept",
        confidence=0.78,
        decision="CONTEXT_ONLY",
    )

    event_aliases = {
        "event_tripura_burning": ("திரிபுரம் எரித்தல்", ["திரிபுரம் எரித்தல்", "திரிபுரம் செற்று", "முப்புரம் எரித்த"]),
        "event_kala_defeat": ("காலனை உதைத்தல்", ["காலனை உதைத்தல்", "காலனைப் பாதம் ஒன்றால் உதைத்து", "காலன் திறல் அறச் சாடிய", "கூற்று உதைசெய்த"]),
        "event_ganga_bearing": ("கங்கை தாங்குதல்", ["கங்கை தாங்குதல்", "கங்கை சடைமேலே", "கங்கையைத் தாழ்சடைமேல்", "கங்கை சடை"]),
        "event_poison_drinking": ("நஞ்சுண்டல்", ["நஞ்சுண்டல்", "நஞ்சு உண்டு", "கறை ஆர் மிடறு", "நீலகண்டம்"]),
        "event_daksha_sacrifice": ("தக்கன் வேள்வி சிதைத்தல்", ["தக்கன் வேள்வி", "தக்கனது வேள்வி", "வேள்வி கெடச் சாடி"]),
        "event_kama_burning": ("காமனை எரித்தல்", ["காமனை", "மலர்க்கணை வேள் உலக்க", "காமன்"]),
    }
    for canonical_id, (canonical_name, aliases) in event_aliases.items():
        add_aliases(
            terms,
            aliases,
            "MYTHOLOGICAL_EVENT",
            canonical_id,
            canonical_name,
            subtype="mythological_event",
            confidence=0.88,
        )

    add_aliases(
        terms,
        ["திருஞானசம்பந்தர்", "ஞானசம்பந்தன்", "சம்பந்தர்", "திருநாவுக்கரசர்", "அப்பர்", "சுந்தரர்", "கண்ணப்பர்"],
        "SAINT",
        "saint_saiva_nayanmar",
        "சைவ நாயன்மார்கள்",
        subtype="saint",
        confidence=0.86,
    )

    for row in read_jsonl(table_root / "paadal_thogupugal.jsonl"):
        thalam = str(row.get("paadapatta_thalam", "")).strip()
        title = str(row.get("title", "")).strip()
        for alias in {thalam, title.split(" - ")[0].strip() if title else ""}:
            if not alias or alias == "பொது":
                continue
            terms.append(
                curated_term(
                    alias,
                    "TEMPLE",
                    "temple_" + stable_hash(alias, length=12),
                    alias,
                    subtype="paadapatta_thalam",
                    confidence=0.9,
                    rule="v3 dynamic temple/thalam term from normalized paadal_thogupugal",
                )
            )

    return sorted(
        {(term.term, term.entity_type, term.canonical_id): term for term in terms}.values(),
        key=lambda item: (-len(item.term), item.entity_type, item.term, item.canonical_id),
    )


def curated_relationships() -> list[dict[str, Any]]:
    edges = [
        ("deity_siva", "consort_of", "deity_parvati", "Shiva and Uma/Parvati relation"),
        ("deity_parvati", "consort_of", "deity_siva", "Uma/Parvati and Shiva relation"),
        ("epithet_siva_iconic", "epithet_of", "deity_siva", "Siva epithets"),
        ("form_siva_manifestations", "manifestation_of", "deity_siva", "Siva forms"),
        ("sacred_rivers", "associated_with", "deity_siva", "Sacred rivers in Siva iconography"),
        ("sacred_mountains", "associated_with", "deity_siva", "Sacred mountains"),
        ("sacred_trees", "associated_with", "deity_siva", "Sacred trees/garlands"),
        ("weapon_siva_mythic", "weapon_of", "deity_siva", "Siva weapons"),
        ("sacred_object_iconic_symbols", "worn_or_held_by", "deity_siva", "Siva iconographic objects"),
        ("event_tripura_burning", "performed_by", "deity_siva", "Tripura burning"),
        ("event_kala_defeat", "performed_by", "deity_siva", "Kalan/Yama defeated"),
        ("event_ganga_bearing", "performed_by", "deity_siva", "Ganga borne in matted hair"),
        ("event_poison_drinking", "performed_by", "deity_siva", "Poison drinking/blue throat"),
        ("event_daksha_sacrifice", "performed_by", "deity_siva", "Daksha sacrifice destroyed"),
        ("event_kama_burning", "performed_by", "deity_siva", "Kama burned"),
        ("event_kala_defeat", "defeats", "myth_yama", "Siva defeats Kalan/Yama"),
        ("event_kama_burning", "defeats", "myth_kama", "Siva burns Kama"),
    ]
    rows: list[dict[str, Any]] = []
    for source, relation_type, target, note in edges:
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "relationship_id": "rel_" + stable_hash(source, relation_type, target, length=16),
                "relationship_source": "v3_curated_ontology",
                "source_entity_id": source,
                "relationship_type": relation_type,
                "target_entity_id": target,
                "confidence": 0.9,
                "evidence_count": 1,
                "note": note,
            }
        )
    return rows


def cooccurrence_relationships(mentions: list[dict[str, Any]], min_count: int = 3) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for mention in mentions:
        paadal_id = str(mention.get("paadal_id", ""))
        entity_id = str(mention.get("canonical_id", ""))
        if not paadal_id or not entity_id:
            continue
        grouped[paadal_id][entity_id] = {
            "entity_id": entity_id,
            "entity_type": mention.get("entity_type", ""),
            "canonical_name": mention.get("canonical_name", ""),
        }

    counts: Counter[tuple[str, str]] = Counter()
    examples: dict[tuple[str, str], str] = {}
    entity_meta: dict[str, dict[str, Any]] = {}
    for paadal_id, entities in grouped.items():
        for entity_id, meta in entities.items():
            entity_meta[entity_id] = meta
        for left, right in combinations(sorted(entities), 2):
            counts[(left, right)] += 1
            examples.setdefault((left, right), paadal_id)

    rows: list[dict[str, Any]] = []
    for (left, right), count in counts.most_common():
        if count < min_count:
            continue
        left_meta = entity_meta.get(left, {})
        right_meta = entity_meta.get(right, {})
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "relationship_id": "rel_co_" + stable_hash(left, right, length=16),
                "relationship_source": "corpus_cooccurrence",
                "source_entity_id": left,
                "source_entity_type": left_meta.get("entity_type", ""),
                "source_entity_name": left_meta.get("canonical_name", ""),
                "relationship_type": "co_occurs_in_paadal",
                "target_entity_id": right,
                "target_entity_type": right_meta.get("entity_type", ""),
                "target_entity_name": right_meta.get("canonical_name", ""),
                "confidence": round(min(0.85, 0.45 + count / 100), 2),
                "evidence_count": count,
                "example_paadal_id": examples.get((left, right), ""),
                "note": "Candidate relation from repeated co-occurrence; requires scholarly review.",
            }
        )
    return rows


def cross_type_overlaps(mentions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for mention in mentions:
        grouped[
            (
                str(mention.get("target_table", "")),
                str(mention.get("target_id", "")),
                str(mention.get("field_name", "")),
            )
        ].append(mention)

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for (target_table, target_id, field_name), group in grouped.items():
        ordered = sorted(group, key=lambda row: (int(row["start_char"]), int(row["end_char"])))
        for index, left in enumerate(ordered):
            left_start = int(left["start_char"])
            left_end = int(left["end_char"])
            for right in ordered[index + 1 :]:
                right_start = int(right["start_char"])
                right_end = int(right["end_char"])
                if right_start >= left_end:
                    break
                if left.get("entity_type") == right.get("entity_type"):
                    continue
                if not (left_start < right_end and right_start < left_end):
                    continue
                key = tuple(sorted([str(left["mention_id"]), str(right["mention_id"])]))
                if key in seen:
                    continue
                seen.add(key)
                overlap_start = max(left_start, right_start)
                overlap_end = min(left_end, right_end)
                rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "overlap_id": "xover_" + stable_hash(*key, length=16),
                        "target_table": target_table,
                        "target_id": target_id,
                        "paadal_id": left.get("paadal_id") or right.get("paadal_id"),
                        "thirumurai_no": left.get("thirumurai_no") or right.get("thirumurai_no"),
                        "field_name": field_name,
                        "overlap_start_char": overlap_start,
                        "overlap_end_char": overlap_end,
                        "overlap_text": str(left.get("mention_text", ""))[
                            max(0, overlap_start - left_start) : max(0, overlap_end - left_start)
                        ],
                        "left_mention_id": left.get("mention_id"),
                        "left_entity_type": left.get("entity_type"),
                        "left_entity_subtype": left.get("entity_subtype", ""),
                        "left_canonical_id": left.get("canonical_id"),
                        "left_canonical_name": left.get("canonical_name"),
                        "right_mention_id": right.get("mention_id"),
                        "right_entity_type": right.get("entity_type"),
                        "right_entity_subtype": right.get("entity_subtype", ""),
                        "right_canonical_id": right.get("canonical_id"),
                        "right_canonical_name": right.get("canonical_name"),
                        "interpretation": "same span carries multiple ontology roles; preserve both for retrieval and relationship extraction",
                    }
                )
    return sorted(
        rows,
        key=lambda row: (
            str(row["target_table"]),
            str(row["target_id"]),
            str(row["field_name"]),
            int(row["overlap_start_char"]),
            str(row["left_entity_type"]),
            str(row["right_entity_type"]),
        ),
    )


def run_v3(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
    review_dir: Path = DEFAULT_REVIEW_DIR,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    extra_terms = curated_ontology_terms(table_root)
    summary = annotate(
        table_root=table_root,
        seed_dir=seed_dir,
        review_dir=review_dir,
        output_root=output_root,
        report_path=report_path,
        extra_terms=extra_terms,
        schema_version=SCHEMA_VERSION,
        report_title="Thevaram Entity Annotation v3 Report",
    )
    mentions = read_jsonl(output_root / "entity_mentions.jsonl")
    curated = curated_relationships()
    cooccur = cooccurrence_relationships(mentions)
    relationships = curated + cooccur
    overlaps = cross_type_overlaps(mentions)
    write_jsonl(output_root / "entity_relationships.jsonl", relationships)
    write_jsonl(output_root / "entity_cross_type_overlaps.jsonl", overlaps)

    summary["counts"]["entity_relationships"] = len(relationships)
    summary["counts"]["entity_cross_type_overlaps"] = len(overlaps)
    summary["extra_terms_loaded"] = len(extra_terms)
    summary["relationship_counts_by_source"] = dict(
        sorted(Counter(row["relationship_source"] for row in relationships).items())
    )
    summary["relationship_counts_by_type"] = dict(
        sorted(Counter(row["relationship_type"] for row in relationships).items())
    )
    summary["mention_counts_by_subtype"] = dict(
        sorted(
            Counter(
                f"{row['entity_type']}:{row.get('entity_subtype') or 'unspecified'}"
                for row in mentions
            ).items()
        )
    )
    (output_root / "annotation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = report_path.read_text(encoding="utf-8")
    report += "\n## v3 Ontology Expansion\n\n"
    report += f"- Extra curated/dynamic terms loaded: `{len(extra_terms)}`\n"
    report += f"- Entity relationships written: `{len(relationships)}`\n"
    report += f"- Cross-type overlap records written: `{len(overlaps)}`\n"
    report += f"- Relationship sources: `{summary['relationship_counts_by_source']}`\n"
    report += f"- Relationship types: `{summary['relationship_counts_by_type']}`\n"
    report += "\n"
    report += "v3 is an aggressive deterministic expansion layer. It improves coverage for retrieval and linking, but new/context-only aliases should still be reviewed before being treated as final scholarly gold.\n"
    report_path.write_text(report, encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build expanded Thevaram entity annotation v3 with ontology terms and relationships."
    )
    parser.add_argument("--table-root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_v3(
        table_root=args.table_root,
        seed_dir=args.seed_dir,
        review_dir=args.review_dir,
        output_root=args.output_root,
        report_path=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["validation"]["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
