import requests
from bs4 import BeautifulSoup

URL = "https://4khdhub.one/"

response = requests.get(
    URL,
    timeout=20,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

results = []

for item in soup.select(".movie-card"):
    title = item.select_one(".title")

    if title:
        results.append({
            "name": title.get_text(strip=True)
        })

print(results)
