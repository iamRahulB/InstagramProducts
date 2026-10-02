# It's the OpenAI SDK you already know — just change the base URL.
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8081/v1", api_key="not-needed")

client.chat.completions.create(
    model="chatgpt-browser",                       # or "gemini-browser"
    messages=[{"role": "user", "content": "Write a haiku about local-first AI."}],
)