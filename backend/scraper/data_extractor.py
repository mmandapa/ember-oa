"""
Data extraction utilities for parsing policy update content
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class DataExtractor:
    """Extracts structured data from policy update HTML content"""
    
    def __init__(self):
        # Medical code patterns
        self.cpt_pattern = re.compile(r'\b(\d{5})\b')  # CPT codes (5 digits)
        self.hcpcs_pattern = re.compile(r'\b([A-Z]\d{4})\b')  # HCPCS codes (letter + 4 digits)
        self.icd10_pattern = re.compile(r'\b([A-Z]\d{2}\.?\d{0,2})\b')  # ICD-10 codes
        
        # Document change patterns
        self.change_patterns = [
            re.compile(r'(added|modified|removed|updated|changed)', re.IGNORECASE),
            re.compile(r'(section|policy|guideline|procedure)', re.IGNORECASE)
        ]
    
    def extract_policy_data(self, soup: BeautifulSoup, url: str, month_year: str) -> Optional[Dict[str, Any]]:
        """
        Extract all policy data from HTML soup
        Returns structured dictionary with all required fields
        """
        try:
            policy_data = {
                'title': self._extract_title(soup),
                'url': url,
                'published_date': self._extract_published_date(soup),
                'category': self._extract_category(soup),
                'body_content': self._extract_body_content(soup),
                'month_year': month_year,
                'referenced_documents': self._extract_referenced_documents(soup),
                'medical_codes': self._extract_medical_codes(soup),
                'document_changes': self._extract_document_changes(soup)
            }
            
            # Validate extracted data
            if not policy_data['title']:
                logger.warning(f"No title found for policy: {url}")
                return None
            
            logger.info(f"Successfully extracted policy data: {policy_data['title']}")
            return policy_data
            
        except Exception as e:
            logger.error(f"Error extracting policy data from {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract policy title"""
        # Try multiple selectors for title
        title_selectors = [
            'h1',
            'h2.title',
            '.policy-title',
            '.title',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 5:  # Avoid very short titles
                    return title
        
        # Fallback: use page title
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        return ""
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract published date"""
        # Look for date patterns in various formats
        date_patterns = [
            r'\b(\w+ \d{1,2}, \d{4})\b',  # "September 10, 2025"
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',  # "09/10/2025"
            r'\b(\d{4}-\d{2}-\d{2})\b',  # "2025-09-10"
        ]
        
        text_content = soup.get_text()
        
        for pattern in date_patterns:
            match = re.search(pattern, text_content)
            if match:
                try:
                    date_str = match.group(1)
                    # Try different date parsing formats
                    for fmt in ['%B %d, %Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract policy category"""
        # Look for category indicators
        category_indicators = [
            '.category',
            '.policy-category',
            '.type',
            '[class*="category"]'
        ]
        
        for indicator in category_indicators:
            elem = soup.select_one(indicator)
            if elem:
                category = elem.get_text(strip=True)
                if category:
                    return category
        
        # Look for category in breadcrumbs or navigation
        breadcrumbs = soup.find_all(['nav', 'ol', 'ul'], class_=re.compile(r'breadcrumb|nav'))
        for breadcrumb in breadcrumbs:
            text = breadcrumb.get_text(strip=True)
            if 'policy' in text.lower() or 'coverage' in text.lower():
                return text
        
        return "Policy Update"
    
    def _extract_body_content(self, soup: BeautifulSoup) -> str:
        """Extract main body content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content area
        content_selectors = [
            '.content',
            '.main-content',
            '.policy-content',
            '.body',
            'main',
            'article'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Get text content while preserving some structure
                content = self._clean_text_content(content_elem)
                if len(content) > 100:  # Ensure substantial content
                    return content
        
        # Fallback: get all text content
        return self._clean_text_content(soup)
    
    def _clean_text_content(self, element) -> str:
        """Clean and format text content"""
        # Get text with some structure preservation
        text = element.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _extract_referenced_documents(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract referenced documents"""
        documents = []
        
        # Look for document links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Check if this looks like a document reference
            if (href and 
                ('policy' in href.lower() or 'guideline' in href.lower() or 
                 'medical' in href.lower() or '.pdf' in href.lower()) and
                len(text) > 5):
                
                doc_type = self._classify_document_type(text, href)
                
                documents.append({
                    'title': text,
                    'url': href,
                    'type': doc_type
                })
        
        return documents
    
    def _classify_document_type(self, title: str, url: str) -> str:
        """Classify document type based on title and URL"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if 'medical policy' in title_lower or 'medical-policy' in url_lower:
            return 'medical_policy'
        elif 'clinical guideline' in title_lower or 'guideline' in url_lower:
            return 'clinical_guideline'
        elif 'reimbursement' in title_lower:
            return 'reimbursement_policy'
        elif 'coverage' in title_lower:
            return 'coverage_policy'
        else:
            return 'policy_document'
    
    def _extract_medical_codes(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract medical codes from content"""
        codes = []
        text_content = soup.get_text()
        
        # Extract CPT codes
        cpt_matches = self.cpt_pattern.findall(text_content)
        for code in cpt_matches:
            codes.append({
                'code': code,
                'type': 'CPT',
                'description': self._get_code_description(code, 'CPT')
            })
        
        # Extract HCPCS codes
        hcpcs_matches = self.hcpcs_pattern.findall(text_content)
        for code in hcpcs_matches:
            codes.append({
                'code': code,
                'type': 'HCPCS',
                'description': self._get_code_description(code, 'HCPCS')
            })
        
        # Extract ICD-10 codes
        icd10_matches = self.icd10_pattern.findall(text_content)
        for code in icd10_matches:
            codes.append({
                'code': code,
                'type': 'ICD10',
                'description': self._get_code_description(code, 'ICD10')
            })
        
        # Remove duplicates
        unique_codes = []
        seen_codes = set()
        for code in codes:
            code_key = f"{code['code']}_{code['type']}"
            if code_key not in seen_codes:
                unique_codes.append(code)
                seen_codes.add(code_key)
        
        return unique_codes
    
    def _get_code_description(self, code: str, code_type: str) -> str:
        """Get description for medical code (placeholder implementation)"""
        # In a real implementation, this would look up code descriptions
        # from a medical code database or API
        return f"{code_type} Code: {code}"
    
    def _extract_document_changes(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract document changes mentioned in policy updates"""
        changes = []
        text_content = soup.get_text()
        
        # Look for change indicators
        change_keywords = ['added', 'modified', 'removed', 'updated', 'changed', 'revised']
        
        sentences = text_content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in change_keywords):
                # Try to extract structured change information
                change_info = self._parse_change_sentence(sentence)
                if change_info:
                    changes.append(change_info)
        
        return changes
    
    def _parse_change_sentence(self, sentence: str) -> Optional[Dict[str, str]]:
        """Parse a sentence to extract change information"""
        sentence_lower = sentence.lower()
        
        # Determine change type
        change_type = 'modified'
        if 'added' in sentence_lower:
            change_type = 'added'
        elif 'removed' in sentence_lower:
            change_type = 'removed'
        elif 'updated' in sentence_lower or 'revised' in sentence_lower:
            change_type = 'updated'
        
        # Extract document title (simplified)
        # Look for quoted text or capitalized words
        title_match = re.search(r'"([^"]+)"', sentence)
        if title_match:
            document_title = title_match.group(1)
        else:
            # Fallback: look for capitalized words
            words = sentence.split()
            capitalized_words = [word for word in words if word[0].isupper()]
            if capitalized_words:
                document_title = ' '.join(capitalized_words[:3])  # Take first few capitalized words
            else:
                document_title = "Policy Document"
        
        return {
            'document_title': document_title,
            'change_type': change_type,
            'description': sentence,
            'section': ''  # Would need more sophisticated parsing
        }