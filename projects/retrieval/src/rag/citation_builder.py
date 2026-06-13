from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REQUIRED_CITATION_FIELDS = (
    "citation_id",
    "parent_record_id",
    "chunk_id",
    "source_title",
    "collection",
    "thirumurai",
    "hymn_id",
    "song_no",
    "citation_text",
    "source_url",
    "retrieval_mode",
    "retrieval_rank",
)


def load_context_package(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def split_source_urls(urls: list[str]) -> tuple[str, str]:
    source_url = ""
    commentary_url = ""
    for url in urls:
        lowered = url.lower()
        if "uri.jsp" in lowered or "comment" in lowered:
            commentary_url = commentary_url or url
        else:
            source_url = source_url or url
    if not source_url and urls:
        source_url = urls[0]
    if not commentary_url and len(urls) > 1:
        commentary_url = next((url for url in urls if url != source_url), "")
    return source_url, commentary_url


def citation_from_context(context: dict[str, Any], citation_index: int, retrieval_mode: str) -> dict[str, Any]:
    source = context.get("citation", {})
    source_url, commentary_url = split_source_urls(source.get("source_urls", []))
    return {
        "citation_id": f"cit_{citation_index:03d}",
        "context_id": context.get("context_id", ""),
        "parent_record_id": context.get("parent_record_id", ""),
        "chunk_id": context.get("chunk_id", ""),
        "chunk_type": context.get("chunk_type", ""),
        "source_name": source.get("source_name", ""),
        "source_title": source.get("source_title", ""),
        "author": source.get("author", ""),
        "collection": source.get("collection", ""),
        "thirumurai": source.get("thirumurai", ""),
        "hymn_id": str(source.get("hymn_id", "")),
        "song_no": str(source.get("song_no", "")),
        "citation_text": source.get("citation_text", ""),
        "source_url": source_url,
        "commentary_url": commentary_url,
        "retrieval_mode": retrieval_mode,
        "retrieval_rank": context.get("rank"),
        "matched_modes": context.get("matched_modes", []),
        "retrieval_score": context.get("hybrid_score", 0.0),
        "deterministic_rank_key": context.get("deterministic_rank_key", ""),
    }


def validate_citation(citation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    citation_id = citation.get("citation_id", "unknown")
    for field in REQUIRED_CITATION_FIELDS:
        value = citation.get(field)
        if value is None or value == "":
            errors.append(f"{citation_id}: missing {field}")
    if citation.get("retrieval_rank") is not None and (
        not isinstance(citation["retrieval_rank"], int) or citation["retrieval_rank"] < 1
    ):
        errors.append(f"{citation_id}: malformed retrieval_rank")
    for field in ("source_url", "commentary_url"):
        value = citation.get(field, "")
        if value and not is_valid_url(value):
            errors.append(f"{citation_id}: malformed {field}")
    if citation.get("source_url") and citation.get("source_url") == citation.get("commentary_url"):
        errors.append(f"{citation_id}: source_url duplicates commentary_url")
    return errors


def duplicate_keys(citations: list[dict[str, Any]]) -> list[str]:
    counts = Counter(
        (citation.get("parent_record_id"), citation.get("chunk_id"))
        for citation in citations
    )
    return [
        f"{parent_record_id}|{chunk_id}"
        for (parent_record_id, chunk_id), count in sorted(counts.items())
        if count > 1
    ]


def validate_citation_package(package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    citations = package.get("citations", [])
    if package.get("citation_count") != len(citations):
        errors.append("citation_count does not match citations")
    expected_ids = [f"cit_{index:03d}" for index in range(1, len(citations) + 1)]
    if [citation.get("citation_id") for citation in citations] != expected_ids:
        errors.append("citation IDs are not deterministic")
    for citation in citations:
        errors.extend(validate_citation(citation))
    for duplicate in duplicate_keys(citations):
        errors.append(f"duplicate citation: {duplicate}")

    known_ids = {citation["citation_id"] for citation in citations}
    for group in package.get("citation_groups", []):
        if not group.get("group_id") or not group.get("group_key"):
            errors.append("malformed citation group")
        unknown = set(group.get("citation_ids", [])) - known_ids
        if unknown:
            errors.append(f"{group.get('group_id', 'unknown')}: unknown citation IDs {sorted(unknown)}")
    for segment in package.get("answer_segment_citations", []):
        unknown = set(segment.get("citation_ids", [])) - known_ids
        if unknown:
            errors.append(f"{segment.get('segment_id', 'unknown')}: unknown citation IDs {sorted(unknown)}")
    return errors


def build_groups(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for citation in citations:
        key = "|".join(
            [
                citation.get("collection", ""),
                citation.get("thirumurai", ""),
                citation.get("hymn_id", ""),
                citation.get("source_title", ""),
            ]
        )
        grouped[key].append(citation)

    groups = []
    for index, key in enumerate(sorted(grouped), start=1):
        members = sorted(
            grouped[key],
            key=lambda citation: (
                citation.get("retrieval_rank", 0),
                citation.get("deterministic_rank_key", ""),
                citation["citation_id"],
            ),
        )
        first = members[0]
        groups.append(
            {
                "group_id": f"grp_{index:03d}",
                "group_key": key,
                "source_title": first["source_title"],
                "collection": first["collection"],
                "thirumurai": first["thirumurai"],
                "hymn_id": first["hymn_id"],
                "citation_ids": [citation["citation_id"] for citation in members],
                "song_numbers": [citation["song_no"] for citation in members],
            }
        )
    return groups


def build_segment_map(
    segment_citations: dict[str, list[str]] | None,
    known_citation_ids: set[str],
) -> list[dict[str, Any]]:
    if not segment_citations:
        return []
    segments = []
    for segment_id in sorted(segment_citations):
        citation_ids = list(dict.fromkeys(segment_citations[segment_id]))
        unknown = set(citation_ids) - known_citation_ids
        if unknown:
            raise ValueError(f"{segment_id}: unknown citation IDs {sorted(unknown)}")
        segments.append({"segment_id": segment_id, "citation_ids": citation_ids})
    return segments


def build_citation_package(
    context_package: dict[str, Any],
    segment_citations: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    contexts = sorted(
        context_package.get("contexts", []),
        key=lambda context: (
            context.get("rank", 0),
            context.get("deterministic_rank_key", ""),
            context.get("parent_record_id", ""),
            context.get("chunk_id", ""),
        ),
    )
    citations = []
    seen: set[tuple[str, str]] = set()
    for context in contexts:
        key = (context.get("parent_record_id", ""), context.get("chunk_id", ""))
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            citation_from_context(
                context,
                citation_index=len(citations) + 1,
                retrieval_mode=context_package.get("retrieval_mode", ""),
            )
        )

    package = {
        "query": context_package.get("query", ""),
        "retrieval_mode": context_package.get("retrieval_mode", ""),
        "citation_count": len(citations),
        "citations": citations,
        "citation_groups": build_groups(citations),
        "answer_segment_citations": build_segment_map(
            segment_citations,
            {citation["citation_id"] for citation in citations},
        ),
        "validation": {"status": "valid", "errors": []},
    }
    errors = validate_citation_package(package)
    package["validation"] = {
        "status": "valid" if not errors else "invalid",
        "errors": errors,
    }
    if errors:
        raise ValueError("invalid citation package: " + "; ".join(errors))
    return package


def citation_metrics(package: dict[str, Any]) -> dict[str, Any]:
    citations = package.get("citations", [])
    total = len(citations)
    complete = sum(not validate_citation(citation) for citation in citations)
    source_url_count = sum(bool(citation.get("source_url")) for citation in citations)
    commentary_url_count = sum(bool(citation.get("commentary_url")) for citation in citations)
    duplicates = duplicate_keys(citations)
    missing_fields = Counter(
        field
        for citation in citations
        for field in REQUIRED_CITATION_FIELDS
        if citation.get(field) in {None, ""}
    )
    return {
        "context_count": total,
        "citation_count": total,
        "citation_coverage": round(complete / total, 4) if total else 0.0,
        "complete_citations": complete,
        "incomplete_citations": total - complete,
        "source_url_coverage": round(source_url_count / total, 4) if total else 0.0,
        "commentary_url_coverage": round(commentary_url_count / total, 4) if total else 0.0,
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
        "missing_fields": dict(sorted(missing_fields.items())),
        "group_count": len(package.get("citation_groups", [])),
    }


def render_citation_report(package: dict[str, Any], input_path: str = "") -> str:
    metrics = citation_metrics(package)
    lines = [
        "# Citation Grounding Report",
        "",
        "## Summary",
        "",
        f"- Input context package: `{input_path}`",
        f"- Contexts represented: `{metrics['context_count']}`",
        f"- Citations generated: `{metrics['citation_count']}`",
        f"- Citation groups: `{metrics['group_count']}`",
        f"- Citation coverage: `{metrics['citation_coverage'] * 100:.2f}%`",
        f"- Complete citations: `{metrics['complete_citations']}`",
        f"- Incomplete citations: `{metrics['incomplete_citations']}`",
        f"- Source URL coverage: `{metrics['source_url_coverage'] * 100:.2f}%`",
        f"- Commentary URL coverage: `{metrics['commentary_url_coverage'] * 100:.2f}%`",
        f"- Duplicate citations removed/detected: `{metrics['duplicate_count']}`",
        "",
        "## Citation Coverage",
        "",
        "| Citation ID | Context | Hymn ID | Song No | Source URL | Commentary URL | Complete |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for citation in package.get("citations", []):
        lines.append(
            f"| `{citation['citation_id']}` | `{citation['context_id']}` | `{citation['hymn_id']}` | `{citation['song_no']}` | `{bool(citation['source_url'])}` | `{bool(citation['commentary_url'])}` | `{not validate_citation(citation)}` |"
        )
    lines.extend(["", "## Missing Field Analysis", ""])
    if metrics["missing_fields"]:
        for field, count in metrics["missing_fields"].items():
            lines.append(f"- `{field}`: `{count}`")
    else:
        lines.append("- No required citation fields are missing.")
    lines.extend(["", "## Duplicate Analysis", ""])
    if metrics["duplicates"]:
        for duplicate in metrics["duplicates"]:
            lines.append(f"- `{duplicate}`")
    else:
        lines.append("- No duplicate citation records remain.")
    lines.extend(
        [
            "",
            "## Grounding Decision",
            "",
            f"- Package validation: `{package.get('validation', {}).get('status', 'unknown')}`",
            "- Every citation retains exact corpus identifiers, retrieval rank, source title, and TamilVU URLs.",
            "- These citation IDs can later be attached to one or more answer segments without changing source traceability.",
        ]
    )
    return "\n".join(lines) + "\n"

