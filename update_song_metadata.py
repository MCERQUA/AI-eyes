#!/usr/bin/env python3
"""
Update Song Metadata from Transcriptions

This script:
1. Reads transcriptions from transcriptions/ folder
2. Renames generated songs (with hash names) to descriptive names
3. Updates music_metadata.json with transcription data
4. Updates the database with improved song info

Usage:
    python3 update_song_metadata.py --preview    # Preview changes without applying
    python3 update_song_metadata.py --apply      # Apply all changes
    python3 update_song_metadata.py --rename     # Only rename files
    python3 update_song_metadata.py --metadata   # Only update metadata
"""

import os
import sys
import json
import re
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
TRANSCRIPTIONS_DIR = BASE_DIR / "transcriptions"
MUSIC_DIR = BASE_DIR / "music"
GENERATED_DIR = BASE_DIR / "generated_music"
METADATA_FILE = MUSIC_DIR / "music_metadata.json"
DATABASE_FILE = BASE_DIR / "usage.db"


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a safe filename"""
    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text.strip())
    # Remove multiple hyphens
    text = re.sub(r'-+', '-', text)
    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    return text


def is_hash_filename(filename: str) -> bool:
    """Check if filename looks like a hash (UUID or hex string)"""
    stem = Path(filename).stem
    # UUID pattern: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', stem, re.I):
        return True
    # Hex hash pattern: 32 hex characters
    if re.match(r'^[0-9a-f]{32}$', stem, re.I):
        return True
    return False


def load_transcriptions() -> dict:
    """Load all transcription files"""
    transcriptions = {}
    if not TRANSCRIPTIONS_DIR.exists():
        return transcriptions

    for f in TRANSCRIPTIONS_DIR.glob("*.json"):
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
                transcriptions[f.stem] = data
        except Exception as e:
            print(f"Warning: Failed to load {f}: {e}")

    return transcriptions


def load_metadata() -> dict:
    """Load existing music_metadata.json"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_metadata(metadata: dict):
    """Save music_metadata.json"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {METADATA_FILE}")


def get_new_filename(transcription: dict) -> str:
    """Generate a new filename from transcription metadata"""
    improved = transcription.get("improved_metadata", {})
    title = improved.get("title", "")

    if not title:
        # Fall back to first few words of lyrics
        text = transcription.get("text", "")
        words = text.split()[:5]
        title = " ".join(words) if words else "Unknown"

    return slugify(title) + ".mp3"


def preview_renames(transcriptions: dict) -> list:
    """Preview what files would be renamed"""
    renames = []

    for stem, trans in transcriptions.items():
        old_filename = trans.get("file", "")
        if not old_filename:
            continue

        # Check if it's a hash filename that needs renaming
        if not is_hash_filename(old_filename):
            continue

        # Find the actual file
        old_path = GENERATED_DIR / old_filename
        if not old_path.exists():
            old_path = MUSIC_DIR / old_filename
        if not old_path.exists():
            print(f"Warning: File not found: {old_filename}")
            continue

        new_filename = get_new_filename(trans)
        new_path = old_path.parent / new_filename

        # Avoid conflicts
        if new_path.exists() and new_path != old_path:
            # Add number suffix
            base = new_path.stem
            for i in range(2, 100):
                new_path = old_path.parent / f"{base}-{i}.mp3"
                if not new_path.exists():
                    break
            new_filename = new_path.name

        if old_filename != new_filename:
            renames.append({
                "old_path": str(old_path),
                "new_path": str(new_path),
                "old_filename": old_filename,
                "new_filename": new_filename,
                "title": trans.get("improved_metadata", {}).get("title", "Unknown")
            })

    return renames


def apply_renames(renames: list) -> dict:
    """Apply file renames and return mapping of old->new"""
    mapping = {}

    for rename in renames:
        old_path = Path(rename["old_path"])
        new_path = Path(rename["new_path"])

        if old_path.exists():
            shutil.move(str(old_path), str(new_path))
            print(f"Renamed: {rename['old_filename']} -> {rename['new_filename']}")
            mapping[rename["old_filename"]] = rename["new_filename"]

            # Also rename the transcription file
            old_trans = TRANSCRIPTIONS_DIR / f"{old_path.stem}.json"
            new_trans = TRANSCRIPTIONS_DIR / f"{new_path.stem}.json"
            if old_trans.exists():
                shutil.move(str(old_trans), str(new_trans))
        else:
            print(f"Warning: File not found: {old_path}")

    return mapping


def update_metadata_from_transcriptions(transcriptions: dict, rename_mapping: dict = None) -> dict:
    """Create/update metadata entries from transcriptions"""
    metadata = load_metadata()
    rename_mapping = rename_mapping or {}

    for stem, trans in transcriptions.items():
        old_filename = trans.get("file", "")
        if not old_filename:
            continue

        # Use new filename if renamed
        filename = rename_mapping.get(old_filename, old_filename)

        # Get improved metadata
        improved = trans.get("improved_metadata", {})

        # Check if entry already exists
        if filename in metadata:
            # Update existing entry with transcription data
            entry = metadata[filename]
            if "transcribed_lyrics" not in entry:
                entry["transcribed_lyrics"] = trans.get("text", "")
            if improved:
                if not entry.get("description") or entry.get("description") == "":
                    entry["description"] = improved.get("description", "")
                if not entry.get("genre"):
                    entry["genre"] = improved.get("genre", "")
                if not entry.get("energy"):
                    entry["energy"] = improved.get("energy", "")
                if "themes" not in entry:
                    entry["themes"] = improved.get("themes", [])
                if "key_lyrics" not in entry:
                    entry["key_lyrics"] = improved.get("key_lyrics", "")
        else:
            # Create new entry
            duration = trans.get("duration", 0)
            metadata[filename] = {
                "title": improved.get("title", stem),
                "artist": "DJ FoamBot Productions",
                "duration_seconds": int(duration) if duration else 0,
                "description": improved.get("description", ""),
                "genre": improved.get("genre", ""),
                "energy": improved.get("energy", ""),
                "themes": improved.get("themes", []),
                "key_lyrics": improved.get("key_lyrics", ""),
                "transcribed_lyrics": trans.get("text", ""),
                "phone_number": None,
                "ad_copy": None,
                "fun_facts": []
            }

    return metadata


def update_database(rename_mapping: dict):
    """Update database with new filenames"""
    if not DATABASE_FILE.exists():
        print("Database not found, skipping database update")
        return

    if not rename_mapping:
        print("No renames to apply to database")
        return

    conn = sqlite3.connect(str(DATABASE_FILE))
    cursor = conn.cursor()

    for old_filename, new_filename in rename_mapping.items():
        cursor.execute(
            "UPDATE generated_songs SET local_file = ? WHERE local_file = ?",
            (new_filename, old_filename)
        )
        if cursor.rowcount > 0:
            print(f"Updated database: {old_filename} -> {new_filename}")

    conn.commit()
    conn.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update song metadata from transcriptions")
    parser.add_argument("--preview", action="store_true", help="Preview changes without applying")
    parser.add_argument("--apply", action="store_true", help="Apply all changes")
    parser.add_argument("--rename", action="store_true", help="Only rename files")
    parser.add_argument("--metadata", action="store_true", help="Only update metadata")

    args = parser.parse_args()

    if not any([args.preview, args.apply, args.rename, args.metadata]):
        args.preview = True

    print("Loading transcriptions...")
    transcriptions = load_transcriptions()
    print(f"Found {len(transcriptions)} transcriptions")

    # Preview renames
    renames = preview_renames(transcriptions)

    if args.preview or args.apply or args.rename:
        print(f"\n{'='*60}")
        print("FILE RENAMES")
        print(f"{'='*60}")
        if renames:
            for r in renames:
                print(f"  {r['old_filename']}")
                print(f"    -> {r['new_filename']}")
                print(f"    Title: {r['title']}")
                print()
        else:
            print("  No files need renaming")

    rename_mapping = {}

    if args.apply or args.rename:
        if renames:
            print("\nApplying renames...")
            rename_mapping = apply_renames(renames)
            print(f"Renamed {len(rename_mapping)} files")

    if args.preview or args.apply or args.metadata:
        print(f"\n{'='*60}")
        print("METADATA UPDATES")
        print(f"{'='*60}")

        new_metadata = update_metadata_from_transcriptions(transcriptions, rename_mapping)
        old_metadata = load_metadata()

        # Show what would be added/updated
        for filename, entry in new_metadata.items():
            if filename not in old_metadata:
                print(f"  NEW: {filename}")
                print(f"    Title: {entry.get('title', 'Unknown')}")
                print(f"    Genre: {entry.get('genre', 'Unknown')}")
                print()

        if args.apply or args.metadata:
            save_metadata(new_metadata)

    if args.apply:
        if rename_mapping:
            print("\nUpdating database...")
            update_database(rename_mapping)

    print("\nDone!")

    if args.preview:
        print("\nTo apply changes, run: python3 update_song_metadata.py --apply")


if __name__ == "__main__":
    main()
