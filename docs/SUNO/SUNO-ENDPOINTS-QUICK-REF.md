# Suno API Quick Reference

**Base URL:** `https://api.sunoapi.org`
**Auth:** `Authorization: Bearer YOUR_API_KEY`

---

## All Endpoints at a Glance

| Endpoint | Method | Path | Credits | Description |
|----------|--------|------|---------|-------------|
| **Generate Music** | POST | `/api/v1/generate` | 12 | Create music from prompt/lyrics |
| **Extend Music** | POST | `/api/v1/generate/extend` | 12 | Continue existing track |
| **Upload & Cover** | POST | `/api/v1/generate/upload-cover` | 12 | Restyle uploaded audio |
| **Upload & Extend** | POST | `/api/v1/generate/upload-extend` | 12 | Extend uploaded audio |
| **Add Instrumental** | POST | `/api/v1/generate/add-instrumental` | 12 | Add backing to vocals |
| **Add Vocals** | POST | `/api/v1/generate/add-vocals` | 12 | Add vocals to instrumental |
| **Replace Section** | POST | `/api/v1/generate/replace-section` | 5 | Replace part of a song |
| **Separate Vocals** | POST | `/api/v1/vocal-removal/generate` | 10/50 | Split vocals/stems |
| **WAV Conversion** | POST | `/api/v1/wav/generate` | 0.4 | Convert to WAV |
| **Generate Lyrics** | POST | `/api/v1/lyrics` | 0.4 | AI lyrics only |
| **Timestamped Lyrics** | POST | `/api/v1/generate/get-timestamped-lyrics` | 0.5 | Word-level timing |
| **Music Video** | POST | `/api/v1/mp4/generate` | 2 | Create MP4 video |
| **Generate Persona** | POST | `/api/v1/generate/generate-persona` | 0 | Create voice persona |
| **Check Status** | GET | `/api/v1/generate/record-info` | 0 | Task status |
| **Check Credits** | GET | `/api/v1/account/credits` | 0 | Credit balance |
| **WAV Status** | GET | `/api/v1/wav/record-info` | 0 | WAV conversion status |

---

## Common Request Patterns

### Generate a Song (Full Example)

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate" \
  -H "Authorization: Bearer $SUNO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "[Verse 1]\nYour lyrics here...\n\n[Chorus]\nCatchy chorus...",
    "customMode": true,
    "instrumental": false,
    "model": "V5",
    "style": "Country Rock, Upbeat",
    "title": "Song Title",
    "vocalGender": "m",
    "callBackUrl": "https://your-server.com/callback"
  }'
```

### Extend a Song

```bash
curl -X POST "https://api.sunoapi.org/api/v1/generate/extend" \
  -H "Authorization: Bearer $SUNO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "audioId": "AUDIO_ID_FROM_CALLBACK",
    "model": "V5",
    "continueAt": 60,
    "defaultParamFlag": true,
    "callBackUrl": "https://your-server.com/callback"
  }'
```

### Check Status

```bash
curl "https://api.sunoapi.org/api/v1/generate/record-info?taskId=YOUR_TASK_ID" \
  -H "Authorization: Bearer $SUNO_API_KEY"
```

---

## Models Quick Reference

| Model | Max Length | Prompt Limit | Best For |
|-------|------------|--------------|----------|
| `V5` | 8 min | 5000 chars | Best quality |
| `V4_5PLUS` | 8 min | 5000 chars | Rich sound |
| `V4_5ALL` | 8 min | 5000 chars | Structure |
| `V4_5` | 8 min | 5000 chars | Genre blend |
| `V4` | 4 min | 3000 chars | Reliable |

---

## Callback Types

| Type | Meaning |
|------|---------|
| `text` | Lyrics generated |
| `first` | First track ready |
| `complete` | All done |
| `error` | Failed |

---

## Status Values

| Status | Meaning |
|--------|---------|
| `PENDING` | Queued |
| `TEXT_SUCCESS` | Lyrics done |
| `FIRST_SUCCESS` | First track done |
| `SUCCESS` | Complete |
| `GENERATE_AUDIO_FAILED` | Failed |
| `SENSITIVE_WORD_ERROR` | Content blocked |

---

## Key Parameter Reference

### Generation Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `customMode` | true/false | Enable advanced options |
| `instrumental` | true/false | No vocals |
| `vocalGender` | "m" / "f" | Male/female vocals |
| `styleWeight` | 0.00-1.00 | How much to follow style |
| `weirdnessConstraint` | 0.00-1.00 | Creativity level |
| `audioWeight` | 0.00-1.00 | Input audio influence |

### Stem Separation Types

| Type | Stems | Credits |
|------|-------|---------|
| `separate_vocal` | 2 (vocals + instrumental) | 10 |
| `split_stem` | 12 (full separation) | 50 |

---

## Cost Calculator

| Action | Credits | USD ($0.005/credit) |
|--------|---------|---------------------|
| 1 song | 12 | $0.06 |
| 1 extended song | 24 | $0.12 |
| 10 songs | 120 | $0.60 |
| 100 songs | 1200 | $6.00 |
| Full stem split | 50 | $0.25 |

---

## Important IDs

- **taskId**: Returned from generation request, used for status checks
- **audioId**: Returned in callback `data[].id`, used for extend/stems/video
- **personaId**: Returned from persona generation, used in future generations

---

## File Retention

| Content | Retention |
|---------|-----------|
| Audio URLs | 14 days |
| WAV files | 15 days |
| Videos | 15 days |
| Lyrics | 15 days |
