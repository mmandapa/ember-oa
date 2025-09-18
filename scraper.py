#!/usr/bin/env python3
"""
Cigna Policy Scraper using pdfplumber + spaCy
Scrapes policy updates from Cigna's provider news website using deterministic text extraction
"""

import os
import json
import requests
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from supabase import create_client
from dotenv import load_dotenv
import spacy
import pdfplumber
import io

# Load environment variables
load_dotenv()

class CignaPolicyScraper:
    def __init__(self):
        self.base_url = "https://static.cigna.com/assets/chcp/resourceLibrary/coveragePolicies/"
        self.main_url = "https://static.cigna.com/assets/chcp/resourceLibrary/coveragePolicies/latestUpdatesListing.html"
        
        # Setup spaCy
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model loaded successfully")
        except OSError:
            print("❌ spaCy model not found. Please run: python -m spacy download en_core_web_sm")
            raise
        
        # Setup Supabase
        url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
        
        self.supabase = create_client(url, key)
        
        print("🤖 Cigna Policy Scraper initialized")
        print("=" * 60)

    def fetch_monthly_links(self):
        """Fetch all monthly policy update links from the main page"""
        try:
            response = requests.get(self.main_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            # Find all policy update links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'policy_updates' in href and href.endswith('.pdf'):
                    # href already contains the full path, just prepend the base domain
                    full_url = "https://static.cigna.com" + href
                    month_year = link.get_text().strip()
                    links.append({
                        'url': full_url,
                        'month_year': month_year
                    })
                    print(f"📅 Found: {month_year}")
            
            return links
            
        except Exception as e:
            print(f"❌ Error fetching monthly links: {e}")
            return []
    
    def extract_policy_links_from_pdf(self, pdf_content, month_year):
        """Extract policy links and comments from monthly PDF using pdfplumber"""
        try:
            policy_links = []
            
            # Open PDF from bytes
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    print(f"    📖 Processing page {page_num + 1}")
                    
                    # Extract hyperlinks from the page
                    hyperlinks = self.extract_hyperlinks_from_page(page)
                    for link in hyperlinks:
                        print(f"    🔗 Found hyperlink: {link['url']}")
                        title = link.get('title') or 'Unknown Policy'
                        
                        # Extract comments from table data for this policy
                        comments = self.extract_comments_from_tables_for_url(page, link['url'])
                        
                        policy_links.append({
                            'title': title,
                            'url': link['url'],
                            'policy_number': self.extract_policy_number_from_url(link['url']),
                            'comments': comments
                        })
                    
                    # Also extract text and tables as fallback
                    text = page.extract_text()
                    tables = page.extract_tables()
                    
                    if text:
                        # Look for policy patterns in text
                        policy_patterns = self.extract_policy_patterns_from_text(text, month_year)
                        policy_links.extend(policy_patterns)
                    
                    if tables:
                        # Look for policy patterns in tables
                        for table in tables:
                            table_policies = self.extract_policy_patterns_from_table(table, month_year)
                            policy_links.extend(table_policies)
            
            print(f"    📋 Extracted {len(policy_links)} policy links from PDF")
            return policy_links
            
        except Exception as e:
            print(f"    ❌ Error parsing PDF: {e}")
            return []
    
    def extract_hyperlinks_from_page(self, page):
        """Extract hyperlinks from a PDF page"""
        hyperlinks = []
        
        try:
            # Debug: Check what attributes are available
            print(f"    🔍 Page attributes: {dir(page)}")
            
            # Get annotations (which include hyperlinks)
            if hasattr(page, 'annots') and page.annots:
                print(f"    📝 Found {len(page.annots)} annotations")
                for i, annot in enumerate(page.annots):
                    print(f"    📝 Annotation {i}: {annot}")
                    if annot.get('uri'):
                        print(f"    🔗 Found URI: {annot['uri']}")
                        # Extract title from text near the hyperlink coordinates
                        title = self.extract_title_near_coordinates(page, annot)
                        hyperlinks.append({
                            'url': annot['uri'],
                            'title': title,
                            'comments': ''
                        })
                    else:
                        print(f"    ⚠️ No URI in annotation: {annot}")
            
            # Also try to extract links from the page's link annotations
            if hasattr(page, 'links') and page.links:
                print(f"    🔗 Found {len(page.links)} links")
                for link in page.links:
                    if link.get('uri'):
                        hyperlinks.append({
                            'url': link['uri'],
                            'title': link.get('title', ''),
                            'comments': ''
                        })
            
            # Try alternative method - look for URLs in text
            text = page.extract_text()
            if text:
                import re
                # Look for URLs in the text
                url_pattern = r'https://static\.cigna\.com/[^\s]+\.pdf'
                urls = re.findall(url_pattern, text)
                for url in urls:
                    hyperlinks.append({
                        'url': url,
                        'title': 'Extracted from text',
                        'comments': ''
                    })
                print(f"    📄 Found {len(urls)} URLs in text")
            
            # Filter for Cigna policy URLs
            cigna_links = []
            print(f"    🔍 Checking {len(hyperlinks)} hyperlinks for Cigna policy URLs:")
            for i, link in enumerate(hyperlinks):
                url = link['url']
                print(f"    🔍 Link {i}: {url}")
                print(f"    🔍 Contains 'static.cigna.com': {'static.cigna.com' in url}")
                print(f"    🔍 Contains 'mm_': {'mm_' in url}")
                print(f"    🔍 Ends with '.pdf': {url.endswith('.pdf')}")
                
                # Check for any Cigna policy pattern (mm_, ip_, ph_, etc.)
                is_cigna_policy = ('static.cigna.com' in url and 
                                 url.endswith('.pdf') and 
                                 ('mm_' in url or 'ip_' in url or 'ph_' in url or 'coveragepositioncriteria' in url))
                
                if is_cigna_policy:
                    print(f"    ✅ This is a Cigna policy link!")
                    cigna_links.append(link)
                else:
                    print(f"    ❌ Not a Cigna policy link")
            
            print(f"    ✅ Found {len(cigna_links)} Cigna policy links")
            return cigna_links
            
        except Exception as e:
            print(f"    ⚠️ Error extracting hyperlinks: {e}")
            return []

    def extract_title_from_url(self, url):
        """Extract policy title from URL"""
        try:
            import re
            
            # Extract policy name from URL for any policy type
            patterns = [
                r'mm_\d+_coveragepositioncriteria_(.+)\.pdf',
                r'ip_\d+_coveragepositioncriteria_(.+)\.pdf',
                r'ph_\d+_coveragepositioncriteria_(.+)\.pdf'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    policy_name = match.group(1).replace('_', ' ').title()
                    # Extract policy number from URL
                    policy_num_match = re.search(r'(mm_|ip_|ph_)(\d+)', url)
                    if policy_num_match:
                        policy_type = policy_num_match.group(1).upper().rstrip('_')
                        policy_number = policy_num_match.group(2)
                        return f"{policy_name} - ({policy_type}{policy_number})"
                    return policy_name
            
            return 'Unknown Policy'
        except:
            return 'Unknown Policy'

    def is_cell_near_hyperlink(self, table, row, cell, x0, y0, x1, y1):
        """Check if a table cell is near the hyperlink coordinates"""
        try:
            # For now, just return True to use the first matching cell
            # This is a simplified approach - in a real implementation,
            # we would need to map table cell coordinates to PDF coordinates
            return True
        except:
            return False

    def extract_title_near_coordinates(self, page, annot):
        """Extract policy title from text near the hyperlink coordinates"""
        try:
            # Get the coordinates of the hyperlink
            x0, y0, x1, y1 = annot.get('x0', 0), annot.get('y0', 0), annot.get('x1', 0), annot.get('y1', 0)
            
            # Extract title from URL first (most reliable)
            url = annot.get('uri', '')
            if url:
                title_from_url = self.extract_title_from_url(url)
                if title_from_url and title_from_url != 'Unknown Policy':
                    print(f"    📝 Extracted title from URL: '{title_from_url}'")
                    return title_from_url
            
            # Fallback: try to extract from tables
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        for cell in row:
                            if cell and isinstance(cell, str):
                                cell_text = cell.strip()
                                # Skip generic headers and look for actual policy names
                                if (len(cell_text) < 100 and 
                                    len(cell_text) > 5 and 
                                    not cell_text.startswith('•') and 
                                    not cell_text.startswith('Effective') and
                                    not 'Policy Statement' in cell_text and
                                    not 'authorizes coverage' in cell_text.lower() and
                                    not 'Coverage Policy Unit' in cell_text and
                                    not 'Monthly Policy Updates' in cell_text and
                                    not 'CPU' in cell_text and
                                    not cell_text.startswith('and ') and  # Skip partial titles
                                    # Look for policy names that contain policy numbers in parentheses
                                    ('(' in cell_text and ')' in cell_text)):
                                    print(f"    📝 Extracted title from table: '{cell_text}'")
                                    return cell_text
            
            # Fallback: Extract text from words near the hyperlink coordinates
            words = page.extract_words()
            
            # Find words near the hyperlink coordinates
            nearby_words = []
            for word in words:
                word_x0, word_y0, word_x1, word_y1 = word.get('x0', 0), word.get('y0', 0), word.get('x1', 0), word.get('y1', 0)
                
                # Check if word is in the same row (similar y-coordinates) and nearby horizontally
                if (abs(word_y0 - y0) < 15 and  # Same row (within 15 pixels vertically)
                    word_x0 < x1 + 100 and      # Not too far to the right
                    word_x1 > x0 - 100):        # Not too far to the left
                    nearby_words.append(word)
            
            # Sort words by x-coordinate to get them in reading order
            nearby_words.sort(key=lambda w: w.get('x0', 0))
            
            # Extract the text from nearby words
            title_text = ' '.join([word.get('text', '') for word in nearby_words])
            
            # Clean up the title
            title_text = title_text.strip()
            if title_text and len(title_text) > 5:  # Reasonable title length
                print(f"    📝 Extracted title from words: '{title_text}'")
                return title_text
            else:
                # Last resort: extract title from URL
                url = annot.get('uri', '')
                if url:
                    # Extract policy name from URL for any policy type
                    import re
                    patterns = [
                        r'mm_\d+_coveragepositioncriteria_(.+)\.pdf',
                        r'ip_\d+_coveragepositioncriteria_(.+)\.pdf', 
                        r'ph_\d+_coveragepositioncriteria_(.+)\.pdf',
                        r'ph_\d+_coverageposition_(.+)\.pdf'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, url)
                        if match:
                            policy_name = match.group(1).replace('_', ' ').title()
                            print(f"    📝 Extracted title from URL: '{policy_name}'")
                            return policy_name
                
                print(f"    ⚠️ Could not extract title from coordinates")
                return 'Unknown Policy'
            
        except Exception as e:
            print(f"    ⚠️ Error extracting title: {e}")
            return 'Unknown Policy'

    def extract_policy_number_from_url(self, url):
        """Extract policy number from URL"""
        try:
            # Look for pattern like mm_0586_ in the URL
            match = re.search(r'mm_(\d{4})_', url)
            return match.group(1) if match else ''
        except:
            return ''

    def extract_policy_patterns_from_text(self, text, month_year):
        """Extract policy patterns from PDF text"""
        policies = []
        
        # Pattern to match policy titles with numbers like "Alveoloplasty - (0586)"
        policy_pattern = r'([A-Za-z\s\-]+)\s*-\s*\((\d{4})\)'
        
        matches = re.finditer(policy_pattern, text)
        for match in matches:
            title = match.group(1).strip().replace('\n', ' ').replace('\r', ' ')
            # Clean up extra whitespace
            title = ' '.join(title.split())
            policy_number = match.group(2)
            
            # Construct the policy URL based on the actual Cigna pattern
            # Clean the title for URL construction - remove newlines and extra whitespace
            clean_title = title.lower().replace('\n', ' ').replace('\r', ' ').replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace(',', '').replace('.', '').replace('&', 'and').replace('__', '_').strip('_')
            policy_url = f"https://static.cigna.com/assets/chcp/pdf/coveragePolicies/medical/mm_{policy_number}_coveragepositioncriteria_{clean_title}.pdf"
            
            policies.append({
                'title': f"{title} - ({policy_number})",
                'url': policy_url,
                'policy_number': policy_number,
                'comments': self.extract_comments_for_policy(text, title, policy_number)
            })
        
        return policies
    
    def extract_policy_patterns_from_table(self, table, month_year):
        """Extract policy patterns from PDF table"""
        policies = []
        
        if not table or len(table) < 2:
            return policies
        
        # Look for policy information in table rows
        for row in table:
            if not row or len(row) < 2:
                    continue
                
            # Join all cells in the row to create a searchable text
            row_text = ' '.join([str(cell) for cell in row if cell])
            
            # Look for policy patterns in the row
            policy_pattern = r'([A-Za-z\s\-]+)\s*-\s*\((\d{4})\)'
            matches = re.finditer(policy_pattern, row_text)
            
            for match in matches:
                title = match.group(1).strip().replace('\n', ' ').replace('\r', ' ')
                # Clean up extra whitespace
                title = ' '.join(title.split())
                policy_number = match.group(2)
                
                # Construct the policy URL based on the actual Cigna pattern
                # Clean the title for URL construction - remove newlines and extra whitespace
                clean_title = title.lower().replace('\n', ' ').replace('\r', ' ').replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace(',', '').replace('.', '').replace('&', 'and').replace('__', '_').strip('_')
                policy_url = f"https://static.cigna.com/assets/chcp/pdf/coveragePolicies/medical/mm_{policy_number}_coveragepositioncriteria_{clean_title}.pdf"
                
                policies.append({
                    'title': f"{title} - ({policy_number})",
                    'url': policy_url,
                    'policy_number': policy_number,
                    'comments': self.extract_comments_for_policy(row_text, title, policy_number)
                })
        
        return policies

    def extract_comments_for_policy(self, text, title, policy_number):
        """Extract comments/changes for a specific policy from the text"""
        # Look for patterns like "Updated", "New", "Modified", etc. near the policy
        comment_patterns = [
            r'(Updated|New|Modified|Retired|Added|Removed|Changed)',
            r'(Coverage criteria|Prior authorization|Documentation requirements)',
            r'(Effective [Dd]ate|Last [Uu]pdated)'
        ]
        
        comments = []
        for pattern in comment_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get some context around the match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                comments.append(context.strip())
        
        return '; '.join(comments[:3]) if comments else ''

    def extract_comments_from_tables_for_url(self, page, url):
        """Extract comments from table data for a specific policy URL"""
        try:
            # Extract policy number from URL
            policy_number = self.extract_policy_number_from_url(url)
            if not policy_number:
                return ''
            
            # Extract tables from the page
            tables = page.extract_tables()
            if not tables:
                return ''
            
            # Look for the policy in table rows and extract comments
            for table in tables:
                for row in table:
                    if not row or len(row) < 2:
                        continue
                    
                    # Join all cells in the row to create a searchable text
                    row_text = ' '.join([str(cell) for cell in row if cell])
                    
                    # Check if this row contains our policy number
                    if policy_number in row_text:
                        # Extract comments from this row
                        comments = self.extract_comments_for_policy(row_text, '', policy_number)
                        if comments:
                            return comments
            
            return ''
        except Exception as e:
            print(f"    ⚠️ Error extracting comments: {e}")
            return ''

    def extract_text_from_policy_pdf(self, pdf_content):
        """Extract text from individual policy PDF"""
        try:
            text_content = []
            
            # Open PDF from bytes
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text from each page
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                    
                    # Also extract tables if they exist
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # Convert table to text representation
                            for row in table:
                                if row:
                                    row_text = ' | '.join([str(cell) for cell in row if cell])
                                    text_content.append(row_text)
            
            return '\n'.join(text_content)
            
        except Exception as e:
            print(f"    ❌ Error extracting text from PDF: {e}")
            return None

    def extract_medical_codes(self, text):
        """Extract medical codes using regex patterns"""
        codes = []
        
        # CPT codes (5 digits)
        cpt_pattern = r'\b(\d{5})\b'
        cpt_matches = re.finditer(cpt_pattern, text)
        for match in cpt_matches:
            code = match.group(1)
            # Get context around the code
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            codes.append({
                'code': code,
                'code_type': 'CPT',
                'description': self.extract_code_description(context, code)
            })
        
        # HCPCS codes (1 letter + 4 digits)
        hcpcs_pattern = r'\b([A-Z]\d{4})\b'
        hcpcs_matches = re.finditer(hcpcs_pattern, text)
        for match in hcpcs_matches:
            code = match.group(1)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            codes.append({
                'code': code,
                'code_type': 'HCPCS',
                'description': self.extract_code_description(context, code)
            })
        
        # ICD-10 codes (letter + digits + optional decimal)
        icd10_pattern = r'\b([A-TV-Z]\d{2}(?:\.\d{1,4})?)\b'
        icd10_matches = re.finditer(icd10_pattern, text)
        for match in icd10_matches:
            code = match.group(1)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            codes.append({
                'code': code,
                'code_type': 'ICD-10',
                'description': self.extract_code_description(context, code)
            })
        
        return codes

    def extract_code_description(self, context, code):
        """Extract description for a medical code from context"""
        # Look for description patterns around the code
        lines = context.split('\n')
        for i, line in enumerate(lines):
            if code in line:
                # Look at the same line and next few lines for description
                description_parts = []
                for j in range(i, min(i + 3, len(lines))):
                    description_parts.append(lines[j].strip())
                description = ' '.join(description_parts)
                # Clean up the description
                description = re.sub(r'\s+', ' ', description)
                return description[:200]  # Limit length
        return ""

    def extract_referenced_documents(self, text):
        """Extract referenced documents from the References section of individual policy documents"""
        documents = []
        seen_documents = set()  # Prevent duplicates
        
        # Look specifically for References section in policy documents
        references_patterns = [
            r'References?\s*[:\-]?\s*\n(.*?)(?=\n\n[A-Z][a-z]+:|$)',
            r'Bibliography\s*[:\-]?\s*\n(.*?)(?=\n\n[A-Z][a-z]+:|$)',
            r'Related\s+Documents?\s*[:\-]?\s*\n(.*?)(?=\n\n[A-Z][a-z]+:|$)',
            r'Supporting\s+Documentation\s*[:\-]?\s*\n(.*?)(?=\n\n[A-Z][a-z]+:|$)'
        ]
        
        references_content = ""
        for pattern in references_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                references_content = match.group(1).strip()
                print(f"    📋 Found References section")
                break
        
        if not references_content:
            print(f"    📋 No References section found")
            return documents
        
        # Extract different types of references from the References section
        # 1. Policy references (mm_, ip_, ph_)
        policy_patterns = [
            (r'mm_(\d{4})', 'Medical Policy'),
            (r'ip_(\d{4})', 'Pharmacy Policy'),
            (r'ph_(\d{4})', 'Pharmacy Policy')
        ]
        
        for pattern, doc_type in policy_patterns:
            matches = re.finditer(pattern, references_content)
            for match in matches:
                policy_number = match.group(1)
                
                # Create unique identifier
                doc_id = f"{doc_type}_{policy_number}"
                if doc_id in seen_documents:
                    continue
                seen_documents.add(doc_id)
                
                # Extract title from context
                title = self.extract_reference_title_from_context(references_content, match.start(), match.end())
                
                # Construct URL
                if doc_type == 'Medical Policy':
                    policy_url = f"https://static.cigna.com/assets/chcp/pdf/coveragePolicies/medical/mm_{policy_number}_coveragepositioncriteria.pdf"
                else:
                    policy_url = f"https://static.cigna.com/assets/chcp/pdf/coveragePolicies/pharmacy/{pattern.split('_')[0]}_{policy_number}_coveragepositioncriteria.pdf"
                
                documents.append({
                    'document_title': title or f"{doc_type} {policy_number}",
                    'document_url': policy_url,
                    'document_type': doc_type
                })
        
        # 2. Clinical guidelines and standards
        guideline_patterns = [
            (r'([A-Z][^.\n]{20,150}(?:guideline|protocol|standard|recommendation)[^.\n]*)', 'Clinical Guideline'),
            (r'([A-Z][^.\n]{20,150}(?:study|research|trial)[^.\n]*)', 'Research Study'),
            (r'([A-Z][^.\n]{20,150}(?:association|society|academy)[^.\n]*)', 'Professional Organization')
        ]
        
        for pattern, doc_type in guideline_patterns:
            matches = re.finditer(pattern, references_content, re.IGNORECASE)
            for match in matches:
                guideline_text = match.group(1).strip()
                
                # Clean up the text
                guideline_text = re.sub(r'^\W+|\W+$', '', guideline_text)  # Remove leading/trailing punctuation
                guideline_text = re.sub(r'\s+', ' ', guideline_text)  # Normalize whitespace
                
                if len(guideline_text) > 20 and len(guideline_text) < 300:
                    # Create unique identifier
                    doc_id = f"{doc_type}_{guideline_text[:50]}"
                    if doc_id not in seen_documents:
                        seen_documents.add(doc_id)
                        documents.append({
                            'document_title': guideline_text,
                            'document_url': '',
                            'document_type': doc_type
                        })
        
        # 3. Extract numbered references (common in academic papers)
        numbered_refs = re.finditer(r'(\d+)\.\s*([^.\n]{20,200})', references_content)
        for match in numbered_refs:
            ref_text = match.group(2).strip()
            
            # Clean up the text
            ref_text = re.sub(r'^\W+|\W+$', '', ref_text)
            ref_text = re.sub(r'\s+', ' ', ref_text)
            
            if len(ref_text) > 20 and len(ref_text) < 300:
                # Create unique identifier
                doc_id = f"Reference_{ref_text[:50]}"
                if doc_id not in seen_documents:
                    seen_documents.add(doc_id)
                    documents.append({
                        'document_title': ref_text,
                        'document_url': '',
                        'document_type': 'Reference'
                    })
        
        print(f"    📚 Extracted {len(documents)} referenced documents from References section")
        return documents
    
    def extract_reference_title_from_context(self, text, start_pos, end_pos):
        """Extract reference title from context around a policy reference in References section"""
        try:
            # Get context around the policy reference
            context_start = max(0, start_pos - 200)
            context_end = min(len(text), end_pos + 200)
            context = text[context_start:context_end]
            
            # Use spaCy to extract meaningful sentences
            context_doc = self.nlp(context)
            
            # Look for sentences that contain the policy reference
            for sent in context_doc.sents:
                sent_text = sent.text.strip()
                
                # Skip very short or very long sentences
                if len(sent_text) < 15 or len(sent_text) > 400:
                    continue
                
                # Look for sentences that contain policy numbers
                if re.search(r'\d{4}', sent_text):
                    # Clean up the sentence
                    title = sent_text
                    # Remove common prefixes
                    title = re.sub(r'^(policy|coverage|medical|pharmacy|see|refer|also)\s*[:\-]?\s*', '', title, flags=re.IGNORECASE)
                    # Remove trailing punctuation
                    title = re.sub(r'\s*[:\-]\s*$', '', title)
                    
                    if len(title) > 15 and len(title) < 300:
                        return title
            
            return ""
        except:
            return ""

    def extract_document_changes(self, comments):
        """Extract document changes from monthly comments"""
        changes = []
        
        if not comments:
            return changes
        
        # Split comments by semicolon and process each
        comment_parts = comments.split(';')
        
        for part in comment_parts:
            part = part.strip()
            if not part:
                continue
            
            # Determine change type
            change_type = "Modification"
            if any(word in part.lower() for word in ['new', 'added', 'added']):
                change_type = "Addition"
            elif any(word in part.lower() for word in ['removed', 'deleted', 'retired']):
                change_type = "Removal"
            elif any(word in part.lower() for word in ['updated', 'modified', 'changed']):
                change_type = "Modification"
            
            changes.append({
                'document_title': 'Policy Update',
                'change_type': change_type,
                'change_description': part,
                'section_affected': 'General'
            })
        
        return changes

    def analyze_policy_with_spacy(self, policy_text, policy_url, month_year, comments=''):
        """Analyze policy using spaCy instead of OpenAI"""
        try:
            # Extract data using deterministic methods
            medical_codes = self.extract_medical_codes(policy_text)
            referenced_documents = self.extract_referenced_documents(policy_text)
            document_changes = self.extract_document_changes(comments)
            
            # Extract basic policy information
            policy_data = {
                'title': self.extract_policy_title(policy_text),
                'policy_url': policy_url,
                'published_date': self.extract_published_date(policy_text, month_year),
                'category': self.extract_category(policy_text),
                'body_content': policy_text,  # Full policy text content
                'referenced_documents': referenced_documents,
                'medical_codes': medical_codes,
                'document_changes': document_changes
            }
            
            return policy_data
            
        except Exception as e:
            print(f"❌ spaCy analysis error: {e}")
            return None
    
    def extract_policy_title(self, text):
        """Extract policy title from text"""
        # Look for title patterns
        title_patterns = [
            r'Policy Title:\s*(.+)',
            r'Coverage Policy:\s*(.+)',
            r'Medical Coverage Policy:\s*(.+)',
            r'^(.+?)\s*Coverage Criteria'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        # Fallback: use first line if it looks like a title
        first_line = text.split('\n')[0].strip()
        if len(first_line) < 100 and not first_line.isdigit():
            return first_line
        
        return "Medical Coverage Policy"

    def extract_published_date(self, text, month_year):
        """Extract published date from text"""
        # Look for date patterns
        date_patterns = [
            r'Effective Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Published Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(1)
                    # Convert to YYYY-MM-DD format
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue
        
        # Fallback: use month_year
        try:
            # Try to parse month_year like "September 2025"
            date_obj = datetime.strptime(month_year.split()[-1] + " " + month_year.split()[0], '%Y %B')
            return date_obj.strftime('%Y-%m-%d')
        except:
            return datetime.now().strftime('%Y-%m-%d')

    def extract_category(self, text):
        """Extract policy category from text"""
        if 'new' in text.lower():
            return 'New Policy'
        elif 'updated' in text.lower() or 'modified' in text.lower():
            return 'Updated Policy'
        elif 'retired' in text.lower():
            return 'Retired Policy'
        else:
            return 'Medical Policy'

    def scrape_policy_url(self, url, month_year):
        """Scrape individual policy URL and extract policy links from monthly PDF"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # For PDF URLs, we need to extract policy links from the monthly update PDF
            if url.endswith('.pdf'):
                print(f"  📄 Processing PDF: {url}")
                
                # Download and parse the PDF to extract policy links
                policy_links = self.extract_policy_links_from_pdf(response.content, month_year)
                
                if not policy_links:
                    print(f"    ⚠️ No policy links found in {month_year}")
                    return False
                
                # Process each policy link found in the monthly PDF
                policies_saved = 0
                for policy_link in policy_links:
                    print(f"    🔗 Found policy: {policy_link['title']}")
                    
                    # Fetch the individual policy document
                    policy_data = self.fetch_individual_policy(policy_link['url'], policy_link['title'], month_year, policy_link.get('comments', ''))
                    
                    if policy_data and isinstance(policy_data, dict):
                        if self.save_policy(policy_data):
                            policies_saved += 1
                    else:
                        print(f"    ⚠️ Failed to get valid policy data for {policy_link['title']}")
                
                return policies_saved > 0
            else:
                soup = BeautifulSoup(response.content, 'html.parser')
                policy_text = soup.get_text()
                
                # Analyze with spaCy
                policy_data = self.analyze_policy_with_spacy(policy_text, url, month_year)
                
                if policy_data:
                    return self.save_policy(policy_data)
            
        except Exception as e:
            print(f"  ❌ Error scraping {url}: {e}")
            return False

    def fetch_individual_policy(self, policy_url, title, month_year, comments=''):
        """Fetch individual policy document and analyze with spaCy"""
        try:
            print(f"    📄 Fetching individual policy: {policy_url}")
            
            # Fetch the actual policy PDF
            response = requests.get(policy_url, timeout=30)
            response.raise_for_status()
            
            # Extract text from the policy PDF
            policy_text = self.extract_text_from_policy_pdf(response.content)
            
            if not policy_text:
                print(f"    ⚠️ Could not extract text from {policy_url}")
                return None
            
            print(f"    📝 Extracted {len(policy_text)} characters from policy PDF")
            
            # Use spaCy to analyze the policy content
            policy_data = self.analyze_policy_with_spacy(policy_text, policy_url, month_year, comments)
            
            if policy_data and isinstance(policy_data, dict):
                # Override the generated URL with the actual scraped URL
                policy_data['policy_url'] = policy_url
                policy_data['title'] = title
                return policy_data
            else:
                print(f"    ⚠️ spaCy analysis failed or returned invalid data for {policy_url}")
                return None
                
        except Exception as e:
            print(f"    ❌ Error fetching policy {policy_url}: {e}")
        return None
    
    def save_policy(self, policy_data):
        """Save policy data to Supabase"""
        try:
            # Debug: Check if policy_data is a dictionary
            if not isinstance(policy_data, dict):
                print(f"  ❌ Policy data is not a dictionary: {type(policy_data)}")
                return False
            
            # Check if policy already exists
            existing_policy = self.supabase.table('policy_updates').select('id').eq('policy_url', policy_data.get('policy_url', '')).execute()
            
            if existing_policy.data:
                print(f"  ⚠️ Policy already exists: {policy_data.get('title', 'Unknown')[:30]}...")
                return False
            
            # Prepare data for insertion
            # Ensure no None values are saved to database
            data = {
                'title': policy_data.get('title') or 'Unknown Policy',
                'policy_url': policy_data.get('policy_url') or '',
                'monthly_pdf_url': policy_data.get('monthly_pdf_url') or '',
                'policy_number': self.extract_policy_number(policy_data.get('title') or ''),
                'published_date': policy_data.get('published_date'),
                'effective_date': policy_data.get('effective_date'),
                'category': policy_data.get('category') or 'Policy Update',
                'status': policy_data.get('status') or 'Active',
                'body_content': policy_data.get('body_content') or '',
                'month_year': policy_data.get('month_year') or ''
            }
            
            result = self.supabase.table('policy_updates').insert(data).execute()
            
            if result.data:
                policy_id = result.data[0]['id']
                print(f"  ✅ Saved policy: {data['title'][:50]}...")
                
                # Save related data
                self.save_related_data(policy_id, policy_data)
                return True
            else:
                print(f"  ❌ Failed to save policy: {result}")
                return False
                
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return False
    
    def save_related_data(self, policy_id, policy_data):
        """Save related data (medical codes, referenced documents, document changes)"""
        try:
            # Save medical codes
            for code_data in policy_data.get('medical_codes', []):
                if code_data.get('code'):  # Only save if code exists
                    self.supabase.table('medical_codes').insert({
                        'policy_update_id': policy_id,
                        'code': code_data.get('code') or '',
                        'code_type': code_data.get('code_type') or '',
                        'description': code_data.get('description') or '',
                        'is_covered': None
                    }).execute()
            
            # Save referenced documents
            for doc_data in policy_data.get('referenced_documents', []):
                if doc_data.get('document_title'):  # Only save if title exists
                    self.supabase.table('referenced_documents').insert({
                            'policy_update_id': policy_id,
                        'document_title': doc_data.get('document_title') or '',
                        'document_url': doc_data.get('document_url') or '',
                        'document_type': doc_data.get('document_type') or ''
                    }).execute()
            
            # Save document changes
            for change_data in policy_data.get('document_changes', []):
                if change_data.get('change_description'):  # Only save if description exists
                    self.supabase.table('document_changes').insert({
                        'policy_update_id': policy_id,
                        'document_title': change_data.get('document_title') or '',
                        'change_type': change_data.get('change_type') or '',
                        'change_description': change_data.get('change_description') or '',
                        'section_affected': change_data.get('section_affected') or ''
                    }).execute()
            
        except Exception as e:
            print(f"  ⚠️ Error saving related data: {e}")

    def extract_policy_number(self, title):
        """Extract policy number from title"""
        match = re.search(r'\((\d{4})\)', title)
        return match.group(1) if match else ''
    
    def run(self):
        """Main scraping function"""
        print("🏥 Starting Cigna Policy Scraper with spaCy")
        print("=" * 60)
        
        start_time = time.time()
        
        # Fetch monthly links
        monthly_links = self.fetch_monthly_links()
            
        if not monthly_links:
            print("❌ No monthly links found")
            return
        
        print(f"📅 Found {len(monthly_links)} monthly pages")
            
        # Process first 5 monthly PDFs for testing
        policies_scraped = 0
        for i, link in enumerate(monthly_links[:5]):
            print(f"\n📄 Processing {i+1}/5: {link['month_year']}")
            
            if self.scrape_policy_url(link['url'], link['month_year']):
                policies_scraped += 1
            
            execution_time = time.time() - start_time
            
        print(f"\n🎉 spaCy scraping completed!")
        print(f"📊 Total policies scraped: {policies_scraped}")
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    scraper = CignaPolicyScraper()
    scraper.run()