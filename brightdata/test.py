# to run smoketest  python -m brightdata.test


from brightdata.auto import scrape_url


if __name__ == "__main__":
    
    
    # Quick smoke-test
    # url="https://www.reddit.com/r/OpenAI/"

    url="https://www.nexperia.com/product/BAV99"
    
    print("scraping")
     
    results = scrape_url(url, fallback_to_browser_api=True)

    print(results)

    results.save_data_to_file(raise_if_empty=False)
    
    print("saved")
   
