import os
import json
import logging
from src.utils import load_history, mark_video_downloaded, is_video_downloaded
from src.xhs_downloader import XHSDownloader
from src.subtitle_gen import SubtitleGenerator
from src.youtube_uploader import YouTubeUploader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LRBAuto")

# Constants
XHS_USER_ID = "665c135f000000000d0277de"
DOWNLOAD_LIMIT_PER_RUN = 1 # Process 1 video per run to stay within limits/time, or loop for more

def main():
    # Load configuration from environment variables
    xhs_cookie = os.environ.get("XHS_COOKIE")
    youtube_client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    youtube_refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([xhs_cookie, youtube_client_secret, youtube_refresh_token]):
        logger.error("Missing environment variables. Please check XHS_COOKIE, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN.")
        return

    try:
        youtube_client_secrets_json = json.loads(youtube_client_secret)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in YOUTUBE_CLIENT_SECRET")
        return

    # Initialize components
    history = load_history()
    downloader = XHSDownloader(cookie=xhs_cookie)
    # Lazy load Whisper only if needed to save startup time? No, might as well load it.
    subtitle_gen = SubtitleGenerator(model_name="small") # Use 'small' for better quality than 'base'
    uploader = YouTubeUploader(youtube_client_secrets_json, youtube_refresh_token)

    # 1. Check for new videos
    logger.info("Checking for new videos...")
    latest_videos = downloader.get_latest_videos(XHS_USER_ID, limit=10) # Fetch more to find un-downloaded ones
    
    videos_processed = 0
    
    for video in latest_videos:
        if videos_processed >= DOWNLOAD_LIMIT_PER_RUN:
            break
            
        video_id = video['id']
        video_title = video['title']

        if is_video_downloaded(video_id, history):
            logger.info(f"Skipping already downloaded video: {video_title} ({video_id})")
            continue

        logger.info(f"Processing new video: {video_title}")

        # 2. Download
        download_result = downloader.download_video(video_id)
        if not download_result:
            logger.error("Download failed. Skipping.")
            continue
        
        video_path = download_result['path']
        
        # 3. Generate Subtitles
        srt_path = subtitle_gen.generate_subtitle_file(video_path)
        if not srt_path:
            logger.error("Subtitle generation failed. Proceeding without subtitles? No, aborting upload.")
            continue # Skip upload if subs fail, or decide to upload anyway
        
        # 4. Upload to YouTube
        # Note: YouTube API allows uploading captions, but for simplicity we might just upload the video first
        # and checking if we can attach the CAPTION. 
        # For now, let's assume we just want to upload the video. 
        # *Self-Correction*: User wants to ADD English subtitle. 
        # To strictly follow "adding an English subtitle", we should use ffmpeg to burn it or upload as caption track.
        # Uploading as caption track requires a separate API call. 
        # For this "MVP", I will stick to just uploading the video content. 
        # WAIT! If I generated an SRT, I should try to upload it. 
        # However, the current `youtube_uploader.py` only has `upload_video`.
        # I will burn the subtitles using moviepy (which uses ffmpeg) to make it a single video file.
        # This is robust for all players.
        
        # Burning subtitles (Override)
        # This is resource heavy but safest for "showing subtitles".
        # Re-encoding...
        # Actually, let's keep it simple for v1: just upload the raw video.
        # If user insisted on "adding", I'll try to implement caption upload in a v2 or if specifically asked.
        # Actually, let's try to update the `upload_video` to include caption? 
        # No, `captions().insert` is a separate call.
        # Let's simple BURNT-IN logic here or just Skip for now and notify user.
        # User said "adding an English subtitle". 
        # I will use `ffmpeg` to create a new video file with hardcoded subtitles.
        # Since I am using `moviepy` in `subtitle_gen.py` imports (though not used logic yet), I can use it.
        # But `moviepy` with `TextClip` requires ImageMagick which is a pain in CI.
        # Better to just use `ffmpeg` directly via `subprocess` if available.
        # GitHub Actions ubuntu-latest has ffmpeg.
        
        logger.info("Burning subtitles into video...")
        output_video_with_subs = video_path.replace(".mp4", "_subbed.mp4")
        # simple ffmpeg command
        # ffmpeg -i input.mp4 -vf "subtitles=subs.srt" output.mp4
        # Need to ensure absolute path for srt in ffmpeg filter often
        import subprocess
        try:
            subprocess.run([
                "ffmpeg", "-i", video_path, 
                "-vf", f"subtitles={os.path.basename(srt_path)}", 
                "-c:a", "copy", 
                output_video_with_subs
            ], check=True, cwd=os.path.dirname(video_path)) # run in dir to find srt easily
            
            upload_file = output_video_with_subs
        except Exception as e:
            logger.error(f"FFmpeg failed: {e}. Uploading original video.")
            upload_file = video_path

        # Translate Title and Description
        from deep_translator import GoogleTranslator
        
        try:
            translator = GoogleTranslator(source='auto', target='en')
            translated_title = translator.translate(video_title)
            translated_desc = translator.translate(download_result['desc'])
            
            final_title = f"{video_title} | {translated_title}"
            final_description = (
                f"{download_result['desc']}\n\n"
                f"--- English Translation ---\n"
                f"{translated_desc}\n\n"
                f"Original: https://www.xiaohongshu.com/explore/{download_result['id']}"
            )
        except Exception as e:
            logger.error(f"Translation failed: {e}. Using original metadata.")
            final_title = f"{video_title} [Eng Sub]"
            final_description = f"{download_result['desc']}\n\nOriginal: https://www.xiaohongshu.com/explore/{download_result['id']}"

        video_id = uploader.upload_video(
            file_path=upload_file,
            title=final_title,
            description=final_description,
            privacy_status="public" 
        )

        if video_id:
            mark_video_downloaded(download_result['id'], history)
            videos_processed += 1
            
    if videos_processed == 0:
        logger.info("No new videos to process.")

if __name__ == "__main__":
    main()
