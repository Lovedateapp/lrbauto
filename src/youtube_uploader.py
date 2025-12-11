import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import logging

logger = logging.getLogger("LRBAuto")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeUploader:
    def __init__(self, client_secrets, refresh_token):
        """
        Initializes the uploader with client secrets and a refresh token.
        client_secrets: Dict containing the client_secrets.json content.
        refresh_token: The refresh token string.
        """
        self.credentials = self._get_credentials(client_secrets, refresh_token)
        self.youtube = googleapiclient.discovery.build("youtube", "v3", credentials=self.credentials)

    def _get_credentials(self, client_secrets, refresh_token):
        try:
            # Construct credentials object directly from the provided refresh token and client config
            # Determine the key for client secrets (installed vs web)
            if "installed" in client_secrets:
                cs = client_secrets["installed"]
            elif "web" in client_secrets:
                cs = client_secrets["web"]
            else:
                cs = client_secrets # Fallback if keys are top-level

            creds = Credentials.from_authorized_user_info(
                info={
                    "refresh_token": refresh_token,
                    "client_id": cs["client_id"],
                    "client_secret": cs["client_secret"],
                },
                scopes=SCOPES
            )
            
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
            return creds
        except Exception as e:
            logger.error(f"Error authenticating with YouTube: {e}")
            raise

def create_bilingual_title(self, chinese_title: str, english_title: str) -> str:
        """
        Create a bilingual title in format: Chinese | English
        
        Args:
            chinese_title: Original Chinese title
            english_title: Translated English title
            
        Returns:
            Bilingual title string
        """
        bilingual = f"{chinese_title} | {english_title}"
        # YouTube title limit is 100 characters
        if len(bilingual) > 100:
            # Truncate English part if too long
            max_english_len = 100 - len(chinese_title) - 3  # 3 for " | "
            if max_english_len > 10:
                english_title = english_title[:max_english_len-3] + "..."
                bilingual = f"{chinese_title} | {english_title}"
            else:
                # If Chinese title is too long, just use it
                bilingual = chinese_title[:100]
        
        return bilingual
    
    def create_bilingual_description(self, chinese_title: str, english_title: str,
                                    chinese_desc: str, english_desc: str,
                                    original_url: str = "") -> str:
        """
        Create a bilingual description with both Chinese and English.
        
        Args:
            chinese_title: Original Chinese title
            english_title: Translated English title
            chinese_desc: Original Chinese description
            english_desc: Translated English description
            original_url: URL to original video
            
        Returns:
            Bilingual description string
        """
        description_parts = [
            f"原标题: {chinese_title}",
            f"Original Title: {english_title}",
            "",
            chinese_desc,
            "",
            english_desc,
        ]
        
        if original_url:
            description_parts.extend([
                "",
                f"Original video: {original_url}"
            ])
        
        description = "\n".join(description_parts)
        
        # YouTube description limit is 5000 characters
        if len(description) > 5000:
            description = description[:4997] + "..."
        
        return description
    
    def generate_tags(self, chinese_title: str, english_title: str, 
                     chinese_tags: list = None) -> list:
        """
        Generate tags from titles and optional Chinese tags.
        
        Args:
            chinese_title: Original Chinese title
            english_title: Translated English title
            chinese_tags: Optional list of Chinese tags
            
        Returns:
            List of tags
        """
        tags = []
        
        # Add words from English title (split and filter)
        english_words = [w.strip().lower() for w in english_title.split() 
                        if len(w.strip()) > 2]
        tags.extend(english_words[:5])  # Limit to 5 words from title
        
        # Add Chinese tags if provided
        if chinese_tags:
            tags.extend(chinese_tags[:5])  # Limit to 5 Chinese tags
        
        # Add default tags
        tags.extend(["china", "chinese", "中国"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        
        # YouTube allows max 500 characters total for tags
        # Limit to ~30 tags to be safe
        return unique_tags[:30]
    
    def upload_video(self, file_path, title, description, category_id="22", 
                    privacy_status="private", tags=None):
        """
        Uploads a video to YouTube.
        
        Args:
            file_path: Path to video file
            title: Video title (can be bilingual)
            description: Video description (can be bilingual)
            category_id: YouTube category ID (default: 22 = People & Blogs)
            privacy_status: Privacy status (default: private)
            tags: Optional list of tags
        """
        try:
            # Use provided tags or default
            if tags is None:
                tags = ["xiaohongshu", "automation", "china", "chinese"]
            
            body = {
                "snippet": {
                    "title": title[:100], # YouTube title limit
                    "description": description[:5000], # YouTube desc limit
                    "tags": tags,
                    "categoryId": category_id
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                }
            }

            logger.info(f"Uploading {file_path} to YouTube...")
            
            # MediaFileUpload handles the file upload
            media_body = googleapiclient.http.MediaFileUpload(
                file_path, 
                chunksize=-1, 
                resumable=True,
                mimetype="video/mp4"
            )

            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media_body
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.progress() * 100)}%")

            logger.info(f"Upload complete! Video ID: {response['id']}")
            return response['id']

        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            return None
