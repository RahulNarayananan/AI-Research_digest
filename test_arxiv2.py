import requests

url = "http://export.arxiv.org/api/query"
params = {
    "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV OR cat:cs.RO OR cat:cs.NE",
    "sortBy": "submittedDate",
    "sortOrder": "descending",
    "max_results": 10
}
try:
    print("Fetching arXiv (Simple query)...")
    r = requests.get(url, params=params)
    print(r.status_code)
    print(r.text[:200])
except Exception as e:
    print(e)
