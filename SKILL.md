# [Skill Name] Skill

<!--
INSTRUCTIONS FOR CLAUDE
This file tells Claude how to use this skill. Replace all placeholders
and describe clearly what commands are available, when to use them,
and what arguments each script expects.
-->

## Overview

[Describe what this skill does and what system it integrates with.]

Credentials are loaded from `.env` (not included in public release).

## Available Commands

### [Command Name]

```bash
python /mnt/skills/user/[folder]/scripts/[script].py [args]
```

[Description: what it does, when to use it, what it returns.]

**Arguments:**
- `arg1` — description
- `arg2` (optional) — description, default: value

**Example:**
```bash
python /mnt/skills/user/[folder]/scripts/[script].py "search term"
```

## Credentials

Required `.env` variables:

```
EXAMPLE_URL=https://...
EXAMPLE_USER=user@example.com
EXAMPLE_APIKEY=your-api-key
```
