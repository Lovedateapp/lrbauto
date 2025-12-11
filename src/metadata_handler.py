import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger("LRBAuto")


class MetadataHandler:
    """
    Handle metadata.json files for locally downloaded videos.
    """
    
    REQUIRED_FIELDS = ["title", "description", "url"]
    OPTIONAL_FIELDS = ["author", "tags", "bv_id"]
    
    @staticmethod
    def load_metadata(json_path: str) -> Dict:
        """
        Load and validate metadata from JSON file.
        
        Args:
            json_path: Path to metadata.json file
            
        Returns:
            Dictionary with metadata
            
        Raises:
            ValueError: If metadata is invalid or missing required fields
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Validate required fields
            missing_fields = [field for field in MetadataHandler.REQUIRED_FIELDS 
                            if field not in metadata]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Ensure all required fields are non-empty strings
            for field in MetadataHandler.REQUIRED_FIELDS:
                if not isinstance(metadata[field], str) or not metadata[field].strip():
                    raise ValueError(f"Field '{field}' must be a non-empty string")
            
            # Validate optional fields if present
            if "tags" in metadata and not isinstance(metadata["tags"], list):
                raise ValueError("Field 'tags' must be a list")
            
            logger.info(f"Loaded metadata: {metadata['title']}")
            return metadata
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except FileNotFoundError:
            raise ValueError(f"Metadata file not found: {json_path}")
    
    @staticmethod
    def validate_video_folder(folder_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Validate that a folder contains both video.mp4 and metadata.json.
        
        Args:
            folder_path: Path to video folder
            
        Returns:
            Tuple of (video_path, metadata_path) if valid, (None, None) otherwise
        """
        video_path = os.path.join(folder_path, "video.mp4")
        metadata_path = os.path.join(folder_path, "metadata.json")
        
        if os.path.isfile(video_path) and os.path.isfile(metadata_path):
            return video_path, metadata_path
        
        return None, None
    
    @staticmethod
    def create_template(output_path: str):
        """
        Create a template metadata.json file.
        
        Args:
            output_path: Where to save the template
        """
        template = {
            "title": "视频标题 (Chinese Title)",
            "description": "视频描述 (Chinese Description)",
            "url": "https://www.xiaohongshu.com/explore/xxxxx",
            "author": "作者名 (Optional)",
            "tags": ["标签1", "标签2", "标签3"]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created metadata template: {output_path}")
