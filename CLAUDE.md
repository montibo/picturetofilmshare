# 🤖 Claude Code Integration Guide

This project is optimized for use with [Claude Code](https://github.com/anthropics/claude-code), Anthropic's AI coding assistant.

## 🚀 Quick Start with Claude Code

```bash
# Open project with Claude Code
claude-code .

# Claude will automatically understand the architecture and can help you:
# - Set up the development environment
# - Deploy to Google Cloud
# - Add new features
# - Debug issues
```

## 📋 Project Context for Claude

### Architecture Overview
- **Backend**: FastAPI on Google Cloud Run
- **Frontend**: React with TypeScript
- **Queue**: Cloud Tasks for async processing
- **AI**: Replicate API for video generation
- **Storage**: Google Cloud Storage for assets
- **Database**: Firestore for job tracking
- **Payments**: Stripe with deferred capture

### Key Workflows

#### 1. Video Generation Pipeline
```
User Upload → Payment → Queue Job → AI Generation → FFmpeg Assembly → Delivery
```

#### 2. Development Workflow
```bash
# Local development with hot reload
docker-compose up -d

# Backend: http://localhost:8093
# Frontend: http://localhost:5177
```

#### 3. Deployment
```bash
# Deploy to production (requires GCP setup)
./deploy-prod.sh
```

## 🎯 Common Tasks for Claude

### Add a New Feature
```
Claude, I want to add [feature description]. Please:
1. Analyze the current architecture
2. Propose implementation approach
3. Create necessary files
4. Update existing code
5. Add tests
```

### Debug an Issue
```
Claude, I'm getting [error description]. Please:
1. Check relevant logs
2. Identify the root cause
3. Propose a fix
4. Implement the solution
```

### Optimize Performance
```
Claude, the [component] is slow. Please:
1. Profile the current implementation
2. Identify bottlenecks
3. Propose optimizations
4. Implement improvements
```

## 📁 Project Structure Guide

### Backend Services (`backend/app/services/`)
- **replicate_video_service.py** - Core AI video generation logic
- **stripe_service.py** - Payment processing and webhooks
- **prompt_service.py** - AI prompt construction
- **video_audio_service.py** - FFmpeg video/audio processing
- **startframe_service.py** - Image preprocessing
- **gemini_gcs_enhance_service.py** - Prompt enhancement with Gemini

### API Endpoints (`backend/app/endpoints/core.py`)
- `/api/upload/init` - Initialize file upload
- `/api/checkout/session` - Create payment session
- `/api/jobs/{job_id}` - Get job status
- `/internal/generate` - Trigger generation (Cloud Tasks)

### Frontend Components (`frontend/src/`)
- **App.tsx** - Main application component
- **Upload.tsx** - File upload interface
- **VideoPlayer.tsx** - Video preview/download

### Storytelling Scripts (`storytelling/`)
- **generate_story_insta_mouse_click.py** - Instagram story with animation
- **add_audio_to_video.py** - Audio mixing utility

## 🔧 Environment Setup

### Required API Keys
```env
# Copy .env.example to .env and fill in:
GCP_PROJECT_ID=           # Google Cloud project
GCS_BUCKET=               # Storage bucket name
REPLICATE_API_TOKEN=      # Replicate.com API key
STRIPE_SECRET_KEY=        # Stripe secret key
STRIPE_WEBHOOK_SECRET=    # Stripe webhook secret
INTERNAL_API_KEY=         # Internal API authentication
```

### Google Cloud Setup
1. Create a GCP project
2. Enable required APIs:
   - Cloud Run
   - Cloud Tasks
   - Cloud Storage
   - Firestore
3. Set up service account with appropriate permissions
4. Configure bucket CORS for frontend access

### Local Development
```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Install Node dependencies
cd ../frontend
npm install

# Run with Docker Compose
cd ..
docker-compose up -d
```

## 🎨 Customization Points

### Video Generation Parameters
- **Duration**: 5, 10, 20, 30, 60 seconds
- **Resolution**: 480p, 720p, 1080p
- **Aspect Ratio**: 16:9, 9:16, 1:1
- **Templates**: Various animation styles

### Prompt Engineering
The main prompt is in `backend/app/services/prompt_service.py`:
```python
"Animate all elements in motion, flowing animation,
all elements moving with life, fluid movements,
natural movement, keep character the same"
```

### Pricing Configuration
Update in `backend/app/config.py`:
```python
PRICING = {
    "5": 490,   # 4.90€
    "10": 690,  # 6.90€
    "20": 990,  # 9.90€
    # ...
}
```

## 🐛 Debugging Guide

### Check Job Status
```bash
# Get job details
curl "http://localhost:8093/api/jobs/{job_id}" \
  -H "X-API-Key: your-internal-key"
```

### View Logs
```bash
# Docker logs
docker-compose logs -f backend

# Production logs (GCP)
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 --project=your-project
```

### Common Issues

#### Job Stuck in Queue
- Check Cloud Tasks configuration
- Verify INTERNAL_API_KEY matches
- Check webhook processing

#### Video Generation Fails
- Verify Replicate API key
- Check input image format
- Review FFmpeg logs

#### Payment Issues
- Verify Stripe webhook secret
- Check webhook endpoint accessibility
- Review Stripe dashboard

## 🚀 Deployment Guide

### Backend Deployment
```bash
# Build and deploy to Cloud Run
gcloud run deploy backend \
  --source backend \
  --region europe-west1 \
  --platform managed
```

### Frontend Deployment
```bash
# Build production bundle
cd frontend
npm run build

# Deploy to your hosting service
# (e.g., Vercel, Netlify, Cloud Run)
```

### Post-Deployment Checklist
- [ ] Environment variables configured
- [ ] Cloud Tasks queue created
- [ ] Firestore indexes deployed
- [ ] CORS configured on GCS bucket
- [ ] Stripe webhook configured
- [ ] Health check passing

## 💡 Tips for Claude Code Users

1. **Ask for explanations**: "Explain how the video generation pipeline works"
2. **Request improvements**: "Optimize the FFmpeg concatenation process"
3. **Debug with context**: "Why is this job failing?" (provide job ID)
4. **Explore features**: "Show me how to add a new video template"
5. **Get deployment help**: "Help me deploy this to Google Cloud"

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Replicate API Docs](https://replicate.com/docs)
- [Google Cloud Run Guide](https://cloud.google.com/run/docs)
- [Stripe Integration](https://stripe.com/docs)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

---

**Remember**: Claude Code has access to the entire codebase and can help with any aspect of the project. Don't hesitate to ask for help with implementation, debugging, or optimization!