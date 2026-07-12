"""Configuration file for the SVG Profile Stats Updater.

Contains paths, GitHub usernames, and alignment budgets for terminal dots.
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
SVG_PATH = BASE_DIR / "assets" / "profile.svg"
TEMP_CLONE_DIR = BASE_DIR / "temp_repos"

# GitHub settings
USERNAME = "Adv41t"

# Spacing budget configuration for dot-alignment.
# The budgets represent:
# - repo_data: dots_count + len(repo_data) + len(contrib_data)
# - star_data: dots_count + len(star_data)
# - commit_data: dots_count + len(commit_data)
# - follower_data: dots_count + len(follower_data)
# - loc_data: dots_count + len(loc_data)
# - loc_del: spaces_count + len(loc_add) + len(loc_del)
ALIGNMENT_BUDGETS = {
    "repo_data": 8,
    "star_data": 13,
    "commit_data": 19,
    "follower_data": 9,
    "loc_data": 7,
    "loc_del": 13,
}

# Common programming file extensions to include in LOC counts
COMMON_CODE_EXTENSIONS = {
    ".py", ".c", ".cpp", ".h", ".hpp", ".cc", ".java", ".js", ".ts", ".tsx", ".jsx",
    ".html", ".css", ".sh", ".bat", ".ps1", ".go", ".rs", ".php", ".rb", ".sql",
    ".yml", ".yaml", ".json", ".md", ".kt", ".swift", ".scala", ".r", ".cs", ".m"
}

