#!/usr/bin/env python3
"""
Start just the Celery workers for parallel processing
"""
import subprocess
import sys
import time

def main():
    print("👷 Starting Celery Workers for Parallel Processing")
    print("=" * 50)
    
    # Start 3 workers with 4 concurrency each = 12 total parallel processes
    workers = []
    for i in range(3):
        worker_id = i + 1
        print(f"🚀 Starting worker {worker_id}...")
        
        try:
            process = subprocess.Popen([
                sys.executable, 'start_worker.py'
            ])
            workers.append(process)
            time.sleep(1)  # Give each worker time to start
        except Exception as e:
            print(f"❌ Failed to start worker {worker_id}: {e}")
    
    print(f"✅ Started {len(workers)} workers")
    print("📊 Total parallel capacity: 12 processes")
    print("\n🔧 To stop workers: Ctrl+C or pkill -f 'python start_worker.py'")
    print("📝 Workers are ready for parallel PDF processing!")
    
    try:
        # Wait for workers
        for process in workers:
            process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all workers...")
        for process in workers:
            process.terminate()
        print("✅ All workers stopped")

if __name__ == '__main__':
    main()

