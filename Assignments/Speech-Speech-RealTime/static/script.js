const chat = document.getElementById("chat");
const partial = document.getElementById("partial");
const status = document.getElementById("status");
const micBtn = document.getElementById("micBtn");

let ws = null;
let audioContext = null;
let scriptNode = null;
let stream = null;

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

micBtn.onclick = async () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    // Stop
    if (audioContext) audioContext.close();
    if (stream) stream.getTracks().forEach(t => t.stop());
    ws.close();
    micBtn.classList.remove("recording");
    status.textContent = "Click microphone to start";
    partial.textContent = "";
    return;
  }

  // Start
  ws = new WebSocket("ws://" + location.host + "/ws");
  status.textContent = "Connecting...";
  micBtn.classList.add("recording");

  ws.onopen = async () => {
    status.textContent = "Listening...";
    await startMicrophone();
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // Partial transcript
    if (data.type === "Turn" && !data.turn_is_formatted) {
      partial.textContent = "You: " + (data.transcript || "");
    }

    // Final user turn
    if (data.type === "Turn" && data.turn_is_formatted) {
      partial.textContent = "";
      addMessage(data.transcript, "user");
    }

    // Assistant response
    if (data.type === "assistant_response") {
      status.textContent = "Speaking...";
      addMessage(data.text, "assistant");
      const audio = new Audio(data.audio_url + "?t=" + Date.now());
      audio.onended = () => status.textContent = "Listening...";
      audio.play();
    }
  };

  ws.onclose = () => {
    status.textContent = "Click microphone to start";
    micBtn.classList.remove("recording");
    partial.textContent = "";
  };
};

async function startMicrophone() {
  stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      sampleRate: 16000,
      echoCancellation: true,
      noiseSuppression: true
    }
  });

  audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
  const source = audioContext.createMediaStreamSource(stream);

  // ScriptProcessor is deprecated but still the simplest cross-browser way for raw PCM
  scriptNode = audioContext.createScriptProcessor(4096, 1, 1);

  scriptNode.onaudioprocess = (e) => {
    if (ws.readyState !== WebSocket.OPEN) return;
    const floatSamples = e.inputBuffer.getChannelData(0);
    const int16 = new Int16Array(floatSamples.length);
    for (let i = 0; i < floatSamples.length; i++) {
      let s = Math.max(-1, Math.min(1, floatSamples[i]));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    ws.send(int16.buffer);
  };

  source.connect(scriptNode);
  scriptNode.connect(audioContext.destination); // mute local echo → remove this line if you want to hear yourself
  await audioContext.resume();
}