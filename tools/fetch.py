import requests
from datetime import datetime, timedelta, timezone, date
from langgraph.graph import MessagesState
from langchain.tools import tool
from google_play_scraper import Sort, reviews
import json, os, time
COUNTRY = "vn"
OUT_DIR = "/home/hqvu/Agent_analysis/data/raw"
MAX_PAGES = 50
SLEEP_BETWEEN = 1.0
RETRY_COUNT = 3
def crawl_app_store_reviews_tool ():
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
    file_name = f"reviews_{monday_date.strftime('%Y%m%d')}_to_{sunday_date.strftime('%Y%m%d')}_app_store.json"
    output_path = os.path.join(OUT_DIR, file_name)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    return output_path
def crawl_ch_play():
    app_id = "com.garena.game.kgvn"
    vn_tz = timezone(timedelta(hours=7))
    today = date.today()
    monday_date = today - timedelta(days=today.weekday())  # weekday() Monday=0
    sunday_date = monday_date + timedelta(days=6)
    monday_dt = datetime.combine(monday_date, datetime.min.time())

    weekdays_vi = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    all_reviews, cont_token = [], None
 
    while True:
        batch, cont_token = reviews(app_id, lang='vi', country='vn', sort=Sort.NEWEST, count=200, continuation_token=cont_token)
        if not batch:
            break
 
        stop_now = False
        for r in batch:
            at_vn_date = r['at'].astimezone(vn_tz).date()
            if monday_date <= at_vn_date <= sunday_date:
                all_reviews.append({
                    "content": r.get("content", "").strip(),
                    "score": r.get("score"),
                    "date": at_vn_date.strftime("%d/%m/%Y"),
                    "day_of_week": weekdays_vi[at_vn_date.weekday()]
                })
            elif at_vn_date < monday_date:
                stop_now = True
                break
 
        if stop_now or cont_token is None:
            break
        time.sleep(0.5)
    out_dir = "/home/hqvu/Agent_analysis/data/raw"
    os.makedirs(out_dir, exist_ok=True)
    file_name = f"reviews_{monday_dt.strftime('%Y%m%d')}_to_{(monday_dt + timedelta(days=6)).strftime('%Y%m%d')}_ch_play.json"
    output_path = os.path.join(out_dir, file_name)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    return output_path



def fetch():
    today = date.today()
    monday_date = today - timedelta(days=today.weekday())  # Monday=0
    sunday_date = monday_date + timedelta(days=6)

    chplay = crawl_ch_play()
    appStore = crawl_app_store_reviews_tool()

    with open(chplay, "r", encoding="utf-8") as f:
        chplay_data = json.load(f)

    with open(appStore, "r", encoding="utf-8") as f:
        appstore_data = json.load(f)

    merged_data = chplay_data + appstore_data

    merged_path = f"/home/hqvu/Agent_analysis/data/raw/merged_reviews_{monday_date.strftime('%Y%m%d')}_to_{sunday_date.strftime('%Y%m%d')}.json"
    
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    return {
        "messages": [
            {"path": merged_path}
        ]
    }

fetch()
