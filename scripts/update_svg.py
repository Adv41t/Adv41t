"""Main script to update the custom SVG terminal profile card.

Retrieves GitHub statistics, clones owned repositories to compute Lines of Code (LOC),
and updates the SVG profile card.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from scripts.config import USERNAME, SVG_PATH, TEMP_CLONE_DIR, COMMON_CODE_EXTENSIONS
from scripts.utils import logger, clean_directory
from scripts.github_api import GitHubAPI
from scripts.svg_utils import update_svg_file

def calculate_single_repo_loc(repo: Dict[str, Any], token: str, author_patterns: List[str]) -> Dict[str, int]:
    """Clones a single repository to compute current LOC, lines added, and lines deleted.
    
    Cleans up the repository directory after calculation.
    """
    repo_name = repo["name"]
    clone_url = repo["cloneUrl"]
    repo_dir = TEMP_CLONE_DIR / repo_name
    
    loc_stats = {"loc_data": 0, "loc_add": 0, "loc_del": 0}
    
    # Authenticate clone URL using the token
    auth_url = clone_url
    if "github.com" in clone_url:
        auth_url = clone_url.replace("https://github.com", f"https://x-access-token:{token}@github.com")
        
    try:
        logger.info(f"Cloning {repo_name} (single branch clone)...")
        # Run shallow-like cloning without checking out other branches to save bandwidth
        subprocess.run(
            ["git", "clone", "--single-branch", auth_url, str(repo_dir)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Calculate current LOC from files tracked by git
        logger.debug(f"Counting lines of code in {repo_name}...")
        res_files = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        for file_path in res_files.stdout.splitlines():
            filepath = repo_dir / file_path
            if filepath.is_file() and filepath.suffix.lower() in COMMON_CODE_EXTENSIONS:
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        loc_stats["loc_data"] += sum(1 for _ in f)
                except Exception as e:
                    logger.debug(f"Could not read file {filepath}: {e}")
                    
        # Calculate lines added/deleted by user using git log --numstat
        logger.debug(f"Calculating commits statistics in {repo_name}...")
        git_log_cmd = ["git", "log"]
        for author in author_patterns:
            git_log_cmd.extend(["--author", author])
        git_log_cmd.extend(["--numstat", "--pretty=tformat:"])
        
        res_log = subprocess.run(
            git_log_cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        for line in res_log.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    if parts[0].isdigit():
                        loc_stats["loc_add"] += int(parts[0])
                    if parts[1].isdigit():
                        loc_stats["loc_del"] += int(parts[1])
                except ValueError:
                    pass
                    
        logger.info(
            f"Repository {repo_name} stats: "
            f"LOC: {loc_stats['loc_data']:,} | "
            f"Added: {loc_stats['loc_add']:,} | "
            f"Deleted: {loc_stats['loc_del']:,}"
        )
        
    except Exception as e:
        logger.warning(f"Failed to calculate LOC for repository {repo_name}: {e}")
    finally:
        # Clean up repository directory immediately to save local storage
        clean_directory(repo_dir)
        
    return loc_stats

def calculate_all_loc(repos: List[Dict[str, Any]], token: str, username: str, api: GitHubAPI) -> Dict[str, int]:
    """Sequentially clones all repositories and aggregates lines of code statistics.
    
    Isolated in its own function to allow easy mock/bypass or performance tuning.
    """
    total_stats = {"loc_data": 0, "loc_add": 0, "loc_del": 0}
    
    if not repos:
        logger.warning("No repositories found to calculate LOC.")
        return total_stats
        
    # Build list of author strings to filter git log matches
    author_patterns = [username]
    try:
        user_metadata = api._get_rest("user")
        if user_metadata.get("name"):
            author_patterns.append(user_metadata["name"])
        if user_metadata.get("email"):
            author_patterns.append(user_metadata["email"])
        if user_metadata.get("id"):
            author_patterns.append(f"{user_metadata['id']}+{username}@users.noreply.github.com")
    except Exception as e:
        logger.warning(f"Could not retrieve authenticated user metadata for git authors matching: {e}")
        
    author_patterns = list(set(filter(None, author_patterns)))
    logger.info(f"Matching Git authors: {author_patterns}")
    
    # Ensure clone parent directory exists and is clean
    clean_directory(TEMP_CLONE_DIR)
    TEMP_CLONE_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        for repo in repos:
            # We only clone repositories owned by the user, skipping forks
            if repo.get("isPrivate") is False or token:  # We can clone private if we have token
                repo_stats = calculate_single_repo_loc(repo, token, author_patterns)
                total_stats["loc_data"] += repo_stats["loc_data"]
                total_stats["loc_add"] += repo_stats["loc_add"]
                total_stats["loc_del"] += repo_stats["loc_del"]
    finally:
        # Final cleanup of cloning directory
        clean_directory(TEMP_CLONE_DIR)
        
    return total_stats

def main() -> None:
    """Main function orchestrating API calls, LOC counting, and SVG updates."""
    # 1. Fetch token (support both GH_TOKEN and TOKEN_GH)
    token = os.environ.get("GH_TOKEN") or os.environ.get("TOKEN_GH")
    if not token:
        logger.error("Neither GH_TOKEN nor TOKEN_GH environment variable is set. Exiting gracefully.")
        sys.exit(0)
        
    try:
        # 2. Initialize API and fetch stats
        logger.info(f"Initializing GitHub API Client for user: {USERNAME}")
        api = GitHubAPI(token)
        
        logger.info("Fetching profile and repository statistics...")
        stats = api.get_user_stats(USERNAME)
        
        # 3. Calculate Lines of Code (LOC)
        logger.info("Calculating Lines of Code (this might take a few moments)...")
        loc_stats = calculate_all_loc(stats["repositories"], token, USERNAME, api)
        
        # Merge stats
        stats.update(loc_stats)
        
        # 4. Update the SVG
        logger.info("Updating SVG profile card...")
        success = update_svg_file(SVG_PATH, stats)
        if success:
            logger.info("Profile SVG successfully updated!")
        else:
            logger.info("Profile SVG update did not result in any changes or skipped due to errors.")
            
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        logger.info("Exiting gracefully keeping previous SVG intact.")
        sys.exit(0)

if __name__ == "__main__":
    main()
