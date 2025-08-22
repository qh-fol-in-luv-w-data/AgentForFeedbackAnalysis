from datetime import date, timedelta
from langchain.tools import tool
import json
from langchain.schema import AIMessage
import re
from vnpreprocess.utils.process import preprocessing
from langgraph.graph import MessagesState
from nltk.corpus import words
from better_profanity import profanity
import string
from wordfreq import zipf_frequency
def removeBadWord (sentence):
    if not sentence:
        return None
    profanity.load_censor_words()
    clean_text = profanity.censor(sentence, censor_char="")
    return clean_text

def is_english_word(word: str) -> bool:
    return zipf_frequency(word, "en") > 2.3

def filter_english_sentences(sentences):
    if not sentences:
        return None
    words = sentences.split()
    if all(is_english_word(w.lower()) for w in words):
        return sentences
    else:
        return None

def removeIcon (sentence):
    sentence = sentence.lower()
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
def getWeeklyScore (scores):
    average_score = sum(scores) / len(scores)
    return average_score
def preprocessEnglishLanguage(state: MessagesState):
    print ("preprocess")
    today = date.today()
    monday_date = today - timedelta(days=today.weekday())  # Monday=0
    sunday_date = monday_date + timedelta(days=6)
    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages found in state")
    last_msg = messages[-1]
    if isinstance(last_msg, AIMessage):
        filename = last_msg.content  
    else:
        raise ValueError("Last message is not an AIMessage containing the path")

    with open (filename, "r", encoding = "utf-8") as f:
        data = json.load (f)
    scores = [item["score"] for item in data]
    score = getWeeklyScore (scores)
    print (score)
    processed_data = []
    for item in data:
        new_item = dict(item)
        content = new_item.get("content")
        processed_content = filter_english_sentences(removeBadWord(
                    removeIcon(content)
        )
        )
    
        if processed_content and processed_content.strip():
            new_item["process"] = processed_content
            processed_data.append(new_item)
    output_filename = f"/home/hqvu/Agent_analysis/data/preprocess/reviews_processed_{monday_date.strftime('%Y%m%d')}_to_{sunday_date.strftime('%Y%m%d')}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
        return {
        "messages": [
                {"role": "assistant",
                "content": f"{output_filename}",
                "additional_kwargs" : {"average_score": score}
                }
        ]
    }