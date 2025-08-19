import os
import ssl
import urllib3
import requests.sessions
import requests
import json
import torch
from langgraph.graph import MessagesState
from langchain.schema import AIMessage
from transformers import AutoTokenizer
from transformers import AutoModel
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import random
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

class TreeNode:
    def __init__(self, comment=None):
        self.comment = comment 
        self.children = []

    def is_leaf(self):
        return len(self.children) == 0
def similarity(v1, v2):
    return float(cosine_similarity(v1, v2)[0, 0])

def average_similarity(vec, node, tfidf_vectors, comments):
    leaf_comments = collect_comments(node)
    if not leaf_comments:
        return 0.0
    sims = []
    for c in leaf_comments:
        idx = comments.index(c)
        sims.append(similarity(vec, tfidf_vectors[idx]))
    return sum(sims) / len(sims)

def collect_comments(node):
    if node.is_leaf():
        return [node.comment] if node.comment else []
    res = []
    for child in node.children:
        res.extend(collect_comments(child))
    return res

def print_cluster(node, indent=0):
    prefix = "  " * indent
    if node.is_leaf():
        print(f"{prefix}- {node.comment}")
    else:
        print(f"{prefix}Cluster:")
        for child in node.children:
            print_cluster(child, indent + 1)
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
    # labels, lda = cluster (embeds, cont)
    # for item, label, lda in zip(data, labels, lda):
    #     item["means_pt"] = int(label) 
    #     item["lda_pt"] = int(lda.argmax())
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    merge_means, merge_lda = getContentForSummarize (filename)
    print (merge_means)
    print (merge_lda)
    
    return {
        "messages": [
                {"role": "assistant",
                "content": f"{filename}",
                }
        ]
    }
def getContentForSummarize(datapath):
    with open(datapath, encoding="utf-8") as f:
        data = json.load(f)
    grouped = defaultdict(list)
    group_lda = defaultdict(list)
    for item in data:
        grouped[item["means_pt"]].append(item["content"])
    for item in data: 
        group_lda[item["lda_pt"]].append(item["content"])
    merged_results = []
    merged_lda = []
    for means_pt, sentences in grouped.items():
        merged_results.append({
            "means_pt": means_pt,
            "merged_content": ".".join(sentences)
        })
    for lda_pt, sentences in group_lda.items():
        merged_lda.append({
            "lda_pt": lda_pt,
            "merged_content": ".".join(sentences)
        })
    return merged_results, merged_lda

def summarize (datapath):
    return True
def embedding(data_path):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # print(f"Using device: {device}")

    # model_name = "/home/hqvu/Agent_analysis/phoBert"
    # tokenizer = AutoTokenizer.from_pretrained(model_name)
    # model = AutoModel.from_pretrained(model_name)
    # model.to(device)
    # model.eval()

    embeds = []

    # for item in data:
    #     content = item.get("content", "")
    #     if not content:
    #         continue

    #     inputs = tokenizer(
    #         content,
    #         return_tensors="pt",
    #         truncation=True,
    #         padding=True,
    #         max_length=512
    #     ).to(device)

    #     with torch.no_grad():
    #         outputs = model(**inputs)
    #         sentence_embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
    #         embeds.append(sentence_embedding)

    # if not embeds:
    #     raise ValueError("No embeddings generated. Check your input data.")

    # embeds = torch.stack(embeds)
    # return embeds, [item.get('content') for item in data]
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(comments)


   


# def cluster(embeds, documents):
    


# # Insertion algorithm
# # --------------------------
# def insert_comment(root, comment, vec, tfidf_vectors, comments, threshold=0.5):
#     if root.is_leaf() and root.comment is None:  # empty root
#         root.comment = comment
#         return

#     # Find best cluster to insert into
#     best_node, best_score = None, -1
#     stack = [root]
#     while stack:
#         node = stack.pop()
#         if node.is_leaf():
#             score = average_similarity(vec, node, tfidf_vectors, comments)
#             if score > best_score:
#                 best_node, best_score = node, score
#         else:
#             stack.extend(node.children)

#     if best_node is not None and best_score >= threshold:
#         # Merge into cluster
#         if best_node.is_leaf():
#             new_cluster = TreeNode()
#             new_cluster.children.append(TreeNode(best_node.comment))
#             new_cluster.children.append(TreeNode(comment))
#             best_node.comment = None
#             best_node.children = new_cluster.children
#         else:
#             best_node.children.append(TreeNode(comment))
#     else:
#         # New independent cluster
#         if root.is_leaf():
#             # Root was a single comment → make it cluster
#             old_comment = root.comment
#             root.comment = None
#             root.children = [TreeNode(old_comment), TreeNode(comment)]
#         else:
#             root.children.append(TreeNode(comment))

# # --------------------------
# # Pretty printing
# # --------------------------
# def print_cluster(node, indent=0):
#     prefix = "  " * indent
#     if node.is_leaf():
#         print(f"{prefix}- {node.comment}")
#     else:
#         print(f"{prefix}Cluster:")
#         for child in node.children:
#             print_cluster(child, indent + 1)

# # --------------------------
# # Example usage
# # --------------------------
# comments = [
#     "Game is lag",
#     "Character too strong, need nerf",
#     "Wifi good but game lag",
#     "Bug in game at the door",
#     "Need more skin"
# ]

# # Build TF-IDF
# vectorizer = TfidfVectorizer()
# X = vectorizer.fit_transform(comments)

# # Incremental insertion
# root = TreeNode()
# for i, comment in enumerate(comments):
#     insert_comment(root, comment, X[i], X, comments, threshold=0.1)  # lower threshold → stricter grouping

# # Print final cluster tree
# print_cluster(root)
