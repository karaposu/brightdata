import requests
import logging
from dataclasses import dataclass
from typing import Any, Optional
from dotenv import load_dotenv
import os
from typing import List
import json
import aiohttp

from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

@dataclass
class ScrapeResult:
    success: bool
    status: str                 # e.g., 'ready', 'in_progress', 'error', 'not_ready'
    error: Optional[str] = None # Detailed error code/string if any (e.g. 'rate_error', 'limit_error', etc.)
    data: Any = None            # The actual data retrieved (if success) or None

class BrightdataBaseSpecializedScraper:
    """
    Base class that handles common logic for interacting with Bright Data's scraper datasets.
    
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

      3) Trigger a new job:
         bd_snapshot_id = scraper.trigger("https://www.example.com/page")
         if bd_snapshot_id is None:
             # handle error

      4) Poll for data:
         result = scraper.get_data(bd_snapshot_id)
         if result.status == "ready":
             # use result.data
    """

    def __init__(self, dataset_id, bearer_token, test_link=None, **kwargs):
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
        self.dataset_id = dataset_id
        if bearer_token is None:
            
            load_dotenv()
            BRIGHTDATA_BEARER = os.getenv("BRIGHTDATA_TOKEN")
            if not BRIGHTDATA_BEARER:
                pass
                #throw breaking error here
            else:
                self.bearer_token = BRIGHTDATA_BEARER
               

        else:
            self.bearer_token = bearer_token

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
    
    # ──────────────────────────────────────────────────────────────
    # OLD convenience helper → rename for clarity
    # Works only for single-URL “collect by url” datasets that accept:
    #     payload = [{"url": "<page>"}]
    # and need **no** extra query-parameters.
    # ──────────────────────────────────────────────────────────────
    def trigger_url(self, target: str, *, timeout: int = 10) -> Optional[str]:
        """
        Convenience call for the simplest Bright-Data datasets
        (collect-by-URL, no extra query params).

        Returns the snapshot-id string on success, or None on any failure.
        """

        payload = [{"url": target}]
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type":  "application/json",
        }

        try:
            resp = requests.post(
                self.trigger_url,      # already contains ?dataset_id=…&include_errors=true
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            snapshot = data.get("snapshot_id")
            if not snapshot:
                logger.debug("Bright Data response for %s had no snapshot_id: %s",
                            target, data)
            return snapshot

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "N/A"
            logger.debug("HTTP Error %s while triggering %s: %s", status, target, e)
            return None

        except requests.exceptions.RequestException as e:
            logger.debug("Request error while triggering %s: %s", target, e)
            return None

        except json.JSONDecodeError as e:
            logger.debug("JSON decode error from Bright Data response for %s: %s",
                        target, e)
            return None

        except Exception as e:
            logger.debug("Unexpected error while triggering %s: %s", target, e)
            return None



   
    def _trigger(
        self,
        payload: List[Dict[str, Any]],
        *,
        dataset_id: str,
        include_errors: bool = True,
        extra_params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        force_async: bool = True,  
    ) -> Optional[Any]:
        """
        Generic POST to Bright Data’s /trigger endpoint.

        Parameters
        ----------
        payload        : list[dict] – whatever that dataset expects
        dataset_id     : str        – Bright Data dataset to hit
        include_errors : bool       – keep Bright Data error objects
        extra_params   : dict       – merged into query string
        timeout        : int        – seconds

        Returns
        -------
        • Parsed JSON on 2xx success (list of records *or* snapshot-ID dict)  
        • None on any error (HTTP, request, JSON parsing, etc.) — details are
          logged at DEBUG level.
        """

        

        params: Dict[str, Any] = {
            "dataset_id": dataset_id,
            "include_errors": str(include_errors).lower(),
             "format":        "json",           # ← missing piece
        }


        # unify behaviour: force async unless caller opts out
        if force_async and (not extra_params or "sync_mode" not in extra_params):
            params["sync_mode"] = "async"

        if extra_params:
            params.update(extra_params)

        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type":  "application/json",
        }


        print("inside the super _trigger:  ")

        print("headers:  ", headers)
        print("params:  ", params)
        print("json:  ", payload)
        
        try:
            resp = requests.post(
                "https://api.brightdata.com/datasets/v3/trigger",
                headers=headers,
                params=params,
                json=payload,
                timeout=timeout,
            )

            print("resp:  ", resp)
            resp.raise_for_status()
            data= resp.json()

            # ▸ if it’s an async job, return just the snapshot-id string
            if isinstance(data, dict) and "snapshot_id" in data:
                return data["snapshot_id"]
            return data

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else "N/A"
            logger.debug("HTTP %s while triggering dataset %s: %s",
                         code, dataset_id, e)
            return None

        except requests.exceptions.RequestException as e:
            logger.debug("Request error while triggering dataset %s: %s",
                         dataset_id, e)
            return None

        except json.JSONDecodeError as e:
            logger.debug("JSON decode error from Bright Data response "
                         "(dataset %s): %s", dataset_id, e)
            return None

        except Exception as e:
            logger.debug("Unexpected error while triggering dataset %s: %s",
                         dataset_id, e)
            return None
        










    async def _fetch_result_async(self, snapshot_id: str,
                              session: aiohttp.ClientSession) -> ScrapeResult:
        """non-blocking version of _fetch_result()"""
        url = f"{self.result_base_url}/{snapshot_id}?format=json"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        try:
            async with session.get(url, headers=headers, timeout=30) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return ScrapeResult(True, "ready", data=data)

        except aiohttp.ClientResponseError as e:
            return ScrapeResult(False, "error", error=f"http_{e.status}")
        except Exception as e:
            return ScrapeResult(False, "error", error=str(e))


    async def get_data_async(self, snapshot_id: str,
                            session: aiohttp.ClientSession) -> ScrapeResult:
        """
        Async twin of get_data(); *never* blocks the event loop.
        """
        url = f"{self.status_base_url}/{snapshot_id}"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        try:
            async with session.get(url, headers=headers, timeout=20) as resp:
                resp.raise_for_status()
                state = await resp.json()

        except aiohttp.ClientResponseError as e:
            return ScrapeResult(False, "error", error=f"http_{e.status}")
        except Exception as e:
            return ScrapeResult(False, "error", error=str(e))

        status = state.get("status", "unknown").lower()
        if status == "ready":
            return await self._fetch_result_async(snapshot_id, session)
        if status in {"error", "failed"}:
            return ScrapeResult(False, "error", error="job_failed")
        return ScrapeResult(True, status)          # not_ready / in_progress    
    


    

    
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
        If it's ready, fetches the final result.
        
        Returns a ScrapeResult object:
          - success: bool
          - status: 'ready' | 'not_ready' | 'error' | ...
          - error: 'rate_error'|'limit_error'|'fetch_error'|None
          - data: The final JSON or None
        """
        check_url = f"{self.status_base_url}/{bd_snapshot_id}"  # /progress/{snapshot_id}
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        
        try:
            resp = requests.get(check_url, headers=headers, timeout=10)
            resp.raise_for_status()
            status_data = resp.json()
            logger.debug(f"Status data: {status_data}")
        except requests.exceptions.HTTPError as e:
            # Distinguish specific error codes
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
        
        if current_status == "ready":
            # If ready, fetch final result
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
            return ScrapeResult(success=True, status="ready", data=data)
        except requests.exceptions.HTTPError as e:
            # Distinguish error codes
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
            # rate limit
            return ScrapeResult(success=False, status="error", error="rate_error", data=None)
        elif status_code in [402, 403]:
            # assume 402 or 403 might be a credit limit or permission error
            return ScrapeResult(success=False, status="error", error="limit_error", data=None)
        else:
            # fallback
            return ScrapeResult(success=False, status="error", error="fetch_error", data=None)
