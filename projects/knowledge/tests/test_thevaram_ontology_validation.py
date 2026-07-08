from pathlib import Path

from knowledge.validate_thevaram_ontology import (
    DEFAULT_MIGRATION,
    DEFAULT_ONTOLOGY,
    DEFAULT_RELATIONS,
    build_summary,
)


def test_thevaram_ontology_v1_contract_is_valid() -> None:
    summary = build_summary(
        ontology_path=DEFAULT_ONTOLOGY,
        relations_path=DEFAULT_RELATIONS,
        migration_path=DEFAULT_MIGRATION,
        v2_root=Path("data/processed/thevaram_entity_annotations_v2"),
        v3_root=Path("data/processed/thevaram_entity_annotations_v3"),
    )

    assert summary["status"] == "VALID"
    assert summary["entity_type_count"] == 25
    assert summary["relation_count"] >= 24
    assert summary["attribute_count"] == 14
    assert summary["myth_event_count"] == 20
    assert {"ACTION", "NATURE"} <= set(summary["deprecated_v2_types"])
    assert "DIVINE_EPITHET" in summary["required_types_present"]
    assert "SACRED_PLACE" in summary["required_types_present"]
    assert "MYTH_EVENT" in summary["required_types_present"]


def test_measured_baseline_includes_v2_and_v3_counts() -> None:
    summary = build_summary()
    measured = summary["measured_counts"]

    assert measured["v2"]["mentions"] > 0
    assert measured["v2"]["cross_type_overlap_spans"] > 0
    assert measured["v3"]["mentions"] >= measured["v2"]["mentions"]
    assert measured["v3"]["temple_mentions"] > 0
    assert measured["v3"]["paadapatta_thalam_mentions"] > 0
