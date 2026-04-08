"""
fetcher.py — Fetches latest AI research papers from multiple credible sources:
  - arXiv API       : Real-time preprint server for CS/AI papers
  - Semantic Scholar: Citation counts & influence scores
  - Papers With Code: GitHub star counts & trending ML papers
"""

import requests
import time
from datetime import datetime

# ── API endpoints ─────────────────────────────────────────────
ARXIV_API_URL          = "http://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_API   = "https://api.semanticscholar.org/graph/v1"
PAPERS_WITH_CODE_API   = "https://paperswithcode.com/api/v1"

HF_API_URL = "https://huggingface.co/api/daily_papers"

def fetch_trending_papers() -> list[dict]:
    """Fetch the top AI/ML papers the industry is talking about from Hugging Face Daily Papers."""
    try:
        response = requests.get(HF_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print(f"[WARNING] Hugging Face fetch failed: {exc}")
        return []

    papers = []
    for entry in data:
        paper_data = entry.get("paper", {})
        if not paper_data:
            continue
            
        arxiv_id = paper_data.get("id", "")
        if not arxiv_id:
            continue

        papers.append({
            "title":          paper_data.get("title", "").replace("\n", " ").strip(),
            "abstract":       paper_data.get("summary", "").replace("\n", " ").strip(),
            "authors":        [a.get("name", "") for a in paper_data.get("authors", [])][:5],
            "published":      paper_data.get("publishedAt", ""),
            "arxiv_id":       arxiv_id,
            "arxiv_url":      f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url":        f"https://arxiv.org/pdf/{arxiv_id}",
            "categories":     ["AI/ML"],
            "citation_count": 0,
            "influence_score": 0,
            "github_stars":   paper_data.get("upvotes", 0),  # We'll use HF upvotes as the baseline 'stars'
        })

    return papers


def enrich_with_semantic_scholar(papers: list[dict], batch_size: int = 10) -> list[dict]:
    """Add citation counts and influential citation scores via Semantic Scholar."""
    enriched = []

    for i in range(0, len(papers), batch_size):
        batch     = papers[i : i + batch_size]
        arxiv_ids = [f"ARXIV:{p['arxiv_id'].split('v')[0]}" for p in batch]

        try:
            resp = requests.post(
                f"{SEMANTIC_SCHOLAR_API}/paper/batch",
                json={"ids": arxiv_ids},
                params={"fields": "citationCount,influentialCitationCount"},
                timeout=20,
            )
            if resp.status_code == 200:
                data = resp.json()
                for j, paper_data in enumerate(data):
                    if paper_data and j < len(batch):
                        batch[j]["citation_count"]  = paper_data.get("citationCount", 0) or 0
                        batch[j]["influence_score"]  = paper_data.get("influentialCitationCount", 0) or 0
            else:
                if "No valid paper ids given" not in resp.text:
                    print(f"[WARNING] Semantic Scholar returned {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            print(f"[WARNING] Semantic Scholar error: {exc}")

        enriched.extend(batch)
        time.sleep(1.2)  # respect rate limits

    return enriched





def fetch_all_papers() -> list[dict]:
    """End-to-end fetch: HF Daily Papers → Semantic Scholar enrichment → GitHub stars."""
    print("[INFO] Fetching trending papers from Hugging Face Daily Papers...")
    papers = fetch_trending_papers()
    print(f"[INFO] Retrieved {len(papers)} trending papers from Hugging Face")

    if not papers:
        return []

    print("[INFO] Enriching with citation data from Semantic Scholar...")
    papers = enrich_with_semantic_scholar(papers)

    return papers
