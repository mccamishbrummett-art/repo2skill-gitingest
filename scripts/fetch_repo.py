"""
GitIngest Repository Fetcher
Fetches and filters GitHub repository content for LLM knowledge bases.

Usage:
  python fetch_repo.py <url> [options]

Modes:
  --tree-only    Only fetch summary + file tree (for reconnaissance)
  --wiki         Clone and ingest the GitHub Wiki instead of the main repo
  (default)      Fetch full filtered content
"""

import argparse
import os
import sys
import re
import shutil
import subprocess
import tempfile
from gitingest import ingest


# Base exclusion patterns — always applied unless --no-base-filter is set.
# These are universally useless for LLM knowledge bases regardless of topic.
BASE_EXCLUDES = [
    # Binary / media
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.svg", "*.bmp", "*.webp",
    "*.mp3", "*.mp4", "*.wav", "*.avi", "*.mov",
    "*.zip", "*.tar", "*.gz", "*.rar", "*.7z",
    "*.woff", "*.woff2", "*.ttf", "*.eot", "*.otf",
    "*.pdf",
    # Compiled / minified
    "*.pyc", "*.pyo", "*.class", "*.o", "*.so", "*.dll", "*.exe",
    "*.min.js", "*.min.css", "*.map",
    # Lock files
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", "go.sum", "Cargo.lock",
    "composer.lock", "Gemfile.lock",
    # Dependencies
    "node_modules/*", "vendor/*", "third_party/*",
    # Build output
    "dist/*", "build/*", "out/*", ".next/*", "__pycache__/*",
    ".cache/*", ".parcel-cache/*", "coverage/*",
    # IDE / editor
    ".vscode/*", ".idea/*", "*.swp", "*.swo", ".DS_Store", "Thumbs.db",
    # Git internals
    ".git/*", ".gitmodules", ".gitattributes",
]


def get_repo_name(url: str) -> str:
    """Extract repository name from GitHub URL."""
    match = re.search(r"github\.com/[\w.-]+/([\w.-]+)", url)
    if match:
        return match.group(1).rstrip(".git")
    return "repository"


def build_wiki_url(url: str) -> str:
    """Convert a GitHub repo URL to its Wiki git clone URL."""
    # Normalize: remove trailing .git or /
    clean = url.rstrip("/")
    if clean.endswith(".git"):
        clean = clean[:-4]
    return clean + ".wiki.git"


def clone_wiki(wiki_url: str, dest_dir: str) -> bool:
    """Clone the GitHub Wiki repo into dest_dir. Returns True on success."""
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", wiki_url, dest_dir],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            # Wiki may not exist for this repo
            print(f"Warning: Could not clone wiki — {result.stderr.strip()}")
            return False
        return True
    except FileNotFoundError:
        print("Error: git is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Error: wiki clone timed out after 120 seconds.", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fetch GitHub repo content for LLM knowledge base"
    )
    parser.add_argument("url", help="GitHub repository URL")
    parser.add_argument(
        "--tree-only",
        action="store_true",
        help="Only fetch summary and file tree (for structure analysis)",
    )
    parser.add_argument(
        "--wiki",
        action="store_true",
        help="Clone and ingest the GitHub Wiki instead of the main repo",
    )
    parser.add_argument(
        "--output-dir",
        default="./GitDB",
        help="Output directory (default: ./GitDB)",
    )
    parser.add_argument(
        "--output-name",
        default=None,
        help="Output filename (default: <repo-name>.txt or <repo-name>-wiki.txt)",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=None,
        help="Include patterns — whitelist mode (only matching files are kept)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=None,
        help="Additional exclude patterns (added on top of base filter)",
    )
    parser.add_argument(
        "--no-base-filter",
        action="store_true",
        help="Disable the built-in base exclusion filter",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Specific branch to fetch",
    )

    args = parser.parse_args()
    repo_name = get_repo_name(args.url)

    # --- Wiki mode: clone wiki repo to temp dir, then ingest locally ---
    wiki_tmp_dir = None
    ingest_source = args.url

    if args.wiki:
        wiki_url = build_wiki_url(args.url)
        wiki_tmp_dir = tempfile.mkdtemp(prefix="gitingest_wiki_")
        wiki_clone_path = os.path.join(wiki_tmp_dir, f"{repo_name}.wiki")
        print(f"Cloning wiki: {wiki_url}")
        if not clone_wiki(wiki_url, wiki_clone_path):
            shutil.rmtree(wiki_tmp_dir, ignore_errors=True)
            print("This repository may not have a Wiki.", file=sys.stderr)
            sys.exit(1)
        ingest_source = wiki_clone_path
        print(f"Wiki cloned to temp dir, ingesting locally...")

    # Build ingest keyword arguments
    kwargs = {}

    if args.include:
        kwargs["include_patterns"] = args.include
        print(f"[whitelist] Include patterns: {args.include}")

    # Build exclude list: base filter + user's extra patterns
    excludes = []
    if not args.no_base_filter:
        excludes.extend(BASE_EXCLUDES)
    if args.exclude:
        excludes.extend(args.exclude)
    if excludes:
        kwargs["exclude_patterns"] = excludes

    if args.branch and not args.wiki:
        kwargs["branch"] = args.branch

    mode_parts = []
    if args.wiki:
        mode_parts.append("wiki")
    if args.tree_only:
        mode_parts.append("tree-only")
    else:
        mode_parts.append("full content")
    mode = " / ".join(mode_parts)

    print(f"Repository : {args.url}")
    print(f"Mode       : {mode}")
    if args.exclude:
        print(f"Extra excl.: {args.exclude}")
    print("Fetching...")

    try:
        summary, tree, content = ingest(ingest_source, **kwargs)
    except Exception as e:
        print(f"\nError fetching repository: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temp wiki clone
        if wiki_tmp_dir:
            shutil.rmtree(wiki_tmp_dir, ignore_errors=True)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Determine default filename
    suffix = "-wiki" if args.wiki else ""

    if args.tree_only:
        output_file = os.path.join(args.output_dir, f"{repo_name}{suffix}_tree.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"{summary}\n\n{tree}")
        print(f"\nTree saved: {output_file}")
    else:
        output_name = args.output_name or f"{repo_name}{suffix}.txt"
        if not output_name.endswith(".txt"):
            output_name += ".txt"
        output_file = os.path.join(args.output_dir, output_name)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"{summary}\n\n{tree}\n\n{content}")
        print(f"\nKnowledge base saved: {output_file}")

    print("Done!")


if __name__ == "__main__":
    main()
