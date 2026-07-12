"""SVG processing utilities.

Parses the SVG, updates corresponding tspan elements, and adjusts dot alignments.
"""

from pathlib import Path
from typing import Dict, Any
import xml.etree.ElementTree as ET
from scripts.config import SVG_PATH
from scripts.utils import logger

# Register the default SVG namespace to prevent ElementTree from adding 'ns0:' prefixes
ET.register_namespace("", "http://www.w3.org/2000/svg")

def get_padding_content(tspan_id: str, value_len: int) -> str:
    """Calculates the correct dot or space padding for a given tspan ID based on config budgets."""
    from scripts.config import ALIGNMENT_BUDGETS
    
    if tspan_id == "loc_del_dots":
        budget_key = "loc_del"
    else:
        budget_key = tspan_id.replace("_dots", "")
        
    budget = ALIGNMENT_BUDGETS.get(budget_key)
    if budget is None:
        raise ValueError(f"No alignment budget configured for tspan ID: {tspan_id}")
        
    if tspan_id == "loc_del_dots":
        # Space padding: no dots, just spaces. Default to at least 1 space.
        spaces_count = budget - value_len
        if spaces_count < 1:
            spaces_count = 1
        return " " * spaces_count
        
    elif tspan_id == "loc_data_dots":
        # Special case: no leading space, only trailing space. Default to at least 0 dots.
        dots_count = budget - value_len
        if dots_count < 0:
            dots_count = 0
        return "." * dots_count + " "
        
    else:
        # Standard decorative dots: space + dots + space. Default to at least 1 dot.
        dots_count = budget - value_len
        if dots_count < 1:
            dots_count = 1
        return " " + "." * dots_count + " "

def update_svg_file(svg_path: Path, stats: Dict[str, Any]) -> bool:
    """Updates the SVG file with the provided statistics.
    
    Returns True if successfully updated, False if no changes or error occurred.
    """
    if not svg_path.exists():
        logger.error(f"SVG file not found at: {svg_path}")
        return False
        
    try:
        # Parse XML tree
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Helper to find elements recursively by id
        def find_element_by_id(element: ET.Element, target_id: str) -> ET.Element:
            for elem in element.iter():
                if elem.get("id") == target_id:
                    return elem
            return None

        # Build formatted values dictionary
        # Format numbers with commas
        formatted_vals = {
            "repo_data": f"{stats['repository_count']:,}",
            "contrib_data": f"{stats['contrib_data']:,}",
            "star_data": f"{stats['total_stars']:,}",
            "commit_data": f"{stats['total_commits']:,}",
            "follower_data": f"{stats['followers']:,}",
            "loc_data": f"{stats['loc_data']:,}",
            "loc_add": f"+{stats['loc_add']:,}",
            "loc_del": f"{stats['loc_del']:,}"
        }
        
        # Calculate dots content dynamically
        dots_vals = {
            "repo_data_dots": get_padding_content(
                "repo_data_dots", 
                len(formatted_vals["repo_data"]) + len(formatted_vals["contrib_data"])
            ),
            "star_data_dots": get_padding_content("star_data_dots", len(formatted_vals["star_data"])),
            "commit_data_dots": get_padding_content("commit_data_dots", len(formatted_vals["commit_data"])),
            "follower_data_dots": get_padding_content("follower_data_dots", len(formatted_vals["follower_data"])),
            "loc_data_dots": get_padding_content("loc_data_dots", len(formatted_vals["loc_data"])),
            "loc_del_dots": get_padding_content(
                "loc_del_dots", 
                len(formatted_vals["loc_add"]) + len(formatted_vals["loc_del"])
            )
        }
        
        # Combine all updates
        all_updates = {**formatted_vals, **dots_vals}
        
        # Apply updates to XML elements
        changed = False
        for tspan_id, val in all_updates.items():
            elem = find_element_by_id(root, tspan_id)
            if elem is None:
                logger.warning(f"Required tspan element with ID '{tspan_id}' not found in SVG.")
                continue
            if elem.text != val:
                elem.text = val
                changed = True

        if not changed:
            logger.info("SVG is already up to date. No changes made.")
            return False

        # Write the tree back to the SVG file
        tree.write(svg_path, encoding="utf-8", xml_declaration=True)
        logger.info(f"Successfully updated SVG at {svg_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update SVG file: {e}", exc_info=True)
        return False
