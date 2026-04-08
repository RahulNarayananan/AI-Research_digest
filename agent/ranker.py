"""
ranker.py — Ranks papers by a composite impact score:

    score = (citation_velocity × 0.40)
          + (influential_citations × 0.40)
          + (github_stars          × 0.20)

All three signals are min-max normalised to [0, 1] before weighting.
If ALL papers have zero citation data (e.g. brand-new papers), the ranker
falls back to publish-date recency so you always get the most relevant paper.
"""

from datetime import datetime, timezone


def _safe_max(values: list[float]) -> float:
    m = max(values, default=0)
    return m if m > 0 else 1.0


def rank_papers(papers: list[dict], top_n: int = 1) -> list[dict]:
    """Return the top-N papers sorted by composite impact score."""
    if not papers:
        return []

    max_cit  = _safe_max([p["citation_count"]  for p in papers])
    max_inf  = _safe_max([p["influence_score"]  for p in papers])
    max_star = _safe_max([p["github_stars"]     for p in papers])

    for paper in papers:
        cit_norm  = paper["citation_count"]  / max_cit
        inf_norm  = paper["influence_score"] / max_inf
        star_norm = paper["github_stars"]    / max_star

        paper["impact_score"] = (
            cit_norm  * 0.40 +
            inf_norm  * 0.40 +
            star_norm * 0.20
        )

    ranked = sorted(papers, key=lambda p: p["impact_score"], reverse=True)

    # Fallback: if everything scored 0, sort by recency
    if all(p["impact_score"] == 0.0 for p in ranked):
        print("[INFO] No citation signals available — falling back to recency ranking")

        def _parse_date(date_str: str) -> datetime:
            try:
                return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                return datetime.min.replace(tzinfo=timezone.utc)

        ranked = sorted(papers, key=lambda p: _parse_date(p["published"]), reverse=True)

    return ranked[:top_n]
