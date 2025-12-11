import os
import json
import logging
from src.utils import load_history, mark_video_downloaded, is_video_downloaded, check_similarity
from src.local_video_processor import LocalVideoProcessor
from src.remote_video_processor import RemoteVideoProcessor
from src.subtitle_gen import SubtitleGenerator
from src.youtube_uploader import YouTubeUploader
from deep_translator import GoogleTranslator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LRBAuto")

# Constants
DOWNLOAD_LIMIT_PER_RUN = 1  # Process 1 video per run

def main():
    # Load configuration from environment variables
    youtube_client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    youtube_refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    remote_video_url = os.environ.get("REMOTE_VIDEO_URL", "https://chat.ainewskit.com/vdos/") # Default to user provided URL

    if not all([youtube_client_secret, youtube_refresh_token]):
        logger.error("Missing environment variables. Please check YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN.")
        return

    try:
        youtube_client_secrets_json = json.loads(youtube_client_secret)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in YOUTUBE_CLIENT_SECRET")
        return

    # Initialize components
    history = load_history()
    
    # Choose processor
    if remote_video_url:
        logger.info(f"Using RemoteVideoProcessor with URL: {remote_video_url}")
        processor = RemoteVideoProcessor(base_url=remote_video_url)
    else:
        logger.info("Using LocalVideoProcessor")
        processor = LocalVideoProcessor(videos_dir="/Volumes/myminihdd/xhsvdo")

    subtitle_gen = SubtitleGenerator(model_name="small")
    uploader = YouTubeUploader(youtube_client_secrets_json, youtube_refresh_token)
    translator = GoogleTranslator(source='zh-CN', target='en')

    # 1. Check for new videos
    logger.info("Checking for new videos...")
    
    # Get list of already processed folder names
    processed_ids = history.get("downloaded_ids", [])
    
    # Find unprocessed videos (Remote processor handles downloading logic internally)
    unprocessed_videos = processor.get_unprocessed_videos(processed_ids, limit=DOWNLOAD_LIMIT_PER_RUN)
    
    if not unprocessed_videos:
        logger.info("No new videos to process.")
        return
    
    logger.info(f"Found {len(unprocessed_videos)} unprocessed video(s)")
    
    videos_processed = 0
    
    for video_info in unprocessed_videos:
        if videos_processed >= DOWNLOAD_LIMIT_PER_RUN:
            break
        
        folder_name = video_info['folder_name']
        video_path = video_info['video_path']
        metadata = video_info['metadata']
        
        chinese_title = metadata['title']
        chinese_desc = metadata['description']
        original_url = metadata.get('url', '')
        chinese_tags = metadata.get('tags', [])
        
        logger.info(f"Processing candidate: {chinese_title}")
        
        # --- Similarity Check ---
        is_similar, match_info = check_similarity(chinese_title, history)
        if is_similar:
            logger.warning(
                f"Skipping video '{chinese_title}' (ID: {folder_name}) - "
                f"It is {match_info['similarity']*100:.1f}% similar to processed video "
                f"'{match_info['title']}' (ID: {match_info['id']})"
            )
            
            # Mark it as processed so we don't try to download it again
            # We don't save its metadata as a reference to keep the reference pool clean? 
            # Actually, saving it helps prevent processing duplicates of duplicates.
            mark_video_downloaded(folder_name, history, metadata)
            
            # Clean up local files if remote
            if remote_video_url:
                import shutil
                if os.path.exists(video_info['folder_path']):
                    shutil.rmtree(video_info['folder_path'])
                    logger.info(f"Cleaned up skipped video files: {video_info['folder_path']}")
            
            continue
        # ------------------------
        
        logger.info(f"Processing video: {chinese_title}")
        
        try:
            # 2. Generate subtitles
            logger.info("Generating subtitles...")
            subtitle_path = subtitle_gen.generate_subtitles(video_path)
            if not subtitle_path:
                logger.error("Subtitle generation failed. Skipping.")
                continue
            
            # 3. Burn subtitles into video
            logger.info("Burning subtitles into video...")
            subtitled_video_path = subtitle_gen.burn_subtitles(video_path, subtitle_path)
            if not subtitled_video_path:
                logger.error("Burning subtitles failed. Skipping.")
                continue
            
            # 4. Translate title and description
            logger.info("Translating title and description...")
            try:
                english_title = translator.translate(chinese_title)
                english_desc = translator.translate(chinese_desc)
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                # Use fallback
                english_title = "Chinese Video"
                english_desc = "Video from China"
            
            # 5. Create bilingual content
            bilingual_title = uploader.create_bilingual_title(chinese_title, english_title)
            bilingual_desc = uploader.create_bilingual_description(
                chinese_title, english_title,
                chinese_desc, english_desc,
                original_url
            )
            tags = uploader.generate_tags(chinese_title, english_title, chinese_tags)
            
            logger.info(f"Bilingual title: {bilingual_title}")
            logger.info(f"Generated {len(tags)} tags")
            
            # 6. Upload to YouTube
            logger.info("Uploading to YouTube...")
            video_id = uploader.upload_video(
                subtitled_video_path,
                title=bilingual_title,
                description=bilingual_desc,
                tags=tags,
                privacy_status="private"  # Change to "public" when ready
            )
            
            if video_id:
                logger.info(f"Successfully uploaded! YouTube video ID: {video_id}")
                
                # 7. Mark as processed
                mark_video_downloaded(folder_name, history, metadata)
                videos_processed += 1
                
                # Clean up downloads if remote
                if remote_video_url:
                     import shutil
                     if os.path.exists(video_info['folder_path']):
                         shutil.rmtree(video_info['folder_path'])
                         logger.info(f"Cleaned up {video_info['folder_path']}")

            else:
                logger.error("Upload failed.")
                
        except Exception as e:
            logger.error(f"Error processing video {folder_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    if videos_processed > 0:
        logger.info(f"Successfully processed {videos_processed} video(s)")
    else:
        logger.info("No videos were successfully processed")

if __name__ == "__main__":
    main()
