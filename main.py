
from tools.fetch import fetch
from tools.seeding_filter import seedingFilter
from tools.preprocess import preprocessEnglishLanguage
from langchain_community.chat_models import ChatOllama
from langchain.tools import tool
from langchain.agents import initialize_agent
from langgraph.graph import MessagesState, StateGraph, END, START
from typing_extensions import TypedDict
from langchain_community.chat_models import ChatHuggingFace
from tools.llm import summarizeText


class State (TypedDict):
    request: str
builder = StateGraph (State)
# llm = ChatHuggingFace(pipeline=pipe)
builder.add_node ("fetch", fetch)
builder.add_node ("seeding_filter", seedingFilter)
builder.add_node ("preprocess_vietnamese", preprocessEnglishLanguage)
builder.add_node ("summarize_text", summarizeText)
# builder.add_node("llm", lambda state: {"request": llm.invoke(state["request"]).content})
builder.add_edge ("fetch", "preprocess_vietnamese")
builder.add_edge (START, "fetch")
builder.add_edge ("preprocess_vietnamese", "seeding_filter")
builder.add_edge ("seeding_filter", "summarize_text")
# builder.add_edge("llm", END)
app = builder.compile()
app.invoke ({"request": "Get the latest reviews for Lien Quan Garena on CH play and App store "})
