"""Build corpus/05_scholarship_policy.pdf from corpus/src/05_scholarship_policy.md.

The PDF is a first-class corpus document: the ingester reads the PDF (via pypdf), not the
markdown source. Keeping the markdown source in the repo makes the PDF reproducible.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "corpus" / "src" / "05_scholarship_policy.md"
OUT = ROOT / "corpus" / "05_scholarship_policy.pdf"


def build(src: Path = SRC, out: Path = OUT) -> Path:
    styles = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=styles["Title"], fontSize=18, spaceAfter=6)
    meta = ParagraphStyle("M", parent=styles["Normal"], fontSize=9, textColor="#555555", spaceAfter=2)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=14, spaceBefore=14, spaceAfter=6)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11.5, spaceBefore=10, spaceAfter=3)
    body = ParagraphStyle("B", parent=styles["Normal"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6)

    story = []
    for raw in src.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line:
            continue
        esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if line.startswith("# "):
            story.append(Paragraph(esc[2:], title))
        elif line.startswith("## "):
            story.append(Paragraph(esc[3:], h1))
        elif line.startswith("### "):
            story.append(Paragraph(esc[4:], h2))
        elif re.match(r"^(Shivalik Institute|Document code)", line):
            story.append(Paragraph(esc, meta))
        else:
            story.append(Paragraph(esc, body))
    story.append(Spacer(1, 0.5 * cm))

    doc = SimpleDocTemplate(
        str(out), pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title="Scholarship and Fee Concession Policy", author="Shivalik Institute of Technology, Indore",
    )
    doc.build(story)
    return out


if __name__ == "__main__":
    path = build()
    print(f"wrote {path} ({path.stat().st_size} bytes)")
    sys.exit(0)
