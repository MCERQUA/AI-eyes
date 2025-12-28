# Suno API Complete Reference

**API Provider:** [sunoapi.org](https://sunoapi.org)
**Documentation:** [docs.sunoapi.org](https://docs.sunoapi.org)
**Base URL:** `https://api.sunoapi.org`
**Authentication:** Bearer Token (`Authorization: Bearer YOUR_API_KEY`)
**Pricing:** 1 credit = $0.005 USD

---

## Table of Contents

1. [Music Generation](#1-music-generation)
2. [Extend Music](#2-extend-music)
3. [Upload & Cover Audio](#3-upload--cover-audio)
4. [Upload & Extend Audio](#4-upload--extend-audio)
5. [Add Instrumental](#5-add-instrumental)
6. [Add Vocals](#6-add-vocals)
7. [Replace Music Section](#7-replace-music-section)
8. [Stem Separation](#8-stem-separation)
9. [WAV Conversion](#9-wav-conversion)
10. [Lyrics Generation](#10-lyrics-generation)
11. [Timestamped Lyrics](#11-timestamped-lyrics)
12. [Music Video Generation](#12-music-video-generation)
13. [Persona Generation](#13-persona-generation)
14. [Status & Credits](#14-status--credits)
15. [File Upload Methods](#15-file-upload-methods)
16. [Callback Reference](#16-callback-reference)
17. [Model Comparison](#17-model-comparison)
18. [Error Codes](#18-error-codes)

---

## 1. Music Generation

Generate AI music from text prompts or lyrics.

### Endpoint
```
POST /api/v1/generate
```

### Credits: 12 per generation (creates 2 tracks)

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Song description or full lyrics with section tags. Max: 3000 chars (V4), 5000 chars (V4.5+) |
| `customMode` | boolean | No | Enable advanced settings (recommended: true) |
| `instrumental` | boolean | No | Generate without vocals |
| `model` | enum | No | `V5`, `V4_5PLUS`, `V4_5ALL`, `V4_5`, `V4` |
| `style` | string | Conditional | Genre/style (required if customMode=true). Max: 200 chars (V4), 1000 chars (V4.5+) |
| `title` | string | No | Track title. Max: 80 chars (V4/V4_5ALL), 100 chars (V4.5+) |
| `callBackUrl` | string (URI) | No | Webhook for completion notification |
| `personaId` | string | No | Use specific voice persona |
| `negativeTags` | string | No | Styles to avoid (e.g., "Heavy Metal, Screaming") |
| `vocalGender` | enum | No | `m` or `f` |
| `styleWeight` | number | No | Style influence (0.00-1.00) |
| `weirdnessConstraint` | number | No | Creativity level (0.00-1.00) |
| `audioWeight` | number | No | Audio consistency (0.00-1.00) |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "[Verse 1]\nSpray foam insulation, keeping homes tight\nEnergy savings day and night\n\n[Chorus]\nFoam it up, seal it right\nSpray foam makes everything airtight",
    "customMode": true,
    "instrumental": false,
    "model": "V5",
    "style": "Country Rock, Upbeat, Radio-friendly",
    "title": "Foam It Up",
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback",
    "vocalGender": "m"
  }'
```

### Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "5c79****be8e"
  }
}
```

### Callback Payload (on completion)

```json
{
  "code": 200,
  "msg": "All generated successfully.",
  "data": {
    "callbackType": "complete",
    "task_id": "5c79****be8e",
    "data": [
      {
        "id": "8551****662c",
        "audio_url": "https://cdn.suno.ai/...",
        "stream_audio_url": "https://cdn.suno.ai/...",
        "image_url": "https://cdn.suno.ai/...",
        "prompt": "[Verse 1]...",
        "model_name": "chirp-v5",
        "title": "Foam It Up",
        "tags": "country rock, upbeat",
        "duration": 198.44
      },
      {
        "id": "9442****773d",
        ...
      }
    ]
  }
}
```

**Note:** Each generation creates 2 song variations. Use the `id` field for extending.

---

## 2. Extend Music

Continue an existing track to make it longer.

### Endpoint
```
POST /api/v1/generate/extend
```

### Credits: 12 per extension

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audioId` | string | Yes | The `id` from the original song callback (NOT taskId) |
| `model` | enum | Yes | Must match original song's model |
| `callBackUrl` | string (URI) | Yes | Webhook URL |
| `defaultParamFlag` | boolean | No | Set true to use custom parameters |
| `continueAt` | number | Conditional | Seconds from start where extension begins |
| `prompt` | string | Conditional | Extension description/lyrics |
| `style` | string | Conditional | Music style for extension |
| `title` | string | No | Track title |
| `personaId` | string | No | Custom persona |
| `negativeTags` | string | No | Styles to avoid |
| `vocalGender` | enum | No | `m` or `f` |
| `styleWeight` | number | No | 0.00-1.00 |
| `weirdnessConstraint` | number | No | 0.00-1.00 |
| `audioWeight` | number | No | 0.00-1.00 |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate/extend" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "audioId": "8551****662c",
    "model": "V5",
    "defaultParamFlag": true,
    "continueAt": 15,
    "prompt": "[Verse 2]\nFrom the attic to the basement floor...",
    "style": "Country Rock, Upbeat",
    "title": "Foam It Up (Extended)",
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback"
  }'
```

### Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "7a82****cf91"
  }
}
```

---

## 3. Upload & Cover Audio

Transform uploaded audio into a new style while retaining the core melody.

### Endpoint
```
POST /api/v1/generate/upload-cover
```

### Credits: 12

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uploadUrl` | string (URI) | Yes | Audio file URL (max 8 min, 1 min for V4_5ALL) |
| `customMode` | boolean | Yes | Enable advanced settings |
| `instrumental` | boolean | Yes | Output without lyrics |
| `model` | enum | Yes | `V5`, `V4_5PLUS`, `V4_5ALL`, `V4_5`, `V4` |
| `callBackUrl` | string (URI) | Yes | Webhook URL |
| `style` | string | Conditional | Required if customMode=true |
| `title` | string | Conditional | Required if customMode=true |
| `prompt` | string | Conditional | Required if customMode=true AND instrumental=false (used as exact lyrics) |
| `personaId` | string | No | Apply specific persona |
| `negativeTags` | string | No | Styles to exclude |
| `vocalGender` | enum | No | `m` or `f` |
| `styleWeight` | number | No | 0.00-1.00 |
| `weirdnessConstraint` | number | No | 0.00-1.00 |
| `audioWeight` | number | No | 0.00-1.00 |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate/upload-cover" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "uploadUrl": "https://example.com/my-song.mp3",
    "customMode": true,
    "instrumental": false,
    "model": "V5",
    "style": "Electronic, Synthwave",
    "title": "My Song (Synthwave Cover)",
    "prompt": "[Verse 1]\nNew lyrics here...",
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback"
  }'
```

---

## 4. Upload & Extend Audio

Extend uploaded audio while preserving its original style.

### Endpoint
```
POST /api/v1/generate/upload-extend
```

### Credits: 12

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uploadUrl` | string (URI) | Yes | Audio file URL (max 8 min) |
| `continueAt` | number | Yes | Seconds from start to begin extension (must be > 0 and < audio duration) |
| `model` | enum | Yes | Model version |
| `callBackUrl` | string (URI) | Yes | Webhook URL |
| `customMode` | boolean | No | Enable advanced settings |
| `style` | string | Conditional | Style for extension |
| `title` | string | No | Track title |
| `prompt` | string | No | Extension lyrics/description |
| `negativeTags` | string | No | Styles to avoid |
| `vocalGender` | enum | No | `m` or `f` |
| `styleWeight` | number | No | 0.00-1.00 |
| `weirdnessConstraint` | number | No | 0.00-1.00 |
| `audioWeight` | number | No | 0.00-1.00 |

---

## 5. Add Instrumental

Generate musical accompaniment for an uploaded vocal/melody track.

### Endpoint
```
POST /api/v1/generate/add-instrumental
```

### Credits: 12

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uploadUrl` | string (URI) | Yes | Vocal/melody track URL (MP3, WAV) |
| `title` | string | Yes | Track title (max 100 chars) |
| `tags` | string | Yes | Desired instrumental style/mood |
| `negativeTags` | string | Yes | Styles to exclude |
| `callBackUrl` | string (URI) | Yes | Webhook URL |
| `vocalGender` | enum | No | `m` or `f` |
| `styleWeight` | number | No | 0.00-1.00 |
| `weirdnessConstraint` | number | No | 0.00-1.00 |
| `audioWeight` | number | No | 0.00-1.00 |
| `model` | enum | No | Default: V4_5PLUS |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate/add-instrumental" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "uploadUrl": "https://example.com/vocals-only.mp3",
    "title": "My Song with Backing",
    "tags": "Acoustic Guitar, Soft Piano, Mellow",
    "negativeTags": "Heavy Metal, Electronic",
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback",
    "model": "V5"
  }'
```

---

## 6. Add Vocals

Generate AI vocals for an uploaded instrumental track.

### Endpoint
```
POST /api/v1/generate/add-vocals
```

### Credits: 12

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uploadUrl` | string (URI) | Yes | Instrumental track URL |
| `prompt` | string | Yes | Lyrics or vocal description |
| `title` | string | Yes | Track title (max 100 chars) |
| `style` | string | Yes | Vocal style (e.g., "Jazz", "Pop") |
| `negativeTags` | string | Yes | Styles to avoid |
| `callBackUrl` | string (URI) | Yes | Webhook URL |
| `vocalGender` | enum | No | `m` or `f` |
| `styleWeight` | number | No | 0.00-1.00 |
| `weirdnessConstraint` | number | No | 0.00-1.00 |
| `audioWeight` | number | No | 0.00-1.00 |
| `model` | enum | No | Default: V4_5PLUS |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate/add-vocals" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "uploadUrl": "https://example.com/instrumental.mp3",
    "prompt": "[Verse 1]\nWalking down the road...",
    "title": "Road Trip Song",
    "style": "Country, Folk",
    "negativeTags": "Rap, Screaming",
    "vocalGender": "f",
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback"
  }'
```

---

## 7. Replace Music Section

Replace a specific time segment within an existing track.

### Endpoint
```
POST /api/v1/generate/replace-section
```

### Credits: 5

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `taskId` | string | Yes | Original track's task ID |
| `audioId` | string | Yes | Audio ID to modify |
| `prompt` | string | Yes | Description for replacement section |
| `tags` | string | Yes | Style tags for replacement |
| `title` | string | Yes | Track title |
| `infillStartS` | number | Yes | Start time in seconds (2 decimal places) |
| `infillEndS` | number | Yes | End time in seconds (2 decimal places) |
| `negativeTags` | string | No | Styles to exclude |
| `callBackUrl` | string (URI) | No | Webhook URL |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate/replace-section" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "5c79****be8e",
    "audioId": "8551****662c",
    "prompt": "Epic guitar solo, soaring melody",
    "tags": "Rock, Guitar Solo, Epic",
    "title": "My Song with New Solo",
    "infillStartS": 45.00,
    "infillEndS": 75.00,
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback"
  }'
```

**Note:** Replacement segments automatically blend with surrounding audio.

---

## 8. Stem Separation

Separate a track into individual stems (vocals, instruments, etc.).

### Endpoint
```
POST /api/v1/vocal-removal/generate
```

### Credits: 10 (separate_vocal) or 50 (split_stem)

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `taskId` | string | Yes | Original music generation task ID |
| `audioId` | string | Yes | Audio ID to process |
| `callBackUrl` | string (URI) | Yes | Webhook URL |
| `type` | enum | No | `separate_vocal` (default) or `split_stem` |

### Separation Modes

| Mode | Stems Returned | Use Case |
|------|----------------|----------|
| `separate_vocal` | 2 (Vocals + Instrumental) | Karaoke, basic remixes |
| `split_stem` | Up to 12 | Advanced mixing, remixing |

**12-Stem Breakdown:**
- Vocals, Backing Vocals, Drums, Bass, Guitar, Keyboard, Strings, Brass, Woodwinds, Percussion, Synth, FX/Other

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/vocal-removal/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "5c79****be8e",
    "audioId": "8551****662c",
    "type": "split_stem",
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback"
  }'
```

### Callback Payload

```json
{
  "code": 200,
  "data": {
    "task_id": "...",
    "original_audio_url": "https://...",
    "vocals_url": "https://...",
    "instrumental_url": "https://...",
    "drums_url": "https://...",
    "bass_url": "https://...",
    ...
  }
}
```

**Note:** Audio URLs remain accessible for 14 days.

---

## 9. WAV Conversion

Convert generated tracks to lossless WAV format.

### Endpoint
```
POST /api/v1/wav/generate
```

### Credits: 0.4

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `taskId` | string | Yes | Music generation task ID |
| `audioId` | string | Yes | Audio ID to convert |
| `callBackUrl` | string (URI) | Yes | Webhook URL |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/wav/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "5c79****be8e",
    "audioId": "8551****662c",
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback"
  }'
```

### Callback Payload

```json
{
  "code": 200,
  "data": {
    "task_id": "...",
    "wav_url": "https://..."
  }
}
```

### Status Check (Alternative to Callback)
```
GET /api/v1/wav/record-info?taskId=xxx
```

**Note:** WAV files are retained for 15 days and are significantly larger than MP3.

---

## 10. Lyrics Generation

Generate AI lyrics without audio.

### Endpoint
```
POST /api/v1/lyrics
```

### Credits: 0.4

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Description of desired lyrics (max 200 words) |
| `callBackUrl` | string (URI) | Yes | Webhook URL |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/lyrics" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A country song about spray foam insulation contractors working hard, staying positive, and building something that lasts",
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback"
  }'
```

### Callback Payload

```json
{
  "code": 200,
  "msg": "All generated successfully",
  "data": {
    "callbackType": "complete",
    "taskId": "11dc****8b0f",
    "data": [
      {
        "text": "[Verse 1]\nUp before the sun...\n\n[Chorus]\nWe're building something...",
        "title": "Building Something Strong",
        "status": "complete"
      }
    ]
  }
}
```

**Note:** Generated lyrics include section markers and can be used directly in the Generate Music endpoint.

---

## 11. Timestamped Lyrics

Get word-by-word timestamps for lyric synchronization.

### Endpoint
```
POST /api/v1/generate/get-timestamped-lyrics
```

### Credits: 0.5

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `taskId` | string | Yes | Music generation task ID |
| `audioId` | string | Yes | Audio ID |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate/get-timestamped-lyrics" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "5c79****be8e",
    "audioId": "8551****662c"
  }'
```

### Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "alignedWords": [
      {
        "word": "Up",
        "success": true,
        "startS": 0.52,
        "endS": 0.78,
        "palign": 1
      },
      {
        "word": "before",
        "success": true,
        "startS": 0.78,
        "endS": 1.12,
        "palign": 1
      }
    ],
    "waveformData": [0.1, 0.3, 0.5, ...],
    "hootCer": 0.95,
    "isStreamed": false
  }
}
```

**Note:** Instrumental tracks (instrumental=true) will not have lyrics data.

---

## 12. Music Video Generation

Create synchronized MP4 videos for tracks.

### Endpoint
```
POST /api/v1/mp4/generate
```

### Credits: 2

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `taskId` | string | Yes | Music generation task ID |
| `audioId` | string | Yes | Audio ID to make video for |
| `callBackUrl` | string (URI) | Yes | Webhook URL |
| `author` | string | No | Artist name displayed (max 50 chars) |
| `domainName` | string | No | Website/brand watermark (max 50 chars) |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/mp4/generate" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "5c79****be8e",
    "audioId": "8551****662c",
    "author": "DJ-FoamBot",
    "domainName": "SprayFoamRadio.com",
    "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback"
  }'
```

### Callback Payload

```json
{
  "code": 200,
  "msg": "MP4 generated successfully.",
  "data": {
    "task_id": "...",
    "video_url": "https://example.com/videos/video_847715e66259.mp4"
  }
}
```

**Note:** Videos retained for 15 days. Includes synchronized visual effects.

---

## 13. Persona Generation

Create a reusable voice/style persona from an existing track.

### Endpoint
```
POST /api/v1/generate/generate-persona
```

### Credits: 0 (FREE)

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `taskId` | string | Yes | Original music task ID (must be from V4 or higher) |
| `audioId` | string | Yes | Audio ID to base persona on |
| `name` | string | Yes | Persona name (e.g., "DJ-FoamBot Voice") |
| `description` | string | Yes | Musical characteristics, style, personality |

### Example Request

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate/generate-persona" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "5c79****be8e",
    "audioId": "8551****662c",
    "name": "DJ-FoamBot Voice",
    "description": "Energetic male radio DJ voice, upbeat country rock style, catchy hooks"
  }'
```

### Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "personaId": "a1b2****c3d4",
    "name": "DJ-FoamBot Voice",
    "description": "Energetic male radio DJ voice..."
  }
}
```

**Usage:** Include `personaId` in future generation requests to use this voice.

---

## 14. Status & Credits

### Get Music Generation Details

Check status of any generation task.

```
GET /api/v1/generate/record-info?taskId=xxx
```

### Response

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "5c79****be8e",
    "status": "SUCCESS",
    "type": "chirp-v5",
    "operationType": "generate",
    "response": {
      "sunoData": [
        {
          "id": "8551****662c",
          "audioUrl": "https://...",
          "streamAudioUrl": "https://...",
          "imageUrl": "https://...",
          "title": "...",
          "duration": 198.44
        }
      ]
    }
  }
}
```

### Status Values

| Status | Description |
|--------|-------------|
| `PENDING` | Task queued |
| `TEXT_SUCCESS` | Lyrics generated |
| `FIRST_SUCCESS` | First track ready |
| `SUCCESS` | All tracks complete |
| `CREATE_TASK_FAILED` | Task creation failed |
| `GENERATE_AUDIO_FAILED` | Audio generation failed |
| `CALLBACK_EXCEPTION` | Callback delivery failed |
| `SENSITIVE_WORD_ERROR` | Content filter triggered |

### Get Remaining Credits

```
GET /api/v1/account/credits
```

### Response

```json
{
  "code": 200,
  "data": {
    "credits_remaining": 1250.5
  }
}
```

---

## 15. File Upload Methods

Three methods available for uploading audio to Suno:

### 1. URL Upload (Recommended)

Just provide a publicly accessible URL in the `uploadUrl` parameter:
```json
{
  "uploadUrl": "https://your-server.com/audio.mp3"
}
```

### 2. Base64 Upload

```
POST /api/v1/upload/base64
```

```json
{
  "filename": "audio.mp3",
  "content": "base64_encoded_audio_data..."
}
```

### 3. Stream Upload

```
POST /api/v1/upload/stream
Content-Type: multipart/form-data

file: <binary audio data>
```

---

## 16. Callback Reference

### Callback Types

| Type | Description |
|------|-------------|
| `text` | Lyrics/text generated (first stage) |
| `first` | First track ready |
| `complete` | All tracks finished |
| `error` | Generation failed |

### Standard Callback Structure

```json
{
  "code": 200,
  "msg": "status message",
  "data": {
    "callbackType": "complete",
    "task_id": "xxx",
    "data": [...]
  }
}
```

### Track Object (in callback data array)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Audio ID (use for extend/stem separation) |
| `audio_url` | string | Download URL for MP3 |
| `stream_audio_url` | string | Streaming URL |
| `image_url` | string | Album art URL |
| `prompt` | string | Original prompt/lyrics |
| `model_name` | string | Model used (e.g., "chirp-v5") |
| `title` | string | Track title |
| `tags` | string | Style tags |
| `duration` | number | Length in seconds |

---

## 17. Model Comparison

| Model | Max Length | Quality | Speed | Best For |
|-------|------------|---------|-------|----------|
| **V5** | 8 min | Best | Fast | Production quality, vocals |
| **V4_5PLUS** | 8 min | Excellent | Fast | Rich, full sound |
| **V4_5ALL** | 8 min | Excellent | Medium | Song structure |
| **V4_5** | 8 min | Great | Fast | Genre blending |
| **V4** | 4 min | Great | Medium | Refined structure |

### Prompt Length Limits

| Model | Prompt | Style | Title |
|-------|--------|-------|-------|
| V4 | 3000 chars | 200 chars | 80 chars |
| V4.5+ | 5000 chars | 1000 chars | 100 chars |

---

## 18. Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Invalid parameters |
| 401 | Unauthorized (check API key) |
| 402 | Payment required |
| 404 | Resource not found |
| 405 | Method not allowed |
| 409 | Conflict (e.g., task already exists) |
| 413 | Prompt/content too long |
| 422 | Unprocessable entity |
| 429 | Rate limit exceeded |
| 430 | Call frequency too high |
| 451 | Content policy violation |
| 455 | System maintenance |
| 500 | Server error |

---

## Quick Reference: Endpoint Costs

| Endpoint | Credits | USD |
|----------|---------|-----|
| Generate Music | 12 | $0.06 |
| Extend Music | 12 | $0.06 |
| Upload & Cover | 12 | $0.06 |
| Upload & Extend | 12 | $0.06 |
| Add Instrumental | 12 | $0.06 |
| Add Vocals | 12 | $0.06 |
| Replace Section | 5 | $0.025 |
| Separate Vocals | 10 | $0.05 |
| Full Stem Split | 50 | $0.25 |
| WAV Conversion | 0.4 | $0.002 |
| Generate Lyrics | 0.4 | $0.002 |
| Timestamped Lyrics | 0.5 | $0.0025 |
| Music Video | 2 | $0.01 |
| Generate Persona | 0 | FREE |
| Status Check | 0 | FREE |
| Credit Check | 0 | FREE |

---

## Sources

- [Suno API Documentation](https://docs.sunoapi.org/)
- [Suno API Music Generation](https://docs.sunoapi.org/suno-api/generate-music)
- [Suno API Extend Music](https://docs.sunoapi.org/suno-api/extend-music)
- [Suno API Stem Separation](https://docs.sunoapi.org/suno-api/separate-vocals-from-music)
- [Suno API Create Music Video](https://docs.sunoapi.org/suno-api/create-music-video)
- [Suno API Generate Persona](https://sunoapiorg.mintlify.app/suno-api/generate-persona)
- [gcui-art/suno-api GitHub](https://github.com/gcui-art/suno-api)
