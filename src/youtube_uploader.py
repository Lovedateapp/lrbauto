import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import logging
import re

logger = logging.getLogger("LRBAuto")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

import jieba

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
        if not english_title or english_title.strip().lower() == chinese_title.strip().lower():
            bilingual = chinese_title
        else:
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

    def create_song_seo_title(self, chinese_title: str, english_title: str) -> str:
        """
        Build a longer SEO-friendly title for children's songs while
        keeping YouTube's 100-char limit.
        """
        base = self.create_bilingual_title(chinese_title, english_title)
        is_birthday = self._is_birthday_song(chinese_title, english_title)
        if is_birthday:
            extras = [
                "Happy Birthday Songs",
                "Birthday Song for Kids",
                "Sing Along",
                "Nursery Rhymes"
            ]
        else:
            topic = self._extract_topic_phrase(chinese_title, english_title)
            extras = [
                f"{topic} Song",
                "Kids Songs",
                "Sing Along",
                "Nursery Rhymes"
            ]

        parts = [base]
        title_lower = base.lower()
        for extra in extras:
            if extra.lower() in title_lower:
                continue

            candidate = " | ".join(parts + [extra])
            if len(candidate) <= 100:
                parts.append(extra)
            else:
                break

        seo_title = " | ".join(parts)[:100]
        if "#shorts" not in seo_title.lower() and len(seo_title) + len(" #Shorts") <= 100:
            seo_title += " #Shorts"
        return seo_title
    
    def create_bilingual_description(self, chinese_title: str, english_title: str,
                                    chinese_desc: str, english_desc: str,
                                    summary: str = "", tags: list = None) -> str:
        """
        Create a clean bilingual description with summary and tags.
        """
        description_parts = []
        
        # 1. Bilingual Title (clean)
        description_parts.append(f"{chinese_title}")
        if english_title and english_title.strip().lower() != chinese_title.strip().lower():
            description_parts.append(f"{english_title}")
        description_parts.append("")

        # 2. Song context
        description_parts.append(
            "A sweet and happy children's song for toddlers, preschool, and family sing-along time."
        )
        description_parts.append("")

        # 3. Conclusion / Summary
        if summary:
            description_parts.append("★ Lyrics Highlights / 歌词摘要:")
            description_parts.append(summary)
            description_parts.append("")
            
        # 4. Bilingual Description body
        if chinese_desc and chinese_desc != chinese_title:
             description_parts.append(chinese_desc)
             description_parts.append("")
             
        if english_desc and english_desc != english_title:
             description_parts.append(english_desc)
             description_parts.append("")

        # 5. Tags at the bottom
        if tags:
            tag_line = " ".join([f"#{t.replace(' ', '')}" for t in tags[:15]])
            description_parts.append("")
            description_parts.append(tag_line)
        
        description = "\n".join(description_parts)
        
        # YouTube description limit is 5000 characters
        if len(description) > 5000:
            description = description[:4997] + "..."
        
        return description
    
    def generate_tags(self, chinese_title: str, english_title: str, 
                     chinese_tags: list = None) -> list:
        """
        Generate tags ensuring at least 6 relevant tags.
        """
        tags = []
        
        # 1. Extract from Chinese title (using jieba)
        try:
            # Cut title into words
            seg_list = jieba.cut(chinese_title)
            # Filter out short words and non-keywords (heuristically)
            cn_words = [w for w in seg_list if len(w) > 1 and w.strip()]
            tags.extend(cn_words[:5]) # Top 5 Chinese keywords
        except Exception:
            # Fallback if jieba fails
            tags.append(chinese_title[:10]) 

        # 2. Extract from English title
        english_words = [w.strip().lower() for w in english_title.split() 
                        if len(w.strip()) > 3 and w.isalpha()]
        tags.extend(english_words[:5])
        
        # 3. Add provided Chinese tags if any
        if chinese_tags:
            tags.extend(chinese_tags[:8])
            
        # 4. Add default children-song context tags
        defaults = [
            "children songs",
            "kids songs",
            "shorts",
            "youtube shorts",
            "nursery rhyme",
            "happy song",
            "sweet song",
            "sing along",
            "toddler songs",
            "preschool songs",
            "kindergarten songs",
            "儿童歌曲",
            "儿歌",
            "快乐儿歌"
        ]
        if self._is_birthday_song(chinese_title, english_title):
            defaults.extend([
                "happy birthday songs",
                "happy birthday song for kids",
                "birthday songs"
            ])
        else:
            topic = self._extract_topic_phrase(chinese_title, english_title)
            defaults.extend([
                f"{topic} song",
                f"{topic} kids song"
            ])
        tags.extend(defaults)
        
        # 5. Filter duplicates
        seen = set()
        unique_tags = []
        for tag in tags:
            tag_clean = tag.lower().strip()
            # Simple deduplication
            if len(tag_clean) > 1 and tag_clean not in seen:
                seen.add(tag_clean)
                unique_tags.append(tag_clean)
        
        # Ensure we have at least 6 tags
        return unique_tags[:45]
    
    def upload_video(self, file_path, title, description, category_id="10",
                    privacy_status="private", tags=None, made_for_kids=False):
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
                    "selfDeclaredMadeForKids": bool(made_for_kids)
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
    def _is_birthday_song(self, chinese_title: str, english_title: str) -> bool:
        title_text = f"{chinese_title} {english_title}".lower()
        birthday_markers = [
            "happy birthday",
            "birthday",
            "生日",
            "生日快乐",
            "祝你生日快乐"
        ]
        return any(marker in title_text for marker in birthday_markers)

    def _extract_topic_phrase(self, chinese_title: str, english_title: str) -> str:
        """
        Extract a short topic phrase from title for non-birthday SEO keywords.
        """
        candidates = re.findall(r"[A-Za-z]+", english_title or "")
        filtered = [w for w in candidates if len(w) > 2 and w.lower() not in {"song", "kids", "kid"}]
        if filtered:
            return " ".join(filtered[:3]).title()
        return chinese_title.strip() or "Kids"
