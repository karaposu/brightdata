import os
import requests
from dotenv import load_dotenv
import pathlib
import tldextract

from brightdata.models import ScrapeResult

class BrightdataWebUnlocker:
    def __init__(self, BRIGHTDATA_WEBUNCLOKCER_BEARER=None, ZONE_STRING=None):
        load_dotenv()
        self.bearer = BRIGHTDATA_WEBUNCLOKCER_BEARER or os.getenv('BRIGHTDATA_WEBUNCLOKCER_BEARER')
        self.zone   = ZONE_STRING                    or os.getenv('BRIGHTDATA_WEBUNCLOKCER_APP_ZONE_STRING')
        self.format = "raw"
        if not (self.bearer and self.zone):
            raise ValueError("Set BRIGHTDATA_WEBUNCLOKCER_BEARER and ZONE_STRING")

    def _make_result(
        self,
        *,
        url: str,
        success: bool,
        status: str,
        data: str | None = None,
        error: str | None = None
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
            fallback_used=False,
            root_domain=ext.domain or None
        )

    def get_source(self, target_weblink: str) -> ScrapeResult:
        """
        Returns ScrapeResult with .data holding the unlocked HTML.
        """
        url = "https://api.brightdata.com/request"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.bearer}"
        }
        payload = {"zone": self.zone, "url": target_weblink, "format": self.format}

        try:
            resp = requests.post(url, headers=headers, json=payload)
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
