
# Brightdata Utils

Python wrapper for Brightdata APIs.  Brightdata provides various data scraping APIs and once triggered they scrape the webpages with their custom scraper and gives you the data. 

From their Website :
"Dedicated endpoints for extracting fresh, structured web data from over 120 popular domains. 100% compliant and ethical scraping."

LinkedIn people profiles, 
Amazon products
Instagram - Profiles
Linkedin job listings information
TikTok - Profiles
Youtube
Airbnb

and many more. 

To use the webunlocker you must have a brightdata account and use it to create a webunlocker scraper ( a.k.a zone) in admin panel and get the below credentials.

BRIGHTDATA_WEBUNCLOKCER_BEARER
BRIGHTDATA_WEBUNCLOKCER_APP_ZONE_STRING

once you have these credentials simply put them in .env file 

you can create custom scrapers (because not all scrape APIs are following similar pattern)

via 
from brightdata.base_specialized_scraper import BrightdataBaseSpecializedScraper