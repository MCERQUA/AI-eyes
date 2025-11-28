# Pi-Guy Voice Agent

An interactive voice agent with an animated sci-fi face, powered by ElevenLabs Conversational AI with Gemini Vision and DeepFace face recognition capabilities.

## Overview
- **Type**: Web app with Python backend
- **Frontend**: GitHub Pages (https://mcerqua.github.io/AI-eyes/)
- **Backend**: Flask server on VPS (https://ai-guy.mikecerqua.ca)
- **Voice**: ElevenLabs Conversational AI
- **Vision**: Google Gemini 2.0 Flash
- **Face Recognition**: DeepFace (VGG-Face model)

## Files
```
├── index.html          # Main app (face + voice agent + camera)
├── server.py           # Flask backend for vision + face recognition API
├── requirements.txt    # Python dependencies
├── setup-nginx.sh      # Nginx + SSL setup script
├── known_faces/        # Face recognition database
│   └── Mike/           # Folder per person with their photos
├── .env                # API keys (not in git)
├── CLAUDE.md           # This file
└── .gitignore
```

## Current Configuration

### ElevenLabs Agent
- **Agent ID**: `agent_0801kb2240vcea2ayx0a2qxmheha`
- **Model**: glm-45-air-fp8 (configurable in ElevenLabs dashboard)
- **Max Tokens**: 1000
- **Voice**: Custom (eZm9vdjYgL9PZKtf7XMM)

### ElevenLabs Tools

#### Vision Tool (look_and_see)
- **Tool ID**: `tool_4801kb43nm64eeyawtqsbpy8rtb4`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/vision`
- **Method**: GET
- **Trigger phrases**: "look", "see", "what is this", "what do you see", "can you see"

#### Face Recognition Tool (identify_person)
- **Tool ID**: `tool_4801kb4bcw3df5x9v7gvpes40b5m`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/identity`
- **Method**: GET
- **Trigger phrases**: "do you recognize me", "who am I", "do you know who I am"

### Server
- **Domain**: ai-guy.mikecerqua.ca
- **VPS IP**: 178.156.162.212
- **Port**: 5000 (proxied through nginx with SSL)
- **SSL**: Let's Encrypt (auto-renews)

## Features

### Animated Face
- **Eyes** that follow cursor movement
- **Random eye movement** when idle (looks around on its own)
- **Realistic blinking** with random intervals
- **Expressions**: neutral, happy, sad, angry, thinking, surprised, listening
- **Waveform mouth** - animates when agent is speaking

### Voice Agent
- **Click phone button** to start/end conversation
- **Random first messages** - Pi-Guy greets differently each time
- **Real-time transcription**: Shows what you and the agent say
- **Status indicators**: Connecting, connected, listening, speaking
- **Keyboard shortcuts**: Space/Enter to toggle conversation, Escape to end

### Wake Word Activation
- **Wake words**: "Pi Guy", "Hey Pi Guy", "AI Guy", "Hey AI", "Hi Guy"
- **Click mic button** to enable/disable wake word listening
- **Always-on listening** - starts conversation hands-free when wake word detected
- **Auto-restarts** after conversation ends (if enabled)
- **800ms delay** after detection to release mic before starting conversation
- Uses browser's Web Speech API (Chrome recommended)

### Vision (Camera)
- **Camera button** with live preview inside the button
- **Captures frames** every 2 seconds and sends to server
- **Gemini Vision API** analyzes images with Pi-Guy's personality
- **Voice describes** what he "sees" in his sarcastic way

### Face Recognition
- **Automatic identification** when camera turns on
- **DeepFace** with VGG-Face model (99%+ accuracy) - runs locally, **FREE** (no API costs)
- **Personalized greetings** - Pi-Guy greets known people by name
- **ElevenLabs tool** - Pi-Guy can identify people mid-conversation ("do you recognize me?")
- **Re-identifies every 10 seconds** while camera is on (if not in conversation)
- **Database structure**: `known_faces/<PersonName>/<photos>.jpg`
- Add faces via console: `saveFace("Name")` with camera on

## API Endpoints

### Server (https://ai-guy.mikecerqua.ca)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves index.html |
| `/api/health` | GET | Health check |
| `/api/frame` | POST | Receive camera frame from client |
| `/api/vision` | GET/POST | Analyze latest frame with Gemini |
| `/api/identify` | POST | Identify face in image using DeepFace |
| `/api/identity` | GET | Get currently identified person |
| `/api/faces` | GET | List all known faces in database |
| `/api/faces/<name>` | POST | Add face image for a person |
| `/api/faces/<name>` | DELETE | Remove a person from database |

## Starting the Server

```bash
cd /home/mike/Mike-AI/ai-eyes
nohup python3 server.py > server.log 2>&1 &
```

Check if running:
```bash
curl https://ai-guy.mikecerqua.ca/api/health
```

## Environment Variables (.env)

```
ELEVENLABS_API_KEY=xxx
ELEVENLABS_AGENT_ID=agent_0801kb2240vcea2ayx0a2qxmheha
ELEVENLABS_VISION_TOOL_ID=tool_4801kb43nm64eeyawtqsbpy8rtb4
ELEVENLABS_IDENTIFY_TOOL_ID=tool_4801kb4bcw3df5x9v7gvpes40b5m
GEMINI_API_KEY=xxx
VPS_IP=178.156.162.212
PORT=5000
DOMAIN=ai-guy.mikecerqua.ca
```

## ElevenLabs API Quick Reference

### Update Agent
```bash
curl -X PATCH "https://api.elevenlabs.io/v1/convai/agents/{agent_id}" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"conversation_config": {...}}'
```

### Update Tool
```bash
curl -X PATCH "https://api.elevenlabs.io/v1/convai/tools/{tool_id}" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tool_config": {...}}'
```

### List Tools
```bash
curl "https://api.elevenlabs.io/v1/convai/tools" \
  -H "xi-api-key: $ELEVENLABS_API_KEY"
```

## JavaScript Console API

```javascript
// Face control
piGuy.setMood('happy')    // happy, sad, angry, thinking, surprised, listening, neutral
piGuy.blink()
piGuy.setAgentId('new-id')
piGuy.getConversation()

// Camera & Vision
toggleCamera()            // Toggle camera on/off
toggleWakeWord()          // Toggle wake word listening
captureAndDescribe()      // Test vision locally

// Face Recognition
saveFace("Mike")          // Save current camera frame as Mike's face
listFaces()               // List all known faces in database
getIdentity()             // Get current identified person
identifyFace()            // Manually trigger face identification
```

## Adding a New Person to Face Database

1. Turn on camera (click camera button)
2. Have the person look at the camera
3. Open browser console (F12)
4. Run: `saveFace("PersonName")`
5. Repeat 2-3 times with different angles/lighting
6. Test by refreshing and turning camera on - should show "Recognized: PersonName"

**Tips for better recognition:**
- Add 3-5 photos per person
- Include different angles (front, slight left/right)
- Include different lighting conditions
- Make sure face is clearly visible and not blurry

## Future Ideas / TODOs
- Add more tools (weather, time, web search)
- Home automation controls
- Memory/context persistence between sessions
- Different "moods" based on conversation
- Screen sharing capability
- Multiple camera support
- Admin UI for managing face database

## Costs

| Feature | Provider | Cost |
|---------|----------|------|
| Voice | ElevenLabs API | Paid (per character) |
| Vision | Gemini API | Paid (per API call) |
| Face Recognition | DeepFace (local) | **FREE** |
| Wake Word | Web Speech API (browser) | **FREE** |

## Notes
- **HTTPS Required**: Both mic and camera require secure context
- **Browser Support**: Chrome, Firefox, Edge, Safari (modern versions)
- **Chrome recommended**: Wake word (Web Speech API) works best in Chrome
- **Server must be running** for vision and face recognition to work
- **Camera permission** needed for vision and face recognition
- **Microphone permission** needed for voice and wake word features
- **DeepFace deps**: Install manually on VPS with `pip install deepface tf-keras` (not in requirements.txt due to Netlify compatibility)
