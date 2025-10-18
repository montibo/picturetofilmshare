# 🔧 Services Documentation

## Overview

This document provides comprehensive documentation for all services in the AnimateMyPicture platform. Each service is designed to be modular, reusable, and independently testable.

## 📚 Table of Contents

1. [Core Services](#core-services)
2. [AI/ML Services](#aiml-services)
3. [Payment Services](#payment-services)
4. [Storage Services](#storage-services)
5. [Communication Services](#communication-services)
6. [Processing Services](#processing-services)
7. [Utility Services](#utility-services)

---

## Core Services

### 🎥 ReplicateVideoService
**Location**: `backend/app/services/replicate_video_service.py`
**Purpose**: Manages AI video generation using Replicate's infrastructure

#### Key Methods
```python
async def generate_from_image(
    prompt: str,
    image_url: str,
    duration: int,
    aspect_ratio: str
) -> Dict[str, Any]
```

#### Configuration
```python
MODELS = {
    "seedance-pro": {
        "id": "bytedance/seedance-1-pro",
        "cost": 0.05,  # Per segment
        "max_duration": 10,
        "resolution": "480p"
    }
}
```

#### Usage Example
```python
result = await replicate_video_client.generate_from_image(
    prompt="Natural flowing animation with life",
    image_url="gs://bucket/image.jpg",
    duration=10,
    aspect_ratio="16:9"
)
```

#### Error Handling
- `ReplicateAPIError`: API communication failures
- `TimeoutError`: Generation exceeds 12 minutes
- `InvalidInputError`: Unsupported image format

---

### 💳 StripeService
**Location**: `backend/app/services/stripe_service.py`
**Purpose**: Handles all payment processing operations

#### Key Methods
```python
def create_checkout_session(
    job_id: str,
    amount_eur_cents: int,
    customer_email: str,
    locale: str
) -> stripe.checkout.Session

def construct_event_from_request(
    payload: bytes,
    sig_header: str
) -> stripe.Event

def refund_payment(
    payment_intent_id: str,
    amount_cents: int = None
) -> stripe.Refund
```

#### Pricing Configuration
```python
PRICING_EUR_CENTS = {
    "5": 490,    # 4.90€
    "10": 690,   # 6.90€
    "20": 990,   # 9.90€
    "30": 1490,  # 14.90€
    "60": 2490   # 24.90€
}
```

#### Webhook Events Handled
- `checkout.session.completed`
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `charge.refunded`

---

### 🎨 PromptService
**Location**: `backend/app/services/prompt_service.py`
**Purpose**: Constructs and optimizes AI prompts for video generation

#### Templates Available
```python
TEMPLATES = {
    "magic_sparkle": "Magical animation with sparkles",
    "floating": "Elements floating and drifting",
    "celebration": "Festive, celebratory animation",
    "peaceful": "Calm, peaceful movement"
}
```

#### Styles Available
```python
STYLES = {
    "cinematic": "Cinematic quality with depth",
    "dreamy": "Soft, dreamy atmosphere",
    "vibrant": "Vibrant colors and high contrast",
    "vintage": "Vintage film aesthetic"
}
```

#### Core Prompt Strategy
```python
# After extensive testing, this simple prompt works best:
BASE_PROMPT = """
Animate all elements in motion,
flowing animation,
all elements moving with life,
fluid movements,
natural movement,
keep character the same,
keep letters,
keep character present and face
"""
```

---

### 🎬 VideoAudioService
**Location**: `backend/app/services/video_audio_service.py`
**Purpose**: FFmpeg-based video and audio processing

#### Key Operations
```python
# Extract last frame for continuity
async def extract_last_frame(video_base64: str) -> str

# Concatenate multiple segments
async def concatenate_videos(segments: List[str]) -> str

# Add audio with fade effects
async def add_audio_to_video(
    video_base64: str,
    audio_base64: str,
    fade_duration: float = 2.0
) -> str
```

#### FFmpeg Optimization Settings
```python
VIDEO_ENCODING = {
    "codec": "libx264",
    "preset": "medium",
    "crf": 18,  # Quality (lower = better)
    "bitrate": "10M",
    "fps": 24
}

AUDIO_ENCODING = {
    "codec": "aac",
    "bitrate": "192k",
    "sample_rate": 44100
}
```

---

## AI/ML Services

### 🤖 GeminiEnhancementService
**Purpose**: Enhances prompts using Google's Gemini AI

#### Capabilities
- Scene analysis
- Mood detection
- Color palette extraction
- Movement suggestions
- Style recommendations

#### Usage
```python
enhanced_prompt = await gemini_service.enhance_prompt(
    base_prompt="Animate the image",
    image_analysis=vision_results,
    target_mood="joyful"
)
```

---

### 🎵 ElevenLabsMusicService
**Purpose**: Generates AI music for videos

#### Features
- Mood-based generation
- Duration matching
- Fade in/out effects
- Style customization

#### Music Styles
```python
MUSIC_STYLES = {
    "upbeat": {"tempo": 120, "energy": "high"},
    "calm": {"tempo": 60, "energy": "low"},
    "epic": {"tempo": 140, "energy": "very_high"},
    "romantic": {"tempo": 70, "energy": "medium"}
}
```

---

### 👁️ VisionAnalysisService
**Purpose**: Analyzes images for context and content

#### Analysis Results
```python
{
    "faces": [{"confidence": 0.95, "emotions": ["happy"]}],
    "objects": ["tree", "sky", "person"],
    "scene": "outdoor",
    "dominant_colors": ["#87CEEB", "#228B22"],
    "text": ["Happy Birthday"],
    "safe_search": {"adult": "UNLIKELY", "violence": "VERY_UNLIKELY"}
}
```

---

## Storage Services

### ☁️ CloudStorageService
**Purpose**: Manages Google Cloud Storage operations

#### Core Functions
```python
# Upload file to GCS
async def upload_to_gcs(
    file_data: bytes,
    destination_path: str,
    content_type: str = "video/mp4"
) -> str

# Generate signed URL
def generate_signed_url(
    blob_path: str,
    expiration_seconds: int = 3600
) -> str

# Download from GCS
async def download_from_gcs(
    source_path: str
) -> bytes
```

#### Bucket Structure
```
gs://bucket/
├── jobs/{job_id}/
│   ├── input/          # Original images
│   ├── output/         # Final videos
│   ├── segments/       # Temporary segments
│   └── thumbnails/     # 200x200 previews
├── temp/               # Temporary uploads
└── demos/              # Sample videos
```

---

### 🗄️ FirestoreService
**Purpose**: Database operations for job management

#### Collections
```python
COLLECTIONS = {
    "jobs": Job,           # Main job documents
    "temp_uploads": Upload, # Temporary uploads
    "users": User,         # User profiles
    "analytics": Event     # Analytics events
}
```

#### Query Examples
```python
# Get recent jobs
jobs = await firestore.get_recent_jobs(
    limit=10,
    status="succeeded"
)

# Update job status
await firestore.update_job_status(
    job_id="uuid",
    status="processing",
    progress=50
)
```

---

## Communication Services

### 📧 BrevoEmailService
**Purpose**: Transactional email delivery

#### Email Templates
```python
TEMPLATES = {
    "video_ready": {
        "subject": "Your video is ready! 🎬",
        "template_id": 1
    },
    "payment_received": {
        "subject": "Payment confirmed ✅",
        "template_id": 2
    }
}
```

#### Usage
```python
await email_service.send_video_ready(
    to_email="user@example.com",
    video_url="https://...",
    job_id="uuid"
)
```

---

### 📱 WhatsAppService
**Purpose**: WhatsApp Business API integration

#### Message Types
```python
# Send video with preview
await whatsapp_service.send_video(
    phone_number="+33600000000",
    video_url="https://...",
    caption="Your video is ready!"
)

# Send template message
await whatsapp_service.send_template(
    phone_number="+33600000000",
    template_name="video_delivery",
    parameters=["John", "20 seconds"]
)
```

#### Webhook Events
- Message delivered
- Message read
- Message failed
- User replied

---

## Processing Services

### ⚙️ JobProcessingService
**Purpose**: Orchestrates the entire video generation pipeline

#### Pipeline Stages
```python
PIPELINE = [
    "validate_input",
    "moderate_content",
    "enhance_image",
    "generate_segments",
    "extract_audio",
    "concatenate_videos",
    "add_effects",
    "upload_result",
    "send_notifications"
]
```

#### State Machine
```
QUEUED → PROCESSING → SUCCEEDED
         ↓           ↓
         FAILED ← CANCELLED
```

---

### 🔄 TaskQueueService
**Purpose**: Manages Cloud Tasks for async processing

#### Queue Configuration
```python
QUEUES = {
    "video-generation": {
        "max_concurrent": 100,
        "rate_limits": "500/s",
        "retry_config": {
            "max_attempts": 3,
            "backoff": "exponential"
        }
    },
    "notifications": {
        "max_concurrent": 50,
        "rate_limits": "100/s"
    }
}
```

---

## Utility Services

### 🔍 ValidationService
**Purpose**: Input validation and sanitization

#### Validators
```python
# Image validation
def validate_image(file_data: bytes) -> bool:
    - Check file size (< 10MB)
    - Verify format (JPEG, PNG, WebP)
    - Check dimensions (min 256x256)
    - Scan for malware

# Email validation
def validate_email(email: str) -> bool:
    - RFC compliance
    - Domain exists
    - Not disposable
```

---

### 📊 AnalyticsService
**Purpose**: Tracks usage and performance metrics

#### Metrics Tracked
```python
METRICS = {
    "api_requests": Counter,
    "video_generations": Histogram,
    "payment_amounts": Summary,
    "error_rates": Gauge
}
```

#### Events
```python
track_event(
    event_type="video_generated",
    properties={
        "duration": 20,
        "template": "magic",
        "processing_time": 145.3
    }
)
```

---

### 🔐 AuthenticationService
**Purpose**: API key and JWT token management

#### Security Features
- API key rotation
- JWT with refresh tokens
- Rate limiting per key
- IP whitelisting
- Request signing

---

### 🚦 RateLimitService
**Purpose**: Prevents abuse and ensures fair usage

#### Limits
```python
RATE_LIMITS = {
    "api_global": "10000/hour",
    "api_per_ip": "100/minute",
    "video_generation": "10/hour/user",
    "free_tier": "3/day/user"
}
```

---

## 🧪 Testing Services

### Mock Services for Testing
```python
class MockReplicateService:
    """Mock for testing without real API calls"""
    async def generate_from_image(self, *args, **kwargs):
        return {
            "ok": True,
            "result": {
                "video_base64": "mock_base64_data",
                "video_url": "https://mock.url/video.mp4"
            }
        }
```

---

## 🔄 Service Dependencies

```mermaid
graph TD
    API[API Endpoints] --> Auth[AuthenticationService]
    API --> RateLimit[RateLimitService]
    API --> Validation[ValidationService]

    API --> Job[JobProcessingService]
    Job --> Queue[TaskQueueService]
    Job --> Storage[CloudStorageService]
    Job --> DB[FirestoreService]

    Queue --> Replicate[ReplicateVideoService]
    Queue --> FFmpeg[VideoAudioService]
    Queue --> Email[BrevoEmailService]
    Queue --> WhatsApp[WhatsAppService]

    Replicate --> Prompt[PromptService]
    Prompt --> Gemini[GeminiEnhancementService]
    FFmpeg --> ElevenLabs[ElevenLabsMusicService]
```

---

## 🚀 Service Initialization

```python
# Application startup
async def initialize_services():
    # Core services
    replicate_service = ReplicateVideoClient()
    stripe_service = StripeService()
    storage_service = CloudStorageService()

    # Initialize connections
    await storage_service.initialize()
    await database.connect()

    # Warm up caches
    await cache_service.warm_up()

    # Health checks
    await verify_all_services_healthy()
```

---

## 📈 Performance Characteristics

| Service | Latency (P50) | Latency (P95) | Throughput | Error Rate |
|---------|---------------|---------------|------------|------------|
| ReplicateVideo | 120s | 300s | 100/hour | < 1% |
| Stripe | 200ms | 500ms | 1000/min | < 0.1% |
| Storage | 100ms | 300ms | 10000/min | < 0.01% |
| Email | 1s | 3s | 100/min | < 0.5% |
| Database | 20ms | 50ms | 5000/sec | < 0.01% |

---

## 🛠️ Maintenance & Monitoring

### Health Check Endpoints
```python
GET /health/replicate    # Check Replicate API
GET /health/stripe       # Check Stripe connectivity
GET /health/storage      # Check GCS access
GET /health/database     # Check Firestore connection
```

### Monitoring Dashboards
- Service availability
- Response time trends
- Error rate tracking
- Cost per service
- Usage patterns

---

*This service architecture processes 1000+ videos daily with 99.9% reliability.*