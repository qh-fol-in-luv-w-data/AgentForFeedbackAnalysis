from datetime import date, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langgraph.graph import MessagesState
from langchain.schema import AIMessage
import json
def tokenizeAndCosineSimilarity (text):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(text)
    similarity = cosine_similarity(tfidf_matrix)
    duplicates = set()
    for i in range(len(text)):
        for j in range(i + 1, len(text)):
            if similarity[i, j] >= 0.85:
                duplicates.add(i)
                duplicates.add(j)
    return list(duplicates)
def eliminateTooShortText(text): 
    min_length = 10
    return [i for i, t in enumerate(text) if len(t.strip()) < min_length]

def seedingFilter(state: MessagesState):
    print ("seeding filter")
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
    comments = [item.get("content", "") for item in data]
    short_idx = set(eliminateTooShortText(comments))
    dup_idx = set(tokenizeAndCosineSimilarity(comments))
    suspicious_idx = short_idx.union(dup_idx)
    clean_data = [item for i, item in enumerate(data) if i not in suspicious_idx]
    clean_output = f"/home/hqvu/Agent_analysis/data/clean/merged_reviews_{monday_date.strftime('%Y%m%d')}_to_{sunday_date.strftime('%Y%m%d')}.json"
    with open(clean_output, "w", encoding="utf-8") as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)
    return {
        "messages": [
                {"role": "assistant",
                "content": f"{clean_output}",
                }
        ]
    }
