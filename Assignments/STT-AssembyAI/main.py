import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
AUDIO_FILE = "sample.mp3"  # path to your audio file

if not API_KEY:
    raise ValueError("❌ Please set ASSEMBLYAI_API_KEY in your .env file")

# 1️⃣ Upload the audio file
upload_url = "https://api.assemblyai.com/v2/upload"
headers = {"authorization": API_KEY}

with open(AUDIO_FILE, "rb") as f:
    print("Uploading audio...")
    response = requests.post(upload_url, headers=headers, data=f)
    upload_result = response.json()
    audio_url = upload_result["upload_url"]

# 2️⃣ Request transcription
transcript_url = "https://api.assemblyai.com/v2/transcript"
json_data = {"audio_url": audio_url}
response = requests.post(transcript_url, json=json_data, headers=headers)
transcript_id = response.json()["id"]

# 3️⃣ Poll for result
print("Transcribing...")
status_url = transcript_url + "/" + transcript_id
while True:
    status = requests.get(status_url, headers=headers).json()
    if status["status"] == "completed":
        print("\n✅ Transcription Result:")
        print(status["text"])
        break
    elif status["status"] == "error":
        print("❌ Error:", status["error"])
        break
    time.sleep(3)
