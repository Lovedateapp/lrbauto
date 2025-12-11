import whisper
import os
import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

logger = logging.getLogger("LRBAuto")

class SubtitleGenerator:
    def __init__(self, model_name="base"): # Using base model for free/fast inference
        logger.info(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)

    def generate_subtitles(self, video_path):
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

    def burn_subtitles(self, video_path, subtitle_path):
        """
        Burns subtitles into video using ffmpeg directly.
        Returns the path to the new video file or None on failure.
        """
        import subprocess
        
        try:
            output_path = video_path.rsplit('.', 1)[0] + "_subtitled.mp4"
            logger.info(f"Burning subtitles: {video_path} + {subtitle_path} -> {output_path}")
            
            # Use absolute paths to avoid FFmpeg confusion
            abs_video_path = os.path.abspath(video_path)
            abs_sub_path = os.path.abspath(subtitle_path)
            abs_output_path = os.path.abspath(output_path)
            
            # Escape path for FFmpeg filter:
            # 1. Escape backslashes first (for Windows paths or weird chars)
            # 2. Escape colons (filter separator)
            # 3. Escape single quotes (we wrap path in single quotes)
            filter_path = abs_sub_path.replace('\\', '/').replace(':', '\\:').replace("'", "'\\''")
            
            cmd = [
                'ffmpeg', '-y',
                '-i', abs_video_path,
                '-vf', f"subtitles='{filter_path}'",
                '-c:a', 'copy',
                abs_output_path
            ]
            
            logger.info(f"Running ffmpeg command: {cmd}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if os.path.exists(abs_output_path) and os.path.getsize(abs_output_path) > 0:
                logger.info(f"Successfully burned subtitles: {abs_output_path}")
                return abs_output_path
            else:
                logger.error("FFmpeg ran but output file is missing or empty")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Error burning subtitles: {e}")
            return None
