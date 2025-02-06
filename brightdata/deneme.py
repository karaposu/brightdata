import requests
import logging
from dataclasses import dataclass
from typing import Any, Optional, List

logger = logging.getLogger(__name__)

@dataclass
class ScrapeResult:
    success: bool
    status: str                 # e.g., 'done', 'in_progress', 'error', 'not_ready'
    error: Optional[str] = None # Detailed error code/string if any (e.g. 'rate_error', 'limit_error', etc.)
    data: Any = None            # The actual data retrieved (if success) or None

class BrightdataBaseSpecializedScraper:
    """
    Base class that handles common logic for interacting with Bright Data's datasets.
    
    Once you provide a dataset_id and bearer_token in 'credentials', it automatically
    constructs the trigger/status/result URLs:
      - trigger_url: 
          https://api.brightdata.com/datasets/v3/trigger?dataset_id=...&include_errors=true&format=json
      - status_base_url: 
          https://api.brightdata.com/datasets/v3/progress
      - result_base_url: 
          https://api.brightdata.com/datasets/v3/snapshot

    Usage (high-level):

      1) Instantiate with credentials:
         scraper = BrightdataBaseSpecializedScraper({"dataset_id": "...", "bearer_token": "..."})
      
      2) (Optional) Check connectivity:
         ok, err = scraper.test_connection()

      3) Trigger a new job (single or multiple URLs):
         bd_snapshot_id = scraper.trigger("https://www.example.com/page")
         # or
         bd_snapshot_id = scraper.trigger_multiple(["https://url1", "https://url2"])

      4) Poll for data:
         result = scraper.get_data(bd_snapshot_id)
         if result.status == "done":
             # use result.data
    """

    def __init__(self, credentials, test_link=None, **kwargs):
        """
        credentials: dict, e.g.:
          {
            "dataset_id": "gd_lj74waf72416ro0k65",
            "bearer_token": "ed81ba0163c55c2f60ea69545..."
          }
        test_link: optional link to test connectivity (HEAD or GET)
        kwargs: any other config
        """
        # Required fields
        self.dataset_id = credentials["dataset_id"]
        self.bearer_token = credentials["bearer_token"]

        # Build Bright Data endpoints
        self.trigger_url = (
            f"https://api.brightdata.com/datasets/v3/trigger"
            f"?dataset_id={self.dataset_id}&include_errors=true&format=json"
        )
        self.status_base_url = "https://api.brightdata.com/datasets/v3/progress"
        self.result_base_url = "https://api.brightdata.com/datasets/v3/snapshot"

        self.test_link = test_link  # optional
        self.config = kwargs

        logger.debug("Initialized BrightdataBaseSpecializedScraper")

    def test_connection(self):
        """
        Makes a HEAD (or GET) request to either self.test_link or self.trigger_url.
        Returns a tuple: (boolean success, string error_message or None).

        Usage:
            ok, err = self.test_connection()
            if not ok:
                print("Connection test failed:", err)
            else:
                print("Connection OK!")
        """
        logger.debug(f"test_connection called with test_link: {self.test_link}")
        url = self.test_link or self.trigger_url
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        try:
            resp = requests.head(url, headers=headers, timeout=5)
            resp.raise_for_status()
            return (True, None)
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code} {e.response.reason}"
            return (False, error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request Error: {str(e)}"
            return (False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            return (False, error_msg)

    def trigger(self, target: str) -> Optional[str]:
        """
        Triggers a scraping job on Bright Data for a single `target` (a single URL).
        Returns the Bright Data snapshot ID if successful, or None on error.
        """
        # Single-item list with one dict: e.g. [{"url": "..."}]
        payload = [{"url": target}]
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(self.trigger_url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"Trigger response JSON: {data}")
        except Exception as e:
            logger.debug(f"self.trigger_url: {self.trigger_url}")
            logger.debug(f"Exception encountered during trigger: {str(e)}")
            return None

        # Suppose the response has "snapshot_id"
        brightdata_snapshot_id = data.get("snapshot_id")
        if not brightdata_snapshot_id:
            logger.debug("No snapshot_id found in Bright Data response")
            return None

        return brightdata_snapshot_id

    def trigger_multiple(self, targets: List[str]) -> Optional[str]:
        """
        Similar to trigger(), but takes a list of URLs. Bright Data expects
        an array of {"url": ...} objects in one request, returning ONE snapshot ID
        for the entire batch job.

        Example:
          urls = ["https://www.example.com/page1", "https://www.example.com/page2"]
          snapshot_id = scraper.trigger_multiple(urls)
        """
        # Build a list of dicts: [{"url": t} for t in targets]
        payload = [{"url": t} for t in targets]
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }

        try:
            resp = requests.post(self.trigger_url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"Trigger (multiple) response JSON: {data}")
        except Exception as e:
            logger.debug(f"self.trigger_url: {self.trigger_url}")
            logger.debug(f"Exception encountered during trigger_multiple: {str(e)}")
            return None

        brightdata_snapshot_id = data.get("snapshot_id")
        if not brightdata_snapshot_id:
            logger.debug("No snapshot_id found in Bright Data response for trigger_multiple")
            return None

        return brightdata_snapshot_id

    def get_data(self, bd_snapshot_id: str) -> ScrapeResult:
        """
        Checks the status of the job associated with 'bd_snapshot_id' on Bright Data.
        If it's done, fetches the final result.
        
        Returns a ScrapeResult object:
          - success: bool
          - status: 'done' | 'not_ready' | 'error' | ...
          - error: 'rate_error'|'limit_error'|'fetch_error'|None
          - data: The final JSON or None
        """
        check_url = f"{self.status_base_url}/{bd_snapshot_id}"  # e.g. /progress/{snapshot_id}
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        try:
            resp = requests.get(check_url, headers=headers, timeout=10)
            resp.raise_for_status()
            status_data = resp.json()
            logger.debug(f"Status data: {status_data}")
        except requests.exceptions.HTTPError as e:
            error_result = self._map_http_error(e)
            logger.debug(f"HTTP Error while checking status: {e}")
            return error_result
        except requests.exceptions.RequestException as e:
            logger.debug(f"Request Error while checking status: {str(e)}")
            return ScrapeResult(success=False, status="error", error="fetch_error", data=None)
        except Exception as e:
            logger.debug(f"Unexpected error while checking status: {str(e)}")
            return ScrapeResult(success=False, status="error", error="fetch_error", data=None)

        current_status = status_data.get("status", "unknown").lower()

        if current_status == "done":
            # If done, fetch final result
            return self._fetch_result(bd_snapshot_id)
        elif current_status in ["error", "failed"]:
            return ScrapeResult(success=False, status="error", error="fetch_error", data=None)
        else:
            # still in progress
            return ScrapeResult(success=True, status="not_ready", data=None)

    def _fetch_result(self, bd_snapshot_id: str) -> ScrapeResult:
        """
        Fetches the final JSON from the Bright Data result endpoint:
          GET /snapshot/{bd_snapshot_id}?format=json
        Returns a ScrapeResult with the final data or an appropriate error.
        """
        result_url = f"{self.result_base_url}/{bd_snapshot_id}?format=json"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        try:
            resp = requests.get(result_url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return ScrapeResult(success=True, status="done", data=data)
        except requests.exceptions.HTTPError as e:
            error_result = self._map_http_error(e)
            logger.debug(f"HTTP Error while fetching result: {e}")
            return error_result
        except requests.exceptions.RequestException as e:
            logger.debug(f"Request Error while fetching result: {str(e)}")
            return ScrapeResult(success=False, status="error", error="fetch_error", data=None)
        except Exception as e:
            logger.debug(f"Unexpected error while fetching result: {str(e)}")
            return ScrapeResult(success=False, status="error", error="fetch_error", data=None)

    def _map_http_error(self, e: requests.exceptions.HTTPError) -> ScrapeResult:
        """
        Helper to map HTTPError status codes to specific error labels
        (e.g., rate_error, limit_error, fetch_error).
        """
        status_code = e.response.status_code if e.response else None
        if status_code == 429:
            return ScrapeResult(success=False, status="error", error="rate_error", data=None)
        elif status_code in [402, 403]:
            return ScrapeResult(success=False, status="error", error="limit_error", data=None)
        else:
            return ScrapeResult(success=False, status="error", erro
