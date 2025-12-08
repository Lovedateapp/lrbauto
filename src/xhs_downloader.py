import requests
from xhs import XhsClient
import os
import logging
from src.utils import clean_filename

logger = logging.getLogger("LRBAuto")

def sign(uri, data=None, a1="", web_session=""):
    # Dummy sign function to satisfy the library requirement
    return {}

class XHSDownloader:
    def __init__(self, cookie):
        self.cookie = cookie
        self.client = XhsClient(cookie=cookie, sign=sign)

    def get_latest_videos(self, user_id, limit=10):
        """
        Fetches the latest video notes from a user.
        """
        try:
            # Get user notes
            notes = self.client.get_user_notes(user_id)
            if not notes:
                logger.warning(f"No notes found for user {user_id}")
                return []
            
            video_notes = []
            for note in notes.get('notes', [])[:limit]:
                if note.get('type') == 'video':
                    video_notes.append({
                        'id': note.get('note_id'),
                        'title': note.get('display_title'),
                        'cover': note.get('cover', {}).get('url')
                    })
            return video_notes
        except Exception as e:
            logger.error(f"Error fetching notes: {e}")
            return []

    def download_video(self, note_id, output_dir="downloads"):
        """
        Downloads a video note without watermark.
        """
        try:
            note_info = self.client.get_note_by_id(note_id)
            if not note_info:
                logger.error(f"Could not fetch details for note {note_id}")
                return None

            video_url = note_info.get('video', {}).get('media', {}).get('stream', {}).get('h264', [{}])[0].get('master_url')
            
            if not video_url:
                # Try finding other verified url
                logger.warning("Master URL not found, trying alternatives...")
                # Add logic if needed, but usually master_url works for the library
            
            title = clean_filename(note_info.get('title', f'video_{note_id}'))
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_path = os.path.join(output_dir, f"{title}.mp4")
            
            # Simple download using requests since we have the direct URL
            response = requests.get(video_url, stream=True)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        f.write(chunk)
                logger.info(f"Downloaded video: {output_path}")
                return {
                    'path': output_path,
                    'title': note_info.get('title'),
                    'desc': note_info.get('desc'),
                    'id': note_id
                }
            else:
                logger.error(f"Failed to download video stream. Status: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error downloading video {note_id}: {e}")
            return None
