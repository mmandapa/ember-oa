#!/usr/bin/env python3
"""
Start the complete high-performance Cigna Policy Scraper system
- Multiple Flask workers with nginx load balancing
- High-performance Celery workers
- Redis optimization
- Performance monitoring
"""

import os
import sys
import subprocess
import time
import signal
import threading
import psutil
from multiprocessing import cpu_count

def check_redis():
    """Check if Redis is running and optimize it"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        
        # Optimize Redis for high performance
        r.config_set('maxmemory-policy', 'allkeys-lru')
        r.config_set('tcp-keepalive', '60')
        r.config_set('timeout', '300')
        
        print("✅ Redis is running and optimized")
        return True
    except:
        print("🚀 Starting optimized Redis server...")
        try:
            # Start Redis with optimized configuration
            subprocess.Popen([
                'redis-server',
                '--maxmemory', '2gb',
                '--maxmemory-policy', 'allkeys-lru',
                '--tcp-keepalive', '60',
                '--timeout', '300',
                '--save', '900 1',  # Save every 15 minutes if at least 1 key changed
                '--save', '300 10', # Save every 5 minutes if at least 10 keys changed
                '--save', '60 10000' # Save every minute if at least 10000 keys changed
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(5)
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            print("✅ Optimized Redis started successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to start Redis: {e}")
            return False

def start_nginx():
    """Start nginx load balancer"""
    print("🌐 Starting nginx load balancer...")
    try:
        # Check if nginx is already running
        result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Nginx configuration error: {result.stderr}")
            return False
        
        # Start nginx
        subprocess.Popen(['nginx'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        
        # Test nginx
        import requests
        response = requests.get('http://localhost/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ Nginx load balancer started successfully")
            return True
        else:
            print("❌ Nginx not responding")
            return False
            
    except Exception as e:
        print(f"❌ Error starting nginx: {e}")
        return False

def start_high_performance_workers():
    """Start high-performance Celery workers"""
    print("👷 Starting high-performance Celery workers...")
    try:
        subprocess.Popen([
            sys.executable, 'start_high_performance_workers.py'
        ], cwd=os.path.join(os.path.dirname(__file__), 'backend'))
        
        # Give workers time to start
        time.sleep(15)
        
        # Verify workers
        from backend.scraper import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers and len(active_workers) > 0:
            print(f"✅ Started {len(active_workers)} high-performance Celery workers")
            return True
        else:
            print("❌ Failed to start Celery workers")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Celery workers: {e}")
        return False

def start_flask_workers():
    """Start multiple Flask workers"""
    print("🌐 Starting multiple Flask workers...")
    try:
        subprocess.Popen([
            sys.executable, 'start_multiple_flask_workers.py'
        ], cwd=os.path.join(os.path.dirname(__file__), 'backend'))
        
        # Give workers time to start
        time.sleep(10)
        
        # Verify Flask workers
        import requests
        healthy_workers = 0
        for port in range(8000, 8004):
            try:
                response = requests.get(f'http://127.0.0.1:{port}/api/health', timeout=5)
                if response.status_code == 200:
                    healthy_workers += 1
            except:
                pass
        
        if healthy_workers >= 2:
            print(f"✅ Started {healthy_workers} Flask workers")
            return True
        else:
            print("❌ Failed to start Flask workers")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Flask workers: {e}")
        return False

def show_system_status():
    """Show comprehensive system status"""
    print("\n📊 High-Performance System Status:")
    print("=" * 50)
    
    # System resources
    cpu_cores = cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    
    print(f"🖥️  System Resources:")
    print(f"   CPU: {cpu_cores} cores ({cpu_percent}% usage)")
    print(f"   Memory: {memory_gb:.1f} GB ({memory_percent}% usage)")
    
    # Redis status
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        redis_info = r.info()
        print(f"📦 Redis: ✅ Connected ({redis_info['used_memory_human']})")
    except:
        print(f"📦 Redis: ❌ Not connected")
    
    # Celery workers
    try:
        from backend.scraper import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()
        
        if active_workers:
            total_processes = sum(worker.get('pool', {}).get('processes', 0) for worker in stats.values())
            print(f"👷 Celery Workers: ✅ {len(active_workers)} workers ({total_processes} processes)")
        else:
            print(f"👷 Celery Workers: ❌ No workers")
    except:
        print(f"👷 Celery Workers: ❌ Error checking")
    
    # Flask workers
    try:
        import requests
        healthy_flask = 0
        for port in range(8000, 8004):
            try:
                response = requests.get(f'http://127.0.0.1:{port}/api/health', timeout=2)
                if response.status_code == 200:
                    healthy_flask += 1
            except:
                pass
        print(f"🌐 Flask Workers: ✅ {healthy_flask} workers")
    except:
        print(f"🌐 Flask Workers: ❌ Error checking")
    
    # Nginx
    try:
        import requests
        response = requests.get('http://localhost/api/health', timeout=2)
        if response.status_code == 200:
            print(f"🔀 Nginx Load Balancer: ✅ Running")
        else:
            print(f"🔀 Nginx Load Balancer: ❌ Not responding")
    except:
        print(f"🔀 Nginx Load Balancer: ❌ Not running")

def main():
    print("🚀 Starting High-Performance Cigna Policy Scraper System")
    print("=" * 60)
    
    # Change to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Start components in order
    if not check_redis():
        print("❌ Cannot start system without Redis")
        sys.exit(1)
    
    if not start_high_performance_workers():
        print("❌ Cannot start system without Celery workers")
        sys.exit(1)
    
    if not start_flask_workers():
        print("❌ Cannot start system without Flask workers")
        sys.exit(1)
    
    if not start_nginx():
        print("❌ Cannot start system without nginx")
        sys.exit(1)
    
    print("\n🎉 High-Performance System Started Successfully!")
    print("=" * 60)
    
    show_system_status()
    
    print("\n🌐 Access Points:")
    print("   Frontend: http://localhost:3000")
    print("   API (via nginx): http://localhost/api/")
    print("   Direct Flask: http://localhost:8000-8003")
    print("   Flower (Celery): http://localhost:5555")
    print("   Nginx Status: http://localhost/nginx_status")
    
    print("\n🎯 Performance Features:")
    print("   ✅ Multiple Flask workers (load balanced)")
    print("   ✅ High-performance Celery workers")
    print("   ✅ Nginx load balancing & caching")
    print("   ✅ Redis optimization")
    print("   ✅ Rate limiting & security")
    print("   ✅ Automatic failover")
    
    print("\n💡 Expected Performance:")
    cpu_cores = cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    if memory_gb >= 16:
        print(f"   📈 High-end system: {cpu_cores * 2} Celery workers, 4 Flask workers")
        print(f"   ⚡ Expected: 50-100 PDFs/minute processing speed")
    elif memory_gb >= 8:
        print(f"   📈 Medium system: {int(cpu_cores * 1.5)} Celery workers, 3 Flask workers")
        print(f"   ⚡ Expected: 30-60 PDFs/minute processing speed")
    else:
        print(f"   📈 Standard system: {cpu_cores} Celery workers, 2 Flask workers")
        print(f"   ⚡ Expected: 20-40 PDFs/minute processing speed")
    
    print("\n🛑 Press Ctrl+C to stop all services")
    
    # Keep the script running
    try:
        while True:
            time.sleep(60)
            show_system_status()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down high-performance system...")
        # Kill all processes
        subprocess.run(['pkill', '-f', 'nginx'], capture_output=True)
        subprocess.run(['pkill', '-f', 'redis-server'], capture_output=True)
        subprocess.run(['pkill', '-f', 'start_high_performance_workers'], capture_output=True)
        subprocess.run(['pkill', '-f', 'start_multiple_flask_workers'], capture_output=True)
        subprocess.run(['pkill', '-f', 'gunicorn'], capture_output=True)
        subprocess.run(['pkill', '-f', 'celery'], capture_output=True)
        print("✅ High-performance system stopped")

if __name__ == '__main__':
    main()
