"""
Prompt Engineering Service
Constructs optimized prompts for AI video generation
Handles templates, styles, and context analysis
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptService:
    """Service for building AI video generation prompts"""

    def __init__(self):
        # Define available animation templates
        self.templates = {
            "none": {
                "name": "Natural Animation",
                "description": "Natural, flowing movement",
                "sequences": ["gentle natural movement"]
            },
            "magic_sparkle": {
                "name": "Magic & Sparkles",
                "description": "Magical animation with sparkles",
                "sequences": ["magical sparkles appearing", "flowing enchantment"]
            },
            "floating": {
                "name": "Floating Elements",
                "description": "Elements floating and drifting",
                "sequences": ["gentle floating motion", "weightless drifting"]
            },
            "celebration": {
                "name": "Celebration",
                "description": "Festive, celebratory animation",
                "sequences": ["joyful celebration", "festive energy"]
            },
            "peaceful": {
                "name": "Peaceful Flow",
                "description": "Calm, peaceful movement",
                "sequences": ["peaceful flowing motion", "tranquil movement"]
            }
        }

        # Define visual styles
        self.styles = {
            "none": {
                "name": "Original",
                "prompt": "maintain original style"
            },
            "cinematic": {
                "name": "Cinematic",
                "prompt": "cinematic quality with depth of field"
            },
            "dreamy": {
                "name": "Dreamy",
                "prompt": "soft, dreamy atmosphere"
            },
            "vibrant": {
                "name": "Vibrant",
                "prompt": "vibrant colors and high contrast"
            },
            "vintage": {
                "name": "Vintage",
                "prompt": "vintage film aesthetic"
            }
        }

    async def build_video_prompt_async(self,
                                      sequence_number: int,
                                      template: str,
                                      style: str,
                                      context: Dict[str, Any],
                                      face_count: int = 0,
                                      character_description: str = "",
                                      analysis: Dict[str, Any] = None,
                                      country: str = "en",
                                      total_duration: int = 30,
                                      total_segments: int = 1) -> str:
        """
        Build video generation prompt asynchronously

        This is the core prompt that instructs the AI on how to animate the image.
        The prompt is deliberately simple and universal to ensure consistent results.

        Args:
            sequence_number: Current segment number (for multi-segment videos)
            template: Animation template to use
            style: Visual style to apply
            context: Scene context from analysis
            face_count: Number of faces detected
            character_description: Description of people in image
            analysis: Image analysis results
            country: User's country/language
            total_duration: Total video duration
            total_segments: Total number of segments

        Returns:
            Optimized prompt string for Replicate API
        """

        # IMPORTANT: This is the actual prompt sent to Replicate
        # After extensive testing, this simple prompt produces the best results
        # It focuses on natural animation without adding new elements

        base_prompt = (
            "Animate all elements in motion, "
            "flowing animation, "
            "all elements moving with life, "
            "fluid movements, "
            "natural movement, "
            "keep character the same, "
            "keep letters, "
            "keep character present and face"
        )

        # For production, you might want to add template/style modifiers
        # But the simple prompt above works best for most cases

        return base_prompt

    def build_video_prompt(self,
                          sequence_number: int,
                          template: str,
                          style: str,
                          context: Dict[str, Any],
                          face_count: int = 0,
                          character_description: str = "",
                          analysis: Dict[str, Any] = None,
                          country: str = "en") -> str:
        """
        Build video generation prompt (synchronous version)

        See build_video_prompt_async for details.
        """
        return (
            "Animate all elements in motion, "
            "flowing animation, "
            "all elements moving with life, "
            "fluid movements, "
            "natural movement, "
            "keep character the same, "
            "keep letters, "
            "keep character present and face"
        )

    def analyze_image_context(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract context from image analysis

        Args:
            analysis: Image analysis results from Vision API

        Returns:
            Structured context dictionary
        """
        context = {
            "scene": "unknown",
            "objects": [],
            "faces": 0,
            "lighting": "natural",
            "mood": "neutral",
            "colors": [],
            "era": "contemporary"
        }

        if not analysis:
            return context

        # Extract scene type
        if "labels" in analysis:
            labels = [label.get("description", "").lower() for label in analysis["labels"]]

            # Determine scene type
            if any(word in labels for word in ["beach", "ocean", "sea", "coast"]):
                context["scene"] = "beach"
            elif any(word in labels for word in ["forest", "tree", "woods", "nature"]):
                context["scene"] = "forest"
            elif any(word in labels for word in ["city", "building", "street", "urban"]):
                context["scene"] = "urban"
            elif any(word in labels for word in ["family", "group", "people"]):
                context["scene"] = "portrait"

            # Extract key objects
            context["objects"] = labels[:5]

        # Extract faces information
        if "faces" in analysis:
            context["faces"] = len(analysis["faces"])

        # Determine lighting
        if "properties" in analysis:
            dominant_colors = analysis["properties"].get("dominantColors", {}).get("colors", [])
            if dominant_colors:
                avg_brightness = sum(
                    (c.get("color", {}).get("red", 0) +
                     c.get("color", {}).get("green", 0) +
                     c.get("color", {}).get("blue", 0)) / 3
                    for c in dominant_colors[:3]
                ) / min(3, len(dominant_colors))

                if avg_brightness > 200:
                    context["lighting"] = "bright"
                elif avg_brightness < 100:
                    context["lighting"] = "dark"
                else:
                    context["lighting"] = "balanced"

                context["colors"] = dominant_colors[:3]

        return context

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a specific template"""
        return self.templates.get(template_name, self.templates["none"])

    def get_style_info(self, style_name: str) -> Dict[str, Any]:
        """Get information about a specific style"""
        return self.styles.get(style_name, self.styles["none"])

    def list_templates(self) -> List[str]:
        """List all available templates"""
        return list(self.templates.keys())

    def list_styles(self) -> List[str]:
        """List all available styles"""
        return list(self.styles.keys())


# Global instance for use in application
prompt_service = PromptService()