"""
fetcher.py — Fetches latest AI research papers from multiple credible sources:
  - arXiv API       : Real-time preprint server for CS/AI papers
  - Semantic Scholar: Citation counts & influence scores
  - Papers With Code: GitHub star counts & trending ML papers
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# ── API endpoints ─────────────────────────────────────────────
ARXIV_API_URL          = "http://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_API   = "https://api.semanticscholar.org/graph/v1"
PAPERS_WITH_CODE_API   = "https://paperswithcode.com/api/v1"

HF_API_URL = "https://huggingface.co/api/daily_papers"

def fetch_trending_papers(days_back: int = 14) -> list[dict]:
    """Fetch the top AI/ML papers from the last 14 days on Hugging Face Daily Papers."""
    all_papers = {}
    
    for i in range(days_back):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        url = f"{HF_API_URL}?date={date_str}"
        
        try:
            # print(f"   [FETCH] {date_str}...")
            response = requests.get(url, timeout=20)
            if response.status_code != 200:
                continue
            data = response.json()
        except Exception:
            continue

        for entry in data:
            paper_data = entry.get("paper", {})
            if not paper_data:
                continue
                
            arxiv_id = paper_data.get("id", "")
            if not arxiv_id or arxiv_id in all_papers:
                continue

            all_papers[arxiv_id] = {
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
                "github_stars":   paper_data.get("upvotes", 0),
            }

    return list(all_papers.values())


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





def fetch_trending_pwc() -> list[dict]:
    """Fetch trending papers from Papers With Code by scraping their homepage."""
    papers = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get("https://paperswithcode.com/", headers=headers, timeout=20)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        # PWC uses a specific structure for cards on their homepage
        cards = soup.select('.item-content')
        for card in cards:
            title_tag = card.select_one('h1 a')
            if not title_tag: continue
            
            title = title_tag.text.strip()
            pwc_url = "https://paperswithcode.com" + title_tag['href']
            
            # Extract ArXiv ID if available in the URL or page (usually in the link)
            # PWC links to paper page: /paper/title-slug
            # On the paper page, it usually has the ArXiv ID. 
            # For the homepage, we'll try to guess if the title is unique enough,
            # but better to store the PWC URL and use it as a fallback.
            
            papers.append({
                "title": title,
                "pwc_url": pwc_url,
                "source": "Papers With Code",
                "github_stars": 0, # We'll enrich this if possible or just use a default
                "arxiv_id": None # Will try to resolve later
            })
    except Exception as exc:
        print(f"[WARNING] Papers With Code scrape failed: {exc}")
        
    return papers

def fetch_all_papers() -> list[dict]:
    """End-to-end fetch: Aggregates HF (Viral Buzz) and PWC (Code Implementation)."""
    print("[INFO] Fetching trending papers from the last 14 days (Hugging Face)...")
    hf_papers = fetch_trending_papers(days_back=14)
    for p in hf_papers: p["source"] = "Hugging Face"
    
    print(f"[INFO] Retrieved {len(hf_papers)} unique papers from Hugging Face")

    print("[INFO] Fetching trending papers from Papers With Code...")
    pwc_papers = fetch_trending_pwc()
    print(f"[INFO] Scraped {len(pwc_papers)} papers from Papers With Code")

    # Merge and De-duplicate by title (ArXiv IDs are preferred but PWC doesn't give them on home)
    combined = {}
    
    # Process HF first (more data-rich)
    for p in hf_papers:
        combined[p['title'].lower()] = p

    # Merge PWC
    for p in pwc_papers:
        key = p['title'].lower()
        if key in combined:
            combined[key]["source"] = "HF + PWC"
            combined[key]["pwc_url"] = p["pwc_url"]
        else:
            # For PWC-only papers, we need to at least try to get ArXiv ID or abstract
            # This is slow, so we'll only do it for the top few if they aren't in HF
            combined[key] = p

    papers = list(combined.values())

    if not papers:
        return []

    print("[INFO] Enriching top candidates with Semantic Scholar...")
    # Sort roughly by upvotes/stars before enrichment to stay in budget
    papers.sort(key=lambda x: x.get('github_stars', 0), reverse=True)
    top_papers = papers[:20] 
    
    # Try to find ArXiv IDs for PWC papers that don't have them
    for p in top_papers:
        if not p.get('arxiv_id'):
            # Simple heuristic: PWC titles are usually exact. Semantic Scholar can find them.
            try:
                search_url = f"{SEMANTIC_SCHOLAR_API}/paper/search?query={p['title']}&limit=1&fields=paperId,externalIds,abstract,title,citationCount,influentialCitationCount"
                resp = requests.get(search_url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json().get('data', [])
                    if data:
                        ext_ids = data[0].get('externalIds', {})
                        p['arxiv_id'] = ext_ids.get('ArXiv')
                        p['abstract'] = data[0].get('abstract', '')
                        p['citation_count'] = data[0].get('citationCount', 0)
                        p['influence_score'] = data[0].get('influentialCitationCount', 0)
            except Exception:
                pass

    # Filter out papers that still don't have an ArXiv ID (we need them for summary)
    ready_papers = [p for p in top_papers if p.get('arxiv_id')]
    
    return ready_papers
