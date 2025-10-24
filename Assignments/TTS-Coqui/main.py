from TTS.api import TTS
import sounddevice as sd
import soundfile as sf

# Load a pretrained model (this will download it once)
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=True, gpu=False)

# Ask user for input text
text = input("Enter text to convert to speech: ")

# Generate speech and save to file
output_path = "output.wav"
tts.tts_to_file(text=text, file_path=output_path)

# Play generated audio
data, samplerate = sf.read(output_path)
sd.play(data, samplerate)
sd.wait()

print("Speech generated and played successfully!")
