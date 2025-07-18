from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By

# python browser_api_test.py

from time import time

AUTH = BRIGHTDATA_BROWSERAPI_USERNAME:BRIGHTDATA_BROWSERAPI_PASSWORD
SBR_WEBDRIVER = f'https://{AUTH}@brd.superproxy.io:9515'
def main():
    t0=time()
    print('Connecting to Browser API...')
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')
    with Remote(sbr_connection, options=ChromeOptions()) as driver:
        print('Connected! Navigating...')
        # driver.get('https://example.com')
        driver.get('https://openai.com')
        # driver.get('https://budgety.ai')
        # print('Taking page screenshot to file page.png')
        # driver.get_screenshot_as_file('./page.png')
        print('Navigated! Scraping page content...')
        html = driver.page_source
        # print(html)
        print(html[:700])
        
    
    t1=time()

    print("elapsed_time: ", t1-t0)
if __name__ == '__main__':
  main()