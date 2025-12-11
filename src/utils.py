import json
import os
import logging
import difflib
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LRBAuto")

HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                # Ensure new structure exists
                if "processed_metadata" not in history:
                    history["processed_metadata"] = {}
                return history
        except json.JSONDecodeError:
            logger.warning(f"{HISTORY_FILE} is corrupted. Starting fresh.")
    return {"downloaded_ids": [], "processed_metadata": {}}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def is_video_downloaded(video_id, history):
    return video_id in history.get("downloaded_ids", [])

def mark_video_downloaded(video_id: str, history: Dict, metadata: Optional[Dict] = None):
    """
    Mark a video as downloaded/processed and save its metadata.
    """
    if "downloaded_ids" not in history:
        history["downloaded_ids"] = []
    
    if video_id not in history["downloaded_ids"]:
        history["downloaded_ids"].append(video_id)
    
    # Save metadata if provided
    if metadata:
        if "processed_metadata" not in history:
            history["processed_metadata"] = {}
        
        # Store simplified metadata to save space, focused on what we need for deduplication
        history["processed_metadata"][video_id] = {
            "title": metadata.get("title", ""),
            "url": metadata.get("url", "")
        }
        
    save_history(history)

def clean_filename(title):
    keepcharacters = (' ','.','_')
    return "".join(c for c in title if c.isalnum() or c in keepcharacters).rstrip()

def calculate_similarity(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings (0.0 to 1.0)."""
    if not s1 or not s2:
        return 0.0
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def check_similarity(new_title: str, history: Dict, threshold: float = 0.8) -> Tuple[bool, Optional[Dict]]:
    """
    Check if the new title is similar to any previously processed video title.
    
    Returns:
        Tuple(bool, dict): (is_similar, matching_video_info)
    """
    if not new_title:
        return False, None
        
    processed_metadata = history.get("processed_metadata", {})
    
    for video_id, meta in processed_metadata.items():
        existing_title = meta.get("title", "")
        if not existing_title:
            continue
            
        similarity = calculate_similarity(new_title, existing_title)
        if similarity >= threshold:
            logger.info(f"Similarity detected: '{new_title}' vs '{existing_title}' score={similarity:.2f}")
            return True, {
                "id": video_id,
                "title": existing_title,
                "similarity": similarity
            }
            
    return False, None
