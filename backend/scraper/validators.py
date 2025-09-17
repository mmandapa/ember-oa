"""
Data validation utilities for scraped policy data
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates scraped policy data for completeness and correctness"""
    
    def __init__(self):
        # Validation patterns
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        self.cpt_pattern = re.compile(r'^\d{5}$')
        self.hcpcs_pattern = re.compile(r'^[A-Z]\d{4}$')
        self.icd10_pattern = re.compile(r'^[A-Z]\d{2}\.?\d{0,2}$')
    
    def validate_policy_data(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete policy data
        Returns validation results with errors and warnings
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'validated_data': policy_data.copy()
        }
        
        # Validate required fields
        self._validate_required_fields(policy_data, validation_result)
        
        # Validate field formats
        self._validate_field_formats(policy_data, validation_result)
        
        # Validate medical codes
        self._validate_medical_codes(policy_data, validation_result)
        
        # Validate referenced documents
        self._validate_referenced_documents(policy_data, validation_result)
        
        # Clean and normalize data
        self._clean_data(validation_result['validated_data'])
        
        return validation_result
    
    def _validate_required_fields(self, data: Dict[str, Any], result: Dict[str, Any]):
        """Validate that required fields are present"""
        required_fields = ['title', 'url']
        
        for field in required_fields:
            if not data.get(field):
                result['errors'].append(f"Missing required field: {field}")
                result['is_valid'] = False
    
    def _validate_field_formats(self, data: Dict[str, Any], result: Dict[str, Any]):
        """Validate field formats"""
        # Validate URL format
        url = data.get('url', '')
        if url and not self._is_valid_url(url):
            result['errors'].append(f"Invalid URL format: {url}")
            result['is_valid'] = False
        
        # Validate published date
        published_date = data.get('published_date')
        if published_date and not isinstance(published_date, datetime):
            result['warnings'].append("Published date should be a datetime object")
        
        # Validate title length
        title = data.get('title', '')
        if title:
            if len(title) < 5:
                result['warnings'].append("Title seems too short")
            elif len(title) > 500:
                result['warnings'].append("Title seems too long")
        
        # Validate body content
        body_content = data.get('body_content', '')
        if body_content:
            if len(body_content) < 50:
                result['warnings'].append("Body content seems too short")
            elif len(body_content) > 50000:
                result['warnings'].append("Body content seems too long")
    
    def _validate_medical_codes(self, data: Dict[str, Any], result: Dict[str, Any]):
        """Validate medical codes"""
        medical_codes = data.get('medical_codes', [])
        
        for i, code in enumerate(medical_codes):
            code_value = code.get('code', '')
            code_type = code.get('type', '')
            
            if not code_value:
                result['warnings'].append(f"Medical code {i+1} has empty code value")
                continue
            
            # Validate code format based on type
            if code_type == 'CPT' and not self.cpt_pattern.match(code_value):
                result['warnings'].append(f"Invalid CPT code format: {code_value}")
            elif code_type == 'HCPCS' and not self.hcpcs_pattern.match(code_value):
                result['warnings'].append(f"Invalid HCPCS code format: {code_value}")
            elif code_type == 'ICD10' and not self.icd10_pattern.match(code_value):
                result['warnings'].append(f"Invalid ICD-10 code format: {code_value}")
    
    def _validate_referenced_documents(self, data: Dict[str, Any], result: Dict[str, Any]):
        """Validate referenced documents"""
        documents = data.get('referenced_documents', [])
        
        for i, doc in enumerate(documents):
            doc_url = doc.get('url', '')
            doc_title = doc.get('title', '')
            
            if doc_url and not self._is_valid_url(doc_url):
                result['warnings'].append(f"Invalid document URL {i+1}: {doc_url}")
            
            if not doc_title:
                result['warnings'].append(f"Document {i+1} has no title")
    
    def _clean_data(self, data: Dict[str, Any]):
        """Clean and normalize data"""
        # Clean title
        if 'title' in data and data['title']:
            data['title'] = data['title'].strip()
        
        # Clean category
        if 'category' in data and data['category']:
            data['category'] = data['category'].strip()
        
        # Clean body content
        if 'body_content' in data and data['body_content']:
            data['body_content'] = self._clean_text(data['body_content'])
        
        # Clean medical codes
        if 'medical_codes' in data:
            for code in data['medical_codes']:
                if 'code' in code:
                    code['code'] = code['code'].strip().upper()
                if 'description' in code:
                    code['description'] = code['description'].strip()
        
        # Clean referenced documents
        if 'referenced_documents' in data:
            for doc in data['referenced_documents']:
                if 'title' in doc:
                    doc['title'] = doc['title'].strip()
                if 'url' in doc:
                    doc['url'] = doc['url'].strip()
    
    def _clean_text(self, text: str) -> str:
        """Clean text content"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        return text.strip()
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def validate_scraping_url(self, url: str) -> bool:
        """Validate if URL is appropriate for scraping"""
        if not self._is_valid_url(url):
            return False
        
        # Check if it's a Cigna URL
        if 'cigna.com' not in url.lower():
            logger.warning(f"URL is not from Cigna domain: {url}")
            return False
        
        return True
    
    def get_validation_summary(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of multiple validation results"""
        total_valid = sum(1 for result in validation_results if result['is_valid'])
        total_errors = sum(len(result['errors']) for result in validation_results)
        total_warnings = sum(len(result['warnings']) for result in validation_results)
        
        return {
            'total_records': len(validation_results),
            'valid_records': total_valid,
            'invalid_records': len(validation_results) - total_valid,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'success_rate': (total_valid / len(validation_results)) * 100 if validation_results else 0
        }