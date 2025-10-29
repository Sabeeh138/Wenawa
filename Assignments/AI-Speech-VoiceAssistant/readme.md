# 🧠 Speech-to-Speech Conversational AI Assistant

A **complete end-to-end voice AI system** that listens, understands, thinks, and speaks — just like a human.

It uses:
- 🎧 **Speech Recognition (STT)** via [AssemblyAI](https://www.assemblyai.com/)
- 🤖 **LLM Response Generation** via [Groq API](https://console.groq.com/)
- 🔊 **Speech Synthesis (TTS)** via [Coqui TTS](https://github.com/coqui-ai/TTS)

Developed as part of our AI project research under guidance of **Sir Wasiq Muhammad / Sir Mohi Uddin** and **Miss Kunza Mansoori**.

---

## 🌟 Key Features

✅ Converts speech to text using advanced AI models  
✅ Generates intelligent, contextual, human-like responses  
✅ Speaks back the response in natural voice  
✅ Modular structure — replace or upgrade any component  
✅ Easy to extend into a full chatbot or virtual assistant  

---

## 🧩 Project Architecture

🎙️ User Voice
│
▼
[Speech-to-Text] → AssemblyAI API
│
▼
[Groq LLM] → Natural Language Response Generation
│
▼
[Text-to-Speech] → Coqui TTS
│
▼
🔊 Spoken AI Reply
