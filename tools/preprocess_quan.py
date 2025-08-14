from datetime import date, timedelta
import json
import re
from vnpreprocess.utils.process import preprocessing

BAD_WORDS = [
    "địt", "lồn", "cặc", "đụ", "mẹ mày", "đm", "dm", "fuck", "bitch", "shit",
    "đéo", "ngu", "khốn nạn", "dcm", "vcl", "ml", "vl", "cl", "cc", "đmm",
    "dmn", "dcmm", "mml", "lmm", "đml", "dmm", "xl", "lol", "vãi l", "lon", "db", "ncc"
]

def remove_bad_words(text):
    """Loại bỏ bad words trong chuỗi (cả đơn từ và cụm từ)."""
    # Xóa bad words nguyên cụm
    for bad in BAD_WORDS:
        pattern = r'\b' + re.escape(bad) + r'\b'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # Xóa khoảng trắng thừa
    return re.sub(r'\s+', ' ', text).strip()

def removeTeencode(sentence):
    return preprocessing(sentence)  # trả về list token

def removeIcon(sentence):
    emoji_pattern = re.compile(
        "[" 
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', sentence)

def preprocessVietnameseLanguage():
    """Preprocess: xóa icon → lọc bad words → chuẩn hóa, giữ nguyên struct JSON"""
    filename = "/home/hqvu/Agent_analysis/data/raw/reviews_20250804_to_20250810.json"
    
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for item in data:
        content = item.get('content', "")
        # 1. Xóa icon
        no_icon = removeIcon(content)
        # 2. Lọc bad words
        no_bad = remove_bad_words(no_icon)
        # 3. Chuẩn hóa + tách từ
        tokens = removeTeencode(no_bad)
        # 4. Ghép lại
        item['content'] = " ".join(tokens)
        print(item['content'])
    
    # Lưu file mới
    out_filename = "/home/hqvu/Agent_analysis/data/reviews_20250804_to_20250810_clean.json"
    with open(out_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

preprocessVietnameseLanguage()
