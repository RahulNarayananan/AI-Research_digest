from paperswithcode import PapersWithCodeClient
client = PapersWithCodeClient()

try:
    print("Fetching papers with -github_link_count...")
    papers = client.paper_list(ordering="-github_link_count", items_per_page=10)
    for p in papers.results:
        print(f"- {p.title} (Stars: {p.github_link_count})")
except Exception as e:
    print(f"FAILED: {e}")
