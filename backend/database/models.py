"""
Database models and schemas for Cigna Policy Scraper
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class PolicyUpdate:
    """Main policy update record"""
    id: Optional[str] = None
    title: str = ""
    url: str = ""
    published_date: Optional[datetime] = None
    category: str = ""
    body_content: str = ""
    month_year: str = ""  # e.g., "January 2024"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


@dataclass
class ReferencedDocument:
    """Referenced documents within policy updates"""
    id: Optional[str] = None
    policy_update_id: str = ""
    document_title: str = ""
    document_url: str = ""
    document_type: str = ""  # medical_policy, clinical_guideline, etc.
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


@dataclass
class MedicalCode:
    """Medical codes extracted from policy updates"""
    id: Optional[str] = None
    policy_update_id: str = ""
    code: str = ""
    code_type: str = ""  # CPT, HCPCS, ICD10
    description: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


@dataclass
class DocumentChange:
    """Document changes mentioned in policy updates"""
    id: Optional[str] = None
    policy_update_id: str = ""
    document_title: str = ""
    change_type: str = ""  # added, modified, removed
    change_description: str = ""
    section_affected: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


@dataclass
class ScrapingLog:
    """Logging for scraping operations"""
    id: Optional[str] = None
    url: str = ""
    status: str = ""  # success, error, skipped
    error_message: str = ""
    records_scraped: int = 0
    execution_time: float = 0.0
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


# Database table schemas for Supabase
SUPABASE_SCHEMAS = {
    "policy_updates": """
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
    
    "referenced_documents": """
        CREATE TABLE IF NOT EXISTS referenced_documents (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            policy_update_id UUID REFERENCES policy_updates(id) ON DELETE CASCADE,
            document_title TEXT NOT NULL,
            document_url TEXT,
            document_type TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """,
    
    "medical_codes": """
        CREATE TABLE IF NOT EXISTS medical_codes (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            policy_update_id UUID REFERENCES policy_updates(id) ON DELETE CASCADE,
            code TEXT NOT NULL,
            code_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """,
    
    "document_changes": """
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
    
    "scraping_logs": """
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
}

# Indexes for better query performance
SUPABASE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_policy_updates_month_year ON policy_updates(month_year);",
    "CREATE INDEX IF NOT EXISTS idx_policy_updates_published_date ON policy_updates(published_date);",
    "CREATE INDEX IF NOT EXISTS idx_medical_codes_code_type ON medical_codes(code_type);",
    "CREATE INDEX IF NOT EXISTS idx_medical_codes_policy_id ON medical_codes(policy_update_id);",
    "CREATE INDEX IF NOT EXISTS idx_referenced_docs_policy_id ON referenced_documents(policy_update_id);",
    "CREATE INDEX IF NOT EXISTS idx_document_changes_policy_id ON document_changes(policy_update_id);",
    "CREATE INDEX IF NOT EXISTS idx_scraping_logs_timestamp ON scraping_logs(timestamp);"
]