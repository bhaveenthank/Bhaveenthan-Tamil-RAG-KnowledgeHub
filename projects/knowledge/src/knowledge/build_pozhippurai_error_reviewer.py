from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_LINKS = Path("data/processed/thevaram_pozhippurai_links/v4/paadal_pozhippurai_links_v4_full.jsonl")
DEFAULT_TABLE_ROOT = Path("data/processed/thevaram_normalized")
DEFAULT_OUTPUT_DIR = Path("data/processed/thevaram_pozhippurai_links/v4/error_review")

NUMERIC_ONLY_RE = re.compile(r"^[0-9०-९௦-௯.,;:()\[\]\-\s]+$")
GENERIC_TOKENS = (
    "கோயில்",
    "திருக்கோயில்",
    "தலம்",
    "பதி",
    "ஊர்",
    "இடம்",
    "மாடம்",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read_tables(table_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    paadal_by_id = {str(row.get("paadal_id", "")): row for row in read_jsonl(table_root / "paadalgal.jsonl")}
    commentary_by_id = {
        str(row.get("commentary_id", "")): row for row in read_jsonl(table_root / "commentaries.jsonl")
    }
    return paadal_by_id, commentary_by_id


def is_numeric_only_source(text: str) -> bool:
    return bool(NUMERIC_ONLY_RE.fullmatch((text or "").strip()))


def matched_generic_tokens(source_text: str, target_text: str) -> list[str]:
    combined = f"{source_text or ''} {target_text or ''}"
    return [token for token in GENERIC_TOKENS if token in combined]


def classify_issue(row: dict[str, Any]) -> tuple[str, list[str]]:
    source_text = str(row.get("source_text", "") or "")
    target_text = str(row.get("target_text", "") or "")
    generic_tokens = matched_generic_tokens(source_text, target_text)
    is_generic_low_confidence = bool(generic_tokens) and str(row.get("confidence", "")) in {"low", "medium"}
    is_numeric = is_numeric_only_source(source_text)
    if is_numeric and is_generic_low_confidence:
        return "numeric_and_generic_token", generic_tokens
    if is_numeric:
        return "numeric_only_source", []
    if is_generic_low_confidence:
        return "generic_token_low_confidence", generic_tokens
    return "", []


def normalize_int(value: Any) -> int | None:
    try:
        if value in {"", None, "None"}:
            return None
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def highlight_span(text: str, start: int | None, end: int | None) -> str:
    if start is None or end is None or start < 0 or end < start or end > len(text or ""):
        return html.escape(text or "")
    return (
        html.escape(text[:start])
        + "<mark>"
        + html.escape(text[start:end])
        + "</mark>"
        + html.escape(text[end:])
    )


def enrich_error_rows(
    rows: list[dict[str, Any]],
    paadal_by_id: dict[str, dict[str, Any]],
    commentary_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        issue_type, generic_tokens = classify_issue(row)
        if not issue_type:
            continue
        paadal = paadal_by_id.get(str(row.get("paadal_id", "")), {})
        commentary = commentary_by_id.get(str(row.get("commentary_id", "")), {})
        paadal_text = str(paadal.get("paadal_text", ""))
        pozhppurai = str(commentary.get("pozhppurai", ""))
        source_start = normalize_int(row.get("source_start_char"))
        source_end = normalize_int(row.get("source_end_char"))
        target_start = normalize_int(row.get("target_start_char"))
        target_end = normalize_int(row.get("target_end_char"))
        enriched.append(
            {
                "issue_type": issue_type,
                "matched_generic_tokens": "|".join(generic_tokens),
                "link_id": row.get("link_id", ""),
                "paadal_id": row.get("paadal_id", ""),
                "commentary_id": row.get("commentary_id", ""),
                "thirumurai_no": row.get("thirumurai_no", ""),
                "global_song_no": paadal.get("global_song_no", ""),
                "local_song_no": paadal.get("local_song_no", ""),
                "confidence": row.get("confidence", ""),
                "score": row.get("score", ""),
                "relationship_type": row.get("relationship_type", ""),
                "source_start_char": source_start,
                "source_end_char": source_end,
                "target_start_char": target_start,
                "target_end_char": target_end,
                "source_text": row.get("source_text", ""),
                "target_text": row.get("target_text", ""),
                "diagnostic_note": row.get("diagnostic_note", ""),
                "reviewer_note": row.get("reviewer_note", ""),
                "source_url": paadal.get("source_url", ""),
                "commentary_url": paadal.get("commentary_url", ""),
                "paadal_text": paadal_text,
                "pozhppurai": pozhppurai,
                "paadal_text_highlighted": highlight_span(paadal_text, source_start, source_end),
                "pozhppurai_highlighted": highlight_span(pozhppurai, target_start, target_end),
            }
        )
    return enriched


def sample_rows(rows: list[dict[str, Any]], per_issue: int) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["issue_type"]), []).append(row)
    for issue_type in sorted(grouped):
        issue_rows = sorted(
            grouped[issue_type],
            key=lambda row: (
                str(row.get("confidence", "")),
                int(row.get("thirumurai_no") or 0),
                int(row.get("global_song_no") or 0),
                str(row.get("link_id", "")),
            ),
        )
        samples.extend(issue_rows[:per_issue])
    return samples


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "issue_type",
        "matched_generic_tokens",
        "confidence",
        "score",
        "relationship_type",
        "thirumurai_no",
        "global_song_no",
        "local_song_no",
        "paadal_id",
        "link_id",
        "source_text",
        "target_text",
        "diagnostic_note",
        "source_url",
        "commentary_url",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_report(rows: list[dict[str, Any]], sample_path: Path, viewer_path: Path) -> str:
    issue_counts = Counter(str(row["issue_type"]) for row in rows)
    confidence_counts = Counter(str(row["confidence"]) for row in rows)
    thirumurai_counts = Counter(str(row["thirumurai_no"]) for row in rows)
    token_counts: Counter[str] = Counter()
    diagnostic_counts = Counter(str(row["diagnostic_note"]) for row in rows)
    numeric_current = sum(
        1 for row in rows if str(row.get("issue_type", "")).startswith("numeric")
    )
    historical_numeric_sample = sample_path.with_name("observed_numeric_error_samples_from_previous_export.csv")
    for row in rows:
        for token in str(row.get("matched_generic_tokens", "")).split("|"):
            if token:
                token_counts[token] += 1

    def table(counter: Counter[str], first_header: str, limit: int | None = None) -> str:
        items = counter.most_common(limit)
        lines = [f"| {first_header} | count |", "| --- | ---: |"]
        lines.extend(f"| {key or '(empty)'} | {value} |" for key, value in items)
        return "\n".join(lines)

    return f"""# Paadal-Pozhippurai Numeric and Generic-Token Review

This report isolates the first common low-confidence family the user flagged: numeric text being treated as paadal source text, plus low/medium-confidence links where broad location/temple words such as `கோயில்` appear to be carrying too much of the match.

## Artifact Paths

- HTML reviewer: `{viewer_path}`
- Sample CSV: `{sample_path}`
- Historical numeric examples, when generated from the previous supervisor export: `{historical_numeric_sample}`

## Current Numeric Status

Current rebuilt v4 numeric-only source rows in this focused reviewer: `{numeric_current}`.

## Counts

{table(issue_counts, "issue_type")}

## Confidence

{table(confidence_counts, "confidence")}

## Thirumurai Spread

{table(thirumurai_counts, "thirumurai_no")}

## Generic Tokens

{table(token_counts, "token")}

## Top Diagnostic Notes

{table(diagnostic_counts, "diagnostic_note", limit=10)}

## Likely Causes

1. Numeric-only source spans are preserved verse or paadal numbers, not literary text. In this run they are concentrated in Thirumurai 3, where normalized `paadal_text` records can end with standalone lines like `1`, `2`, or `11`.
2. The v4 linker then splits/considers those numeric lines as candidate paadal phrases. Because a number has no real lexical or entity evidence, the selected pozhippurai target is usually supported only by poem/commentary order.
3. Generic temple/location words such as `கோயில்`, `பதி`, `இடம்`, `ஊர்`, and `தலம்` occur in many paadal and pozhippurai spans. They are valid words, but by themselves they are weak anchors and often produce ambiguous or low-confidence matches.

## Fix Direction

1. Filter standalone numbering lines from paadal source segmentation before link generation while preserving the original raw snapshot and source order metadata.
2. Keep the number as metadata only when it agrees with `local_song_no`, `verse_index_in_thogupu`, or a known printed verse index.
3. Downweight generic location/temple tokens unless they are part of a more specific phrase such as a named thalam, named temple, deity phrase, or a longer shared expression.
"""


def render_html(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="ta">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Paadal-Pozhippurai Error Reviewer</title>
  <style>
    :root {{
      --ink: #202124;
      --muted: #5f6368;
      --line: #d7dce2;
      --panel: #fff;
      --bg: #f6f7f9;
      --accent: #0b6bcb;
      --soft: #e8f1fd;
      --mark: #fff0a8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Noto Sans Tamil", "Noto Sans", sans-serif;
      line-height: 1.55;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 5;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 12px 16px;
    }}
    h1 {{ margin: 0 0 10px; font-size: 20px; letter-spacing: 0; }}
    .toolbar {{
      display: grid;
      grid-template-columns: minmax(220px, 1.2fr) repeat(4, minmax(130px, .5fr)) auto auto;
      gap: 8px;
      align-items: center;
    }}
    input, select, button, textarea {{
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      font: inherit;
    }}
    input, select {{ padding: 6px 10px; }}
    button {{
      padding: 6px 12px;
      cursor: pointer;
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      white-space: nowrap;
    }}
    button.secondary {{ background: #fff; color: var(--accent); }}
    main {{
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      gap: 14px;
      max-width: 1720px;
      margin: 0 auto;
      padding: 14px;
    }}
    .list, .detail {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 0;
    }}
    .list {{ height: calc(100vh - 102px); overflow: auto; }}
    .item {{
      display: block;
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--line);
      border-radius: 0;
      background: white;
      color: var(--ink);
      text-align: left;
      padding: 10px 12px;
    }}
    .item.active {{ background: var(--soft); }}
    .item strong {{ display: block; font-size: 14px; }}
    .item span {{ display: block; color: var(--muted); font-size: 12px; }}
    .detail {{ padding: 16px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }}
    .tag {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 3px 9px;
      background: #fff;
      font-size: 13px;
    }}
    section {{ border-top: 1px solid var(--line); margin-top: 12px; padding-top: 12px; }}
    h2 {{ margin: 0 0 8px; font-size: 15px; letter-spacing: 0; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .box {{ border: 1px solid var(--line); border-radius: 6px; padding: 10px; background: #f8fafc; }}
    .text {{ white-space: pre-wrap; overflow-wrap: anywhere; font-size: 18px; line-height: 1.75; }}
    mark {{ background: var(--mark); padding: 1px 2px; border-radius: 3px; }}
    textarea {{ width: 100%; min-height: 76px; padding: 8px 10px; resize: vertical; }}
    .review-controls {{ display: grid; grid-template-columns: repeat(3, minmax(120px, 1fr)); gap: 8px; }}
    .review-controls textarea {{ grid-column: 1 / -1; }}
    .links a {{ color: var(--accent); margin-right: 12px; }}
    .empty {{ padding: 18px; color: var(--muted); }}
    @media (max-width: 980px) {{
      .toolbar, main, .grid, .review-controls {{ grid-template-columns: 1fr; }}
      .list {{ height: 260px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Paadal-Pozhippurai Numeric / Generic Token Reviewer</h1>
    <div class="toolbar">
      <input id="search" type="search" placeholder="Search text, id, note">
      <select id="issue"><option value="">All issue types</option></select>
      <select id="confidence"><option value="">All confidence</option></select>
      <select id="token"><option value="">All generic tokens</option></select>
      <select id="thirumurai"><option value="">All Thirumurai</option></select>
      <button class="secondary" id="prev">Previous</button>
      <button id="next">Next</button>
      <button id="export">Export CSV</button>
    </div>
  </header>
  <main>
    <aside class="list" id="list"></aside>
    <article class="detail" id="detail"></article>
  </main>
  <script>
    const rows = {payload};
    const state = {{ filtered: rows, index: 0 }};
    const saved = JSON.parse(localStorage.getItem("thevaram_ppl_error_review") || "{{}}");
    const decisions = ["", "NUMBERING_NO_LINK", "GENERIC_TOKEN_WEAK", "ACCEPT", "WRONG_TARGET", "NEEDS_SPLIT", "NO_LINK_POSSIBLE"];
    const confidenceChoices = ["", "high", "medium", "low", "no_link"];

    function byId(id) {{ return document.getElementById(id); }}
    function text(value) {{ return value === null || value === undefined ? "" : String(value); }}
    function unique(field) {{ return [...new Set(rows.map(row => text(row[field])).filter(Boolean))].sort(); }}
    function uniqueTokens() {{
      return [...new Set(rows.flatMap(row => text(row.matched_generic_tokens).split("|")).filter(Boolean))].sort();
    }}
    function fillSelect(id, values) {{
      const el = byId(id);
      for (const value of values) {{
        const opt = document.createElement("option");
        opt.value = value;
        opt.textContent = value;
        el.appendChild(opt);
      }}
    }}
    fillSelect("issue", unique("issue_type"));
    fillSelect("confidence", unique("confidence"));
    fillSelect("token", uniqueTokens());
    fillSelect("thirumurai", unique("thirumurai_no"));

    function escapeHtml(value) {{
      return text(value).replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[ch]));
    }}
    function rowReview(row) {{
      return saved[row.link_id] || {{ decision: "", updated_confidence: row.confidence || "", note: "" }};
    }}
    function applyFilters() {{
      const q = byId("search").value.trim().toLowerCase();
      const issue = byId("issue").value;
      const confidence = byId("confidence").value;
      const token = byId("token").value;
      const thirumurai = byId("thirumurai").value;
      state.filtered = rows.filter(row => {{
        const hay = [row.link_id, row.paadal_id, row.source_text, row.target_text, row.paadal_text, row.pozhppurai, row.diagnostic_note].join(" ").toLowerCase();
        return (!q || hay.includes(q)) &&
          (!issue || row.issue_type === issue) &&
          (!confidence || row.confidence === confidence) &&
          (!token || text(row.matched_generic_tokens).split("|").includes(token)) &&
          (!thirumurai || text(row.thirumurai_no) === thirumurai);
      }});
      state.index = Math.min(state.index, Math.max(0, state.filtered.length - 1));
      renderList();
      renderDetail();
    }}
    function renderList() {{
      const list = byId("list");
      list.innerHTML = "";
      if (!state.filtered.length) {{
        list.innerHTML = '<div class="empty">No rows match the filters.</div>';
        return;
      }}
      state.filtered.forEach((row, index) => {{
        const item = document.createElement("button");
        item.className = "item" + (index === state.index ? " active" : "");
        item.innerHTML = `<strong>${{index + 1}}. ${{escapeHtml(row.source_text || row.paadal_id)}}</strong><span>${{escapeHtml(row.issue_type)}} · ${{escapeHtml(row.confidence)}} · T${{escapeHtml(row.thirumurai_no)}} · song ${{escapeHtml(row.global_song_no)}}</span>`;
        item.onclick = () => {{ state.index = index; renderList(); renderDetail(); }};
        list.appendChild(item);
      }});
    }}
    function renderDetail() {{
      const detail = byId("detail");
      const row = state.filtered[state.index];
      if (!row) {{
        detail.innerHTML = '<div class="empty">Choose a row to review.</div>';
        return;
      }}
      const review = rowReview(row);
      detail.innerHTML = `
        <div class="meta">
          <span class="tag">Row ${{state.index + 1}} / ${{state.filtered.length}}</span>
          <span class="tag">${{escapeHtml(row.issue_type)}}</span>
          <span class="tag">T${{escapeHtml(row.thirumurai_no)}}</span>
          <span class="tag">song ${{escapeHtml(row.global_song_no)}}</span>
          <span class="tag">${{escapeHtml(row.confidence)}}</span>
          <span class="tag">score ${{escapeHtml(row.score)}}</span>
          <span class="tag">${{escapeHtml(row.matched_generic_tokens || "no generic token")}}</span>
        </div>
        <section>
          <h2>Candidate Span</h2>
          <div class="grid">
            <div class="box"><strong>Paadal source span</strong><div class="text">${{escapeHtml(row.source_text)}}</div></div>
            <div class="box"><strong>Pozhippurai target span</strong><div class="text">${{escapeHtml(row.target_text)}}</div></div>
          </div>
        </section>
        <section>
          <h2>Review Decision</h2>
          <div class="review-controls">
            <select id="decision">${{decisions.map(v => `<option value="${{v}}" ${{review.decision === v ? "selected" : ""}}>${{v || "Decision..."}}</option>`).join("")}}</select>
            <select id="updatedConfidence">${{confidenceChoices.map(v => `<option value="${{v}}" ${{review.updated_confidence === v ? "selected" : ""}}>${{v || "Confidence..."}}</option>`).join("")}}</select>
            <button id="saveReview">Save Row</button>
            <textarea id="note" placeholder="Correct source/target or note">${{escapeHtml(review.note)}}</textarea>
          </div>
        </section>
        <section>
          <h2>Full Paadal</h2>
          <div class="text">${{row.paadal_text_highlighted || escapeHtml(row.paadal_text)}}</div>
        </section>
        <section>
          <h2>Full Pozhippurai</h2>
          <div class="text">${{row.pozhppurai_highlighted || escapeHtml(row.pozhppurai || "(empty pozhppurai)")}}</div>
        </section>
        <section>
          <h2>Diagnostics</h2>
          <div class="text">${{escapeHtml(row.diagnostic_note || "")}}</div>
          <div class="links">
            ${{row.source_url ? `<a href="${{escapeHtml(row.source_url)}}" target="_blank">TamilVU paadal</a>` : ""}}
            ${{row.commentary_url ? `<a href="${{escapeHtml(row.commentary_url)}}" target="_blank">TamilVU commentary</a>` : ""}}
            <span>${{escapeHtml(row.paadal_id)}} · ${{escapeHtml(row.link_id)}}</span>
          </div>
        </section>`;
      byId("saveReview").onclick = () => {{
        saved[row.link_id] = {{
          decision: byId("decision").value,
          updated_confidence: byId("updatedConfidence").value,
          note: byId("note").value
        }};
        localStorage.setItem("thevaram_ppl_error_review", JSON.stringify(saved));
        renderList();
      }};
    }}
    function exportCsv() {{
      const fields = ["link_id","paadal_id","issue_type","matched_generic_tokens","thirumurai_no","global_song_no","source_text","target_text","confidence","manual_decision","updated_confidence","reviewer_note"];
      const lines = [fields.join(",")];
      for (const row of rows) {{
        const review = rowReview(row);
        const values = [row.link_id,row.paadal_id,row.issue_type,row.matched_generic_tokens,row.thirumurai_no,row.global_song_no,row.source_text,row.target_text,row.confidence,review.decision,review.updated_confidence,review.note]
          .map(v => `"${{text(v).replace(/"/g, '""')}}"`);
        lines.push(values.join(","));
      }}
      const blob = new Blob([lines.join("\\n")], {{type: "text/csv;charset=utf-8"}});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "paadal_pozhippurai_numeric_generic_review_export.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    for (const id of ["search","issue","confidence","token","thirumurai"]) {{
      byId(id).addEventListener("input", applyFilters);
    }}
    byId("prev").onclick = () => {{ state.index = Math.max(0, state.index - 1); renderList(); renderDetail(); }};
    byId("next").onclick = () => {{ state.index = Math.min(state.filtered.length - 1, state.index + 1); renderList(); renderDetail(); }};
    byId("export").onclick = exportCsv;
    document.addEventListener("keydown", event => {{
      if (event.target && ["INPUT","TEXTAREA","SELECT"].includes(event.target.tagName)) return;
      if (event.key === "ArrowRight") byId("next").click();
      if (event.key === "ArrowLeft") byId("prev").click();
    }});
    applyFilters();
  </script>
</body>
</html>
"""


def build_error_reviewer(
    *,
    links_path: Path = DEFAULT_LINKS,
    table_root: Path = DEFAULT_TABLE_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    sample_per_issue: int = 12,
) -> dict[str, Any]:
    paadal_by_id, commentary_by_id = read_tables(table_root)
    rows = enrich_error_rows(read_jsonl(links_path), paadal_by_id, commentary_by_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    viewer_path = output_dir / "paadal_pozhippurai_numeric_generic_error_reviewer.html"
    sample_path = output_dir / "numeric_generic_error_samples.csv"
    report_path = output_dir / "numeric_generic_error_report.md"
    write_csv(sample_path, sample_rows(rows, sample_per_issue))
    viewer_path.write_text(render_html(rows), encoding="utf-8")
    report_path.write_text(render_report(rows, sample_path, viewer_path), encoding="utf-8")
    return {
        "links_path": str(links_path),
        "table_root": str(table_root),
        "output_dir": str(output_dir),
        "viewer_path": str(viewer_path),
        "sample_path": str(sample_path),
        "report_path": str(report_path),
        "rows": len(rows),
        "issue_counts": dict(sorted(Counter(str(row["issue_type"]) for row in rows).items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a focused reviewer for numeric-only and generic-token paadal-pozhppurai link errors."
    )
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS)
    parser.add_argument("--table-root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sample-per-issue", type=int, default=12)
    args = parser.parse_args(argv)
    summary = build_error_reviewer(
        links_path=args.links,
        table_root=args.table_root,
        output_dir=args.output_dir,
        sample_per_issue=args.sample_per_issue,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
