"""
Replicate Video Generation Service
Handles AI video generation using Replicate's SeeDance models
Cost: $0.01-0.05 per video segment
"""

import aiohttp
import asyncio
import base64
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class ReplicateVideoClient:
    """Client for AI video generation using Replicate API"""

    def __init__(self):
        # Get API token from environment
        self.api_token = os.getenv('REPLICATE_API_TOKEN')
        self.timeout = 600  # 10 minutes max per segment

        # Default to Pro model for better quality
        self.model_choice = 'seedance-pro'

        # Available models catalog
        self.models = {
            "seedance-lite": {
                "id": "bytedance/seedance-1-lite",
                "name": "SeeDance-1-Lite",
                "cost": 0.01,  # Very economical
                "duration": 10,  # 10s max per segment
                "resolution": "480p",
                "params_key": "seedance"
            },
            "seedance-pro": {
                "id": "bytedance/seedance-1-pro",
                "name": "SeeDance-1-Pro",
                "cost": 0.05,  # Higher quality
                "duration": 10,  # 10s max per segment
                "resolution": "480p",  # Limited to optimize size
                "params_key": "seedance-pro"
            }
        }

    async def generate_from_image(self,
                                 prompt: str,
                                 image_url: str,
                                 duration: int,
                                 aspect_ratio: str,
                                 animation_mode: str = "auto",
                                 use_pro: bool = True) -> Dict[str, Any]:
        """
        Generate video from image using Replicate AI

        Args:
            prompt: Animation description (e.g., "flowing motion, natural movement")
            image_url: Source image URL (can be GCS gs:// URL)
            duration: Desired duration (will be capped at 10s per segment)
            aspect_ratio: Video format (16:9, 9:16, 1:1)
            animation_mode: Animation style
            use_pro: Use Pro model for better quality

        Returns:
            Dict with ok=True/False and result or error
        """

        if not self.api_token:
            return {"ok": False, "error": "REPLICATE_API_TOKEN not configured"}

        try:
            # Prepare image URL (handle GCS signed URLs if needed)
            image_url_final = await self._prepare_image_url(image_url)

            # Select model (Pro for better quality)
            model = self.models["seedance-pro"] if use_pro else self.models["seedance-lite"]
            logger.info(f"Using model: {model['name']} (${model['cost']}/segment)")

            # Create prediction and get result
            result = await self._create_prediction(
                model=model,
                prompt=prompt,
                image_url=image_url_final,
                duration=duration,
                aspect_ratio=aspect_ratio
            )

            return result

        except Exception as e:
            logger.error(f"Replicate generation error: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def _prepare_image_url(self, image_url: str) -> str:
        """
        Prepare image URL for Replicate (handle GCS URLs)
        """
        if image_url.startswith("gs://"):
            # Convert GCS URL to public URL or signed URL
            # In production, you might need to generate signed URLs
            # This is a simplified example
            bucket_name = os.getenv('GCS_BUCKET', 'your-bucket')
            path = image_url.replace(f"gs://{bucket_name}/", "")
            public_url = f"https://storage.googleapis.com/{bucket_name}/{path}"
            logger.info(f"Using GCS public URL: {public_url[:100]}...")
            return public_url

        # For HTTP/HTTPS URLs, use as-is
        return image_url

    async def _create_prediction(self,
                                model: Dict,
                                prompt: str,
                                image_url: str,
                                duration: int = 10,
                                aspect_ratio: str = "16:9") -> Dict[str, Any]:
        """Create and poll Replicate prediction"""

        import replicate

        # Configure API token
        replicate.api_token = self.api_token

        # Build input parameters based on model type
        params_key = model.get("params_key", "default")

        # Determine resolution based on aspect ratio
        if aspect_ratio == "9:16":
            width, height = 480, 854  # Portrait
        else:
            width, height = 854, 480  # Landscape (default)

        # Build input for Replicate API
        input_data = {
            "image": image_url,
            "prompt": prompt,
            "width": width,
            "height": height,
            "fps": 24,
            "duration": min(duration, 10),  # Cap at 10s per segment
            "camera_fixed": False
        }

        if params_key == "seedance-pro":
            input_data["resolution"] = "480p"  # Explicit resolution for Pro

        logger.info(f"Creating prediction with model: {model['name']}")
        logger.info(f"Input parameters: {input_data}")

        try:
            # Create prediction
            loop = asyncio.get_event_loop()
            prediction = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: replicate.predictions.create(
                        version=model["id"],
                        input=input_data
                    )
                ),
                timeout=30  # 30s timeout for creation
            )

            logger.info(f"Prediction created: {prediction.id}")

            # Poll for completion
            TIMEOUT_SECONDS = 720  # 12 minutes max
            start_time = asyncio.get_event_loop().time()
            poll_interval = 15  # Check every 15 seconds

            while asyncio.get_event_loop().time() - start_time < TIMEOUT_SECONDS:
                await asyncio.sleep(poll_interval)

                # Refresh prediction status
                prediction.reload()

                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info(f"Status: {prediction.status} after {elapsed:.0f}s")

                if prediction.status == "succeeded":
                    logger.info(f"✅ Prediction succeeded after {elapsed:.1f}s")
                    break
                elif prediction.status == "failed":
                    error = getattr(prediction, 'error', 'Unknown error')
                    logger.error(f"❌ Prediction failed: {error}")
                    raise Exception(f"Replicate failed: {error}")
            else:
                # Timeout reached
                raise Exception(f"Timeout after {TIMEOUT_SECONDS}s")

            # Get output video URL
            output = prediction.output

            # Convert output to string URL
            if hasattr(output, '__class__') and output.__class__.__name__ == 'FileOutput':
                video_url = str(output)
            elif isinstance(output, str):
                video_url = output
            elif isinstance(output, list) and len(output) > 0:
                video_url = output[0]
            else:
                raise Exception("No video URL in output")

            logger.info(f"Video generated: {video_url[:80]}...")

            # Download video and convert to base64
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status == 200:
                        video_bytes = await response.read()
                        video_base64 = base64.b64encode(video_bytes).decode('utf-8')

                        return {
                            "ok": True,
                            "result": {
                                "video_base64": video_base64,
                                "video_url": video_url,
                                "metadata": {
                                    "duration": model["duration"],
                                    "resolution": model.get("resolution", "480p"),
                                    "model": model["name"],
                                    "cost_estimate": model["cost"]
                                }
                            }
                        }

            return {"ok": False, "error": "Failed to download video"}

        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {"ok": False, "error": str(e)}

    async def recover_prediction(self, prediction_id: str) -> Dict[str, Any]:
        """
        Recover an existing prediction by ID (useful for retries)
        """
        if not self.api_token:
            return {"ok": False, "error": "REPLICATE_API_TOKEN not configured"}

        try:
            import replicate
            replicate.api_token = self.api_token

            prediction = replicate.predictions.get(prediction_id)

            logger.info(f"Recovering prediction {prediction_id}: status={prediction.status}")

            if prediction.status == "succeeded" and prediction.output:
                # Extract video URL from output
                output = prediction.output
                if isinstance(output, str):
                    video_url = output
                elif isinstance(output, list) and len(output) > 0:
                    video_url = output[0]
                else:
                    return {"ok": False, "error": "No video URL in prediction"}

                # Download video
                async with aiohttp.ClientSession() as session:
                    async with session.get(video_url) as response:
                        if response.status == 200:
                            video_bytes = await response.read()
                            video_base64 = base64.b64encode(video_bytes).decode('utf-8')

                            return {
                                "ok": True,
                                "result": {
                                    "video_base64": video_base64,
                                    "video_url": video_url,
                                    "metadata": {
                                        "prediction_id": prediction_id,
                                        "recovered": True
                                    }
                                }
                            }

            return {"ok": False, "error": f"Prediction status: {prediction.status}"}

        except Exception as e:
            logger.error(f"Failed to recover prediction {prediction_id}: {str(e)}")
            return {"ok": False, "error": str(e)}


# Global instance for use in application
replicate_video_client = ReplicateVideoClient()