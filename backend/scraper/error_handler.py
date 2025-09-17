"""
Error handling and logging utilities for the scraper
"""

import logging
import os
from datetime import datetime
from typing import Optional
import traceback

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.supabase_client import supabase_client
from database.models import ScrapingLog


class ErrorHandler:
    """Handles errors and logging for the scraper"""
    
    def __init__(self):
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scraper.log'),
                logging.StreamHandler()
            ]
        )
    
    async def log_error(self, error_type: str, error_message: str, url: str = "") -> None:
        """Log error to both file and database"""
        try:
            # Log to file
            logger = logging.getLogger(__name__)
            logger.error(f"{error_type}: {error_message} (URL: {url})")
            
            # Log to database
            log_entry = ScrapingLog(
                url=url,
                status='error',
                error_message=f"{error_type}: {error_message}",
                timestamp=datetime.now()
            )
            
            await supabase_client.insert_scraping_log(log_entry)
            
        except Exception as e:
            # Fallback logging if database fails
            logging.error(f"Failed to log error to database: {e}")
    
    async def log_success(self, url: str, records_scraped: int, execution_time: float) -> None:
        """Log successful scraping operation"""
        try:
            log_entry = ScrapingLog(
                url=url,
                status='success',
                records_scraped=records_scraped,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            await supabase_client.insert_scraping_log(log_entry)
            
        except Exception as e:
            logging.error(f"Failed to log success: {e}")
    
    def log_warning(self, message: str) -> None:
        """Log warning message"""
        logger = logging.getLogger(__name__)
        logger.warning(message)
    
    def log_info(self, message: str) -> None:
        """Log info message"""
        logger = logging.getLogger(__name__)
        logger.info(message)
    
    def log_debug(self, message: str) -> None:
        """Log debug message"""
        logger = logging.getLogger(__name__)
        logger.debug(message)