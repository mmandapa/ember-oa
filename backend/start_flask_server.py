#!/usr/bin/env python3
"""
Start Flask backend server
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting Flask Backend Server...")
    print("📡 This will replace Next.js API routes for better performance")
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Start Flask server
    try:
        # Use Gunicorn for production or Flask dev server for development
        if os.environ.get('FLASK_ENV') == 'production':
            print("🏭 Starting with Gunicorn (Production Mode)")
            subprocess.run([
                sys.executable, '-m', 'gunicorn',
                '--bind', '0.0.0.0:8000',
                '--workers', '4',
                '--worker-class', 'sync',
                '--timeout', '120',
                '--keep-alive', '2',
                '--max-requests', '1000',
                '--max-requests-jitter', '100',
                'app:app'
            ])
        else:
            print("🔧 Starting with Flask Dev Server (Development Mode)")
            subprocess.run([sys.executable, 'app.py'])
            
    except KeyboardInterrupt:
        print("\n🛑 Flask server stopped")
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
