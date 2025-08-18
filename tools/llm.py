import os
import ssl
import urllib3
import requests.sessions
import requests
import json
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from langgraph.graph import MessagesState
from langchain.schema import AIMessage
from transformers import AutoTokenizer, AutoModelForMaskedLM
from transformers import AutoModel
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
# --- Disable SSL Verification ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
 
old_request = requests.sessions.Session.request
def unsafe_request(self, *args, **kwargs):
    kwargs['verify'] = False
    return old_request(self, *args, **kwargs)
requests.sessions.Session.request = unsafe_request
 
from requests.sessions import Session as OriginalSession
class UnsafeSession(OriginalSession):
    def request(self, *args, **kwargs):
        kwargs['verify'] = False
        return super().request(*args, **kwargs)
requests.Session = UnsafeSession

def summarizeText(state: MessagesState):
    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages found in state")
    
    last_msg = messages[-1]
    if isinstance(last_msg, AIMessage):
        filename = last_msg.content
    else:
        raise ValueError("Last message is not an AIMessage containing the JSON file path") 
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    embeds, cont = embedding (filename) 
    labels, lda = cluster (embeds, cont)
    for item, label, lda in zip(data, labels, lda):
        item["means_pt"] = int(label) 
        item["lda_pt"] = int(lda.argmax())

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {
        "messages": [
                {"role": "assistant",
                "content": f"{filename}",
                }
        ]
    }
def summarize (datapath):
    return True
def embedding(data_path):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    model_name = "/home/hqvu/Agent_analysis/phoBert"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.to(device)
    model.eval()

    embeds = []

    for item in data:
        content = item.get("content", "")
        if not content:
            continue

        inputs = tokenizer(
            content,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            sentence_embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
            embeds.append(sentence_embedding)

    if not embeds:
        raise ValueError("No embeddings generated. Check your input data.")

    embeds = torch.stack(embeds)
    return embeds, [item.get('content') for item in data]


   


def cluster(embeds, documents):
    vietnamese_stopwords = [
    "a", "ai", "alô", "anh", "anh ấy", "anh ta", "bà", "bạn", "bạn ấy", "bạn ta",
    "bây giờ", "bị", "biết", "cả", "các", "các bạn", "các anh", "các chị", "các em",
    "các ông", "các bà", "cái", "cái đó", "cái này", "cần", "cao", "cả", "cả hai",
    "chỉ", "cho", "chúng", "chúng tôi", "chúng ta", "chứ", "chưa", "có", "có thể",
    "có người", "của", "cũng", "cũng như", "cứ", "cứu", "đã", "đang", "đây",
    "điều", "điều đó", "điều này", "đó", "được", "đừng", "em", "em ấy", "em ta",
    "giữa", "gì", "hơn", "hầu như", "hãy", "hiện", "hiện tại", "hoặc", "họ", "khi",
    "khoảng", "không", "là", "lại", "làm", "làm cho", "lúc", "lúc đó", "mà", "mấy",
    "mỗi", "một", "một số", "một vài", "này", "nên", "nếu", "những", "như", "như thế",
    "nói", "nơi", "nơi đây", "nơi đó", "nước", "phải", "qua", "quá", "ra", "rằng",
    "rất", "rồi", "sau", "sau đó", "sẽ", "tại", "tất cả", "tôi", "tôi ấy", "tôi ta",
    "trong", "trước", "trước đó", "trước tiên", "và", "vậy", "vì", "việc", "với",
    "vừa", "vẫn", "điều", "điều gì", "đó", "để", "đây", "đó", "được", "đã", "ở",
    "ở đây", "ở đó", "ấy", "ì", "ồ", "ừ", "ấy", "ừ", "ơ", "à", "á", "ừm"
]

    n_clusters = 20
    embeds = embeds.detach().cpu().numpy()
    clustering  = KMeans(n_clusters=n_clusters, random_state=42)
    labels = clustering.fit_predict(embeds)
    print (labels)
    vectorizer = TfidfVectorizer(stop_words=vietnamese_stopwords)
    X_bow = vectorizer.fit_transform(documents)
    lda = LatentDirichletAllocation(n_components=n_clusters, random_state=42)
    lda_topics = lda.fit_transform(X_bow) 
    return labels, lda_topics
    # n_clusters = 40
    # embeds_np = embeds.detach().cpu().numpy()
    # agg = AgglomerativeClustering(n_clusters=n_clusters, metric='cosine', linkage='average')
    # labels = agg.fit_predict(embeds_np)
    # return labels
# embedding ("data/clean/merged_reviews_20250818_to_20250824.json")


