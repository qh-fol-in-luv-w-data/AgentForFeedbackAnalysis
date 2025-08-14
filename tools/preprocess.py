from datetime import date, timedelta
from langchain.tools import tool
import json
import re
from vnpreprocess.utils.process import preprocessing
from viet_badwords_filter.filter import VNBadwordsFilter
import sys
from bad_word_list import badwords
# Apply to remove urls, brackets; standardize unicode, teencode, punctuation; lower text, word segmentation ,... in Vietnamese text.
def removeBadWord (sentence):
    if not sentence:
        return None
    words = sentence.split()
    cleaned_words = [
        "" if word.lower() in badwords else word for word in words
    ]
    return " ".join(cleaned_words)
def removeTeencode (sentence):
    if not sentence:
        return None

    prepro = preprocessing (sentence)
    return prepro.strip() if prepro.strip() else None
def removeIcon (sentence):
    if not sentence:
        return None

    emoji_pattern = re.compile("["
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
        flags=re.UNICODE)
    prepro = emoji_pattern.sub(r'', sentence) 
    return prepro.strip() if prepro.strip() else None

def preprocessVietnameseLanguage():
    """Preprocess data"""
    today = date.today().strftime ("%Y%m%d")
    seven_days_ago = (date.today() - timedelta(days = 8)).strftime ("%Y%m%d")
    filename = f"/home/hqvu/Agent_analysis/data/raw/reviews_20250804_to_20250810.json"
    with open (filename, "r", encoding = "utf-8") as f:
        data = json.load (f)
    contents = [item['content'] for item in data]
    # processed = [removeTeencode(removeIcon(sentence)) for sentence in contents]
    processed = []
    for sentence in contents:
        pro = removeBadWord(removeTeencode(removeIcon(sentence)))
        if pro is not None:
            processed.extend(pro)
            print (pro)
    


    

preprocessVietnameseLanguage()