# Pi-Guy Voice Agent

An interactive AI voice agent with an animated sci-fi face, powered by ElevenLabs Conversational AI. Pi-Guy can see through your camera, recognize faces, manage todos, search the web, run server commands, take notes, remember things permanently, and schedule jobs.

![Pi-Guy](https://img.shields.io/badge/Pi--Guy-AI%20Voice%20Agent-blue)
![ElevenLabs](https://img.shields.io/badge/Powered%20by-ElevenLabs-purple)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Voice Conversations** - Natural voice chat powered by ElevenLabs Conversational AI
- **Animated Face** - Sci-fi inspired face with blinking eyes, expressions, and waveform mouth
- **Vision** - Camera integration with Google Gemini for image analysis
- **Face Recognition** - Identifies people using DeepFace (runs locally, FREE)
- **Wake Word** - Hands-free activation with "Pi Guy" or "Hey AI"
- **Todo Lists** - Per-user task management via face recognition
- **Web Search** - DuckDuckGo search integration (FREE)
- **Server Commands** - Run whitelisted system commands
- **Notes System** - Personal note-taking for the AI
- **Long-term Memory** - Persistent memory via ElevenLabs Knowledge Base + RAG
- **Job Scheduling** - Schedule one-time or recurring tasks (cron-style)
- **User Authentication** - Clerk integration with usage limits

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (Client)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Animated    │  │ Voice Agent │  │ Camera      │              │
│  │ Face (CSS)  │  │ (ElevenLabs)│  │ (WebRTC)    │              │
│  └─────────────┘  └──────┬──────┘  └──────┬──────┘              │
└──────────────────────────┼────────────────┼─────────────────────┘
                           │                │
                    WebSocket          HTTP POST
                           │                │
┌──────────────────────────┼────────────────┼─────────────────────┐
│                    ElevenLabs API         │                      │
│                          │                │                      │
│              Tool Webhooks (9 tools)      │                      │
└──────────────────────────┼────────────────┼─────────────────────┘
                           │                │
                      HTTPS (nginx)         │
                           │                │
┌──────────────────────────┴────────────────┴─────────────────────┐
│                      VPS Server (Flask)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Vision API  │  │ Face Recog  │  │ Jobs/Cron   │              │
│  │ (Gemini)    │  │ (DeepFace)  │  │ Scheduler   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Todos       │  │ Notes       │  │ Memory      │              │
│  │ (SQLite)    │  │ (Files)     │  │ (EL KB+RAG) │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **VPS/Server** with:
  - Ubuntu 20.04+ (or similar Linux)
  - Python 3.8+
  - nginx
  - Domain name with SSL (Let's Encrypt)
- **API Keys**:
  - [ElevenLabs](https://elevenlabs.io) - Voice AI (paid, per-minute)
  - [Google Gemini](https://makersuite.google.com/app/apikey) - Vision (paid, per-call)
  - [Clerk](https://clerk.com) - Authentication (free tier available)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/MCERQUA/AI-eyes.git
cd AI-eyes
```

### 2. Install Python Dependencies

```bash
pip3 install flask flask-cors python-dotenv google-generativeai psutil requests

# For face recognition (optional but recommended)
pip3 install deepface tf-keras
```

### 3. Create Environment File

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
```bash
# ElevenLabs (get from https://elevenlabs.io)
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_AGENT_ID=your_agent_id_here

# Google Gemini (get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_key_here

# Clerk (get from https://clerk.com)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here

# Server
PORT=5000
DOMAIN=your-domain.com
```

### 4. Set Up ElevenLabs Agent

1. Go to [ElevenLabs Conversational AI](https://elevenlabs.io/conversational-ai)
2. Create a new agent
3. Copy the Agent ID to your `.env`
4. Create the 9 webhook tools (see [Setting Up Tools](#setting-up-elevenlabs-tools))

### 5. Configure nginx + SSL

```bash
# Install nginx and certbot
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# Run the setup script
chmod +x setup-nginx.sh
sudo ./setup-nginx.sh
```

Or manually configure nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 6. Set Up Systemd Service

```bash
sudo cp pi-guy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pi-guy
sudo systemctl start pi-guy
```

### 7. Set Up Job Runner (Cron)

```bash
chmod +x job_runner.sh
crontab -e
# Add this line:
* * * * * /path/to/AI-eyes/job_runner.sh >> /path/to/AI-eyes/job_runner.log 2>&1
```

### 8. Verify Everything Works

```bash
python3 tools_health_check.py --remote
```

## Setting Up ElevenLabs Tools

Pi-Guy uses 9 webhook tools. Each tool needs to be created in the ElevenLabs dashboard and attached to your agent.

### Tool Reference

| Tool | Endpoint | Purpose |
|------|----------|---------|
| look_and_see | `/api/vision` | Analyze camera feed with Gemini |
| identify_person | `/api/identity` | Face recognition |
| manage_todos | `/api/todos` | Todo list management |
| search_web | `/api/search` | Web search via DuckDuckGo |
| run_command | `/api/command` | Run whitelisted server commands |
| check_server_status | `/api/server-status` | CPU, memory, disk stats |
| manage_notes | `/api/notes` | Create/read notes |
| manage_memory | `/api/memory` | Long-term memory (ElevenLabs KB) |
| manage_jobs | `/api/jobs` | Schedule tasks |

### Creating a Tool

1. Go to ElevenLabs > Conversational AI > Tools
2. Click "Create Tool"
3. Select "Webhook"
4. Configure:
   - **Name**: e.g., `look_and_see`
   - **Description**: Include trigger phrases
   - **URL**: `https://your-domain.com/api/vision`
   - **Method**: GET
   - **Query Parameters**: As needed (see TOOLS.md)
5. Save and copy the Tool ID
6. Attach to your agent via API:

```bash
curl -X PATCH "https://api.elevenlabs.io/v1/convai/agents/YOUR_AGENT_ID" \
  -H "xi-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_config": {
      "agent": {
        "prompt": {
          "tool_ids": ["tool_id_1", "tool_id_2", ...]
        }
      }
    }
  }'
```

See [TOOLS.md](TOOLS.md) for complete tool configurations.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main app (index.html) |
| `/api/health` | GET | Health check |
| `/api/frame` | POST | Receive camera frame |
| `/api/vision` | GET | Analyze frame with Gemini |
| `/api/identify` | POST | Identify face in image |
| `/api/identity` | GET | Get current identified person |
| `/api/faces` | GET | List known faces |
| `/api/faces/<name>` | POST/DELETE | Add/remove face |
| `/api/usage/<user_id>` | GET | Check user usage |
| `/api/server-status` | GET | Server health metrics |
| `/api/todos` | GET | Manage todos |
| `/api/search` | GET | Web search |
| `/api/command` | GET | Run whitelisted command |
| `/api/commands` | GET | List available commands |
| `/api/notes` | GET | Manage notes |
| `/api/memory` | GET | Manage long-term memory |
| `/api/jobs` | GET | Manage scheduled jobs |
| `/api/jobs/run-pending` | POST | Execute pending jobs |

## Configuration

### Server Commands Whitelist

Edit `ALLOWED_COMMANDS` in `server.py` to add/remove available commands:

```python
ALLOWED_COMMANDS = {
    'git_status': {'cmd': ['git', 'status'], 'cwd': '/path/to/repo', 'desc': 'Check git status'},
    'disk_usage': {'cmd': ['df', '-h', '/'], 'desc': 'Disk usage'},
    # Add your own...
}
```

### Job Actions Whitelist

Edit `JOB_ACTIONS` in `server.py` to add schedulable actions:

```python
JOB_ACTIONS = {
    'command': 'Execute a whitelisted server command',
    'note_write': 'Write or append to a note',
    'server_status': 'Check server status',
    # Add your own...
}
```

### Adding Known Faces

1. Enable camera in the web UI
2. Open browser console (F12)
3. Run: `saveFace("PersonName")`
4. Repeat 3-5 times with different angles

## File Structure

```
AI-eyes/
├── index.html           # Main web app
├── server.py            # Flask backend
├── requirements.txt     # Python dependencies
├── .env                 # API keys (create from .env.example)
├── .env.example         # Template for environment variables
├── CLAUDE.md            # Development instructions
├── TOOLS.md             # Master tool reference
├── tools_health_check.py # Health check script
├── job_runner.sh        # Cron job runner
├── setup-nginx.sh       # nginx setup script
├── pi-guy.service       # Systemd service file
├── netlify.toml         # Netlify config (if using)
├── known_faces/         # Face recognition database
├── pi_notes/            # Notes storage
├── usage.db             # SQLite database (auto-created)
└── memory_docs.json     # Memory mapping (auto-created)
```

## Costs

| Feature | Provider | Cost |
|---------|----------|------|
| Voice | ElevenLabs | ~$0.30/min |
| Vision | Google Gemini | ~$0.001/image |
| Face Recognition | DeepFace | **FREE** (local) |
| Wake Word | Web Speech API | **FREE** |
| Auth | Clerk | Free tier (10k MAU) |
| Web Search | DuckDuckGo | **FREE** |
| Todos/Notes/Jobs | SQLite/Local | **FREE** |
| Memory (RAG) | ElevenLabs KB | Included with ElevenLabs |

## Troubleshooting

### Server won't start
```bash
# Check logs
sudo journalctl -u pi-guy -f

# Check if port is in use
sudo lsof -i :5000

# Start manually for debugging
python3 server.py
```

### Tools not working
```bash
# Run health check
python3 tools_health_check.py

# Check specific endpoint
curl https://your-domain.com/api/health
```

### Face recognition not working
```bash
# Ensure DeepFace is installed
pip3 install deepface tf-keras

# Check known_faces directory has images
ls -la known_faces/
```

### Jobs not running
```bash
# Check cron is set up
crontab -l

# Check job runner log
tail -f job_runner.log

# Manually trigger
curl -X POST http://localhost:5000/api/jobs/run-pending
```

## Development

### Running Locally

```bash
# Start the server
python3 server.py

# Access at http://localhost:5000
```

### Adding a New Tool

1. Add endpoint in `server.py`
2. Create tool in ElevenLabs dashboard
3. Attach tool to agent
4. Update `TOOLS.md` and `tools_health_check.py`
5. Run health check to verify

See [TOOLS.md](TOOLS.md) for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `python3 tools_health_check.py` to verify
5. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) for details.

## Credits

- [ElevenLabs](https://elevenlabs.io) - Voice AI platform
- [Google Gemini](https://deepmind.google/technologies/gemini/) - Vision AI
- [DeepFace](https://github.com/serengil/deepface) - Face recognition
- [Clerk](https://clerk.com) - Authentication

---

**Note**: This project is designed for personal/educational use. Ensure you comply with all API terms of service and applicable laws when deploying.
