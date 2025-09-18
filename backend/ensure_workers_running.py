#!/usr/bin/env python3
"""
Ensure Celery workers are running for parallel processing
"""
import subprocess
import sys
import time
import redis

def check_redis():
    """Check if Redis is running"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except:
        return False

def count_workers():
    """Count running Celery workers using ps command"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        count = 0
        for line in lines:
            if 'start_worker.py' in line and 'python' in line:
                count += 1
        return count
    except:
        return 0

def start_workers():
    """Start workers if needed"""
    current_workers = count_workers()
    target_workers = 3  # Start 3 workers for parallel processing
    
    if current_workers >= target_workers:
        print(f"✅ {current_workers} workers already running")
        return True
    
    print(f"👷 Starting {target_workers - current_workers} additional workers...")
    
    for i in range(target_workers - current_workers):
        try:
            subprocess.Popen([
                sys.executable, 'start_worker.py'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
        except Exception as e:
            print(f"❌ Failed to start worker: {e}")
            return False
    
    # Verify workers started
    time.sleep(2)
    final_count = count_workers()
    print(f"✅ {final_count} workers now running")
    return final_count >= target_workers

def main():
    print("🔍 Checking parallel processing system...")
    
    # Check Redis
    if not check_redis():
        print("❌ Redis is not running. Please start Redis first:")
        print("   redis-server")
        return False
    
    print("✅ Redis is running")
    
    # Check and start workers
    if not start_workers():
        print("❌ Failed to start workers")
        return False
    
    print("🎉 Parallel processing system is ready!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
