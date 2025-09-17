#!/usr/bin/env python3
"""
Main entry point for running the Cigna Policy Scraper
This script provides a simple interface to run the scraper with proper error handling
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from scraper.main_scraper import CignaPolicyScraper
from database.supabase_client import supabase_client
from scraper.error_handler import ErrorHandler

async def main():
    """Main function to run the scraper with proper setup and error handling"""
    
    print("🏥 Cigna Policy Scraper")
    print("=" * 50)
    
    # Load environment variables
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print("✅ Environment variables loaded")
    else:
        print("⚠️  No .env file found. Please create one from env.example")
        return
    
    # Check required environment variables
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with the required Supabase credentials")
        return
    
    try:
        # Initialize error handler
        error_handler = ErrorHandler()
        
        # Initialize database
        print("🔗 Connecting to Supabase database...")
        await supabase_client.initialize_database()
        print("✅ Database connection established")
        
        # Create and run scraper
        print("🚀 Starting policy scraping...")
        scraper = CignaPolicyScraper()
        
        summary = await scraper.scrape_all_policies()
        
        # Display results
        print("\n📊 Scraping Results:")
        print("=" * 30)
        print(f"📄 Total Monthly Pages: {summary['total_monthly_pages']}")
        print(f"📋 Total Policies Scraped: {summary['total_policies_scraped']}")
        print(f"❌ Total Errors: {summary['total_errors']}")
        print(f"⏱️  Execution Time: {summary['execution_time']:.2f} seconds")
        
        # Monthly breakdown
        if summary['monthly_summaries']:
            print("\n📅 Monthly Breakdown:")
            for month_summary in summary['monthly_summaries'][:5]:  # Show first 5
                print(f"  • {month_summary['month_year']}: {month_summary['policies_scraped']} policies")
            
            if len(summary['monthly_summaries']) > 5:
                print(f"  ... and {len(summary['monthly_summaries']) - 5} more months")
        
        # Success message
        if summary['total_policies_scraped'] > 0:
            print(f"\n🎉 Successfully scraped {summary['total_policies_scraped']} policy updates!")
            print("🌐 You can now view the results in the web interface:")
            print("   cd frontend && npm run dev")
            print("   Then open http://localhost:3000")
        else:
            print("\n⚠️  No policies were scraped. Check the logs for errors.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        print("Check the logs/scraper.log file for detailed error information")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
