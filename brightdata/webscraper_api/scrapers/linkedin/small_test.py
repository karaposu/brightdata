# run with  python -m brightdata.webscraper_api.scrapers.linkedin.small_test


from brightdata.webscraper_api.scrapers.linkedin import LinkedInScraper
from brightdata.utils import show_scrape_results   # unified pretty-printer


def main() -> None:
    scraper = LinkedInScraper()           # token from env
    

    sample = "https://www.linkedin.com/in/enes-kuzucu/"
    sid= scraper.collect_by_url(sample)
    
    res = scraper.poll_until_ready(sid)
    
    print("type(res) ",type(res) )
    print(res)
    # show_scrape_results(f"collect_by_url → {kind}", res)
    

if __name__ == "__main__":
    main()