import requests
import json
import os
import time
from datetime import datetime, timedelta, timezone
from langchain.tools import tool
COUNTRY = "vn"
OUT_DIR = "data/raw"
MAX_PAGES = 50
SLEEP_BETWEEN = 1.0
RETRY_COUNT = 3
# @tool
def crawl_app_store_reviews_tool (APP_ID):
    """ Crawl data with app store with APP_ID is thre app id of the app store.
    """
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    this_monday = (utc_now - timedelta(days=utc_now.weekday())).date()
    monday_date = this_monday - timedelta(days=7)
    sunday_date = monday_date + timedelta(days=6)
    
    print(f"Lấy review từ {monday_date} đến {sunday_date}")
    
    def parse_review_date(date_str):
        try:
            return datetime.fromisoformat(date_str).astimezone(timezone.utc)
        except Exception:
            return None
    
    all_reviews = []
    
    for page in range(1, MAX_PAGES + 1):
        url = f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/page={page}/id=1150288115/sortby=mostrecent/json"
    
        for attempt in range(RETRY_COUNT):
            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code == 404:
                    break
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                time.sleep(2)
        else:
            break
    
        entries = data.get("feed", {}).get("entry", [])
        if not entries or len(entries) <= 1:
            print("Không còn review, dừng.")
            break
    
        stop_crawl = False
        for i, entry in enumerate(entries):
            if i == 0 and "im:name" in entry:
                continue
    
            date_str = None
            if isinstance(entry.get("updated"), dict):
                date_str = entry.get("updated", {}).get("label")
            else:
                date_str = entry.get("updated")
    
            review_date = parse_review_date(date_str)
            if review_date is None:
                continue
    
            review_day = review_date.date()
            if review_day < monday_date:
                stop_crawl = True
                break
    
            if monday_date <= review_day <= sunday_date:
                all_reviews.append({
                    "author": entry.get("author", {}).get("name", {}).get("label", ""),
                    "rating": int(entry.get("im:rating", {}).get("label", 0)),
                    "title": entry.get("title", {}).get("label", ""),
                    "content": entry.get("content", {}).get("label", ""),
                    "date": review_date.strftime("%Y-%m-%d %H:%M:%S %Z")
                })
    
        if stop_crawl:
            break
    
        time.sleep(SLEEP_BETWEEN)
    
    os.makedirs(OUT_DIR, exist_ok=True)
    file_name = f"reviews_ios_{APP_ID}_{monday_date.strftime('%Y%m%d')}_to_{sunday_date.strftime('%Y%m%d')}.json"
    output_path = os.path.join(OUT_DIR, file_name)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    