# 🚀 Ember OA Backend Deployment Guide

## Overview
This guide explains how to properly start and manage the backend services for the Ember OA policy scraper.

## 🏗️ Architecture
- **Redis**: Message broker for Celery
- **Flask**: API server handling scraping requests
- **Celery Workers**: Background task processors (idle until scraping starts)

## 🚀 Quick Start

### Start All Services
```bash
./start_backend.sh
```

### Stop All Services
```bash
./stop_backend.sh
```

## 📋 Manual Service Management

### 1. Start Redis
```bash
redis-server --daemonize yes --port 6379
```

### 2. Start Celery Workers
```bash
cd backend
source ../venv/bin/activate
celery -A scraper worker --concurrency=1 --prefetch-multiplier=1 --max-tasks-per-child=3 --loglevel=info --detach
```

### 3. Start Flask Backend
```bash
cd backend
source ../venv/bin/activate
python app.py
```

## 🔍 Health Checks

### Check All Services
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "celery_workers": 1,
  "redis": "connected",
  "status": "healthy",
  "workers": ["celery@hostname"]
}
```

### Check Individual Services
```bash
# Redis
redis-cli ping

# Celery Workers
celery -A backend.scraper inspect active

# Flask
curl http://localhost:8000/api/health
```

## 🎯 How It Works

### Service Lifecycle
1. **Redis starts** → Message broker ready
2. **Celery workers start** → Background processors ready (but idle)
3. **Flask starts** → API server ready
4. **User clicks "Run Scraper"** → Workers begin processing tasks
5. **Scraping completes** → Workers return to idle state

### Filter Awareness
- Workers respect selected months/options from the frontend dropdown
- Only selected PDFs are processed (not all 33 months)
- Progress shows accurate counts (e.g., "2/3 policies" instead of "2/33")

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check for port conflicts
lsof -i :6379  # Redis
lsof -i :8000  # Flask

# Kill conflicting processes
pkill -f "redis-server"
pkill -f "python.*app.py"
pkill -f "celery.*worker"
```

### Workers Not Processing Tasks
```bash
# Check worker status
celery -A backend.scraper inspect active

# Check Redis connection
redis-cli ping

# Restart workers
./stop_backend.sh
./start_backend.sh
```

### Memory Issues
- Workers are configured with conservative settings
- Process 1 PDF at a time with 3-second delays
- Workers restart every 3 tasks to prevent memory leaks

## 🚀 Production Deployment

### Using the Startup Script
The `start_backend.sh` script is production-ready and includes:
- ✅ Process monitoring
- ✅ Graceful shutdown handling
- ✅ Health checks
- ✅ Error handling
- ✅ Clean logging

### Environment Variables
```bash
export REDIS_URL=redis://localhost:6379/0
export FLASK_ENV=production
export CELERY_BROKER_URL=redis://localhost:6379/0
```

### Process Management
For production, consider using:
- **systemd** (Linux)
- **supervisor** (Python)
- **PM2** (Node.js alternative)
- **Docker Compose** (Containerized)

## 📊 Monitoring

### Log Files
- `celery_worker.log` - Celery worker logs
- Flask logs to stdout (can be redirected)

### Metrics to Monitor
- Redis memory usage
- Celery worker CPU/memory
- Flask response times
- Task queue length

## 🔧 Configuration

### Celery Settings (backend/scraper.py)
```python
celery_app.conf.worker_prefetch_multiplier = 1  # Process one task at a time
celery_app.conf.worker_max_tasks_per_child = 3  # Restart workers frequently
celery_app.conf.worker_max_memory_per_child = 200000  # 200MB limit
celery_app.conf.task_time_limit = 1800  # 30 minute timeout
```

### Flask Settings (backend/app.py)
- Debug mode: OFF for production
- Host: 0.0.0.0 (all interfaces)
- Port: 8000

## 🎉 Success Indicators
- ✅ All services start without errors
- ✅ Health check returns "healthy"
- ✅ Workers are idle but ready
- ✅ Frontend can connect to API
- ✅ Scraping respects selected filters
- ✅ Progress tracking works accurately
