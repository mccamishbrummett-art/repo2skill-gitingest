---
name: gitingest
description: Build clean LLM knowledge bases from GitHub repositories on any topic. Use this skill whenever the user wants to create a knowledge base, study material, reference docs, or context for an AI tutor/consultant from GitHub repositories. Trigger when users mention building a knowledge base, creating a tutor or consultant agent, downloading repos for LLM context, parsing GitHub content, gitingest, studying a technology from source repos. Even for casual requests like "help me understand React" or "I need docs on Kubernetes" — if a curated GitHub repo dump would be valuable, use this skill.
---

# GitIngest — LLM Knowledge Base Builder

Build clean, filtered knowledge bases from GitHub repositories. The result is `.txt` files containing only valuable content (docs, guides, examples) with all noise filtered out — ready to feed into an LLM as context for a tutor, consultant, or assistant agent.

## Prerequisites

- Python package `gitingest` installed (`pip install gitingest`)
- `git` available in PATH (required for `--wiki` mode)
- Internet access for downloading repositories

## Workflow

### Step 1: Understand the Goal

Ask the user:
1. **What topic?** — What technology or area they need a knowledge base for
2. **What's the end goal?** — Tutor? Consultant? Reference? This affects what content is valuable
3. **Specific repos or search?** — Do they have URLs, or should you find repos?

### Step 2: Find Repositories (if no URL given)

Search GitHub for relevant repos using web search (e.g. `site:github.com <topic> tutorial guide documentation`).

Present 3-5 options with:
- Name and stars
- Brief description of what's inside
- Why it's relevant

Let the user choose which to process. Multiple repos are fine — each becomes a separate file.

### Step 3: Process Each Repository

For each selected repository, follow this two-pass sequence:

#### Pass 1: Reconnaissance

Run the fetch script in tree-only mode:

```bash
python <this-skill-path>/scripts/fetch_repo.py <URL> --tree-only --output-dir ./GitDB
```

The base filter (binaries, lock files, build output, IDE configs) is applied automatically.

Read the generated `GitDB/<repo-name>_tree.txt` and analyze the structure.

#### Pass 2: Design the Filter

Looking at the tree, classify each directory/file group:
- ✅ Valuable (docs, guides, examples, relevant configs)
- 🗑️ Noise (CI, tests, build artifacts, meta files)
- 🟡 Context-dependent (source code, Docker files)

**Choose the method:**

| Condition | Method |
|-----------|--------|
| Most content is useful, just remove junk | **Blacklist** (`--exclude`) |
| Only specific folders needed (e.g. `docs/`) | **Whitelist** (`--include`) |
| Repo < 50 files, mostly docs | **Blacklist** |
| Repo > 200 files, need only docs/ | **Whitelist** |

#### Pass 3: Clean Download

Run with refined filter:

```bash
# Blacklist mode (extra excludes on top of base filter):
python <this-skill-path>/scripts/fetch_repo.py <URL> --output-dir ./GitDB --exclude "tests/*" ".github/*" "LICENSE" "CONTRIBUTING.md"

# OR whitelist mode:
python <this-skill-path>/scripts/fetch_repo.py <URL> --output-dir ./GitDB --include "docs/*" "examples/*" "README.md"
```

Result is saved as `GitDB/<repo-name>.txt`.

Clean up the temporary tree file after: delete `GitDB/<repo-name>_tree.txt`.

### Step 4: Check for Wiki

Many GitHub repos keep their detailed documentation in the Wiki (setup guides, configuration, API docs, troubleshooting). The Wiki is a separate git repository that gitingest doesn't fetch by default.

**Always check if a wiki exists** — visit `https://github.com/OWNER/REPO/wiki` mentally or search for references to "wiki" in the README.

If a wiki is likely to exist and be useful:

```bash
# Tree-only reconnaissance of wiki:
python <this-skill-path>/scripts/fetch_repo.py <URL> --wiki --tree-only --output-dir ./GitDB

# Full wiki download (after reviewing tree):
python <this-skill-path>/scripts/fetch_repo.py <URL> --wiki --output-dir ./GitDB
```

This clones the wiki repo (`<url>.wiki.git`) to a temp directory, ingests it via gitingest, saves as `GitDB/<repo-name>-wiki.txt`, and cleans up.

### Step 5: Finalize and Report

After all repos are processed, you MUST rename the resulting output `.txt` files to include the current date and their size in KB. 
The naming format must be: `<name>-DD-MM-YYYY-<size>KB.txt` (e.g., `v2rayN-04-04-2026-225KB.txt` or `v2rayN-wiki-04-04-2026-13KB.txt`).
To do this, check the sizes of the created files, and then use the terminal to rename them.

Finally, tell the user:
- What was downloaded and what was filtered out
- File locations (with the new names)
- Whether wiki was available and what it contained
- Suggestions for how to use the files

---

## Filtering Rules

### 🔴 Always Exclude (built into script automatically)

Binary/media, compiled files, lock files, dependencies, build output, IDE configs, git internals. See `BASE_EXCLUDES` in the script for the full list.

### 🟡 Usually Exclude (add via `--exclude` unless topic requires them)

| Category | Patterns | KEEP when topic is... |
|----------|----------|-----------------------|
| CI/CD | `.github/workflows/*` `.travis.yml` `.circleci/*` | DevOps, CI/CD |
| Tests | `tests/*` `__tests__/*` `*_test.*` `*.spec.*` | Testing, TDD |
| Docker | `Dockerfile` `docker-compose.yml` | Containers, deployment |
| Meta | `LICENSE*` `CONTRIBUTING*` `CODE_OF_CONDUCT*` `SECURITY*` | Never keep |
| Build configs | `webpack.config.*` `tsconfig.json` `Makefile` | Build systems |
| Linters | `.eslintrc*` `.prettierrc*` `.flake8` | Code style tools |
| Changelog | `CHANGELOG*` `CHANGES*` | Version migration |

### ✅ High-Value Content (prioritize keeping)

| Category | Patterns |
|----------|----------|
| Documentation | `docs/*` `doc/*` `documentation/*` `*.md` `*.rst` |
| Guides | `guides/*` `tutorials/*` `howto/*` |
| Examples | `examples/*` `example/*` `samples/*` `demo/*` |
| README | `README*` (root — essential overview) |
| API docs | `api/*` `reference/*` |

### Source Code — Decide by Goal

| User's goal | Decision |
|-------------|----------|
| Learn to USE a tool | Skip code, keep docs + examples |
| Understand HOW it works | Keep core source, skip utilities |
| Repo IS documentation | Keep all .md files, skip everything else |

---

## Script Reference

Script path: `<this-skill-directory>/scripts/fetch_repo.py`

| Argument | Description |
|----------|-------------|
| `url` | GitHub repository URL (required) |
| `--tree-only` | Only save summary + file tree |
| `--wiki` | Clone and ingest the GitHub Wiki instead of main repo |
| `--output-dir` | Output directory (default: `./GitDB`) |
| `--output-name` | Custom output filename |
| `--exclude` | Extra exclude patterns (on top of base filter) |
| `--include` | Include patterns (whitelist mode) |
| `--no-base-filter` | Disable built-in base exclusions |
| `--branch` | Specific branch to fetch |

### Output File Naming

| Mode | Filename |
|------|----------|
| Main repo | `<repo-name>.txt` |
| Main repo tree | `<repo-name>_tree.txt` |
| Wiki | `<repo-name>-wiki.txt` |
| Wiki tree | `<repo-name>-wiki_tree.txt` |
