#!/usr/bin/env python3
"""
Start the complete Cigna Policy Scraper system with Flask backend
This replaces Next.js API routes for better performance
"""

import os
import sys
import subprocess
import time
import signal
import threading

def start_redis():
    """Start Redis server if not running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is already running")
        return True
    except:
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

def start_celery_workers():
    """Start Celery workers"""
    print("👷 Starting Celery workers...")
    try:
        # Start multiple workers
        for i in range(3):
            subprocess.Popen([
                sys.executable, 'start_worker.py'
            ], cwd=os.path.dirname(__file__), 
               stdout=subprocess.DEVNULL, 
               stderr=subprocess.DEVNULL)
            time.sleep(1)
        
        # Give workers time to start
        time.sleep(5)
        
        # Verify workers are running
        from scraper import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers and len(active_workers) > 0:
            print(f"✅ Started {len(active_workers)} Celery workers")
            return True
        else:
            print("❌ Failed to start Celery workers")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Celery workers: {e}")
        return False

def start_flask_server():
    """Start Flask API server"""
    print("🌐 Starting Flask API server...")
    try:
        subprocess.Popen([
            sys.executable, 'app.py'
        ], cwd=os.path.dirname(__file__))
        
        # Give Flask time to start
        time.sleep(3)
        
        # Test Flask server
        import requests
        response = requests.get('http://localhost:8000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ Flask API server started successfully")
            return True
        else:
            print("❌ Flask API server not responding")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")
        return False

def main():
    print("🚀 Starting Complete Cigna Policy Scraper System")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Start components
    if not start_redis():
        print("❌ Cannot start system without Redis")
        sys.exit(1)
    
    if not start_celery_workers():
        print("❌ Cannot start system without Celery workers")
        sys.exit(1)
    
    if not start_flask_server():
        print("❌ Cannot start system without Flask server")
        sys.exit(1)
    
    print("\n🎉 Complete System Started Successfully!")
    print("=" * 60)
    print("📡 Flask API Server: http://localhost:8000")
    print("🔧 API Endpoints:")
    print("   POST /api/scrape-async - Start parallel scraping")
    print("   GET  /api/task-status/<task_id> - Check task status")
    print("   GET  /api/health - Health check")
    print("   GET  /api/system-status - System status")
    print("\n📊 System Status:")
    
    # Show system status
    try:
        import requests
        response = requests.get('http://localhost:8000/api/system-status', timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"   Redis: ✅ Connected ({status['redis']['memory_used']})")
            print(f"   Celery Workers: ✅ {status['celery']['active_workers']} active")
            print(f"   Flask Server: ✅ Running on port 8000")
    except:
        print("   Status check failed")
    
    print("\n🎯 Next Steps:")
    print("1. Open your frontend dashboard")
    print("2. Click 'Run Scraper' button")
    print("3. The system will automatically:")
    print("   - Start Redis + Workers")
    print("   - Process PDFs in parallel")
    print("   - Update the database")
    print("   - Show real-time progress")
    
    print("\n💡 Performance Benefits:")
    print("   - Flask backend (vs Next.js API routes)")
    print("   - Parallel PDF processing")
    print("   - Multiple Celery workers")
    print("   - Efficient resource management")
    
    print("\n🛑 Press Ctrl+C to stop all services")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
        # Kill background processes
        subprocess.run(['pkill', '-f', 'redis-server'], capture_output=True)
        subprocess.run(['pkill', '-f', 'start_worker.py'], capture_output=True)
        subprocess.run(['pkill', '-f', 'app.py'], capture_output=True)
        print("✅ System stopped")

if __name__ == '__main__':
    main()
