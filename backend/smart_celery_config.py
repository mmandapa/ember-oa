#!/usr/bin/env python3
"""
Smart Celery Configuration with Resource-Aware Settings
Optimizes worker behavior based on system resources
"""

import os
from celery import Celery
from resource_monitor import resource_monitor

# Create Celery app with smart configuration
celery_app = Celery(
    'cigna_scraper_smart',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Smart configuration based on system resources
def get_smart_config():
    """Get Celery configuration optimized for current system resources"""
    optimal_workers = resource_monitor.get_optimal_worker_count()
    
    config = {
        # Basic settings
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'timezone': 'UTC',
        'enable_utc': True,
        
        # Worker settings optimized for resource management
        'worker_concurrency': optimal_workers,
        'worker_prefetch_multiplier': 1,  # Process one task at a time to prevent memory buildup
        'worker_max_tasks_per_child': 10,  # Restart workers after 10 tasks to prevent memory leaks
        
        # Task execution settings
        'task_acks_late': True,  # Acknowledge tasks only after completion
        'task_reject_on_worker_lost': True,  # Reject tasks if worker dies
        
        # Memory management
        'worker_max_memory_per_child': 200000,  # 200MB per worker (in KB)
        'worker_disable_rate_limits': True,  # Disable rate limits for better performance
        
        # Timeout settings
        'task_soft_time_limit': 300,  # 5 minutes soft limit
        'task_time_limit': 600,  # 10 minutes hard limit
        
        # Result backend settings
        'result_expires': 3600,  # Results expire after 1 hour
        'result_backend_max_retries': 3,
        
        # Queue settings for priority management
        'task_routes': {
            'scraper.process_individual_policy': {'queue': 'high_priority'},
            'scraper.process_single_pdf': {'queue': 'medium_priority'},
            'scraper.scrape_all_policies_task': {'queue': 'low_priority'},
        },
        
        # Broker settings
        'broker_connection_retry_on_startup': True,
        'broker_connection_retry': True,
        'broker_connection_max_retries': 10,
        
        # Worker optimization
        'worker_hijack_root_logger': False,  # Don't hijack root logger
        'worker_log_color': True,
        'worker_log_format': '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        'worker_task_log_format': '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    }
    
    return config

# Apply smart configuration
celery_app.conf.update(get_smart_config())

# Add resource-aware task decorator
def resource_aware_task(*args, **kwargs):
    """Decorator that adds resource awareness to Celery tasks"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check if processing should be throttled
            if resource_monitor.should_throttle_processing():
                # Sleep briefly to reduce resource pressure
                import time
                time.sleep(2)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Export the configured Celery app
__all__ = ['celery_app', 'resource_aware_task']

