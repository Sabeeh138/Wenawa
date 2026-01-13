import pyaudio
import websocket
import json
import threading
import time
import wave
from urllib.parse import urlencode
from datetime import datetime
from TTS.api import TTS
import soundfile as sf
import os
import tempfile
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Configuration from stt_assemblyai_stream.py ---
YOUR_API_KEY = "d189e16df426412fa391c9ebe8f58ef0"  # Replace with your actual API key

CONNECTION_PARAMS = {
    "sample_rate": 16000,
    "format_turns": True,  # Request formatted final transcripts
}
API_ENDPOINT_BASE_URL = "wss://streaming.assemblyai.com/v3/ws"
API_ENDPOINT = f"{API_ENDPOINT_BASE_URL}?{urlencode(CONNECTION_PARAMS)}"

# Audio Configuration
FRAMES_PER_BUFFER = 800  # 50ms of audio (0.05s * 16000Hz)
SAMPLE_RATE = CONNECTION_PARAMS["sample_rate"]
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 1024  # For playback

# Global variables for audio stream and websocket
audio = None
stream = None
ws_app = None
audio_thread = None
stop_event = threading.Event()  # To signal the audio thread to stop
pausing_event = threading.Event()  # To pause audio streaming during response playback

# Conversation history
conversation_history = []

# Initialize TTS
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

# --- Functions from tts_generate.py ---
def speak_text(text):
    tmp_path = "audio/output.wav"
    os.makedirs("audio", exist_ok=True)
    tts.tts_to_file(text=text, file_path=tmp_path)
    print("🔊 Speech generated:", tmp_path)
    return tmp_path

# --- Functions from groq_llm.py ---
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

# --- Playback Function ---
def play_wav(file_path):
    wf = wave.open(file_path, 'rb')
    p = pyaudio.PyAudio()
    stream_out = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
        output=True
    )
    data = wf.readframes(CHUNK)
    while data:
        stream_out.write(data)
        data = wf.readframes(CHUNK)
    stream_out.stop_stream()
    stream_out.close()
    p.terminate()
    wf.close()

# --- WebSocket Event Handlers ---
def on_open(ws):
    """Called when the WebSocket connection is established."""
    print("WebSocket connection opened.")
    print(f"Connected to: {API_ENDPOINT}")

    # Start sending audio data in a separate thread
    def stream_audio():
        global stream
        print("Starting audio streaming...")
        while not stop_event.is_set():
            if pausing_event.is_set():
                time.sleep(0.1)
                continue
            try:
                audio_data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                # Send audio data as binary message
                ws.send(audio_data, websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                print(f"Error streaming audio: {e}")
                # If stream read fails, likely means it's closed, stop the loop
                break
        print("Audio streaming stopped.")

    global audio_thread
    audio_thread = threading.Thread(target=stream_audio)
    audio_thread.daemon = True
    audio_thread.start()

def on_message(ws, message):
    global conversation_history
    try:
        data = json.loads(message)
        msg_type = data.get('type')

        if msg_type == "Begin":
            session_id = data.get('id')
            expires_at = data.get('expires_at')
            print(f"\nSession began: ID={session_id}, ExpiresAt={datetime.fromtimestamp(expires_at)}")
        elif msg_type == "Turn":
            transcript = data.get('transcript', '')
            formatted = data.get('turn_is_formatted', False)

            # Clear previous line for formatted messages
            if formatted:
                print('\r' + ' ' * 80 + '\r', end='')
                print("User:", transcript)
                
                # Pause audio input
                pausing_event.set()
                
                # Get LLM response
                response = chat_with_groq(transcript, conversation_history)
                print("AI:", response)
                
                # Update history
                conversation_history.append({"role": "user", "content": transcript})
                conversation_history.append({"role": "assistant", "content": response})
                
                # Synthesize and play
                wav_path = speak_text(response)
                play_wav(wav_path)
                
                # Resume audio input
                pausing_event.clear()
            else:
                print(f"\r{transcript}", end='')
        elif msg_type == "Termination":
            audio_duration = data.get('audio_duration_seconds', 0)
            session_duration = data.get('session_duration_seconds', 0)
            print(f"\nSession Terminated: Audio Duration={audio_duration}s, Session Duration={session_duration}s")
    except json.JSONDecodeError as e:
        print(f"Error decoding message: {e}")
    except Exception as e:
        print(f"Error handling message: {e}")
        pausing_event.clear()  # Ensure resume on error

def on_error(ws, error):
    """Called when a WebSocket error occurs."""
    print(f"\nWebSocket Error: {error}")
    # Attempt to signal stop on error
    stop_event.set()
    pausing_event.clear()

def on_close(ws, close_status_code, close_msg):
    """Called when the WebSocket connection is closed."""
    print(f"\nWebSocket Disconnected: Status={close_status_code}, Msg={close_msg}")

    # Ensure audio resources are released
    global stream, audio
    stop_event.set()  # Signal audio thread just in case it's still running

    if stream:
        if stream.is_active():
            stream.stop_stream()
        stream.close()
        stream = None
    if audio:
        audio.terminate()
        audio = None
    # Try to join the audio thread to ensure clean exit
    if audio_thread and audio_thread.is_alive():
        audio_thread.join(timeout=1.0)

# --- Main Execution ---
def run():
    global audio, stream, ws_app

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Open microphone stream
    try:
        stream = audio.open(
            input=True,
            frames_per_buffer=FRAMES_PER_BUFFER,
            channels=CHANNELS,
            format=FORMAT,
            rate=SAMPLE_RATE,
        )
        print("Microphone stream opened successfully.")
        print("Speak into your microphone. Press Ctrl+C to stop.")
    except Exception as e:
        print(f"Error opening microphone stream: {e}")
        if audio:
            audio.terminate()
        return  # Exit if microphone cannot be opened

    # Create WebSocketApp
    ws_app = websocket.WebSocketApp(
        API_ENDPOINT,
        header={"Authorization": YOUR_API_KEY},
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    # Run WebSocketApp in a separate thread to allow main thread to catch KeyboardInterrupt
    ws_thread = threading.Thread(target=ws_app.run_forever)
    ws_thread.daemon = True
    ws_thread.start()

    try:
        # Keep main thread alive until interrupted
        while ws_thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nCtrl+C received. Stopping...")
        stop_event.set()  # Signal audio thread to stop

        # Send termination message to the server
        if ws_app and ws_app.sock and ws_app.sock.connected:
            try:
                terminate_message = {"type": "Terminate"}
                print(f"Sending termination message: {json.dumps(terminate_message)}")
                ws_app.send(json.dumps(terminate_message))
                # Give a moment for messages to process before forceful close
                time.sleep(5)
            except Exception as e:
                print(f"Error sending termination message: {e}")

        # Close the WebSocket connection (will trigger on_close)
        if ws_app:
            ws_app.close()

        # Wait for WebSocket thread to finish
        ws_thread.join(timeout=2.0)

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        stop_event.set()
        if ws_app:
            ws_app.close()
        ws_thread.join(timeout=2.0)

    finally:
        # Final cleanup (already handled in on_close, but good as a fallback)
        if stream and stream.is_active():
            stream.stop_stream()
        if stream:
            stream.close()
        if audio:
            audio.terminate()
        print("Cleanup complete. Exiting.")

if __name__ == "__main__":
    run()