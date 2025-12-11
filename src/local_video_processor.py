import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from src.metadata_handler import MetadataHandler

logger = logging.getLogger("LRBAuto")


class LocalVideoProcessor:
    """
    Process locally downloaded videos from a specified folder.
    Scans for video folders containing video.mp4 and metadata.json.
    """
    
    def __init__(self, videos_dir: str = "/Volumes/myminihdd/xhsvdo"):
        """
        Initialize the local video processor.
        
        Args:
            videos_dir: Directory containing video folders (default: external HDD)
        """
        self.videos_dir = videos_dir
        os.makedirs(self.videos_dir, exist_ok=True)
        logger.info(f"Local video processor initialized: {self.videos_dir}")
    
    def find_video_folders(self) -> List[str]:
        """
        Find all folders in videos_dir that contain video.mp4 and metadata.json.
        
        Returns:
            List of folder paths
        """
        video_folders = []
        
        if not os.path.exists(self.videos_dir):
            logger.warning(f"Videos directory does not exist: {self.videos_dir}")
            return video_folders
        
        # Scan all subdirectories
        for item in os.listdir(self.videos_dir):
            folder_path = os.path.join(self.videos_dir, item)
            
            if not os.path.isdir(folder_path):
                continue
            
            # Check if folder contains required files
            video_path, metadata_path = MetadataHandler.validate_video_folder(folder_path)
            
            if video_path and metadata_path:
                video_folders.append(folder_path)
                logger.info(f"Found valid video folder: {item}")
            else:
                logger.debug(f"Skipping invalid folder: {item}")
        
        return sorted(video_folders)
    
    def get_unprocessed_videos(self, processed_ids: List[str]) -> List[Dict]:
        """
        Get list of unprocessed videos with their metadata.
        
        Args:
            processed_ids: List of already processed folder names
            
        Returns:
            List of dictionaries with video info:
            {
                'folder_name': str,
                'folder_path': str,
                'video_path': str,
                'metadata': dict
            }
        """
        video_folders = self.find_video_folders()
        unprocessed = []
        
        for folder_path in video_folders:
            folder_name = os.path.basename(folder_path)
            
            # Skip if already processed
            if folder_name in processed_ids:
                logger.debug(f"Skipping processed video: {folder_name}")
                continue
            
            # Load metadata
            video_path, metadata_path = MetadataHandler.validate_video_folder(folder_path)
            
            try:
                metadata = MetadataHandler.load_metadata(metadata_path)
                
                unprocessed.append({
                    'folder_name': folder_name,
                    'folder_path': folder_path,
                    'video_path': video_path,
                    'metadata': metadata
                })
                
                logger.info(f"Found unprocessed video: {folder_name} - {metadata['title']}")
                
            except ValueError as e:
                logger.error(f"Invalid metadata in {folder_name}: {e}")
                continue
        
        return unprocessed
    
    def get_video_id(self, video_info: Dict) -> str:
        """
        Get unique ID for a video (folder name).
        
        Args:
            video_info: Video info dictionary
            
        Returns:
            Unique ID string
        """
        return video_info['folder_name']
    
    def create_sample_folder(self, folder_name: str = "sample_video"):
        """
        Create a sample video folder with template metadata.json.
        
        Args:
            folder_name: Name of sample folder to create
        """
        sample_path = os.path.join(self.videos_dir, folder_name)
        os.makedirs(sample_path, exist_ok=True)
        
        # Create template metadata
        metadata_path = os.path.join(sample_path, "metadata.json")
        MetadataHandler.create_template(metadata_path)
        
        # Create placeholder for video
        readme_path = os.path.join(sample_path, "README.txt")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("Place your downloaded video.mp4 file here\n")
            f.write("Edit metadata.json with the video's Chinese title and description\n")
        
        logger.info(f"Created sample folder: {sample_path}")
        return sample_path
