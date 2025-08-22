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
 
def makeReport (results, scores):
    for key, value in results.items():
        try:
            final_summary = value.get("final_summary", "")
            positive_items = []
            if "1. Positive aspects" in final_summary:
                positive_split = final_summary.split("2. Negative")[0].replace("1. Positive aspects\n", "").strip()
                positive_items = positive_split.split("\n- ")[1:] if positive_split and "\n- " in positive_split else positive_split.split("- ") if positive_split else []
                positive_items = [item.strip() for item in positive_items if item.strip()]
            else:
                positive_items = ["No positive aspects recorded."]
            negative_items = []
            if "2. Negative aspects / bugs" in final_summary:
                negative_section = final_summary.split("2. Negative aspects / bugs")[1].strip()
                negative_split = negative_section.split("3. Suggestions")[0].strip() if "3. Suggestions" in negative_section else negative_section
                negative_items = negative_split.split("\n- ")[1:] if negative_split and "\n- " in negative_split else negative_split.split("- ") if negative_split else []
                negative_items = [item.strip() for item in negative_items if item.strip()]
            else:
                negative_items = ["No negative aspects or bugs recorded."]
            suggestions_items = []
            if "3. Suggestions" in final_summary:
                suggestions_split = final_summary.split("3. Suggestions")[1].strip()
                suggestions_items = suggestions_split.split("\n- ")[1:] if suggestions_split and "\n- " in suggestions_split else suggestions_split.split("- ") if suggestions_split else []
                suggestions_items = [item.strip() for item in suggestions_items if item.strip()]
            else:
                suggestions_items = ["No suggestions recorded."]
    
            sections.append({
                "label": key.upper(), 
                "num_reviews": value.get("num_reviews", 0),
                "positive": positive_items,
                "negative": negative_items,
                "suggestions": suggestions_items
            })
        except (IndexError, KeyError) as e:
            print(f"Warning: Failed to parse section '{key}' due to error: {str(e)}. Skipping this section.")
            continue
    today = date.today()
    monday_date = today - timedelta(days=today.weekday())  # Monday=0
    sunday_date = monday_date + timedelta(days=6)
    pdf_file = f"/home/hqvu/Agent_analysis/data/report/Feedback_Analysis_{monday_date.strftime('%Y%m%d')}_to_{sunday_date.strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, leftMargin=1*inch, rightMargin=1*inch, topMargin=1*inch, bottomMargin=1*inch)
    story = []
  
    story.append(Paragraph("FEEDBACK ANALYSIS", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    for i, section in enumerate(sections):
        if i > 0:  
            story.append(PageBreak())
        story.append(Paragraph(section["label"], section_style))
        story.append(Paragraph(f"Number of reviews: {section['num_reviews']}", review_count_style))
        story.append(Paragraph("[Positive] Positive Aspects", positive_style))
        for item in section["positive"]:
            story.append(Paragraph(f"• {item}", body_style))
        story.append(Paragraph("[Negative] Negative Aspects / Bugs", negative_style))
        for item in section["negative"]:
            story.append(Paragraph(f"• {item}", body_style))
        story.append(Paragraph("[Suggestions] Suggestions", suggestion_style))
        for item in section["suggestions"]:
            story.append(Paragraph(f"• {item}", body_style))
        story.append(Spacer(1, 0.3*inch))
    try:
        doc.build(story)
        print(f"PDF report generated: {pdf_file}")
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
    
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

    BATCH_SIZE = 30
    MAP_MAX_CHARS, REDUCE_MAX_CHARS = 4000, 4000
    MAP_MAX_TOKENS, REDUCE_MAX_TOKENS = 220, 280
    results = {}
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
    
        results[label] = {

            "label": label,

            "num_reviews": len(texts),

            "mini_summaries": mini_summaries,

            "final_summary": final
        }
    with open("/home/hqvu/Agent_analysis/data/clean/summaries_openai.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    makeReport (results, SCORES)
 
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
 

     