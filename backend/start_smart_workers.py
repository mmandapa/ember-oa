#!/usr/bin/env python3
"""
Smart Celery Worker Startup Script
Starts workers with optimal configuration based on system resources
"""

import os
import sys
import subprocess
import time
import signal
import threading
from resource_monitor import resource_monitor, start_resource_monitoring
from smart_celery_config import celery_app

class SmartWorkerManager:
    def __init__(self):
        self.worker_processes = []
        self.monitoring_thread = None
        self.running = False
        
    def start_workers(self):
        """Start Celery workers with smart configuration"""
        print("🚀 Starting Smart Celery Workers")
        print("=" * 50)
        
        # Get optimal worker count
        optimal_workers = resource_monitor.get_optimal_worker_count()
        print(f"📊 Optimal worker count: {optimal_workers}")
        
        # Start resource monitoring
        self.monitoring_thread = start_resource_monitoring()
        
        # Start workers
        for i in range(optimal_workers):
            self.start_single_worker(i)
        
        self.running = True
        print(f"✅ Started {optimal_workers} smart workers")
        
        # Monitor and adjust workers
        self.monitor_and_adjust()
    
    def start_single_worker(self, worker_id):
        """Start a single Celery worker"""
        try:
            # Worker configuration
            worker_name = f"smart_worker_{worker_id}"
            concurrency = 1  # One task at a time to prevent memory buildup
            
            # Start worker process
            cmd = [
                sys.executable, '-m', 'celery', 'worker',
                '-A', 'smart_celery_config',
                '-n', worker_name,
                '--concurrency', str(concurrency),
                '--loglevel', 'info',
                '--queues', 'high_priority,medium_priority,low_priority',
                '--prefetch-multiplier', '1',
                '--max-tasks-per-child', '10',
                '--max-memory-per-child', '200000'  # 200MB
            ]
            
            print(f"🔧 Starting worker {worker_name} with concurrency {concurrency}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(__file__)
            )
            
            self.worker_processes.append({
                'process': process,
                'name': worker_name,
                'worker_id': worker_id
            })
            
            print(f"✅ Worker {worker_name} started (PID: {process.pid})")
            
        except Exception as e:
            print(f"❌ Error starting worker {worker_id}: {e}")
    
    def monitor_and_adjust(self):
        """Monitor system resources and adjust workers accordingly"""
        print("🔍 Starting worker monitoring and adjustment")
        
        while self.running:
            try:
                # Check if processing should be throttled
                if resource_monitor.should_throttle_processing():
                    print("⚠️ High resource usage detected - throttling workers")
                    self.throttle_workers()
                else:
                    print("✅ System resources normal - workers running optimally")
                
                # Check worker health
                self.check_worker_health()
                
                # Sleep before next check
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n🛑 Worker monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in worker monitoring: {e}")
                time.sleep(10)
    
    def throttle_workers(self):
        """Throttle worker activity to reduce resource usage"""
        try:
            # Reduce worker priority
            for worker_info in self.worker_processes:
                try:
                    process = worker_info['process']
                    if process.poll() is None:  # Process is still running
                        os.nice(10)  # Lower priority
                except Exception as e:
                    print(f"⚠️ Error adjusting worker priority: {e}")
        except Exception as e:
            print(f"❌ Error throttling workers: {e}")
    
    def check_worker_health(self):
        """Check if all workers are healthy and restart if needed"""
        healthy_workers = []
        
        for worker_info in self.worker_processes:
            process = worker_info['process']
            worker_id = worker_info['worker_id']
            worker_name = worker_info['name']
            
            if process.poll() is None:
                # Worker is still running
                healthy_workers.append(worker_info)
            else:
                # Worker died, restart it
                print(f"⚠️ Worker {worker_name} died, restarting...")
                self.start_single_worker(worker_id)
        
        self.worker_processes = healthy_workers
    
    def stop_workers(self):
        """Stop all workers gracefully"""
        print("🛑 Stopping smart workers...")
        self.running = False
        
        for worker_info in self.worker_processes:
            process = worker_info['process']
            worker_name = worker_info['name']
            
            try:
                print(f"🛑 Stopping worker {worker_name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    print(f"✅ Worker {worker_name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    print(f"⚠️ Worker {worker_name} didn't stop gracefully, forcing...")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                print(f"❌ Error stopping worker {worker_name}: {e}")
        
        print("✅ All workers stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    if 'worker_manager' in globals():
        worker_manager.stop_workers()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start worker manager
    worker_manager = SmartWorkerManager()
    
    try:
        worker_manager.start_workers()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Error starting workers: {e}")
    finally:
        worker_manager.stop_workers()

