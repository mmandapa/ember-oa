#!/usr/bin/env python3
"""
Simple startup script for Cigna Policy Scraper
Ensures Redis, Celery workers, and Flask are running
"""

import os
import sys
import subprocess
import time
import signal

def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
        return True
    except:
        print("❌ Redis is not running")
        return False

def start_redis():
    """Start Redis server"""
    print("🚀 Starting Redis server...")
    try:
        subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        
        # Verify Redis started
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis started successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to start Redis: {e}")
        return False

def start_celery_worker():
    """Start a single Celery worker"""
    print("👷 Starting Celery worker...")
    try:
        subprocess.Popen([
            sys.executable, 'start_worker.py'
        ], cwd=os.path.join(os.path.dirname(__file__), 'backend'))
        
        time.sleep(5)
        
        # Verify worker started
        from backend.scraper import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers and len(active_workers) > 0:
            print(f"✅ Celery worker started successfully")
            return True
        else:
            print("❌ Celery worker failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Celery worker: {e}")
        return False

def start_flask_server():
    """Start Flask server"""
    print("🌐 Starting Flask server...")
    try:
        subprocess.Popen([
            sys.executable, 'app.py'
        ], cwd=os.path.join(os.path.dirname(__file__), 'backend'))
        
        time.sleep(3)
        
        # Test Flask server
        import requests
        response = requests.get('http://localhost:8000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ Flask server started successfully")
            return True
        else:
            print("❌ Flask server not responding")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")
        return False

def main():
    print("🚀 Starting Simple Cigna Policy Scraper System")
    print("=" * 50)
    
    # Change to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Start Redis if not running
    if not check_redis():
        if not start_redis():
            print("❌ Cannot start system without Redis")
            sys.exit(1)
    
    # Start Celery worker
    if not start_celery_worker():
        print("❌ Cannot start system without Celery worker")
        sys.exit(1)
    
    # Start Flask server
    if not start_flask_server():
        print("❌ Cannot start system without Flask server")
        sys.exit(1)
    
    print("\n🎉 Simple System Started Successfully!")
    print("=" * 50)
    print("📡 Flask API Server: http://localhost:8000")
    print("🔧 API Endpoints:")
    print("   POST /api/scrape-async - Start scraping")
    print("   GET  /api/task-status/<task_id> - Check task status")
    print("   POST /api/clear-data - Clear all data")
    print("   GET  /api/health - Health check")
    print("   GET  /api/system-status - System status")
    
    print("\n🎯 How to Use:")
    print("1. Open your frontend dashboard")
    print("2. Click 'Clear Data' to delete existing data")
    print("3. Click 'Run Scraper' to start scraping")
    print("4. Monitor progress in real-time")
    
    print("\n🛑 Press Ctrl+C to stop all services")
    
    # Keep the script running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
        # Kill background processes
        subprocess.run(['pkill', '-f', 'redis-server'], capture_output=True)
        subprocess.run(['pkill', '-f', 'start_worker.py'], capture_output=True)
        subprocess.run(['pkill', '-f', 'app.py'], capture_output=True)
        print("✅ System stopped")

if __name__ == '__main__':
    main()
