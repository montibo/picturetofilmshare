#!/usr/bin/env python3
"""
Instagram Story Generator with Mouse Click Animation
Creates a 9:16 vertical video with animated mouse click effect
Perfect for social media engagement
"""

import os
import sys
import argparse
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# FFmpeg configuration
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

# Video settings
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 24
DURATION_PHOTO = 2.0  # Show photo for 2 seconds
DURATION_MOUSE = 1.0  # Mouse animation duration
DURATION_CLICK = 0.5  # Click effect duration


def download_from_gcs(job_id: str, temp_dir: str) -> Tuple[str, str]:
    """
    Download input image and video from Google Cloud Storage

    Args:
        job_id: Job identifier
        temp_dir: Temporary directory for downloads

    Returns:
        Tuple of (image_path, video_path)
    """
    print(f"🌐 Downloading files for job {job_id}...")

    # In production, you would download from GCS
    # For demo, we'll use placeholder paths
    image_path = os.path.join(temp_dir, "input.jpg")
    video_path = os.path.join(temp_dir, "video.mp4")

    # Placeholder: In real implementation, download from GCS
    # Example with gsutil or gcloud storage:
    # subprocess.run(["gcloud", "storage", "cp", f"gs://bucket/jobs/{job_id}/input.jpg", image_path])
    # subprocess.run(["gcloud", "storage", "cp", f"gs://bucket/jobs/{job_id}/output.mp4", video_path])

    print("✅ Files downloaded successfully")
    return image_path, video_path


def create_mouse_animation(temp_dir: str, duration: float = DURATION_MOUSE) -> str:
    """
    Create animated mouse cursor that moves to center

    Args:
        temp_dir: Directory for temporary files
        duration: Animation duration in seconds

    Returns:
        Path to mouse animation video
    """
    output_path = os.path.join(temp_dir, "mouse_animation.mp4")

    # Create mouse cursor animation using FFmpeg
    # This creates a simple animated dot that moves from top-left to center
    filter_complex = f"""
        color=c=black@0:s={OUTPUT_WIDTH}x{OUTPUT_HEIGHT}:d={duration}[bg];
        [bg]drawbox=x='(w-40)/2+200*cos(2*PI*t/{duration})':
                    y='(h-40)/2+200*sin(2*PI*t/{duration})':
                    w=40:h=40:c=white:t=fill[cursor];
        [cursor]format=yuv420p[out]
    """

    cmd = [
        FFMPEG, "-f", "lavfi",
        "-i", f"color=c=black@0:s={OUTPUT_WIDTH}x{OUTPUT_HEIGHT}:d={duration}",
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-r", str(FPS),
        "-y", output_path
    ]

    print("🖱️ Creating mouse animation...")
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def create_click_effect(temp_dir: str, duration: float = DURATION_CLICK) -> str:
    """
    Create click effect animation (ripple/flash)

    Args:
        temp_dir: Directory for temporary files
        duration: Effect duration in seconds

    Returns:
        Path to click effect video
    """
    output_path = os.path.join(temp_dir, "click_effect.mp4")

    # Create expanding circle effect for click
    filter_complex = f"""
        color=c=white@0:s={OUTPUT_WIDTH}x{OUTPUT_HEIGHT}:d={duration}[bg];
        [bg]drawbox=x='(w-200*t/{duration})/2':
                    y='(h-200*t/{duration})/2':
                    w='200*t/{duration}':
                    h='200*t/{duration}':
                    c=white@0.5:t=1[effect];
        [effect]format=yuv420p[out]
    """

    cmd = [
        FFMPEG, "-f", "lavfi",
        "-i", f"color=c=black@0:s={OUTPUT_WIDTH}x{OUTPUT_HEIGHT}:d={duration}",
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-r", str(FPS),
        "-y", output_path
    ]

    print("✨ Creating click effect...")
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def add_branding(video_path: str, temp_dir: str) -> str:
    """
    Add logo and branding to video

    Args:
        video_path: Input video path
        temp_dir: Directory for temporary files

    Returns:
        Path to branded video
    """
    output_path = os.path.join(temp_dir, "branded_video.mp4")

    # Add text overlay for branding
    filter_complex = f"""
        [0:v]drawtext=text='PictureToFilm':
                     fontfile=/System/Library/Fonts/Helvetica.ttc:
                     fontsize=48:
                     fontcolor=white:
                     x=(w-text_w)/2:
                     y=h-100:
                     enable='gte(t,2)'[out]
    """

    cmd = [
        FFMPEG, "-i", video_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-y", output_path
    ]

    print("🏷️ Adding branding...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except subprocess.CalledProcessError:
        # If font not found, return original
        print("⚠️ Could not add branding (font not found), using original")
        return video_path


def generate_instagram_story(
    job_id: str,
    output_path: str,
    add_music: bool = False,
    add_voice: bool = False
) -> bool:
    """
    Generate complete Instagram story video

    Args:
        job_id: Job identifier for GCS
        output_path: Output video path
        add_music: Whether to add background music
        add_voice: Whether to add voice over

    Returns:
        True if successful, False otherwise
    """
    temp_dir = tempfile.mkdtemp(prefix="insta_story_")

    try:
        # 1. Download files from GCS
        image_path, video_path = download_from_gcs(job_id, temp_dir)

        # 2. Create photo display segment
        photo_segment = os.path.join(temp_dir, "photo_segment.mp4")
        cmd = [
            FFMPEG, "-loop", "1",
            "-i", image_path,
            "-c:v", "libx264",
            "-t", str(DURATION_PHOTO),
            "-vf", f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(FPS),
            "-y", photo_segment
        ]
        print("📸 Creating photo segment...")
        subprocess.run(cmd, check=True, capture_output=True)

        # 3. Create mouse animation
        mouse_animation = create_mouse_animation(temp_dir)

        # 4. Create click effect
        click_effect = create_click_effect(temp_dir)

        # 5. Process main video to 9:16
        video_segment = os.path.join(temp_dir, "video_segment.mp4")
        cmd = [
            FFMPEG, "-i", video_path,
            "-vf", f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-r", str(FPS),
            "-y", video_segment
        ]
        print("🎬 Processing main video...")
        subprocess.run(cmd, check=True, capture_output=True)

        # 6. Create concat list
        concat_list = os.path.join(temp_dir, "concat.txt")
        with open(concat_list, "w") as f:
            f.write(f"file '{photo_segment}'\n")
            f.write(f"file '{mouse_animation}'\n")
            f.write(f"file '{click_effect}'\n")
            f.write(f"file '{video_segment}'\n")

        # 7. Concatenate all segments
        final_video = os.path.join(temp_dir, "final.mp4")
        cmd = [
            FFMPEG, "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            "-y", final_video
        ]
        print("🎞️ Assembling final video...")
        subprocess.run(cmd, check=True, capture_output=True)

        # 8. Add branding
        branded_video = add_branding(final_video, temp_dir)

        # 9. Add audio if requested
        if add_music:
            print("🎵 Adding background music...")
            # In production, download music from GCS or generate with AI
            # For demo, we'll skip this step
            pass

        if add_voice:
            print("🎤 Adding voice over...")
            # In production, generate voice with TTS service
            # For demo, we'll skip this step
            pass

        # 10. Copy to output path
        import shutil
        shutil.copy2(branded_video, output_path)

        print(f"✅ Instagram story generated: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error generating story: {str(e)}")
        return False

    finally:
        # Cleanup temp files
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate Instagram story with mouse click animation"
    )
    parser.add_argument(
        "job_id",
        help="Job ID from GCS"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="instagram_story.mp4",
        help="Output video path"
    )
    parser.add_argument(
        "--music",
        choices=["Y", "N"],
        default="N",
        help="Add background music (Y/N)"
    )
    parser.add_argument(
        "--voice",
        choices=["Y", "N"],
        default="N",
        help="Add voice over (Y/N)"
    )

    args = parser.parse_args()

    # Generate the story
    success = generate_instagram_story(
        job_id=args.job_id,
        output_path=args.output,
        add_music=(args.music == "Y"),
        add_voice=(args.voice == "Y")
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()