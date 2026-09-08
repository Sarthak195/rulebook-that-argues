"""End-to-end browser test with Playwright, and the source of the screenshots in docs/img.

    python scripts/ui_test.py                          # against http://127.0.0.1:8000
    python scripts/ui_test.py http://34.93.55.172      # against the deployed VM
    python scripts/ui_test.py --no-eval                # skip the 2-4 minute evaluation run

Checks, in a real Chromium: the three response types render with the right badge and the
cited passage is highlighted; the audit tab lists the planted contradictions; the evaluation tab
runs every question and the pass count equals the total. Exit code 1 on any failure.
Requires: pip install playwright && python -m playwright install chromium
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"

CASES = [
    ("answered", "What is the minimum attendance required to appear for the end-semester examination?", "AR §4.1"),
    ("not_covered", "What happens if I miss the end-semester exam because of a family wedding?", None),
    ("conflict", "My attendance is 58% because I was hospitalised for three weeks. Can the shortage be condoned?", "LM §2.2"),
]


def main() -> int:
    from playwright.sync_api import sync_playwright

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    base = (args[0] if args else "http://127.0.0.1:8000").rstrip("/")
    run_eval = "--no-eval" not in sys.argv
    IMG.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1000})

        for status, question, must_cite in CASES:
            page.goto(f"{base}/?q={quote(question)}")
            page.wait_for_selector("#answer-card:not([hidden])", timeout=120_000)
            badge = page.inner_text("#badge").strip().lower().replace(" ", "_")  # CSS uppercases it
            cited = [e.inner_text() for e in page.query_selector_all(".passage.cited .id")]
            ok = badge == status and (must_cite is None or must_cite in cited)
            print(f"{'ok ' if ok else 'BAD'} {status:<12} badge={badge:<12} cited={cited}")
            if not ok:
                failures.append(f"{status}: badge={badge} cited={cited}")
            page.screenshot(path=str(IMG / f"{status}.png"))

        page.goto(f"{base}/?tab=audit")
        # The list starts with a "Loading…" placeholder; the summary cards only appear after the fetch.
        page.wait_for_selector("#audit-summary .stat, #audit-list .error", timeout=60_000)
        pairs = page.inner_text("#audit-list")
        planted = [("AR §11.2", "SF §3.1"), ("FS §4.1", "SF §6.2"), ("AR §4.3", "LM §2.2")]
        found = sum(1 for a, b in planted if a in pairs and b in pairs)
        print(f"{'ok ' if found == 3 else 'BAD'} audit tab lists {found}/3 planted contradictions")
        if found != 3:
            failures.append(f"audit shows {found}/3")
        page.screenshot(path=str(IMG / "audit.png"))

        if run_eval:
            page.goto(f"{base}/?tab=eval")
            page.wait_for_selector("#run-eval", timeout=30_000)
            page.click("#run-eval")
            t0 = time.time()
            # The run is a server-side job: the button is disabled while it runs and re-enabled
            # when the server reports done, so wait for that transition rather than for rows.
            page.wait_for_function("() => document.querySelector('#run-eval').disabled", timeout=60_000)
            page.wait_for_function("() => !document.querySelector('#run-eval').disabled", timeout=900_000)
            page.wait_for_timeout(500)
            stats = page.inner_text("#stats").split("\n")[0]
            rows = page.query_selector_all("#eval-table tbody tr")
            passed = len(page.query_selector_all("#eval-table tbody tr.pass"))
            ok = rows and passed == len(rows)
            print(f"{'ok ' if ok else 'BAD'} evaluation tab: {passed}/{len(rows)} passed in {int(time.time() - t0)} s ({stats})")
            if not ok:
                failures.append(f"evaluation {passed}/{len(rows)}")
                for tr in page.query_selector_all("#eval-table tbody tr.fail"):
                    print("    FAIL", tr.inner_text().replace("\n", " | ")[:200])
            page.screenshot(path=str(IMG / "evaluation.png"))

        browser.close()

    print("\nall good" if not failures else "\nFAILURES:\n  " + "\n  ".join(failures))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
