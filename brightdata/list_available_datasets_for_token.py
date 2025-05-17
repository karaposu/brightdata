#!/usr/bin/env python3
"""
List all Bright Data datasets visible to the given bearer-token.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Tuple

load_dotenv()
API_TOKEN = os.getenv("BRIGHTDATA_TOKEN")  

if not API_TOKEN:
    print("Set BRIGHTDATA_TOKEN first"); sys.exit(1)


def _fetch_datasets_raw(token: str, *, timeout: int = 15) -> Optional[Any]:
    url = "https://api.brightdata.com/datasets/list"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.json()                       # could be list or {"datasets": [...]}

    except requests.exceptions.HTTPError as e:
        print("HTTP", e.response.status_code, e.response.reason)
    except requests.exceptions.RequestException as e:
        print("Network error:", e)
    except json.JSONDecodeError:
        print("Response was not JSON:", r.text)

    return None


# ──────────────────────────────────────────────────────────────
# high-level: always return a clean list[dict] (empty list on failure)
# ──────────────────────────────────────────────────────────────
def list_datasets(token: str) -> List[Dict[str, Any]]:
    """Return a normalised list of dataset objects visible to `token`."""
    raw = _fetch_datasets_raw(token)
    if raw is None:
        return []

    if isinstance(raw, list):                          # already a list
        return raw
    if isinstance(raw, dict) and "datasets" in raw:    # wrapped structure
        return raw["datasets"]

    print("Unexpected response format:", json.dumps(raw, indent=2))
    return []



# def list_datasets(token: str):
#     """Return a python list of dataset objects."""
#     url = "https://api.brightdata.com/datasets/list"
#     headers = {"Authorization": f"Bearer {token}"}

#     try:
#         r = requests.get(url, headers=headers, timeout=15)
#         r.raise_for_status()
#         data = r.json()                 # ← may be *list* or {"datasets": [...]}

#         # Normalise to list
#         if isinstance(data, list):
#             return data
#         if isinstance(data, dict) and "datasets" in data:
#             return data["datasets"]

#         print("Unexpected response format:", json.dumps(data, indent=2))
#         return []

#     except requests.exceptions.HTTPError as e:
#         print("HTTP", e.response.status_code, e.response.reason)
#     except requests.exceptions.RequestException as e:
#         print("Network error:", e)
#     except json.JSONDecodeError:
#         print("Response was not JSON:", r.text)

#     return []

if __name__ == "__main__":
    for ds in list_datasets(API_TOKEN):
        print(f"{ds['id']:>22}  {ds['name']}")
