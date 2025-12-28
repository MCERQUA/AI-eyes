#!/usr/bin/env python3
"""
Song Transcription Script using faster-whisper

Transcribes songs from the music/ and generated_music/ folders,
saves transcriptions, and can use Gemini to generate improved metadata.

Uses faster-whisper (no FFmpeg required - bundles PyAV).

Usage:
    python3 transcribe_songs.py                    # Transcribe all songs
    python3 transcribe_songs.py --file song.mp3   # Transcribe specific file
    python3 transcribe_songs.py --improve         # Also improve metadata with Gemini
    python3 transcribe_songs.py --list            # List songs and their transcription status
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# faster-whisper model sizes: tiny, base, small, medium, large-v3
# Use base for speed on CPU, large-v3 for best accuracy
DEFAULT_MODEL = "base"

# Cache the model to avoid reloading
_cached_model = None
_cached_model_name = None

def load_whisper_model(model_name: str = DEFAULT_MODEL):
    """Load faster-whisper model (cached)"""
    global _cached_model, _cached_model_name

    if _cached_model is not None and _cached_model_name == model_name:
        return _cached_model

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ERROR: faster-whisper not installed.")
        print("Run: pip3 install --break-system-packages faster-whisper")
        sys.exit(1)

    print(f"Loading faster-whisper model '{model_name}'...")
    # Use CPU with int8 quantization for speed
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    _cached_model = model
    _cached_model_name = model_name
    return model

def get_transcription_path(audio_path: str) -> str:
    """Get the path where transcription should be saved"""
    audio_path = Path(audio_path)
    transcription_dir = Path(__file__).parent / "transcriptions"
    transcription_dir.mkdir(exist_ok=True)
    return str(transcription_dir / f"{audio_path.stem}.json")

def transcribe_audio(audio_path: str, model_name: str = DEFAULT_MODEL) -> dict:
    """Transcribe an audio file using faster-whisper"""
    model = load_whisper_model(model_name)

    print(f"Transcribing: {audio_path}")
    segments, info = model.transcribe(audio_path, beam_size=5, word_timestamps=True)

    # Collect all segments
    segment_list = []
    full_text_parts = []
    for segment in segments:
        segment_list.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
        full_text_parts.append(segment.text.strip())

    full_text = " ".join(full_text_parts)

    return {
        "file": os.path.basename(audio_path),
        "path": audio_path,
        "text": full_text,
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "segments": segment_list,
        "transcribed_at": datetime.now().isoformat(),
        "model": model_name
    }

def save_transcription(transcription: dict, output_path: str):
    """Save transcription to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(transcription, f, indent=2)
    print(f"Saved transcription to: {output_path}")

def load_transcription(path: str) -> dict:
    """Load existing transcription"""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def get_all_songs() -> list:
    """Get all song files from music/ and generated_music/"""
    base_dir = Path(__file__).parent
    songs = []

    # Music folder
    music_dir = base_dir / "music"
    if music_dir.exists():
        for f in music_dir.glob("*.mp3"):
            songs.append(str(f))

    # Generated music folder
    generated_dir = base_dir / "generated_music"
    if generated_dir.exists():
        for f in generated_dir.glob("*.mp3"):
            songs.append(str(f))

    return sorted(songs)

def list_songs():
    """List all songs and their transcription status"""
    songs = get_all_songs()
    print(f"\n{'='*60}")
    print(f"{'Song':<40} {'Transcribed?':<15}")
    print(f"{'='*60}")

    for song_path in songs:
        trans_path = get_transcription_path(song_path)
        status = "Yes" if os.path.exists(trans_path) else "No"
        name = Path(song_path).name[:38]
        print(f"{name:<40} {status:<15}")

    print(f"{'='*60}")
    print(f"Total: {len(songs)} songs")

def improve_metadata_with_gemini(transcription: dict) -> dict:
    """Use Gemini to generate improved title/description from lyrics"""
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not set, skipping metadata improvement")
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        lyrics = transcription.get("text", "")
        filename = transcription.get("file", "")

        prompt = f"""Analyze these song lyrics and provide improved metadata.

Filename: {filename}
Lyrics:
{lyrics}

Return a JSON object with:
{{
  "title": "A catchy, descriptive title based on the lyrics",
  "description": "A 1-2 sentence description of what the song is about",
  "genre": "The music genre (e.g., Pop, Rock, Country, Hip-Hop, etc.)",
  "energy": "The energy level (e.g., upbeat, chill, energetic, mellow)",
  "themes": ["theme1", "theme2"],
  "key_lyrics": "The most memorable or catchy line from the song"
}}

Only return valid JSON, no markdown or explanation."""

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Clean up response
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        return json.loads(text.strip())

    except Exception as e:
        print(f"WARNING: Failed to improve metadata: {e}")
        return None

def transcribe_all(model_name: str = DEFAULT_MODEL, improve: bool = False, force: bool = False):
    """Transcribe all songs"""
    songs = get_all_songs()

    print(f"\nFound {len(songs)} songs to process")
    print(f"Using Whisper model: {model_name}")
    if improve:
        print("Will improve metadata with Gemini")
    print()

    for i, song_path in enumerate(songs, 1):
        trans_path = get_transcription_path(song_path)

        # Skip if already transcribed (unless force)
        if os.path.exists(trans_path) and not force:
            existing = load_transcription(trans_path)
            print(f"[{i}/{len(songs)}] Already transcribed: {Path(song_path).name}")
            if improve and "improved_metadata" not in existing:
                print("  → Improving metadata...")
                improved = improve_metadata_with_gemini(existing)
                if improved:
                    existing["improved_metadata"] = improved
                    save_transcription(existing, trans_path)
            continue

        print(f"\n[{i}/{len(songs)}] Processing: {Path(song_path).name}")

        try:
            transcription = transcribe_audio(song_path, model_name)

            if improve:
                print("  → Improving metadata with Gemini...")
                improved = improve_metadata_with_gemini(transcription)
                if improved:
                    transcription["improved_metadata"] = improved

            save_transcription(transcription, trans_path)
            print(f"  → Lyrics: {transcription['text'][:100]}...")

        except Exception as e:
            print(f"  ERROR: {e}")

    print("\nDone!")

def transcribe_single(file_path: str, model_name: str = DEFAULT_MODEL, improve: bool = False):
    """Transcribe a single file"""
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    print(f"Transcribing: {file_path}")
    transcription = transcribe_audio(file_path, model_name)

    if improve:
        print("Improving metadata with Gemini...")
        improved = improve_metadata_with_gemini(transcription)
        if improved:
            transcription["improved_metadata"] = improved

    trans_path = get_transcription_path(file_path)
    save_transcription(transcription, trans_path)

    print("\n" + "="*60)
    print("TRANSCRIPTION:")
    print("="*60)
    print(transcription["text"])

    if "improved_metadata" in transcription:
        print("\n" + "="*60)
        print("IMPROVED METADATA:")
        print("="*60)
        print(json.dumps(transcription["improved_metadata"], indent=2))

def main():
    parser = argparse.ArgumentParser(description="Transcribe songs using Whisper")
    parser.add_argument("--file", "-f", help="Transcribe a specific file")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                       help=f"Whisper model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--improve", "-i", action="store_true",
                       help="Improve metadata with Gemini")
    parser.add_argument("--force", action="store_true",
                       help="Re-transcribe even if already done")
    parser.add_argument("--list", "-l", action="store_true",
                       help="List all songs and transcription status")

    args = parser.parse_args()

    if args.list:
        list_songs()
    elif args.file:
        transcribe_single(args.file, args.model, args.improve)
    else:
        transcribe_all(args.model, args.improve, args.force)

if __name__ == "__main__":
    main()
