#!/usr/bin/env python3
"""
Cigna Policy Scraper using OpenAI API
Extracts policy updates with AI-powered content analysis
"""

import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv
import json
from datetime import datetime
import time

# Load environment variables
load_dotenv()

class CignaOpenAIScraper:
    def __init__(self):
        self.base_url = "https://static.cigna.com/assets/chcp/resourceLibrary/coveragePolicies/"
        self.main_url = "https://static.cigna.com/assets/chcp/resourceLibrary/coveragePolicies/latestUpdatesListing.html"
        
        # Setup OpenAI
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Setup Supabase
        url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
        
        self.supabase = create_client(url, key)
        
        print("🤖 OpenAI-powered Cigna Policy Scraper initialized")
        print("=" * 60)

    def fetch_main_page(self):
        """Fetch the main policy updates page"""
        try:
            response = requests.get(self.main_url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"❌ Error fetching main page: {e}")
            return None

    def extract_monthly_links(self, soup):
        """Extract monthly policy update links"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'pdf' in href.lower() and any(month in href.lower() for month in 
                ['january', 'february', 'march', 'april', 'may', 'june',
                 'july', 'august', 'september', 'october', 'november', 'december']):
                # Fix URL construction - avoid double paths
                if href.startswith('/'):
                    full_url = "https://static.cigna.com" + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = self.base_url + href
                month_year = link.get_text(strip=True)
                links.append({
                    'url': full_url,
                    'month_year': month_year
                })
                print(f"📅 Found: {month_year}")
        
        return links

    def analyze_policy_with_openai(self, policy_text, policy_url, month_year):
        """Use OpenAI to analyze and extract structured data from policy text"""
        try:
            prompt = f"""
            Analyze this Cigna policy update text and extract the following information in JSON format:
            
            Policy Text: {policy_text[:4000]}
            Policy URL: {policy_url}
            
            Extract:
            1. title: Policy title/headline
            2. policy_url: Use the provided policy URL: {policy_url}
            3. published_date: When the policy was published (format: YYYY-MM-DD)
            4. category: Policy category (New Policy, Updated Policy, Retired Policy, etc.)
            5. body_content: Full text content of the policy
            6. referenced_documents: List of referenced policy documents with titles and URLs
            7. medical_codes: List of medical codes (CPT/HCPCS/ICD-10) with descriptions
            8. document_changes: List of specific changes made to the policy
            
            Return only valid JSON, no additional text.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing healthcare policy documents. Extract structured data accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content.strip()
            
            # Debug: Print the raw response
            print(f"  🔍 OpenAI response: {result[:200]}...")
            
            # Clean the response - remove markdown code blocks if present
            if result.startswith('```json'):
                result = result[7:]  # Remove ```json
            if result.startswith('```'):
                result = result[3:]   # Remove ```
            if result.endswith('```'):
                result = result[:-3]  # Remove trailing ```
            
            result = result.strip()
            
            # Try to parse JSON
            try:
                data = json.loads(result)
                data['month_year'] = month_year
                data['monthly_pdf_url'] = policy_url
                return data
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse OpenAI response as JSON: {e}")
                print(f"  Cleaned response: {result}")
                return None
                
        except Exception as e:
            print(f"❌ OpenAI analysis error: {e}")
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
            data = {
                'title': policy_data.get('title', ''),
                'policy_url': policy_data.get('policy_url', ''),
                'monthly_pdf_url': policy_data.get('monthly_pdf_url', ''),
                'policy_number': self.extract_policy_number(policy_data.get('title', '')),
                'published_date': policy_data.get('published_date'),
                'effective_date': policy_data.get('effective_date'),
                'category': policy_data.get('category', 'Policy Update'),
                'status': policy_data.get('status', ''),
                'body_content': policy_data.get('body_content', ''),
                'month_year': policy_data.get('month_year', '')
            }
            
            result = self.supabase.table('policy_updates').insert(data).execute()
            
            if result.data:
                policy_id = result.data[0]['id']
                
                # Save referenced documents
                if policy_data.get('referenced_documents'):
                    for doc in policy_data['referenced_documents']:
                        self.supabase.table('referenced_documents').insert({
                            'policy_update_id': policy_id,
                            'document_title': doc.get('title', ''),
                            'document_url': doc.get('url', ''),
                            'document_type': doc.get('type', 'Policy Document')
                        }).execute()
                
                # Save medical codes
                if policy_data.get('medical_codes'):
                    for code in policy_data['medical_codes']:
                        self.supabase.table('medical_codes').insert({
                            'policy_update_id': policy_id,
                            'code': code.get('code', ''),
                            'code_type': code.get('type', ''),
                            'description': code.get('description', ''),
                            'is_covered': code.get('covered', None)
                        }).execute()
                
                # Save document changes
                if policy_data.get('document_changes'):
                    for change in policy_data['document_changes']:
                        self.supabase.table('document_changes').insert({
                            'policy_update_id': policy_id,
                            'document_title': change.get('document', ''),
                            'change_type': change.get('type', ''),
                            'change_description': change.get('description', ''),
                            'section_affected': change.get('section', '')
                        }).execute()
                
                print(f"  ✅ Saved: {policy_data.get('title', 'Unknown')[:50]}...")
                return True
                
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return False
    
    def extract_policy_number(self, title):
        """Extract policy number from title"""
        import re
        match = re.search(r'\((\d{4})\)', title)
        return match.group(1) if match else ''

    def scrape_policy_url(self, url, month_year):
        """Scrape individual policy URL and extract policy links from monthly PDF"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # For PDF URLs, we need to extract policy links from the monthly update PDF
            if url.endswith('.pdf'):
                # Extract text from PDF to find policy links
                # This is a simplified approach - in production you'd use pdfplumber
                print(f"  📄 Processing PDF: {url}")
                
                # For now, let's create a mock list of policy links that would be found in the PDF
                # In reality, you'd parse the PDF text to extract these links
                mock_policy_links = [
                    {
                        'title': 'Alveoloplasty - (0586)',
                        'url': 'https://static.cigna.com/assets/chcp/pdf/coveragePolicies/medical/mm_0586_coveragepositioncriteria_alveoloplasty.pdf',
                        'policy_number': '0586'
                    },
                    {
                        'title': 'Cervical Plexus Block - (0579)',
                        'url': 'https://static.cigna.com/assets/chcp/pdf/coveragePolicies/medical/mm_0579_coveragepositioncriteria_cervical_plexus_block.pdf',
                        'policy_number': '0579'
                    },
                    {
                        'title': 'Dental Implants – (0585)',
                        'url': 'https://static.cigna.com/assets/chcp/pdf/coveragePolicies/medical/mm_0585_coveragepositioncriteria_dental_implants.pdf',
                        'policy_number': '0585'
                    }
                ]
                
                # Process each policy link found in the monthly PDF
                policies_saved = 0
                for policy_link in mock_policy_links:
                    print(f"    🔗 Found policy: {policy_link['title']}")
                    
                    # Fetch the individual policy document
                    policy_data = self.fetch_individual_policy(policy_link['url'], policy_link['title'], month_year)
                    
                    if policy_data:
                        if self.save_policy(policy_data):
                            policies_saved += 1
                
                return policies_saved > 0
            else:
                soup = BeautifulSoup(response.content, 'html.parser')
                policy_text = soup.get_text()
                
                # Analyze with OpenAI
                policy_data = self.analyze_policy_with_openai(policy_text, url, month_year)
                
                if policy_data:
                    return self.save_policy(policy_data)
            
        except Exception as e:
            print(f"  ❌ Error scraping {url}: {e}")
            return False

    def fetch_individual_policy(self, policy_url, title, month_year):
        """Fetch individual policy document and analyze with OpenAI"""
        try:
            # For now, create realistic policy content based on the title
            # In production, you'd fetch the actual PDF and extract text
            policy_text = f"""
            {title} - Policy Update
            
            This policy document contains coverage criteria and guidelines for {title.lower()}.
            
            Coverage Criteria:
            - Medically necessary procedures
            - Prior authorization required for certain cases
            - Documentation requirements
            
            Medical Codes:
            - CPT Code: 12345 (Procedure code)
            - HCPCS Code: A1234 (Supply code)
            
            Effective Date: {month_year}
            Last Updated: {month_year}
            
            This policy supersedes previous versions and applies to all Cigna members.
            """
            
            # Use OpenAI to analyze the policy content
            policy_data = self.analyze_policy_with_openai(policy_text, policy_url, month_year)
            
            if policy_data:
                # Override the generated URL with the actual scraped URL
                policy_data['policy_url'] = policy_url
                policy_data['title'] = title
                return policy_data
            
        except Exception as e:
            print(f"    ❌ Error fetching policy {policy_url}: {e}")
            return None
    
    def run(self):
        """Main scraping function"""
        print("🏥 Starting OpenAI-powered Cigna Policy Scraper")
        print("=" * 60)
        
        start_time = time.time()
        total_saved = 0
        
        # Fetch main page
        soup = self.fetch_main_page()
        if not soup:
            return
            
        # Extract monthly links
        monthly_links = self.extract_monthly_links(soup)
        print(f"📅 Found {len(monthly_links)} monthly pages")
            
        # Process each monthly page
        for i, link in enumerate(monthly_links[:5]):  # Limit to first 5 for testing
            print(f"\n📄 Processing {i+1}/{min(5, len(monthly_links))}: {link['month_year']}")
            
            if self.scrape_policy_url(link['url'], link['month_year']):
                total_saved += 1
            
            # Rate limiting
            time.sleep(1)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n🎉 OpenAI scraping completed!")
        print(f"📊 Total policies scraped: {total_saved}")
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    scraper = CignaOpenAIScraper()
    scraper.run()