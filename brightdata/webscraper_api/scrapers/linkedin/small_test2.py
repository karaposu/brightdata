# to run python  /Users/ns/Desktop/projects/brightdata/brightdata/scrapers/linkedin/small_test2.py


import time
import requests

# 1) Trigger the job
TRIGGER_URL  = "https://api.brightdata.com/datasets/v3/trigger"
DATASET_ID   = "gd_l1viktl72bvl7bjuj0"
BEARER_TOKEN = "95a56e936a40822fe99780b8af0eab05cab72425bc266b14e3d2d39c5ea592bb"

headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type":  "application/json",
}
params = {
    "dataset_id":     DATASET_ID,
    "include_errors": "true",
}
payload = [{"url": "https://www.linkedin.com/in/enes-kuzucu/"}]

r = requests.post(TRIGGER_URL, headers=headers, params=params, json=payload)
r.raise_for_status()
resp = r.json()
sid = resp.get("snapshot_id")
if not sid:
    raise RuntimeError(f"failed to get snapshot_id: {resp!r}")

print("🔔 snapshot_id =", sid)


# 2) Poll status until ready (or error)
STATUS_URL   = f"https://api.brightdata.com/datasets/v3/progress/{sid}"
SNAPSHOT_URL = f"https://api.brightdata.com/datasets/v3/snapshot/{sid}?format=json"

while True:
    r = requests.get(STATUS_URL, headers=headers)
    r.raise_for_status()
    status = r.json().get("status", "").lower()
    print(f"→ status = {status}")
    if status == "ready":
        break
    if status in ("error", "failed"):
        raise RuntimeError(f"job failed, status={status!r}")
    time.sleep(15)


# 3) Fetch the data
r = requests.get(SNAPSHOT_URL, headers=headers)
r.raise_for_status()
data = r.json()

print("✅ got", len(data or []), "records")
print("data:")
print(data)
# now you can inspect `data`
