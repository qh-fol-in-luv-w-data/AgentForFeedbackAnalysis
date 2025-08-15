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
from sklearn.cluster import DBSCAN
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

    model_name = "/home/hqvu/Agent_analysis/model" 
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    model.to(device)
    model.eval()

    max_input_length = 512
    max_summary_length = 100

    for item in data:
        content = item.get("content", "")
        if not content:
            continue

        inputs = tokenizer.encode(
            content, return_tensors="pt", max_length=max_input_length, truncation=True
        ).to(device)

        summary_ids = model.generate(
            inputs,
            max_length=max_summary_length,
            num_beams=5,
            repetition_penalty=2.5,
            length_penalty=1.0,
            early_stopping=True
        )

        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        item["summary"] = summary 
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "messages": [
                {"role": "assistant",
                "content": f"{filename}",
                }
        ]
    }

def embedding(data):
    with open(data, "r", encoding="utf-8") as f:
        data = json.load(f)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    model_name = "/home/hqvu/Agent_analysis/phoBert" 
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    embeds = []
    for item in data:
        content = item.get("content", "")
        if not content:
            continue

        inputs = tokenizer.encode(
            content, return_tensors="pt", max_length=10000, truncation=True
        ).to(device)
        embeds = torch.stack(embeds)
    return embeds
    
# def cluster (embeds):
#     clustering = DBSCAN(eps=1.0, min_samples=2, metric='cosine')
#     labels = clustering.fit_predict(labels = clustering.fit_predict(embeds.cpu().numpy())
# )
#     print (labels)
#     return labels

embedding ("/home/hqvu/Agent_analysis/data/clean/merged_reviews_20250811_to_20250817.json")