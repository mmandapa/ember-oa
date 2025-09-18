#!/usr/bin/env python3
"""
Start multiple Celery workers for maximum parallel processing
"""
import os
import sys
import subprocess
import time
from celery import Celery
from scraper import celery_app

def start_worker(worker_id, concurrency=4):
    """Start a single worker process"""
    try:
        print(f"🚀 Starting worker {worker_id} with concurrency {concurrency}")
        celery_app.worker_main([
            'worker',
            '--loglevel=info',
            '--concurrency=4',
            '--hostname=scraper_worker_{}@%h'.format(worker_id)
        ])
    except Exception as e:
        print(f"❌ Error starting worker {worker_id}: {e}")

if __name__ == '__main__':
    print("🏭 Starting multiple Celery workers for parallel processing")
    print("=" * 60)
    
    # Start 3 workers with 4 concurrency each = 12 total parallel processes
    workers = []
    for i in range(3):
        worker_id = i + 1
        print(f"👷 Starting worker {worker_id}...")
        
        # Start worker in background
        process = subprocess.Popen([
            sys.executable, __file__, str(worker_id)
        ])
        workers.append(process)
        time.sleep(2)  # Give each worker time to start
    
    print(f"✅ Started {len(workers)} workers")
    print("📊 Total parallel capacity: 12 processes")
    print("🔧 To stop all workers: Ctrl+C")
    
    try:
        # Wait for all workers
        for process in workers:
            process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all workers...")
        for process in workers:
            process.terminate()
        print("✅ All workers stopped")
