#!/usr/bin/env python3
"""
Script to ensure Celery workers stay running during scraping
"""

import subprocess
import time
import sys
import os
import signal
from celery import Celery

# Import the same Celery app configuration
sys.path.append(os.path.dirname(__file__))
from scraper import celery_app

def check_workers():
    """Check if Celery workers are running"""
    try:
        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ Found {len(active_workers)} active Celery workers")
            return True
        else:
            print("❌ No active Celery workers found")
            return False
    except Exception as e:
        print(f"❌ Error checking workers: {e}")
        return False

def start_worker():
    """Start a Celery worker"""
    try:
        print("🚀 Starting Celery worker...")
        cmd = [
            sys.executable, "-m", "celery", 
            "-A", "scraper", "worker",
            "--concurrency=1",
            "--prefetch-multiplier=1", 
            "--max-tasks-per-child=3",
            "--loglevel=info"
        ]
        
        # Start worker in background
        process = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(__file__),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"✅ Celery worker started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Error starting worker: {e}")
        return None

def main():
    """Main monitoring loop"""
    print("🔍 Starting Celery worker monitor...")
    
    worker_process = None
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down worker monitor...")
        if worker_process:
            worker_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while True:
        try:
            if not check_workers():
                print("🔄 Restarting Celery worker...")
                if worker_process:
                    worker_process.terminate()
                worker_process = start_worker()
            
            # Check every 30 seconds
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped by user")
            break
        except Exception as e:
            print(f"❌ Monitor error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
