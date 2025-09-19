#!/usr/bin/env python3
"""
Progress Tracker for Real-time Scraping Updates
Provides detailed progress information to the frontend
"""

import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import redis
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProgressUpdate:
    """Structure for progress updates"""
    task_id: str
    status: str  # 'started', 'processing', 'completed', 'failed'
    current_step: int
    total_steps: int
    current_item: str
    items_processed: int
    items_total: int
    start_time: float
    estimated_completion: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[Dict] = None

class ProgressTracker:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=1)
        self.active_tasks = {}
        
    def start_task(self, task_id: str, total_items: int, task_type: str = "scraping") -> ProgressUpdate:
        """Start tracking a new task"""
        progress = ProgressUpdate(
            task_id=task_id,
            status='started',
            current_step=0,
            total_steps=total_items,
            current_item='Initializing...',
            items_processed=0,
            items_total=total_items,
            start_time=time.time(),
            details={'task_type': task_type}
        )
        
        self.active_tasks[task_id] = progress
        self._save_progress(progress)
        
        logger.info(f"🚀 Started tracking task {task_id} with {total_items} items")
        return progress
    
    def update_progress(self, task_id: str, current_item: str, items_processed: int, 
                      status: str = 'processing', details: Optional[Dict] = None) -> Optional[ProgressUpdate]:
        """Update progress for an active task"""
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return None
        
        progress = self.active_tasks[task_id]
        progress.status = status
        progress.current_item = current_item
        progress.items_processed = items_processed
        progress.current_step = items_processed
        
        if details:
            progress.details = details
        
        # Calculate estimated completion time
        if items_processed > 0:
            elapsed_time = time.time() - progress.start_time
            rate = items_processed / elapsed_time
            remaining_items = progress.items_total - items_processed
            progress.estimated_completion = time.time() + (remaining_items / rate)
        
        self._save_progress(progress)
        
        logger.info(f"📊 Progress update for {task_id}: {items_processed}/{progress.items_total} - {current_item}")
        return progress
    
    def complete_task(self, task_id: str, success: bool = True, error_message: Optional[str] = None) -> Optional[ProgressUpdate]:
        """Mark a task as completed"""
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return None
        
        progress = self.active_tasks[task_id]
        progress.status = 'completed' if success else 'failed'
        progress.current_item = 'Completed' if success else 'Failed'
        progress.items_processed = progress.items_total if success else progress.items_processed
        progress.current_step = progress.items_total if success else progress.current_step
        
        if error_message:
            progress.error_message = error_message
        
        self._save_progress(progress)
        
        # Keep completed task for a while for reference
        if success:
            logger.info(f"✅ Task {task_id} completed successfully")
        else:
            logger.error(f"❌ Task {task_id} failed: {error_message}")
        
        return progress
    
    def get_progress(self, task_id: str) -> Optional[ProgressUpdate]:
        """Get current progress for a task"""
        try:
            progress_data = self.redis_client.get(f"progress:{task_id}")
            if progress_data:
                data = json.loads(progress_data)
                return ProgressUpdate(**data)
        except Exception as e:
            logger.error(f"Error getting progress for {task_id}: {e}")
        return None
    
    def get_all_active_tasks(self) -> List[ProgressUpdate]:
        """Get all currently active tasks"""
        active_tasks = []
        try:
            keys = self.redis_client.keys("progress:*")
            for key in keys:
                progress_data = self.redis_client.get(key)
                if progress_data:
                    data = json.loads(progress_data)
                    progress = ProgressUpdate(**data)
                    if progress.status in ['started', 'processing']:
                        active_tasks.append(progress)
        except Exception as e:
            logger.error(f"Error getting active tasks: {e}")
        
        return active_tasks
    
    def _save_progress(self, progress: ProgressUpdate):
        """Save progress to Redis"""
        try:
            key = f"progress:{progress.task_id}"
            data = json.dumps(asdict(progress))
            self.redis_client.setex(key, 3600, data)  # Expire after 1 hour
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        try:
            keys = self.redis_client.keys("progress:*")
            current_time = time.time()
            
            for key in keys:
                progress_data = self.redis_client.get(key)
                if progress_data:
                    data = json.loads(progress_data)
                    progress = ProgressUpdate(**data)
                    
                    # Remove tasks older than max_age_hours
                    if current_time - progress.start_time > max_age_hours * 3600:
                        self.redis_client.delete(key)
                        logger.info(f"🧹 Cleaned up old task: {progress.task_id}")
        except Exception as e:
            logger.error(f"Error cleaning up old tasks: {e}")

# Global progress tracker instance
progress_tracker = ProgressTracker()

def get_task_progress_summary(task_id: str) -> Dict:
    """Get a summary of task progress for frontend display"""
    progress = progress_tracker.get_progress(task_id)
    
    if not progress:
        return {
            'state': 'PENDING',
            'current': 0,
            'total': 100,
            'status': 'Task not found or not started',
            'progress_percent': 0
        }
    
    progress_percent = int((progress.items_processed / progress.items_total) * 100) if progress.items_total > 0 else 0
    
    return {
        'state': progress.status.upper(),
        'current': progress.items_processed,
        'total': progress.items_total,
        'status': f"{progress.current_item} ({progress.items_processed}/{progress.items_total})",
        'progress_percent': progress_percent,
        'estimated_completion': progress.estimated_completion,
        'details': progress.details,
        'error': progress.error_message
    }

if __name__ == "__main__":
    # Test the progress tracker
    tracker = ProgressTracker()
    
    print("🧪 Testing Progress Tracker")
    print("=" * 50)
    
    # Start a test task
    task_id = "test_task_123"
    progress = tracker.start_task(task_id, 10, "test_scraping")
    print(f"Started task: {progress}")
    
    # Update progress
    for i in range(1, 6):
        tracker.update_progress(task_id, f"Processing item {i}", i)
        time.sleep(0.5)
    
    # Complete task
    tracker.complete_task(task_id, success=True)
    
    # Get final progress
    final_progress = tracker.get_progress(task_id)
    print(f"Final progress: {final_progress}")
    
    # Get summary for frontend
    summary = get_task_progress_summary(task_id)
    print(f"Frontend summary: {summary}")

