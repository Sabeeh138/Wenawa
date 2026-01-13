import os
import requests
from dotenv import load_dotenv

load_dotenv()

def chat_with_groq(prompt, conversation_history=None):
    """
    Chat with Groq LLM
    
    Args:
        prompt: User's message
        conversation_history: List of {"role": "user/assistant", "content": "..."} 
    """
    api_key = os.getenv("GROQ_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json"
    }

    # Build messages with history
    messages = [
        {"role": "system", "content": "You are a friendly, conversational AI assistant. Keep your responses concise and natural for voice conversation - aim for 2-3 sentences maximum."}
    ]
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current prompt
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 150  # Keep responses short for voice
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions", 
        headers=headers, 
        json=data
    )
    resp_json = response.json()

    if "choices" not in resp_json:
        print("❌ Groq Error:", resp_json)
        return "Sorry, I had trouble generating a response."

    return resp_json["choices"][0]["message"]["content"]