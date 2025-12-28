# Suno API Use Cases for Pi-Guy / DJ-FoamBot

This document outlines potential integrations and features we could build using the Suno API.

---

## Current Implementation

### What We Have Now

1. **Song Generation** (`generate_song` tool)
   - User requests a song → Gemini enhances prompt → Suno generates
   - Callback saves MP3 to `generated_music/`
   - Auto-extend if song < 60 seconds
   - Pi-Guy can play via `play_music` tool

### Current Flow
```
User: "Make me a song about spray foam"
     ↓
Pi-Guy calls generate_song tool
     ↓
Server: Gemini enhances prompt → full lyrics
     ↓
Suno API: Generates 2 tracks (V5 model)
     ↓
Callback: Downloads MP3, auto-extends if short
     ↓
Pi-Guy: "Your song is ready! Playing it now..."
```

---

## Priority 1: High Value, Easy to Implement

### 1. Persona Creation for DJ-FoamBot

**Use Case:** Create a consistent "DJ-FoamBot voice" that all generated songs use.

**Implementation:**
1. Generate a good reference song with the style we want
2. Call Generate Persona endpoint with that song
3. Store `personaId` in config
4. All future generations use that persona

**Benefits:**
- Consistent voice/style across all DJ-FoamBot songs
- Unique brand identity for SprayFoamRadio.com
- FREE (0 credits)

**Code Change:**
```python
# In server.py generate_song endpoint
DJFOAMBOT_PERSONA_ID = "xxx"  # Get from persona generation

# Add to generation request
payload["personaId"] = DJFOAMBOT_PERSONA_ID
```

---

### 2. Lyrics-Only Generation

**Use Case:** Let users preview/edit lyrics before generating music.

**Implementation:**
1. Add `action=lyrics` to generate_song tool
2. Call `/api/v1/lyrics` endpoint
3. Return lyrics to user for approval
4. If approved, generate with those exact lyrics

**Benefits:**
- Cheaper iterations (0.4 vs 12 credits)
- User control over final lyrics
- Better quality songs from refined lyrics

**Tool Update:**
```
generate_song:
  action: "lyrics" | "generate" | "from_lyrics"
  prompt: "description"
  lyrics: "for from_lyrics action"
```

---

### 3. Song Variations/Remixes

**Use Case:** "Make a rock version of that last song"

**Implementation:**
1. Use Upload & Cover endpoint
2. Take existing generated song
3. Apply new style while keeping melody

**Benefits:**
- Quick genre variations
- Content variety for radio
- Same 12 credits as new song

---

## Priority 2: Medium Value, Medium Effort

### 4. Karaoke Mode (Stem Separation)

**Use Case:** "Give me the instrumental version"

**Implementation:**
1. Add `action=karaoke` to play_music tool
2. Call stem separation with `type=separate_vocal`
3. Save instrumental version separately
4. Play instrumental while user sings

**Benefits:**
- Interactive feature
- Party mode
- 10 credits per separation

**Stored Files:**
```
generated_music/
  song_123.mp3           # Original
  song_123_vocals.mp3    # Vocals only
  song_123_instrumental.mp3  # Karaoke version
```

---

### 5. Song Editing (Replace Section)

**Use Case:** "Change the chorus to be about roofing instead"

**Implementation:**
1. Add `action=edit` to generate_song tool
2. User specifies time range and new content
3. Call Replace Section endpoint
4. New section blends with original

**Benefits:**
- Fix mistakes without regenerating
- Customize existing songs
- Only 5 credits

---

### 6. Music Videos

**Use Case:** "Make a video for that song"

**Implementation:**
1. Add `action=video` to generate_song tool
2. Call Music Video endpoint with branding
3. Save MP4 to `generated_videos/`
4. Serve via new endpoint

**Benefits:**
- Social media content
- Visual branding for SprayFoamRadio
- Only 2 credits

**Example:**
```json
{
  "author": "DJ-FoamBot",
  "domainName": "SprayFoamRadio.com"
}
```

---

### 7. Timestamped Lyrics Display

**Use Case:** Show lyrics synced with playback (like karaoke)

**Implementation:**
1. Fetch timestamped lyrics on song load
2. Send to frontend via SSE
3. Display word-by-word as song plays

**Benefits:**
- Engaging visual element
- Professional feel
- 0.5 credits

**Frontend:**
```javascript
// Highlight words as they're sung
lyrics.forEach(word => {
  if (currentTime >= word.startS && currentTime < word.endS) {
    highlightWord(word.word);
  }
});
```

---

## Priority 3: Advanced Features

### 8. Full Stem Mixing Board

**Use Case:** "Turn down the drums" or "Remove the bass"

**Implementation:**
1. Full stem split (12 tracks)
2. Frontend audio mixer
3. Real-time mixing of stems

**Challenges:**
- 50 credits per split (expensive)
- Complex frontend audio mixing
- Large file storage (12 stems per song)

**Potential:**
- True DJ mixing capability
- Remix creation
- Mashup tools

---

### 9. Voice Upload for Covers

**Use Case:** User uploads their vocals, Suno adds music

**Implementation:**
1. Add voice upload endpoint
2. Use Add Instrumental feature
3. Generate backing track for user's voice

**Challenges:**
- File upload handling
- Voice quality requirements
- Privacy considerations

---

### 10. Song Continuation/Story Mode

**Use Case:** Generate a multi-part song series

**Implementation:**
1. Generate initial song
2. Auto-extend with narrative continuation
3. Create "chapters" or "parts"

**Example:**
```
Part 1: "The Foam Installer's Morning"
Part 2: "The Big Job"
Part 3: "The Satisfied Customer"
```

---

## Implementation Roadmap

### Phase 1: Quick Wins (This Week)
- [ ] Create DJ-FoamBot persona
- [ ] Add lyrics preview mode
- [ ] Store persona ID in config

### Phase 2: Core Features (Next Sprint)
- [ ] Karaoke mode (stem separation)
- [ ] Music video generation
- [ ] Song variations/covers

### Phase 3: Advanced (Future)
- [ ] Timestamped lyrics display
- [ ] Replace section editing
- [ ] Full stem mixer

---

## Cost Projections

| Feature | Credits/Use | Monthly Est. (50 uses) | USD |
|---------|-------------|------------------------|-----|
| Song Generation | 12 | 600 | $3.00 |
| Persona (one-time) | 0 | 0 | $0.00 |
| Lyrics Preview | 0.4 | 20 | $0.10 |
| Karaoke Split | 10 | 500 | $2.50 |
| Music Video | 2 | 100 | $0.50 |
| Full Stem Split | 50 | 2500 | $12.50 |

**Recommended Budget:** $10-20/month for moderate usage

---

## Technical Notes

### Callback Handling

All Suno operations are async with callbacks. Current implementation:

```python
@app.route('/api/suno/callback', methods=['POST'])
def suno_callback():
    data = request.json
    callback_type = data['data']['callbackType']

    if callback_type == 'complete':
        # Download and save audio
        # Auto-extend if needed
        # Update database
```

### File Organization

```
generated_music/
  ├── song_20251207_123456.mp3      # Generated songs
  ├── song_20251207_123456_ext.mp3  # Extended versions
  └── song_20251207_123456_inst.mp3 # Instrumentals

generated_videos/
  └── video_20251207_123456.mp4     # Music videos

personas/
  └── djfoambot.json                # Persona config
```

### Database Schema Addition

```sql
-- For tracking generated content
ALTER TABLE generated_songs ADD COLUMN persona_id TEXT;
ALTER TABLE generated_songs ADD COLUMN has_video BOOLEAN DEFAULT FALSE;
ALTER TABLE generated_songs ADD COLUMN has_stems BOOLEAN DEFAULT FALSE;
ALTER TABLE generated_songs ADD COLUMN stem_urls TEXT;  -- JSON
```

---

## API Integration Patterns

### Retry Logic

```python
async def call_suno_with_retry(endpoint, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await call_suno(endpoint, payload)
            return response
        except RateLimitError:
            await asyncio.sleep(2 ** attempt)
        except CreditError:
            raise  # Don't retry credit issues
```

### Webhook Verification

```python
def verify_suno_callback(request):
    # Verify callback is from Suno (if they provide signatures)
    # For now, just check expected structure
    return 'data' in request.json and 'callbackType' in request.json.get('data', {})
```

---

## Sources

- [Suno API Documentation](https://docs.sunoapi.org/)
- [gcui-art/suno-api GitHub](https://github.com/gcui-art/suno-api)
- [Suno V5 API Guide](https://suno-api.org/blog/2025/09-25-suno-v5-api)
