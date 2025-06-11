from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
import os

#   BRIGHTDATA_BROWSERAPI_USERNAME
#     BRIGHTDATA_BROWSERAPI_PASSWORD


class BrowserAPI:
    """
    Wrapper around Bright Data's Browser API (Selenium) with:
      • get_page_source()
      • get_page_source_and_wait()
      • capture_screenshot()
    """

    DEFAULT_HOST = "brd.superproxy.io"
    DEFAULT_PORT = 9515
    
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        host: str = DEFAULT_HOST,
        scheme: str = "https",
        headless: bool = True,
        window_size: tuple[int, int] = (1920, 1080),
    ):
        load_dotenv()

        # 1) Load from env if not provided
        env_user = os.getenv("BRIGHTDATA_BROWSERAPI_USERNAME")
        env_pass = os.getenv("BRIGHTDATA_BROWSERAPI_PASSWORD")
        
        self.username = username or env_user
        self.password = password or env_pass
    
        if not (self.username and self.password):
            raise ValueError(
                "BrowserAPI requires username & password; "
                "set BRIGHTDATA_BROWSERAPI_USERNAME and BRIGHTDATA_BROWSERAPI_PASSWORD"
                "username should look like this:"
                "brd-customer-hl_1434343-zone-scraping_browser1"
            )

        # 2) Build endpoint with fixed port
        self._endpoint = f"{scheme}://{self.username}:{self.password}@{host}:{self.DEFAULT_PORT}"

        opts = ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        self._opts = opts

    def _new_driver(self) -> Remote:
        conn = ChromiumRemoteConnection(self._endpoint, "goog", "chrome")
        return Remote(conn, options=self._opts)

    def get_page_source(
        self,
        url: str,
    ) -> str:
        """
        Navigate to `url` and return the raw page_source immediately.
        """
        driver = self._new_driver()
        try:
            driver.get(url)
            return driver.page_source
        finally:
            driver.quit()

    def get_page_source_with_a_delay(
        self,
        url: str,
        wait_time_in_seconds: int = 20,
        extra_delay: float = 1.0,
    ) -> str:
        """
        Navigate to `url`, wait until <div id="main"> is present
        (SPA shell hydration), then return fully rendered HTML.
        """
        driver = self._new_driver()
        try:
            driver.get(url)
            WebDriverWait(driver, wait_time_in_seconds).until(
                EC.presence_of_element_located((By.ID, "main"))
            )
            time.sleep(extra_delay)
            return driver.page_source
        finally:
            driver.quit()

    def capture_screenshot(
        self,
        url: str,
        path: str,
        wait_for_main: bool = False,
        wait_time_in_seconds: int = 20,
        extra_delay: float = 1.0,
    ) -> None:
        """
        Navigate to `url` and save a screenshot to `path`.
        If wait_for_main is True, first wait until <div id="main"> appears.
        """
        driver = self._new_driver()
        try:
            driver.get(url)
            if wait_for_main:
                WebDriverWait(driver, wait_time_in_seconds).until(
                    EC.presence_of_element_located((By.ID, "main"))
                )
                time.sleep(extra_delay)
            driver.get_screenshot_as_file(path)
        finally:
            driver.quit()


def main():
    # AUTH = "brd-customer-hl_1cdf8003-zone-scraping_browser1:f05i50grymt3"
    # api = BrowserAPI(AUTH)

  

    api = BrowserAPI(
    username="brd-customer-hl_1cdf8003-zone-scraping_browser1",
    password="f05i50grymt3",
)

    target_page_address="https://budgety.ai"
    
    # 1) Just grab the raw HTML immediately:
    # html_raw = api.get_page_source(target_page_address)
    # print(html_raw)
    
    
    # 2) Grab the hydrated HTML by waiting for the headline:
    html_hydrated = api.get_page_source_with_a_delay(target_page_address)
    print(html_hydrated)

    #api.capture_screenshot(target_page_address, "budgety.png", wait_for_main=True, wait_time_in_seconds=30)


if __name__ == "__main__":
    main()