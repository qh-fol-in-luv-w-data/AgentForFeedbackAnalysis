from langgraph.graph import MessagesState
from langchain.schema import AIMessage
import json
import numpy as np
import os
from openai import OpenAI
from collections import defaultdict
from tqdm import tqdm 
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import date, timedelta
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.widgets.markers import makeMarker
from collections import Counter
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv
load_dotenv()

TITLE_BLUE = colors.Color(0/255, 102/255, 204/255) 
NAVY_BLUE = colors.Color(0/255, 0/255, 128/255)   
POS_GREEN = colors.Color(34/255, 139/255, 34/255) 
NEG_RED = colors.Color(178/255, 34/255, 34/255)    
SUG_YELLOW = colors.Color(255/255, 140/255, 0/255) 
 

sections = []
 
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    name='TitleStyle',
    parent=styles['Title'],
    fontSize=18,
    textColor=TITLE_BLUE,
    spaceAfter=12
)
section_style = ParagraphStyle(
    name='SectionStyle',
    parent=styles['Heading2'],
    fontSize=14,
    textColor=NAVY_BLUE,
    spaceBefore=12,
    spaceAfter=6
)
review_count_style = ParagraphStyle(
    name='ReviewCountStyle',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.black,
    spaceAfter=6
)
positive_style = ParagraphStyle(
    name='PositiveStyle',
    parent=styles['Heading3'],
    fontSize=12,
    textColor=POS_GREEN,
    spaceBefore=10,
    spaceAfter=6
)
negative_style = ParagraphStyle(
    name='NegativeStyle',
    parent=styles['Heading3'],
    fontSize=12,
    textColor=NEG_RED,
    spaceBefore=10,
    spaceAfter=6
)
suggestion_style = ParagraphStyle(
    name='SuggestionStyle',
    parent=styles['Heading3'],
    fontSize=12,
    textColor=SUG_YELLOW,
    spaceBefore=10,
    spaceAfter=6
)
body_style = ParagraphStyle(
    name='BodyStyle',
    parent=styles['Normal'],
    fontSize=10,
    leading=12,
    spaceAfter=4,
    leftIndent=15
)
def send_email_report(receiver_email, subject, body, pdf_file):
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")  # Gmail App Password

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_file, "rb") as f:
        mime = MIMEBase("application", "octet-stream")
        mime.set_payload(f.read())
        encoders.encode_base64(mime)
        mime.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_file)}")
        msg.attach(mime)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print(f"✅ Email đã gửi đến {receiver_email}")
    except Exception as e:
        print(f"❌ Lỗi gửi mail: {e}")
def format_bullet_text(text):
    return text.replace('\n- ', '<br/>- ').replace('- ', '<br/>- ')

def makeReport (dateDataPath, results, scores, total, percenPosi, percentCheat, percentFeed, percentProb):
    today = date.today()
    monday_date = today - timedelta(days=today.weekday())  # Monday=0
    sunday_date = monday_date + timedelta(days=6)
    with open(dateDataPath, "r", encoding="utf-8") as f:
        dateData = json.load(f)
    day_counts = Counter(item['day_of_week'] for item in dateData)
    WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_counts_complete = {day: day_counts.get(day, 0) for day in WEEKDAYS}

    # # Output
    # for day, count in day_counts_complete.items():
    #     print(f"{day}: {count}")

    drawing = Drawing(400, 200)

    bar = VerticalBarChart()
    bar.x = 50
    bar.y = 30
    bar.height = 125
    bar.width = 300
    bar.data = [list(day_counts_complete.values())]
    

    bar.strokeColor = colors.black

    bar.valueAxis.valueMin = 0
    bar.valueAxis.valueMax = max( day_counts_complete.values()) + 5  
    bar.valueAxis.valueStep = max(1, (max( day_counts_complete.values()) // 5))

    bar.categoryAxis.labels.boxAnchor = 'ne'
    bar.categoryAxis.labels.dx = 8
    bar.categoryAxis.labels.dy = -2
    bar.categoryAxis.categoryNames = WEEKDAYS

    drawing.add(bar)

    # Optional: Add a label
    label = Label()
    label.setOrigin(200, 180)
    label.boxAnchor = 'n'
    label.setText("Number of Reviews per Day")
    label.fontSize = 12
    drawing.add(label)
    story = []
    # Add chart to story
    
    pdf_file = f"/home/hqvu/Agent_analysis/data/report/Feedback_Analysis_{monday_date.strftime('%Y%m%d')}_to_{sunday_date.strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, leftMargin=1*inch, rightMargin=1*inch, topMargin=1*inch, bottomMargin=1*inch)
  
    story.append(Paragraph("WEEKLY FEEDBACK ANALYSIS", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append (Paragraph("Hi, ", styles['Normal']))
    story.append (Paragraph
                   (f"I hope you're doing well! Please find below your weekly feedback analysis report for the period of {monday_date} to {sunday_date}. This report summarizes key trends, insights, and any action points identified from your customer feedback during this period.", styles['Normal']))
    story.append(Spacer(0.5, 0.1*inch))
    story.append(Paragraph("Overall summary of weekly feedback", section_style))
    story.append (Paragraph(f"Total feedback received: {total}", styles['Normal']))
    story.append(Paragraph(f"Positive feedback: {round(percenPosi, 2)} %", styles['Normal']))
    story.append(Paragraph(f"Game problems feedback: {round(percentProb, 2)} %", styles['Normal']))
    story.append(Paragraph(f"New feature request feedback: {round(percentFeed, 2)} %", styles['Normal']))
    story.append(Paragraph(f"Cheating report feedback: {round(percentCheat, 2)} %", styles['Normal']))
    story.append(Paragraph(f"Average score: {round(scores, 2)}/5", styles['Normal']))
    story.append(drawing)
    story.append(Spacer(0.5, 0.1*inch))
    story.append(Paragraph("Key Trends & Insights", section_style))
    pos_header = "**1. Positive aspects**"
    neg_header = "**2. Negative aspects / bugs**  "
    sug_header = "**3. Suggestions**"

    pos_start = results.find(pos_header)
    neg_start = results.find(neg_header)
    sug_start = results.find(sug_header)

    positive_text = results[pos_start + len(pos_header):neg_start].strip() if pos_start != -1 and neg_start != -1 else ""
    negative_text = results[neg_start + len(neg_header):sug_start].strip() if neg_start != -1 and sug_start != -1 else ""
    suggestions_text = results[sug_start + len(sug_header):].strip() if sug_start != -1 else ""
    positive_text = format_bullet_text(positive_text)
    negative_text = format_bullet_text(negative_text)
    suggestions_text = format_bullet_text(suggestions_text) 
    story.append(Paragraph("Positive aspects", suggestion_style))
    story.append(Paragraph(positive_text, body_style))
    story.append(Paragraph("Bugs found aspects", suggestion_style))
    story.append(Paragraph(negative_text, body_style))
    story.append(Paragraph("Suggestion aspects", suggestion_style))
    story.append(Paragraph(suggestions_text, body_style))
    try:
        doc.build(story)
        print(f"PDF report generated: {pdf_file}")
        subject = "Weekly Feedback Analysis Report"
        body = f"Dear team,\n\nPlease find attached the weekly feedback analysis report for {monday_date} to {sunday_date}.\n\nBest regards,\nYour Bot"
        send_email_report("hodacquan2004@gmail.com", subject, body, pdf_file)
    except Exception as e:
        print(e)
        traceback.print_exc()
    
def format_as_bullets(texts, max_chars=4000):
    bullets = ["- " + t.replace("\n", " ").strip() for t in texts if t.strip()]
    s = "\n".join(bullets)
    return s[:max_chars]
def getFromCluster(data):
    gameProblem = [item["content"] for item in data if item.get("label") in ["bug report", "game problem", "game error", "game not working"]]
    cheating = [item["content"] for item in data if item.get("label") == "cheating or hacking report"]
    posi = [item["content"] for item in data if item.get("label") == "positive feedback"]
    featureRequest = [item["content"] for item in data if item.get("label") == "feature request"]
    return gameProblem, cheating, posi, featureRequest

def callOpenAI (state: MessagesState):
    print ("make report")
    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages found in state")
    last_msg = messages[-1]
    if isinstance(last_msg, AIMessage):
        filename = last_msg.content
        SCORES = last_msg.additional_kwargs.get("average_score")
        total = last_msg.additional_kwargs.get("total_review")
    else:
        raise ValueError("Last message is not an AIMessage containing the JSON file path") 
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    print (os.getenv("OPENAI_API_KEY"))
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    gameProblem, cheating, posi, featureRequest = getFromCluster (data)
    cluster = [
    ("game problem", gameProblem),
    ("cheating", cheating),
    ("positive feedback", posi),
    ("feature request", featureRequest)
    ]
    percenPosi = (len (posi)/len (data))* 100
    percenProblem = (len (gameProblem)/ len(data))* 100
    percenCheat = (len (cheating)/ len(data))* 100
    percenFeature = (len (featureRequest)/ len(data))* 100
    BATCH_SIZE = 30
    MAP_MAX_CHARS, REDUCE_MAX_CHARS = 4000, 4000
    MAP_MAX_TOKENS, REDUCE_MAX_TOKENS = 220, 280
    results = []
    for label, texts in tqdm(cluster, desc="Summarizing (OpenAI GPT)"):
        mini_summaries = []

        for i in range(0, len(texts), BATCH_SIZE):

            batch = texts[i:i+BATCH_SIZE]

            inp = format_as_bullets(batch, max_chars=MAP_MAX_CHARS)

            prompt = make_map_prompt(inp)

            mini = run_openai(prompt, client, max_tokens=MAP_MAX_TOKENS).split("Summary:")[-1].strip()

            if mini:

                mini_summaries.append(mini)

        reduce_inp = format_as_bullets(mini_summaries, max_chars=REDUCE_MAX_CHARS)

        final = run_openai(make_reduce_prompt(reduce_inp), client,  max_tokens=REDUCE_MAX_TOKENS).split("Final summary:")[-1].strip()
    
        results.extend (final)
    final = format_as_bullets(results, max_chars=REDUCE_MAX_CHARS)
    prompt = make_reduce_prompt(final)
    final_summary = run_openai(prompt, client, max_tokens=REDUCE_MAX_TOKENS).split("Final summary:")[-1].strip()
    print (final_summary)
    with open("/home/hqvu/Agent_analysis/data/clean/summaries_openai.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    makeReport (filename, final_summary,  SCORES, total, percenPosi, percenCheat, percenFeature, percenProblem)
 
def run_openai(prompt, client, max_tokens=220):

    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        messages=[{"role": "user", "content": prompt}],

        temperature=0.7,

        max_tokens=max_tokens

    )

    return response.choices[0].message.content.strip()

def make_reduce_prompt(bulleted):

    return (

        "You are merging partial summaries of player reviews. Combine overlapping points, "

        "remove redundancy, and produce a final structured summary with 3 sections:\n"

        "1. Positive aspects\n"

        "2. Negative aspects / bugs\n"

        "3. Suggestions\n\n"

        "Be concise but keep important details.\n\n"

        "Partial summaries:\n" + bulleted + "\n\nFinal summary:"

    )

def make_map_prompt(bulleted):

    return (

        "You are analyzing player reviews. Summarize them into 3 clear sections:\n"

        "1. Positive aspects (what players like or praise)\n"

        "2. Negative aspects / bugs / frustrations\n"

        "3. Suggestions or feature requests\n\n"

        "Be specific, avoid generic phrasing. Do not copy sentences, synthesize them.\n\n"

        "Reviews:\n" + bulleted + "\n\nSummary:"

    )                                                                              