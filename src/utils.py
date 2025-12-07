import json
import os
import logging

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
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"{HISTORY_FILE} is corrupted. Starting fresh.")
    return {"downloaded_ids": []}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def is_video_downloaded(video_id, history):
    return video_id in history.get("downloaded_ids", [])

def mark_video_downloaded(video_id, history):
    if "downloaded_ids" not in history:
        history["downloaded_ids"] = []
    if video_id not in history["downloaded_ids"]:
        history["downloaded_ids"].append(video_id)
        save_history(history)

def clean_filename(title):
    keepcharacters = (' ','.','_')
    return "".join(c for c in title if c.isalnum() or c in keepcharacters).rstrip()
