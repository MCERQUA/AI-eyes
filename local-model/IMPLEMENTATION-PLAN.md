# Local TTS Implementation Plan

## Server Constraints
- **CPU:** 4 vCPU
- **RAM:** 8GB
- **GPU:** None
- **Current Load:** Flask server + DeepFace + SQLite

---

## Phase 1: Basic Piper TTS (Start Here)

### Goal
Get any local TTS running as proof of concept.

### Steps

#### Option A: Binary Installation (Fastest - No Python needed!)

```bash
cd /home/mike/Mike-AI/ai-eyes/local-model

# Download Piper binary (AMD64 Linux)
wget "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz"
tar xzvf piper_amd64.tar.gz

# Download voice model (British male - good for sarcastic AI!)
cd piper
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json"

# Test with real-time playback!
echo "What do you want now? I was in the middle of something important." | \
  ./piper --model en_GB-alan-medium.onnx --output-raw | \
  aplay -r 24000 -f S16_LE -t raw -

# Or save to file
echo "What do you want now?" | \
  ./piper --model en_GB-alan-medium.onnx --output_file test.wav
```

#### Option B: Python Installation (pip)

```bash
cd /home/mike/Mike-AI/ai-eyes/local-model
python3 -m venv venv
source venv/bin/activate
pip install piper-tts
```

#### Download Voice Models

```bash
mkdir -p voices
cd voices

# British male - Alan (recommended for sarcastic AI voice)
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json"

# American male - Lessac (clear, professional)
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

# American male - Joe (casual, could work)
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/joe/medium/en_US-joe-medium.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/joe/medium/en_US-joe-medium.onnx.json"
```

See all voices: https://rhasspy.github.io/piper-samples/

#### Test CLI (Python version)
```bash
source venv/bin/activate

# Save to file
echo "What do you want now? I was in the middle of something important." | \
  piper --model voices/en_GB-alan-medium.onnx --output_file test.wav

# Real-time playback (raw audio stream)
echo "What do you want now?" | \
  piper --model voices/en_GB-alan-medium.onnx --output-raw | \
  aplay -r 24000 -f S16_LE -t raw -

# Play the saved file
aplay test.wav
# or
ffplay -nodisp -autoexit test.wav
```

#### 1.4 Create Flask Endpoint
Create `tts_server.py`:
```python
from flask import Flask, request, send_file, jsonify
import subprocess
import tempfile
import os
import time

app = Flask(__name__)

MODEL_PATH = "/home/mike/Mike-AI/ai-eyes/local-model/voices/en_US-lessac-medium.onnx"

@app.route('/api/local-tts', methods=['POST', 'GET'])
def local_tts():
    text = request.args.get('text') or request.json.get('text', '')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    start = time.time()

    # Create temp file for output
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        output_path = f.name

    try:
        # Run piper
        process = subprocess.Popen(
            ['piper', '--model', MODEL_PATH, '--output_file', output_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        process.communicate(input=text.encode())

        latency = time.time() - start

        # Return audio file
        response = send_file(output_path, mimetype='audio/wav')
        response.headers['X-TTS-Latency'] = str(latency)
        return response

    finally:
        # Cleanup temp file after sending
        if os.path.exists(output_path):
            os.remove(output_path)

@app.route('/api/local-tts/health')
def health():
    return jsonify({
        "status": "ok",
        "model": MODEL_PATH,
        "engine": "piper"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
```

#### 1.5 Test the Endpoint
```bash
# Run the server
source venv/bin/activate
python tts_server.py &

# Test it
curl -X POST "http://localhost:5001/api/local-tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is Pi-Guy testing local TTS."}' \
  --output test.wav

# Check latency
curl -v "http://localhost:5001/api/local-tts?text=Test" --output /dev/null 2>&1 | grep X-TTS-Latency
```

---

## Phase 2: Integrate with Main Server

### Option A: Add to Existing server.py
Add the TTS endpoint directly to the main Flask server.

### Option B: Run as Separate Microservice
Keep TTS on port 5001, main server on 5000.
Pros: Isolation, can restart TTS without affecting main server.

### Integration Code (for server.py)
```python
import subprocess
import tempfile

PIPER_MODEL = "/home/mike/Mike-AI/ai-eyes/local-model/voices/en_US-lessac-medium.onnx"
PIPER_VENV = "/home/mike/Mike-AI/ai-eyes/local-model/venv/bin/piper"

@app.route('/api/local-tts', methods=['POST', 'GET'])
def local_tts():
    text = request.args.get('text') or request.json.get('text', '')
    if not text:
        return jsonify({"error": "No text provided"}), 400

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        output_path = f.name

    try:
        process = subprocess.Popen(
            [PIPER_VENV, '--model', PIPER_MODEL, '--output_file', output_path],
            stdin=subprocess.PIPE
        )
        process.communicate(input=text.encode())
        return send_file(output_path, mimetype='audio/wav')
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
```

---

## Phase 3: Frontend Toggle

### Add UI Switch
```html
<!-- In index.html controls -->
<label>
  <input type="checkbox" id="localTTSToggle" onchange="toggleTTSMode()">
  Use Local TTS (experimental)
</label>
```

### JavaScript
```javascript
let useLocalTTS = false;

function toggleTTSMode() {
    useLocalTTS = document.getElementById('localTTSToggle').checked;
    console.log('Local TTS:', useLocalTTS ? 'ON' : 'OFF');
}

// When receiving text from agent, if local TTS is on:
async function playLocalTTS(text) {
    const response = await fetch('/api/local-tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });

    if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
    }
}
```

---

## Phase 4: Voice Cloning (Advanced)

### Option A: Use XTTS-v2 for Zero-Shot

#### Install
```bash
pip install coqui-tts torch torchaudio
```

#### Create Reference Audio
Export ~10 seconds of Pi-Guy voice from ElevenLabs as reference.

#### Code
```python
from TTS.api import TTS

# Load model (first time will download ~2GB)
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

# Generate with cloned voice
tts.tts_to_file(
    text="What the hell do you want now?",
    speaker_wav="piguy_reference.wav",
    language="en",
    file_path="output.wav"
)
```

**Note:** This will be SLOW on CPU (maybe 5-10x realtime). Only use for non-realtime scenarios or testing.

### Option B: Train Custom Piper Voice

#### Step 1: Generate Training Data
Use ElevenLabs to generate 1000+ phrases in Pi-Guy's voice.

#### Step 2: Prepare Dataset
```
dataset/
├── metadata.csv  # format: filename|text
├── wav/
│   ├── 001.wav
│   ├── 002.wav
│   └── ...
```

#### Step 3: Train on Cloud GPU
Use Google Colab or Vast.ai to run Piper training.

#### Step 4: Deploy Model
Copy trained .onnx model to server.

---

## Phase 5: Full Local Voice Agent (Future)

### Architecture
```
User Speech
    ↓
[Whisper/faster-whisper STT]  ← Local or API
    ↓
[LLM API - Claude/GPT/etc]    ← Keep as API for quality
    ↓
[Local Piper TTS]             ← Local!
    ↓
Audio Output
```

### Components Needed
1. **STT:** faster-whisper (local) or keep ElevenLabs
2. **LLM:** Keep API (Claude, GPT, etc.)
3. **TTS:** Piper (local)
4. **Transport:** WebSocket/WebRTC
5. **VAD:** Voice Activity Detection

### Framework Options
- **Pipecat:** Full voice agent framework
- **LiveKit Agents:** Real-time voice with WebRTC
- **Custom:** Build with Flask + WebSockets

---

## Benchmarks to Run

### Test Commands
```bash
# Benchmark Piper latency
time echo "This is a test of the local text to speech system." | \
  piper --model voices/en_US-lessac-medium.onnx --output_file /dev/null

# Measure with Python
python3 -c "
import subprocess
import time

text = 'What do you want now? I was in the middle of something important.'
start = time.time()
subprocess.run(['piper', '--model', 'voices/en_US-lessac-medium.onnx', '--output_file', 'test.wav'],
               input=text.encode(), capture_output=True)
print(f'Latency: {time.time() - start:.3f}s')
"
```

### Expected Results
- Piper medium voice: ~100-300ms for short sentences
- XTTS-v2 on CPU: ~2-5 seconds for same text
- ElevenLabs API: ~300-800ms (network dependent)

---

## Files to Create

```
local-model/
├── RESEARCH.md          ✅ Created
├── IMPLEMENTATION-PLAN.md  ✅ This file
├── venv/                # Virtual environment
├── voices/              # Piper voice models
│   ├── en_US-lessac-medium.onnx
│   └── en_US-lessac-medium.onnx.json
├── tts_server.py        # Standalone TTS server
├── test_tts.py          # Test script
└── piguy_reference.wav  # (Future) Voice reference for cloning
```

---

## Quick Start Checklist

- [ ] Create venv and install piper-tts
- [ ] Download voice model
- [ ] Test CLI synthesis
- [ ] Create Flask endpoint
- [ ] Benchmark latency
- [ ] Add to main server or run as microservice
- [ ] Test end-to-end
- [ ] (Optional) Add frontend toggle
- [ ] (Optional) Test voice cloning with XTTS-v2
- [ ] (Optional) Train custom Piper voice
