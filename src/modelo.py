from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=1,
    max_tokens=8192,
)
