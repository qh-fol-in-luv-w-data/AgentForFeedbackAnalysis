
from tools.fetch import fetch
from tools.preprocess import preprocessVietnameseLanguage
from langchain_community.chat_models import ChatOllama
from langchain.tools import tool
from langchain.agents import initialize_agent
from langgraph.graph import MessagesState, StateGraph, END, START
from typing_extensions import TypedDict
class State (TypedDict):
    request: str
builder = StateGraph (State)
builder.add_node ("fetch", 
                  fetch)
builder.add_node ("preprocess_vietnamese", preprocessVietnameseLanguage)
builder.add_edge ("fetch", "preprocess_vietnamese")
builder.add_edge (START, "fetch")
app = builder.compile()
app.invoke ({"requst": "Get the latest reviews for Lien Quan Garena on CH play and App store with app id =1150288115"})
