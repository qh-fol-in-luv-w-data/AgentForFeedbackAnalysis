from datetime import date, timedelta
from langchain.tools import tool
import json
import re
from vnpreprocess.utils.process import preprocessing
# Apply to remove urls, brackets; standardize unicode, teencode, punctuation; lower text, word segmentation ,... in Vietnamese text.
def removeTeencode (sentence):
    return preprocessing (sentence)
def removeIcon (sentence):
    emoji_pattern = re.compile("["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002700-\U000027BF"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA70-\U0001FAFF"  # Symbols & Pictographs Extended-A (contains 🫠)
        "\U00002600-\U000026FF"  # Misc symbols
        "]+",
        flags=re.UNICODE)
    return emoji_pattern.sub(r'', sentence) 
# def spamfilter (sentence):

# @tool
def preprocessVietnameseLanguage():
    """Preprocess data"""
    today = date.today().strftime ("%Y%m%d")
    seven_days_ago = (date.today() - timedelta(days = 8)).strftime ("%Y%m%d")
    filename = f"/home/hqvu/Agent_analysis/data/raw/reviews_{seven_days_ago}_to_{today}.json"
    with open (filename, "r", encoding = "utf-8") as f:
        data = json.load (f)
    contents = [item['content'] for item in data]
    # processed = [removeTeencode(removeIcon(sentence)) for sentence in contents]
    processed = []
    for sentence in contents:
        pro = removeTeencode(removeIcon(sentence))
        processed.extend (pro)
        print (pro)
    


    

preprocessVietnameseLanguage()