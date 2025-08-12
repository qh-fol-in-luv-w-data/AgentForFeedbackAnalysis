from tools.fetch_app_store import crawl_app_store_reviews_tool
from tools.fetch_ch_play import crawl_weekly_reviews_tool
from langchain_community.chat_models import ChatOllama
from langchain.tools import tool
from langchain.agents import initialize_agent
tools = [
    crawl_app_store_reviews_tool,
    crawl_weekly_reviews_tool
]
llm = ChatOllama(
    model="llama3",   # Must match model you pulled via `ollama pull llama3`
    temperature=0
)
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

response = agent.run("Get the latest reviews for Lien Quan Garena on CH play and App store")
print(response)