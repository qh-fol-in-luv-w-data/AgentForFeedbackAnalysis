from datetime import date, timedelta
from langchain.tools import tool
import json
from langchain.schema import AIMessage
import re
from vnpreprocess.utils.process import preprocessing
from langgraph.graph import MessagesState
import nltk
from nltk.corpus import words
from nltk.corpus import stopwords
from better_profanity import profanity
from nltk.stem import WordNetLemmatizer
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0
nltk.download('stopwords')
nltk.download('words')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('punkt')


# def jaccardSimi (a, b):

def CommentTermNormalization (sentence):
    return True
def removeStopWords (sentence):
    if not sentence:
        return None
    stop_words = set(stopwords.words('english'))
    words_in_text = sentence.split()
    filtered_words = [word for word in words_in_text if word.lower() not in stop_words]

    clean_text = ' '.join(filtered_words)
    return clean_text

def removeBadWord (sentence):
    if not sentence:
        return None
    profanity.load_censor_words()
    clean_text = profanity.censor(sentence, censor_char="")
    return clean_text


def removeTeencode (sentence):
    if not sentence:
        return None
    lang = detect(sentence)
    if lang != 'en':
        return None
    lemmatizer = WordNetLemmatizer()
    words = sentence.split()
    lemmatized = [lemmatizer.lemmatize(w, pos='v') for w in words]
    # Join back into a sentence
    return " ".join(lemmatized) if lemmatized else None
def removeIcon (sentence):
    sentence = sentence.lower()
    if not sentence:
        return None
    english_vocab = set(words.words())
    words_in_text = sentence.split()
    english_words = [word for word in words_in_text if word.lower().strip('.,!?') in english_vocab]
    clean_text = ' '.join(english_words)
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
    prepro = emoji_pattern.sub(r'', clean_text) 
    return prepro.strip() if prepro.strip() else None

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
    processed_data = []
    for item in data:
        new_item = dict(item)
        content = new_item.get("content")
        processed_content = removeStopWords(removeBadWord(
            removeTeencode(
                removeIcon(content)
            )
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
                }
        ]
    }


    

# preprocessVietnameseLanguage()