# harness-api-switcher

Beautiful [Rich](https://github.com/Textualize/rich) TUI to switch API keys across coding
harnesses **per profile**. One command flips every harness to the credentials of a profile.

Supported harnesses:

| Harness | Target written |
| --- | --- |
| opencode | `~/.local/share/opencode/auth.json` |
| hermes | `%LOCALAPPDATA%/hermes/.env` + `config.yaml` (or `~/.hermes`) |
| claude code | `~/.claude/settings.json` (`env` block) |
| codex | `~/.codex/auth.json` + `~/.codex/config.toml` |

## Install

```bash
uv sync
uv run has          # launches the TUI
```

The `has` script is also installed into the environment (`uv run has --help`).

## Usage

Run `has` with no arguments for the full-screen TUI:

- `↑` / `↓` move, `enter` apply, `n` new profile, `e` edit, `c` capture current setup,
  `d` delete, `r` reload, `q` quit.
- Apply shows a **dry-run preview** with masked keys before writing.

CLI subcommands (scripting / non-interactive):

```bash
has list                 # list profiles
has use work             # apply profile "work"
has use work --dry-run   # preview only
has current              # show active profile
has show work            # print profile (keys masked)
has show work --reveal   # print profile with secrets
has capture work         # snapshot current harness credentials into a profile
has edit                 # open the config JSON in $EDITOR
has path                 # print the config path
has doctor               # diagnose config + harness detection
has backup               # back up the config file
```

## Config

Default location: `~/.config/harness-api-switcher/config.json`
(override with the `HAS_CONFIG` environment variable).

```jsonc
{
  "version": 1,
  "active_profile": "personal",
  "profiles": {
    "personal": {
      "harnesses": {
        "opencode": {
          "providers": {
            "opencode-go": { "type": "api", "key": "sk-..." },
            "zai-coding-plan": { "type": "api", "key": "..." }
          }
        },
        "hermes": {
          "provider": "opencode-go",
          "model": "deepseek-v4-flash",
          "env": { "OPENCODE_GO_API_KEY": "..." }
        },
        "claude": { "env": { "ANTHROPIC_API_KEY": "..." } },
        "codex": { "auth": { "OPENAI_API_KEY": "..." }, "model": "gpt-5.6-luna" }
      }
    }
  }
}
```

A harness omitted from a profile is left untouched when that profile is applied.

## Safety

- Every write makes a timestamped backup (`*.bak.<timestamp>`); the last 10 are kept.
- Writes are atomic (temp file + replace).
- The config file is created with restrictive permissions where the OS allows it.
- Secrets are masked in all output unless `--reveal` is passed.

## Development

```bash
uv run pytest
```
