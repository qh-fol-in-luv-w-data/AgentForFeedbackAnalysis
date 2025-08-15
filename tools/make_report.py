from langgraph.graph import MessagesState
from langchain.schema import AIMessage
import json
import numpy as np
def average_score_analysis(points):
    average = np.mean(points)
    return average
def make_report (state: MessagesState):
    print ("make report")
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
    points  = np.array([row.get("name") for row in data if "name" in row])
    average_point = average_score_analysis (points)
