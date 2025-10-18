"""
Video and Audio Processing Service
Handles FFmpeg operations for video assembly and audio mixing
Manages multi-segment concatenation for longer videos
"""

import asyncio
import base64
import logging
import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoAudioService:
    """Service for video and audio processing using FFmpeg"""

    def __init__(self):
        self.ffmpeg_path = "ffmpeg"  # Assumes ffmpeg is in PATH
        self.ffprobe_path = "ffprobe"

    async def extract_last_frame(self, video_base64: str) -> str:
        """
        Extract the last frame from a video as base64 image

        This is critical for multi-segment videos to ensure continuity.
        The last frame of segment N becomes the first frame of segment N+1.

        Args:
            video_base64: Base64 encoded video

        Returns:
            Base64 encoded JPEG image of the last frame
        """
        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="extract_frame_")
            video_path = os.path.join(temp_dir, "input.mp4")
            frame_path = os.path.join(temp_dir, "last_frame.jpg")

            # Save video to temp file
            video_bytes = base64.b64decode(video_base64)
            with open(video_path, 'wb') as f:
                f.write(video_bytes)

            # Extract last frame using FFmpeg
            # -sseof -1 seeks to 1 second before end
            # -update 1 overwrites the output file
            # -q:v 2 sets JPEG quality (2 = high quality)
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-sseof", "-0.1",  # Seek to 0.1 seconds before end
                "-update", "1",
                "-frames:v", "1",
                "-q:v", "2",
                frame_path
            ]

            logger.info(f"Extracting last frame with: {' '.join(cmd)}")

            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg frame extraction failed: {stderr.decode()}")
                raise Exception(f"Frame extraction failed: {stderr.decode()}")

            # Read and encode frame
            with open(frame_path, 'rb') as f:
                frame_bytes = f.read()

            frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
            logger.info(f"✅ Extracted last frame: {len(frame_base64)} chars")

            return frame_base64

        finally:
            # Cleanup temp files
            if temp_dir and os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                except:
                    pass

    async def concatenate_videos(self, video_segments_base64: List[str]) -> str:
        """
        Concatenate multiple video segments into one video

        This is the core function for assembling multi-segment videos.
        Uses FFmpeg concat demuxer for lossless concatenation.

        Args:
            video_segments_base64: List of base64 encoded video segments

        Returns:
            Base64 encoded concatenated video
        """
        if not video_segments_base64:
            raise ValueError("No video segments provided")

        if len(video_segments_base64) == 1:
            # Single segment, return as-is
            return video_segments_base64[0]

        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="concat_videos_")

            # Save all segments to temp files
            segment_paths = []
            for i, segment_base64 in enumerate(video_segments_base64):
                segment_path = os.path.join(temp_dir, f"segment_{i:03d}.mp4")
                segment_bytes = base64.b64decode(segment_base64)
                with open(segment_path, 'wb') as f:
                    f.write(segment_bytes)
                segment_paths.append(segment_path)
                logger.info(f"Saved segment {i} to {segment_path}")

            # Create concat list file
            concat_file = os.path.join(temp_dir, "concat_list.txt")
            with open(concat_file, 'w') as f:
                for path in segment_paths:
                    # Use relative paths in concat file
                    f.write(f"file '{os.path.basename(path)}'\n")

            # Output path
            output_path = os.path.join(temp_dir, "output.mp4")

            # FFmpeg concatenation command
            # -safe 0: Allow any file paths
            # -f concat: Use concat demuxer
            # -c copy: Copy streams without re-encoding (fast & lossless)
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",  # Copy without re-encoding
                "-movflags", "+faststart",  # Optimize for web streaming
                output_path
            ]

            logger.info(f"Concatenating {len(segment_paths)} segments with: {' '.join(cmd)}")

            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=temp_dir,  # Run in temp dir for relative paths
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg concatenation failed: {stderr.decode()}")
                raise Exception(f"Video concatenation failed: {stderr.decode()}")

            # Read output video
            with open(output_path, 'rb') as f:
                output_bytes = f.read()

            output_base64 = base64.b64encode(output_bytes).decode('utf-8')
            logger.info(f"✅ Concatenated {len(segment_paths)} segments: {len(output_base64)} chars")

            return output_base64

        finally:
            # Cleanup temp files
            if temp_dir and os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                except:
                    pass

    async def add_audio_to_video(self,
                                video_base64: str,
                                audio_base64: str,
                                fade_duration: float = 2.0) -> str:
        """
        Add audio track to video with optional fade out

        Args:
            video_base64: Base64 encoded video
            audio_base64: Base64 encoded audio
            fade_duration: Fade out duration in seconds

        Returns:
            Base64 encoded video with audio
        """
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="add_audio_")

            # Save input files
            video_path = os.path.join(temp_dir, "video.mp4")
            audio_path = os.path.join(temp_dir, "audio.mp3")
            output_path = os.path.join(temp_dir, "output.mp4")

            video_bytes = base64.b64decode(video_base64)
            with open(video_path, 'wb') as f:
                f.write(video_bytes)

            audio_bytes = base64.b64decode(audio_base64)
            with open(audio_path, 'wb') as f:
                f.write(audio_bytes)

            # Get video duration for audio fade
            duration_cmd = [
                self.ffprobe_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]

            process = await asyncio.create_subprocess_exec(
                *duration_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            video_duration = float(stdout.decode().strip())

            # Add audio with fade out
            # -shortest: End output when shortest input ends
            # -af: Audio filter for fade out
            fade_start = max(0, video_duration - fade_duration)
            audio_filter = f"afade=t=out:st={fade_start}:d={fade_duration}"

            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",  # Copy video stream
                "-c:a", "aac",  # Encode audio as AAC
                "-b:a", "192k",  # Audio bitrate
                "-af", audio_filter,
                "-shortest",  # End when video ends
                "-movflags", "+faststart",
                output_path
            ]

            logger.info(f"Adding audio with fade: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg audio mixing failed: {stderr.decode()}")
                raise Exception(f"Audio mixing failed: {stderr.decode()}")

            # Read output
            with open(output_path, 'rb') as f:
                output_bytes = f.read()

            return base64.b64encode(output_bytes).decode('utf-8')

        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                except:
                    pass

    async def get_video_info(self, video_base64: str) -> Dict[str, Any]:
        """
        Get video metadata using ffprobe

        Args:
            video_base64: Base64 encoded video

        Returns:
            Dictionary with video metadata
        """
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="video_info_")
            video_path = os.path.join(temp_dir, "video.mp4")

            video_bytes = base64.b64decode(video_base64)
            with open(video_path, 'wb') as f:
                f.write(video_bytes)

            # Get video info with ffprobe
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"ffprobe failed: {stderr.decode()}")

            import json
            info = json.loads(stdout.decode())

            # Extract relevant info
            video_stream = next((s for s in info.get("streams", [])
                               if s.get("codec_type") == "video"), None)

            if video_stream:
                return {
                    "duration": float(info.get("format", {}).get("duration", 0)),
                    "width": video_stream.get("width"),
                    "height": video_stream.get("height"),
                    "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                    "codec": video_stream.get("codec_name"),
                    "bitrate": int(info.get("format", {}).get("bit_rate", 0)),
                    "size": int(info.get("format", {}).get("size", 0))
                }

            return {}

        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                except:
                    pass


# Global instance for use in application
video_audio_service = VideoAudioService()