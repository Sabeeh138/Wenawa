# tts_generate.py
from TTS.api import TTS
import soundfile as sf
import os
import tempfile

tts = TTS("tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

def speak_text(text):
    tmp_path = "audio/output.wav"
    os.makedirs("audio", exist_ok=True)
    tts.tts_to_file(text=text, file_path=tmp_path)
    print("🔊 Speech generated:", tmp_path)
    return tmp_path

def synthesize_to_bytes(text):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()
    
    tts.tts_to_file(text=text, file_path=tmp_path)
    
    with open(tmp_path, "rb") as f:
        wav_bytes = f.read()
    
    # Clean up
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
    
    return wav_bytes
