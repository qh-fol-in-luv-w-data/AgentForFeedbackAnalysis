from tools.fetch_app_store import crawl_app_store_reviews_tool
from tools.fetch_ch_play import crawl_ch_play
from tools.preprocess import preprocessVietnameseLanguage
from langchain_community.chat_models import ChatOllama
from langchain.tools import tool
from langchain.agents import initialize_agent
from langgraph.graph import MessagesState, StateGraph, END, START
from typing_extensions import TypedDict
# tools = [
#     crawl_app_store_reviews_tool,
#     crawl_weekly_reviews_tool
# ]
# llm = ChatOllama(
#     model="llama3",   # Must match model you pulled via `ollama pull llama3`
#     temperature=0
# )
# agent = initialize_agent(
#     tools=tools,
#     llm=llm,
#     agent="zero-shot-react-description",
#     verbose=True
# )

# response = agent.run("Get the latest reviews for Lien Quan Garena on CH play and App store with app id =1150288115")
# print(response)
# raw sau get, preprocess sau preprocess, clean sau seeding
class State (TypedDict):
    request: str
builder = StateGraph (State)
builder.add_node ("crawl_ch_play", 
                  crawl_ch_play)
builder.add_node ("preprocess_vietnamese", preprocessVietnameseLanguage)
builder.add_node ("crawl_app_store",
                  crawl_app_store_reviews_tool)
builder.add_edge ("crawl_app_store", "preprocess_vietnamese")
builder.add_edge (START, "crawl_ch_play")
builder.add_edge ("crawl_ch_play", "crawl_app_store")
app = builder.compile()
app.invoke ({"requst": "Get the latest reviews for Lien Quan Garena on CH play and App store with app id =1150288115"})
