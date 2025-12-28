#!/usr/bin/env python3
"""
Download all past conversation recordings from ElevenLabs.

This script fetches conversation history and downloads audio files
for building a clip library for DJ-FoamBot.

Usage:
    python3 scripts/download_conversations.py
    python3 scripts/download_conversations.py --limit 10
    python3 scripts/download_conversations.py --since 2024-01-01
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime
from pathlib import Path

# Load environment variables from .env
def load_env():
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

API_KEY = os.environ.get('ELEVENLABS_API_KEY')
AGENT_ID = os.environ.get('ELEVENLABS_AGENT_ID', 'agent_0801kb2240vcea2ayx0a2qxmheha')
BASE_URL = 'https://api.elevenlabs.io/v1/convai'
HEADERS = {'xi-api-key': API_KEY}

# Output directories
RECORDINGS_DIR = Path(__file__).parent.parent / 'dj-clips' / 'audio'
TRANSCRIPTS_DIR = Path(__file__).parent.parent / 'dj-clips' / 'transcripts'


def get_conversations(agent_id=None, page_size=100, since_date=None, cursor=None):
    """Fetch list of conversations from ElevenLabs API."""
    params = {'page_size': page_size}

    if agent_id:
        params['agent_id'] = agent_id
    if cursor:
        params['cursor'] = cursor
    if since_date:
        # Convert date string to unix timestamp
        dt = datetime.strptime(since_date, '%Y-%m-%d')
        params['call_start_after_unix'] = int(dt.timestamp())

    response = requests.get(
        f'{BASE_URL}/conversations',
        headers=HEADERS,
        params=params
    )

    if response.status_code != 200:
        print(f"Error fetching conversations: {response.status_code}")
        print(response.text)
        return None

    return response.json()


def get_conversation_details(conversation_id):
    """Get detailed info about a specific conversation."""
    response = requests.get(
        f'{BASE_URL}/conversations/{conversation_id}',
        headers=HEADERS
    )

    if response.status_code != 200:
        print(f"Error fetching conversation {conversation_id}: {response.status_code}")
        return None

    return response.json()


def download_conversation_audio(conversation_id, output_path):
    """Download audio for a specific conversation."""
    response = requests.get(
        f'{BASE_URL}/conversations/{conversation_id}/audio',
        headers=HEADERS,
        stream=True
    )

    if response.status_code != 200:
        print(f"Error downloading audio for {conversation_id}: {response.status_code}")
        return False

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return True


def format_duration(seconds):
    """Format seconds into mm:ss."""
    if seconds is None:
        return "??:??"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def main():
    parser = argparse.ArgumentParser(description='Download ElevenLabs conversation recordings')
    parser.add_argument('--limit', type=int, default=None, help='Maximum conversations to download')
    parser.add_argument('--since', type=str, default=None, help='Only download since date (YYYY-MM-DD)')
    parser.add_argument('--list-only', action='store_true', help='List conversations without downloading')
    parser.add_argument('--with-transcripts', action='store_true', help='Also save transcripts as JSON')
    args = parser.parse_args()

    if not API_KEY:
        print("Error: ELEVENLABS_API_KEY not found in environment")
        sys.exit(1)

    # Create output directories
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    if args.with_transcripts:
        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching conversations for agent: {AGENT_ID}")
    print("-" * 60)

    all_conversations = []
    cursor = None

    while True:
        result = get_conversations(
            agent_id=AGENT_ID,
            page_size=100,
            since_date=args.since,
            cursor=cursor
        )

        if not result or 'conversations' not in result:
            break

        conversations = result.get('conversations', [])
        all_conversations.extend(conversations)

        print(f"Fetched {len(all_conversations)} conversations so far...")

        # Check for more pages
        cursor = result.get('next_cursor')
        if not cursor:
            break

        # Check limit
        if args.limit and len(all_conversations) >= args.limit:
            all_conversations = all_conversations[:args.limit]
            break

    print(f"\nTotal conversations found: {len(all_conversations)}")
    print("=" * 60)

    if not all_conversations:
        print("No conversations found!")
        return

    # Process each conversation
    downloaded = 0
    skipped = 0
    errors = 0

    for i, conv in enumerate(all_conversations, 1):
        conv_id = conv.get('conversation_id')
        start_time = conv.get('start_time_unix_secs', 0)
        duration = conv.get('call_duration_secs')
        status = conv.get('status', 'unknown')

        # Format date
        date_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M') if start_time else 'Unknown'

        print(f"\n[{i}/{len(all_conversations)}] {conv_id}")
        print(f"    Date: {date_str}")
        print(f"    Duration: {format_duration(duration)}")
        print(f"    Status: {status}")

        if args.list_only:
            continue

        # Check if already downloaded
        audio_path = RECORDINGS_DIR / f"{conv_id}.mp3"
        if audio_path.exists():
            print(f"    -> Already exists, skipping")
            skipped += 1
            continue

        # Download audio
        print(f"    -> Downloading audio...")
        if download_conversation_audio(conv_id, audio_path):
            file_size = audio_path.stat().st_size / 1024 / 1024
            print(f"    -> Saved: {audio_path.name} ({file_size:.2f} MB)")
            downloaded += 1
        else:
            print(f"    -> Failed to download audio")
            errors += 1

        # Save transcript if requested
        if args.with_transcripts:
            details = get_conversation_details(conv_id)
            if details:
                transcript_path = TRANSCRIPTS_DIR / f"{conv_id}.json"
                with open(transcript_path, 'w') as f:
                    json.dump(details, f, indent=2)
                print(f"    -> Saved transcript")

    print("\n" + "=" * 60)
    print(f"Download complete!")
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped (existing): {skipped}")
    print(f"  Errors: {errors}")
    print(f"\nRecordings saved to: {RECORDINGS_DIR}")

    if args.with_transcripts:
        print(f"Transcripts saved to: {TRANSCRIPTS_DIR}")


if __name__ == '__main__':
    main()
