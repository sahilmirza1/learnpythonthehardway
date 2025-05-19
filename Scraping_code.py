import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import time
import concurrent.futures

# Configuration
INPUT_FILE = 'convert_unique_urls.txt'
OUTPUT_FILE = 'convert_articles.txt'
MAX_WORKERS = 10
REQUEST_DELAY = 0.5


def clean_text(text):
    """Clean and normalize scraped text"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def scrape_article(url):
    """Scrape a single support article"""
    try:
        response = requests.get(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout=15
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract article content
        content_div = soup.find('div', class_=re.compile(r'article-body|content'))
        if content_div:
            for element in content_div(['script', 'style', 'nav', 'footer', 'aside']):
                element.decompose()
            content = clean_text(content_div.get_text())
        else:
            content = "No content found"

        return {
            'url': url,
            'content': content
        }

    except Exception as e:
        print(f"⚠️ Error scraping {url}: {str(e)[:80]}")
        return None


def format_article(article):
    """Format article data for text output (simplified version)"""
    return f"""
URL: {article['url']}

Content:
{article['content']}

{'=' * 80}
"""


def main():
    # Read crawled URLs
    with open(INPUT_FILE, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Found {len(urls)} URLs to scrape")

    # Scrape articles concurrently
    scraped_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for url in urls:
            futures.append(executor.submit(scrape_article, url))
            time.sleep(REQUEST_DELAY)

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            if result:
                scraped_data.append(result)
            print(f"\rScraped {i + 1}/{len(urls)} articles", end="")

    # Save results
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for article in scraped_data:
            f.write(format_article(article))

    print(f"\n✅ Saved {len(scraped_data)} articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()