"""
BrightData Web Scraper API module
"""

from .base_specialized_scraper import BrightdataBaseSpecializedScraper
from .registry import register, get_scraper_for

__all__ = [
    'BrightdataBaseSpecializedScraper',
    'register',
    'get_scraper_for',
]