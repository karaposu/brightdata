# demo_registry.py


# python -m brightdata.demo_registry
import os, sys
from pprint import pprint
from dotenv import load_dotenv

from brightdata.registry import get_scraper_for
from brightdata.utils.poll import poll_until_ready

load_dotenv()
TOKEN = os.getenv("BRIGHTDATA_TOKEN") or sys.exit("Set BRIGHTDATA_TOKEN")

urls = [
    "https://www.amazon.de/dp/B0CRMZHDG8",
    "https://www.digikey.com/en/products/detail/stmicroelectronics/STM32F407VGT6/2747117",
    "https://www.mouser.co.uk/ProductDetail/Diotec-Semiconductor/BAV99?qs=sGAEpiMZZMtbRapU8LlZDx2r3HTumQni5UY%252Bzi41ryxF5nfDFQU%252BRw%3D%3D",
]

for u in urls:
    print(" ")
    print(" ")
    ScraperCls = get_scraper_for(u)
    print("ScraperCls found", ScraperCls)
    if not ScraperCls:

        print("No scraper for", u)
        continue
    
    snap = ScraperCls(bearer_token=TOKEN).collect_by_url([u])
    res  = poll_until_ready(ScraperCls(bearer_token=TOKEN), snap)
    
    print(f"\n{u}\n→ {res.status} {res.error or ''}")
    if res.status == "ready":
        pprint(res.data[0])
