# Backend - Cigna Policy Scraper

This directory contains the backend components for the Cigna Policy Scraper system with **Flask API** for better performance.

## Files

- **`app.py`** - Flask API server (replaces Next.js API routes)
- **`scraper.py`** - Main scraper script with Celery integration
- **`start_worker.py`** - Script to start the Celery worker
- **`start_scrape_task.py`** - Script to initiate the scraping task
- **`check_task_status.py`** - Script to check task status
- **`start_flask_server.py`** - Script to start Flask server
- **`requirements.txt`** - Python dependencies
- **`schema.sql`** - Database schema
- **`test_openai.py`** - OpenAI testing script
- **`TESTING.md`** - Testing documentation

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start Redis server:
   ```bash
   redis-server
   ```

3. Start Celery worker:
   ```bash
   python start_worker.py
   ```

4. Start Flask API server:
   ```bash
   python start_flask_server.py
   ```

5. Start scraping task (via Flask API):
   ```bash
   curl -X POST http://localhost:8000/api/scrape-async
   ```

6. Check task status:
   ```bash
   python check_task_status.py <task_id>
   ```

## Flask API Endpoints

- **POST** `/api/scrape-async` - Start parallel scraping
- **GET** `/api/task-status/<task_id>` - Check task status
- **GET** `/api/health` - Health check
- **GET** `/api/system-status` - Detailed system status

## Monitoring

- **Flower UI**: http://localhost:5555 (Celery task monitoring)
- **Redis**: localhost:6379

## Environment Variables

Make sure you have the following environment variables set:
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_SUPABASE_URL`
