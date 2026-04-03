# 📚 repo2skill-gitingest

> AI skill for building clean LLM knowledge bases from GitHub repositories.

A universal skill for AI coding assistants (Cursor, Claude Code, Antigravity, Windsurf, and others) that turns any GitHub repository into a curated, noise-free `.txt` knowledge base — ready to use as context for an AI tutor, consultant, or assistant agent.

Works with any LLM model that supports the skill format (SKILL.md with YAML frontmatter).

## ✨ What it does

1. **Find repos** — you give a topic ("VPN setup", "React hooks"), the AI finds the best GitHub repositories and helps you choose
2. **Analyze structure** — downloads only the file tree first (fast, lightweight), then analyzes what's useful
3. **Smart filtering** — decides between whitelist or blacklist approach based on repo structure
4. **Clean download** — fetches only the valuable content: docs, guides, examples, configs
5. **Wiki support** — optionally fetches the GitHub Wiki (separate git repo), which often contains the real documentation

**Result:** One clean `.txt` file per repo, saved to `./GitDB/`, ready to paste into any LLM.

## 🗂️ Output example

```
GitDB/
├── 3x-ui.txt           ← main repo (filtered)
└── 3x-ui-wiki.txt      ← wiki documentation
```

## 🔧 Requirements

- Python 3.8+
- `pip install gitingest`
- `git` in PATH (for `--wiki` mode)

## 🚀 Installation

Copy the skill folder into your assistant's skills directory:

| Assistant | Path |
|-----------|------|
| **Antigravity** | `%APPDATA%\.gemini\antigravity\skills\gitingest\` |
| **Claude Code** | `.claude/skills/gitingest/` (project) or `~/.claude/skills/gitingest/` (global) |
| **Cursor** | `.cursor/skills/gitingest/` |
| **Other** | Check your assistant's skill/plugin directory |

Then just ask your AI assistant:

> *"I want to create a knowledge base about WireGuard VPN setup"*
> *"Build me a tutor agent for FastAPI"*
> *"Download the docs from github.com/tiangolo/fastapi for me"*

The skill handles the rest.

## 📜 Script usage (standalone)

The `scripts/fetch_repo.py` script can also be used directly without any AI assistant:

```bash
# Step 1: Get file tree for analysis
python scripts/fetch_repo.py https://github.com/owner/repo --tree-only --output-dir ./GitDB

# Step 2: Full filtered download (blacklist mode)
python scripts/fetch_repo.py https://github.com/owner/repo --output-dir ./GitDB \
  --exclude "tests/*" ".github/*" "LICENSE" "CONTRIBUTING.md"

# Step 3 (optional): Download Wiki
python scripts/fetch_repo.py https://github.com/owner/repo --wiki --output-dir ./GitDB

# Whitelist mode (only specific folders)
python scripts/fetch_repo.py https://github.com/owner/repo --output-dir ./GitDB \
  --include "docs/*" "examples/*" "README.md"
```

### All arguments

| Argument | Description |
|----------|-------------|
| `url` | GitHub repository URL (required) |
| `--tree-only` | Save only file tree (for structure analysis) |
| `--wiki` | Clone and ingest the GitHub Wiki |
| `--output-dir` | Output directory (default: `./GitDB`) |
| `--output-name` | Custom output filename |
| `--include` | Whitelist patterns (only these files kept) |
| `--exclude` | Extra blacklist patterns (added to base filter) |
| `--no-base-filter` | Disable built-in noise filter |
| `--branch` | Specific branch to fetch |

## 🧹 Built-in noise filter

The script automatically removes:
- Binaries, images, fonts, archives
- Minified JS/CSS, source maps
- Lock files (`package-lock.json`, `go.sum`, etc.)
- `node_modules/`, `vendor/`, `dist/`, `build/`
- IDE configs (`.vscode/`, `.idea/`)
- Git internals

## 📄 License

MIT
