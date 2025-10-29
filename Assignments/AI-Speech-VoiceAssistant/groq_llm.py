import os, requests
from dotenv import load_dotenv

load_dotenv()

def chat_with_groq(prompt):
    api_key = os.getenv("GROQ_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a helpful and conversational AI assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    response_json = resp.json()
    return response_json["choices"][0]["message"]["content"]
