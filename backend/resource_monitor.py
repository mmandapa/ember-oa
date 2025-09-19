#!/usr/bin/env python3
"""
Resource Monitor for Smart Celery Worker Management
Monitors system resources and dynamically adjusts worker behavior
"""

import psutil
import time
import os
import signal
import threading
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceMonitor:
    def __init__(self):
        self.cpu_threshold = 70.0  # CPU usage threshold (%)
        self.memory_threshold = 80.0  # Memory usage threshold (%)
        self.frontend_response_threshold = 2.0  # Frontend response time threshold (seconds)
        self.monitoring_active = False
        self.worker_processes = []
        self.circuit_breaker_active = False
        self.circuit_breaker_start_time = None
        self.circuit_breaker_duration = 60  # seconds
        
    def get_system_metrics(self) -> Dict:
        """Get current system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get process-specific metrics
            current_process = psutil.Process()
            process_memory = current_process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / 1024 / 1024 / 1024,
                'disk_percent': disk.percent,
                'process_memory_mb': process_memory,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def check_frontend_responsiveness(self) -> bool:
        """Check if frontend is responsive by testing API endpoint"""
        try:
            import requests
            start_time = time.time()
            response = requests.get('http://localhost:8000/api/health', timeout=5)
            response_time = time.time() - start_time
            
            return response.status_code == 200 and response_time < self.frontend_response_threshold
        except Exception as e:
            logger.warning(f"Frontend responsiveness check failed: {e}")
            return False
    
    def should_throttle_processing(self) -> bool:
        """Determine if processing should be throttled based on system metrics"""
        metrics = self.get_system_metrics()
        
        if not metrics:
            return True  # Err on the side of caution
        
        # Check if circuit breaker is active
        if self.circuit_breaker_active:
            if time.time() - self.circuit_breaker_start_time > self.circuit_breaker_duration:
                logger.info("🔓 Circuit breaker timeout reached, resuming normal operation")
                self.circuit_breaker_active = False
                self.circuit_breaker_start_time = None
            else:
                return True
        
        # Check resource thresholds
        cpu_high = metrics['cpu_percent'] > self.cpu_threshold
        memory_high = metrics['memory_percent'] > self.memory_threshold
        frontend_slow = not self.check_frontend_responsiveness()
        
        if cpu_high or memory_high or frontend_slow:
            logger.warning(f"⚠️ High resource usage detected - CPU: {metrics['cpu_percent']:.1f}%, "
                          f"Memory: {metrics['memory_percent']:.1f}%, Frontend responsive: {not frontend_slow}")
            
            # Activate circuit breaker if conditions persist
            if cpu_high and memory_high:
                self.activate_circuit_breaker()
            
            return True
        
        return False
    
    def activate_circuit_breaker(self):
        """Activate circuit breaker to prevent system overload"""
        if not self.circuit_breaker_active:
            logger.critical("🚨 Circuit breaker activated - stopping all processing")
            self.circuit_breaker_active = True
            self.circuit_breaker_start_time = time.time()
    
    def get_optimal_worker_count(self) -> int:
        """Calculate optimal number of workers based on system resources"""
        metrics = self.get_system_metrics()
        
        if not metrics:
            return 1  # Conservative default
        
        # Base calculation on available resources
        cpu_count = psutil.cpu_count()
        memory_gb = metrics['memory_available_gb']
        
        # Conservative calculation: 1 worker per 2 CPU cores, max 4 workers
        optimal_workers = min(cpu_count // 2, 4)
        
        # Reduce if memory is low
        if memory_gb < 2:
            optimal_workers = 1
        elif memory_gb < 4:
            optimal_workers = min(optimal_workers, 2)
        
        # Reduce if CPU usage is high
        if metrics['cpu_percent'] > 60:
            optimal_workers = max(1, optimal_workers - 1)
        
        return max(1, optimal_workers)
    
    def adjust_worker_priority(self, worker_pids: List[int], high_priority: bool = False):
        """Adjust worker process priority to prevent frontend lag"""
        try:
            for pid in worker_pids:
                try:
                    process = psutil.Process(pid)
                    if high_priority:
                        # Lower priority (higher nice value) for workers
                        os.nice(10)
                    else:
                        # Normal priority
                        os.nice(0)
                except (psutil.NoSuchProcess, PermissionError):
                    continue
        except Exception as e:
            logger.error(f"Error adjusting worker priority: {e}")
    
    def monitor_resources_continuously(self):
        """Continuously monitor resources and log metrics"""
        self.monitoring_active = True
        logger.info("🔍 Starting continuous resource monitoring")
        
        while self.monitoring_active:
            try:
                metrics = self.get_system_metrics()
                if metrics:
                    logger.info(f"📊 Resources - CPU: {metrics['cpu_percent']:.1f}%, "
                              f"Memory: {metrics['memory_percent']:.1f}%, "
                              f"Available: {metrics['memory_available_gb']:.1f}GB")
                
                # Check if throttling is needed
                if self.should_throttle_processing():
                    logger.warning("⚠️ Throttling recommended due to high resource usage")
                
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                logger.info("🛑 Resource monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(5)
        
        self.monitoring_active = False

# Global resource monitor instance
resource_monitor = ResourceMonitor()

def start_resource_monitoring():
    """Start resource monitoring in a separate thread"""
    monitor_thread = threading.Thread(target=resource_monitor.monitor_resources_continuously)
    monitor_thread.daemon = True
    monitor_thread.start()
    return monitor_thread

if __name__ == "__main__":
    # Test the resource monitor
    monitor = ResourceMonitor()
    print("🔍 Testing Resource Monitor")
    print("=" * 50)
    
    metrics = monitor.get_system_metrics()
    print(f"System Metrics: {metrics}")
    
    optimal_workers = monitor.get_optimal_worker_count()
    print(f"Optimal Worker Count: {optimal_workers}")
    
    should_throttle = monitor.should_throttle_processing()
    print(f"Should Throttle: {should_throttle}")
    
    print("\n🔍 Starting continuous monitoring (Ctrl+C to stop)...")
    monitor.monitor_resources_continuously()

