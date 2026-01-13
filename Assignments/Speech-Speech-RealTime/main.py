# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import websocket
import threading
import json
import os
import requests
from TTS.api import TTS
from dotenv import load_dotenv
import asyncio
import time

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

# === CONFIG ===
ASSEMBLYAI_KEY = "d189e16df426412fa391c9ebe8f58ef0"
GROQ_KEY = os.getenv("GROQ_API_KEY")
ASSEMBLYAI_WS = "wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&format_turns=true"

tts = TTS("tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)
conversation_history = []

# === GROQ ===
def chat_with_groq(prompt):
    global conversation_history
    messages = [{"role": "system", "content": "You are a friendly voice assistant. Max 2-3 short sentences."}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": prompt})

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}"},
        json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": 150}
    )
    resp = r.json()["choices"][0]["message"]["content"]
    conversation_history.append({"role": "user", "content": prompt})
    conversation_history.append({"role": "assistant", "content": resp})
    return resp

# === TTS ===
def generate_speech(text):
    os.makedirs("audio", exist_ok=True)
    path = f"audio/{int(time.time() * 1000)}.wav"
    tts.tts_to_file(text=text, file_path=path)
    return "/" + path

# === WebSocket Bridge ===
class AssemblyAIConnection:
    def __init__(self, client_ws: WebSocket):
        self.client_ws = client_ws
        self.aai_ws = None

    async def start(self):
        self.aai_ws = websocket.WebSocketApp(
            ASSEMBLYAI_WS,
            header={"Authorization": ASSEMBLYAI_KEY},
            on_open=self.on_aai_open,
            on_message=self.on_aai_message,
            on_error=self.on_aai_error,
            on_close=self.on_aai_close,
        )
        threading.Thread(target=self.aai_ws.run_forever, daemon=True).start()

    def on_aai_open(self, ws):
        print("AssemblyAI connected")

    async def send_to_client(self, data):
        if self.client_ws.client_state == 1:  # CONNECTED
            await self.client_ws.send_text(data)

    def on_aai_message(self, ws, message):
        data = json.loads(message)
        asyncio.run(self.send_to_client(json.dumps(data)))

        if data.get("type") == "Turn" and data.get("turn_is_formatted"):
            transcript = data["transcript"]
            response = chat_with_groq(transcript)
            audio_url = generate_speech(response)
            asyncio.run(self.send_to_client(json.dumps({
                "type": "assistant_response",
                "text": response,
                "audio_url": audio_url
            })))

    def on_aai_error(self, ws, error):
        print("AAI Error:", error)

    def on_aai_close(self, ws, *args):
        print("AssemblyAI disconnected")

# === FastAPI Routes ===
@app.get("/")
async def root():
    return HTMLResponse(open("static/index.html").read())

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connection = AssemblyAIConnection(ws)
    await connection.start()

    try:
        while True:
            data = await ws.receive_bytes()
            if connection.aai_ws and connection.aai_ws.sock:
                connection.aai_ws.sock.send(data, websocket.ABNF.OPCODE_BINARY)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print("WS Error:", e)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)