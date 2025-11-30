#!/usr/bin/env python3
"""
Generate DJ sound effects using ElevenLabs Text-to-Sound Effects API
These are CLUB/DJ style sounds - not car horns!
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('ELEVENLABS_API_KEY')
SOUNDS_DIR = 'sounds'

# REAL DJ/Club sound effects with specific prompts
DJ_SOUNDS = {
    # AIR HORNS - The classic hip-hop/dancehall DJ sound
    'air_horn': {
        'prompt': 'Loud stadium air horn blast, the classic hip-hop DJ MLG air horn sound effect, three quick blasts ba ba baaaa, very loud and punchy electronic horn',
        'duration': 2.5
    },
    'air_horn_long': {
        'prompt': 'Long sustained stadium air horn, DJ club horn building up, electronic foghorn blast that builds in intensity, hip-hop style',
        'duration': 4.0
    },

    # SIRENS - Club/EDM style
    'siren': {
        'prompt': 'Electronic club siren, rising pitch EDM siren sound effect, rave alarm synth siren that builds up, dance music warning siren',
        'duration': 3.0
    },
    'siren_woop': {
        'prompt': 'Quick woop woop police siren, DJ remix style two-tone siren, electronic club siren quick bursts',
        'duration': 2.0
    },

    # DJ SCRATCHES - Turntable sounds
    'scratch': {
        'prompt': 'Vinyl record scratch, DJ turntable scratch sound effect, classic hip-hop record scratching, wicka wicka scratch',
        'duration': 1.5
    },
    'scratch_long': {
        'prompt': 'Extended DJ scratch solo, multiple vinyl scratches in sequence, turntablist scratching performance, hip-hop DJ battle scratches',
        'duration': 3.5
    },

    # TRANSITIONS
    'rewind': {
        'prompt': 'DJ rewind sound effect, vinyl record being spun backwards rapidly, tape rewind whoosh, pull up selecta rewind',
        'duration': 2.0
    },
    'record_stop': {
        'prompt': 'Record player stopping abruptly, vinyl slowdown and stop, DJ cutting the music suddenly, turntable power off',
        'duration': 2.0
    },
    'whoosh': {
        'prompt': 'Cinematic whoosh transition, fast swoosh sound effect, DJ transition swoosh, quick movement whoosh',
        'duration': 1.0
    },
    'riser': {
        'prompt': 'EDM riser build up, tension building synth riser, white noise sweep building to drop, electronic music build up',
        'duration': 4.0
    },

    # IMPACTS AND DROPS
    'bass_drop': {
        'prompt': 'Massive EDM bass drop impact, heavy sub bass hit, dubstep drop impact, the drop moment with deep bass thud',
        'duration': 2.5
    },
    'impact': {
        'prompt': 'Cinematic impact hit, punchy electronic boom, DJ transition impact sound, powerful bass impact',
        'duration': 1.5
    },

    # CROWD SOUNDS - Club atmosphere
    'crowd_cheer': {
        'prompt': 'Excited nightclub crowd cheering, audience going wild at a concert, massive crowd roar and applause, festival crowd reaction',
        'duration': 4.0
    },
    'crowd_hype': {
        'prompt': 'Hyped up club crowd, people screaming and cheering at DJ set, rave crowd losing their minds, party crowd noise',
        'duration': 3.0
    },
    'applause': {
        'prompt': 'Enthusiastic crowd applause, audience clapping and cheering, thunderous applause, standing ovation',
        'duration': 4.0
    },

    # DJ VOCAL SHOTS
    'yeah': {
        'prompt': 'DJ vocal sample yeah, hype man shouting yeah, energetic male voice saying yeah with reverb',
        'duration': 1.5
    },
    'lets_go': {
        'prompt': 'DJ vocal sample lets go, hype man shouting lets go, energetic crowd chant lets go',
        'duration': 2.0
    },

    # LASERS AND FX
    'laser': {
        'prompt': 'Retro arcade laser zap, sci-fi pew pew laser sound, electronic laser beam, 80s synth laser',
        'duration': 1.0
    },
    'gunshot': {
        'prompt': 'Dancehall DJ gunshot sound effect, reggae sound system gunshot, single shot gun finger sound',
        'duration': 1.0
    },
    'explosion': {
        'prompt': 'Cinematic explosion boom, massive explosion impact, epic movie explosion, bass heavy explosion',
        'duration': 2.5
    },

    # VINYL/RETRO
    'vinyl_crackle': {
        'prompt': 'Vinyl record static and crackle, old record player noise, warm vinyl surface noise, nostalgic record crackle',
        'duration': 3.0
    },
}

def generate_sound(name, prompt, duration):
    """Generate a sound effect using ElevenLabs API"""
    print(f"🎵 Generating '{name}'...")
    print(f"   Prompt: {prompt[:60]}...")

    url = "https://api.elevenlabs.io/v1/sound-generation"

    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": prompt,
        "duration_seconds": duration,
        "prompt_influence": 0.7  # Higher influence for more accurate sounds
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        filepath = os.path.join(SOUNDS_DIR, f"{name}.mp3")
        with open(filepath, 'wb') as f:
            f.write(response.content)
        size_kb = len(response.content) / 1024
        print(f"   ✅ Saved to {filepath} ({size_kb:.1f} KB)")
        return True
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text[:200]}")
        return False

def main():
    # Create sounds directory
    os.makedirs(SOUNDS_DIR, exist_ok=True)

    print("🎧 DJ-FoamBot Sound Generator v2.0")
    print("=" * 50)
    print("Generating REAL club DJ sounds...")
    print()

    success = 0
    failed = 0

    for name, config in DJ_SOUNDS.items():
        # Skip if already exists (use --force to regenerate)
        filepath = os.path.join(SOUNDS_DIR, f"{name}.mp3")
        if os.path.exists(filepath):
            print(f"⏭️  '{name}' already exists, skipping...")
            success += 1
            continue

        if generate_sound(name, config['prompt'], config['duration']):
            success += 1
        else:
            failed += 1

    print()
    print("=" * 50)
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    print()
    print("Sounds are cached in the 'sounds/' directory.")
    print("They're now FREE to use forever! 🎉")

if __name__ == '__main__':
    main()
