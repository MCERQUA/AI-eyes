# DJ-FoamBot Cost Reduction Research

**Date:** 2024-12-14
**Purpose:** Document strategies for reducing or eliminating ElevenLabs costs while maintaining DJ radio experience

---

## Executive Summary

Several viable paths exist to reduce or eliminate ElevenLabs costs while keeping the fun DJ radio experience:

1. **Voice Caching** - Pre-generate common phrases (50-80% savings)
2. **Download Past Recordings** - Build clip library from existing conversations (FREE)
3. **Clip DJ System** - AI selects from pre-recorded clips ($0 after setup)
4. **Local TTS** - Open-source voice cloning (Fish Speech, OpenVoice) ($0)
5. **Hybrid Architecture** - Combine all approaches (90-95% cost reduction)

---

## Current ElevenLabs Audio Settings

**Status: AUDIO SAVING IS ENABLED**

```json
"privacy": {
  "record_voice": true,         // Audio recording enabled
  "retention_days": -1,         // Unlimited retention (never deleted)
  "delete_transcript_and_pii": false,
  "delete_audio": false,
  "zero_retention_mode": false
}
```

**Location:** `platform_settings.privacy` in agent config

---

## 1. ElevenLabs Voice Caching

### Official Recommendation
> "Cache your audio to avoid generating the same piece of audio multiple times. If your application frequently uses the same text phrases, generate the audio once and save the MP3 file."

### Implementation for DJ-FoamBot
Pre-generate and cache:
- Station IDs: "You're listening to SprayFoam Radio!"
- Transitions: "Up next...", "That was...", "Coming up..."
- Common reactions: "Nice!", "Let's go!", "Fire track!"
- Ad reads and commercial breaks
- DJ persona phrases

**Estimated savings:** 50-80% of TTS costs

---

## 2. Downloading Past Conversation Recordings

### API Endpoints

#### List All Conversations
```bash
GET https://api.elevenlabs.io/v1/convai/conversations
  ?agent_id=agent_0801kb2240vcea2ayx0a2qxmheha
  &page_size=100
```

**Query Parameters:**
- `agent_id` - Filter by agent
- `cursor` - Pagination
- `call_start_before_unix` / `call_start_after_unix` - Date filters
- `call_duration_min_secs` / `call_duration_max_secs` - Duration filters
- `page_size` - 1-100 (default 30)

#### Get Conversation Audio
```bash
GET https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}/audio
```

Returns: MP3/WAV audio file of the entire conversation

#### Get Conversation Details
```bash
GET https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}
```

Returns: Transcript, metadata, timestamps

### Download Script
See: `scripts/download_conversations.py`

---

## 3. The "Clip DJ" Concept

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    "Clip DJ" System                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   1. CLIP LIBRARY (Pre-recorded Pi-Guy voice)                │
│      ├── greetings/        (50+ variations)                  │
│      ├── song_intros/      (templates + song-specific)       │
│      ├── reactions/        (laughs, sighs, "bruh", etc.)     │
│      ├── transitions/      ("up next...", "that was...")     │
│      ├── ad_reads/         (commercial breaks)               │
│      ├── insults/          (sarcastic comebacks)             │
│      └── fillers/          ("anyway...", "so yeah...")       │
│                                                              │
│   2. AI SELECTOR (Local LLM - Ollama/llama.cpp)              │
│      - Analyzes context (what song just played, user input)  │
│      - Selects appropriate clips                             │
│      - Determines playback order & timing                    │
│      - Adds variety by mixing similar clips                  │
│                                                              │
│   3. CONCATENATION ENGINE                                    │
│      - Smooth transitions between clips                      │
│      - Volume normalization                                  │
│      - Optional: crossfade/effects                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### How It Works
1. **Build Clip Library:** Download past ElevenLabs conversations, segment with Whisper
2. **AI Selection:** Local LLM picks clips based on context
3. **Playback:** Concatenate selected clips with randomization

### Example Flow
```
Song "Bassline Inferno" ends
    ↓
AI analyzes: "high energy track just finished"
    ↓
AI selects:
  - reaction/yeah_03.mp3 ("YEAH!")
  - transition/that_was_07.mp3 ("That was...")
  - [song title - pre-recorded or local TTS]
  - filler/fire_track_02.mp3 ("Absolute fire!")
  - transition/next_up_04.mp3 ("Next up...")
    ↓
Clips concatenated & played
```

**Cost: $0** after initial clip generation

---

## 4. Open-Source TTS Alternatives

### Tier 1: Best Quality (GPU Required)

| Model | Quality | Speed | Voice Clone | License | Notes |
|-------|---------|-------|-------------|---------|-------|
| **Fish Speech 1.5** | ★★★★★ | 1:7 RT on 4090 | 15s sample | Apache 2.0 | #1 on TTS-Arena, 4GB VRAM |
| **OpenVoice V2** | ★★★★ | Fast | 10s sample | MIT | Great emotion control |
| **XTTS v2** | ★★★★ | Medium | 6s sample | Coqui License | 17 languages |
| **Bark** | ★★★★ | Slower | Limited | MIT | Can do laughs, music |

### Tier 2: Lightweight (Runs on Pi!)

| Model | Quality | Speed | Notes |
|-------|---------|-------|-------|
| **Piper** | ★★★ | Real-time | Perfect for Raspberry Pi |

### Resources
- Fish Speech: https://github.com/fishaudio/fish-speech
- OpenVoice: https://github.com/myshell-ai/OpenVoice
- XTTS v2: https://huggingface.co/coqui/XTTS-v2
- Bark: https://github.com/suno-ai/bark
- Piper: https://github.com/rhasspy/piper

---

## 5. Hybrid Architecture (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│               Hybrid DJ-FoamBot Architecture                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   LAYER 1: Pre-Recorded Clips ($0)                          │
│   ├── Station IDs, jingles, common phrases                   │
│   ├── Downloaded from past ElevenLabs conversations          │
│   └── Used for: 70% of DJ content                           │
│                                                              │
│   LAYER 2: Local TTS - Fish Speech ($0)                     │
│   ├── Song titles, dynamic announcements                     │
│   ├── Pi-Guy voice cloned from recordings                    │
│   └── Used for: 25% of DJ content                           │
│                                                              │
│   LAYER 3: ElevenLabs Conversational AI ($$)                │
│   ├── Interactive conversations with users                   │
│   ├── Complex responses requiring real intelligence          │
│   └── Used for: 5% of content (user interactions only)       │
│                                                              │
│   RESULT: 90-95% cost reduction!                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. ElevenLabs Retention Settings Reference

### Configuration Options
- **retention_days:** Number of days to keep data
  - `-1` = Unlimited (current setting)
  - `0` = Immediate deletion
  - Any positive number = days to retain

### How to Modify via API
```bash
curl -X PATCH "https://api.elevenlabs.io/v1/convai/agents/{agent_id}" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "platform_settings": {
      "privacy": {
        "record_voice": true,
        "retention_days": -1
      }
    }
  }'
```

### Via Dashboard
1. Go to ElevenLabs → Agents → Select Agent
2. Click "Advanced" tab
3. Find "Privacy Settings" section
4. Toggle audio saving / set retention period
5. Save changes

---

## 7. Cost Comparison

| Approach | Monthly Cost | Quality | Interactivity |
|----------|-------------|---------|---------------|
| Current (100% ElevenLabs) | $$$ | ★★★★★ | Full |
| + Caching common phrases | $$ | ★★★★★ | Full |
| Hybrid (clips + local TTS) | $ | ★★★★ | Limited DJ, full chat |
| Full clip-based DJ | $0 | ★★★ | None (pre-recorded) |
| Local TTS only | $0 | ★★★★ | Full (but local LLM) |

---

## 8. Implementation Checklist

### Quick Wins (Do Now)
- [x] Audio saving enabled in ElevenLabs ✅
- [ ] Download all past conversations
- [ ] Create clips folder structure
- [ ] Categorize Pi-Guy's best lines

### Medium Term
- [ ] Clone Pi-Guy's voice using Fish Speech
- [ ] Pre-generate common DJ phrases
- [ ] Build clip selection system

### Long Term
- [ ] Replace most DJ content with hybrid system
- [ ] Keep ElevenLabs only for live conversations
- [ ] Consider Piper for edge deployment

---

## Sources

- [ElevenLabs API Pricing](https://elevenlabs.io/pricing/api)
- [ElevenLabs Retention Documentation](https://elevenlabs.io/docs/agents-platform/customization/privacy/retention)
- [Get Conversation Audio API](https://elevenlabs.io/docs/api-reference/conversations/get-audio)
- [List Conversations API](https://elevenlabs.io/docs/conversational-ai/api-reference/conversations/list)
- [Fish Speech GitHub](https://github.com/fishaudio/fish-speech)
- [OpenVoice GitHub](https://github.com/myshell-ai/OpenVoice)
- [Piper TTS GitHub](https://github.com/rhasspy/piper)
- [Bark GitHub](https://github.com/suno-ai/bark)
- [XTTS v2 on Hugging Face](https://huggingface.co/coqui/XTTS-v2)
