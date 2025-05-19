import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import re
import time
import concurrent.futures
from typing import Set, List

base_url = "https://support.convert.com"
start_url = "https://support.convert.com/hc/en-us"
session = requests.Session()
session.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Encoding": "gzip, deflate"
}

# Regex to match relevant paths
PATH_PATTERN = re.compile(r'/hc/en-us/(articles|categories|sections)/[\w-]+')


def normalize_url(url: str) -> str:
    """Standardize URLs to prevent duplicates"""
    parsed = urlparse(url)
    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip('/') + '/',
        parsed.params,
        '',  # Remove all query parameters
        ''  # Remove fragments
    ))


def is_valid_url(url: str) -> bool:
    """Check if URL should be crawled"""
    parsed = urlparse(url)
    return (
            parsed.netloc == "support.convert.com"
            and bool(PATH_PATTERN.search(parsed.path))
            and not any(x in url.lower() for x in ["/signin", "/search"])
    )


def fetch_url(url: str) -> List[str]:
    """Fetch a single URL and return discovered links"""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        discovered = set()
        for link in soup.find_all('a', href=True):
            absolute = urljoin(base_url, link['href'])
            normalized = normalize_url(absolute)
            if is_valid_url(normalized):
                discovered.add(normalized)

        return list(discovered)

    except Exception as e:
        print(f"⚠️ Error on {url}: {str(e)[:80]}")
        return []


def fast_crawler(max_workers: int = 10, max_pages: int = 1000) -> Set[str]:
    """High-performance concurrent crawler"""
    visited = set()
    queue = {normalize_url(start_url)}
    results = set()
    pages_crawled = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        while queue and pages_crawled < max_pages:
            # Get batch of URLs to process
            current_batch = list(queue - visited)
            if not current_batch:
                break

            # Process batch concurrently
            future_to_url = {
                executor.submit(fetch_url, url): url
                for url in current_batch[:max_workers * 2]
            }

            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                visited.add(url)
                pages_crawled += 1

                try:
                    new_urls = future.result()
                    for new_url in new_urls:
                        if new_url not in visited and new_url not in results:
                            queue.add(new_url)
                            results.add(new_url)

                    print(f"\rCrawled: {pages_crawled} | Found: {len(results)}", end="")

                except Exception as e:
                    print(f"\nError processing {url}: {e}")

    return results


# Run the optimized crawler
print("🚀 Starting high-speed crawler...")
start_time = time.time()
unique_urls = fast_crawler(
    max_workers=15,  # Increase for faster crawling (but be respectful)
    max_pages=2000  # Maximum pages to crawl
)

# Save results
with open('convert_unique_urls.txt', 'w') as f:
    f.write("\n".join(sorted(unique_urls)))

print(f"\n✅ Saved {len(unique_urls)} URLs in {time.time() - start_time:.2f} seconds")