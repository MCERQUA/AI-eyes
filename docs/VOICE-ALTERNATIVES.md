# Voice AI Alternatives Research

**Date:** November 30, 2025
**Problem:** ElevenLabs Conversational AI is expensive - $20+ spent in one day just testing/building

## Current Setup Cost Analysis

### ElevenLabs Conversational AI
- **Current cost:** ~$0.10/minute (Creator/Pro plans)
- **Business plan:** $0.08/minute
- **Problem:** Costs add up FAST during development and testing
- **Our usage:** ~200 minutes = $20 in ONE DAY

**Sources:**
- [ElevenLabs Pricing Cut Announcement](https://elevenlabs.io/blog/we-cut-our-pricing-for-conversational-ai)
- [ElevenLabs Conversational AI Cost](https://help.elevenlabs.io/hc/en-us/articles/29298065878929-How-much-does-Conversational-AI-cost)

---

## Alternative Approaches

### Option 1: Build Your Own Pipeline (STT → LLM → TTS)

Instead of using ElevenLabs all-in-one, build a custom pipeline:

```
User Speech → STT → LLM → TTS → Audio Output
```

#### Recommended Stack:

| Component | Option | Cost | Notes |
|-----------|--------|------|-------|
| **STT** | Deepgram | $0.0077/min streaming | $200 free credits |
| **LLM** | Cerebras | $0.10/M tokens (8B) | 2000+ tokens/sec, blazing fast |
| **TTS** | Cartesia Sonic | ~$0.05/1K chars | 40ms latency, best-in-class |

**Total estimated cost:** ~$0.02-0.03/minute (vs $0.10 with ElevenLabs)

**Framework:** [LiveKit Agents](https://github.com/livekit/agents) - handles orchestration, WebRTC, turn detection

**Sources:**
- [Deepgram Pricing](https://deepgram.com/pricing)
- [Cerebras Pricing](https://www.cerebras.ai/pricing)
- [Cartesia Pricing](https://cartesia.ai/pricing)
- [LiveKit Agents GitHub](https://github.com/livekit/agents)

---

### Option 2: Cerebras + LiveKit Voice Agent

Cerebras offers the **fastest inference** in the industry - 2000+ tokens/second.

#### Cerebras Pricing (Pay-per-token):
| Model | Input | Output |
|-------|-------|--------|
| Llama 3.1 8B | $0.10/M tokens | $0.10/M tokens |
| Llama 3.1 70B | $0.60/M tokens | $0.60/M tokens |
| Llama 3.1 405B | $6/M tokens | $12/M tokens |

#### Why Cerebras for Voice:
- **Speed:** 30x faster than GPT/Claude - critical for real-time voice
- **Latency:** <200ms time-to-first-token
- **OpenAI compatible:** Works with LiveKit's OpenAI plugin
- **Hume AI partnership:** Expressive, emotionally intelligent voice

#### Sample LiveKit + Cerebras Setup:
```python
from livekit import agents
from livekit.plugins import openai, deepgram, silero

# Cerebras via OpenAI-compatible API
llm = openai.LLM.with_cerebras(
    model="llama3.3-70b",
    temperature=0.7
)

# Deepgram for STT + TTS
stt = deepgram.STT()
tts = deepgram.TTS()  # or use Cartesia/Rime

# Voice Activity Detection
vad = silero.VAD()
```

**Sources:**
- [Cerebras + LiveKit Docs](https://docs.livekit.io/agents/integrations/cerebras/)
- [Cerebras Voice Agent Tutorial](https://inference-docs.cerebras.ai/cookbook/agents/livekit)
- [Hume AI + Cerebras Partnership](https://www.hume.ai/blog/case-study-hume-cerebras)

---

### Option 3: Cheaper ElevenLabs Alternatives (Drop-in TTS)

If we just want cheaper TTS and keep the rest:

#### Fish Audio / OpenAudio S1
- **Price:** $9.99/month for 200 minutes OR $15/M characters
- **Quality:** #1 on TTS-Arena, better than ElevenLabs in many cases
- **Free option:** 0.5B model can run locally
- [Fish Audio](https://fish.audio)

#### Cartesia Sonic-3
- **Price:** ~$0.05/1K characters ($5/month for 100K credits)
- **Latency:** 40ms (fastest in industry)
- **Features:** Laughs, emotes, conversational
- **Voice cloning:** 3 seconds of audio
- [Cartesia Pricing](https://cartesia.ai/pricing)

#### Resemble AI
- **Price:** 3x cheaper than ElevenLabs
- **Features:** 10-second voice cloning, can self-host
- **Open source:** Chatterbox TTS (MIT license, FREE)
- [Resemble AI](https://www.resemble.ai/alternative-to-elevenlabs/)

#### Deepgram Aura-2
- **Price:** Per-character billing, included in Voice Agent API
- **Latency:** ~184ms TTFB
- **Free:** $200 credits to start
- [Deepgram TTS](https://deepgram.com/learn/aura-text-to-speech-tts-api-voice-ai-agents-launch)

**Sources:**
- [Top ElevenLabs Alternatives - Cartesia](https://cartesia.ai/learn/top-elevenlabs-alternatives)
- [Best FREE ElevenLabs Alternatives](https://nerdynav.com/open-source-ai-voice/)

---

### Option 4: OpenAI Realtime API

OpenAI's native voice-to-voice API:

#### Pricing (gpt-realtime model):
- **Audio Input:** $32/M tokens (~$0.06/min)
- **Audio Output:** $64/M tokens (~$0.24/min)
- **Text tokens:** $5/M input, $20/M output

#### Estimated Cost:
- ~$0.30/minute for typical conversation
- **More expensive than ElevenLabs!**

#### Pros:
- Native GPT-4 voice, no pipeline needed
- Lower latency (no STT→LLM→TTS chain)

#### Cons:
- More expensive than building your own pipeline
- Less customization

**Sources:**
- [OpenAI Realtime API Pricing](https://openai.com/api/pricing/)
- [OpenAI Realtime API Announcement](https://openai.com/index/introducing-the-realtime-api/)

---

### Option 5: Fully Self-Hosted (FREE)

Run everything locally - zero API costs:

#### Stack:
| Component | Tool | Notes |
|-----------|------|-------|
| **STT** | FastWhisper | C++ optimized, runs on CPU |
| **LLM** | Ollama + Llama 3 | Local inference |
| **TTS** | Chatterbox / Kokoro-82M | MIT license, free |
| **Framework** | Pipecat / Vocode | Open source orchestration |

#### Requirements:
- Modern multi-core CPU
- 16GB+ RAM
- GPU recommended (RTX 3060+ ideal)

#### Projects:
- [Local-Talking-LLM](https://github.com/vndee/local-talking-llm) - Complete offline voice assistant
- [Verbi](https://github.com/PromtEngineer/Verbi) - FastWhisper + Ollama + MeloTTS
- [Moshi](https://github.com/kyutai-labs/moshi) - End-to-end speech model

**Sources:**
- [Build Local Speech-to-Speech AI](https://www.arsturn.com/blog/how-to-build-a-local-speech-to-speech-ai-voice-agent)
- [Voice AI Guide 2025](https://dev.to/programmerraja/2025-voice-ai-guide-how-to-make-your-own-real-time-voice-agent-part-2-1288)
- [Open Source Python Libraries for Voice Agents](https://www.analyticsvidhya.com/blog/2025/03/python-libraries-for-building-voice-agents/)

---

## Cost Comparison Summary

| Solution | Est. Cost/Min | Latency | Complexity | Notes |
|----------|---------------|---------|------------|-------|
| **ElevenLabs** (current) | $0.10 | Low | Easy | All-in-one but expensive |
| **Deepgram + Cerebras + Cartesia** | ~$0.02-0.03 | Low | Medium | Best balance |
| **OpenAI Realtime** | ~$0.30 | Lowest | Easy | Most expensive |
| **Fish Audio** (TTS only) | ~$0.05 | Low | Easy | Drop-in replacement |
| **Self-hosted** | $0 | Medium | Hard | Requires good hardware |

---

## Recommended Migration Path

### Phase 1: Quick Win (Reduce TTS Costs)
1. Keep ElevenLabs STT + LLM
2. Replace TTS with Cartesia Sonic ($0.05/1K chars)
3. **Savings:** ~30-40%

### Phase 2: Full Pipeline (Maximum Savings)
1. Use LiveKit Agents framework
2. Deepgram for STT ($0.0077/min)
3. Cerebras for LLM ($0.10-0.60/M tokens)
4. Cartesia for TTS ($0.05/1K chars)
5. **Savings:** ~70-80%

### Phase 3: Self-Hosted (If Hardware Available)
1. FastWhisper for STT
2. Ollama + Llama 3 for LLM
3. Chatterbox for TTS
4. **Savings:** 100% (zero API costs)

---

## Next Steps

1. **Get API keys:**
   - [Cerebras Cloud](https://cloud.cerebras.ai/) - Pay-per-token, starts at $10
   - [Deepgram Console](https://console.deepgram.com/) - $200 free credits
   - [Cartesia](https://cartesia.ai/) - Free tier with 20K credits

2. **Try LiveKit Agents:**
   ```bash
   pip install livekit-agents livekit-plugins-deepgram livekit-plugins-openai
   ```

3. **Test Cerebras speed:**
   - [Cerebras Chat](https://chat.cerebras.ai/) - Try it free
   - [Cerebras Voice Demo](https://cerebras.vercel.app/)

4. **Evaluate TTS options:**
   - [Fish Audio Playground](https://fish.audio)
   - [Cartesia Demo](https://cartesia.ai/sonic)

---

## Resources

### Tutorials
- [Build Voice Agent with LiveKit + AssemblyAI](https://www.assemblyai.com/blog/build-and-deploy-real-time-ai-voice-agents-using-livekit-and-assemblyai)
- [Cerebras Voice Agent Tutorial](https://inference-docs.cerebras.ai/cookbook/agents/livekit)
- [FreeCodeCamp: Voice AI with Open Source](https://www.freecodecamp.org/news/how-to-build-a-voice-ai-agent-using-open-source-tools/)

### Frameworks
- [LiveKit Agents](https://github.com/livekit/agents) - Most popular
- [Pipecat](https://github.com/pipecat-ai/pipecat) - Flexible mix-and-match
- [Vocode](https://github.com/vocodedev/vocode-python) - Python library

### Open Source TTS
- [Chatterbox](https://github.com/resemble-ai/chatterbox) - MIT license, 63.8% preferred over ElevenLabs
- [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) - #1 on HuggingFace TTS Arena
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) - Easy voice cloning
