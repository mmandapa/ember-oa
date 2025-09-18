#!/usr/bin/env python3
"""
Script to start the Celery scrape task
"""
import os
from dotenv import load_dotenv
from scraper import scrape_all_policies_task

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    print("🚀 Starting PDF scraping task...")
    task = scrape_all_policies_task.delay()
    print(f"✅ Task started with ID: {task.id}")
    print("📊 Check progress at: http://localhost:5555")
    print(f"🔍 Or check status with: python check_task_status.py {task.id}")
