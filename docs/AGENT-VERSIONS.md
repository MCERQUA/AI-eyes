# Pi-Guy Agent Version History

> Tracking all versions of the Pi-Guy ElevenLabs agent

## Agent Info

| Property | Value |
|----------|-------|
| **Agent ID** | `agent_0801kb2240vcea2ayx0a2qxmheha` |
| **Agent Name** | Pi-Guy |
| **Main Branch ID** | `agtbrch_0601kcccvnnveza8ws2egm714wmn` |
| **Versioning Enabled** | 2025-12-13 |

---

## Current Production (Main Branch)

**Latest Version:** `agtvrsn_3601kcccvq5cf8yrbft5vzgeyryy`
**Traffic:** 100%

---

## Version History

### v2 - Initial Versioning Snapshot (CURRENT)
| Property | Value |
|----------|-------|
| **Version ID** | `agtvrsn_3601kcccvq5cf8yrbft5vzgeyryy` |
| **Branch** | Main |
| **Date** | 2025-12-13 17:41:43 |
| **Seq #** | 2 |
| **Parent** | `agtvrsn_7901kcccvnntf2g9r3h0z6s5bqxc` |

**Summary:** Snapshot when versioning was enabled. Contains:
- 13 tools (11 webhook/client + 2 system)
- 3 voices: Primary (eZm9vdjYgL9PZKtf7XMM), Radio Voice, Kitt-Voice, DJ-Soul
- LLM: claude-sonnet-4-5
- DJ-FoamBot + DJ-Soul dual persona system
- Song generation via Suno AI
- Commercial playback system
- Full soundboard integration

**Tools:**
- manage_memory, identify_person, search_web, look_and_see
- run_command, manage_todos, check_server_status, manage_jobs
- manage_notes, play_music, dj_soundboard (client), generate_song
- play_commercial, end_call, skip_turn

---

### v1 - Initial Version
| Property | Value |
|----------|-------|
| **Version ID** | `agtvrsn_7901kcccvnntf2g9r3h0z6s5bqxc` |
| **Branch** | Main |
| **Date** | 2025-12-13 17:41:41 |
| **Seq #** | 1 |
| **Parent** | None (root) |

**Summary:** Automatic initial version created when versioning was enabled.

---

## Active Branches

| Branch | ID | Traffic | Status | Description |
|--------|-----|---------|--------|-------------|
| **Main** | `agtbrch_0601kcccvnnveza8ws2egm714wmn` | 100% | Active | Production branch |

---

## Archived Branches

_None yet_

---

## How to Use This Document

### When Making Changes

1. **Before changes:** Save backup and note current version
2. **After committing:** Add new version entry here with:
   - Version ID
   - Date
   - Summary of changes
   - Any config changes (tools, voices, LLM, etc.)

### Version Entry Template

```markdown
### vX - [Brief Description]
| Property | Value |
|----------|-------|
| **Version ID** | `agtvrsn_xxxx` |
| **Branch** | Main/[branch name] |
| **Date** | YYYY-MM-DD HH:MM:SS |
| **Seq #** | X |
| **Parent** | `agtvrsn_xxxx` |

**Summary:** What changed in this version

**Changes:**
- [ ] Prompt changes
- [ ] Tool added/removed
- [ ] Voice changes
- [ ] LLM changes
- [ ] Other config
```

### Creating Experiment Branches

1. Document the branch purpose before creating
2. Add entry to "Active Branches" table
3. Track versions on that branch separately
4. When merged, move to "Archived Branches" with outcome

---

## Quick Commands

```bash
# Get current version info
curl -s "https://api.elevenlabs.io/v1/convai/agents/agent_0801kb2240vcea2ayx0a2qxmheha" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('version_id:', d.get('version_id')); print('branch_id:', d.get('branch_id'))"

# List all branches
curl -s "https://api.elevenlabs.io/v1/convai/agents/agent_0801kb2240vcea2ayx0a2qxmheha/branches" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | python3 -m json.tool

# Get branch with versions
curl -s "https://api.elevenlabs.io/v1/convai/agents/agent_0801kb2240vcea2ayx0a2qxmheha/branches/agtbrch_0601kcccvnnveza8ws2egm714wmn" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | python3 -m json.tool

# Get agent at specific version
curl -s "https://api.elevenlabs.io/v1/convai/agents/agent_0801kb2240vcea2ayx0a2qxmheha?version_id=agtvrsn_xxxx" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | python3 -m json.tool > version_backup.json
```

---

## Related Files

- `docs/ELEVENLABS-VERSIONING.md` - API reference for versioning
- `docs/agent-backup-*.json` - Configuration backups
- `docs/Elevenlabs-Agent-Master-Prompt.md` - Master prompt reference
