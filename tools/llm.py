import os
import ssl
import urllib3
import requests.sessions
import requests
import json
import torch
from langgraph.graph import MessagesState
from langchain.schema import AIMessage
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
    model_name = "/home/hqvu/Agent_analysis/bart_large_mnli"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    classifier = pipeline(
        "zero-shot-classification",
        model=model,
        tokenizer=tokenizer,
        device=device
    )
    labels = labelize(filename, classifier) 
    for item, label in zip(data, labels):
        item["label"] = label
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {
        "messages": [
                {"role": "assistant",
                "content": f"{filename}",
                }
        ]
    }

def labelize(data_path, classifier):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [item.get("process", "") for item in data if item.get("process", "").strip()]
    candidate_labels=[
            "positive feedback",
            "feature request",
            "cheating or hacking report", 
            "off-topic joke",
            "bug report", "game problem", "game error", "game not working"
        ]
    results = classifier(
        texts,
        candidate_labels=candidate_labels
    )
    labels = []
    results = classifier(texts, candidate_labels, batch_size=1)

    # pipeline returns a list of dicts when input is a list
    for res in results:
        labels.append(res["labels"][0])   # top label only

    return labels

def makeReport (datapath):
    with open(datapath, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [item.get("process", "") for item in data if item.get("process", "").strip()]