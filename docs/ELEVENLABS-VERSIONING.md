# ElevenLabs Agent Versioning

> Reference documentation for Pi-Guy agent versioning system

## Overview

Agent versioning allows us to safely experiment with Pi-Guy's configuration without risking the production setup. We can create isolated branches, test changes, and gradually roll out updates.

**IMPORTANT:** Once versioning is enabled on an agent, it cannot be disabled.

## Core Concepts

### Versions
- **Immutable snapshots** of agent configuration
- Format: `agtvrsn_xxxx`
- Contains: conversation_config, platform_settings, workflow
- Created automatically when saving changes to a versioned agent

### Branches
- Named lines of development (like git branches)
- Every versioned agent has a **Main** branch (cannot be deleted)
- Additional branches created from any version on main
- Format: `agtbrch_xxxx`

### Traffic Deployment
- Split traffic across branches by percentage
- Must total exactly **100%**
- Deterministic routing based on conversation ID (same user = same branch)

### Drafts
- Unsaved changes stored per-user, per-branch
- Discarded when new version committed or branch merged

## Quick Reference Commands

### Enable Versioning (One-Time)

```bash
# Enable versioning on Pi-Guy agent
curl -X PATCH "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"enable_versioning_if_not_enabled": true}'
```

### List All Branches

```bash
curl -s "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID/branches" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | python3 -m json.tool
```

### Get Branch Details

```bash
curl -s "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID/branches/agtbrch_xxxx" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | python3 -m json.tool
```

### Create a New Branch

```bash
# Create branch from a specific version on main
curl -X POST "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID/branches" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "parent_version_id": "agtvrsn_xxxx",
    "name": "experiment-name",
    "description": "Testing new feature"
  }'
```

### Commit Changes to a Branch

```bash
# Update agent on specific branch (creates new version)
curl -X PATCH "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID?branch_id=agtbrch_xxxx" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_config": {
      "agent": {
        "prompt": {
          "prompt": "Updated system prompt..."
        }
      }
    }
  }'
```

### Deploy Traffic

```bash
# Split traffic between branches (must total 100%)
curl -X POST "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID/deployments" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "deployments": [
      {"branch_id": "agtbrch_main", "percentage": 90},
      {"branch_id": "agtbrch_xxxx", "percentage": 10}
    ]
  }'
```

### Merge Branch to Main

```bash
curl -X POST "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID/branches/agtbrch_xxxx/merge" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "target_branch_id": "agtbrch_main",
    "archive_source_branch": true
  }'
```

### Archive a Branch

```bash
# Must have 0% traffic allocated first
curl -X PATCH "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID/branches/agtbrch_xxxx" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"archived": true}'
```

### Get Agent at Specific Version

```bash
curl -s "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID?version_id=agtvrsn_xxxx" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | python3 -m json.tool
```

### Get Agent at Branch Tip (Latest)

```bash
curl -s "https://api.elevenlabs.io/v1/convai/agents/$ELEVENLABS_AGENT_ID?branch_id=agtbrch_xxxx" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" | python3 -m json.tool
```

## What Gets Versioned

### Versioned Settings (Per-Branch)
| Category | Settings |
|----------|----------|
| **Conversation Config** | System prompt, LLM params, voice settings, tools, knowledge base, first message |
| **Platform Settings** | Evaluation, widget, data collection, safety/guardrails |
| **Workflow** | Complete workflow definition |

### Per-Agent Settings (Shared Across All Versions)
| Setting | Description |
|---------|-------------|
| `name`, `tags` | Agent name and tags |
| `auth` | Authentication settings |
| `call_limits` | Concurrency and daily limits |
| `privacy` | Retention settings |

## Best Practices

1. **Create tests before branching** - Establish baseline behavior
2. **Use descriptive branch names** - e.g., `experiment/shorter-responses`
3. **Document branch purposes** - Use description field
4. **Start with small traffic %** - Begin with 5-10%
5. **Monitor metrics before increasing** - Check analytics dashboard
6. **Increase traffic gradually** - 10% → 25% → 50% → 100%
7. **Keep branches short-lived** - Merge successful experiments promptly

## Workflow Example

```
1. Save current config backup
2. Enable versioning (one-time)
3. Create branch: "experiment/new-voice"
4. Make changes on branch
5. Deploy 10% traffic to branch
6. Monitor performance
7. If successful, increase to 50%
8. If good, merge to main (100%)
9. Archive experiment branch
```

## Related Files

- `docs/AGENT-VERSIONS.md` - Version history and changelog
- `docs/agent-snapshot-*.json` - Configuration backups
- `CLAUDE.md` - Main project documentation
