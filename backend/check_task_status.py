#!/usr/bin/env python3
"""
Script to check the status of a Celery task
"""
import sys
import json
from scraper import celery_app

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_task_status.py <task_id>")
        sys.exit(1)

    task_id = sys.argv[1]
    task = celery_app.AsyncResult(task_id)

    response = {
        'task_id': task.id,
        'status': task.status,
        'result': task.result,
        'info': task.info
    }
    
    # Handle non-serializable objects
    def safe_serialize(obj):
        if hasattr(obj, '__dict__'):
            return str(obj)
        return obj
    
    try:
        print(json.dumps(response, default=safe_serialize))
    except Exception as e:
        print(json.dumps({
            'task_id': task.id,
            'status': str(task.status),
            'result': str(task.result) if task.result else None,
            'info': str(task.info) if task.info else None,
            'error': str(e)
        }))
