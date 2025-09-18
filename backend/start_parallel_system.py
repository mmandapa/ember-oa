#!/usr/bin/env python3
"""
Start the complete parallel processing system with one command
"""
import subprocess
import time
import sys
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
            subprocess.Popen(['redis-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
            print("✅ Redis server started")
            return True
        except Exception as e:
            print(f"❌ Failed to start Redis: {e}")
            return False

def start_workers():
    """Start multiple Celery workers for parallel processing"""
    print("👷 Starting multiple Celery workers...")
    
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
    return workers

def start_flower():
    """Start Flower monitoring UI"""
    print("🌸 Starting Flower monitoring...")
    try:
        process = subprocess.Popen([
            sys.executable, '-m', 'celery', '-A', 'scraper', 'flower', '--port=5555'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        print("✅ Flower started with PID:", process.pid)
        return process
    except Exception as e:
        print(f"❌ Failed to start Flower: {e}")
        return None

def main():
    print("🏭 Starting Complete Parallel Processing System")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Start Redis
    if not start_redis():
        print("❌ Cannot start system without Redis")
        return
    
    # Start workers
    workers = start_workers()
    if not workers:
        print("❌ Cannot start system without workers")
        return
    
    # Start Flower
    flower = start_flower()
    
    print("\n🎉 Parallel processing system is ready!")
    print("📊 Monitoring:")
    if flower:
        print("   - Flower UI: http://localhost:5555")
    print("   - Redis: localhost:6379")
    print("   - Workers: 3 workers with 4 concurrency each")
    print("\n🔧 To stop the system:")
    print("   - Kill workers: pkill -f 'python start_worker.py'")
    print("   - Kill flower: pkill -f 'celery.*flower'")
    print("   - Stop Redis: redis-cli shutdown")
    print("\n📝 The system is now ready for parallel PDF processing!")
    print("   Use the frontend 'Run Scraper' button to start processing.")

if __name__ == '__main__':
    main()

