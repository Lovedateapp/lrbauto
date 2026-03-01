import os
import logging
import requests
import json
import shutil
import hashlib
import re
import subprocess
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from typing import List, Dict, Optional

logger = logging.getLogger("LRBAuto")

class RemoteVideoProcessor:
    """
    Process videos from a remote web server (directory listing).
    Supports:
    1) Direct MP4 files
    2) Folders containing MP4 files
    3) Same-name MP3 + image pairs that are converted to MP4
    """

    SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    
    def __init__(self, base_url: str = "https://chat.ainewskit.com/vdos/"):
        self.base_url = base_url if base_url.endswith('/') else base_url + '/'
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        logger.info(f"Remote video processor initialized: {self.base_url}")
        
    def get_remote_items(self) -> List[Dict]:
        """
        List items (files and directories) from the remote base URL.
        Returns a list of dicts:
        - dir: {'name': str, 'type': 'dir', 'url': str}
        - file: {'name': str, 'stem': str, 'ext': str, 'type': 'file', 'url': str}
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

                full_url = urljoin(self.base_url, href)
                decoded_name = self._decode_name_from_href(href)

                if href.endswith('/'):
                    items.append({'name': decoded_name, 'type': 'dir', 'url': full_url})
                    continue

                stem, ext = os.path.splitext(decoded_name)
                if not ext:
                    continue
                items.append({
                    'name': decoded_name,
                    'stem': stem,
                    'ext': ext.lower(),
                    'type': 'file',
                    'url': full_url
                })

            # Sort to ensure deterministic order
            items.sort(key=lambda x: x['name'])
            logger.info(f"Found {len(items)} remote items")
            return items
            
        except Exception as e:
            logger.error(f"Failed to list remote items: {e}")
            return []

    def _decode_name_from_href(self, href: str) -> str:
        parsed = urlparse(href)
        path = parsed.path if parsed.path else href
        name = os.path.basename(path.rstrip('/'))
        return unquote(name)

    def _normalize_key(self, value: str) -> str:
        return re.sub(r'\s+', ' ', value.strip().lower())

    def _canonical_id(self, value: str) -> str:
        """
        Canonical form for duplicate matching across different separators/cases.
        """
        return re.sub(r'[\W_]+', '', value.strip().lower(), flags=re.UNICODE)

    def _is_birthday_song(self, title: str) -> bool:
        title_text = title.lower()
        birthday_markers = ["happy birthday", "birthday", "生日", "生日快乐", "祝你生日快乐"]
        return any(marker in title_text for marker in birthday_markers)

    def _safe_folder_name(self, name: str) -> str:
        safe = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        if safe:
            return safe
        return f"item_{hashlib.md5(name.encode('utf-8')).hexdigest()[:12]}"

    def _pretty_title(self, raw_name: str) -> str:
        title = raw_name.replace('_', ' ').replace('-', ' ')
        title = re.sub(r'\s+', ' ', title).strip()
        return title or raw_name

    def _build_song_pair_items(self, items: List[Dict]) -> List[Dict]:
        mp3_by_key: Dict[str, Dict] = {}
        image_by_key: Dict[str, Dict] = {}

        for item in items:
            if item.get('type') != 'file':
                continue

            ext = item.get('ext', '').lower()
            stem = item.get('stem', '')
            key = self._normalize_key(stem)
            if not key:
                continue

            if ext == '.mp3':
                mp3_by_key[key] = item
            elif ext in self.SUPPORTED_IMAGE_EXTS and key not in image_by_key:
                image_by_key[key] = item

        pairs = []
        for key, audio_item in mp3_by_key.items():
            image_item = image_by_key.get(key)
            if not image_item:
                continue

            pairs.append({
                'name': audio_item['stem'],
                'type': 'song',
                'audio_url': audio_item['url'],
                'audio_name': audio_item['name'],
                'image_url': image_item['url'],
                'image_name': image_item['name']
            })

        pairs.sort(key=lambda x: x['name'])
        if pairs:
            logger.info(f"Found {len(pairs)} MP3+image pair(s)")
        return pairs

    def _create_video_from_song_assets(self, image_path: str, audio_path: str, output_path: str) -> bool:
        """
        Create an MP4 video from a still image and an MP3 audio track.
        """
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-movflags', '+faststart',
            output_path
        ]

        try:
            logger.info(f"Building MP4 from assets: {audio_path} + {image_path}")
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return os.path.exists(output_path) and os.path.getsize(output_path) > 0
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed while creating song video: {e.stderr[-1200:]}")
            return False
        except Exception as e:
            logger.error(f"Failed to create song video: {e}")
            return False

    def get_unprocessed_videos(self, processed_ids: List[str], limit: int = 1) -> List[Dict]:
        """
        Get list of unprocessed videos, downloading them locally on demand.
        Handles:
        - MP3+image song assets (builds a local MP4)
        - Direct MP4 files
        - Folder-style remote videos
        """
        items = self.get_remote_items()
        song_items = self._build_song_pair_items(items)
        direct_mp4_items = [
            {
                'name': item['stem'],
                'type': 'file',
                'url': item['url']
            }
            for item in items
            if item.get('type') == 'file' and item.get('ext') == '.mp4'
        ]
        folder_items = [item for item in items if item.get('type') == 'dir']
        candidates = sorted(song_items + direct_mp4_items + folder_items, key=lambda x: x['name'])
        processed_keys = {self._canonical_id(pid) for pid in processed_ids if pid}

        unprocessed = []
        count = 0

        for item in candidates:
            if count >= limit:
                break

            # Use item name as the ID
            unique_id = item['name']
            if unique_id in processed_ids or self._canonical_id(unique_id) in processed_keys:
                logger.debug(f"Skipping processed: {unique_id}")
                continue
                
            logger.info(f"Process candidate: {unique_id} ({item['type']})")

            # Setup local paths
            safe_name = self._safe_folder_name(unique_id)
            local_folder = os.path.join(self.download_dir, safe_name)

            # For remote MP4/folder sources, clean old attempts first.
            # For song assets, keep existing build cache so we can reuse video.mp4.
            if item['type'] in ('file', 'dir') and os.path.exists(local_folder):
                shutil.rmtree(local_folder)
            os.makedirs(local_folder, exist_ok=True)
            
            local_video_path = os.path.join(local_folder, 'video.mp4')
            local_metadata_path = os.path.join(local_folder, 'metadata.json')
            
            try:
                # Logic depends on whether it's a file or folder
                video_download_url = ""
                metadata = {}

                if item['type'] == 'song':
                    # Case A: MP3 + image files with same basename
                    audio_url = item['audio_url']
                    image_url = item['image_url']
                    image_ext = os.path.splitext(urlparse(image_url).path)[1] or '.png'
                    local_audio_path = os.path.join(local_folder, 'audio.mp3')
                    local_image_path = os.path.join(local_folder, f'cover{image_ext.lower()}')

                    # Reuse previously built song video if available.
                    if os.path.isfile(local_video_path) and os.path.getsize(local_video_path) > 0:
                        if os.path.isfile(local_metadata_path):
                            try:
                                with open(local_metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                            except Exception:
                                metadata = {}
                        if not metadata:
                            display_title = self._pretty_title(unique_id)
                            metadata = {
                                "id": unique_id,
                                "title": display_title,
                                "description": (
                                    f"{display_title} is a sweet and happy children's song. "
                                    "Great for sing-along time at home, preschool, and kindergarten."
                                ),
                                "url": audio_url,
                                "tags": (
                                    [
                                        "children songs",
                                        "kids songs",
                                        "happy birthday songs",
                                        "birthday songs",
                                        "nursery rhyme",
                                        "happy song",
                                        "sweet song",
                                        "sing along"
                                    ] if self._is_birthday_song(display_title) else [
                                        "children songs",
                                        "kids songs",
                                        "nursery rhyme",
                                        "happy song",
                                        "sweet song",
                                        "sing along",
                                        f"{display_title} song"
                                    ]
                                ),
                                "content_type": "song",
                                "source_audio": item['audio_name'],
                                "source_image": item['image_name']
                            }
                        logger.info(f"Reusing prebuilt song video for {unique_id}")
                        unprocessed.append({
                            'folder_name': unique_id,
                            'folder_path': local_folder,
                            'video_path': local_video_path,
                            'metadata': metadata
                        })
                        count += 1
                        continue

                    if not self.download_file(audio_url, local_audio_path):
                        logger.warning(f"Failed to download audio for {unique_id}, skipping.")
                        shutil.rmtree(local_folder)
                        continue
                    if not self.download_file(image_url, local_image_path):
                        logger.warning(f"Failed to download image for {unique_id}, skipping.")
                        shutil.rmtree(local_folder)
                        continue
                    if not self._create_video_from_song_assets(local_image_path, local_audio_path, local_video_path):
                        logger.warning(f"Failed to build video for {unique_id}, skipping.")
                        shutil.rmtree(local_folder)
                        continue

                    display_title = self._pretty_title(unique_id)
                    metadata = {
                        "id": unique_id,
                        "title": display_title,
                        "description": (
                            f"{display_title} is a sweet and happy children's song. "
                            "Great for sing-along time at home, preschool, and kindergarten."
                        ),
                        "url": audio_url,
                        "tags": (
                            [
                                "children songs",
                                "kids songs",
                                "happy birthday songs",
                                "birthday songs",
                                "nursery rhyme",
                                "happy song",
                                "sweet song",
                                "sing along"
                            ] if self._is_birthday_song(display_title) else [
                                "children songs",
                                "kids songs",
                                "nursery rhyme",
                                "happy song",
                                "sweet song",
                                "sing along",
                                f"{display_title} song"
                            ]
                        ),
                        "content_type": "song",
                        "source_audio": item['audio_name'],
                        "source_image": item['image_name']
                    }
                    with open(local_metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                elif item['type'] == 'file':
                    # Case A: Direct MP4 file
                    video_download_url = item['url']

                    # Generate metadata from filename
                    metadata = {
                        "id": unique_id,
                        "title": unique_id,
                        "description": f"{unique_id}",
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

                # Download Video when needed (song assets already created local_video_path)
                if item['type'] in ('file', 'dir'):
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
        try:
            response = requests.get(folder_url, timeout=10)
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.text, 'html.parser')
            items = []
            for a in soup.find_all('a'):
                href = a.get('href')
                if not href or href in ['../', './', '/']:
                    continue
                full_url = urljoin(folder_url, href)
                items.append({'url': full_url, 'name': self._decode_name_from_href(href)})
            return items
        except Exception:
            return []

    def download_file(self, url: str, local_path: str) -> bool:
        """Download a file from a URL to a local path"""
        try:
            logger.info(f"Downloading {url} to {local_path}")
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return True
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
