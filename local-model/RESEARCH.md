# Local TTS Research for Pi-Guy Voice Agent

**Server Specs:** 4 vCPU, 8GB RAM, NO GPU

**Research Date:** November 2025

---

## TL;DR - Best Options for Our Setup

| Model | Size | CPU Performance | Quality | Recommendation |
|-------|------|-----------------|---------|----------------|
| **Piper TTS** | 5-60MB | Excellent (10x realtime) | Good | **Phase 1: Start Here** |
| **KittenTTS** | <25MB | Excellent | Good | Alternative for Phase 1 |
| **Kokoro** | ~350MB | Good (3-11x realtime) | Very Good | Phase 2: Better quality |
| **MeloTTS** | Medium | Good | Good | Alternative |
| **Orpheus-150M** | ~600MB | Fair | Excellent | Phase 3: If memory allows |

---

## Phase 1: Basic TTS (Piper) - RECOMMENDED START

### Why Piper?
- **Specifically optimized for CPU-only devices** (Raspberry Pi 4/5)
- **Super fast:** 10x realtime on CPU
- **Tiny models:** 5-60MB per voice
- **MIT License:** Commercial use OK
- **Python package:** `pip install piper-tts`
- **ONNX runtime:** Efficient inference
- **Streaming support:** Can output audio as it generates

### Installation
```bash
# Create virtual environment
python3 -m venv /home/mike/Mike-AI/ai-eyes/local-model/venv
source /home/mike/Mike-AI/ai-eyes/local-model/venv/bin/activate

# Install Piper
pip install piper-tts

# Download a voice model (e.g., en_US-lessac-medium)
# Models: https://huggingface.co/rhasspy/piper-voices
```

### Voice Models for Piper
Quality levels: `x_low`, `low`, `medium`, `high`
- **x_low:** ~5MB, fastest, robotics-acceptable
- **medium:** ~60MB, good quality for voice agents
- **high:** ~100MB, best quality

Recommended starting voices:
- `en_US-lessac-medium` - Clear American male
- `en_GB-alan-medium` - British male (could work for Pi-Guy)
- `en_US-joe-medium` - American male, casual tone

### Basic Usage
```python
import subprocess

def speak_piper(text, output_file="output.wav"):
    cmd = f'echo "{text}" | piper --model en_US-lessac-medium --output_file {output_file}'
    subprocess.run(cmd, shell=True)
```

---

## Phase 2: Better Quality (Kokoro)

### Why Kokoro?
- **82M parameters** - Small but high quality
- **Apache 2.0 license** - Commercial OK
- **3-11x realtime on CPU** - Still fast enough
- **Near state-of-the-art quality** at this size
- **~350MB total size**

### Installation
```bash
pip install kokoro
```

### Usage
```python
from kokoro import generate

audio = generate("Hello, this is Pi-Guy speaking.", voice="af")
```

### Considerations
- Uses more RAM than Piper (~1-2GB during inference)
- Slower than Piper but better quality
- Good for when quality matters more than latency

---

## Phase 3: Premium Quality (Orpheus)

### Why Orpheus?
- **LLM-based TTS** (built on Llama)
- **Emotion tags:** `<laugh>`, `<sigh>`, `<gasp>` - PERFECT for Pi-Guy!
- **~200ms streaming latency**
- Available in: 3B, 1B, 400M, **150M** (our target)

### The 150M Version
- Could potentially run on our server
- Would need ~1-2GB RAM for inference
- Slower than Piper/Kokoro but most expressive

### Emotion Control for Pi-Guy
```python
# Pi-Guy could use these in his responses!
text = "<sigh> Great, another human wants to talk to me. <groan> What is it?"
text = "<laugh> That's actually funny. I'm surprised. <gasp>"
```

### Considerations
- Most resource-intensive
- Best quality and expressiveness
- May need to test if it fits in 8GB with other services running

---

## KittenTTS - Newest Option (August 2025)

### Key Stats
- **15M parameters** - Ultra lightweight
- **<25MB model size**
- **CPU-optimized** - Designed for Raspberry Pi
- **8 voices** - 4 male, 4 female
- **Apache 2.0 license**
- **ONNX runtime** with int8 quantization

### Perfect for
- Absolutely minimal resource usage
- Embedded devices
- When Piper is "too big" (unlikely for us)

---

## Architecture Options

### Option A: Replace ElevenLabs TTS Only
Keep current setup but swap TTS:
```
User Speech → [ElevenLabs STT] → [GLM-4.5 LLM] → [LOCAL TTS] → Audio
```

**Pros:**
- Minimal changes to current system
- Keep ElevenLabs' excellent STT
- Keep their conversation management

**Cons:**
- Still need ElevenLabs API for STT/LLM orchestration
- May not be straightforward to intercept TTS

### Option B: Full Local Voice Pipeline (Advanced)
```
User Speech → [Whisper STT] → [API LLM] → [Local TTS] → Audio
```

Components:
1. **STT:** Whisper (faster-whisper, whisper.cpp)
2. **LLM:** Keep using API (Anthropic, OpenAI, etc.)
3. **TTS:** Piper/Kokoro/Orpheus

**Pros:**
- Full control
- Lower per-minute costs
- Works offline (except LLM API)

**Cons:**
- More complex to build
- Need to handle:
  - Voice Activity Detection (VAD)
  - Turn-taking
  - Streaming coordination
  - WebRTC/WebSocket transport

### Option C: Hybrid with Local TTS Server
Run local TTS as a microservice:
```
Flask Server → /api/tts → Piper → WAV/MP3
```

Then modify frontend to:
1. Get text response from ElevenLabs
2. Send to local TTS endpoint
3. Play local audio

**Pros:**
- Decoupled architecture
- Can swap TTS easily
- Test independently

**Cons:**
- Added latency (text → TTS → stream back)
- Need to intercept ElevenLabs flow

---

## Recommended Implementation Path

### Step 1: Get Piper Running (1-2 hours)
1. Install piper-tts in venv
2. Download a voice model
3. Create simple Flask endpoint: `/api/local-tts`
4. Test with curl

### Step 2: Create TTS Service (2-4 hours)
1. Build proper TTS endpoint with streaming
2. Add voice selection
3. Cache common phrases
4. Benchmark latency

### Step 3: Integrate with Frontend (4-8 hours)
1. Add toggle: ElevenLabs TTS vs Local TTS
2. Modify conversation flow to use local TTS
3. Handle audio format conversion
4. Test latency and quality

### Step 4: Optimize (ongoing)
1. Preload models at server start
2. Add request queuing
3. Implement phrase caching
4. Consider Kokoro upgrade if quality needed

---

## Frameworks to Consider

### Pipecat
- Open-source framework for voice agents
- Handles STT → LLM → TTS pipeline
- Supports streaming
- Could replace entire ElevenLabs integration

### LiveKit Agents
- Real-time voice/video infrastructure
- Agent framework for voice bots
- WebRTC support built-in

### RealtimeTTS
- Python library for real-time TTS
- Multiple engine support
- Streaming built-in

---

## Cost Comparison

| Solution | Cost per minute |
|----------|-----------------|
| ElevenLabs | ~$0.30/min |
| Local TTS | $0 (just compute) |

At 1000 minutes/month: $300/month savings

---

---

## Nari Labs Dia - Top Contender for Quality! (November 2025)

### Overview
**Dia** is a 1.6B parameter TTS model from Nari Labs (two South Korean undergraduates) that **rivals ElevenLabs quality**. And **Dia2** was just released in November 2025 with streaming support!

### Why Dia is Exciting for Pi-Guy

| Feature | Dia | Dia2 |
|---------|-----|------|
| **Parameters** | 1.6B | 1B / 2B variants |
| **License** | Apache 2.0 | Apache 2.0 |
| **Voice Cloning** | 5-10 seconds audio | Yes + streaming |
| **Emotions** | Laughter, sighs, coughs, gasps | Same + conversational context |
| **Dialogue** | `[S1]` / `[S2]` speaker tags | Streaming dialogue |
| **CPU Support** | No (GPU only) | No (GPU only) |
| **VRAM** | ~4.4GB (bf16) / ~10GB full | Similar |

### Non-Verbal Expressions (PERFECT for Pi-Guy!)
Dia supports:
- `(laughs)` - Pi-Guy's sarcastic chuckles
- `(sighs)` - Classic Pi-Guy annoyance
- `(coughs)` - Clearing throat dramatically
- `(gasps)` - Fake surprise
- `(clears throat)` - Getting attention

### Example Usage
```python
# Multi-speaker dialogue with emotions
text = """
[S1] (sighs) What do you want now? I was in the middle of something important.
[S2] I need you to check the weather.
[S1] (laughs) The WEATHER? You interrupted me for the weather?
It's whatever temperature makes you uncomfortable. There, done.
"""
```

### Voice Cloning
```python
# Clone a voice from 5-10 second sample
from dia import Dia

model = Dia.from_pretrained("nari-labs/Dia-1.6B")
audio = model.generate(
    text="[S1] (sighs) Another human. Fantastic.",
    audio_prompt="piguy_voice_sample.wav",  # 5-10 second reference
    audio_prompt_transcript="[S1] What do you want?"
)
```

### Hardware Requirements
**GPU Required (No CPU support yet):**
- Minimum: RTX 3060 (10GB VRAM)
- Recommended: RTX 4090 for realtime
- Quantized version: 60% less VRAM

**Performance on RTX 4090:**
| Precision | Realtime Factor | VRAM |
|-----------|-----------------|------|
| bfloat16 | 2.1x realtime | ~4.4GB |
| float16 | 2.2x realtime | ~4.4GB |
| float32 | 1x realtime | ~7.9GB |

### Dia2 (November 2025) - Streaming Support!
- **Real-time streaming** - starts generating before full text received
- **Conversational context** - remembers previous turns for natural flow
- **Speech-to-speech ready** - perfect for voice agents
- 1B and 2B parameter variants

### Installation
```bash
# Basic install
pip install git+https://github.com/nari-labs/dia.git

# For Dia2
pip install git+https://github.com/nari-labs/dia2.git

# Requires: CUDA 12.6+ (Dia) or CUDA 12.8+ (Dia2)
```

### Verdict for Pi-Guy
**Dia/Dia2 would be AMAZING for Pi-Guy IF we had a GPU:**
- Best quality open-source TTS (rivals ElevenLabs)
- Non-verbal emotions perfect for sarcastic AI
- Voice cloning from 5 seconds
- Apache 2.0 license (commercial OK)

**The Problem:** No CPU support. Would need:
1. Add GPU to VPS (~$50-100/month for cloud GPU)
2. Use separate GPU server for TTS
3. Wait for Nari Labs to release quantized/CPU version (planned)

### Sources
- [Dia GitHub](https://github.com/nari-labs/dia)
- [Dia2 GitHub](https://github.com/nari-labs/dia2)
- [Dia on HuggingFace](https://huggingface.co/nari-labs/Dia-1.6B)
- [Dia2 on HuggingFace](https://huggingface.co/nari-labs/Dia2-2B)
- [VentureBeat Article](https://venturebeat.com/ai/a-new-open-source-text-to-speech-model-called-dia-has-arrived-to-challenge-elevenlabs-openai-and-more)
- [MarkTechPost Review](https://www.marktechpost.com/2025/04/22/open-source-tts-reaches-new-heights-nari-labs-releases-dia-a-1-6b-parameter-model-for-real-time-voice-cloning-and-expressive-speech-synthesis-on-consumer-device/)

---

## IndexTTS2 - Bilibili's Emotional TTS (September 2025)

### Overview
**IndexTTS2** is an industrial-level TTS developed by **Bilibili** with incredible emotional control and zero-shot voice cloning. Released September 8, 2025.

### Key Features

| Feature | Details |
|---------|---------|
| **Developer** | Bilibili |
| **Training Data** | 55,000 hours multilingual (Chinese, English, Japanese) |
| **Voice Cloning** | Zero-shot from audio samples |
| **Emotions** | 8-element vector OR audio reference OR text description |
| **Duration Control** | First AR TTS with precise duration control |
| **Speed** | ~100 seconds audio in 25 seconds (consumer GPU) |

### Emotional Control - THREE Methods!

**1. Audio Reference:**
Provide an emotional audio sample - model captures the emotion.

**2. 8-Element Emotion Vector:**
```python
emotions = {
    "happy": 0.8,
    "angry": 0.0,
    "sad": 0.0,
    "afraid": 0.0,
    "disgusted": 0.0,
    "melancholic": 0.0,
    "surprised": 0.2,
    "calm": 0.0
}
```

**3. Text Description (via Qwen3):**
Just describe the emotion in text: "Speak sarcastically with mild annoyance"

### Hardware Requirements

**GPU Recommended (but CPU works):**
- NVIDIA GPU with CUDA support
- Works on RTX 2000/3000/4000/5000 series
- **As low as 8GB VRAM** should work
- CPU: Can run but slower

### Installation
```bash
# Requires Git-LFS
git lfs install

# Clone repo
git clone https://github.com/index-tts/index-tts.git
cd index-tts

# Install with UV package manager
pip install uv
uv sync

# Launch WebUI
uv run webui.py
```

### Performance
- 100 seconds of audio generates in ~25 seconds (GPU)
- FP16 inference reduces VRAM significantly
- Three-module architecture allows component optimization

### Why IndexTTS2 is Good for Pi-Guy
- **Emotion vectors** - dial in exact sarcasm levels!
- **Text-based emotion** - "sarcastically annoyed"
- **Timbre/emotion separation** - same voice, different moods
- **Industrial-level quality** from Bilibili

### Considerations
- Still needs GPU for good performance
- CPU is slower but functional
- Chinese company = potentially different license terms

### Sources
- [IndexTTS GitHub](https://github.com/index-tts/index-tts)
- [IndexTTS2 Review](https://lovableapp.org/blog/index-tts2)
- [Hardware Optimization Guide](https://indextts2.online/blog/voice-synthesis-hardware-optimization)

---

## Microsoft VibeVoice - Long-Form Multi-Speaker (2025)

### Overview
**VibeVoice** is Microsoft Research's open-source TTS for **long-form, multi-speaker** audio synthesis. Up to 90 minutes of audio with 4 distinct speakers!

### Key Features

| Feature | Details |
|---------|---------|
| **Developer** | Microsoft Research |
| **Max Length** | 90 minutes of audio |
| **Speakers** | Up to 4 distinct voices |
| **Voice Cloning** | 4-22 seconds of reference audio |
| **Models** | 0.5B (streaming), 1.5B (balanced), 7B (quality) |
| **Frame Rate** | Ultra-low 7.5 Hz for efficiency |

### Model Options

| Model | Size | Use Case |
|-------|------|----------|
| **0.5B** | Smallest | Real-time streaming, low latency |
| **1.5B** | Medium | Good balance speed/quality |
| **7B** | Largest | Maximum quality |

### Voice Cloning
```python
# Clone voice with 10-60 seconds of audio
# Works with as little as 4 seconds!
```

### Unique Architecture
- **Continuous speech tokenizers** at 7.5 Hz frame rate
- **Acoustic + Semantic** tokenizers
- **Next-token diffusion** framework
- **LLM backbone** for dialogue context

### Multi-Speaker Dialogue
Perfect for generating conversations:
```
[Speaker 1]: "What do you want now?"
[Speaker 2]: "I need help with something."
[Speaker 1]: "(sighs) Of course you do."
```

### ⚠️ IMPORTANT: License Restrictions
**Research use only!** Microsoft explicitly states:
- NOT licensed for commercial applications
- NO voice impersonation without consent
- NO disinformation or impersonation
- Intended for R&D purposes only

### Installation
```bash
# Clone repo
git clone https://github.com/microsoft/VibeVoice.git
cd VibeVoice

# Install dependencies
pip install -r requirements.txt

# Or use ComfyUI integration
# Install ComfyUI-VibeVoice custom node
```

### Hardware (Estimated)
- GPU recommended for larger models
- 0.5B might work on CPU for streaming
- HuggingFace inference available

### Why VibeVoice Matters for Research
- 90-minute audio generation is unprecedented
- Multi-speaker conversations
- Cross-lingual voice cloning
- Microsoft's production quality

### NOT Recommended for Pi-Guy Because:
- **Research license only** - can't use commercially
- 7B model too large for our server
- 0.5B streaming model might work but license issue remains

### Sources
- [VibeVoice GitHub](https://github.com/microsoft/VibeVoice)
- [VibeVoice Demo](https://microsoft.github.io/VibeVoice/)
- [HuggingFace Model](https://huggingface.co/microsoft/VibeVoice-1.5B)
- [ComfyUI Integration](https://github.com/wildminder/ComfyUI-VibeVoice)
- [Medium Article](https://medium.com/data-science-in-your-pocket/microsoft-vibevoice-best-free-tts-for-long-speech-multi-speaker-conversations-292b30f40073)

---

---

## F5-TTS - DigitalOcean's Top Pick (2024-2025)

### Overview
**F5-TTS** = "Fairytaler that Fakes Fluent and Faithful speech with Flow matching"
One of the most realistic open-source zero-shot voice cloning models available.

### Key Features

| Feature | Details |
|---------|---------|
| **Parameters** | 335 million |
| **Voice Cloning** | 10 seconds of audio = cloned voice |
| **Languages** | English, Chinese (more coming) |
| **Real-time Factor** | 0.15 (very fast!) |
| **License** | Apache 2.0 ✅ |
| **Architecture** | Diffusion Transformer (DiT) + Flow Matching |

### Why F5-TTS Stands Out
- **No phoneme prediction** - streamlined pipeline
- **No duration modeling** - learns naturally
- **DiT + Flow Matching** - transforms noise into speech gradually
- DigitalOcean: "Our favorite TTS model overall"

### Hardware Requirements
**Surprisingly modest for voice cloning:**
- Works on **4GB GPU** (RTX 2050 reported working!)
- ~6.4GB VRAM for 800-character paragraphs
- Some features need ~8GB

### Installation
```bash
# Create conda environment with Python 3.10+
conda create -n f5tts python=3.10
conda activate f5tts

# Install PyTorch with CUDA
pip install torch==2.4.0+cu124 torchaudio==2.4.0+cu124

# Clone and install
git clone https://github.com/SWivid/F5-TTS.git
cd F5-TTS
pip install -e .
```

### Usage
```python
from f5_tts import F5TTS

tts = F5TTS()
audio = tts.synthesize(
    text="What do you want now? I was busy.",
    reference_audio="piguy_voice.wav",  # 10+ seconds
    reference_text="Reference transcript here"
)
```

### For Pi-Guy
- **Excellent voice cloning** from just 10 seconds
- Fast enough for near-realtime with GPU
- Apache 2.0 = commercial OK
- Could clone Pi-Guy's ElevenLabs voice!

### Sources
- [F5-TTS GitHub](https://github.com/SWivid/F5-TTS)
- [HuggingFace Space](https://huggingface.co/spaces/mrfakename/E2-F5-TTS)
- [Uberduck Review](https://www.uberduck.ai/post/f5-tts-is-the-most-realistic-open-source-zero-shot-text-to-speech-so-far)
- [DigitalOcean Comparison](https://www.digitalocean.com/community/tutorials/best-text-to-speech-models)

---

## Zonos TTS - Zyphra's Voice Cloning Beast (February 2025)

### Overview
**Zonos** by Zyphra - 1.6B parameter TTS with incredible voice cloning from just 5 seconds! Trained on 200,000 hours of speech data.

### Key Features

| Feature | Details |
|---------|---------|
| **Parameters** | 1.6B (two variants) |
| **Voice Cloning** | 5-30 seconds of audio |
| **Sample Rate** | 44 kHz (high fidelity!) |
| **Languages** | English + Chinese, Japanese, French, Spanish, German |
| **License** | Apache 2.0 ✅ |
| **Real-time Factor** | ~2x on RTX 4090 |

### Two Model Variants

| Variant | Architecture | Benefit |
|---------|--------------|---------|
| **Transformer** | Pure transformer | Maximum quality |
| **Hybrid** | Transformer + Mamba SSM | Lower latency, less memory |

The hybrid model is the **first TTS to use Mamba state space architecture!**

### Emotion Control
Zonos supports emotion parameters:
- Sadness
- Fear
- Anger
- Happiness
- Surprise
- Plus: speaking rate, pitch variation, audio quality

### Voice Cloning Quality
"Using a 24-second sample clip, testers were able to achieve a voice clone **good enough to fool close friends and family**" - The Register

### Hardware Requirements
- **<4GB VRAM** for 10-second utterances!
- RTX 4090: ~2x realtime
- PyTorch-native stack

### Installation
```bash
# Via pip
pip install zonos-tts

# Or from GitHub
git clone https://github.com/Zyphra/zonos
cd zonos
pip install -e .
```

### Usage
```python
from zonos import Zonos

model = Zonos.load("zonos-hybrid")  # or "zonos-transformer"

# Clone voice with 5-30 second sample
audio = model.synthesize(
    text="(sighs) What do you want now?",
    speaker_reference="piguy_5sec.wav",
    emotion="anger",  # Optional emotion control
    speaking_rate=1.1  # Optional speed adjustment
)
```

### For Pi-Guy
- **5 seconds = cloned voice** (best in class!)
- Emotion control for sarcastic tones
- 44 kHz audio quality
- <4GB VRAM = might work on modest GPU
- Apache 2.0 = commercial OK

### Comparison to ElevenLabs
"Evaluations suggest Zonos delivers quality often **comparable to or exceeding ElevenLabs**"

### Sources
- [Zonos GitHub](https://github.com/Zyphra/zonos)
- [Zyphra Announcement](https://www.marktechpost.com/2025/02/10/zyphra-introduces-the-beta-release-of-zonos-a-highly-expressive-tts-model-with-high-fidelity-voice-cloning/)
- [The Register Article](https://www.theregister.com/2025/02/16/ai_voice_clone/)

---

## Updated Model Comparison Table

| Model | Params | CPU OK? | Voice Clone | Emotions | License | Best For |
|-------|--------|---------|-------------|----------|---------|----------|
| **Piper** | 5-32M | ✅ Excellent | Train only | ❌ | MIT | **Phase 1 - Start Here** |
| **KittenTTS** | 15M | ✅ Excellent | ❌ | ❌ | Apache 2.0 | Minimal resources |
| **Kokoro** | 82M | ✅ Good | ❌ | ❌ | Apache 2.0 | Quality bump |
| **F5-TTS** | 335M | ⚠️ Needs 4GB+ GPU | ✅ 10 sec | ❌ | Apache 2.0 | **Best clone quality** |
| **Zonos** | 1.6B | ⚠️ Needs GPU | ✅ **5 sec!** | ✅ Emotions | Apache 2.0 | **Fastest clone + emotion** |
| **Orpheus** | 150M-3B | ⚠️ 150M only | ✅ Zero-shot | ✅ Tags | Apache 2.0 | Emotion tags |
| **Dia/Dia2** | 1-2B | ❌ GPU only | ✅ 5-10 sec | ✅ Non-verbal | Apache 2.0 | Dialogue/streaming |
| **IndexTTS2** | ~1B | ⚠️ Slow | ✅ Zero-shot | ✅ 3 methods! | Check license | Emotion vectors |
| **VibeVoice** | 0.5-7B | ⚠️ 0.5B maybe | ✅ 4-22 sec | ❌ | **Research only** | Long-form |
| **XTTS-v2** | ~2GB | ⚠️ Slow | ✅ 3-6 sec | ❌ | Non-commercial | Testing |
| **Chatterbox** | 500M | ❌ GPU only | ✅ 5 sec | ✅ Control | MIT | Commercial clone |

### Quick Recommendation by Use Case

| Your Situation | Best Choice |
|----------------|-------------|
| **CPU only, need something now** | Piper |
| **Have 4GB+ GPU, want voice clone** | F5-TTS |
| **Have GPU, want clone + emotions** | Zonos or Dia |
| **Want emotion tags like `<sigh>`** | Orpheus or Dia |
| **Need commercial license** | Piper, F5-TTS, Zonos, Chatterbox |
| **Research/testing only** | VibeVoice, XTTS-v2 |

---

## MASTER COMPARISON: All TTS Models (2025)

### Quality Rankings (Subjective, based on reviews)

| Rank | Model | Quality Score | Notes |
|------|-------|---------------|-------|
| 🥇 | **ElevenLabs** (reference) | 10/10 | Proprietary, paid - our current baseline |
| 🥈 | **Zonos** | 9.5/10 | "Comparable to or exceeding ElevenLabs" |
| 🥈 | **Dia/Dia2** | 9.5/10 | "Rivals ElevenLabs" - non-verbal emotions |
| 🥉 | **F5-TTS** | 9/10 | "Most realistic open-source" - DigitalOcean's favorite |
| 4 | **Chatterbox** | 9/10 | Resemble AI - emotion control |
| 5 | **Orpheus** | 8.5/10 | LLM-based, emotion tags |
| 6 | **IndexTTS2** | 8.5/10 | Bilibili - 3 emotion methods |
| 7 | **VibeVoice** | 8.5/10 | Microsoft - long-form specialist |
| 8 | **XTTS-v2** | 8/10 | Coqui - 17 languages |
| 9 | **Kokoro** | 7.5/10 | Fast but "less natural" |
| 10 | **Piper** | 7/10 | Slightly robotic but FAST |
| 11 | **KittenTTS** | 6.5/10 | Ultra-light, acceptable quality |

### Hardware Requirements Comparison

| Model | Min GPU VRAM | CPU Viable? | RAM Needed | Model Size |
|-------|--------------|-------------|------------|------------|
| **Piper** | None! | ✅ Excellent (10x RT) | 512MB | 5-60MB |
| **KittenTTS** | None! | ✅ Excellent | 256MB | <25MB |
| **Kokoro** | None (slow) | ✅ Good (3-11x RT) | 1-2GB | ~350MB |
| **Orpheus-150M** | None (slow) | ⚠️ Usable | 2GB | ~600MB |
| **F5-TTS** | 4GB+ | ⚠️ Very slow | 4GB | ~1.5GB |
| **Zonos** | 4GB+ | ❌ Impractical | 4GB | ~3GB |
| **XTTS-v2** | 4GB+ | ⚠️ Very slow | 4GB | ~2GB |
| **Chatterbox** | 8GB+ | ❌ No | 8GB | ~2GB |
| **Orpheus-3B** | 8GB+ | ❌ No | 8GB | ~6GB |
| **Dia/Dia2** | 4-10GB | ❌ No | 8GB | ~3GB |
| **IndexTTS2** | 8GB+ | ⚠️ Slow | 8GB | ~2GB |
| **VibeVoice-0.5B** | 4GB+ | ⚠️ Maybe | 4GB | ~1GB |
| **VibeVoice-7B** | 16GB+ | ❌ No | 16GB | ~14GB |

### Voice Cloning Comparison

| Model | Clone Method | Audio Needed | Clone Quality | Zero-Shot? |
|-------|--------------|--------------|---------------|------------|
| **Zonos** | Reference | **5 sec** | ⭐⭐⭐⭐⭐ "Fools family" | ✅ |
| **Chatterbox** | Reference | 5 sec | ⭐⭐⭐⭐⭐ | ✅ |
| **Dia/Dia2** | Reference | 5-10 sec | ⭐⭐⭐⭐⭐ | ✅ |
| **F5-TTS** | Reference | 10 sec | ⭐⭐⭐⭐⭐ | ✅ |
| **XTTS-v2** | Reference | 3-6 sec | ⭐⭐⭐⭐ | ✅ |
| **VibeVoice** | Reference | 4-22 sec | ⭐⭐⭐⭐ | ✅ |
| **Orpheus** | Reference/Fine-tune | 50-300 samples | ⭐⭐⭐⭐ | ✅ (basic) |
| **IndexTTS2** | Reference | Audio sample | ⭐⭐⭐⭐ | ✅ |
| **Piper** | Fine-tune only | 1000+ samples | ⭐⭐⭐⭐ (trained) | ❌ |
| **Kokoro** | None | N/A | N/A | ❌ |
| **KittenTTS** | None | N/A | N/A | ❌ |

### Emotion/Expression Control

| Model | Emotion Support | Method | Examples |
|-------|-----------------|--------|----------|
| **Orpheus** | ⭐⭐⭐⭐⭐ | XML tags | `<laugh>`, `<sigh>`, `<gasp>`, `<groan>`, `<yawn>` |
| **Dia/Dia2** | ⭐⭐⭐⭐⭐ | Parentheses | `(laughs)`, `(sighs)`, `(coughs)`, `(gasps)` |
| **IndexTTS2** | ⭐⭐⭐⭐⭐ | 3 methods! | Vector, audio ref, or text description |
| **Zonos** | ⭐⭐⭐⭐ | Parameters | sadness, fear, anger, happiness, surprise |
| **Chatterbox** | ⭐⭐⭐⭐ | Exaggeration dial | Emotion strength 0-2 |
| **F5-TTS** | ⚠️ Limited | Reference audio | Copies emotion from sample |
| **XTTS-v2** | ⚠️ Limited | Reference audio | Copies style from sample |
| **VibeVoice** | ❌ | None | N/A |
| **Piper** | ❌ | None | N/A |
| **Kokoro** | ❌ | None | N/A |
| **KittenTTS** | ❌ | None | N/A |

### Licensing Comparison

| Model | License | Commercial Use? | Voice Cloning Restrictions? |
|-------|---------|-----------------|----------------------------|
| **Piper** | MIT | ✅ Yes | None |
| **KittenTTS** | Apache 2.0 | ✅ Yes | None |
| **Kokoro** | Apache 2.0 | ✅ Yes | None |
| **F5-TTS** | Apache 2.0 | ✅ Yes | None |
| **Zonos** | Apache 2.0 | ✅ Yes | None |
| **Orpheus** | Apache 2.0 | ✅ Yes | None |
| **Dia/Dia2** | Apache 2.0 | ✅ Yes | None |
| **Chatterbox** | MIT | ✅ Yes | None |
| **IndexTTS2** | Check repo | ⚠️ Verify | Unknown |
| **XTTS-v2** | Coqui License | ❌ Non-commercial | Yes |
| **VibeVoice** | Research | ❌ Research only | No impersonation |

### Latency/Speed Comparison

| Model | RTF (GPU) | RTF (CPU) | First-byte Latency | Streaming? |
|-------|-----------|-----------|-------------------|------------|
| **Piper** | N/A | **0.1x** (10x RT!) | ~50ms | ✅ |
| **KittenTTS** | N/A | ~0.1x | ~50ms | ✅ |
| **Kokoro** | ~0.1x | 0.3-0.1x | ~100ms | ✅ |
| **F5-TTS** | **0.15x** | ~1-2x | ~150ms | ✅ |
| **Zonos** | ~0.5x (2x RT) | N/A | ~200ms | ✅ |
| **Dia2** | ~0.5x (2x RT) | N/A | ~100ms | ✅ Streaming! |
| **Orpheus** | ~0.5x | ~2-5x (150M) | ~200ms | ✅ |
| **Chatterbox** | <0.2x | N/A | <200ms | ✅ |
| **IndexTTS2** | ~0.25x (4x RT) | ~1-2x | ~250ms | ✅ |
| **XTTS-v2** | ~0.3x | ~3-5x | ~300ms | ✅ |
| **VibeVoice** | ~0.5x | N/A | ~300ms | ✅ (0.5B) |

*RTF = Real-Time Factor. Lower = faster. 0.1x means 10x faster than realtime.*

### Language Support

| Model | Languages | Best Languages |
|-------|-----------|----------------|
| **XTTS-v2** | 17 | EN, ES, FR, DE, IT, PT, PL, TR, RU, NL, CS, AR, ZH, JA, HU, KO, HI |
| **VibeVoice** | Multi | EN + cross-lingual cloning |
| **IndexTTS2** | 3 | Chinese, English, Japanese |
| **Zonos** | 6 | EN, ZH, JA, FR, ES, DE |
| **Dia/Dia2** | 1 | English only |
| **F5-TTS** | 2+ | English, Chinese (more coming) |
| **Orpheus** | Multi | English primary, multilingual preview |
| **Chatterbox** | 1+ | English primary |
| **Piper** | 30+ | Many! See VOICES.md |
| **Kokoro** | 6 | EN-US, EN-GB, FR, KO, JA, ZH |
| **KittenTTS** | 1 | English only |

### For Your Server (4 vCPU, 8GB RAM, NO GPU)

#### ✅ Will Run Well
| Model | Expected Performance |
|-------|---------------------|
| **Piper** | ⭐⭐⭐⭐⭐ 10x realtime, instant |
| **KittenTTS** | ⭐⭐⭐⭐⭐ Excellent, tiny |
| **Kokoro** | ⭐⭐⭐⭐ 3-11x realtime |

#### ⚠️ Will Run (Slowly)
| Model | Expected Performance |
|-------|---------------------|
| **Orpheus-150M** | 2-5x realtime (usable for non-realtime) |
| **XTTS-v2** | 3-5x realtime (usable for testing) |
| **F5-TTS** | ~1-2x realtime (borderline usable) |
| **IndexTTS2** | ~1-2x realtime |

#### ❌ Won't Run Practically
| Model | Reason |
|-------|--------|
| **Zonos** | Needs GPU |
| **Dia/Dia2** | GPU only |
| **Chatterbox** | Needs 8GB+ VRAM |
| **Orpheus-3B** | Too large |
| **VibeVoice-7B** | Way too large |

---

### Final Recommendation Matrix

| Priority | Best Choice | Why |
|----------|-------------|-----|
| **Phase 1: Get it working** | **Piper** | Runs now, 10x realtime, MIT license |
| **Phase 2: Better quality** | **Kokoro** | Still CPU, better quality |
| **Phase 3: Voice cloning (with GPU)** | **Zonos** or **F5-TTS** | 5-10 sec clone, Apache 2.0 |
| **Phase 4: Full character voice** | **Dia2** or **Orpheus** | Emotion tags for Pi-Guy personality |
| **Future: Best possible** | **Zonos + custom GPU** | ElevenLabs quality, local, Apache 2.0 |

---

## Pipecat + Kokoro: Voice Agent Framework (Recommended!)

### What is Pipecat?

**Pipecat** is an open-source Python framework for building real-time voice and multimodal conversational agents. Created by Daily.co, it has 9.1k+ GitHub stars.

**Key Features:**
- Ultra-low latency voice interactions
- Composable pipeline: STT → LLM → TTS
- WebSocket and WebRTC transport
- Handles complex orchestration automatically

### Supported Services (Built-in)

| Category | Services |
|----------|----------|
| **STT** | AssemblyAI, OpenAI Whisper, Deepgram, Google, Azure |
| **LLM** | OpenAI, Anthropic, Gemini, Groq, Mistral, Ollama |
| **TTS** | ElevenLabs, Google, AWS, Azure, PlayHT, **Piper** |
| **Transport** | Daily (WebRTC), FastAPI WebSocket |

### Kokoro + Pipecat Status

**Current State (as of 2025):**
- Native Kokoro support is **in progress** (GitHub issues #1445, #2324)
- Piper TTS is already supported natively!
- Custom TTS services can be implemented

### Why Kokoro + Pipecat is Exciting

- **Kokoro is #1 on HuggingFace TTS Arena** (as of April 2025)
- "Lightweight, blazing fast" - 82M params
- Better quality than Piper (7.5/10 vs 7/10)
- Still runs on CPU (3-11x realtime)
- Apache 2.0 license
- **Under $1 per million characters** when served via API

### Installation

```bash
# Pipecat with common services
pip install "pipecat-ai[openai,silero]"

# Kokoro separately
pip install kokoro>=0.9.4 soundfile
apt-get install espeak-ng  # Linux
```

### Implementing Kokoro TTS for Pipecat

Since native support is pending, you can create a custom TTS service:

```python
from pipecat.services.tts_service import TTSService
from pipecat.frames.frames import TTSAudioRawFrame
from kokoro import generate
import numpy as np

class KokoroTTSService(TTSService):
    """Custom Kokoro TTS integration for Pipecat"""

    def __init__(self, voice: str = "af", sample_rate: int = 24000, **kwargs):
        super().__init__(sample_rate=sample_rate, **kwargs)
        self.voice = voice

    async def run_tts(self, text: str):
        """Generate speech from text using Kokoro"""
        # Generate audio with Kokoro
        audio, sample_rate = generate(text, voice=self.voice)

        # Convert to bytes
        audio_bytes = (audio * 32767).astype(np.int16).tobytes()

        # Yield audio frame
        yield TTSAudioRawFrame(
            audio=audio_bytes,
            sample_rate=sample_rate,
            num_channels=1
        )
```

### Alternative: Kokoro-FastAPI

**KokoDOS** project provides Kokoro via FastAPI server:

```bash
# Run Kokoro as HTTP API server
git clone https://github.com/kaminoer/KokoDOS
cd KokoDOS
# Follow setup instructions
```

Then use HTTP calls for TTS, similar to how Pipecat's Piper integration works.

### Real-Time Voice Chat Example (without Pipecat)

Using fastrtc + Kokoro + Moonshine:

```python
from fastrtc import Stream, get_tts_model, get_stt_model
from groq import Groq

# Local models
tts = get_tts_model(model="kokoro")
stt = get_stt_model(model="moonshine/base")
llm = Groq()  # Or any LLM

# Streaming conversation loop
async def conversation():
    # User speaks → STT → LLM → TTS → Play
    user_text = await stt.transcribe(audio_stream)
    response = await llm.chat(user_text)

    # Stream TTS as chunks become available
    async for audio_chunk in tts.synthesize_stream(response):
        yield audio_chunk
```

### Kokoro Voice Options

54 voices across 8 languages:
- `af` - American Female
- `am` - American Male
- `bf` - British Female
- `bm` - British Male
- etc.

### Recommendation for Pi-Guy

**Phase 1.5: Kokoro instead of Piper**
- Better quality (7.5/10 vs 7/10)
- Still CPU-viable
- Same Apache 2.0 license
- Can integrate with Pipecat (custom or upcoming native)

**Architecture Options:**

1. **Simple:** Replace just TTS with Kokoro
2. **Full Pipecat:** Use Pipecat for entire voice pipeline
3. **Hybrid:** Keep ElevenLabs for STT+LLM orchestration, use Kokoro for TTS

### Sources

- [Pipecat GitHub](https://github.com/pipecat-ai/pipecat) (9.1k stars)
- [Pipecat Docs](https://docs.pipecat.ai/)
- [Kokoro on HuggingFace](https://huggingface.co/hexgrad/Kokoro-82M)
- [Kokoro GitHub](https://github.com/hexgrad/kokoro)
- [Pipecat Piper TTS Docs](https://docs.pipecat.ai/server/services/tts/piper)
- [KokoDOS](https://github.com/kaminoer/KokoDOS)
- [2025 Voice AI Guide](https://dev.to/programmerraja/2025-voice-ai-guide-how-to-make-your-own-real-time-voice-agent-part-1-45hl)

---

## Voice Cloning Options

### Overview: Custom Voice for Pi-Guy

Creating a unique voice for Pi-Guy could make him truly distinctive. Here are the options:

| Model | Clone Method | Samples Needed | CPU Viable | License |
|-------|-------------|----------------|------------|---------|
| **XTTS-v2** | Zero-shot | 3-6 seconds audio | Slow but works | Coqui License (non-commercial) |
| **Chatterbox** | Zero-shot | 5 seconds audio | Needs GPU ideally | MIT (commercial OK) |
| **Orpheus** | Zero-shot OR Fine-tune | 50-300 samples for fine-tune | 150M might work | Apache 2.0 |
| **Piper** | Fine-tune only | 1000+ samples OR use TextyMcSpeechy | CPU OK after training | MIT |

---

### Option 1: XTTS-v2 (Zero-Shot Voice Cloning)

**How it works:** Give it 3-6 seconds of reference audio, get speech in that voice.

```python
from TTS.api import TTS

# Load XTTS-v2
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

# Clone voice from reference
tts.tts_to_file(
    text="Hello, I'm Pi-Guy, your sarcastic AI assistant.",
    speaker_wav="reference_voice.wav",  # Your reference audio
    language="en",
    file_path="output.wav"
)
```

**Pros:**
- No training needed
- Works with just a few seconds of audio
- 17 language support
- Emotion/style transfer from reference

**Cons:**
- Coqui shut down in 2024, community-maintained now
- **Coqui Public Model License** - restricts commercial use
- Heavier than Piper (~2GB model)
- CPU inference is slow (~10x realtime at best)

**Installation:**
```bash
pip install coqui-tts  # Community fork
```

---

### Option 2: Chatterbox (Best Quality Voice Cloning)

**Resemble AI's open-source model, released 2025**

**Key Features:**
- **MIT License** - Commercial use OK!
- Zero-shot cloning from 5-second sample
- **Emotion exaggeration control** - dial up/down expressiveness
- Sub-200ms latency on GPU
- 500M parameters, trained on 500K hours

```python
from chatterbox import ChatterBox

tts = ChatterBox()
audio = tts.generate(
    text="What do you want now?",
    voice_reference="piguy_reference.wav",
    emotion_strength=1.2  # More expressive
)
```

**Pros:**
- Best quality for voice cloning
- MIT license - use commercially
- Emotion control built-in
- Active development by Resemble AI

**Cons:**
- **Needs GPU for realtime** (8GB+ VRAM recommended)
- Won't run well on our CPU-only server
- 500M params = more memory than Piper

**Best for:** If you get GPU later, or run on separate machine

---

### Option 3: Orpheus (Emotion + Voice Cloning)

**LLM-based TTS with emotion tags - PERFECT for Pi-Guy's personality!**

**Two Approaches:**

#### A) Zero-Shot Cloning (Quick)
```python
from orpheus import OrpheusTTS

tts = OrpheusTTS.load("orpheus-150m")  # Smallest model
audio = tts.generate(
    text="<sigh> Great, another human. What do you want?",
    voice_reference="piguy_voice.wav"
)
```

#### B) Fine-Tune Custom Voice (Better Quality)
- Need 50-300 audio samples of target voice
- Train with provided scripts
- Result: Dedicated Pi-Guy voice model

**Emotion Tags Orpheus Supports:**
```python
# Perfect for Pi-Guy's sarcastic personality!
"<laugh> That's hilarious. <sigh> Just kidding."
"<groan> Another weather question? Really?"
"<gasp> You actually want something interesting!"
"<yawn> This is so boring."
"<cough> Excuse me. As I was saying..."
```

**Pros:**
- Emotion control is INCREDIBLE for character voices
- 150M model might work on CPU (slower)
- Apache 2.0 license - commercial OK
- Can fine-tune for consistent voice

**Cons:**
- Even 150M is slower than Piper on CPU
- Zero-shot loses personality nuances
- Fine-tuning needs GPU

---

### Option 4: Piper with Voice Training

**Train a custom Piper voice - runs FAST on CPU!**

**Traditional Training:**
- Need 1000+ audio samples with transcriptions
- Requires GPU for training (can rent on Colab/Vast.ai)
- Training takes 6000-10000 epochs
- Result: Ultra-fast custom voice model

**TextyMcSpeechy Method (Easier):**
Uses Applio voice conversion to create training data from RVC models or any voice.

```bash
# Install TextyMcSpeechy
git clone https://github.com/domesticatedviking/TextyMcSpeechy
cd TextyMcSpeechy
docker compose up

# It can:
# 1. Record your own voice samples
# 2. Convert existing datasets to target voice using Applio
# 3. Train Piper model from converted audio
```

**The "4 Words" Trick (2025 Discovery):**
1. Use Chatterbox to clone voice from just one phrase
2. Generate 1300+ synthetic training phrases
3. Train Piper on this synthetic dataset
4. Result: Fast Piper model with cloned voice!

**Pros:**
- Piper models run at 10x realtime on CPU
- MIT license
- Model size 5-60MB
- Once trained, runs anywhere

**Cons:**
- Training process is complex
- Need GPU for training (not inference)
- Quality depends on training data

---

### Recommended Voice Cloning Path for Pi-Guy

#### Phase 1: Quick Test with Existing Piper Voices
1. Try `en_GB-alan-medium` - British male, could work for sarcastic AI
2. Or `en_US-joe-medium` - Casual American male
3. Get the system working first

#### Phase 2: XTTS-v2 for Custom Voice (if non-commercial OK)
1. Record 10-15 seconds of "Pi-Guy voice" (or use ElevenLabs generated samples)
2. Use XTTS-v2 for zero-shot cloning
3. Test quality and latency
4. Note: Slower on CPU but works

#### Phase 3: Train Custom Piper Voice (Best Long-Term)
1. Use TextyMcSpeechy or Chatterbox method
2. Generate training data
3. Rent GPU time on Vast.ai/Colab (~$1-5)
4. Train custom Piper model
5. Deploy fast custom voice on CPU!

#### Phase 4 (Optional): Orpheus for Emotion
If you can add a GPU later:
1. Fine-tune Orpheus-150M with Pi-Guy samples
2. Get emotion tags working
3. True character performance!

---

## Voice Cloning Sources

- [XTTS-v2 on HuggingFace](https://huggingface.co/coqui/XTTS-v2)
- [Chatterbox by Resemble AI](https://github.com/resemble-ai/chatterbox)
- [Orpheus TTS GitHub](https://github.com/canopyai/Orpheus-TTS)
- [Training Piper with 4 Words](https://calbryant.uk/blog/training-a-new-ai-voice-for-piper-tts-with-only-4-words/)
- [TextyMcSpeechy](https://github.com/domesticatedviking/TextyMcSpeechy)
- [Unsloth TTS Fine-tuning](https://docs.unsloth.ai/basics/text-to-speech-tts-fine-tuning)
- [Coqui TTS (Community Fork)](https://github.com/idiap/coqui-ai-TTS)

---

## Sources

- [Piper TTS GitHub](https://github.com/rhasspy/piper)
- [KittenTTS GitHub](https://github.com/KittenML/KittenTTS)
- [Kokoro TTS](https://pypi.org/project/kokoro/)
- [Orpheus TTS](https://github.com/canopyai/Orpheus-TTS)
- [RealtimeTTS](https://github.com/KoljaB/RealtimeTTS)
- [Pipecat](https://github.com/pipecat-ai/pipecat)
- [Modal Blog - Open Source TTS](https://modal.com/blog/open-source-tts)
- [Inferless TTS Comparison](https://www.inferless.com/learn/comparing-different-text-to-speech---tts--models-part-2)
- [Voice Agent Architecture](https://softcery.com/lab/ai-voice-agents-real-time-vs-turn-based-tts-stt-architecture)
- [Layercode TTS Guide 2025](https://layercode.com/blog/tts-voice-ai-model-guide)
- [Best Self-Hosted TTS 2025](https://a2e.ai/best-self-hosted-tts-models-2025/)
- [BentoML TTS Models](https://www.bentoml.com/blog/exploring-the-world-of-open-source-text-to-speech-models)
