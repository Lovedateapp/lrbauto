import yt_dlp
import os
import logging
import json
from src.utils import clean_filename

logger = logging.getLogger("LRBAuto")

class BilibiliDownloader:
    def __init__(self, user_id):
        """
        Initialize Bilibili downloader for a specific user.
        
        Args:
            user_id (str): Bilibili user ID (UID)
        """
        self.user_id = user_id
        self.user_url = f"https://space.bilibili.com/{user_id}"
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)
    
    def get_latest_videos(self, limit=10):
        """
        Fetches the latest video IDs from the user's space.
        
        Args:
            limit (int): Maximum number of videos to fetch
            
        Returns:
            list: List of video info dicts with 'id', 'title', 'url'
        """
        try:
            logger.info(f"Fetching latest {limit} videos from Bilibili user {self.user_id}")
            
            # Add realistic browser headers to avoid anti-bot detection
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Only extract metadata, don't download
                'playlistend': limit,  # Limit number of videos
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Referer': 'https://www.bilibili.com/',
                },
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.user_url, download=False)
                
                if not info or 'entries' not in info:
                    logger.warning("No videos found for this user")
                    return []
                
                videos = []
                for entry in info['entries'][:limit]:
                    if entry:
                        video_info = {
                            'id': entry.get('id', ''),
                            'title': entry.get('title', 'Untitled'),
                            'url': entry.get('url', '') or f"https://www.bilibili.com/video/{entry.get('id', '')}",
                            'description': entry.get('description', ''),
                        }
                        videos.append(video_info)
                        logger.info(f"Found video: {video_info['id']} - {video_info['title']}")
                
                return videos
                
        except Exception as e:
            logger.error(f"Error fetching videos: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def download_video(self, video_id, video_title="video"):
        """
        Downloads a single video from Bilibili.
        
        Args:
            video_id (str): Bilibili video ID (BV ID)
            video_title (str): Video title for filename
            
        Returns:
            str: Path to downloaded video file, or None if failed
        """
        try:
            video_url = f"https://www.bilibili.com/video/{video_id}"
            logger.info(f"Downloading video: {video_id} - {video_title}")
            
            # Clean filename
            safe_title = clean_filename(video_title)
            output_template = os.path.join(self.download_dir, f"{video_id}_{safe_title}.%(ext)s")
            
            # Add realistic browser headers to avoid anti-bot detection
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'merge_output_format': 'mp4',  # Ensure output is mp4
                'max_filesize': 500 * 1024 * 1024,  # 500MB limit
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Referer': 'https://www.bilibili.com/',
                },
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
                # Get the actual downloaded filename
                downloaded_file = ydl.prepare_filename(info)
                
                if os.path.exists(downloaded_file):
                    logger.info(f"Successfully downloaded: {downloaded_file}")
                    return downloaded_file
                else:
                    logger.error(f"Download completed but file not found: {downloaded_file}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading video {video_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def get_video_info(self, video_id):
        """
        Gets detailed information about a video without downloading.
        
        Args:
            video_id (str): Bilibili video ID (BV ID)
            
        Returns:
            dict: Video information including title, description, etc.
        """
        try:
            video_url = f"https://www.bilibili.com/video/{video_id}"
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                return {
                    'id': info.get('id', video_id),
                    'title': info.get('title', 'Untitled'),
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', ''),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                }
                
        except Exception as e:
            logger.error(f"Error getting video info for {video_id}: {e}")
            return {
                'id': video_id,
                'title': 'Unknown',
                'description': '',
            }
