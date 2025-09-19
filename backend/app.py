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
from scraper import celery_app, scrape_all_policies_task, scrape_selected_policies_task, CignaPolicyScraper

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

@app.route('/api/monthly-pdfs', methods=['GET'])
def get_monthly_pdfs():
    """
    Fetch available monthly PDFs from Cigna
    """
    try:
        scraper = CignaPolicyScraper()
        monthly_links = scraper.fetch_monthly_links()
        
        if not monthly_links:
            return jsonify({
                'success': False,
                'message': 'No monthly PDFs found',
                'data': []
            }), 500
        
        # Format the data for frontend
        formatted_links = []
        for link in monthly_links:
            formatted_links.append({
                'value': link['url'],
                'label': link['month_year'],
                'url': link['url']
            })
        
        return jsonify({
            'success': True,
            'message': f'Found {len(formatted_links)} monthly PDFs',
            'data': formatted_links
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching monthly PDFs: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        }), 500

@app.route('/api/policy-options', methods=['GET'])
def get_policy_options():
    """
    Fetch all available policy options from the main Cigna page
    """
    try:
        scraper = CignaPolicyScraper()
        policy_options = scraper.fetch_all_policy_options()
        
        if not policy_options:
            return jsonify({
                'success': False,
                'message': 'No policy options found',
                'data': []
            }), 500
        
        # Format the data for frontend
        formatted_options = []
        for option in policy_options:
            formatted_options.append({
                'value': option['url'],
                'label': option['title'],
                'url': option['url'],
                'category': option['category'],
                'is_pdf': option['is_pdf']
            })
        
        return jsonify({
            'success': True,
            'message': f'Found {len(formatted_options)} policy options',
            'data': formatted_options
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching policy options: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        }), 500

@app.route('/api/scrape-async', methods=['POST'])
def start_scraping():
    """
    Start the parallel scraping process with optional month selection
    Replaces the Next.js API route with Flask
    """
    try:
        # Get selected options from request body
        data = request.get_json() or {}
        selected_options = data.get('selected_options', [])
        selected_months = data.get('selected_months', [])  # Keep backward compatibility
        
        print("🏭 Starting scraping process...")
        print(f"📋 Received selected_options: {len(selected_options)} items")
        print(f"📋 Received selected_months: {len(selected_months)} items")
        if selected_options:
            print(f"🎯 First few selected options: {selected_options[:3]}")
        
        # Check if Celery workers are running
        try:
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            if not active_workers:
                print("❌ No Celery workers found! Please start workers first.")
                return jsonify({
                    'success': False,
                    'message': 'No Celery workers available. Please start the backend services first.'
                }), 500
            else:
                print(f"✅ Found {len(active_workers)} active Celery workers")
        except Exception as e:
            print(f"❌ Could not check workers: {e}")
            return jsonify({
                'success': False,
                'message': 'Could not connect to Celery workers. Please check backend services.'
            }), 500
        
        print("✅ Starting scraping task...")
        
        # Start the scraping task with selected options or months
        if selected_options:
            # Pass the selected options to the task
            task = scrape_selected_policies_task.delay(selected_options)
            message = f'Scraping task started for {len(selected_options)} selected policy options'
        elif selected_months:
            task = scrape_selected_policies_task.delay(selected_months)
            message = f'Scraping task started for {len(selected_months)} selected months'
        else:
            task = scrape_all_policies_task.delay()
            message = 'Scraping task started for all available options'
        
        return jsonify({
            'success': True,
            'message': message,
            'task_id': task.id,
            'selected_options': selected_options,
            'selected_months': selected_months
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
        elif task.state == 'SUCCESS':
            # Check if this is a dispatched task (parallel processing)
            if task.result and isinstance(task.result, dict) and task.result.get('status') == 'dispatched':
                # Count completed individual tasks
                group_id = task.result.get('group_id')
                if group_id:
                    try:
                        group_result = celery_app.GroupResult.restore(group_id)
                        if group_result:
                            completed = sum(1 for r in group_result.results if r.state == 'SUCCESS')
                            total = len(group_result.results) if group_result.results else 0
                            
                            if completed >= total and total > 0:
                                response = {
                                    'state': 'SUCCESS',
                                    'current': completed,
                                    'total': total,
                                    'status': f'Completed {completed}/{total} policies',
                                    'result': task.result
                                }
                            else:
                                response = {
                                    'state': 'PROGRESS',
                                    'current': completed,
                                    'total': total,
                                    'status': f'Processing {completed}/{total} policies in parallel...',
                                    'result': task.result
                                }
                        else:
                            response = {
                                'state': 'PROGRESS',
                                'current': 0,
                                'total': task.result.get('total_pdfs', 100),
                                'status': 'Processing policies in parallel...',
                                'result': task.result
                            }
                    except Exception as e:
                        response = {
                            'state': 'PROGRESS',
                            'current': 0,
                            'total': task.result.get('total_pdfs', 100),
                            'status': 'Processing policies in parallel...',
                            'result': task.result
                        }
                else:
                    response = {
                        'state': 'PROGRESS',
                        'current': 0,
                        'total': task.result.get('total_pdfs', 100),
                        'status': 'Processing policies in parallel...',
                        'result': task.result
                    }
            else:
                response = {
                    'state': task.state,
                    'current': task.info.get('current', 0) if task.info else 0,
                    'total': task.info.get('total', 100) if task.info else 100,
                    'status': task.info.get('status', '') if task.info else '',
                    'result': task.result if task.result else None
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

@app.route('/api/pause-scraper', methods=['POST'])
def pause_scraper():
    """
    Pause the scraper by revoking active tasks
    """
    try:
        print("⏸️ Pausing scraper...")
        
        # Get active tasks
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return jsonify({
                'success': False,
                'message': 'No active tasks to pause'
            }), 400
        
        # Revoke all active tasks
        revoked_count = 0
        for worker, tasks in active_tasks.items():
            for task in tasks:
                celery_app.control.revoke(task['id'], terminate=True)
                revoked_count += 1
                print(f"🛑 Revoked task {task['id']} from worker {worker}")
        
        print(f"✅ Paused {revoked_count} active tasks")
        
        return jsonify({
            'success': True,
            'message': f'Paused {revoked_count} active tasks',
            'revoked_count': revoked_count
        }), 200
        
    except Exception as e:
        print(f"❌ Error pausing scraper: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/resume-scraper', methods=['POST'])
def resume_scraper():
    """
    Resume the scraper (this would require restarting tasks)
    """
    try:
        print("▶️ Resume scraper requested...")
        
        # Check if there are any active tasks
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if active_tasks:
            active_count = sum(len(tasks) for tasks in active_tasks.values())
            return jsonify({
                'success': True,
                'message': f'Scraper is already running with {active_count} active tasks',
                'active_count': active_count
            }), 200
        
        # If no active tasks, suggest restarting the scraper
        return jsonify({
            'success': True,
            'message': 'No active tasks found. Please restart the scraper to resume processing.',
            'suggestion': 'restart_scraper'
        }), 200
        
    except Exception as e:
        print(f"❌ Error resuming scraper: {e}")
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
    print("   POST /api/pause-scraper - Pause active tasks")
    print("   POST /api/resume-scraper - Resume scraper")
    print("🌐 Server will be available at: http://localhost:8000")
    
    # Run with Gunicorn for production or Flask dev server for development
    if os.environ.get('FLASK_ENV') == 'production':
        # Production mode with Gunicorn
        app.run(host='0.0.0.0', port=8000, debug=False)
    else:
        # Development mode
        app.run(host='0.0.0.0', port=8000, debug=True)
