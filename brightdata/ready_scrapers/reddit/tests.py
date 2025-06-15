#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/reddit/tests.py
#
# Smoke-test for brightdata.ready_scrapers.reddit.RedditScraper
#   ▸ Triggers each endpoint           (sync path)
#   ▸ Blocks with scraper.poll_until_ready()
#
# Run with:
#   python -m brightdata.ready_scrapers.reddit.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from brightdata.ready_scrapers.reddit import RedditScraper
from brightdata.models import ScrapeResult
from brightdata.utils import show_scrape_results


# ────────────────────────── helpers ──────────────────────────
def _show(label: str, res_or_dict):
    """Pretty print ScrapeResult or {bucket: ScrapeResult}."""
    if isinstance(res_or_dict, ScrapeResult):
        _print_one(label, res_or_dict)
    else:                      # multi-bucket dict
        for bucket, sub in res_or_dict.items():
            _print_one(f"{label}/{bucket}", sub)


def _print_one(label: str, res: ScrapeResult):
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    status = "✓" if res.success and res.status == "ready" else "✗"
    rows   = len(res.data) if isinstance(res.data, list) else "n/a"
    err    = f" err={res.error}" if res.error else ""
    print(f"{ts}  {label:30s} {status}  rows={rows}{err}")


# ─────────────────────────── main ────────────────────────────
def main():
    load_dotenv()
    if not os.getenv("BRIGHTDATA_TOKEN"):
        sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

    scraper = RedditScraper()                 # token from .env
    
    # 1. posts__collect_by_url ------------------------------------------------
    post_urls = [
        "https://www.reddit.com/r/battlefield2042/comments/1cmqs1d/official_update_on_the_next_battlefield_game/",
        "https://www.reddit.com/r/singularity/comments/1cmoa52/former_google_ceo_on_ai_its_underhyped/",
        "https://www.reddit.com/r/datascience/comments/1cmnf0m/technical_interview_python_sql_problem_but_not/",
    ]
    sid = scraper.posts__collect_by_url(post_urls)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("posts__collect_by_url", res)

    # 2. posts__discover_by_keyword ------------------------------------------
    keyword_queries = [
        {"keyword": "datascience",    "date": "All time",   "sort_by": "Hot"},
        {"keyword": "battlefield2042","date": "Past year",  "num_of_posts": 10,"sort_by": "Top"},
        {"keyword": "cats",           "date": "Past month", "num_of_posts": 50,"sort_by": "New"},
    ]
    sid = scraper.posts__discover_by_keyword(keyword_queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("posts__discover_by_keyword", res)
    
    # 3. posts__discover_by_subreddit_url ------------------------------------
    subreddit_queries = [
        {"url": "https://www.reddit.com/r/battlefield2042",
         "sort_by": "Hot", "sort_by_time": "Today"},
        {"url": "https://www.reddit.com/r/singularity/",
         "sort_by": "New", "sort_by_time": ""},
        {"url": "https://www.reddit.com/r/datascience/",
         "sort_by": "Rising", "sort_by_time": "All Time"},
    ]
    sid = scraper.posts__discover_by_subreddit_url(subreddit_queries)
    res = scraper.poll_until_ready(sid)
    show_scrape_results("posts__discover_by_subreddit_url", res)

    # 4. comments__collect_by_url -------------------------------------------
    comment_queries = [
        {
            "url": "https://www.reddit.com/r/datascience/comments/1cmnf0m/comment/l32204i/",
            "days_back": 10,
            "load_all_replies": False,
            "comment_limit": 10,
        },
        {
            "url": "https://www.reddit.com/r/singularity/comments/1cmoa52/comment/l31pwza/",
            "days_back": 30,
            "load_all_replies": True,
            "comment_limit": 5,
        },
        {
            "url": "https://www.reddit.com/r/battlefield2042/comments/1cmqs1d/comment/l32778k/",
            "days_back": 183,
            "load_all_replies": False,
            "comment_limit": "",
        },
    ]
    sid_map = scraper.comments__collect_by_url(comment_queries)  # multi-bucket
    # comments__collect_by_url always hits one dataset → sid_map is str
    res = scraper.poll_until_ready(sid_map)
    show_scrape_results("comments__collect_by_url", res)


if __name__ == "__main__":
    main()
