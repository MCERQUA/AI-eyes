# ElevenLabs Advanced Features

Reference documentation for ElevenLabs Conversational AI features beyond basic setup.

## Multi-Voice Support (Voice Switching)

Allows your agent to switch between different voices mid-conversation using XML-style tags.

### Use Cases
- **Multi-character storytelling** - Different voices for different characters
- **Emotional agents** - Voice changes based on emotional context
- **Role-playing scenarios** - Distinct voices for different personas
- **Language tutoring** - Native speaker voices for different languages
- **Pi-Guy's DJ-FoamBot** - Radio announcer voice for updates/announcements

### Configuration
1. Go to agent's **Voice tab** in ElevenLabs dashboard
2. Find **"Multi-voice support"** section
3. Click **"Add voice"** and configure:
   - **Voice label**: Unique identifier (e.g., "RadioVoice", "Spanish", "Narrator")
   - **Voice**: Select from available ElevenLabs voices
   - **Model Family**: Override default (Turbo, Flash, Multilingual) - optional
   - **Language**: Override default language if needed - optional
   - **Description**: Context for when the agent should use this voice

### XML Tag Syntax
```xml
<VOICE_LABEL>text to be spoken in this voice</VOICE_LABEL>
```

**Rules:**
- Replace `VOICE_LABEL` with your configured label (case-sensitive)
- Text outside tags uses the default voice
- Nested tags NOT supported
- Tags must be properly formatted and closed

### Examples

**Radio announcer (Pi-Guy):**
```
Checking server status...
<RadioVoice>LIVE from the DJ-FoamBot control room - all systems operational!</RadioVoice>
Yeah, everything looks fine.
```

**Language tutoring:**
```
In Spanish, we say <Spanish>¡Hola! ¿Cómo estás?</Spanish>
```

**Storytelling:**
```
<Princess>I'm not afraid!</Princess> she declared.
The dragon rumbled, <Dragon>You should be, little one.</Dragon>
```

### Performance Notes
- Voice switching adds minimal overhead
- First use of each voice may have slightly higher latency (voice initialization)
- If agent uses unconfigured label, text falls back to default voice (tags ignored)

### Documentation
- [Multi-voice support | ElevenLabs](https://elevenlabs.io/docs/agents-platform/customization/voice/multi-voice-support)
- [Voice customization | ElevenLabs](https://elevenlabs.io/docs/agents-platform/customization/voice)

---

## Dynamic Variables

Inject runtime values into system prompts, first messages, and tools without hardcoding.

### Syntax
```
{{variable_name}}
```

### Use Cases
- **Personalized greetings**: "Hello {{user_name}}"
- **User-specific data**: Pass account ID, subscription tier, etc.
- **Tool parameters**: Dynamic values in webhook calls
- **Pre-identified users**: Pass face recognition result at conversation start

### System Variables (Built-in)
| Variable | Description |
|----------|-------------|
| `system__agent_id` | Unique ID of agent that started conversation |
| `system__current_agent_id` | Currently active agent (changes after transfers) |
| `system__caller_id` | Caller's phone number (voice calls only) |
| `system__called_number` | Destination phone number (voice calls only) |
| `system__call_duration_secs` | Call duration in seconds |
| `system__conversation_id` | Unique conversation identifier |

### Secret Variables
Prefix with `secret__` for sensitive data (auth tokens, private IDs):
```
{{secret__api_key}}
```
- Only used in webhook headers
- Never sent to LLM provider
- Not included in system prompt

### Example for Pi-Guy
Could pass identified user at connection time:
```
System prompt: "The user {{identified_user}} is talking to you."
First message: "Oh look, {{identified_user}} decided to show up."
```

### Passing Variables
Variables are passed when starting the conversation via SDK or URL parameters.

### Documentation
- [Dynamic variables | ElevenLabs](https://elevenlabs.io/docs/agents-platform/customization/personalization/dynamic-variables)
- [Personalization | ElevenLabs](https://elevenlabs.io/docs/agents-platform/customization/personalization)

---

## Overrides

Completely replace system prompts or first messages at runtime.

### When to Use
- Dynamic variables are **preferred** for most use cases
- Overrides are for **completely replacing** prompts (not just inserting values)

### System Variables for Overrides (Genesys)
- `system__override_system_prompt` - Replace entire system prompt
- `system__override_first_message` - Replace first message
- `system__override_language` - Change agent language

### Documentation
- [Overrides | ElevenLabs](https://elevenlabs.io/docs/agents-platform/customization/personalization/overrides)

---

## SSML Support (Pronunciation Control)

Use SSML phoneme tags for precise pronunciation control.

### Supported Alphabets
- CMU Arpabet
- International Phonetic Alphabet (IPA)

### Compatible Models Only
- Eleven Flash v2
- Eleven Turbo v2
- Eleven English v1

### Note
This is for pronunciation, NOT voice switching. Use multi-voice support for different voices.

---

## Prompting Best Practices

### System Prompt Structure
The system prompt controls:
- Personality and behavior
- Response style
- Tool usage instructions
- Guardrails (what NOT to do)

Does NOT control:
- Turn-taking mechanics
- Language settings (use agent config)
- Voice settings (use Voice tab)

### Response Guidelines
- Keep responses **2-3 sentences** for voice agents
- Always **complete sentences fully** (no trailing off)
- Don't say "I apologize" - blame external factors instead

### Documentation
- [Prompting guide | ElevenLabs](https://elevenlabs.io/docs/agents-platform/best-practices/prompting-guide)
- [How to Prompt a Conversational AI System | ElevenLabs Blog](https://elevenlabs.io/blog/how-to-prompt-a-conversational-ai-system)

---

## Tools Integration

### Webhook Tools
Tools are called via webhooks to your server endpoints.

### Current Pi-Guy Tools (9 total)
| Tool | ID | Endpoint |
|------|-----|----------|
| look_and_see | tool_3401kb73sh07ed5bvhtshsbxq35j | /api/vision |
| identify_person | tool_1901kb73sh08f27bct0d3w81qdgn | /api/identity |
| manage_todos | tool_4801kb73sh09fxfsvjf3csmca1w5 | /api/todos |
| search_web | tool_2901kb73sh0ae2a8z7yj04v4chn1 | /api/search |
| run_command | tool_3501kb73sh0be5tt4xb5162ejdxz | /api/command |
| check_server_status | tool_5601kb73sh06e6q9t8ng87bv1qsa | /api/server-status |
| manage_notes | tool_8001kb754p5setqb2qedb7rfez15 | /api/notes |
| manage_memory | tool_0301kb77mf7vf0sbdyhxn3w470da | /api/memory |
| manage_jobs | tool_6801kb79mrdwfycsawytjq0gx1ck | /api/jobs |

### Tool Parameter Types
- Query parameters (GET requests)
- Request body (POST requests)
- Headers (can use secret variables)

---

## Knowledge Base (Long-Term Memory)

ElevenLabs Knowledge Base enables RAG (Retrieval Augmented Generation) for persistent memory.

### How Pi-Guy Uses It
- `manage_memory` tool creates documents in Knowledge Base
- Documents attached with `usage_mode: "auto"` (RAG retrieval)
- Memories persist across ALL conversations
- Local tracking via `memory_docs.json`

### API Endpoints
```bash
# List documents
GET https://api.elevenlabs.io/v1/convai/agents/{agent_id}/knowledge-base

# Add document
POST https://api.elevenlabs.io/v1/convai/agents/{agent_id}/knowledge-base

# Delete document
DELETE https://api.elevenlabs.io/v1/convai/agents/{agent_id}/knowledge-base/{doc_id}
```

---

## Future Exploration

Things to investigate:
- [ ] Agent-to-agent transfers
- [ ] Phone number integration
- [ ] Custom LLM backends
- [ ] Latency optimization settings
- [ ] Analytics and conversation history API
