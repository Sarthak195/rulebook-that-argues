"""Parse the corpus into section-level chunks with stable ids like "AR §4.3".

Two parsers share one line-walker:
  * markdown files use ``## N. Title`` / ``### N.M Title`` headings
  * the PDF is read with pypdf and headings are recognised as bare ``N. Title`` / ``N.M Title`` lines

A chunk is one numbered sub-section. Regulations are written that way on purpose, so a
sub-section is the natural citation unit: small enough to quote, large enough to be self-contained.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

DOC_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")
DOC_CODE_RE = re.compile(r"Document code:\s*([A-Z]{2,4})")

MD_H2 = re.compile(r"^##\s+(\d+)\.?\s+(.+?)\s*$")
MD_H3 = re.compile(r"^###\s+(\d+\.\d+)\s+(.+?)\s*$")
PDF_H2 = re.compile(r"^(\d+)\.\s+([A-Z][^.]{2,80})$")
PDF_H3 = re.compile(r"^(\d+\.\d+)\s+([A-Z].{2,90})$")


@dataclass
class Chunk:
    id: str            # "AR §4.3"
    doc_code: str      # "AR"
    doc_title: str     # "Academic Regulations for the B.Tech. Programme (2026-27)"
    section: str       # "4.3"
    title: str         # "Condonation of Shortage of Attendance"
    parent_title: str  # "Attendance"
    text: str          # body text of the sub-section
    source: str        # file name
    format: str        # markdown | table | pdf

    @property
    def embed_text(self) -> str:
        return f"{self.doc_title} | {self.parent_title} | {self.section} {self.title}\n{self.text}"

    @property
    def label(self) -> str:
        return f"{self.parent_title} > {self.title}"


def _walk(lines: list[str], h2: re.Pattern, h3: re.Pattern, *, source: str, fmt: str) -> list[Chunk]:
    doc_title, doc_code = "", ""
    parent_title = ""
    chunks: list[Chunk] = []
    cur: dict | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal cur, buf
        if cur is not None:
            body = "\n".join(buf).strip()
            body = re.sub(r"\n{3,}", "\n\n", body)
            is_table = any(l.lstrip().startswith("|") for l in body.splitlines())
            chunks.append(Chunk(
                id=f"{doc_code} §{cur['section']}", doc_code=doc_code, doc_title=doc_title,
                section=cur["section"], title=cur["title"], parent_title=parent_title,
                text=body, source=source, format="table" if is_table else fmt,
            ))
        cur, buf = None, []

    for raw in lines:
        line = raw.rstrip()
        if not doc_title and (m := DOC_TITLE_RE.match(line)):
            doc_title = m.group(1)
            continue
        if not doc_code and (m := DOC_CODE_RE.search(line)):
            doc_code = m.group(1)
            continue
        if m := h3.match(line):
            flush()
            cur = {"section": m.group(1), "title": m.group(2).strip()}
            continue
        if m := h2.match(line):
            flush()
            parent_title = m.group(2).strip()
            continue
        if cur is not None:
            buf.append(line)
    flush()
    if not doc_code:
        raise ValueError(f"{source}: no 'Document code:' line found")
    return chunks


def parse_markdown(path: Path) -> list[Chunk]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return _walk(lines, MD_H2, MD_H3, source=path.name, fmt="markdown")


def parse_pdf(path: Path) -> list[Chunk]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    lines = [l.strip() for l in text.splitlines()]
    # pypdf gives us the title as a bare first line; mark it so the walker finds it.
    if lines and not lines[0].startswith("#"):
        lines[0] = "# " + lines[0]
    # Body lines inside a sub-section were wrapped by the PDF layout; join them back.
    joined: list[str] = []
    for l in lines:
        if not l:
            continue
        if PDF_H2.match(l) or PDF_H3.match(l) or l.startswith("#") or DOC_CODE_RE.search(l):
            joined.append(l)
        elif joined and not (PDF_H2.match(joined[-1]) or PDF_H3.match(joined[-1]) or joined[-1].startswith("#") or DOC_CODE_RE.search(joined[-1])):
            joined[-1] = joined[-1] + " " + l
        else:
            joined.append(l)
    return _walk(joined, PDF_H2, PDF_H3, source=path.name, fmt="pdf")


def load_corpus(corpus_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.iterdir()):
        if path.is_dir() or path.name.upper() in {"README.MD", "CONTRADICTIONS.MD"}:
            continue
        if path.suffix.lower() == ".md":
            chunks.extend(parse_markdown(path))
        elif path.suffix.lower() == ".pdf":
            chunks.extend(parse_pdf(path))
    ids = [c.id for c in chunks]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"duplicate section ids: {sorted(dupes)}")
    return chunks


def dump(chunks: list[Chunk], path: Path) -> None:
    path.write_text(json.dumps([asdict(c) for c in chunks], ensure_ascii=False, indent=1), encoding="utf-8")


def load(path: Path) -> list[Chunk]:
    return [Chunk(**d) for d in json.loads(path.read_text(encoding="utf-8"))]
