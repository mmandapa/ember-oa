"""
Main scraper for Cigna Policy Updates
Handles the complete scraping workflow from main page to individual policy updates
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
import re

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.supabase_client import supabase_client
from database.models import PolicyUpdate, ReferencedDocument, MedicalCode, DocumentChange, ScrapingLog
from scraper.data_extractor import DataExtractor
from scraper.error_handler import ErrorHandler
from scraper.validators import DataValidator

logger = logging.getLogger(__name__)


class CignaPolicyScraper:
    """Main scraper class for Cigna policy updates"""
    
    def __init__(self):
        self.base_url = "https://static.cigna.com/assets/chcp/resourceLibrary/coveragePolicies/"
        self.main_url = "https://static.cigna.com/assets/chcp/resourceLibrary/coveragePolicies/latestUpdatesListing.html"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CignaPolicyScraper/1.0 (Educational Purpose)'
        })
        
        self.data_extractor = DataExtractor()
        self.error_handler = ErrorHandler()
        self.validator = DataValidator()
        
        # Initialize Selenium driver for dynamic content
        self.driver = None
        self._setup_selenium()
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver for dynamic content"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            self.driver = None
    
    async def scrape_all_policies(self) -> Dict[str, Any]:
        """
        Main scraping method that orchestrates the entire process
        Returns summary of scraping results
        """
        start_time = time.time()
        scraping_summary = {
            'total_monthly_pages': 0,
            'total_policies_scraped': 0,
            'total_errors': 0,
            'execution_time': 0,
            'monthly_summaries': []
        }
        
        try:
            logger.info("Starting comprehensive Cigna policy scraping")
            
            # Step 1: Get all monthly update links from main page
            monthly_links = await self._get_monthly_update_links()
            scraping_summary['total_monthly_pages'] = len(monthly_links)
            
            logger.info(f"Found {len(monthly_links)} monthly update pages to scrape")
            
            # Step 2: Scrape each monthly page
            for month_link in monthly_links:
                month_summary = await self._scrape_monthly_page(month_link)
                scraping_summary['monthly_summaries'].append(month_summary)
                scraping_summary['total_policies_scraped'] += month_summary['policies_scraped']
                scraping_summary['total_errors'] += month_summary['errors']
                
                # Add delay between requests
                await asyncio.sleep(2)
            
            scraping_summary['execution_time'] = time.time() - start_time
            
            logger.info(f"Scraping completed. Total policies: {scraping_summary['total_policies_scraped']}")
            
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}")
            scraping_summary['total_errors'] += 1
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return scraping_summary
    
    async def _get_monthly_update_links(self) -> List[Dict[str, str]]:
        """
        Extract all monthly update links from the main page
        Returns list of dictionaries with month info and URLs
        """
        monthly_links = []
        
        try:
            logger.info(f"Fetching main page: {self.main_url}")
            response = self.session.get(self.main_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all monthly update links
            # Based on the website structure, look for links containing "Policy Updates"
            links = soup.find_all('a', href=True)
            
            for link in links:
                link_text = link.get_text(strip=True)
                href = link.get('href', '')
                
                # Check if this is a monthly policy update link
                if 'Policy Updates' in link_text and href:
                    # Extract month and year from link text
                    month_year = self._extract_month_year(link_text)
                    
                    # Convert relative URL to absolute
                    full_url = urljoin(self.base_url, href)
                    
                    monthly_links.append({
                        'month_year': month_year,
                        'url': full_url,
                        'link_text': link_text
                    })
                    
                    logger.info(f"Found monthly link: {month_year} -> {full_url}")
            
            logger.info(f"Extracted {len(monthly_links)} monthly update links")
            
        except Exception as e:
            logger.error(f"Error extracting monthly links: {e}")
            await self.error_handler.log_error("monthly_links_extraction", str(e), self.main_url)
        
        return monthly_links
    
    def _extract_month_year(self, link_text: str) -> str:
        """Extract month and year from link text"""
        # Examples: "Policy Updates September 2025", "Policy Updates August 2024"
        match = re.search(r'Policy Updates\s+(\w+\s+\d{4})', link_text)
        if match:
            return match.group(1)
        return link_text.replace('Policy Updates', '').strip()


async def main():
    """Main function to run the scraper"""
    scraper = CignaPolicyScraper()
    
    # Initialize database
    await supabase_client.initialize_database()
    
    # Run scraping
    summary = await scraper.scrape_all_policies()
    
    print(f"Scraping Summary:")
    print(f"Total Monthly Pages: {summary['total_monthly_pages']}")
    print(f"Total Policies Scraped: {summary['total_policies_scraped']}")
    print(f"Total Errors: {summary['total_errors']}")
    print(f"Execution Time: {summary['execution_time']:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())