#!/usr/bin/env python3
"""
Start high-performance Celery workers for maximum scraping speed
"""

import os
import sys
import subprocess
import time
import psutil
from multiprocessing import cpu_count

def get_optimal_worker_config():
    """Calculate optimal worker configuration based on system resources"""
    cpu_cores = cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Calculate optimal workers based on CPU cores and memory
    if memory_gb >= 16:
        # High-memory system - can handle more workers
        workers = min(cpu_cores * 2, 16)  # Max 16 workers
        concurrency_per_worker = 8
    elif memory_gb >= 8:
        # Medium-memory system
        workers = min(cpu_cores * 1.5, 12)  # Max 12 workers
        concurrency_per_worker = 6
    else:
        # Lower-memory system
        workers = min(cpu_cores, 8)  # Max 8 workers
        concurrency_per_worker = 4
    
    return int(workers), concurrency_per_worker

def start_high_performance_workers():
    """Start multiple high-performance Celery workers"""
    workers, concurrency = get_optimal_worker_config()
    
    print(f"🚀 Starting High-Performance Celery Workers")
    print(f"📊 System Configuration:")
    print(f"   CPU Cores: {cpu_count()}")
    print(f"   Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print(f"   Workers: {workers}")
    print(f"   Concurrency per Worker: {concurrency}")
    print(f"   Total Parallel Processes: {workers * concurrency}")
    
    worker_processes = []
    
    try:
        for i in range(workers):
            print(f"👷 Starting worker {i+1}/{workers}...")
            
            # Start worker with optimized settings
            process = subprocess.Popen([
                sys.executable, '-m', 'celery',
                '-A', 'scraper',
                'worker',
                '--loglevel=info',
                f'--concurrency={concurrency}',
                '--hostname=high_perf_worker_{i}@%h',
                '--queues=celery',
                '--prefetch-multiplier=1',  # Reduce prefetch for better load balancing
                '--max-tasks-per-child=1000',  # Restart workers periodically to prevent memory leaks
                '--time-limit=300',  # 5 minute time limit per task
                '--soft-time-limit=240'  # 4 minute soft limit
            ], cwd=os.path.dirname(__file__))
            
            worker_processes.append(process)
            time.sleep(2)  # Stagger worker startup
        
        # Wait a moment for workers to register
        time.sleep(10)
        
        # Verify workers are running
        from scraper import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers and len(active_workers) >= workers:
            print(f"✅ Successfully started {len(active_workers)} high-performance workers")
            print(f"📈 Total parallel capacity: {len(active_workers) * concurrency} processes")
            return True
        else:
            print(f"❌ Only {len(active_workers) if active_workers else 0} workers started (expected {workers})")
            return False
            
    except Exception as e:
        print(f"❌ Error starting workers: {e}")
        # Clean up any started processes
        for process in worker_processes:
            try:
                process.terminate()
            except:
                pass
        return False

def main():
    print("🏭 High-Performance Celery Worker Manager")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    if start_high_performance_workers():
        print("\n🎉 High-performance workers are ready!")
        print("💡 Performance Tips:")
        print("   - Workers are optimized for CPU and memory")
        print("   - Prefetch multiplier set to 1 for better load balancing")
        print("   - Workers restart every 1000 tasks to prevent memory leaks")
        print("   - Time limits prevent hanging tasks")
        print("\n📊 Monitor with Flower: http://localhost:5555")
        
        # Keep the script running
        try:
            while True:
                time.sleep(60)
                # Check if workers are still running
                from scraper import celery_app
                inspect = celery_app.control.inspect()
                active_workers = inspect.active()
                if not active_workers or len(active_workers) == 0:
                    print("⚠️  No workers detected, restarting...")
                    start_high_performance_workers()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down high-performance workers...")
    else:
        print("❌ Failed to start high-performance workers")
        sys.exit(1)

if __name__ == '__main__':
    main()
