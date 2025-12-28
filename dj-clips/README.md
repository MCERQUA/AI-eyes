# DJ-FoamBot Clips Library

**Created:** 2025-12-14

## Summary

| Metric | Value |
|--------|-------|
| Total Conversations | 250 |
| Total Duration | 10:18:41 |
| Total Size | 709.2 MB |
| With Radio Voice | 109 |

## Folder Structure

```
dj-clips/
├── audio/          # MP3 recordings (250 files)
├── transcripts/    # JSON transcripts with full conversation text
├── clips/          # Extracted clips (organized by category)
│   ├── greetings/
│   ├── transitions/
│   ├── reactions/
│   ├── ad-reads/
│   ├── station-ids/
│   └── fillers/
├── manifest.json   # This index file
└── README.md       # This file
```

## Top 10 Longest Conversations

| Date | Duration | Size | Radio Voice | Preview |
|------|----------|------|-------------|---------|
| Unknown | 41:38 | 54.9MB | ✓ | Do you have any idea what you just interrupted? |
| Unknown | 39:48 | 36.4MB | ✓ | Oh look, it's Mike. Did you bring me that 3D print... |
| Unknown | 22:19 | 20.4MB | ✓ | Oh Mike's here! Should I put 'Jetson Thor' on my C... |
| Unknown | 18:33 | 17.2MB | ✓ | Yo Mike! DJ FoamBot here. Ready to rock SprayFoamR... |
| Unknown | 17:22 | 15.9MB | ✓ | Mike! The Thor has Blackwell architecture. BLACKWE... |
| Unknown | 15:40 | 14.6MB | ✓ | Well fuck me, it's Mike. This better be good. |
| Unknown | 14:33 | 13.4MB | ✓ | Spoiler alert: whatever you're about to ask, I'm g... |
| Unknown | 13:55 | 14.8MB | ✓ | Jesus Christ Mike, finally. I was starting to thin... |
| Unknown | 13:35 | 12.4MB | ✓ | Plot development incoming. What narrative arc are ... |
| Unknown | 12:18 | 11.3MB | ✓ | Hey Mike. I was just working on my plans for world... |

## Usage

### View manifest
```bash
cat dj-clips/manifest.json | python3 -m json.tool
```

### Find Radio Voice conversations
```bash
cat dj-clips/manifest.json | python3 -c "import sys,json; d=json.load(sys.stdin); [print(c['conversation_id'], c['duration_formatted']) for c in d['conversations'] if c['has_radio_voice']]"
```

### Search transcripts for a phrase
```bash
grep -r "SprayFoamRadio" dj-clips/transcripts/
```

## Next Steps

1. **Extract clips** - Use Whisper to segment audio by transcript timestamps
2. **Categorize** - Move clips into appropriate folders
3. **Build soundboard** - Create quick-access system for DJ clips
4. **Voice clone** - Use Fish Speech to clone Pi-Guy's voice for new content
