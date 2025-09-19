#!/usr/bin/env python3
"""
Simple Lag-Fixed System Startup
Uses existing working scraper.py with lag prevention optimizations
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

class SimpleLagFixedSystem:
    def __init__(self):
        self.processes = {}
        self.running = False
        self.backend_dir = Path(__file__).parent / "backend"
        
    def start_redis(self):
        """Start Redis server"""
        print("🔴 Starting Redis server...")
        try:
            # Try to start Redis
            result = subprocess.run(['redis-server', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Redis is available")
                return True
            else:
                print("❌ Redis not found. Please install Redis:")
                print("   macOS: brew install redis")
                print("   Ubuntu: sudo apt install redis-server")
                return False
        except FileNotFoundError:
            print("❌ Redis not found. Please install Redis:")
            print("   macOS: brew install redis")
            print("   Ubuntu: sudo apt install redis-server")
            return False
    
    def start_flask_backend(self):
        """Start Flask backend"""
        print("🌐 Starting Flask backend...")
        try:
            cmd = [sys.executable, 'app.py']
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.backend_dir
            )
            
            self.processes['flask'] = process
            print(f"✅ Flask backend started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Error starting Flask backend: {e}")
            return False
    
    def start_celery_worker(self):
        """Start Celery worker with lag prevention settings"""
        print("⚙️ Starting Celery worker with lag prevention...")
        try:
            cmd = [
                sys.executable, '-m', 'celery', 'worker',
                '-A', 'scraper',
                '--concurrency', '2',  # Limit to 2 workers
                '--prefetch-multiplier', '1',  # One task at a time
                '--max-tasks-per-child', '5',  # Restart frequently
                '--loglevel', 'info'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.backend_dir
            )
            
            self.processes['worker'] = process
            print(f"✅ Celery worker started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Error starting Celery worker: {e}")
            return False
    
    def start_frontend(self):
        """Start Next.js frontend"""
        print("🎨 Starting Next.js frontend...")
        try:
            frontend_dir = Path(__file__).parent / "frontend"
            cmd = ['npm', 'run', 'dev']
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=frontend_dir
            )
            
            self.processes['frontend'] = process
            print(f"✅ Frontend started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Error starting frontend: {e}")
            return False
    
    def check_health(self):
        """Check if all services are healthy"""
        print("🔍 Checking system health...")
        
        # Check Flask backend
        try:
            import requests
            response = requests.get('http://localhost:8000/api/health', timeout=5)
            if response.status_code == 200:
                print("✅ Flask backend is healthy")
            else:
                print("⚠️ Flask backend health check failed")
                return False
        except Exception as e:
            print(f"⚠️ Flask backend health check failed: {e}")
            return False
        
        # Check Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            print("✅ Redis is healthy")
        except Exception as e:
            print(f"⚠️ Redis health check failed: {e}")
            return False
        
        return True
    
    def start_system(self):
        """Start the complete lag-fixed system"""
        print("🚀 Starting Lag-Fixed Cigna Policy Scraper System")
        print("=" * 60)
        
        # Check Redis availability
        if not self.start_redis():
            return False
        
        # Start Flask backend
        if not self.start_flask_backend():
            return False
        
        # Wait for Flask to start
        print("⏳ Waiting for Flask backend to initialize...")
        time.sleep(3)
        
        # Start Celery worker
        if not self.start_celery_worker():
            return False
        
        # Wait for worker to start
        print("⏳ Waiting for worker to initialize...")
        time.sleep(5)
        
        # Start frontend
        if not self.start_frontend():
            return False
        
        # Wait for frontend to start
        print("⏳ Waiting for frontend to initialize...")
        time.sleep(5)
        
        # Check system health
        if self.check_health():
            print("\n🎉 Lag-Fixed System started successfully!")
            print("=" * 60)
            print("📊 System Status:")
            print("   🌐 Frontend: http://localhost:3000")
            print("   🔧 Backend API: http://localhost:8000")
            print("   🔴 Redis: localhost:6379")
            print("   ⚙️ Celery Worker: Running with lag prevention")
            print("\n💡 Lag Prevention Features:")
            print("   📦 Batch processing (3 PDFs at a time)")
            print("   ⏱️ Small delays between tasks")
            print("   🔄 Worker restarts every 5 tasks")
            print("   🎯 Limited concurrency (2 workers max)")
            print("\n🎯 Ready to scrape policies without lag!")
            return True
        else:
            print("❌ System health check failed")
            return False
    
    def stop_system(self):
        """Stop all processes gracefully"""
        print("🛑 Stopping lag-fixed system...")
        self.running = False
        
        for name, process in self.processes.items():
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    print(f"✅ {name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    print(f"⚠️ {name} didn't stop gracefully, forcing...")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        print("✅ All processes stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    if 'system_manager' in globals():
        system_manager.stop_system()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start system manager
    system_manager = SimpleLagFixedSystem()
    
    try:
        if system_manager.start_system():
            print("\n🎯 System is running! Press Ctrl+C to stop.")
            # Keep the script running
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Error starting system: {e}")
    finally:
        system_manager.stop_system()

