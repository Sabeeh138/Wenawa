from TTS.api import TTS
import sounddevice as sd
import soundfile as sf

# Load model once globally
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)

def speak_text(text):
    output_path = "audio/output.wav"
    tts.tts_to_file(text=text, file_path=output_path)
    data, samplerate = sf.read(output_path)
    sd.play(data, samplerate)
    sd.wait()
