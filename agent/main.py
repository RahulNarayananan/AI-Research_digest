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

    # 2️⃣  Rank and pick the best paper
    print(f"[2/4] Ranking {len(papers)} papers by impact...")
    top_papers = ranker.rank_papers(papers, top_n=1)
    top_paper  = top_papers[0]

    print(f"\n   📄 Top paper: {top_paper['title']}")
    if verbose:
        print(f"   Authors   : {', '.join(top_paper['authors'][:5])}")
        print(f"   Citations : {top_paper['citation_count']}")
        print(f"   Influence : {top_paper['influence_score']}")
        print(f"   GH Stars  : {top_paper['github_stars']}")
        print(f"   Impact %  : {round(top_paper.get('impact_score', 0) * 100)}%")
        print(f"   URL       : {top_paper['arxiv_url']}")

    # 3️⃣  Summarise with Ollama
    ollama_model = os.getenv("OLLAMA_MODEL", "mistral")
    print(f"\n[3/4] Generating summary with Ollama ({ollama_model})...")
    summary_raw = summarizer.summarize_paper(top_paper, model=ollama_model)

    if summary_raw:
        sections = summarizer.parse_summary(summary_raw)
        if verbose:
            for k, v in sections.items():
                print(f"\n   [{k.upper()}] {v[:120]}…")
    else:
        print("[WARN] Ollama unavailable – using abstract as fallback.")
        sections = summarizer.fallback_sections(top_paper)

    # 4️⃣  Send (or preview) the email
    print("\n[4/4] Sending email digest...")
    success = mailer.send_email(top_paper, sections, dry_run=dry_run)
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
