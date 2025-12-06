#!/usr/bin/env python3
"""
Pi-Guy Wake Word Listener

Always-on wake word detection using Picovoice Porcupine.
When wake word is detected, triggers the browser to start ElevenLabs conversation.

Listens for: "Pi Guy", "Hi Guy", "My Guy" (custom trained models)

Requirements:
    pip3 install pvporcupine pvrecorder

Setup:
    1. Get free API key from https://console.picovoice.ai/
    2. Create custom wake word models for "Pi Guy", "Hi Guy", "My Guy"
    3. Download .ppn files for Raspberry Pi platform
    4. Place them in wake_words/ directory
    5. Set PICOVOICE_ACCESS_KEY in .env

Usage:
    python3 wake_word_listener.py

The listener will:
    1. Listen continuously for wake words
    2. When detected, POST to /api/wake-trigger endpoint
    3. Frontend receives event and starts conversation
"""

import os
import sys
import time
import struct
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
ACCESS_KEY = os.getenv('PICOVOICE_ACCESS_KEY')
SERVER_URL = os.getenv('WAKE_TRIGGER_URL', 'http://localhost:5000')
WAKE_WORDS_DIR = Path(__file__).parent / 'wake_words'

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
RESET = '\033[0m'

def print_banner():
    """Print startup banner"""
    print(f"""
{CYAN}╔═══════════════════════════════════════════════════════════╗
║                                                               ║
║   🎤 Pi-Guy Wake Word Listener                                ║
║                                                               ║
║   Listening for: "Pi Guy" / "Hi Guy" / "My Guy"              ║
║                                                               ║
║   Say the magic words to wake up Pi-Guy!                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝{RESET}
""")

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import pvporcupine
        import pvrecorder
        return True
    except ImportError as e:
        print(f"{RED}Missing dependency: {e}{RESET}")
        print(f"\n{YELLOW}Install with:{RESET}")
        print("    pip3 install pvporcupine pvrecorder")
        return False

def find_wake_word_models():
    """Find custom wake word model files"""
    if not WAKE_WORDS_DIR.exists():
        WAKE_WORDS_DIR.mkdir(parents=True)
        print(f"{YELLOW}Created wake_words/ directory{RESET}")
        print(f"\n{YELLOW}You need to create custom wake word models:{RESET}")
        print("1. Go to https://console.picovoice.ai/")
        print("2. Create wake word models for 'Pi Guy', 'Hi Guy', 'My Guy'")
        print("3. Select 'Raspberry Pi' as the platform")
        print("4. Download the .ppn files")
        print(f"5. Place them in: {WAKE_WORDS_DIR}")
        return []

    # Find all .ppn files
    models = list(WAKE_WORDS_DIR.glob('*.ppn'))
    return models

def trigger_wake(keyword_name):
    """Notify server that wake word was detected"""
    try:
        response = requests.post(
            f"{SERVER_URL}/api/wake-trigger",
            json={'keyword': keyword_name, 'timestamp': time.time()},
            timeout=2
        )
        if response.ok:
            print(f"{GREEN}✓ Triggered! Pi-Guy is waking up...{RESET}")
        else:
            print(f"{RED}✗ Trigger failed: {response.status_code}{RESET}")
    except requests.exceptions.RequestException as e:
        print(f"{RED}✗ Could not reach server: {e}{RESET}")

def run_with_builtin_keywords():
    """Run with built-in keywords (for testing without custom models)"""
    import pvporcupine
    from pvrecorder import PvRecorder

    print(f"\n{YELLOW}No custom wake word models found.{RESET}")
    print(f"Using built-in keyword 'jarvis' for testing.\n")
    print(f"Available built-in keywords: {', '.join(pvporcupine.KEYWORDS)}\n")

    # Use Jarvis as a test keyword
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keywords=['jarvis']
    )

    recorder = PvRecorder(
        device_index=-1,  # Default device
        frame_length=porcupine.frame_length
    )

    print(f'{GREEN}Listening for "Jarvis"... (say it to test){RESET}\n')
    recorder.start()

    try:
        while True:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print(f"\n{GREEN}★ Wake word detected: JARVIS ★{RESET}")
                trigger_wake('jarvis')
                # Brief cooldown to prevent double triggers
                time.sleep(1.5)
                print(f'{CYAN}Listening...{RESET}')

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopping...{RESET}")
    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()

def run_with_custom_keywords(model_paths):
    """Run with custom wake word models"""
    import pvporcupine
    from pvrecorder import PvRecorder

    # Get keyword names from filenames
    keyword_names = [p.stem for p in model_paths]
    keyword_paths = [str(p) for p in model_paths]

    print(f"{GREEN}Loading custom wake words: {', '.join(keyword_names)}{RESET}\n")

    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=keyword_paths,
        sensitivities=[0.7] * len(keyword_paths)  # Adjust sensitivity (0.0-1.0)
    )

    recorder = PvRecorder(
        device_index=-1,  # Default device
        frame_length=porcupine.frame_length
    )

    print(f'{GREEN}Listening for: {", ".join(keyword_names)}{RESET}\n')
    recorder.start()

    try:
        while True:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                detected_keyword = keyword_names[keyword_index]
                print(f"\n{GREEN}★ Wake word detected: {detected_keyword.upper()} ★{RESET}")
                trigger_wake(detected_keyword)
                # Brief cooldown to prevent double triggers
                time.sleep(1.5)
                print(f'{CYAN}Listening...{RESET}')

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopping...{RESET}")
    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()

def main():
    print_banner()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check access key
    if not ACCESS_KEY:
        print(f"{RED}Error: PICOVOICE_ACCESS_KEY not set in .env{RESET}")
        print(f"\n{YELLOW}Get your free key at: https://console.picovoice.ai/{RESET}")
        sys.exit(1)

    print(f"{GREEN}✓ Access key loaded{RESET}")
    print(f"{GREEN}✓ Server URL: {SERVER_URL}{RESET}")

    # Find wake word models
    models = find_wake_word_models()

    if models:
        print(f"{GREEN}✓ Found {len(models)} wake word model(s){RESET}")
        run_with_custom_keywords(models)
    else:
        # Fall back to built-in keywords for testing
        run_with_builtin_keywords()

if __name__ == '__main__':
    main()
