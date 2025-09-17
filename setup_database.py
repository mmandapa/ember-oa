#!/usr/bin/env python3
"""
Database setup script for Cigna Policy Scraper
Creates all required tables in Supabase
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def setup_database():
    """Create all required database tables"""
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ Missing Supabase credentials in .env file")
        return False
    
    try:
        client = create_client(url, key)
        print("✅ Connected to Supabase")
        
        # SQL commands to create tables
        sql_commands = [
            """
            CREATE TABLE IF NOT EXISTS policy_updates (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                published_date TIMESTAMP WITH TIME ZONE,
                category TEXT,
                body_content TEXT,
                month_year TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS referenced_documents (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                policy_update_id UUID REFERENCES policy_updates(id) ON DELETE CASCADE,
                document_title TEXT NOT NULL,
                document_url TEXT,
                document_type TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS medical_codes (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                policy_update_id UUID REFERENCES policy_updates(id) ON DELETE CASCADE,
                code TEXT NOT NULL,
                code_type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS document_changes (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                policy_update_id UUID REFERENCES policy_updates(id) ON DELETE CASCADE,
                document_title TEXT NOT NULL,
                change_type TEXT NOT NULL,
                change_description TEXT,
                section_affected TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS scraping_logs (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                records_scraped INTEGER DEFAULT 0,
                execution_time FLOAT DEFAULT 0.0,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
        ]
        
        # Create indexes
        index_commands = [
            "CREATE INDEX IF NOT EXISTS idx_policy_updates_month_year ON policy_updates(month_year);",
            "CREATE INDEX IF NOT EXISTS idx_policy_updates_published_date ON policy_updates(published_date);",
            "CREATE INDEX IF NOT EXISTS idx_medical_codes_code_type ON medical_codes(code_type);",
            "CREATE INDEX IF NOT EXISTS idx_medical_codes_policy_id ON medical_codes(policy_update_id);",
            "CREATE INDEX IF NOT EXISTS idx_referenced_docs_policy_id ON referenced_documents(policy_update_id);",
            "CREATE INDEX IF NOT EXISTS idx_document_changes_policy_id ON document_changes(policy_update_id);",
            "CREATE INDEX IF NOT EXISTS idx_scraping_logs_timestamp ON scraping_logs(timestamp);"
        ]
        
        print("🔨 Creating database tables...")
        
        # Execute table creation commands
        for i, sql in enumerate(sql_commands, 1):
            try:
                result = client.rpc('exec_sql', {'sql': sql}).execute()
                print(f"✅ Table {i}/5 created successfully")
            except Exception as e:
                print(f"❌ Error creating table {i}: {e}")
                # Try alternative method
                try:
                    # For some Supabase setups, we might need to use the SQL editor
                    print(f"⚠️  Please run this SQL in your Supabase SQL editor:")
                    print(sql)
                    print("---")
                except:
                    pass
        
        print("🔨 Creating database indexes...")
        
        # Execute index creation commands
        for i, sql in enumerate(index_commands, 1):
            try:
                result = client.rpc('exec_sql', {'sql': sql}).execute()
                print(f"✅ Index {i}/7 created successfully")
            except Exception as e:
                print(f"❌ Error creating index {i}: {e}")
                print(f"⚠️  Please run this SQL in your Supabase SQL editor:")
                print(sql)
                print("---")
        
        print("\n🎉 Database setup completed!")
        print("\n📝 Manual Setup Required:")
        print("If any tables failed to create, please run the SQL commands above")
        print("in your Supabase SQL editor at: https://supabase.com/dashboard")
        print(f"Project URL: {url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Cigna Policy Scraper - Database Setup")
    print("=" * 50)
    
    success = setup_database()
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print("🚀 You can now run the scraper: python run_scraper.py")
    else:
        print("\n❌ Database setup failed!")
        print("Please check your Supabase credentials and try again.")
        sys.exit(1)
