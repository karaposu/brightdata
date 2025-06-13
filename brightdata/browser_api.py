# browser_api.py

# to run python -m brightdata.browser_api

import os
import time
import pathlib
import tldextract
import requests
from dotenv import load_dotenv
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import asyncio
from selenium.common.exceptions import WebDriverException, TimeoutException

from typing import Any
from brightdata.models import ScrapeResult
from datetime import datetime     

class BrowserAPI:
    """
    Wrapper around Bright Data's Browser API (Selenium) that returns ScrapeResult.
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
        env_user = os.getenv("BRIGHTDATA_BROWSERAPI_USERNAME")
        env_pass = os.getenv("BRIGHTDATA_BROWSERAPI_PASSWORD")

        self.username = username or env_user
        self.password = password or env_pass
        if not (self.username and self.password):
            raise ValueError(
                "BrowserAPI requires BRIGHTDATA_BROWSERAPI_USERNAME and _PASSWORD"
            )

        self._endpoint = (
            f"{scheme}://{self.username}:{self.password}@{host}:{self.DEFAULT_PORT}"
        )

        opts = ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        self._opts = opts

    def _new_driver(self) -> Remote:
        conn = ChromiumRemoteConnection(self._endpoint, "goog", "chrome")
        return Remote(conn, options=self._opts)

    def _make_result(
        self,
        url: str,
        *,
        success: bool,
        status: str,
        data: Any = None,
        error: str | None = None,
        request_sent_at: datetime | None = None,
        data_received_at: datetime | None = None,
    ) -> ScrapeResult:
        ext = tldextract.extract(url)
        return ScrapeResult(
            success=success,
            url=url,
            status=status,
            data=data,
            error=error,
            snapshot_id=None,
            cost=None,
            fallback_used=True,
            root_domain=ext.domain or None,
            request_sent_at=request_sent_at,
            data_received_at=data_received_at,
        )
    
    def get_page_source(self, url: str) -> ScrapeResult:
        driver = self._new_driver()
        try:
            sent = datetime.utcnow()
            driver.get(url)
            html = driver.page_source
            received = datetime.utcnow()
            return self._make_result(
                url,
                success=True,
                status="ready",
                data=html,
                request_sent_at=sent,
                data_received_at=received,
            )
        except Exception as e:
            # build a friendly error string (unchanged)
            if isinstance(e, WebDriverException):
                msg = e.msg or repr(e)
            elif getattr(e, "args", None):
                msg = "; ".join(map(str, e.args))
            else:
                msg = repr(e)
            return self._make_result(
                url,
                success=False,
                status="error",
                error=msg,
                request_sent_at=sent,
                data_received_at=datetime.utcnow(),
            )
        finally:
            driver.quit()

        


    def get_page_source_with_a_delay(
        self,
        url: str,
        wait_time_in_seconds: int = 20,
        extra_delay: float = 1.0,
    ) -> ScrapeResult:
        driver = self._new_driver()
        try:
            sent = datetime.utcnow()
            driver.get(url)
            WebDriverWait(driver, wait_time_in_seconds).until(
                EC.presence_of_element_located((By.ID, "main"))
            )
            time.sleep(extra_delay)
            html = driver.page_source
            received = datetime.utcnow()
            return self._make_result(
                url,
                success=True,
                status="ready",
                data=html,
                request_sent_at=sent,
                data_received_at=received,
            )

        except TimeoutException:
            msg = f'<div id="main"> not found after {wait_time_in_seconds}s'
            return self._make_result(
                url,
                success=False,
                status="error",
                error=msg,
                request_sent_at=sent,
                data_received_at=datetime.utcnow(),
            )

        except Exception as e:
            if isinstance(e, WebDriverException):
                msg = e.msg or repr(e)
            elif getattr(e, "args", None):
                msg = "; ".join(map(str, e.args))
            else:
                msg = repr(e)
            return self._make_result(
                url,
                success=False,
                status="error",
                error=msg,
                request_sent_at=sent,
                data_received_at=datetime.utcnow(),
            )
        finally:
            driver.quit()

            

    def capture_screenshot(
        self,
        url: str,
        path: str,
        wait_for_main: bool = False,
        wait_time_in_seconds: int = 20,
        extra_delay: float = 1.0,
    ) -> ScrapeResult:
        """
        Save a screenshot to `path`; return ScrapeResult.status = "ready"/"error".
        """
        driver = self._new_driver()
        try:
            driver.get(url)
            if wait_for_main:
                WebDriverWait(driver, wait_time_in_seconds).until(
                    EC.presence_of_element_located((By.ID, "main"))
                )
                time.sleep(extra_delay)
            filepath = pathlib.Path(path)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            driver.save_screenshot(path)
            return self._make_result(
                url, success=True, status="ready", data=path
            )
        except Exception as e:
            return self._make_result(url, success=False, status="error", error=str(e))
        finally:
            driver.quit()


    
    async def get_page_source_async(
        self,
        url: str,
    ) -> str:
        """
        Async wrapper around get_page_source().
        Offloads the blocking Selenium call into a thread so you can await it.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.get_page_source(url)
        )

    async def get_page_source_with_a_delay_async(
        self,
        url: str,
        wait_time_in_seconds: int = 20,
        extra_delay: float = 1.0,
    ) -> str:
        """
        Async wrapper around get_page_source_with_a_delay().
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.get_page_source_with_a_delay(
                url,
                wait_time_in_seconds=wait_time_in_seconds,
                extra_delay=extra_delay
            )
        )

    async def capture_screenshot_async(
        self,
        url: str,
        path: str,
        wait_for_main: bool = False,
        wait_time_in_seconds: int = 20,
        extra_delay: float = 1.0,
    ) -> None:
        """
        Async wrapper around capture_screenshot().
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.capture_screenshot(
                url, path,
                wait_for_main=wait_for_main,
                wait_time_in_seconds=wait_time_in_seconds,
                extra_delay=extra_delay
            )
        )





def main():
    # AUTH = "brd-customer-hl_1cdf8003-zone-scraping_browser1:f05i50grymt3"
    # api = BrowserAPI(AUTH)

  
    
    api = BrowserAPI(
    username="brd-customer-hl_1cdf8003-zone-scraping_browser1",
    password="f05i50grymt3",
    ) 
    
    # BRIGHTDATA_BROWSERAPI_USERNAME=brd-customer-hl_1cdf8003-zone-scraping_browser1
    # BRIGHTDATA_BROWSERAPI_PASSWORD=f05i50grymt3
    
    target_page_address="https://budgety.ai"

    # target_page_address="https://example.com"
    
    # 1) Just grab the raw HTML immediately:
    # html_raw = api.get_page_source(target_page_address)
    # print(html_raw)
    
    
    # 2) Grab the hydrated HTML by waiting for the headline:
    scrape_result = api.get_page_source_with_a_delay(target_page_address)
    
    print("success:" , scrape_result.success)
    
    print("root_domain:" , scrape_result.root_domain)

    print("status:" , scrape_result.status)

    print("cost:" , scrape_result.cost)
    
    print("data:" , scrape_result.data)

    print("error :", scrape_result.error)

    #api.capture_screenshot(target_page_address, "budgety.png", wait_for_main=True, wait_time_in_seconds=30)


if __name__ == "__main__":
    main()