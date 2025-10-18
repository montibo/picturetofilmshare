#!/usr/bin/env python3
"""
Add Audio to Video with Professional Quality
Handles audio mixing, fade effects, and quality preservation
Optimized for social media platforms
"""

import os
import sys
import argparse
import subprocess
import tempfile
from pathlib import Path

# FFmpeg configuration
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

# Quality presets
QUALITY_PRESETS = {
    "instagram": {
        "video_codec": "libx264",
        "crf": 18,
        "preset": "medium",
        "video_bitrate": "10M",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
        "description": "Optimized for Instagram (4.2MB for 10s)"
    },
    "preserve": {
        "video_codec": "copy",
        "audio_codec": "aac",
        "audio_bitrate": "256k",
        "description": "Preserve original video quality (6.3MB for 10s)"
    },
    "high": {
        "video_codec": "libx264",
        "crf": 15,
        "preset": "slow",
        "video_bitrate": "15M",
        "audio_codec": "aac",
        "audio_bitrate": "320k",
        "description": "High quality for professional use"
    },
    "web": {
        "video_codec": "libx264",
        "crf": 23,
        "preset": "fast",
        "video_bitrate": "5M",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "description": "Optimized for web streaming"
    }
}


def get_video_duration(video_path: str) -> float:
    """
    Get video duration in seconds

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds
    """
    cmd = [
        FFPROBE,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        print("⚠️ Could not determine video duration, using default 10s")
        return 10.0


def process_audio(
    audio_path: str,
    video_duration: float,
    audio_start: float,
    fade_duration: float,
    temp_dir: str
) -> str:
    """
    Process audio: trim, fade, and prepare for mixing

    Args:
        audio_path: Input audio file path
        video_duration: Duration of video in seconds
        audio_start: Start time in audio (seconds)
        fade_duration: Fade out duration (seconds)
        temp_dir: Directory for temporary files

    Returns:
        Path to processed audio file
    """
    output_path = os.path.join(temp_dir, "processed_audio.m4a")

    # Calculate fade start time
    fade_start = max(0, video_duration - fade_duration)

    # Build audio filter
    audio_filters = []

    # Trim audio to video duration
    audio_filters.append(f"atrim=start={audio_start}:duration={video_duration}")

    # Add fade out
    if fade_duration > 0:
        audio_filters.append(f"afade=t=out:st={fade_start}:d={fade_duration}")

    # Normalize audio
    audio_filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

    filter_string = ",".join(audio_filters)

    cmd = [
        FFMPEG,
        "-i", audio_path,
        "-af", filter_string,
        "-c:a", "aac",
        "-b:a", "192k",
        "-y", output_path
    ]

    print(f"🎵 Processing audio (start: {audio_start}s, fade: {fade_duration}s)...")
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def add_audio_to_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    audio_start: float = 0,
    quality_preset: str = "instagram",
    fade_duration: float = 2.0,
    volume: float = 1.0
) -> bool:
    """
    Add audio track to video with professional quality

    Args:
        video_path: Input video file path
        audio_path: Input audio file path
        output_path: Output video file path
        audio_start: Start time in audio (seconds)
        quality_preset: Quality preset name
        fade_duration: Fade out duration (seconds)
        volume: Audio volume multiplier (1.0 = normal)

    Returns:
        True if successful, False otherwise
    """
    temp_dir = tempfile.mkdtemp(prefix="audio_mix_")

    try:
        # Get video duration
        video_duration = get_video_duration(video_path)
        print(f"📹 Video duration: {video_duration:.1f}s")

        # Get quality settings
        preset = QUALITY_PRESETS.get(quality_preset, QUALITY_PRESETS["instagram"])
        print(f"🎨 Quality preset: {quality_preset} - {preset['description']}")

        # Process audio
        processed_audio = process_audio(
            audio_path,
            video_duration,
            audio_start,
            fade_duration,
            temp_dir
        )

        # Build FFmpeg command
        cmd = [FFMPEG, "-i", video_path, "-i", processed_audio]

        # Video codec settings
        if preset["video_codec"] == "copy":
            cmd.extend(["-c:v", "copy"])
        else:
            cmd.extend(["-c:v", preset["video_codec"]])
            if "crf" in preset:
                cmd.extend(["-crf", str(preset["crf"])])
            if "preset" in preset:
                cmd.extend(["-preset", preset["preset"]])
            if "video_bitrate" in preset:
                cmd.extend(["-b:v", preset["video_bitrate"]])

        # Audio codec settings
        cmd.extend([
            "-c:a", preset["audio_codec"],
            "-b:a", preset.get("audio_bitrate", "192k")
        ])

        # Volume adjustment
        if volume != 1.0:
            cmd.extend(["-af", f"volume={volume}"])

        # Additional flags
        cmd.extend([
            "-map", "0:v:0",  # Use first video stream
            "-map", "1:a:0",  # Use processed audio
            "-shortest",  # End when shortest input ends
            "-movflags", "+faststart",  # Optimize for streaming
            "-y", output_path
        ])

        print("🎬 Mixing audio with video...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False

        # Get file size
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Output video created: {output_path}")
        print(f"📊 File size: {file_size_mb:.1f} MB")
        print(f"⏱️ Duration: {video_duration:.1f}s")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

    finally:
        # Cleanup temp files
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Add audio to video with professional quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality presets:
  instagram  - Optimized for Instagram (default)
  preserve   - Preserve original video quality
  high       - High quality for professional use
  web        - Optimized for web streaming

Examples:
  %(prog)s video.mp4 audio.mp3 output.mp4
  %(prog)s video.mp4 audio.mp3 output.mp4 --audio-start 9
  %(prog)s video.mp4 audio.mp3 output.mp4 --quality preserve
  %(prog)s video.mp4 audio.mp3 output.mp4 --fade 3 --volume 0.8
        """
    )

    parser.add_argument("video", help="Input video file")
    parser.add_argument("audio", help="Input audio file")
    parser.add_argument("output", help="Output video file")

    parser.add_argument(
        "--audio-start", "-s",
        type=float,
        default=0,
        help="Start time in audio (seconds, default: 0)"
    )

    parser.add_argument(
        "--quality", "-q",
        choices=list(QUALITY_PRESETS.keys()),
        default="instagram",
        help="Quality preset (default: instagram)"
    )

    parser.add_argument(
        "--fade", "-f",
        type=float,
        default=2.0,
        help="Fade out duration in seconds (default: 2.0)"
    )

    parser.add_argument(
        "--volume", "-v",
        type=float,
        default=1.0,
        help="Audio volume multiplier (default: 1.0)"
    )

    parser.add_argument(
        "--preserve-quality", "-p",
        action="store_true",
        help="Shortcut for --quality preserve"
    )

    args = parser.parse_args()

    # Check input files exist
    if not os.path.exists(args.video):
        print(f"❌ Video file not found: {args.video}")
        sys.exit(1)

    if not os.path.exists(args.audio):
        print(f"❌ Audio file not found: {args.audio}")
        sys.exit(1)

    # Override quality if preserve flag is set
    quality = "preserve" if args.preserve_quality else args.quality

    # Process video
    success = add_audio_to_video(
        video_path=args.video,
        audio_path=args.audio,
        output_path=args.output,
        audio_start=args.audio_start,
        quality_preset=quality,
        fade_duration=args.fade,
        volume=args.volume
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()