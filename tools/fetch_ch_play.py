from langchain.tools import tool
from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta, timezone, date
import json, os, time
 
@tool("crawl_google_play_weekly", return_direct=True)
def crawl_weekly_reviews_tool(app_id: str) -> str:
    """
    Crawl review của 1 app Google Play trong tuần chỉ định.
    - app_id: ID của app trên Google Play
    - monday_str: ngày thứ 2 đầu tuần, format dd-mm-YYYY
    - out_dir: thư mục lưu file
    """
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
    out_dir = "data/raw"
    os.makedirs(out_dir, exist_ok=True)
    file_name = f"reviews_{monday_dt.strftime('%Y%m%d')}_to_{(monday_dt + timedelta(days=6)).strftime('%Y%m%d')}.json"
    output_path = os.path.join(out_dir, file_name)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    return output_path