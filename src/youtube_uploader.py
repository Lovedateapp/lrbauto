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

    def upload_video(self, file_path, title, description, category_id="22", privacy_status="private"):
        """
        Uploads a video to YouTube.
        """
        try:
            body = {
                "snippet": {
                    "title": title[:100], # YouTube title limit
                    "description": description[:5000], # YouTube desc limit
                    "tags": ["xiaohongshu", "automation"],
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
