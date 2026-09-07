"""Parse the corpus, embed every section, and write the index to ./index.

    python scripts/ingest.py

The API rebuilds the index automatically on startup if it is missing or stale, so this is
only needed to inspect the chunking or to force a rebuild after editing the corpus.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from app.retriever import build_index  # noqa: E402


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    r = build_index()
    chunks = r.chunks
    words = sum(len(c.text.split()) for c in chunks)
    print(f"\n{len(chunks)} sections, {words} words of regulation text")
    print("per document:", dict(Counter(c.doc_code for c in chunks)))
    print("per format:  ", dict(Counter(c.format for c in chunks)))
    longest = max(chunks, key=lambda c: len(c.text.split()))
    print(f"longest section: {longest.id} ({len(longest.text.split())} words)")


if __name__ == "__main__":
    main()
