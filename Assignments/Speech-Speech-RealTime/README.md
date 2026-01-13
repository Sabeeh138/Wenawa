# Real-Time AI Voice Agent

This project is a real-time AI voice assistant that integrates Speech-to-Text (STT), a Large Language Model (LLM), and Text-to-Speech (TTS) to carry out natural voice conversations.

## Features

- **Real-time Speech-to-Text**: Uses AssemblyAI's streaming API for accurate and low-latency transcription.
- **Intelligent Responses**: Leverages Groq API (Llama 3.3 70b) for fast and natural AI responses.
- **Text-to-Speech**: Uses Coqui TTS (`tacotron2-DDC`) to convert AI text responses back into speech.
- **Interactive Web Interface**: A simple frontend to interact with the voice agent.

## Tech Stack

- **Backend**: Python, FastAPI, WebSockets
- **Frontend**: HTML, JavaScript
- **AI Services**:
  - STT: AssemblyAI
  - LLM: Groq (Llama 3)
  - TTS: Coqui TTS

## Prerequisites

- Python 3.8 or higher
- [Groq API Key](https://console.groq.com/)
- [AssemblyAI API Key](https://www.assemblyai.com/)

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory.

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: You may need to install system dependencies for `sounddevice` (e.g., `libportaudio2` on Linux).*

3. **Configuration**:
   - Create a `.env` file in the root directory.
   - Add your Groq API key:
     ```env
     GROQ_API_KEY=your_groq_api_key_here
     ```
   - *Note*: The AssemblyAI API key is currently configured in `main.py`. You may update it directly there or modify the code to load it from `.env`.

## Usage

1. **Start the Server**:
   You can run the application using `uvicorn`:
   ```bash
   uvicorn main:app --reload
   ```
   Or run the Python script directly if configured:
   ```bash
   python main.py
   ```

2. **Access the Interface**:
   - Open your web browser and navigate to `http://localhost:8000`.
   - Allow microphone access when prompted.
   - Start speaking to interact with the AI agent.

## Project Structure

- `main.py`: Main entry point for the FastAPI application and WebSocket handling.
- `groq_llm.py`: Logic for interacting with the Groq LLM API.
- `tts_generate.py`: Handles Text-to-Speech generation.
- `stt_assemblyai_stream.py`: Standalone script/module for AssemblyAI streaming (used for testing or specific logic).
- `static/`: Contains frontend assets (`index.html`, `script.js`, `style.css`).
- `audio/`: Directory where generated audio files are stored.
