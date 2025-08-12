import requests
import json
import os
import time
from datetime import datetime, timedelta, timezone
from langchain.tools import tool
# === Cấu hình ===
# APP_ID = 1150288115  # Liên Quân Mobile VN
COUNTRY = "vn"
OUT_DIR = "data/raw"
MAX_PAGES = 50
SLEEP_BETWEEN = 1.0
RETRY_COUNT = 3
@tool
def crawl_app_store_reviews_tool (APP_ID):
    """ Crawl data with app store"""
    # === Tính tuần trước (UTC timezone-aware) ===
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    this_monday = (utc_now - timedelta(days=utc_now.weekday())).date()
    monday_date = this_monday - timedelta(days=7)
    sunday_date = monday_date + timedelta(days=6)
    
    print(f"Lấy review từ {monday_date} đến {sunday_date}")
    
    def parse_review_date(date_str):
        # Ví dụ date_str = '2025-08-10T05:15:08-07:00'
        try:
            return datetime.fromisoformat(date_str).astimezone(timezone.utc)
        except Exception:
            return None
    
    all_reviews = []
    
    for page in range(1, MAX_PAGES + 1):
        url = f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/page={page}/id={APP_ID}/sortby=mostrecent/json"
        print(f"Lấy trang {page}: {url}")
    
        for attempt in range(RETRY_COUNT):
            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code == 404:
                    print("Không còn trang nữa, dừng.")
                    break
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                print(f"Lỗi tải trang {page}, thử lại lần {attempt+1}: {e}")
                time.sleep(2)
        else:
            print(f"Không tải được trang {page}, dừng.")
            break
    
        entries = data.get("feed", {}).get("entry", [])
        if not entries or len(entries) <= 1:
            print("Không còn review, dừng.")
            break
    
        stop_crawl = False
        for i, entry in enumerate(entries):
            # Bỏ metadata app đầu tiên
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
                # Nếu review quá cũ, dừng crawl tiếp các trang sau
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
            print("Đã đạt tới review quá cũ, dừng crawl.")
            break
    
        time.sleep(SLEEP_BETWEEN)
    
    os.makedirs(OUT_DIR, exist_ok=True)
    file_name = f"reviews_ios_{APP_ID}_{monday_date.strftime('%Y%m%d')}_to_{sunday_date.strftime('%Y%m%d')}.json"
    output_path = os.path.join(OUT_DIR, file_name)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    
    print(f"Đã lưu {len(all_reviews)} review vào {output_path}")