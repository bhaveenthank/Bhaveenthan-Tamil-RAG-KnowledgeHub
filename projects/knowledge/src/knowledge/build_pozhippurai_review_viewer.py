from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any

from knowledge.link_thevaram_pozhippurai_v3 import read_jsonl

DEFAULT_REVIEW_PACK = Path("data/processed/thevaram_pozhippurai_links/v3/paadal_pozhippurai_links_v3_manual_review_pack.csv")
DEFAULT_TABLE_ROOT = Path("data/processed/thevaram_normalized")
DEFAULT_OUTPUT = Path("data/processed/thevaram_pozhippurai_links/v3/review_viewer/paadal_pozhippurai_v3_review_viewer.html")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_int(value: Any) -> int | None:
    try:
        if value in {"", None, "None"}:
            return None
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def highlight_span(text: str, start: int | None, end: int | None) -> str:
    escaped = html.escape(text or "")
    if start is None or end is None or start < 0 or end < start or end > len(text or ""):
        return escaped
    before = html.escape(text[:start])
    middle = html.escape(text[start:end])
    after = html.escape(text[end:])
    return f'{before}<mark>{middle}</mark>{after}'


def enrich_rows(review_rows: list[dict[str, str]], table_root: Path) -> list[dict[str, Any]]:
    paadal_by_id = {
        str(row.get("paadal_id", "")): row
        for row in read_jsonl(table_root / "paadalgal.jsonl")
    }
    commentary_by_id = {
        str(row.get("commentary_id", "")): row
        for row in read_jsonl(table_root / "commentaries.jsonl")
    }
    enriched: list[dict[str, Any]] = []
    for index, row in enumerate(review_rows, start=1):
        paadal = paadal_by_id.get(str(row.get("paadal_id", "")), {})
        commentary = commentary_by_id.get(str(row.get("commentary_id", "")), {})
        paadal_text = str(paadal.get("paadal_text", ""))
        pozhppurai = str(commentary.get("pozhppurai", ""))
        kurippurai = str(commentary.get("kurippurai", ""))
        source_start = normalize_int(row.get("source_start_char"))
        source_end = normalize_int(row.get("source_end_char"))
        target_start = normalize_int(row.get("target_start_char"))
        target_end = normalize_int(row.get("target_end_char"))
        target_field = row.get("target_field", "pozhppurai") or "pozhppurai"
        enriched.append(
            {
                "row_no": index,
                "link_id": row.get("link_id", ""),
                "paadal_id": row.get("paadal_id", ""),
                "commentary_id": row.get("commentary_id", ""),
                "thirumurai_no": row.get("thirumurai_no", ""),
                "pathigam_id": row.get("pathigam_id", ""),
                "source_text": row.get("source_text", ""),
                "target_text": row.get("target_text", ""),
                "target_field": target_field,
                "relationship_type": row.get("relationship_type", ""),
                "confidence": row.get("confidence", ""),
                "score": row.get("score", ""),
                "review_reason": row.get("review_reason", ""),
                "diagnostic_note": row.get("diagnostic_note", ""),
                "reviewer_note": row.get("reviewer_note", ""),
                "split_parent_id": row.get("split_parent_id", ""),
                "manual_review_required": row.get("manual_review_required", ""),
                "source_start_char": source_start,
                "source_end_char": source_end,
                "target_start_char": target_start,
                "target_end_char": target_end,
                "paadal_text": paadal_text,
                "pozhppurai": pozhppurai,
                "kurippurai": kurippurai,
                "source_url": paadal.get("source_url", ""),
                "commentary_url": paadal.get("commentary_url", ""),
                "paadal_text_highlighted": highlight_span(paadal_text, source_start, source_end),
                "pozhppurai_highlighted": highlight_span(
                    pozhppurai,
                    target_start if target_field == "pozhppurai" else None,
                    target_end if target_field == "pozhppurai" else None,
                ),
                "kurippurai_highlighted": highlight_span(
                    kurippurai,
                    target_start if target_field == "kurippurai" else None,
                    target_end if target_field == "kurippurai" else None,
                ),
            }
        )
    return enriched


def render_html(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="ta">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Thevaram Paadal-Pozhippurai Review</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #202124;
      --muted: #5f6368;
      --line: #d7dce2;
      --panel: #ffffff;
      --bg: #f6f7f9;
      --accent: #0b6bcb;
      --accent-soft: #e8f1fd;
      --mark: #fff0a8;
      --danger: #a53030;
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
      z-index: 10;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 12px 18px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 20px;
      font-weight: 700;
      letter-spacing: 0;
    }}
    .toolbar {{
      display: grid;
      grid-template-columns: minmax(180px, 1.2fr) repeat(4, minmax(120px, .6fr)) auto auto;
      gap: 8px;
      align-items: center;
    }}
    input, select, button, textarea {{
      font: inherit;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
    }}
    input, select {{ min-height: 38px; padding: 6px 10px; }}
    button {{
      min-height: 38px;
      padding: 6px 12px;
      cursor: pointer;
      background: var(--accent);
      border-color: var(--accent);
      color: white;
      white-space: nowrap;
    }}
    button.secondary {{
      background: white;
      color: var(--accent);
    }}
    main {{
      display: grid;
      grid-template-columns: 330px 1fr;
      gap: 14px;
      padding: 14px;
      max-width: 1680px;
      margin: 0 auto;
    }}
    .list, .detail {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-width: 0;
    }}
    .list {{
      height: calc(100vh - 102px);
      overflow: auto;
    }}
    .item {{
      display: block;
      width: 100%;
      border: 0;
      border-bottom: 1px solid var(--line);
      background: white;
      color: var(--ink);
      text-align: left;
      padding: 10px 12px;
      border-radius: 0;
    }}
    .item.active {{ background: var(--accent-soft); }}
    .item strong {{ display: block; font-size: 14px; }}
    .item span {{ display: block; color: var(--muted); font-size: 12px; }}
    .detail {{ padding: 16px; }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }}
    .tag {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 3px 9px;
      font-size: 13px;
      background: #fff;
    }}
    .tag.low, .tag.no_link {{ color: var(--danger); border-color: #e2aaaa; }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      align-items: start;
    }}
    section {{
      border-top: 1px solid var(--line);
      padding-top: 12px;
      margin-top: 12px;
    }}
    h2 {{
      margin: 0 0 8px;
      font-size: 15px;
      letter-spacing: 0;
    }}
    .text {{
      white-space: pre-wrap;
      font-size: 18px;
      line-height: 1.75;
      overflow-wrap: anywhere;
    }}
    .target {{
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
    }}
    mark {{
      background: var(--mark);
      padding: 1px 2px;
      border-radius: 3px;
    }}
    .review-controls {{
      display: grid;
      grid-template-columns: repeat(3, minmax(120px, 1fr));
      gap: 8px;
      margin-top: 12px;
    }}
    .review-controls textarea {{
      grid-column: 1 / -1;
      min-height: 72px;
      padding: 8px 10px;
      resize: vertical;
    }}
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
    <h1>Thevaram Paadal-Pozhippurai Review</h1>
    <div class="toolbar">
      <input id="search" type="search" placeholder="Search Tamil text, paadal id, note">
      <select id="confidence"><option value="">All confidence</option></select>
      <select id="relationship"><option value="">All relations</option></select>
      <select id="thirumurai"><option value="">All Thirumurai</option></select>
      <select id="reason"><option value="">All review reasons</option></select>
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
    const decisions = ["", "ACCEPT", "WRONG_TARGET", "PARTIAL_MATCH", "WRONG_RELATION_TYPE", "NEEDS_SPLIT", "NO_LINK_POSSIBLE"];
    const confidenceChoices = ["", "high", "medium", "low", "no_link"];
    const state = {{ filtered: rows, index: 0 }};
    const saved = JSON.parse(localStorage.getItem("thevaram_ppl_v3_review") || "{{}}");

    function byId(id) {{ return document.getElementById(id); }}
    function text(v) {{ return (v === null || v === undefined) ? "" : String(v); }}
    function unique(field) {{ return [...new Set(rows.map(r => text(r[field])).filter(Boolean))].sort(); }}
    function fillSelect(id, values) {{
      const el = byId(id);
      for (const value of values) {{
        const opt = document.createElement("option");
        opt.value = value;
        opt.textContent = value;
        el.appendChild(opt);
      }}
    }}
    fillSelect("confidence", unique("confidence"));
    fillSelect("relationship", unique("relationship_type"));
    fillSelect("thirumurai", unique("thirumurai_no"));
    fillSelect("reason", unique("review_reason"));

    function rowDecision(row) {{
      return saved[row.link_id] || {{ decision: "", updated_confidence: row.confidence || "", note: "" }};
    }}
    function applyFilters() {{
      const q = byId("search").value.trim().toLowerCase();
      const c = byId("confidence").value;
      const rel = byId("relationship").value;
      const th = byId("thirumurai").value;
      const reason = byId("reason").value;
      state.filtered = rows.filter(row => {{
        const hay = [row.paadal_id, row.commentary_id, row.source_text, row.target_text, row.paadal_text, row.pozhppurai, row.kurippurai, row.diagnostic_note, row.reviewer_note].join(" ").toLowerCase();
        return (!q || hay.includes(q)) &&
          (!c || row.confidence === c) &&
          (!rel || row.relationship_type === rel) &&
          (!th || text(row.thirumurai_no) === th) &&
          (!reason || row.review_reason === reason);
      }});
      state.index = Math.min(state.index, Math.max(0, state.filtered.length - 1));
      renderList();
      renderDetail();
    }}
    function renderList() {{
      const list = byId("list");
      list.innerHTML = "";
      if (!state.filtered.length) {{
        list.innerHTML = '<div class="empty">No rows match the current filters.</div>';
        return;
      }}
      state.filtered.forEach((row, idx) => {{
        const item = document.createElement("button");
        item.className = "item" + (idx === state.index ? " active" : "");
        item.innerHTML = `<strong>${{idx + 1}}. ${{row.source_text || row.paadal_id}}</strong><span>${{row.relationship_type}} · ${{row.confidence}} · T${{row.thirumurai_no}} · ${{row.review_reason || ""}}</span>`;
        item.onclick = () => {{ state.index = idx; renderList(); renderDetail(); }};
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
      const review = rowDecision(row);
      detail.innerHTML = `
        <div class="meta">
          <span class="tag">Row ${{state.index + 1}} / ${{state.filtered.length}}</span>
          <span class="tag">T${{row.thirumurai_no}}</span>
          <span class="tag ${{row.confidence}}">${{row.confidence}}</span>
          <span class="tag">${{row.relationship_type}}</span>
          <span class="tag">${{row.target_field || "pozhppurai"}}</span>
          <span class="tag">${{row.review_reason || "review"}}</span>
          <span class="tag">score ${{row.score}}</span>
        </div>
        <section>
          <h2>Candidate Link</h2>
          <div class="grid">
            <div class="target"><strong>Paadal span</strong><div class="text">${{escapeHtml(row.source_text)}}</div></div>
            <div class="target"><strong>Pozhippurai span</strong><div class="text">${{escapeHtml(row.target_text)}}</div></div>
          </div>
        </section>
        <section>
          <h2>Review</h2>
          <div class="review-controls">
            <select id="decisionSelect">${{decisions.map(v => `<option value="${{v}}" ${{review.decision === v ? "selected" : ""}}>${{v || "Decision..."}}</option>`).join("")}}</select>
            <select id="confidenceSelect">${{confidenceChoices.map(v => `<option value="${{v}}" ${{review.updated_confidence === v ? "selected" : ""}}>${{v || "Confidence..."}}</option>`).join("")}}</select>
            <button id="saveReview">Save Row</button>
            <textarea id="noteInput" placeholder="Your note or corrected target/source">${{escapeHtml(review.note || "")}}</textarea>
          </div>
        </section>
        <section>
          <h2>Full Paadal</h2>
          <div class="text">${{row.paadal_text_highlighted || escapeHtml(row.paadal_text)}}</div>
        </section>
        <section>
          <h2>Full Pozhippurai</h2>
          <div class="text">${{row.pozhppurai_highlighted || escapeHtml(row.pozhppurai)}}</div>
        </section>
        <section>
          <h2>Kurippurai</h2>
          <div class="text">${{row.kurippurai_highlighted || escapeHtml(row.kurippurai || "")}}</div>
        </section>
        <section>
          <h2>Diagnostics</h2>
          <div class="text">${{escapeHtml(row.diagnostic_note || "")}}</div>
          <div class="text">${{escapeHtml(row.reviewer_note || "")}}</div>
          <div class="links">
            ${{row.source_url ? `<a href="${{escapeAttr(row.source_url)}}" target="_blank">TamilVU paadal</a>` : ""}}
            ${{row.commentary_url ? `<a href="${{escapeAttr(row.commentary_url)}}" target="_blank">TamilVU commentary</a>` : ""}}
            <span>${{escapeHtml(row.paadal_id)}} · ${{escapeHtml(row.link_id)}}</span>
          </div>
        </section>`;
      byId("saveReview").onclick = () => saveCurrent(row);
    }}
    function saveCurrent(row) {{
      saved[row.link_id] = {{
        decision: byId("decisionSelect").value,
        updated_confidence: byId("confidenceSelect").value,
        note: byId("noteInput").value
      }};
      localStorage.setItem("thevaram_ppl_v3_review", JSON.stringify(saved));
      renderList();
    }}
    function escapeHtml(value) {{
      return text(value).replace(/[&<>"']/g, ch => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[ch]));
    }}
    function escapeAttr(value) {{ return escapeHtml(value); }}
    function exportCsv() {{
      const fields = ["link_id","paadal_id","commentary_id","thirumurai_no","source_text","target_text","relationship_type","confidence","review_reason","manual_decision","updated_confidence","reviewer_note"];
      const lines = [fields.join(",")];
      for (const row of rows) {{
        const review = rowDecision(row);
        const values = [row.link_id,row.paadal_id,row.commentary_id,row.thirumurai_no,row.source_text,row.target_text,row.relationship_type,row.confidence,row.review_reason,review.decision,review.updated_confidence,review.note]
          .map(v => `"${{text(v).replace(/"/g, '""')}}"`);
        lines.push(values.join(","));
      }}
      const blob = new Blob([lines.join("\\n")], {{type: "text/csv;charset=utf-8"}});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "paadal_pozhippurai_v3_browser_review_export.csv";
      a.click();
      URL.revokeObjectURL(url);
    }}
    for (const id of ["search","confidence","relationship","thirumurai","reason"]) {{
      byId(id).addEventListener("input", applyFilters);
    }}
    byId("prev").onclick = () => {{ state.index = Math.max(0, state.index - 1); renderList(); renderDetail(); }};
    byId("next").onclick = () => {{ state.index = Math.min(state.filtered.length - 1, state.index + 1); renderList(); renderDetail(); }};
    byId("export").onclick = exportCsv;
    document.addEventListener("keydown", ev => {{
      if (ev.target && ["INPUT","TEXTAREA","SELECT"].includes(ev.target.tagName)) return;
      if (ev.key === "ArrowRight") byId("next").click();
      if (ev.key === "ArrowLeft") byId("prev").click();
    }});
    applyFilters();
  </script>
</body>
</html>
"""


def build_viewer(
    *,
    review_pack: Path = DEFAULT_REVIEW_PACK,
    table_root: Path = DEFAULT_TABLE_ROOT,
    output: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    rows = enrich_rows(read_csv(review_pack), table_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(rows), encoding="utf-8")
    return {
        "review_pack": str(review_pack),
        "table_root": str(table_root),
        "output": str(output),
        "rows": len(rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local HTML viewer for Thevaram paadal-pozhppurai review.")
    parser.add_argument("--review-pack", type=Path, default=DEFAULT_REVIEW_PACK)
    parser.add_argument("--table-root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    print(json.dumps(build_viewer(review_pack=args.review_pack, table_root=args.table_root, output=args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
