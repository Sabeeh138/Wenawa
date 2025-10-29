from stt_assemblyai import speech_to_text
from groq_llm import chat_with_groq
from tts_generate import speak_text

def main():
    print("🎙️ Speak now... (record your voice as 'audio/input.wav')")

    user_text = speech_to_text("audio/input.wav")
    print("🗣️ You said:", user_text)

    ai_response = chat_with_groq(user_text)
    print("🤖 Groq AI:", ai_response)

    speak_text(ai_response)

if __name__ == "__main__":
    main()
