"""
Supabase client configuration and database operations
"""

import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from datetime import datetime
import logging

from .models import (
    PolicyUpdate, ReferencedDocument, MedicalCode, 
    DocumentChange, ScrapingLog, SUPABASE_SCHEMAS, SUPABASE_INDEXES
)

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client wrapper for database operations"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not all([self.url, self.key]):
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        self._initialized = False
    
    async def initialize_database(self):
        """Initialize database tables and indexes"""
        if self._initialized:
            return
        
        try:
            # Create tables
            for table_name, schema in SUPABASE_SCHEMAS.items():
                logger.info(f"Creating table: {table_name}")
                # Note: Supabase handles table creation through SQL editor or migrations
                # This is a placeholder for the schema definitions
            
            # Create indexes
            for index_sql in SUPABASE_INDEXES:
                logger.info(f"Creating index: {index_sql}")
                # Note: Indexes should be created through Supabase SQL editor
            
            self._initialized = True
            logger.info("Database initialization completed")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def insert_policy_update(self, policy: PolicyUpdate) -> Optional[str]:
        """Insert a policy update and return its ID"""
        try:
            data = policy.to_dict()
            result = self.client.table('policy_updates').insert(data).execute()
            
            if result.data:
                policy_id = result.data[0]['id']
                logger.info(f"Inserted policy update: {policy.title} (ID: {policy_id})")
                return policy_id
            else:
                logger.error(f"Failed to insert policy update: {policy.title}")
                return None
                
        except Exception as e:
            logger.error(f"Error inserting policy update: {e}")
            return None
    
    async def insert_referenced_documents(self, documents: List[ReferencedDocument]) -> List[str]:
        """Insert referenced documents and return their IDs"""
        if not documents:
            return []
        
        try:
            data = [doc.to_dict() for doc in documents]
            result = self.client.table('referenced_documents').insert(data).execute()
            
            if result.data:
                doc_ids = [doc['id'] for doc in result.data]
                logger.info(f"Inserted {len(doc_ids)} referenced documents")
                return doc_ids
            else:
                logger.error("Failed to insert referenced documents")
                return []
                
        except Exception as e:
            logger.error(f"Error inserting referenced documents: {e}")
            return []
    
    async def insert_medical_codes(self, codes: List[MedicalCode]) -> List[str]:
        """Insert medical codes and return their IDs"""
        if not codes:
            return []
        
        try:
            data = [code.to_dict() for code in codes]
            result = self.client.table('medical_codes').insert(data).execute()
            
            if result.data:
                code_ids = [code['id'] for code in result.data]
                logger.info(f"Inserted {len(code_ids)} medical codes")
                return code_ids
            else:
                logger.error("Failed to insert medical codes")
                return []
                
        except Exception as e:
            logger.error(f"Error inserting medical codes: {e}")
            return []
    
    async def insert_document_changes(self, changes: List[DocumentChange]) -> List[str]:
        """Insert document changes and return their IDs"""
        if not changes:
            return []
        
        try:
            data = [change.to_dict() for change in changes]
            result = self.client.table('document_changes').insert(data).execute()
            
            if result.data:
                change_ids = [change['id'] for change in result.data]
                logger.info(f"Inserted {len(change_ids)} document changes")
                return change_ids
            else:
                logger.error("Failed to insert document changes")
                return []
                
        except Exception as e:
            logger.error(f"Error inserting document changes: {e}")
            return []
    
    async def insert_scraping_log(self, log: ScrapingLog) -> Optional[str]:
        """Insert scraping log and return its ID"""
        try:
            data = log.to_dict()
            result = self.client.table('scraping_logs').insert(data).execute()
            
            if result.data:
                log_id = result.data[0]['id']
                logger.info(f"Inserted scraping log for URL: {log.url}")
                return log_id
            else:
                logger.error(f"Failed to insert scraping log for URL: {log.url}")
                return None
                
        except Exception as e:
            logger.error(f"Error inserting scraping log: {e}")
            return None
    
    async def get_policy_updates(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve policy updates with pagination"""
        try:
            result = self.client.table('policy_updates')\
                .select('*')\
                .order('published_date', desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving policy updates: {e}")
            return []
    
    async def get_policy_update_by_id(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific policy update with all related data"""
        try:
            # Get policy update
            policy_result = self.client.table('policy_updates')\
                .select('*')\
                .eq('id', policy_id)\
                .execute()
            
            if not policy_result.data:
                return None
            
            policy = policy_result.data[0]
            
            # Get related data
            referenced_docs = self.client.table('referenced_documents')\
                .select('*')\
                .eq('policy_update_id', policy_id)\
                .execute()
            
            medical_codes = self.client.table('medical_codes')\
                .select('*')\
                .eq('policy_update_id', policy_id)\
                .execute()
            
            document_changes = self.client.table('document_changes')\
                .select('*')\
                .eq('policy_update_id', policy_id)\
                .execute()
            
            policy['referenced_documents'] = referenced_docs.data or []
            policy['medical_codes'] = medical_codes.data or []
            policy['document_changes'] = document_changes.data or []
            
            return policy
            
        except Exception as e:
            logger.error(f"Error retrieving policy update {policy_id}: {e}")
            return None
    
    async def search_policy_updates(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search policy updates by title or content"""
        try:
            result = self.client.table('policy_updates')\
                .select('*')\
                .or_(f'title.ilike.%{query}%,body_content.ilike.%{query}%')\
                .order('published_date', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error searching policy updates: {e}")
            return []
    
    async def get_medical_codes_by_type(self, code_type: str) -> List[Dict[str, Any]]:
        """Get medical codes by type (CPT, HCPCS, ICD10)"""
        try:
            result = self.client.table('medical_codes')\
                .select('*, policy_updates(title, published_date)')\
                .eq('code_type', code_type)\
                .order('created_at', desc=True)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving medical codes by type {code_type}: {e}")
            return []
    
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        try:
            # Total policies
            policies_result = self.client.table('policy_updates')\
                .select('id', count='exact')\
                .execute()
            
            # Total medical codes
            codes_result = self.client.table('medical_codes')\
                .select('id', count='exact')\
                .execute()
            
            # Recent scraping activity
            recent_logs = self.client.table('scraping_logs')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(10)\
                .execute()
            
            return {
                'total_policies': policies_result.count or 0,
                'total_medical_codes': codes_result.count or 0,
                'recent_scraping_activity': recent_logs.data or []
            }
            
        except Exception as e:
            logger.error(f"Error retrieving scraping stats: {e}")
            return {}


# Global client instance
supabase_client = SupabaseClient()