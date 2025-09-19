#!/usr/bin/env python3
"""
Flask Backend for Cigna Policy Scraper
Replaces Next.js API routes with efficient Flask server
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import sys
import os
import json
from scraper import celery_app, scrape_all_policies_task

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

@app.route('/api/scrape-async', methods=['POST'])
def start_scraping():
    """
    Start the parallel scraping process
    Replaces the Next.js API route with Flask
    """
    try:
        print("🏭 Starting complete parallel processing system...")
        
        # Start the complete system (Redis + Workers)
        start_everything_path = os.path.join(os.path.dirname(__file__), 'start_everything.py')
        result = subprocess.run([sys.executable, start_everything_path], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Failed to start parallel processing system. Please ensure Redis is installed and running.',
                'error': result.stderr
            }), 500
        
        print("✅ Parallel processing system is ready, starting scraping task...")
        
        # Start the scraping task
        task = scrape_all_policies_task.delay()
        
        return jsonify({
            'success': True,
            'message': 'Parallel scraping task started with multiple workers',
            'task_id': task.id
        }), 200
        
    except Exception as e:
        print(f"❌ Error starting scraper: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Get the status of a Celery task
    Replaces the Next.js API route with Flask
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'current': 0,
                'total': 100,
                'status': 'Task is waiting to be processed...'
            }
        elif task.state != 'FAILURE':
            response = {
                'state': task.state,
                'current': task.info.get('current', 0) if task.info else 0,
                'total': task.info.get('total', 100) if task.info else 100,
                'status': task.info.get('status', '') if task.info else '',
                'result': task.result if task.result else None
            }
        else:
            # Task failed
            response = {
                'state': task.state,
                'current': 0,
                'total': 100,
                'status': str(task.info),
                'error': str(task.info)
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"❌ Error checking task status: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    try:
        # Check if Redis is running
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        
        # Check if Celery workers are running
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        return jsonify({
            'status': 'healthy',
            'redis': 'connected',
            'celery_workers': len(active_workers) if active_workers else 0,
            'workers': list(active_workers.keys()) if active_workers else []
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/system-status', methods=['GET'])
def system_status():
    """
    Get detailed system status
    """
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Redis info
        redis_info = r.info()
        
        # Celery worker info
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()
        
        return jsonify({
            'redis': {
                'connected': True,
                'memory_used': redis_info.get('used_memory_human', 'N/A'),
                'connected_clients': redis_info.get('connected_clients', 0),
                'total_commands_processed': redis_info.get('total_commands_processed', 0)
            },
            'celery': {
                'active_workers': len(active_workers) if active_workers else 0,
                'workers': list(active_workers.keys()) if active_workers else [],
                'stats': stats if stats else {}
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/clear-data', methods=['POST'])
def clear_data():
    """
    Clear all scraped data from the database
    """
    try:
        from supabase import create_client, Client
        import os
        
        # Initialize Supabase client
        supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        supabase_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            return jsonify({
                'success': False,
                'message': 'Supabase credentials not configured'
            }), 500
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Clear data in order (respecting foreign key constraints)
        tables_to_clear = [
            'medical_codes',
            'referenced_documents', 
            'document_changes',
            'policy_updates'
        ]
        
        cleared_counts = {}
        
        for table in tables_to_clear:
            try:
                # Delete all records from table
                result = supabase.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                cleared_counts[table] = len(result.data) if result.data else 0
                print(f"✅ Cleared {cleared_counts[table]} records from {table}")
            except Exception as e:
                print(f"❌ Error clearing {table}: {e}")
                cleared_counts[table] = f"Error: {str(e)}"
        
        total_cleared = sum(count for count in cleared_counts.values() if isinstance(count, int))
        
        return jsonify({
            'success': True,
            'message': f'Successfully cleared {total_cleared} records from database',
            'details': cleared_counts
        }), 200
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Flask backend server...")
    print("📡 API Endpoints:")
    print("   POST /api/scrape-async - Start scraping")
    print("   GET  /api/task-status/<task_id> - Check task status")
    print("   GET  /api/health - Health check")
    print("   GET  /api/system-status - System status")
    print("🌐 Server will be available at: http://localhost:8000")
    
    # Run with Gunicorn for production or Flask dev server for development
    if os.environ.get('FLASK_ENV') == 'production':
        # Production mode with Gunicorn
        app.run(host='0.0.0.0', port=8000, debug=False)
    else:
        # Development mode
        app.run(host='0.0.0.0', port=8000, debug=True)
