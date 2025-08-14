import json
import pandas as pd
import numpy as np
import torch
from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# ===== Khởi tạo BERT multilingual trên GPU nếu có =====
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-uncased')
model = BertModel.from_pretrained('bert-base-multilingual-uncased').to(device)
model.eval()
def get_embeddings(texts, batch_size=32):
    """Tạo BERT embeddings theo batch để tiết kiệm GPU."""
    embeddings = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
        batch_texts = [t if isinstance(t, str) else "" for t in texts[i:i+batch_size]]
        inputs = tokenizer(batch_texts, return_tensors='pt', truncation=True, padding=True, max_length=512).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        batch_emb = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        embeddings.append(batch_emb)
    return np.vstack(embeddings)

def filter_seeding(df, min_content_length=20, pr_keywords=None, similarity_threshold=0.7):
    """
    Lọc review nghi ngờ seeding dựa trên:
      - review ngắn
      - chứa PR keywords
      - cosine similarity
    Trả về DataFrame sạch.
    """
    if pr_keywords is None:
        pr_keywords = ['tuyệt vời nhất', 'hay nhất thế giới', 'game đỉnh cao',
                       'perfect game', 'best game ever']

    df = df.copy()
    df['content'] = df['content'].fillna("").astype(str)

    # --- Heuristics ---
    df['is_short'] = df['content'].str.len() < min_content_length
    df['has_pr_keyword'] = df['content'].str.lower().apply(lambda x: any(kw in x for kw in pr_keywords))

    # --- Embeddings ---
    embeddings = get_embeddings(df['content'].tolist())

    # --- Cosine similarity ---
    sim_matrix = cosine_similarity(embeddings)
    df['has_duplicate'] = np.any(sim_matrix > similarity_threshold, axis=1)

    # --- Tính điểm seeding ---
    conditions = ['is_short', 'has_pr_keyword', 'has_duplicate']
    df['seeding_score'] = df[conditions].sum(axis=1)

    # --- Lọc review sạch ---
    df_clean = df[df['seeding_score'] < 2].copy()

    # --- Xóa cột tạm ---
    df_clean = df_clean.drop(columns=['is_short', 'has_pr_keyword', 'has_duplicate', 'seeding_score'])
    return df_clean