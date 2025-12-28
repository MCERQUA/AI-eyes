#!/usr/bin/env python3
"""
Create a manifest/index of all downloaded DJ conversations.
Extracts metadata from transcripts and creates a searchable index.
"""

import os
import json
from datetime import datetime
from pathlib import Path

DJ_CLIPS_DIR = Path(__file__).parent.parent / 'dj-clips'
AUDIO_DIR = DJ_CLIPS_DIR / 'audio'
TRANSCRIPTS_DIR = DJ_CLIPS_DIR / 'transcripts'
MANIFEST_PATH = DJ_CLIPS_DIR / 'manifest.json'
README_PATH = DJ_CLIPS_DIR / 'README.md'


def format_duration(seconds):
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds is None or seconds == 0:
        return "00:00"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def get_file_size_mb(filepath):
    """Get file size in MB."""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0


def extract_agent_lines(transcript):
    """Extract all Pi-Guy (agent) lines from transcript."""
    lines = []
    for entry in transcript:
        if entry.get('role') == 'agent':
            msg = entry.get('message', '') or ''
            if msg.strip():
                lines.append(msg)
    return lines


def has_radio_voice(transcript):
    """Check if conversation uses Radio Voice."""
    for entry in transcript:
        if entry.get('role') == 'agent':
            msg = entry.get('message', '') or ''
            if '<Radio Voice>' in msg or '<RadioVoice>' in msg:
                return True
    return False


def count_transcript_entries(transcript):
    """Count agent and user entries."""
    agent_count = sum(1 for e in transcript if e.get('role') == 'agent' and e.get('message'))
    user_count = sum(1 for e in transcript if e.get('role') == 'user' and e.get('message'))
    return agent_count, user_count


def get_duration_from_transcript(transcript):
    """Get duration from last transcript entry's time_in_call_secs."""
    if not transcript:
        return 0
    # Find the max time_in_call_secs
    max_time = 0
    for entry in transcript:
        time_in_call = entry.get('time_in_call_secs', 0) or 0
        if time_in_call > max_time:
            max_time = time_in_call
    return max_time


def main():
    print("Creating manifest of DJ clips...")

    manifest = {
        'created': datetime.now().isoformat(),
        'total_conversations': 0,
        'total_duration_seconds': 0,
        'total_size_mb': 0,
        'conversations': []
    }

    # Process each transcript
    transcript_files = sorted(TRANSCRIPTS_DIR.glob('*.json'))

    for transcript_path in transcript_files:
        conv_id = transcript_path.stem
        audio_path = AUDIO_DIR / f"{conv_id}.mp3"

        try:
            with open(transcript_path) as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {transcript_path}: {e}")
            continue

        # Extract metadata
        transcript = data.get('transcript', [])
        duration = data.get('call_duration_secs') or get_duration_from_transcript(transcript)
        start_time = data.get('start_time_unix_secs', 0)
        status = data.get('status', 'unknown')

        agent_lines, user_lines = count_transcript_entries(transcript)
        has_dj_voice = has_radio_voice(transcript)
        file_size = get_file_size_mb(audio_path)

        # Extract first agent line as preview
        first_line = ""
        for entry in transcript:
            if entry.get('role') == 'agent' and entry.get('message'):
                first_line = (entry.get('message', '') or '')[:100]
                break

        conv_entry = {
            'conversation_id': conv_id,
            'date': datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M') if start_time else 'Unknown',
            'duration_seconds': duration,
            'duration_formatted': format_duration(duration),
            'status': status,
            'file_size_mb': round(file_size, 2),
            'agent_responses': agent_lines,
            'user_messages': user_lines,
            'has_radio_voice': has_dj_voice,
            'preview': first_line,
            'audio_file': f"audio/{conv_id}.mp3",
            'transcript_file': f"transcripts/{conv_id}.json"
        }

        manifest['conversations'].append(conv_entry)
        manifest['total_duration_seconds'] += duration
        manifest['total_size_mb'] += file_size

    manifest['total_conversations'] = len(manifest['conversations'])
    manifest['total_size_mb'] = round(manifest['total_size_mb'], 2)
    manifest['total_duration_formatted'] = format_duration(manifest['total_duration_seconds'])

    # Sort by date (newest first)
    manifest['conversations'].sort(key=lambda x: x['date'], reverse=True)

    # Save manifest
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved manifest to {MANIFEST_PATH}")

    # Create README
    readme = f"""# DJ-FoamBot Clips Library

**Created:** {manifest['created'][:10]}

## Summary

| Metric | Value |
|--------|-------|
| Total Conversations | {manifest['total_conversations']} |
| Total Duration | {manifest['total_duration_formatted']} |
| Total Size | {manifest['total_size_mb']:.1f} MB |
| With Radio Voice | {sum(1 for c in manifest['conversations'] if c['has_radio_voice'])} |

## Folder Structure

```
dj-clips/
├── audio/          # MP3 recordings ({manifest['total_conversations']} files)
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
"""

    # Add top 10 by duration
    top_by_duration = sorted(manifest['conversations'], key=lambda x: x['duration_seconds'], reverse=True)[:10]
    for conv in top_by_duration:
        preview = conv['preview'][:50] + '...' if len(conv['preview']) > 50 else conv['preview']
        dj = '✓' if conv['has_radio_voice'] else ''
        readme += f"| {conv['date']} | {conv['duration_formatted']} | {conv['file_size_mb']:.1f}MB | {dj} | {preview} |\n"

    readme += f"""
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
"""

    with open(README_PATH, 'w') as f:
        f.write(readme)
    print(f"Saved README to {README_PATH}")

    # Print summary
    print("\n" + "=" * 60)
    print("DJ CLIPS LIBRARY SUMMARY")
    print("=" * 60)
    print(f"Total conversations: {manifest['total_conversations']}")
    print(f"Total duration: {manifest['total_duration_formatted']}")
    print(f"Total size: {manifest['total_size_mb']:.1f} MB")
    print(f"With Radio Voice: {sum(1 for c in manifest['conversations'] if c['has_radio_voice'])}")
    print("=" * 60)


if __name__ == '__main__':
    main()
