from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/papers/thevaram_1_8_resource_paper_draft.md"
OUTPUT = ROOT / "output/pdf/thevaram_1_8_resource_paper_draft.pdf"


def clean_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    return text


def parse_table(lines):
    rows = []
    for line in lines:
        cells = [clean_inline(c.strip()) for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "Draft reading copy - Thevaram 1-8 resource paper")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="PaperTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            alignment=TA_CENTER,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=15,
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTextTight",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=12,
            alignment=TA_LEFT,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletTight",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=11.5,
            leftIndent=14,
            firstLineIndent=-8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.4,
            leading=8.6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHead",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=8.4,
            textColor=colors.white,
        )
    )

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.7 * inch,
    )

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = []
    i = 0
    title_done = False
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(clean_inline(line[2:]), styles["PaperTitle"]))
            title_done = True
            i += 1
            continue
        if line.startswith("## "):
            if title_done and "References" in line:
                story.append(PageBreak())
            story.append(Paragraph(clean_inline(line[3:]), styles["SectionHeading"]))
            i += 1
            continue
        if line.startswith("- "):
            story.append(Paragraph("- " + clean_inline(line[2:]), styles["BulletTight"]))
            i += 1
            continue
        if re.match(r"^\d+\. ", line):
            story.append(Paragraph(clean_inline(line), styles["BulletTight"]))
            i += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|\s*-", lines[i]):
                    table_lines.append(lines[i])
                i += 1
            data = parse_table(table_lines)
            if data:
                styled = []
                for r, row in enumerate(data):
                    style = styles["TableHead"] if r == 0 else styles["TableCell"]
                    styled.append([Paragraph(cell, style) for cell in row])
                available_width = 7.2 * inch
                col_width = available_width / max(len(styled[0]), 1)
                table = Table(styled, colWidths=[col_width] * len(styled[0]), repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24364b")),
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b8c0cc")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 3),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 8))
            continue
        story.append(Paragraph(clean_inline(line), styles["BodyTextTight"]))
        i += 1

    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


if __name__ == "__main__":
    build()

