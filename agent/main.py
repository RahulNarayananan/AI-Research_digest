"""
main.py — Orchestrates the full daily AI research digest workflow.

Steps:
1. Fetch the latest AI papers (arXiv → Semantic Scholar → Papers With Code).
2. Rank by composite impact score and pick the top paper.
3. Summarise with Ollama (local LLM).
4. Send (or preview) the HTML email digest.

Usage (run from the agent/ directory OR the project root):
    python agent/main.py              # send real email
    python agent/main.py --dry-run    # save HTML preview only
    python agent/main.py --test       # print top paper without emailing
    python agent/main.py --verbose    # extra debug output
"""

import sys
import os
import argparse

# ── Path fix ─────────────────────────────────────────────────
# Ensure agent/ is in sys.path so sibling modules can be imported directly
# regardless of the working directory the script is launched from.
_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _AGENT_DIR not in sys.path:
    sys.path.insert(0, _AGENT_DIR)

# Load .env from the project root (one level up from agent/)
from dotenv import load_dotenv
load_dotenv(os.path.join(_AGENT_DIR, "..", ".env"), override=True)

# ── Sibling module imports ────────────────────────────────────
import fetcher
import ranker
import summarizer
import mailer


# ─────────────────────────────────────────────────────────────

def run_once(dry_run: bool = False, verbose: bool = False) -> None:
    """Run the full fetch → rank → summarise → email pipeline once."""

    # 1️⃣  Fetch papers
    print("[1/4] Fetching latest AI papers...")
    papers = fetcher.fetch_all_papers()
    if not papers:
        print("[ERROR] No papers were fetched – check your internet connection.")
        return

    # 2️⃣  Rank and pick the best papers
    print(f"[2/4] Ranking {len(papers)} papers by impact...")
    top_3 = ranker.rank_papers(papers, top_n=3)

    digest_data = []

    # 3️⃣  Summarise each paper with Gemini
    print(f"\n[3/4] Generating summaries with Gemini API...")
    for idx, paper in enumerate(top_3):
        rank = idx + 1
        print(f"   [{rank}/3] Summarizing: {paper['title'][:60]}...")
        
        summary_raw = summarizer.summarize_paper(paper)
        if summary_raw:
            sections = summarizer.parse_summary(summary_raw)
        else:
            print(f"      [WARN] Summarization failed for Paper #{rank} – using fallback.")
            sections = summarizer.fallback_sections(paper)
        
        digest_data.append((paper, sections))

    # 4️⃣  Send (or preview) the email
    print("\n[4/4] Sending email digest...")
    success = mailer.send_email(digest_data, dry_run=dry_run)
    if not success:
        print("[ERROR] Email step failed. Check the error message above.")
    else:
        print("[DONE] ✅ Workflow complete.")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI Research Paper Daily Digest")
    p.add_argument("--dry-run", action="store_true",
                   help="Render the HTML email and save to email_preview.html, but do NOT send it")
    p.add_argument("--test",    action="store_true",
                   help="Same as --dry-run (alias for convenience)")
    p.add_argument("--verbose", action="store_true",
                   help="Print extra debugging information")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_once(dry_run=(args.dry_run or args.test), verbose=args.verbose)
