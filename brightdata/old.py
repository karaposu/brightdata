import requests
import time
from uuid import uuid4
import logging
logger = logging.getLogger(__name__)


from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class ScrapeResult:
    success: bool   
    status: str          # e.g., 'done', 'in_progress', 'error'
    
    error: Optional[str] # Error message if any, else None
    data: Any            # The actual data retrieved or None

class BrightdataBaseSpecializedScraper:
    """
    Base class that handles common logic for interacting with Bright Data's datasets.
    
    Once you provide a dataset_id and bearer_token in 'credentials', it automatically
    constructs the trigger/status/result URLs:
      - trigger_url = "https://api.brightdata.com/datasets/v3/trigger?dataset_id=...&include_errors=true&format=json"
      - status_base_url = "https://api.brightdata.com/datasets/v3/progress"
      - result_base_url = "https://api.brightdata.com/datasets/v3/snapshot"

    The class keeps an in-memory store of jobs in 'self.jobs' for demonstration.
    In production, you'd likely store these snapshot/job states in a DB or other store.
    """

    def __init__(self, credentials, test_link=None, **kwargs):
        """
        credentials: dict, e.g.:
          {
            "dataset_id": "gd_lj74waf72416ro0k65",
            "bearer_token": "ed81ba0163c55c2f60ea69545...",
          }
        test_link: optional link to test connectivity (HEAD or GET)
        kwargs: any other config
        """
        # Required fields
        self.dataset_id = credentials["dataset_id"]
        self.bearer_token = credentials["bearer_token"]

        # Automatically build full Bright Data endpoints
        # For an example: 
        #   trigger: https://api.brightdata.com/datasets/v3/trigger?dataset_id=xxx&include_errors=true&format=json
        self.trigger_url = (
            f"https://api.brightdata.com/datasets/v3/trigger"
            f"?dataset_id={self.dataset_id}&include_errors=true&format=json"
        )
        self.status_base_url = "https://api.brightdata.com/datasets/v3/progress"  # we append /{snapshot_id}
        self.result_base_url = "https://api.brightdata.com/datasets/v3/snapshot"  # we append /{snapshot_id}?format=json

        self.test_link = test_link  # optional
        self.config = kwargs

        # Simple in-memory tracking: snapshot_id -> job info
        self.jobs = {}

        logger.debug("Initialized")

    def test_connection(self):
        """
        Makes a HEAD (or GET) request to either self.test_link or self.trigger_url.
        Returns a tuple: (boolean success, string error_message or None).

        Example usage:
            ok, error = self.test_connection()
            if not ok:
                print("Connection test failed:", error)
            else:
                print("Connection OK!")
        """
        logger.debug(f"test_connection called with test.link: {self.test_link}")
    
        url = self.test_link or self.trigger_url
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        try:
            resp = requests.head(url, headers=headers, timeout=5)
            resp.raise_for_status()
            return (True, None)  # success, no error message
        except requests.exceptions.HTTPError as e:
            # e.response.status_code or e.response.text might help you glean more info
            error_msg = f"HTTP Error: {e.response.status_code} {e.response.reason}"
            return (False, error_msg)
        except requests.exceptions.RequestException as e:
            # Catches all other requests-related errors (ConnectionError, Timeout, etc.)
            error_msg = f"Request Error: {str(e)}"
            return (False, error_msg)
        except Exception as e:
            # Fallback for anything unexpected
            error_msg = f"Unexpected error: {str(e)}"
            return (False, error_msg)
    
    def trigger(self, target: str) -> str:
        """
        Triggers a scraping job on Bright Data for the given `target` (e.g. a URL).
        Returns a brightdata_snapshot_id and local_unique_scrape_task_id.
        
        1. POST to self.trigger_url with the request data (like {"url": target}).
        2. The response should include a 'local_unique_scrape_task_id' or something indicating the job reference.
        3. Store job state in self.jobs[local_unique_scrape_task_id].
        """
        local_unique_scrape_task_id = str(uuid4())  # local unique ID to track this job; can also rely on Bright Data's snapshot ID
        # lusti

        # We'll pass 'target' in the JSON body. 
        # Depending on your dataset config, you might call it "url", "input", or something else.
        payload = {"url": target}

        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        try:
            resp = requests.post(self.trigger_url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"data {data}")
        except Exception as e:
            # Mark job as error
            self.jobs[local_unique_scrape_task_id] = {"status": "error", "data": str(e)}
            logger.debug(f"Exception encountered. ")
            return local_unique_scrape_task_id, False

        # The Bright Data response typically returns a "snapshot_id" or "id".
        # We'll assume "id" is the actual snapshot ID from Bright Data.
        # Adjust based on how your actual response looks.

        brightdata_snapshot_id = data.get("snapshot_id") 

        # In many cases, the job might already be queued or in progress. 
        # We'll store that info here.
        self.jobs[local_unique_scrape_task_id] = {
            "bd_snapshot_id": brightdata_snapshot_id,  # The "real" BD snapshot ID
            "status": "in_progress",
            "data": None
        }

        return brightdata_snapshot_id, local_unique_scrape_task_id

    def get_data(self, bd_snapshot_id: str):
       
        # if snapshot_id not in self.jobs:
        #     return "invalid_snapshot_id"

        # job_record = self.jobs[snapshot_id]

        # # If we've already flagged it as error or done, just return that
        # if job_record["status"] == "error":
        #     return f"Job encountered an error: {job_record['data']}"
        # elif job_record["status"] == "done":
        #     return job_record["data"]

        # It's presumably "in_progress", so let's check the Bright Data status
       # bd_snapshot_id = job_record["bd_snapshot_id"]
        check_url = f"{self.status_base_url}/{bd_snapshot_id}"  # e.g.: /datasets/v3/progress/{snapshot_id}
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        try:
            resp = requests.get(check_url, headers=headers, timeout=10)
            resp.raise_for_status()
            status_data = resp.json()
            logger.debug(f"status: {status_data} ")
        except Exception as e:
            logger.debug(f"error: {e} ")
            # return False
            sc= ScrapeResult(success=False,
                             error=e)
            return sc

        # Suppose the status_data might contain: {"status": "done"} or "in_progress", etc.
        current_status = status_data.get("status", "unknown").lower()

        if current_status == "done":
            # If done, fetch final result
            final_data = self._fetch_result(bd_snapshot_id)

            if final_data=="fetching_error":
                sc= ScrapeResult(success=False,
                                status=current_status, 
                                error="fetching_error"
                               )
            else:
            
                sc= ScrapeResult(success=True,
                                status=current_status, 
                                data=final_data)
  
            return sc
        
        elif current_status in ["error", "failed"]:
            sc= ScrapeResult(success=False,
                             status=current_status, 
                             error="error_detail"
                             )
         
            return sc
        else:
            # still in progress
            sc= ScrapeResult(success=True,
                             status="not_ready", 
                        
                            )
         
            return sc
            

    def _fetch_result(self, bd_snapshot_id):
        """
        Fetches the final JSON from the Bright Data result endpoint:
          GET {self.result_base_url}/{bd_snapshot_id}?format=json
        Returns parsed JSON data on success or raises exception on error.
        """
        result_url = f"{self.result_base_url}/{bd_snapshot_id}?format=json"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        try:
            resp = requests.get(result_url, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return "fetching_error"
           