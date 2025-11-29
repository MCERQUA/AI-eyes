# Pi-Guy Voice Agent

An interactive voice agent with an animated sci-fi face, powered by ElevenLabs Conversational AI with Gemini Vision and DeepFace face recognition capabilities.

## ⚠️ IMPORTANT: Development Guidelines

**This project is being BUILT and features are being ADDED. When making changes:**
1. **NEVER remove existing tools, endpoints, or features** unless explicitly asked
2. **Always preserve all 6 ElevenLabs tools** when updating the agent
3. **Check server.py for all existing endpoints** before adding new ones
4. **All API endpoints must continue working** - don't break existing functionality
5. **When updating ElevenLabs agent config**, include ALL existing tool_ids in the array

**Current tools that MUST always be attached to the agent (8 total):**
- look_and_see (vision)
- identify_person (face recognition)
- manage_todos (todo list)
- search_web (web search)
- run_command (server commands)
- check_server_status (server health)
- manage_notes (notes/files)
- manage_memory (long-term memory via ElevenLabs Knowledge Base)

## Overview
- **Type**: Web app with Python backend
- **Frontend**: Netlify (https://ai-guy.mikecerqua.ca or GitHub Pages)
- **Backend**: Flask server on VPS (https://ai-guy.mikecerqua.ca)
- **Voice**: ElevenLabs Conversational AI
- **Vision**: Google Gemini 2.0 Flash
- **Face Recognition**: DeepFace (VGG-Face model)
- **Auth**: Clerk (login required for voice chat)

## Files
```
├── index.html          # Main app (face + voice agent + camera)
├── server.py           # Flask backend for vision + face recognition + usage API + todos + search + commands + notes
├── requirements.txt    # Python dependencies
├── setup-nginx.sh      # Nginx + SSL setup script
├── pi-guy.service      # Systemd service for auto-start
├── netlify.toml        # Netlify deployment config
├── known_faces/        # Face recognition database
│   └── Mike/           # Folder per person with their photos
├── pi_notes/           # Pi-Guy's personal notes (created by manage_notes tool)
├── memory_docs.json    # Maps memory names to ElevenLabs document IDs (not in git)
├── face_owners.json    # Maps face names to Clerk user IDs (not in git)
├── usage.db            # SQLite database for user usage + todos (not in git)
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

**All 8 tools attached to agent (tool_ids array):**
```
tool_5601kb73sh06e6q9t8ng87bv1qsa  # check_server_status
tool_3401kb73sh07ed5bvhtshsbxq35j  # look_and_see
tool_1901kb73sh08f27bct0d3w81qdgn  # identify_person
tool_4801kb73sh09fxfsvjf3csmca1w5  # manage_todos
tool_2901kb73sh0ae2a8z7yj04v4chn1  # search_web
tool_3501kb73sh0be5tt4xb5162ejdxz  # run_command
tool_8001kb754p5setqb2qedb7rfez15  # manage_notes
tool_0301kb77mf7vf0sbdyhxn3w470da  # manage_memory
```

#### Vision Tool (look_and_see)
- **Tool ID**: `tool_3401kb73sh07ed5bvhtshsbxq35j`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/vision`
- **Method**: GET
- **Trigger phrases**: "look", "see", "what is this", "what do you see", "can you see", "look at this", "check this out"

#### Face Recognition Tool (identify_person)
- **Tool ID**: `tool_1901kb73sh08f27bct0d3w81qdgn`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/identity`
- **Method**: GET
- **Trigger phrases**: "do you recognize me", "who am I", "do you know who I am", "who is this"

#### Server Status Tool (check_server_status)
- **Tool ID**: `tool_5601kb73sh06e6q9t8ng87bv1qsa`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/server-status`
- **Method**: GET
- **Trigger phrases**: "server status", "what's running", "how is the server", "system status", "check the server", "how much memory", "uptime", "server health"

#### Todo List Tool (manage_todos)
- **Tool ID**: `tool_4801kb73sh09fxfsvjf3csmca1w5`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/todos`
- **Method**: GET
- **Trigger phrases**: "add to my list", "todo", "remind me", "what's on my list", "mark done"
- **Query params**: `task` (for add), `task_text` (for complete) - user_id comes from face recognition

#### Web Search Tool (search_web)
- **Tool ID**: `tool_2901kb73sh0ae2a8z7yj04v4chn1`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/search`
- **Method**: GET
- **Trigger phrases**: "search for", "look up", "google", "find information about"
- **Query params**: `query` (required)

#### Server Command Tool (run_command)
- **Tool ID**: `tool_3501kb73sh0be5tt4xb5162ejdxz`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/command`
- **Method**: GET
- **Trigger phrases**: "git status", "disk space", "check memory", "list files"
- **Query params**: `command` - one of:
  - `git_status` - Check git status
  - `git_log` - Recent commits
  - `disk_usage` - Disk usage
  - `memory` - Memory usage
  - `uptime` - System uptime
  - `date` - Current date/time
  - `whoami` - Current user
  - `list_files` - List project files
  - `list_faces` - List known faces
  - `nginx_status` - Nginx status
  - `service_status` - Pi-Guy service status
  - `network` - Network connections
  - `processes` - Running processes
  - `hostname` - Server hostname
  - `ip_address` - Server IP addresses

#### Notes Tool (manage_notes)
- **Tool ID**: `tool_8001kb754p5setqb2qedb7rfez15`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/notes`
- **Method**: GET
- **Trigger phrases**: "write this down", "make a note", "save this", "my notes", "read notes"
- **Query params**:
  - `action` - one of: `list`, `read`, `write`, `append`, `delete`, `search`
  - `filename` - name of the note (e.g., "research", "ideas")
  - `content` - text to write or append
  - `search` - text to search for across all notes
- **Storage**: `pi_notes/` directory, all files are `.md` format

#### Memory Tool (manage_memory)
- **Tool ID**: `tool_0301kb77mf7vf0sbdyhxn3w470da`
- **Webhook URL**: `https://ai-guy.mikecerqua.ca/api/memory`
- **Method**: GET
- **Trigger phrases**: "remember this", "remember that", "don't forget", "what do you remember", "do you remember", "recall", "forget this"
- **Query params**:
  - `action` - one of: `list`, `read`, `remember`, `forget`, `search`
  - `name` - memory name/label (e.g., "Mike's dog", "project deadline")
  - `content` - information to remember (for remember action)
  - `search` - search term (for search action)
- **Storage**: ElevenLabs Knowledge Base (uses RAG for retrieval)
- **How it works**:
  - Creates documents in ElevenLabs Knowledge Base via API
  - Documents are attached to the agent with `usage_mode: "auto"` (RAG)
  - RAG retrieves relevant memories during conversations
  - Memories persist across ALL conversations
- **Local tracking**: `memory_docs.json` maps memory names to document IDs

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
- **No login required** - face recognition works for everyone

### User Authentication & Limits
- **Clerk login** required to start voice conversations
- **20 agent responses per month** per user (resets monthly)
- **Usage tracked** in SQLite database on server
- **No login needed** for: face recognition, camera, viewing the face

## API Endpoints

### Server (https://ai-guy.mikecerqua.ca)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves index.html |
| `/api/health` | GET | Health check |
| `/api/frame` | POST | Receive camera frame from client |
| `/api/vision` | GET/POST | Analyze latest frame with Gemini |
| `/api/identify` | POST | Identify face in image using DeepFace |
| `/api/identity` | GET | Get currently identified person (used by ElevenLabs tool) |
| `/api/faces` | GET | List all known faces in database |
| `/api/faces/<name>` | POST | Add face image for a person |
| `/api/faces/<name>` | DELETE | Remove a person from database |
| `/api/faces/<name>/photo/<filename>` | DELETE | Remove single photo from person |
| `/known_faces/<name>/<filename>` | GET | Serve face photo (for My Face UI) |
| `/api/usage/<user_id>` | GET | Check user's usage and remaining allowance |
| `/api/usage/<user_id>/increment` | POST | Increment user's message count |
| `/api/server-status` | GET | Get server status (CPU, memory, disk, processes) |
| `/api/todos` | GET | List/add/complete todos (`?task=` to add, `?task_text=` to complete) |
| `/api/todos` | POST | Add a todo (`{"user_id": "xxx", "task": "..."}`) |
| `/api/todos/complete` | POST | Complete a todo (`{"user_id": "xxx", "task_text": "..."}`) |
| `/api/todos/<id>` | DELETE | Delete a todo |
| `/api/search` | GET/POST | Web search (`?query=xxx`) |
| `/api/command` | GET/POST | Run whitelisted command (`?command=git_status`) |
| `/api/commands` | GET | List available commands |
| `/api/notes` | GET | List/read/write/delete notes (`?action=list/read/write/append/delete/search`) |
| `/api/notes` | POST | Create/update note (`{"filename": "...", "content": "...", "append": bool}`) |
| `/api/notes/<filename>` | GET | Read specific note |
| `/api/notes/<filename>` | DELETE | Delete specific note |
| `/api/memory` | GET | Manage long-term memory (`?action=list/read/remember/forget/search`) |
| `/api/memory/sync` | POST | Sync local memory mapping with ElevenLabs |
| `/api/memory/list-all` | GET | List all knowledge base documents (debug) |

## Starting the Server

The server runs as a systemd service (auto-starts on boot):

```bash
# Start/stop/restart
sudo systemctl start pi-guy
sudo systemctl stop pi-guy
sudo systemctl restart pi-guy

# Check status
sudo systemctl status pi-guy

# View logs
sudo journalctl -u pi-guy -f
```

Manual start (if needed):
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
# ElevenLabs
ELEVENLABS_API_KEY=xxx
ELEVENLABS_AGENT_ID=agent_0801kb2240vcea2ayx0a2qxmheha
ELEVENLABS_VISION_TOOL_ID=tool_3401kb73sh07ed5bvhtshsbxq35j
ELEVENLABS_IDENTIFY_TOOL_ID=tool_1901kb73sh08f27bct0d3w81qdgn
ELEVENLABS_SERVER_STATUS_TOOL_ID=tool_5601kb73sh06e6q9t8ng87bv1qsa
ELEVENLABS_TODO_TOOL_ID=tool_4801kb73sh09fxfsvjf3csmca1w5
ELEVENLABS_SEARCH_TOOL_ID=tool_2901kb73sh0ae2a8z7yj04v4chn1
ELEVENLABS_COMMAND_TOOL_ID=tool_3501kb73sh0be5tt4xb5162ejdxz
ELEVENLABS_NOTES_TOOL_ID=tool_8001kb754p5setqb2qedb7rfez15
ELEVENLABS_MEMORY_TOOL_ID=tool_0301kb77mf7vf0sbdyhxn3w470da

# Google Gemini (the only real secret!)
GEMINI_API_KEY=xxx

# Clerk (publishable key is public, ok to expose)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxx

# Server
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

// Auth
isLoggedIn()              // Check if user is logged in
getUser()                 // Get current Clerk user object
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
- Home automation controls (Home Assistant integration)
- ~~Memory/context persistence between sessions~~ ✅ DONE - via manage_memory tool
- Different "moods" based on conversation
- Screen sharing capability
- Multiple camera support
- Admin UI for managing face database
- Weather tool (OpenWeatherMap)
- Calendar/reminders integration
- Email notifications

## Costs

| Feature | Provider | Cost |
|---------|----------|------|
| Voice | ElevenLabs API | Paid (per minute) |
| Vision | Gemini API | Paid (per API call) |
| Face Recognition | DeepFace (local) | **FREE** |
| Wake Word | Web Speech API (browser) | **FREE** |
| Auth | Clerk | Free tier (10k MAU) |
| Web Search | DuckDuckGo (scraping) | **FREE** |
| Todos | SQLite (local) | **FREE** |
| Server Commands | Local subprocess | **FREE** |
| Notes/Files | Local filesystem | **FREE** |
| Long-term Memory | ElevenLabs Knowledge Base | **FREE** (included with ElevenLabs) |

## Notes
- **HTTPS Required**: Both mic and camera require secure context
- **Browser Support**: Chrome, Firefox, Edge, Safari (modern versions)
- **Chrome recommended**: Wake word (Web Speech API) works best in Chrome
- **Server must be running** for vision and face recognition to work
- **Camera permission** needed for vision and face recognition
- **Microphone permission** needed for voice and wake word features
- **DeepFace deps**: Install manually on VPS with `pip install deepface tf-keras` (not in requirements.txt due to Netlify compatibility)
