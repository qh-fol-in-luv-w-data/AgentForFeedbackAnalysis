from datetime import date, timedelta
from langchain.tools import tool
import json
from langchain.schema import AIMessage
import re
from vnpreprocess.utils.process import preprocessing
from langgraph.graph import MessagesState
badwords = [
    "địt",
    "dit",
    "đit",
    "địt mẹ",
    "dit chi may",
    "ditchimay",
    "dit me",
    "dit me may",
    "dit con me may",
    "địtconmẹmày",
    "ditconmemay",
    "địtconmẹ",
    "ditconme",
    "đm",
    "dm",
    "đmm",
    "dmm",
    "đcm",
    "dcm",
    "dkm",
    "dkmm",
    "đkm",
    "đkmm",
    "đờ mờ",
    "đê ca mờ",
    "đéo",
    "dmm",
    "đmm",
    "cmm",
    "con me may",
    "conmemay",
    "con mẹ mày",
    "con mặt lồn",
    "thằng mặt lồn",
    "đệch",
    "đệt",
    "dit",
    "dis",
    "diz",
    "đjt",
    "djt",
    "đis",
    "ditmemayconcho",
    "ditmemay",
    "ditmethangoccho",
    "ditmeconcho",
    "dmconcho",
    "dmcs",
    "ditmecondi",
    "ditmecondicho",
    "con cặc",
    "cặc",
    "cac",
    "lon",
    "loz",
    "lozz",
    "cacc",
    "concac",
    "concu",
    "cailon",
    "lồn",
    "lồng",
    "lờ",
    "mé",
    "má",
    "mọe",
    "buồi",
    "cu",
    "cứt",
    "con mẹ",
    "vãi lồn",
    "vl",
    "vãi cả lồn",
    "vcl",
    "vãi cặc",
    "vãi lồng",
    "vãi lìn",
    "vãi con cặc",
    "vcc",
    "như cái lồn",
    "như con cặc",
    "đệch",
    "đéo",
    "chịch",
    "lếu lều",
    "liếm lồn",
    "bú cu",
    "xoạc",
    "mặt lồn",
    "mặt lờ",
    "đầu buồi",
    "đồ khỉ",
    "cailonmemay",
    "cailonme",
    "cailon",
    "concac",
    "thangmatlon",
    "buồi",
    "buoi",
    "dau buoi",
    "daubuoi",
    "caidaubuoi",
    "nhucaidaubuoi",
    "dau boi",
    "bòi",
    "dauboi",
    "caidauboi",
    "đầu bòy",
    "đầu bùi",
    "dau boy",
    "dauboy",
    "caidauboy",
    "b`",
    "cặc",
    "cak",
    "kak",
    "kac",
    "cac",
    "concak",
    "nungcak",
    "bucak",
    "caiconcac",
    "caiconcak",
    "cu",
    "cặk",
    "cak",
    "dái",
    "giái",
    "zái",
    "kiu",
    "cứt",
    "cuccut",
    "cutcut",
    "cứk",
    "cuk",
    "cười ỉa",
    "cười ẻ",
    "đéo",
    "đếch",
    "đếk",
    "dek",
    "đết",
    "đệt",
    "đách",
    "dech",
    "đ'",
    "deo",
    "d'",
    "đel",
    "đél",
    "del",
    "dell",
    "sapmatlol",
    "sapmatlon",
    "sapmatloz",
    "sấp mặt",
    "sap mat",
    "vlon",
    "vloz",
    "vlol",
    "vailon",
    "vai lon",
    "vai lol",
    "vailol",
    "nốn lừng",
    "vcl",
    "vl",
    "vleu",
    "chịch",
    "chich",
    "v~",
    "nứng",
    "nug",
    "đút đít",
    "chổng mông",
    "banh háng",
    "xéo háng",
    "xhct",
    "xephinh",
    "la liếm",
    "đổ vỏ",
    "xoạc",
    "xoac",
    "chich choac",
    "húp sò",
    "fuck",
    "fck",
    "bỏ bú",
    "buscu",
    "ngu",
    "óc chó",
    "occho",
    "lao cho",
    "láo chó",
    "bố láo",
    "chó má",
    "cờ hó",
    "sảng",
    "thằng chó",
    "thang cho'",
    "thang cho",
    "chó điên",
    "thằng điên",
    "thang dien",
    "đồ điên",
    "sủa bậy",
    "sủa tiếp",
    "sủa đi",
    "sủa càn",
    "mẹ bà",
    "mẹ cha mày",
    "me cha may",
    "mẹ cha anh",
    "mẹ cha nhà anh",
    "mẹ cha nhà mày",
    "me cha nha may",
    "mả cha mày",
    "mả cha nhà mày",
    "ma cha may",
    "ma cha nha may",
    "mả mẹ",
    "mả cha",
    "kệ mẹ",
    "kệ mịe",
    "kệ mịa",
    "kệ mje",
    "kệ mja",
    "ke me",
    "ke mie",
    "ke mia",
    "ke mja",
    "ke mje",
    "bỏ mẹ",
    "bỏ mịa",
    "bỏ mịe",
    "bỏ mja",
    "bỏ mje",
    "bo me",
    "bo mia",
    "bo mie",
    "bo mje",
    "bo mja",
    "chetme",
    "chet me",
    "chết mẹ",
    "chết mịa",
    "chết mja",
    "chết mịe",
    "chết mie",
    "chet mia",
    "chet mie",
    "chet mja",
    "chet mje",
    "thấy mẹ",
    "thấy mịe",
    "thấy mịa",
    "thay me",
    "thay mie",
    "thay mia",
    "tổ cha",
    "bà cha mày",
    "cmn",
    "cmnl",
    "lồn", 
    "duma",
    "vc",
    "cc"
]
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

def preprocessVietnameseLanguage(state: MessagesState):
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
        processed_content = removeBadWord(
            removeTeencode(
                removeIcon(content)
            )
        )
        if processed_content and processed_content.strip():
            new_item["content"] = processed_content
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