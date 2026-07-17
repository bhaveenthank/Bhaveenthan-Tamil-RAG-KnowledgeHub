from pathlib import Path

from knowledge.build_pozhippurai_links_v4 import write_iob_v4
from knowledge.build_pozhippurai_links_v4_blocker_hardened import (
    DEFAULT_BLOCKER_PACK,
    REQUIRED_FEATURE_FIELDS,
    append_split_children,
    blocker_base_features,
    blocker_score_and_confidence,
    harden_links_with_blocker_pack,
    load_blocker_pack,
    matching_patterns,
    resolve_anchor_ids,
    select_minimal_target,
)


def linked_row(
    *,
    link_id: str = "ppl_v4_base_fixture",
    source: str,
    target: str,
    relationship: str = "interprets_image",
    confidence: str = "low",
    score: float = 0.24,
    note: str = "The selected target is mainly supported by poem/commentary order.",
    margin: float = 0.5,
) -> dict:
    return {
        "schema_version": "thevaram-pozhppurai-paadallink-v4",
        "link_id": link_id,
        "thirumurai_no": 1,
        "paadal_id": "p1",
        "commentary_id": "p1_commentary",
        "source_field": "paadal_text",
        "target_field": "pozhppurai",
        "source_text": source,
        "source_text_normalized": source,
        "target_text": target,
        "relationship_type": relationship,
        "confidence": confidence,
        "score": score,
        "source_start_char": 0,
        "source_end_char": len(source),
        "target_start_char": 0,
        "target_end_char": len(target),
        "rule_ids_applied": [],
        "manual_review_required": confidence == "low",
        "diagnostic_note": note,
        "method": "fixture",
        "features": {"score_margin": margin},
    }


def test_blocker_pack_loads_review_inputs() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    assert pack.profile["positive_recovered_links"] == 28
    assert len(pack.patterns) >= 6
    assert len(pack.anchors) >= 10
    assert len(pack.test_cases) >= 30


def test_anchor_resolver_recovers_ganga_moon_and_hair() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    anchors = resolve_anchor_ids(
        "அலை, வளர் தண்மதியோடு அயலே அடக்கி",
        "கங்கையையும், குளிர்ந்த சந்திரனையும் சடை முடியிலே அடக்கி",
        pack,
    )
    assert {"ANCH_CRESCENT_001", "ANCH_GANGA_002"} <= anchors


def test_crescent_hair_examples_become_high_confidence_interprets_image() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    row = linked_row(
        link_id="ppl_v4_base_9a203bea66f3f56a",
        source="மேகமொடு ஓடு திங்கள் மலரா அணிந்து, மலையான்",
        target="மேகங்களோடு ஓடும் திங்களைக் கண்ணியாகச் சூடி",
    )
    hardened, _counts = harden_links_with_blocker_pack([row], pack=pack)
    assert hardened[0]["relationship_type"] == "interprets_image"
    assert hardened[0]["confidence"] == "high"
    assert not hardened[0]["manual_review_required"]


def test_serpent_waist_target_is_high_confidence_after_reviewed_shrink() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    row = linked_row(
        link_id="ppl_v4_base_6275f770ba71a288",
        source="ஐந்தலைய மா நாகம் அரையில் சாத்தி",
        target="சடைமுடியில் கங்கையைத் தரித்து, இடையில் அணிந்த தோலாடை மீது ஐந்தலையை உடைய பெரிய பாம்பினை இறுகக் கட்டி",
    )
    hardened, counts = harden_links_with_blocker_pack([row], pack=pack)
    assert "பாம்பினை இறுகக் கட்டி" in hardened[0]["target_text"]
    assert "கங்கையைத் தரித்து" not in hardened[0]["target_text"]
    assert hardened[0]["confidence"] == "high"
    assert counts["anchor_resolver_recovered_rows"] >= 1


def test_worship_result_promotes_to_theological_explanation() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    row = linked_row(
        link_id="ppl_v4_base_3db905d105db9db4",
        source="அழகர் பாதம் தொழுது ஏத்த வல்லார்க்கு அழகு ஆகுமே",
        target="நாகேச்சுரத்தில் விளங்கும் அழகர் பாதங்களைத் தொழுது போற்றவல்லார்க்கு அழகு நலம் வாய்க்கும்",
        relationship="explains_phrase",
    )
    hardened, _counts = harden_links_with_blocker_pack([row], pack=pack)
    assert hardened[0]["relationship_type"] == "theological_explanation"
    assert hardened[0]["confidence"] == "high"


def test_broad_target_selector_prefers_minimal_span() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    row = linked_row(
        source="விரவும் திரு முடி தன் மேல் வெண்திங்கள் சூடி",
        target="புலித்தோலை உடுத்து, அழகிய முடிமீது பொருந்திய வெண்பிறையைச்சூடி, திருவடிகளை பணிய இன்பம் உளதாம்",
    )
    target, _start, _end, changed = select_minimal_target(row["source_text"], row["target_text"], row, pack)
    assert changed
    assert target == "அழகிய முடிமீது பொருந்திய வெண்பிறையைச்சூடி"


def test_split_examples_create_child_links() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    parent = linked_row(
        link_id="ppl_v4_base_48cde99b5b041b18",
        source="வெண்மதி சூடி விளங்க நின்றானை",
        target="வெண்பிறை சூடி உலகு விளங்கு நிற்பவனாய், தேவர்கள் தொழுமாறு",
        confidence="medium",
        score=0.6,
    )
    rows = append_split_children([parent], pack)
    child_ids = {row["link_id"] for row in rows}
    assert "ppl_v4_base_48cde99b5b041b18_S1" in child_ids
    assert "ppl_v4_base_48cde99b5b041b18_S2" in child_ids


def test_order_only_examples_are_not_promoted() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    row = linked_row(
        link_id="ppl_v4_base_0c0e5790787c38f2",
        source="மல் ஆர்ந்த கோயிலே கோயில் ஆக மகிழ்ந்தீரே",
        target="பொல்லாத சமணர்களோடு புறங்கூறும் சாக்கியர் என்ற ஒன்றிலும் சேராதார் கூறும் அறவுரைகளை விட்டு",
        relationship="explains_phrase",
        score=0.7,
    )
    hardened, _counts = harden_links_with_blocker_pack([row], pack=pack)
    assert hardened[0]["confidence"] != "high"
    assert hardened[0]["manual_review_required"]
    assert "order_only_penalty" in hardened[0]["penalties_applied"]


def test_duplicate_link_ids_are_deduplicated() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    low = linked_row(link_id="dup", source="அடி ஒன்று", target="சம்பந்தமில்லா உரை", confidence="low", score=0.2)
    high = linked_row(link_id="dup", source="பிறை முடிமேல்", target="வெண்பிறையைச் சூடி", confidence="high", score=0.9)
    hardened, counts = harden_links_with_blocker_pack([low, high], pack=pack)
    assert len([row for row in hardened if row["link_id"] == "dup"]) == 1
    assert counts["duplicate_link_ids_deduped"] == 1


def test_required_feature_fields_are_emitted() -> None:
    pack = load_blocker_pack(DEFAULT_BLOCKER_PACK)
    row = linked_row(source="சடை ஆர் புனல்", target="சடைமுடியில் கங்கையைத் தரித்தவனும்")
    hardened, _counts = harden_links_with_blocker_pack([row], pack=pack)
    assert set(REQUIRED_FEATURE_FIELDS) <= set(hardened[0]["feature_scores"])


def test_iob_output_has_paadal_and_pozhppurai_sides_for_positive_links(tmp_path: Path) -> None:
    row = linked_row(source="பிறை முடிமேல்", target="வெண்பிறையைச் சூடி", confidence="high", score=0.9)
    row["manual_review_required"] = False
    output = tmp_path / "links.iob.conll"
    write_iob_v4(output, [row])
    sides_by_link: dict[str, set[str]] = {}
    for line in output.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        _token, _label, link_id, side, _relationship, _confidence = line.split("\t")
        sides_by_link.setdefault(link_id, set()).add(side)
    assert sides_by_link
    assert all({"paadal", "pozhppurai"} <= sides for sides in sides_by_link.values())
