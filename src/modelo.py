from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=1,
    max_tokens=8192,
    top_p=1,
    reasoning_effort="medium",
)
