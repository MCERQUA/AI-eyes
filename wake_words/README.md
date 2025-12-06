# Wake Word Models

This directory contains custom Porcupine wake word models for Pi-Guy.

## Setup Instructions

### 1. Get a Free Picovoice API Key

1. Go to https://console.picovoice.ai/
2. Sign up with email or GitHub
3. Copy your Access Key

### 2. Add Key to .env

```bash
PICOVOICE_ACCESS_KEY=your_key_here
```

### 3. Create Custom Wake Words

1. Go to https://console.picovoice.ai/
2. Click "Porcupine" → "Create Model"
3. Create models for these wake words:
   - **pi_guy** - "Pi Guy"
   - **hi_guy** - "Hi Guy"
   - **my_guy** - "My Guy"
4. Select platform: **Raspberry Pi**
5. Download the `.ppn` files
6. Place them in this directory

### 4. Install Dependencies (on Pi)

```bash
pip3 install pvporcupine pvrecorder
```

### 5. Run the Listener

```bash
cd /home/mike/Mike-AI/ai-eyes
python3 wake_word_listener.py
```

## Testing Without Custom Models

If you don't have custom models yet, the listener will use the built-in "Jarvis" keyword for testing.

## File Structure

```
wake_words/
├── README.md           # This file
├── pi_guy_en_raspberry-pi.ppn    # "Pi Guy" model
├── hi_guy_en_raspberry-pi.ppn    # "Hi Guy" model
└── my_guy_en_raspberry-pi.ppn    # "My Guy" model
```

## How It Works

1. `wake_word_listener.py` runs on the Pi, always listening
2. When wake word detected → POSTs to `/api/wake-trigger`
3. Server broadcasts via SSE to all connected browsers
4. Browser starts ElevenLabs conversation automatically

This bypasses Chromium's broken Web Speech API!
