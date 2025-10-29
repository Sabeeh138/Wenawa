import os, requests
from dotenv import load_dotenv

load_dotenv()

def speech_to_text(audio_path="audio/input.wav"):  # ✅ Default path
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    headers = {"authorization": api_key}

    # Upload audio file
    with open(audio_path, "rb") as f:
        response = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=f)
    upload_url = response.json()["upload_url"]

    # Request transcription
    json_data = {"audio_url": upload_url}
    response = requests.post("https://api.assemblyai.com/v2/transcript", headers=headers, json=json_data)
    transcript_id = response.json()["id"]

    print("🎧 Transcribing... please wait")

    # Wait until completed
    while True:
        polling = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
        status = polling.json()["status"]
        if status == "completed":
            return polling.json()["text"]
        elif status == "error":
            raise Exception("Transcription failed:", polling.json()["error"])
