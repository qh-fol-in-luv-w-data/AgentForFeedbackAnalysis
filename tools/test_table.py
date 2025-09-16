import json
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ====== Đọc dữ liệu JSON ======
with open("data/clean/merged_reviews_20250825_to_20250831.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Gom comment theo label
grouped = defaultdict(list)
for item in data:
    grouped[item["label"]].append(item["content"])

# ====== Chuẩn bị dữ liệu cho bảng ======
styles = getSampleStyleSheet()
header = ["Label", "Comment"]
table_data = [header]

row_spans = []  # để lưu chỉ số hàng cần merge

row_index = 1  # bắt đầu sau header
for label, comments in grouped.items():
    first = True
    start_row = row_index
    for comment in comments:
        if first:
            table_data.append([Paragraph(label, styles["BodyText"]),
                               Paragraph(comment, styles["Normal"])])
            first = False
        else:
            table_data.append(["", Paragraph(comment, styles["Normal"])])
        row_index += 1
    end_row = row_index - 1
    if end_row > start_row:  # có nhiều comment => cần merge cell
        row_spans.append((start_row, end_row))

# ====== Tạo bảng ======
table = Table(table_data, colWidths=[150, 350])

# Style chung
style_cmds = [
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 11),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
]

# Thêm merge cell cho cột Label
for start, end in row_spans:
    style_cmds.append(("SPAN", (0, start), (0, end)))
    style_cmds.append(("VALIGN", (0, start), (0, end), "MIDDLE"))

table.setStyle(TableStyle(style_cmds))

# ====== Xuất PDF ======
doc = SimpleDocTemplate("comments_by_label_merged.pdf", pagesize=A4)
story = [Paragraph("Comments by Label (Merged Labels)", styles["Title"]), Spacer(1, 12), table]
doc.build(story)

print("✅ Đã tạo file comments_by_label_merged.pdf")
