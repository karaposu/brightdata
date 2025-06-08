from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
AUTH = 'brd-customer-hl_1cdf8003-zone-scraping_browser1:f05i50grymt3'
SBR_WEBDRIVER = f'https://{AUTH}@brd.superproxy.io:9515'
def main():
    print('Connecting to Browser API...')
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')
    with Remote(sbr_connection, options=ChromeOptions()) as driver:
        print('Connected! Navigating...')
        # driver.get('https://example.com')
        driver.get('https://budgety.ai')
        print('Taking page screenshot to file page.png')
        driver.get_screenshot_as_file('./page.png')
        print('Navigated! Scraping page content...')
        html = driver.page_source
        print(html)
if __name__ == '__main__':
  main()