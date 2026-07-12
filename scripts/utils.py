"""Utility functions for the SVG Profile Stats Updater.

Contains logger configuration and filesystem cleaning helpers.
"""

import logging
import os
import shutil
import stat
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("svg_updater")

def clean_directory(path: Path) -> None:
    """Safely and recursively removes a directory.
    
    Handles Windows read-only file issues in git history folders.
    """
    if not path.exists():
        return
    
    logger.info(f"Cleaning directory: {path}")
    
    # Walk and force write permissions before deleting
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filepath = Path(root) / name
            try:
                filepath.chmod(stat.S_IWRITE)
                filepath.unlink()
            except Exception as e:
                logger.debug(f"Failed to delete file {filepath}: {e}")
        for name in dirs:
            dirpath = Path(root) / name
            try:
                dirpath.chmod(stat.S_IWRITE)
                dirpath.rmdir()
            except Exception as e:
                logger.debug(f"Failed to delete directory {dirpath}: {e}")
                
    try:
        path.chmod(stat.S_IWRITE)
        path.rmdir()
    except Exception as e:
        logger.warning(f"Could not remove root directory {path}: {e}")
        # Final fallback using shutil
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
