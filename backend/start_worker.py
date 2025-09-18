#!/usr/bin/env python3
"""
Start Celery worker for the scraper
"""
import os
import sys
from celery import Celery
from scraper import celery_app

if __name__ == '__main__':
    # Start the worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=8',  # Increased worker processes for parallel processing
        '--hostname=scraper_worker@%h'
    ])