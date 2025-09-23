import json
from ddgs import DDGS
import random


def generate_urls(max_total=200):
    industries = [
        "restaurant",
        "boutique",
        "plumbing",
        "coffee shop",
        "hair salon",
        "auto repair",
        "bakery",
        "florist",
        "gym",
        "bookstore",
        "pet store",
        "dentist",
        "real estate agent",
        "landscaping",
        "yoga studio",
        "photography",
        "accounting",
        "law firm",
        "catering",
        "event planning",
    ]
    all_urls = set()
    for industry in industries:
        query = f"{industry} small business website California"
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=50)
            urls = [
                r["href"]
                for r in results
                if "href" in r
                and r["href"].startswith("http")
                and "example" not in r["href"]
                and "list" not in r["href"]
            ]
            all_urls.update(urls)
        if len(all_urls) >= max_total:
            break
    unique_urls = list(all_urls)[:max_total]
    random.shuffle(unique_urls)  # Randomize for varied testing
    return unique_urls


if __name__ == "__main__":
    urls = generate_urls()
    with open("test_urls.json", "w") as f:
        json.dump(urls, f, indent=2)
    print(f"Generated {len(urls)} unique URLs and saved to test_urls.json")
