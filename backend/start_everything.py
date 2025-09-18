#!/usr/bin/env python3
"""
Start everything needed for parallel processing with one command
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def start_redis():
    """Start Redis server if not running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is already running")
        return True
    except:
        print("🔴 Starting Redis server...")
        try:
            # Try to start Redis server
            subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)  # Give Redis time to start
            
            # Verify it's running
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            print("✅ Redis server started successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to start Redis: {e}")
            print("💡 Please install Redis: brew install redis")
            return False

def start_workers():
    """Start Celery workers for parallel processing"""
    print("👷 Starting Celery workers...")
    
    # Start 3 workers with 4 concurrency each = 12 total parallel processes
    workers = []
    for i in range(3):
        worker_id = i + 1
        print(f"🚀 Starting worker {worker_id}...")
        
        try:
            process = subprocess.Popen([
                sys.executable, 'start_worker.py'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            workers.append(process)
            time.sleep(1)  # Give each worker time to start
        except Exception as e:
            print(f"❌ Failed to start worker {worker_id}: {e}")
    
    print(f"✅ Started {len(workers)} workers")
    print("📊 Total parallel capacity: 12 processes")
    return len(workers) > 0

def main():
    print("🏭 Starting Complete Parallel Processing System")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Start Redis
    if not start_redis():
        print("❌ Cannot start system without Redis")
        return False
    
    # Start workers
    if not start_workers():
        print("❌ Cannot start system without workers")
        return False
    
    print("\n🎉 Parallel processing system is ready!")
    print("📊 System Status:")
    print("   - Redis: ✅ Running on localhost:6379")
    print("   - Workers: ✅ 3 workers with 4 concurrency each")
    print("   - Total Capacity: 12 parallel processes")
    print("\n📝 The system is now ready for parallel PDF processing!")
    print("   Use the frontend 'Run Scraper' button to start processing.")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

