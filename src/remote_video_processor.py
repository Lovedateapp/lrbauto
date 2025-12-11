import os
import logging
import requests
import json
import shutil
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Optional

logger = logging.getLogger("LRBAuto")

class RemoteVideoProcessor:
    """
    Process videos from a remote web server (directory listing).
    scrapes for folders containing video.mp4 and metadata.json.
    """
    
    def __init__(self, base_url: str = "https://chat.ainewskit.com/vdos/"):
        self.base_url = base_url if base_url.endswith('/') else base_url + '/'
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        logger.info(f"Remote video processor initialized: {self.base_url}")
        
    def get_remote_items(self) -> List[Dict]:
        """
        List items (files and directories) from the remote base URL.
        Returns a list of dicts: {'name': str, 'type': 'file'|'dir', 'url': str}
        """
        try:
            logger.info(f"Fetching directory listing from {self.base_url}")
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = []
            
            for a in soup.find_all('a'):
                href = a.get('href')
                if not href:
                    continue
                
                # Skip parent directory links
                if href in ['../', './', '/'] or href.startswith('?'):
                    continue
                    
                name = href.rstrip('/')
                # Handle full URLs if present
                if name.startswith('http'):
                     if name.startswith(self.base_url):
                         name = name[len(self.base_url):]
                         href_suffix = href[len(self.base_url):]
                     else:
                         continue # External link
                else:
                    href_suffix = href

                full_url = urljoin(self.base_url, href)
                
                # Determine type
                if href.endswith('/'):
                    items.append({'name': name, 'type': 'dir', 'url': full_url})
                elif href.lower().endswith('.mp4'):
                    # It's a direct video file
                    # Decode URL encoding for the name (e.g. %20 -> space)
                    from urllib.parse import unquote
                    decoded_name = unquote(name)
                    if decoded_name.lower().endswith('.mp4'):
                        decoded_name = decoded_name[:-4]
                    items.append({'name': decoded_name, 'type': 'file', 'url': full_url})
            
            # Sort to ensure deterministic order
            items.sort(key=lambda x: x['name'])
            logger.info(f"Found {len(items)} remote items")
            return items
            
        except Exception as e:
            logger.error(f"Failed to list remote items: {e}")
            return []

    def get_unprocessed_videos(self, processed_ids: List[str], limit: int = 1) -> List[Dict]:
        """
        Get list of unprocessed videos, downloading them locally on demand.
        Handles both direct MP4 files and folders. Generates metadata if missing.
        """
        items = self.get_remote_items()
        unprocessed = []
        count = 0
        
        for item in items:
            if count >= limit:
                break
            
            # Use item name as the ID
            unique_id = item['name']
            if unique_id in processed_ids:
                logger.debug(f"Skipping processed: {unique_id}")
                continue
                
            logger.info(f"Process candidate: {unique_id} ({item['type']})")
            
            # Setup local paths
            safe_name = "".join([c for c in unique_id if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            local_folder = os.path.join(self.download_dir, safe_name)
            
            # Clean up previous failed attempts
            if os.path.exists(local_folder):
                shutil.rmtree(local_folder)
            os.makedirs(local_folder, exist_ok=True)
            
            local_video_path = os.path.join(local_folder, 'video.mp4')
            local_metadata_path = os.path.join(local_folder, 'metadata.json')
            
            try:
                # Logic depends on whether it's a file or folder
                video_download_url = ""
                metadata = {}
                
                if item['type'] == 'file':
                    # Case A: Direct MP4 file
                    video_download_url = item['url']
                    
                    # Generate metadata from filename
                    metadata = {
                        "id": unique_id,
                        "title": unique_id,
                        "description": f"{unique_id} - Video shared from {self.base_url}",
                        "url": self.base_url,
                        "tags": ["video", "auto-upload"]
                    }
                    
                    # We still construct a metadata.json locally for consistency
                    with open(local_metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                        
                elif item['type'] == 'dir':
                    # Case B: Folder
                    folder_url = item['url']
                    metadata_url = urljoin(folder_url, 'metadata.json')
                    # We need to find the video file inside the folder if it's not named video.mp4
                    # For simplicity, let's assume video.mp4 OR try to find one.
                    # To minimize requests, we'll just try video.mp4 first, or maybe scan the folder?
                    # Scanning the folder is safer if we don't know the filename.
                    
                    sub_items = self._scan_folder(folder_url)
                    video_file_url = next((i['url'] for i in sub_items if i['url'].lower().endswith('.mp4')), None)
                    
                    if not video_file_url:
                        logger.warning(f"No MP4 found in folder {unique_id}, skipping.")
                        shutil.rmtree(local_folder)
                        continue
                        
                    video_download_url = video_file_url
                    
                    # Try to get metadata, if fail, generate it
                    try:
                        if self.download_file(metadata_url, local_metadata_path):
                            with open(local_metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        else:
                            raise FileNotFoundError("No metadata.json")
                    except Exception:
                        logger.info(f"No metadata found for {unique_id}, generating from folder name.")
                        metadata = {
                            "id": unique_id,
                            "title": unique_id,
                            "description": f"{unique_id}",
                            "url": folder_url,
                            "tags": ["video"]
                        }
                        with open(local_metadata_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)

                # Download Video
                logger.info(f"Downloading video for {unique_id}...")
                if not self.download_file(video_download_url, local_video_path):
                    logger.warning(f"Failed to download video for {unique_id}, skipping.")
                    shutil.rmtree(local_folder)
                    continue
                    
                unprocessed.append({
                    'folder_name': unique_id, # This effectively becomes the ID in history.json
                    'folder_path': local_folder,
                    'video_path': local_video_path,
                    'metadata': metadata
                })
                count += 1
                
            except Exception as e:
                logger.error(f"Processing failed for {unique_id}: {e}")
                shutil.rmtree(local_folder)
                continue
                
        return unprocessed

    def _scan_folder(self, folder_url: str) -> List[Dict]:
        """Helper to scan a sub-folder for items"""
        # Reuse get_remote_items logic but for a specific URL
        # We can create a temporary instance or just duplicate logic. 
        # For cleanliness, let's just do a quick fetch here
        try:
            response = requests.get(folder_url, timeout=10)
            if response.status_code != 200: return []
            soup = BeautifulSoup(response.text, 'html.parser')
            items = []
            for a in soup.find_all('a'):
                href = a.get('href')
                if not href or href in ['../','./','/']: continue
                full_url = urljoin(folder_url, href)
                items.append({'url': full_url, 'name': href})
            return items
        except:
            return []
