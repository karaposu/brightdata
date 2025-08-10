# brightdata_web_unlocker.py

# to run   python -m brightdata.brightdata_web_unlocker
import os
import requests
from dotenv import load_dotenv
import pathlib
import tldextract

import asyncio
import aiohttp
import logging

from brightdata.models import ScrapeResult

class BrightdataWebUnlocker:

    COST_PER_THOUSAND = 1.50  # USD per 1000 requests
    COST_PER_REQUEST = COST_PER_THOUSAND / 1000.0

    def __init__(self, BRIGHTDATA_WEBUNLOCKER_BEARER=None, ZONE_STRING=None):
        load_dotenv()
        self.bearer = BRIGHTDATA_WEBUNLOCKER_BEARER or os.getenv('BRIGHTDATA_WEBUNLOCKER_BEARER')
        self.zone   = ZONE_STRING                    or os.getenv('BRIGHTDATA_WEBUNLOCKER_APP_ZONE_STRING')
        self.format = "raw"
        if not (self.bearer and self.zone):
            raise ValueError("Set BRIGHTDATA_WEBUNLOCKER_BEARER and ZONE_STRING")
        
        self._endpoint = "https://api.brightdata.com/request"

    def _make_result(
        self,
        *,
        url: str,
        success: bool,
        status: str,
        data: str | None = None,
        error: str | None = None
    ) -> ScrapeResult:
        from datetime import datetime
        ext = tldextract.extract(url)
        return ScrapeResult(
            success=success,
            url=url,
            status=status,
            data=data,
            error=error,
            snapshot_id=None,
            cost=self.COST_PER_REQUEST if success else 0.0,
            fallback_used=True,  # Web Unlocker is used as a fallback
            root_domain=ext.domain or None,
            request_sent_at=datetime.utcnow() if success else None,
            data_received_at=datetime.utcnow() if success else None,
            html_char_size=len(data) if data else None
        )

    def get_source(self, target_weblink: str) -> ScrapeResult:
        """
        Returns ScrapeResult with .data holding the unlocked HTML.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.bearer}"
        }
        payload = {"zone": self.zone, "url": target_weblink, "format": self.format}

        try:
            resp = requests.post(self._endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            return self._make_result(
                url=target_weblink,
                success=True,
                status="ready",
                data=resp.text
            )
        
        except requests.HTTPError as e:
            return self._make_result(
                url=target_weblink,
                success=False,
                status="error",
                error=f"HTTP {e.response.status_code}"
            )
        except Exception as e:
            return self._make_result(
                url=target_weblink,
                success=False,
                status="error",
                error=str(e)
            )

    def get_source_safe(self, target_weblink: str) -> ScrapeResult:
        """
        Wraps get_source and never raises: always returns ScrapeResult.
        """
        res = self.get_source(target_weblink)
        if not res.success:
            res.status = "error"
        return res

    def download_source(self, site: str, filename: str) -> ScrapeResult:
        """
        Fetches and writes HTML to disk. Returns ScrapeResult.
        """
        res = self.get_source(site)
        if not res.success:
            return res

        path = pathlib.Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(res.data or "", encoding="utf-8")
            return self._make_result(
                url=site,
                success=True,
                status="ready",
                data=f"Saved to {filename}"
            )
        except Exception as e:
            return self._make_result(
                url=site,
                success=False,
                status="error",
                error=str(e)
            )

    def download_source_safe(self, site: str, filename: str) -> ScrapeResult:
        """
        Safe download: uses get_source_safe, then writes file if possible.
        """
        res = self.get_source_safe(site)
        if not res.success:
            return res
        return self.download_source(site, filename)
    



    async def get_source_async(self, target_weblink: str) -> ScrapeResult:
        """
        Async unlock + HTML fetch via aiohttp.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.bearer}"
        }
        payload = {"zone": self.zone, "url": target_weblink, "format": "raw"}

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as sess:
                async with sess.post(self._endpoint, headers=headers, json=payload) as resp:
                    text = await resp.text()
                    if resp.status >= 400:
                        raise aiohttp.ClientResponseError(
                            request_info=resp.request_info,
                            history=resp.history,
                            status=resp.status,
                            message=text,
                            headers=resp.headers,
                        )
            return self._make_result(
                url=target_weblink,
                success=True,
                status="ready",
                data=text
            )
        except aiohttp.ClientResponseError as e:
            return self._make_result(
                url=target_weblink,
                success=False,
                status="error",
                error=f"HTTP {e.status}"
            )
        except Exception as e:
            return self._make_result(
                url=target_weblink,
                success=False,
                status="error",
                error=str(e)
            )
        
    async def get_source_safe_async(self, target_weblink: str) -> ScrapeResult:
        """Async-safe: never raises."""
        res = await self.get_source_async(target_weblink)
        if not res.success:
            res.status = "error"
        return res

    def test_unlocker(self) -> ScrapeResult:
        """
        Tests retrieving example.com. Returns ScrapeResult.
        """
        test_url = "https://example.com"
        res = self.get_source_safe(test_url)
        if res.success and res.data and res.data.strip():
            return self._make_result(
                url=test_url,
                success=True,
                status="ready",
                data="Test succeeded"
            )
        return self._make_result(
            url=test_url,
            success=False,
            status="error",
            error="empty_or_failed"
        )
    

if __name__ == "__main__":

   
    logging.basicConfig(level=logging.DEBUG)
    async def main():
        unlocker = BrightdataWebUnlocker()
        url = "https://example.com"
        print(f"\n→ fetching {url!r} via web-unlocker…")
        res = await unlocker.get_source_async(url)
        print(f" success       : {res.success}")
        print(f" status        : {res.status}")
        print(f" root domain   : {res.root_domain}")
        print(f" html length   : {len(res.data or '')} chars")
        print(f" cost          : {res.cost:.6f}$")
    asyncio.run(main())
