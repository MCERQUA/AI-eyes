# Suno API Reference (Current Implementation)

Documentation for the Suno API used by Pi-Guy/DJ-FoamBot for AI song generation.

**See Also:**
- **[SUNO-API-REFERENCE.md](./SUNO-API-REFERENCE.md)** - Complete API documentation (all endpoints)
- **[SUNO-ENDPOINTS-QUICK-REF.md](./SUNO-ENDPOINTS-QUICK-REF.md)** - Quick reference table
- **[SUNO-USE-CASES.md](./SUNO-USE-CASES.md)** - Future integration ideas

---

**API Provider:** [sunoapi.org](https://sunoapi.org)
**Documentation:** [docs.sunoapi.org](https://docs.sunoapi.org)
**Pricing:** Each credit = $0.005 USD

## Current Configuration

- **API Base URL:** `https://api.sunoapi.org`
- **Model:** V5 (latest, best quality)
- **Callback URL:** `https://ai-guy.mikecerqua.ca/api/suno/callback`

## Available Endpoints

### Music Generation (12 credits each)

| Endpoint | Model | Description |
|----------|-------|-------------|
| Generate Music (V5) | V5 | Latest model - best quality, up to 8 min |
| Generate Music (V4.5+) | V4_5PLUS | Enhanced V4.5, richer sound, up to 8 min |
| Generate Music (V4.5) | V4_5 | Superior genre blending, up to 8 min |
| Generate Music (V4) | V4 | Best audio quality, up to 4 min |
| Generate Music (V4.5ALL) | V4_5ALL | Better song structure, up to 8 min |

### Extend Music (12 credits each)

| Endpoint | Model | Description |
|----------|-------|-------------|
| Extend Music (V5) | V5 | Extend existing track with V5 |
| Extend Music (V4.5+) | V4_5PLUS | Extend with V4.5+ |
| Extend Music (V4.5) | V4_5 | Extend with V4.5 |
| Extend Music (V4) | V4 | Extend with V4 |
| Extend Music (V4.5ALL) | V4_5ALL | Extend with V4.5ALL |

### Audio Processing

| Endpoint | Credits | Description |
|----------|---------|-------------|
| Upload And Cover Audio | 12 | Create AI cover of uploaded audio |
| Upload And Extend Audio | 12 | Upload audio and extend it |
| Add Instrumental | 12 | Add instrumental track to vocals |
| Add Vocals | 12 | Add vocals to instrumental |
| Separate Vocals from Music | 10 | Split vocals from instrumental |
| Split Stem | 50 | Full stem separation (vocals, bass, drums, etc.) |
| Replace Music Section | 5 | Replace part of a song |
| Convert to WAV Format | 0.4 | Convert to lossless WAV |

### Content Generation

| Endpoint | Credits | Description |
|----------|---------|-------------|
| Generate Lyrics | 0.4 | AI-generated lyrics |
| Get Timestamped Lyrics | 0.5 | Get lyrics with timestamps |
| Boost Musik Stil | 0.4 | Enhance/boost music style |
| Generate Music Cover | 0 | Generate cover art |
| Create Music Video | 2 | Create video for track |
| Generate Persona | 0 | Create voice persona |

### Status/Info (Free - 0 credits)

| Endpoint | Description |
|----------|-------------|
| Get Music Generation Details | Check generation status |
| Get Remaining Credits | Check credit balance |
| Get Music Cover Details | Cover generation status |
| Get Lyrics Generation Details | Lyrics generation status |
| Get WAV Conversion Details | WAV conversion status |
| Get Vocal Separation Details | Separation job status |
| Get Music Video Details | Video generation status |

## API Request Format

### Generate Music (V5)

```bash
POST https://api.sunoapi.org/api/v1/generate
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "prompt": "[Verse 1]\nLyrics here...\n\n[Chorus]\nChorus lyrics...",
  "customMode": true,
  "instrumental": false,
  "model": "V5",
  "style": "Rock, Energetic, Radio-friendly",
  "title": "Song Title",
  "callBackUrl": "https://your-server.com/callback",
  "negativeTags": "Heavy Metal, Screaming",
  "vocalGender": "m",
  "styleWeight": 0.65,
  "weirdnessConstraint": 0.65,
  "audioWeight": 0.65
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Song description or lyrics (with section tags for full songs) |
| `customMode` | boolean | No | Enable advanced settings (recommended: true) |
| `instrumental` | boolean | No | Generate instrumental only (no vocals) |
| `model` | enum | No | V5, V4_5PLUS, V4_5ALL, V4_5, V4 |
| `style` | string | No | Genre/style description |
| `title` | string | No | Song title |
| `callBackUrl` | URI | No | Webhook for completion notification |
| `personaId` | string | No | Use specific voice persona |
| `negativeTags` | string | No | Styles to avoid |
| `vocalGender` | enum | No | "m" or "f" |
| `styleWeight` | number | No | Style influence (0-1) |
| `weirdnessConstraint` | number | No | Creativity level (0-1) |
| `audioWeight` | number | No | Audio influence (0-1) |

### Response Format

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "taskId": "task_abc123..."
  }
}
```

### Callback Format

When generation completes, Suno POSTs to your callback URL:

```json
{
  "code": 200,
  "data": {
    "task_id": "task_abc123...",
    "callbackType": "complete",
    "data": [
      {
        "id": "song_id_1",
        "title": "Song Title",
        "audio_url": "https://...",
        "stream_audio_url": "https://...",
        "image_url": "https://...",
        "duration": 180.5,
        "model": "V5"
      },
      {
        "id": "song_id_2",
        ...
      }
    ]
  }
}
```

**Note:** Each generation creates 2 songs. We use the first one.

## Song Length Tips

To generate **full-length songs** (not short clips):

1. **Use V5 or V4.5 models** - Support up to 8 minutes
2. **Use customMode: true** - Enables better control
3. **Include section tags in lyrics:**
   ```
   [Verse 1]
   First verse lyrics here...

   [Chorus]
   Catchy chorus lyrics...

   [Verse 2]
   Second verse lyrics...

   [Chorus]
   Repeat chorus...

   [Bridge]
   Bridge section...

   [Outro]
   Ending...
   ```

4. **Use the Extend endpoint** to make songs longer after generation

## Model Comparison

| Model | Max Length | Quality | Speed | Best For |
|-------|------------|---------|-------|----------|
| V5 | 8 min | Best | Fast | Production quality |
| V4.5+ | 8 min | Excellent | Fast | Rich sound |
| V4.5ALL | 8 min | Excellent | Medium | Song structure |
| V4.5 | 8 min | Great | Fast | Genre blending |
| V4 | 4 min | Great | Medium | Refined structure |

## Pi-Guy Implementation

Our implementation in `server.py`:

1. User requests song via ElevenLabs `generate_song` tool
2. Gemini enhances prompt → full lyrics with section tags
3. Suno API generates with V5 model + customMode
4. Callback receives audio URLs + `suno_audio_id`
5. We download MP3 to `generated_music/` folder
6. **AUTO-EXTEND**: If song < 60 seconds, automatically call Extend API
7. Extended version downloads when ready
8. Pi-Guy can play via `play_music` or `generate_song action=play`

### Auto-Extend Feature

Songs under 60 seconds are automatically extended:

```
[Initial Generation]
  ↓
Callback received (duration: 20s)
  ↓
Auto-extend triggered (continueAt: 15s)
  ↓
New callback with extended version
  ↓
Extended song saved (duration: ~2-3 min)
```

**Database columns for extending:**
- `suno_audio_id` - Suno's audio ID (needed for extend API)
- `is_extended` - Flag to prevent infinite extend loops
- `parent_song_id` - Links extended version to original

### Extend API Request

```bash
POST https://api.sunoapi.org/api/v1/generate/extend
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "defaultParamFlag": true,
  "audioId": "8551****662c",
  "model": "V5",
  "prompt": "Original lyrics...",
  "style": "Rock, Energetic",
  "title": "Song Title (Extended)",
  "continueAt": 15,
  "callBackUrl": "https://ai-guy.mikecerqua.ca/api/suno/callback"
}
```

**Key parameters:**
- `audioId` - The `id` from the original song callback (NOT task_id!)
- `continueAt` - Where to start extending (seconds from start)
- `model` - Must match original song's model

### Local Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/suno?action=generate&prompt=...` | GET | Start generation |
| `/api/suno?action=status&task_id=...` | GET | Check progress |
| `/api/suno?action=list` | GET | List generated songs |
| `/api/suno?action=play&song_id=...` | GET | Play a generated song |
| `/api/suno/callback` | POST | Receives Suno callback |
| `/generated_music/<filename>` | GET | Serve audio file |

## Callback Data Reference

When Suno completes generation, it POSTs:

```json
{
  "code": 200,
  "msg": "All generated successfully.",
  "data": {
    "callbackType": "complete",
    "task_id": "2fac****9f72",
    "data": [
      {
        "id": "8551****662c",        // THIS is suno_audio_id for extending!
        "audio_url": "https://...",
        "stream_audio_url": "https://...",
        "image_url": "https://...",
        "prompt": "[Verse 1]...",
        "model_name": "chirp-v5",
        "title": "Song Title",
        "tags": "rock, energetic",
        "duration": 198.44
      }
    ]
  }
}
```

**Callback types:**
- `text` - Lyrics generated
- `first` - First track ready
- `complete` - All tracks ready
- `error` - Generation failed

## Future Ideas

Endpoints we could use later:

- **Add Vocals/Instrumental** - Remix capabilities
- **Separate Vocals** - Karaoke mode
- **Split Stem** - Full mixing control
- **Generate Lyrics** - Let Suno write lyrics
- **Create Music Video** - Auto-generate videos
- **Generate Persona** - Custom voice for DJ-FoamBot

## Cost Estimates

| Action | Credits | USD |
|--------|---------|-----|
| Generate 1 song | 12 | $0.06 |
| Extend song | 12 | $0.06 |
| Separate vocals | 10 | $0.05 |
| Full stem split | 50 | $0.25 |
| Generate lyrics | 0.4 | $0.002 |
| Get status | 0 | Free |
