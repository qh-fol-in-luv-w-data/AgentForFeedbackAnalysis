import json
import time
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from google_play_scraper import reviews
from langchain.tools import tool
import re
# @tool
# def crawl_steam(app_id: str = "792990"):
#     """
#     Crawl recent discussions from a Steam community forum within the last 7 days.
#     app_id should be the numeric ID of the Steam game (e.g., "792990").
#     """
#     base_url = f"https://steamcommunity.com/app/{app_id}/discussions/"
#     cutoff_date = datetime.now() - timedelta(days=7)

#     session = requests.Session()
#     headers = {
#         "User-Agent": (
#             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#             "AppleWebKit/537.36 (KHTML, like Gecko) "
#             "Chrome/115.0.0.0 Safari/537.36"
#         ),
#         "Accept-Language": "en-US,en;q=0.9",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Referer": "https://steamcommunity.com/",
#         "Connection": "keep-alive",
#     }

#     def fetch_soup(url):
#         for attempt in range(3):  # Retry up to 3 times
#             try:
#                 resp = session.get(url, headers=headers, timeout=10)
#                 resp.raise_for_status()
#                 return BeautifulSoup(resp.text, "html.parser")
#             except requests.HTTPError as e:
#                 if resp.status_code == 403:
#                     print(f"[403] Access forbidden for {url}, trying again...")
#                     time.sleep(2)
#                 else:
#                     raise
#             except Exception as e:
#                 print(f"[Error] {e}, retrying...")
#                 time.sleep(2)
#         return None

#     def parse_steam_date(date_str):
#         try:
#             if "am" in date_str.lower() or "pm" in date_str.lower():
#                 return datetime.strptime(date_str, "%d %b @ %I:%M%p").replace(year=datetime.now().year)
#             else:
#                 return datetime.strptime(date_str, "%d %b, %Y")
#         except Exception:
#             return None

#     def get_thread_urls_from_page(page_number):
#         url = base_url if page_number == 1 else f"{base_url}?fp={page_number}"
#         soup = fetch_soup(url)
#         if soup is None:
#             return []

#         threads = []
#         for row in soup.select("div.forum_topic_row"):
#             link_tag = row.select_one("a.forum_topic_overlay")
#             date_tag = row.select_one("div.forum_lastpost > div:nth-of-type(2)")
#             if not link_tag or not date_tag:
#                 continue

#             thread_url = (
#                 link_tag["href"]
#                 if link_tag["href"].startswith("http")
#                 else "https://steamcommunity.com" + link_tag["href"]
#             )
#             date_str = date_tag.text.strip()
#             thread_date = parse_steam_date(date_str)

#             if thread_date and thread_date >= cutoff_date:
#                 threads.append(thread_url)
#         return threads

#     def parse_thread(url):
#         soup = fetch_soup(url)
#         if soup is None:
#             return None

#         title = soup.select_one('div.topic')
#         author = soup.select_one('div.topic_author a')
#         posts = []
#         for post in soup.select('div.commentthread_comment'):
#             user = post.select_one('.commentthread_comment_author a')
#             date = post.select_one('.commentthread_comment_timestamp')
#             content = post.select_one('.commentthread_comment_text')
#             posts.append({
#                 "user": user.text.strip() if user else "Unknown",
#                 "date": date.text.strip() if date else "Unknown",
#                 "content": content.text.strip() if content else ""
#             })
#         return {
#             "url": url,
#             "title": title.text.strip() if title else "No title",
#             "author": author.text.strip() if author else "Unknown",
#             "posts": posts
#         }

#     all_threads = set()
#     page = 1
#     saved_data = []

#     while True:
#         urls = get_thread_urls_from_page(page)
#         if not urls:
#             break
#         all_threads.update(urls)
#         page += 1
#         time.sleep(1)

#     for thread_url in all_threads:
#         thread_data = parse_thread(thread_url)
#         if not thread_data:
#             continue
#         for post in thread_data["posts"]:
#             saved_data.append({"content": post["content"]})
#             time.sleep(1)

#     return [{"source": "steam", "content": p["content"]} for p in saved_data]
def parse_vietnamese_date(html_str):
    """Parse date like '8 tháng 8, 2025' từ html string"""
    soup = BeautifulSoup(html_str, 'html.parser')
    date_text = soup.get_text(strip=True)  # "8 tháng 8, 2025"

    # Dùng regex tách ngày, tháng, năm
    match = re.match(r"(\d{1,2}) tháng (\d{1,2}), (\d{4})", date_text)
    if not match:
        raise ValueError("Không nhận dạng được định dạng ngày")

    day, month, year = match.groups()
    day = int(day)
    month = int(month)
    year = int(year)

    return datetime(year, month, day)
@tool
def crawl_google_play(app_id: str = "com.garena.game.kgvn"):
    """Crawl reviews from Google Play for the given app ID."""
    result, _ = reviews(app_id, lang='vi', country='vn')
    return [{"source": "google_play", "content": r["content"]} for r in result]


@tool
def crawl_app_store(app_id: str = "1150288115", country: str = "vn"):
    """Crawl reviews from App Store for Liên Quân."""
    url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
    r = requests.get(url)
    feed = r.json().get("feed", {}).get("entry", [])[1:]
    return [{"source": "app_store", "content": e["content"]["label"]} for e in feed]


def run_crawl_agent():
    print("🤖 Starting daily crawl...")
    today = datetime.now().strftime("%Y-%m-%d")

    with ThreadPoolExecutor() as executor:
        futures = [
            # executor.submit(crawl_steam.run, "https://steamcommunity.com/app/792990/discussions/"),
            executor.submit(crawl_google_play.run, "com.garena.game.kgvn"),
            executor.submit(crawl_app_store.run, "1150288115")
        ]

        results = []
        for f in futures:
            try:
                results.extend(f.result())
            except Exception as e:
                print(f"Error: {e}")

    out_file = f"reviews_{today}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ {today}: {len(results)} reviews saved to {out_file}")


if __name__ == "__main__":
    run_crawl_agent()
