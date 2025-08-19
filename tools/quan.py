# import json
# import re
# import torch
# import numpy as np
# import pandas as pd
# from tqdm import tqdm
# from datetime import date, timedelta
# import os
 
# from underthesea import text_normalize
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity
# from transformers import BertTokenizer, BertModel
# from googletrans import Translator  # dịch sang tiếng Việt
 
# # ===== Paths =====
# input_dir = "/kaggle/input/d/qhofol/process-cluster-agent"
# badwords_path = os.path.join(input_dir, "badwords.txt")
# ten_tuong_path = os.path.join(input_dir, "champions.txt")
# khen_game_path = os.path.join(input_dir, "khen_game.txt")
 
# for path in [badwords_path, ten_tuong_path, khen_game_path]:
#     if not os.path.exists(path):
#         raise FileNotFoundError(f"Missing file: {path}")
 
# # ===== Load dictionaries =====
# with open(badwords_path, "r", encoding="utf-8") as f:
#     badwords = [line.strip().lower() for line in f if line.strip()]
 
# with open(ten_tuong_path, "r", encoding="utf-8") as f:
#     ten_tuong = [line.strip().lower() for line in f if line.strip()]
 
# with open(khen_game_path, "r", encoding="utf-8") as f:
#     list_khen_game = [line.strip().lower() for line in f if line.strip()]
 
# # ===== Rule tướng đặc biệt =====
# special_prefix = {"nakroth", "dirak", "florentino"}
 
# def has_tuong(full_text):
#     words = re.findall(r'\b\w+\b', full_text.lower())  # tách từ
#     for word in words:
#         for tuong in ten_tuong:
#             if tuong in special_prefix:
#                 if word == tuong[:3]:  # chỉ cần 3 ký tự
#                     return True
#             else:
#                 if word == tuong:  # cần match full
#                     return True
#     return False
 
# # ===== Text cleaning =====
# def removeBadWord(sentence):
#     if not sentence:
#         return None
#     words = sentence.split()
#     cleaned_words = ["" if word.lower() in badwords else word for word in words]
#     return " ".join(cleaned_words).strip()
 
# def removeTeencode(sentence):
#     if not sentence:
#         return None
#     prepro = text_normalize(sentence)
#     return prepro.strip() if prepro.strip() else None
 
# def removeIcon(sentence):
#     if not sentence:
#         return None
#     emoji_pattern = re.compile("["  
#         "\U0001F600-\U0001F64F"
#         "\U0001F300-\U0001F5FF"
#         "\U0001F680-\U0001F6FF"
#         "\U0001F1E0-\U0001F1FF"
#         "\U00002700-\U000027BF"
#         "\U000024C2-\U0001F251"
#         "\U0001F900-\U0001F9FF"
#         "\U0001FA70-\U0001FAFF"
#         "\U00002600-\U000026FF"
#         "]+", flags=re.UNICODE)
#     prepro = emoji_pattern.sub(r'', sentence)
#     return prepro.strip() if prepro.strip() else None
 
# # ===== Rule-based clustering & labeling =====
# list_loi_game = ["lag", "server", "đăng nhập", "crash", "bảo trì", "bug", "lỗi", "văng",  
#                  "cân bằng", "hệ thống", "xem lại","tố cáo"]
 
# def assign_label(item):
#     full_text = item["content"].lower()
#     if any(kw in full_text for kw in list_khen_game):
#         return "khen game"
#     elif any(kw in full_text for kw in list_loi_game):
#         return "lỗi game"
#     elif has_tuong(full_text):
#         return "lỗi tướng"
#     else:
#         return "rác"
 
# def cluster_comments(processed_data):
#     for i, item in enumerate(processed_data):
#         item["cluster"] = assign_label(item)  # cluster = label
#         item["label"] = item["cluster"]
#     return processed_data
 
# # ===== Seeding filter (BERT) =====
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-uncased')
# bert_model = BertModel.from_pretrained('bert-base-multilingual-uncased').to(device)
# bert_model.eval()
 
# def get_embeddings(texts, batch_size=32):
#     embeddings = []
#     for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
#         batch_texts = [t if isinstance(t, str) else "" for t in texts[i:i+batch_size]]
#         inputs = tokenizer(batch_texts, return_tensors='pt', truncation=True, padding=True, max_length=512).to(device)
#         with torch.no_grad():
#             outputs = bert_model(**inputs)
#         batch_emb = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
#         embeddings.append(batch_emb)
#     return np.vstack(embeddings)
 
# def filter_seeding(data, min_content_length=20, pr_keywords=None, similarity_threshold=0.7):
#     if pr_keywords is None:
#         pr_keywords = ['tuyệt vời nhất', 'hay nhất thế giới', 'game đỉnh cao',
#                        'perfect game', 'best game ever']
 
#     df = pd.DataFrame(data)
#     df['content'] = df['content'].fillna("").astype(str)
#     df['is_short'] = df['content'].str.len() < min_content_length
#     df['has_pr_keyword'] = df['content'].str.lower().apply(lambda x: any(kw in x for kw in pr_keywords))
 
#     embeddings = get_embeddings(df['content'].tolist())
#     sim_matrix = cosine_similarity(embeddings)
#     df['has_duplicate'] = np.any(sim_matrix > similarity_threshold, axis=1)
 
#     df['seeding_score'] = df[['is_short', 'has_pr_keyword', 'has_duplicate']].sum(axis=1)
#     df_clean = df[df['seeding_score'] < 2].copy()
 
#     for col in ['is_short', 'has_pr_keyword', 'has_duplicate', 'seeding_score']:
#         if col in df_clean:
#             df_clean.drop(columns=col, inplace=True)
 
#     return df_clean.to_dict(orient="records")
 
# # ===== Main processing =====
# def preprocessVietnameseLanguage(input_filename):
#     today = date.today()
#     monday_date = today - timedelta(days=today.weekday())
#     sunday_date = monday_date + timedelta(days=6)
 
#     input_filename = os.path.join(input_dir, input_filename) if not input_filename.startswith('/kaggle/input/') else input_filename
#     if not os.path.exists(input_filename):
#         raise FileNotFoundError(f"Input file not found: {input_filename}")
 
#     with open(input_filename, "r", encoding="utf-8") as f:
#         data = json.load(f)
 
#     # --- Translate to Vietnamese ---
#     translator = Translator()
#     for item in tqdm(data, desc="Translating to Vietnamese"):
#         if "content" in item and item["content"].strip():
#             try:
#                 item["content"] = translator.translate(item["content"], dest='vi').text
#             except:
#                 pass  # nếu lỗi dịch thì giữ nguyên
 
#     # --- Preprocess text ---
#     processed_data = []
#     for item in data:
#         content = item.get("content")
#         if not content:
#             continue
#         processed_content = removeBadWord(removeTeencode(removeIcon(content)))
#         if processed_content and processed_content.strip():
#             new_item = dict(item)
#             new_item["content"] = processed_content
#             processed_data.append(new_item)
 
#     # --- Cluster and label ---
#     clustered_data = cluster_comments(processed_data)
 
#     # --- Filter seeding ---
#     clustered_data = filter_seeding(clustered_data)
 
#     # --- Remove comments labeled "rác" ---
#     clustered_data = [item for item in clustered_data if item.get("label") != "rác"]
 
#     # --- Output JSON ---
#     output_filename = f"/kaggle/working/reviews_clustered_{monday_date.strftime('%Y%m%d')}_to_{sunday_date.strftime('%Y%m%d')}.json"
#     with open(output_filename, "w", encoding="utf-8") as f:
#         json.dump(clustered_data, f, ensure_ascii=False, indent=2)
 
#     return output_filename
 
# # ===== Run example =====
# try:
#     input_json = "merged_reviews_20250811_to_20250817.json"
#     output_file = preprocessVietnameseLanguage(input_json)
#     print(f"[SUCCESS] Processing complete. Output: {output_file}")
# except Exception as e:
#     print(f"[ERROR] Failed to process: {str(e)}")