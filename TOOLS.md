# Pi-Guy Tools Reference

**This is the MASTER REFERENCE for all Pi-Guy tools, whitelists, and configurations.**

> **⚠️ CRITICAL FOR CLAUDE - READ BEFORE ANY AGENT UPDATES:**
>
> 1. **ALWAYS get the full agent config FIRST** before making changes:
>    ```bash
>    curl -s "https://api.elevenlabs.io/v1/convai/agents/agent_0801kb2240vcea2ayx0a2qxmheha" \
>      -H "xi-api-key: $ELEVENLABS_API_KEY" | python3 -m json.tool
>    ```
> 2. **Review ALL of these before updating:**
>    - `conversation_config.agent.prompt.tools` - All 12 tools
>    - `conversation_config.agent.prompt.prompt` - System prompt with Radio Voice instructions
>    - `conversation_config.tts.supported_voices` - **RADIO VOICE MUST BE PRESERVED!**
> 3. **NEVER partially update** - always include ALL existing config when patching
> 4. Update this file with any changes you make
> 5. Never remove tools/voices unless explicitly asked
>
> **🎙️ RADIO VOICE**: Pi-Guy has a SECOND VOICE (Radio Voice ID: `CeNX9CMwmxDxUF5Q2Inm`)
> for his DJ-FoamBot persona. This is in `tts.supported_voices`. DO NOT DELETE IT!
> The prompt must include: `<Radio Voice>text here</Radio Voice>` XML tag instructions.

---

## Quick Reference: All Tools

| # | Tool Name | Tool ID | Endpoint | Status |
|---|-----------|---------|----------|--------|
| 1 | look_and_see | `tool_3401kb73sh07ed5bvhtshsbxq35j` | `/api/vision` | Active |
| 2 | identify_person | `tool_1901kb73sh08f27bct0d3w81qdgn` | `/api/identity` | Active |
| 3 | manage_todos | `tool_4801kb73sh09fxfsvjf3csmca1w5` | `/api/todos` | Active |
| 4 | search_web | `tool_2901kb73sh0ae2a8z7yj04v4chn1` | `/api/search` | Active |
| 5 | run_command | `tool_3501kb73sh0be5tt4xb5162ejdxz` | `/api/command` | Active |
| 6 | check_server_status | `tool_5601kb73sh06e6q9t8ng87bv1qsa` | `/api/server-status` | Active |
| 7 | manage_notes | `tool_8001kb754p5setqb2qedb7rfez15` | `/api/notes` | Active |
| 8 | manage_memory | `tool_0301kb77mf7vf0sbdyhxn3w470da` | `/api/memory` | Active |
| 9 | manage_jobs | `tool_6801kb79mrdwfycsawytjq0gx1ck` | `/api/jobs` | Active |
| 10 | play_music | `tool_9801kb8k61zpfkksynb8m4wztkkx` | `/api/music` | Active |

---

## ElevenLabs Agent Configuration

```
Agent ID: agent_0801kb2240vcea2ayx0a2qxmheha
Model: glm-45-air-fp8
Voice ID: eZm9vdjYgL9PZKtf7XMM
RAG: Enabled (e5_mistral_7b_instruct)
```

### Tool IDs Array (for agent updates)

When updating the agent, ALWAYS include ALL tool IDs:

```json
"tool_ids": [
    "tool_5601kb73sh06e6q9t8ng87bv1qsa",
    "tool_3401kb73sh07ed5bvhtshsbxq35j",
    "tool_1901kb73sh08f27bct0d3w81qdgn",
    "tool_4801kb73sh09fxfsvjf3csmca1w5",
    "tool_2901kb73sh0ae2a8z7yj04v4chn1",
    "tool_3501kb73sh0be5tt4xb5162ejdxz",
    "tool_8001kb754p5setqb2qedb7rfez15",
    "tool_0301kb77mf7vf0sbdyhxn3w470da",
    "tool_6801kb79mrdwfycsawytjq0gx1ck",
    "tool_9801kb8k61zpfkksynb8m4wztkkx"
]
```

---

## Tool Details

### 1. Vision (look_and_see)

**Purpose**: Analyze camera feed using Gemini Vision API

**Endpoint**: `GET /api/vision`

**Triggers**: "look", "see", "what is this", "what do you see", "can you see"

**Dependencies**:
- Camera must be enabled (client sends frames to `/api/frame`)
- `GEMINI_API_KEY` in .env

**Test**:
```bash
curl https://ai-guy.mikecerqua.ca/api/vision
# Expected: {"response": "I can't see anything..."} if no camera
```

---

### 2. Face Recognition (identify_person)

**Purpose**: Identify people using DeepFace

**Endpoint**: `GET /api/identity`

**Triggers**: "do you recognize me", "who am I", "who is this"

**Dependencies**:
- Camera enabled
- DeepFace installed on server (`pip install deepface tf-keras`)
- Known faces in `known_faces/` directory

**Test**:
```bash
curl https://ai-guy.mikecerqua.ca/api/identity
# Expected: {"name": "unknown/Name", "confidence": X, "response": "..."}
```

---

### 3. Todo List (manage_todos)

**Purpose**: Manage per-user todo lists

**Endpoint**: `GET /api/todos`

**Triggers**: "add to my list", "todo", "remind me", "what's on my list", "mark done"

**Parameters**:
- `task` - Add a new todo
- `task_text` - Complete a matching todo
- (no params) - List todos

**Dependencies**:
- SQLite database (`usage.db`)
- User identified via face recognition or user_id param

**Test**:
```bash
curl "https://ai-guy.mikecerqua.ca/api/todos?user_id=test"
# Expected: {"todos": [...], "count": X, "response": "..."}
```

---

### 4. Web Search (search_web)

**Purpose**: Search the internet via DuckDuckGo

**Endpoint**: `GET /api/search`

**Triggers**: "search for", "look up", "google", "find information"

**Parameters**:
- `query` (required) - Search terms

**Dependencies**:
- Internet access
- No API key needed (uses DuckDuckGo HTML scraping)

**Test**:
```bash
curl "https://ai-guy.mikecerqua.ca/api/search?query=test"
# Expected: {"query": "test", "results": [...], "response": "..."}
```

---

### 5. Server Commands (run_command)

**Purpose**: Run whitelisted server commands

**Endpoint**: `GET /api/command`

**Triggers**: "git status", "disk space", "check memory", "list files"

**Parameters**:
- `command` - Command name from whitelist

**WHITELIST** (defined in server.py `ALLOWED_COMMANDS`):

| Command | Description | Actual Command |
|---------|-------------|----------------|
| `git_status` | Check git status | `git status` |
| `git_log` | Recent commits | `git log --oneline -10` |
| `disk_usage` | Disk usage | `df -h /` |
| `memory` | Memory usage | `free -h` |
| `uptime` | System uptime | `uptime` |
| `date` | Current date/time | `date` |
| `whoami` | Current user | `whoami` |
| `list_files` | List project files | `ls -la /home/mike/Mike-AI/ai-eyes` |
| `list_faces` | List known faces | `ls -la .../known_faces` |
| `nginx_status` | Nginx status | `systemctl status nginx` |
| `service_status` | Pi-Guy service | `systemctl status pi-guy` |
| `network` | Network connections | `ss -tuln` |
| `processes` | Running processes | `ps aux --sort=-%cpu` |
| `hostname` | Server hostname | `hostname` |
| `ip_address` | Server IPs | `hostname -I` |

**To add a new command**: Edit `ALLOWED_COMMANDS` dict in server.py:
```python
ALLOWED_COMMANDS = {
    'new_command': {
        'cmd': ['command', 'args'],
        'cwd': '/optional/working/dir',  # optional
        'desc': 'Human description'
    },
    # ... existing commands
}
```

**Test**:
```bash
curl "https://ai-guy.mikecerqua.ca/api/command?command=uptime"
# Expected: {"command": "uptime", "output": "...", "response": "..."}
```

---

### 6. Server Status (check_server_status)

**Purpose**: Get system health metrics (CPU, memory, disk)

**Endpoint**: `GET /api/server-status`

**Triggers**: "server status", "how is the server", "system status", "check the server"

**Dependencies**:
- `psutil` Python package

**Test**:
```bash
curl https://ai-guy.mikecerqua.ca/api/server-status
# Expected: {"cpu_percent": X, "memory_used_percent": X, "summary": "..."}
```

---

### 7. Notes (manage_notes)

**Purpose**: Pi-Guy's personal note-taking system (local files)

**Endpoint**: `GET /api/notes`

**Triggers**: "write this down", "make a note", "save this", "my notes", "read notes"

**Parameters**:
- `action` - `list`, `read`, `write`, `append`, `delete`, `search`
- `filename` - Note name
- `content` - Text to write/append
- `search` - Search term

**Storage**: `pi_notes/` directory (markdown files)

**Test**:
```bash
curl "https://ai-guy.mikecerqua.ca/api/notes?action=list"
# Expected: {"notes": [...], "count": X, "response": "..."}
```

---

### 8. Memory (manage_memory)

**Purpose**: Long-term memory via ElevenLabs Knowledge Base + RAG

**Endpoint**: `GET /api/memory`

**Triggers**: "remember this", "don't forget", "what do you remember", "recall", "forget this"

**Parameters**:
- `action` - `list`, `read`, `remember`, `forget`, `search`
- `name` - Memory name/label
- `content` - Information to remember
- `search` - Search term

**Dependencies**:
- `ELEVENLABS_API_KEY` in .env
- ElevenLabs Knowledge Base API access

**Storage**:
- ElevenLabs Knowledge Base (documents)
- Local mapping: `memory_docs.json`

**Test**:
```bash
curl "https://ai-guy.mikecerqua.ca/api/memory?action=list"
# Expected: {"memories": [...], "count": X, "response": "..."}
```

---

### 9. Jobs (manage_jobs)

**Purpose**: Schedule and manage recurring or one-time tasks

**Endpoint**: `GET /api/jobs`

**Triggers**: "schedule a job", "run this later", "remind me in", "set up a recurring task", "what jobs", "cancel job"

**Parameters**:
- `action` - `list`, `schedule`, `cancel`, `status`, `history`, `run`
- `name` - Job name (for schedule/cancel/status)
- `schedule` - When to run (see formats below)
- `job_action` - What to do (see whitelist below)
- `params` - JSON parameters for the job action
- `job_id` - Job ID (for cancel/status/history/run)

**Schedule Formats**:
- `in 5 minutes`, `in 2 hours`, `in 1 day` - One-time
- `at 14:00`, `at 9:30` - One-time at specific time
- `daily at 9:00` - Recurring daily
- `hourly` - Every hour
- `every 30 minutes` - Every N minutes
- `0 9 * * *` - Raw cron expression

**JOB_ACTIONS Whitelist** (defined in server.py `JOB_ACTIONS`):

| Action | Description | Params |
|--------|-------------|--------|
| `command` | Run a whitelisted server command | `{"command": "disk_usage"}` |
| `note_write` | Write or append to a note | `{"filename": "log", "content": "text", "append": true}` |
| `note_read` | Read a note | `{"filename": "log"}` |
| `search` | Web search | `{"query": "search terms"}` |
| `server_status` | Check server health | `{}` |
| `remind` | Log a reminder | `{"message": "reminder text"}` |

**To add a new job action**: Edit `JOB_ACTIONS` dict and `execute_job_action()` in server.py.

**Cron Setup**: For recurring jobs to run automatically:
```bash
chmod +x /home/mike/Mike-AI/ai-eyes/job_runner.sh
crontab -e
# Add: * * * * * /home/mike/Mike-AI/ai-eyes/job_runner.sh >> /home/mike/Mike-AI/ai-eyes/job_runner.log 2>&1
```

**Test**:
```bash
# List jobs
curl "https://ai-guy.mikecerqua.ca/api/jobs?action=list"

# Schedule a job
curl "https://ai-guy.mikecerqua.ca/api/jobs?action=schedule&name=status_check&schedule=in%205%20minutes&job_action=server_status"

# Run immediately
curl "https://ai-guy.mikecerqua.ca/api/jobs?action=run&name=status_check"
```

---

### 10. Music/DJ (play_music)

**Purpose**: DJ Pi-Guy music controls - play, pause, skip, and control music playback

**Endpoint**: `GET /api/music`

**Triggers**: "play music", "play a song", "stop the music", "next track", "skip", "pause music", "turn it up", "turn it down", "what's playing", "list music", "DJ mode"

**Parameters**:
- `action` - `list`, `play`, `pause`, `resume`, `stop`, `skip`, `next`, `volume`, `status`, `shuffle`
- `track` - Track name to play (optional, for play action)
- `volume` - Volume level 0-100 (for volume action)

**Storage**: `music/` directory (MP3, WAV, OGG, M4A, WebM files)

**Frontend Features**:
- Music button in control bar
- "Now Playing" display with play/pause/skip controls
- Volume slider
- Volume ducking when Pi-Guy speaks

**Test**:
```bash
# List available tracks
curl "https://ai-guy.mikecerqua.ca/api/music?action=list"

# Play random track
curl "https://ai-guy.mikecerqua.ca/api/music?action=play"

# Play specific track
curl "https://ai-guy.mikecerqua.ca/api/music?action=play&track=mysong"

# Set volume
curl "https://ai-guy.mikecerqua.ca/api/music?action=volume&volume=50"
```

**Adding Music**:
```bash
# Upload MP3 files to the server
scp mysong.mp3 mike@178.156.162.212:/home/mike/Mike-AI/ai-eyes/music/
```

---

## Adding a New Tool

### Step 1: Create the endpoint in server.py

```python
@app.route('/api/newtool', methods=['GET'])
def handle_newtool():
    """
    Description of what this tool does
    ElevenLabs tool endpoint
    """
    param = request.args.get('param')

    # ... implementation ...

    return jsonify({
        "result": result,
        "response": "Pi-Guy style response for the agent to speak"
    })
```

### Step 2: Create the ElevenLabs tool

```bash
curl -X POST "https://api.elevenlabs.io/v1/convai/tools" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_config": {
      "type": "webhook",
      "name": "tool_name",
      "description": "Description with trigger phrases",
      "response_timeout_secs": 20,
      "api_schema": {
        "url": "https://ai-guy.mikecerqua.ca/api/newtool",
        "method": "GET",
        "path_params_schema": {},
        "query_params_schema": {
          "properties": {
            "param": {
              "type": "string",
              "description": "Parameter description"
            }
          },
          "required": ["param"]
        },
        "request_body_schema": null,
        "content_type": "application/json"
      }
    }
  }'
```

Save the returned tool ID!

### Step 3: Attach to agent

```bash
curl -X PATCH "https://api.elevenlabs.io/v1/convai/agents/agent_0801kb2240vcea2ayx0a2qxmheha" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_config": {
      "agent": {
        "prompt": {
          "tool_ids": [
            "tool_5601kb73sh06e6q9t8ng87bv1qsa",
            "tool_3401kb73sh07ed5bvhtshsbxq35j",
            "tool_1901kb73sh08f27bct0d3w81qdgn",
            "tool_4801kb73sh09fxfsvjf3csmca1w5",
            "tool_2901kb73sh0ae2a8z7yj04v4chn1",
            "tool_3501kb73sh0be5tt4xb5162ejdxz",
            "tool_8001kb754p5setqb2qedb7rfez15",
            "tool_0301kb77mf7vf0sbdyhxn3w470da",
            "NEW_TOOL_ID_HERE"
          ]
        }
      }
    }
  }'
```

### Step 4: Update documentation

1. Add to this file (TOOLS.md)
2. Add to CLAUDE.md
3. Add tool ID to .env
4. Update the health check script

### Step 5: Test

```bash
python3 tools_health_check.py
```

---

## Environment Variables

All required in `.env`:

```bash
# ElevenLabs (required for voice + memory)
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
ELEVENLABS_JOBS_TOOL_ID=tool_6801kb79mrdwfycsawytjq0gx1ck
ELEVENLABS_MUSIC_TOOL_ID=tool_9801kb8k61zpfkksynb8m4wztkkx

# Google Gemini (required for vision)
GEMINI_API_KEY=xxx

# Clerk (required for auth)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxx

# Server
VPS_IP=178.156.162.212
PORT=5000
DOMAIN=ai-guy.mikecerqua.ca
```

---

## Troubleshooting

### Tool not responding
1. Check server is running: `curl https://ai-guy.mikecerqua.ca/api/health`
2. Check specific endpoint: `curl https://ai-guy.mikecerqua.ca/api/[endpoint]`
3. Check server logs: `sudo journalctl -u pi-guy -f`

### Tool not being called by agent
1. Verify tool ID is in agent's tool_ids array
2. Check trigger phrases in tool description
3. Test tool directly via ElevenLabs dashboard

### After code changes
1. Push to GitHub: `git push origin main`
2. On VPS, pull and restart: `cd /home/mike/Mike-AI/ai-eyes && git pull && sudo systemctl restart pi-guy`

---

## Version History

| Date | Change | Tools Affected |
|------|--------|----------------|
| 2024-XX-XX | Initial setup | 1-6 |
| 2024-XX-XX | Added notes system | 7 |
| 2024-XX-XX | Added memory system | 8 |
| 2024-XX-XX | Added jobs/scheduling system | 9 |
| 2024-11-29 | Added music/DJ system | 10 |
