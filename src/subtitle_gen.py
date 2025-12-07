import whisper
import os
import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

logger = logging.getLogger("LRBAuto")

class SubtitleGenerator:
    def __init__(self, model_name="base"): # Using base model for free/fast inference
        logger.info(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)

    def generate_subtitle_file(self, video_path):
        """
        Generates English subtitles for the given video.
        Returns the path to the SRT file.
        """
        try:
            logger.info(f"Transcribing {video_path}...")
            result = self.model.transcribe(video_path, task="translate", language="Chinese") # Translate Chinese audio to English text
            
            srt_path = video_path.rsplit('.', 1)[0] + ".srt"
            
            with open(srt_path, "w", encoding="utf-8") as f:
                for i, segment in enumerate(result["segments"]):
                    start = self._format_time(segment["start"])
                    end = self._format_time(segment["end"])
                    text = segment["text"].strip()
                    
                    f.write(f"{i+1}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n\n")
            
            logger.info(f"Generated subtitles: {srt_path}")
            return srt_path
        except Exception as e:
            logger.error(f"Error generating subtitles: {e}")
            return None

    def _format_time(self, seconds):
        """Converts seconds to HH:MM:SS,mmm format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"
