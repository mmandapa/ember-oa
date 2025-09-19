#!/usr/bin/env python3
"""
Start multiple Flask workers with Gunicorn for high performance
"""

import os
import sys
import subprocess
import time
import psutil
from multiprocessing import cpu_count

def get_optimal_flask_config():
    """Calculate optimal Flask worker configuration"""
    cpu_cores = cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Calculate optimal workers based on CPU cores
    if memory_gb >= 16:
        workers = min(cpu_cores * 2, 8)  # Max 8 workers
        worker_class = 'gevent'  # Async workers for I/O bound tasks
        worker_connections = 1000
    elif memory_gb >= 8:
        workers = min(cpu_cores * 1.5, 6)  # Max 6 workers
        worker_class = 'gevent'
        worker_connections = 500
    else:
        workers = min(cpu_cores, 4)  # Max 4 workers
        worker_class = 'sync'  # Sync workers for lower memory
        worker_connections = 100
    
    return int(workers), worker_class, worker_connections

def start_flask_workers():
    """Start multiple Flask workers on different ports"""
    workers, worker_class, worker_connections = get_optimal_flask_config()
    
    print(f"🌐 Starting High-Performance Flask Workers")
    print(f"📊 Configuration:")
    print(f"   Workers: {workers}")
    print(f"   Worker Class: {worker_class}")
    print(f"   Worker Connections: {worker_connections}")
    print(f"   Ports: 8000-{8000 + workers - 1}")
    
    worker_processes = []
    
    try:
        for i in range(workers):
            port = 8000 + i
            print(f"🚀 Starting Flask worker {i+1}/{workers} on port {port}...")
            
            # Start Gunicorn worker
            cmd = [
                sys.executable, '-m', 'gunicorn',
                '--bind', f'127.0.0.1:{port}',
                '--workers', '1',  # One worker per port
                f'--worker-class={worker_class}',
                f'--worker-connections={worker_connections}',
                '--timeout', '300',  # 5 minutes
                '--keep-alive', '5',
                '--max-requests', '1000',
                '--max-requests-jitter', '100',
                '--preload',  # Preload app for better performance
                '--access-logfile', '-',
                '--error-logfile', '-',
                '--log-level', 'info',
                'app:app'
            ]
            
            process = subprocess.Popen(cmd, cwd=os.path.dirname(__file__))
            worker_processes.append((process, port))
            time.sleep(2)  # Stagger startup
        
        # Wait for workers to start
        time.sleep(10)
        
        # Verify workers are running
        import requests
        healthy_workers = 0
        
        for process, port in worker_processes:
            try:
                response = requests.get(f'http://127.0.0.1:{port}/api/health', timeout=5)
                if response.status_code == 200:
                    healthy_workers += 1
                    print(f"✅ Worker on port {port} is healthy")
                else:
                    print(f"❌ Worker on port {port} is not responding")
            except:
                print(f"❌ Worker on port {port} failed health check")
        
        if healthy_workers == workers:
            print(f"✅ All {workers} Flask workers are running and healthy")
            return worker_processes
        else:
            print(f"❌ Only {healthy_workers}/{workers} workers are healthy")
            return None
            
    except Exception as e:
        print(f"❌ Error starting Flask workers: {e}")
        # Clean up
        for process, port in worker_processes:
            try:
                process.terminate()
            except:
                pass
        return None

def main():
    print("🌐 High-Performance Flask Worker Manager")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    worker_processes = start_flask_workers()
    
    if worker_processes:
        print("\n🎉 High-performance Flask workers are ready!")
        print("📡 Workers are available on ports 8000-8003")
        print("🔧 Configure nginx to load balance between these ports")
        print("\n💡 Performance Benefits:")
        print("   - Multiple Flask workers for parallel request handling")
        print("   - Gunicorn with optimized worker classes")
        print("   - Preloaded applications for faster startup")
        print("   - Connection pooling and keep-alive")
        print("   - Automatic worker restarts to prevent memory leaks")
        
        # Keep the script running
        try:
            while True:
                time.sleep(30)
                # Check if workers are still running
                healthy_count = 0
                for process, port in worker_processes:
                    if process.poll() is None:  # Process is still running
                        try:
                            import requests
                            response = requests.get(f'http://127.0.0.1:{port}/api/health', timeout=2)
                            if response.status_code == 200:
                                healthy_count += 1
                        except:
                            pass
                
                if healthy_count < len(worker_processes):
                    print(f"⚠️  Only {healthy_count}/{len(worker_processes)} workers healthy, restarting...")
                    worker_processes = start_flask_workers()
                    if not worker_processes:
                        break
                        
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Flask workers...")
            for process, port in worker_processes:
                try:
                    process.terminate()
                    process.wait(timeout=10)
                except:
                    try:
                        process.kill()
                    except:
                        pass
    else:
        print("❌ Failed to start Flask workers")
        sys.exit(1)

if __name__ == '__main__':
    main()
