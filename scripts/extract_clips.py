#!/usr/bin/env python3
"""
Extract audio clips from DJ-FoamBot conversation recordings.

Uses transcript timestamps to extract individual Pi-Guy responses as separate clips.
Automatically categorizes clips based on content analysis.

Requirements:
    - ffmpeg (install with: sudo apt install ffmpeg)

Usage:
    python3 scripts/extract_clips.py                    # Extract from all conversations
    python3 scripts/extract_clips.py --limit 5          # Extract from first 5 conversations
    python3 scripts/extract_clips.py --radio-only       # Only Radio Voice conversations
    python3 scripts/extract_clips.py --conversation-id conv_xxx  # Specific conversation
    python3 scripts/extract_clips.py --dry-run          # Preview without extracting
"""

import os
import sys
import json
import re
import subprocess
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# Directories
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DJ_CLIPS_DIR = PROJECT_DIR / 'dj-clips'
AUDIO_DIR = DJ_CLIPS_DIR / 'audio'
TRANSCRIPTS_DIR = DJ_CLIPS_DIR / 'transcripts'
CLIPS_DIR = DJ_CLIPS_DIR / 'clips'

# Category folders
CATEGORIES = {
    'greetings': CLIPS_DIR / 'greetings',
    'transitions': CLIPS_DIR / 'transitions',
    'reactions': CLIPS_DIR / 'reactions',
    'ad-reads': CLIPS_DIR / 'ad-reads',
    'station-ids': CLIPS_DIR / 'station-ids',
    'fillers': CLIPS_DIR / 'fillers',
    'dj-intros': CLIPS_DIR / 'dj-intros',
    'song-outros': CLIPS_DIR / 'song-outros',
    'uncategorized': CLIPS_DIR / 'uncategorized',
}

# Category detection patterns
CATEGORY_PATTERNS = {
    'station-ids': [
        r'sprayfoamradio\.com',
        r'sprayfoam\s*radio',
        r'dj[\-\s]*foambot',
        r'you\'re listening to',
        r'this is .* radio',
    ],
    'greetings': [
        r'^(hey|hi|yo|what\'s up|mike!|well)',
        r'good (morning|afternoon|evening)',
        r'welcome back',
        r'finally.*here',
    ],
    'transitions': [
        r'(next up|up next|coming up)',
        r'(that was|and that was)',
        r'let\'s (go|keep|switch)',
        r'alright alright',
        r'here we go',
        r'moving on',
    ],
    'reactions': [
        r'^(yeah|whoo|oh|damn|fire|nice|boom)',
        r'that\'s (fire|heat|dope)',
        r'absolute (fire|heat|banger)',
        r'let\'s go!*$',
    ],
    'ad-reads': [
        r'\d{3}[\-\s]*\d{3}[\-\s]*\d{4}',  # Phone numbers
        r'call (us|them|now)',
        r'visit .*(\.com|\.ca)',
        r'bbb.*rated',
        r'family[\-\s]owned',
    ],
    'dj-intros': [
        r'spinning',
        r'dropping',
        r'playing.*for you',
        r'check this out',
        r'this (one|track|joint)',
    ],
    'song-outros': [
        r'that was.*by',
        r'shout\s*out',
        r'big ups',
        r'respect to',
    ],
    'fillers': [
        r'^(anyway|so yeah|you know|like)',
        r'my bad',
        r'hold up',
        r'wait wait',
    ],
}


# ffmpeg path (check common locations)
FFMPEG_PATH = None
for path in ['/home/mike/bin/ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', 'ffmpeg']:
    try:
        result = subprocess.run([path, '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            FFMPEG_PATH = path
            break
    except FileNotFoundError:
        continue


def check_ffmpeg() -> bool:
    """Check if ffmpeg is installed."""
    return FFMPEG_PATH is not None


def categorize_clip(text: str, has_radio_voice: bool) -> str:
    """Determine category for a clip based on its text content."""
    text_lower = text.lower()

    # Check each category's patterns
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return category

    # Default: if it has Radio Voice, it's probably a DJ intro
    if has_radio_voice:
        return 'dj-intros'

    return 'uncategorized'


def extract_clip(
    audio_path: Path,
    output_path: Path,
    start_time: float,
    duration: float,
    dry_run: bool = False
) -> bool:
    """Extract a clip from audio file using ffmpeg."""
    if dry_run:
        print(f"    [DRY RUN] Would extract: {start_time:.1f}s - {start_time + duration:.1f}s")
        return True

    try:
        cmd = [
            FFMPEG_PATH,
            '-i', str(audio_path),
            '-ss', str(start_time),
            '-t', str(duration),
            '-acodec', 'libmp3lame',
            '-ab', '128k',
            '-y',  # Overwrite output
            '-loglevel', 'error',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"    Error extracting clip: {e}")
        return False


def generate_clip_filename(text: str, conv_id: str, index: int) -> str:
    """Generate a unique filename for a clip."""
    # Create a short hash from the text
    text_hash = hashlib.md5(text.encode()).hexdigest()[:6]

    # Clean the text for filename (first 30 chars)
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    clean_text = re.sub(r'\s+', '-', clean_text.strip())[:30].lower()

    return f"{conv_id[:20]}_{index:03d}_{clean_text}_{text_hash}.mp3"


def has_radio_voice_tag(text: str) -> bool:
    """Check if text contains Radio Voice tags."""
    return '<Radio Voice>' in text or '<RadioVoice>' in text


def clean_radio_voice_tags(text: str) -> str:
    """Remove Radio Voice XML tags from text."""
    text = re.sub(r'</?Radio\s*Voice>', '', text, flags=re.IGNORECASE)
    return text.strip()


def process_conversation(
    conv_id: str,
    dry_run: bool = False,
    min_duration: float = 1.0,
    max_duration: float = 30.0
) -> Dict:
    """Process a single conversation and extract clips."""

    audio_path = AUDIO_DIR / f"{conv_id}.mp3"
    transcript_path = TRANSCRIPTS_DIR / f"{conv_id}.json"

    if not audio_path.exists():
        return {'error': f"Audio file not found: {audio_path}"}
    if not transcript_path.exists():
        return {'error': f"Transcript not found: {transcript_path}"}

    # Load transcript
    with open(transcript_path) as f:
        data = json.load(f)

    transcript = data.get('transcript', [])
    if not transcript:
        return {'error': "Empty transcript"}

    results = {
        'conversation_id': conv_id,
        'clips_extracted': 0,
        'clips_skipped': 0,
        'categories': {},
        'clips': []
    }

    # Process each agent response
    for i, entry in enumerate(transcript):
        if entry.get('role') != 'agent':
            continue

        message = entry.get('message', '') or ''
        if not message.strip():
            continue

        # Get timing
        start_time = entry.get('time_in_call_secs', 0) or 0

        # Calculate duration: time until next entry or default
        if i + 1 < len(transcript):
            next_time = transcript[i + 1].get('time_in_call_secs', 0) or 0
            if next_time > start_time:
                duration = next_time - start_time
            else:
                # Estimate based on text length (~150 words/minute, ~5 chars/word)
                duration = min(len(message) / 750 * 60, 15)
        else:
            # Last entry: estimate duration
            duration = min(len(message) / 750 * 60, 15)

        # Apply duration limits
        if duration < min_duration:
            results['clips_skipped'] += 1
            continue
        if duration > max_duration:
            duration = max_duration

        # Check for Radio Voice
        has_radio = has_radio_voice_tag(message)
        clean_message = clean_radio_voice_tags(message)

        # Categorize
        category = categorize_clip(clean_message, has_radio)

        # Generate filename
        filename = generate_clip_filename(clean_message, conv_id, i)
        output_path = CATEGORIES.get(category, CATEGORIES['uncategorized']) / filename

        # Extract clip
        success = extract_clip(
            audio_path,
            output_path,
            start_time,
            duration,
            dry_run=dry_run
        )

        if success:
            results['clips_extracted'] += 1
            results['categories'][category] = results['categories'].get(category, 0) + 1
            results['clips'].append({
                'filename': filename,
                'category': category,
                'start_time': start_time,
                'duration': round(duration, 2),
                'has_radio_voice': has_radio,
                'text': clean_message[:100] + ('...' if len(clean_message) > 100 else ''),
                'full_text': clean_message
            })
        else:
            results['clips_skipped'] += 1

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Extract audio clips from DJ-FoamBot conversations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scripts/extract_clips.py --dry-run          # Preview extraction
    python3 scripts/extract_clips.py --limit 3          # Process 3 conversations
    python3 scripts/extract_clips.py --radio-only       # Only Radio Voice content
    python3 scripts/extract_clips.py --min-duration 2   # Skip clips under 2 seconds
        """
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview extraction without creating files')
    parser.add_argument('--limit', type=int, default=None,
                        help='Maximum conversations to process')
    parser.add_argument('--radio-only', action='store_true',
                        help='Only process conversations with Radio Voice')
    parser.add_argument('--conversation-id', type=str, default=None,
                        help='Process specific conversation ID')
    parser.add_argument('--min-duration', type=float, default=1.0,
                        help='Minimum clip duration in seconds (default: 1.0)')
    parser.add_argument('--max-duration', type=float, default=30.0,
                        help='Maximum clip duration in seconds (default: 30.0)')

    args = parser.parse_args()

    # Check ffmpeg
    if not args.dry_run and not check_ffmpeg():
        print("ERROR: ffmpeg is not installed!")
        print("")
        print("Install ffmpeg with:")
        print("    sudo apt install ffmpeg")
        print("")
        print("Or use --dry-run to preview extraction without ffmpeg")
        sys.exit(1)

    # Ensure category directories exist
    for category_dir in CATEGORIES.values():
        category_dir.mkdir(parents=True, exist_ok=True)

    # Load manifest to get conversation list
    manifest_path = DJ_CLIPS_DIR / 'manifest.json'
    if not manifest_path.exists():
        print("ERROR: manifest.json not found. Run create_manifest.py first.")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    conversations = manifest.get('conversations', [])

    # Filter conversations
    if args.conversation_id:
        conversations = [c for c in conversations if c['conversation_id'] == args.conversation_id]
        if not conversations:
            print(f"ERROR: Conversation {args.conversation_id} not found")
            sys.exit(1)

    if args.radio_only:
        conversations = [c for c in conversations if c.get('has_radio_voice', False)]
        print(f"Filtered to {len(conversations)} conversations with Radio Voice")

    if args.limit:
        conversations = conversations[:args.limit]

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processing {len(conversations)} conversations...")
    print("=" * 60)

    total_clips = 0
    total_skipped = 0
    all_categories = {}
    clips_index = []

    for i, conv in enumerate(conversations, 1):
        conv_id = conv['conversation_id']
        duration = conv.get('duration_formatted', '??:??')

        print(f"\n[{i}/{len(conversations)}] {conv_id} ({duration})")

        results = process_conversation(
            conv_id,
            dry_run=args.dry_run,
            min_duration=args.min_duration,
            max_duration=args.max_duration
        )

        if 'error' in results:
            print(f"    ERROR: {results['error']}")
            continue

        print(f"    Extracted: {results['clips_extracted']} clips")
        print(f"    Skipped: {results['clips_skipped']} (too short)")
        if results['categories']:
            cats = ', '.join(f"{k}: {v}" for k, v in results['categories'].items())
            print(f"    Categories: {cats}")

        total_clips += results['clips_extracted']
        total_skipped += results['clips_skipped']

        for cat, count in results['categories'].items():
            all_categories[cat] = all_categories.get(cat, 0) + count

        clips_index.extend(results['clips'])

    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Total clips extracted: {total_clips}")
    print(f"Total skipped: {total_skipped}")
    print(f"\nBy category:")
    for cat, count in sorted(all_categories.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}")

    # Save clips index
    if not args.dry_run and clips_index:
        index_path = CLIPS_DIR / 'clips_index.json'
        with open(index_path, 'w') as f:
            json.dump({
                'created': datetime.now().isoformat(),
                'total_clips': total_clips,
                'categories': all_categories,
                'clips': clips_index
            }, f, indent=2)
        print(f"\nClips index saved to: {index_path}")

    print(f"\nClips saved to: {CLIPS_DIR}")


if __name__ == '__main__':
    main()
