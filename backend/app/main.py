"""
AnimateMyPicture Backend API
FastAPI application for AI-powered video generation
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    logger.info("🚀 Starting AnimateMyPicture API")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Python: {os.sys.version}")

    yield

    # Shutdown
    logger.info("👋 Shutting down AnimateMyPicture API")


# Create FastAPI app
app = FastAPI(
    title="AnimateMyPicture API",
    description="Transform static images into captivating AI-generated videos",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5177').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Health Check
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AnimateMyPicture API",
        "version": "1.0.0"
    }


# ============================================
# Upload Management
# ============================================

@app.post("/api/upload/init")
async def init_upload(request: Request):
    """
    Initialize file upload and return upload URL

    In production, this would return a signed URL for direct upload to cloud storage.
    For the demo, it returns a local upload endpoint.
    """
    try:
        data = await request.json()
        filename = data.get("filename", "image.jpg")

        # In production, generate a signed URL for cloud storage
        # For demo, return local upload endpoint
        upload_url = f"{request.base_url}api/upload/file"

        return {
            "uploadUrl": upload_url,
            "uploadId": "demo-upload-id",
            "filename": filename
        }
    except Exception as e:
        logger.error(f"Upload init error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/file")
async def upload_file(file: UploadFile = File(...)):
    """
    Handle file upload

    In production, this would upload to cloud storage.
    For the demo, it simulates the upload.
    """
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")

        # Validate file size (max 10MB)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # In production, upload to cloud storage
        # For demo, return success
        return {
            "success": True,
            "imageUrl": f"gs://demo-bucket/uploads/{file.filename}",
            "size": len(contents)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Payment Processing
# ============================================

@app.post("/api/checkout/session")
async def create_checkout_session(request: Request):
    """
    Create a payment checkout session

    In production, this integrates with Stripe.
    For the demo, it returns a mock session.
    """
    try:
        data = await request.json()

        # Extract parameters
        job_id = data.get("jobId")
        duration = data.get("duration", 20)
        email = data.get("email")
        locale = data.get("locale", "en")

        # Calculate price (demo pricing)
        prices = {5: 490, 10: 690, 20: 990, 30: 1490, 60: 2490}
        price = prices.get(duration, 990)

        # In production, create Stripe session
        # For demo, return mock session
        return {
            "sessionId": "cs_demo_session",
            "sessionUrl": f"{request.base_url}checkout?session=demo",
            "jobId": job_id,
            "amount": price
        }
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events

    In production, this processes payment confirmations.
    For the demo, it simulates webhook processing.
    """
    try:
        # In production, verify webhook signature
        # For demo, return success
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# Job Management
# ============================================

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get job status and details

    Returns the current status of a video generation job.
    """
    try:
        # In production, fetch from database
        # For demo, return mock data
        return {
            "id": job_id,
            "status": "succeeded",
            "progress": 100,
            "videoUrl": f"https://storage.googleapis.com/demo-bucket/jobs/{job_id}/output.mp4",
            "thumbnailUrl": f"https://storage.googleapis.com/demo-bucket/jobs/{job_id}/thumbnail.jpg",
            "duration": 20,
            "createdAt": "2024-01-01T00:00:00Z",
            "completedAt": "2024-01-01T00:05:00Z"
        }
    except Exception as e:
        logger.error(f"Get job error: {str(e)}")
        raise HTTPException(status_code=404, detail="Job not found")


@app.get("/api/download/{job_id}")
async def download_video(job_id: str):
    """
    Get download URL for completed video

    Returns a signed URL for downloading the generated video.
    """
    try:
        # In production, generate signed download URL
        # For demo, return mock URL
        return {
            "downloadUrl": f"https://storage.googleapis.com/demo-bucket/jobs/{job_id}/output.mp4",
            "expiresIn": 3600
        }
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=404, detail="Video not found")


# ============================================
# Internal Endpoints (Protected)
# ============================================

@app.post("/internal/generate")
async def generate_video(
    request: Request,
    x_api_key: str = Header(None, alias="X-API-Key")
):
    """
    Internal endpoint to trigger video generation

    This is called by the task queue to process jobs.
    Protected by API key authentication.
    """
    try:
        # Verify API key
        expected_key = os.getenv("INTERNAL_API_KEY")
        if not expected_key or x_api_key != expected_key:
            raise HTTPException(status_code=401, detail="Unauthorized")

        data = await request.json()
        job_id = data.get("jobId")

        if not job_id:
            raise HTTPException(status_code=400, detail="Missing jobId")

        # In production, this would:
        # 1. Fetch job details from database
        # 2. Download input image
        # 3. Call Replicate API for each segment
        # 4. Concatenate segments with FFmpeg
        # 5. Upload final video
        # 6. Send notifications

        logger.info(f"Processing job: {job_id}")

        # For demo, return success
        return {
            "success": True,
            "jobId": job_id,
            "message": "Video generation started"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8093))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )