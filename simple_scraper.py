#!/usr/bin/env python3
"""
Simple Cigna Policy Scraper
A standalone version without complex imports
"""

import os
import sys
import time
import requests
import asyncio
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client
import PyPDF2
import io
import re

# Load environment variables
load_dotenv()

class SimpleCignaScraper:
    def __init__(self):
        self.base_url = "https://static.cigna.com/assets/chcp/resourceLibrary/coveragePolicies/"
        self.main_url = "https://static.cigna.com/assets/chcp/resourceLibrary/coveragePolicies/latestUpdatesListing.html"
        
        # Setup Supabase
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
        
        self.supabase = create_client(url, key)
        
        # Setup requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CignaPolicyScraper/1.0 (Educational Purpose)'
        })
    
    def scrape_main_page(self):
        """Scrape the main policy updates page"""
        print(f"🔍 Fetching main page: {self.main_url}")
        
        try:
            response = self.session.get(self.main_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find monthly update links
            monthly_links = []
            links = soup.find_all('a', href=True)
            
            for link in links:
                link_text = link.get_text(strip=True)
                href = link.get('href', '')
                
                if 'Policy Updates' in link_text and href:
                    month_year = self.extract_month_year(link_text)
                    full_url = urljoin(self.base_url, href)
                    
                    monthly_links.append({
                        'month_year': month_year,
                        'url': full_url,
                        'link_text': link_text
                    })
                    
                    print(f"📅 Found: {month_year}")
            
            return monthly_links
            
        except Exception as e:
            print(f"❌ Error fetching main page: {e}")
            return []
    
    def extract_month_year(self, link_text):
        """Extract month and year from link text"""
        import re
        match = re.search(r'Policy Updates\s+(\w+\s+\d{4})', link_text)
        if match:
            return match.group(1)
        return link_text.replace('Policy Updates', '').strip()
    
    def scrape_monthly_page(self, month_info):
        """Scrape a monthly policy PDF"""
        print(f"📄 Scraping PDF: {month_info['month_year']}")
        
        try:
            # Check if this is a PDF file
            if month_info['url'].endswith('.pdf'):
                return self.scrape_pdf_policy(month_info)
            else:
                # Handle HTML pages (if any)
                return self.scrape_html_page(month_info)
                
        except Exception as e:
            print(f"❌ Error scraping monthly page: {e}")
            return 0
    
    def scrape_pdf_policy(self, month_info):
        """Scrape policy data from PDF"""
        try:
            print(f"  📋 Processing PDF: {month_info['url']}")
            
            # Download PDF
            response = self.session.get(month_info['url'], timeout=30)
            response.raise_for_status()
            
            # Extract text from PDF
            pdf_text = self.extract_pdf_text(response.content)
            
            if not pdf_text:
                print(f"  ❌ Could not extract text from PDF")
                return 0
            
            print(f"  📝 Extracted {len(pdf_text)} characters from PDF")
            
            # Parse the PDF text to find individual policies
            policies = self.parse_pdf_policies(pdf_text, month_info)
            
            # Save each policy
            policies_saved = 0
            for policy_data in policies:
                if policy_data:
                    self.save_policy(policy_data)
                    policies_saved += 1
                    print(f"  ✅ Saved: {policy_data['title'][:50]}...")
            
            print(f"  📊 Saved {policies_saved} policies from PDF")
            return policies_saved
            
        except Exception as e:
            print(f"  ❌ Error processing PDF: {e}")
            return 0
    
    def extract_pdf_text(self, pdf_content):
        """Extract text from PDF content"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            return text
            
        except Exception as e:
            print(f"  ❌ PDF extraction error: {e}")
            return ""
    
    def parse_pdf_policies(self, pdf_text, month_info):
        """Parse PDF text to extract individual policies"""
        policies = []
        
        # Split text into sections (look for policy titles)
        # Common patterns for policy titles in PDFs
        policy_patterns = [
            r'([A-Z][^.]*Policy[^.]*)',
            r'([A-Z][^.]*Coverage[^.]*)',
            r'([A-Z][^.]*Guideline[^.]*)',
            r'([A-Z][^.]*Update[^.]*)',
        ]
        
        # Try to find policy sections
        lines = pdf_text.split('\n')
        current_policy = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this looks like a policy title
            is_policy_title = False
            for pattern in policy_patterns:
                if re.search(pattern, line) and len(line) > 10 and len(line) < 200:
                    is_policy_title = True
                    break
            
            if is_policy_title:
                # Save previous policy if exists
                if current_policy:
                    policies.append(current_policy)
                
                # Start new policy
                current_policy = {
                    'title': line,
                    'url': month_info['url'],
                    'published_date': None,
                    'category': 'Policy Update',
                    'body_content': line,
                    'month_year': month_info['month_year']
                }
            elif current_policy:
                # Add to current policy content
                current_policy['body_content'] += '\n' + line
        
        # Add last policy
        if current_policy:
            policies.append(current_policy)
        
        # If no policies found, create one from the whole PDF
        if not policies:
            policies.append({
                'title': f"Policy Updates - {month_info['month_year']}",
                'url': month_info['url'],
                'published_date': None,
                'category': 'Policy Update',
                'body_content': pdf_text[:2000],  # First 2000 chars
                'month_year': month_info['month_year']
            })
        
        return policies[:10]  # Limit to 10 policies per PDF
    
    def scrape_individual_policy(self, policy_url, month_year):
        """Scrape an individual policy page"""
        try:
            response = self.session.get(policy_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract policy data
            title = self.extract_title(soup)
            if not title:
                return None
            
            published_date = self.extract_published_date(soup)
            category = self.extract_category(soup)
            body_content = self.extract_body_content(soup)
            
            return {
                'title': title,
                'url': policy_url,
                'published_date': published_date,
                'category': category,
                'body_content': body_content,
                'month_year': month_year
            }
            
        except Exception as e:
            print(f"❌ Error scraping policy {policy_url}: {e}")
            return None
    
    def extract_title(self, soup):
        """Extract policy title"""
        # Try multiple selectors
        for selector in ['h1', 'h2.title', '.policy-title', '.title', 'title']:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        
        return ""
    
    def extract_published_date(self, soup):
        """Extract published date"""
        import re
        text_content = soup.get_text()
        
        # Look for date patterns
        date_patterns = [
            r'\b(\w+ \d{1,2}, \d{4})\b',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_content)
            if match:
                try:
                    date_str = match.group(1)
                    for fmt in ['%B %d, %Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(date_str, fmt).isoformat()
                        except ValueError:
                            continue
                except Exception:
                    continue
        
        return None
    
    def extract_category(self, soup):
        """Extract policy category"""
        # Look for category indicators
        for selector in ['.category', '.policy-category', '.type']:
            elem = soup.select_one(selector)
            if elem:
                category = elem.get_text(strip=True)
                if category:
                    return category
        
        return "Policy Update"
    
    def extract_body_content(self, soup):
        """Extract main body content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content area
        for selector in ['.content', '.main-content', '.policy-content', '.body', 'main', 'article']:
            elem = soup.select_one(selector)
            if elem:
                content = elem.get_text(separator='\n', strip=True)
                if len(content) > 100:
                    return content
        
        # Fallback: get all text content
        return soup.get_text(separator='\n', strip=True)
    
    def save_policy(self, policy_data):
        """Save policy to Supabase"""
        try:
            data = {
                'title': policy_data['title'],
                'url': policy_data['url'],
                'published_date': policy_data['published_date'],
                'category': policy_data['category'],
                'body_content': policy_data['body_content'],
                'month_year': policy_data['month_year']
            }
            
            result = self.supabase.table('policy_updates').insert(data).execute()
            
            if result.data:
                print(f"  💾 Saved to database: {policy_data['title'][:30]}...")
            else:
                print(f"  ❌ Failed to save: {policy_data['title'][:30]}...")
                
        except Exception as e:
            print(f"  ❌ Database error: {e}")
    
    def run(self):
        """Main scraping method"""
        print("🏥 Starting Cigna Policy Scraper")
        print("=" * 50)
        
        start_time = time.time()
        total_policies = 0
        
        try:
            # Get monthly links
            monthly_links = self.scrape_main_page()
            
            if not monthly_links:
                print("❌ No monthly links found")
                return
            
            print(f"📅 Found {len(monthly_links)} monthly pages")
            
            # Scrape each monthly page (limit to 3 for testing)
            for month_link in monthly_links[:3]:
                policies_scraped = self.scrape_monthly_page(month_link)
                total_policies += policies_scraped
                
                time.sleep(2)  # Be respectful
            
            execution_time = time.time() - start_time
            
            print("\n🎉 Scraping completed!")
            print(f"📊 Total policies scraped: {total_policies}")
            print(f"⏱️  Execution time: {execution_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Critical error: {e}")

def main():
    try:
        scraper = SimpleCignaScraper()
        scraper.run()
    except Exception as e:
        print(f"❌ Failed to initialize scraper: {e}")

if __name__ == "__main__":
    main()
