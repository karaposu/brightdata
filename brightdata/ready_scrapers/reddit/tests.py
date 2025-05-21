#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# brightdata/ready_scrapers/reddit/tests.py
#
# Smoke-test for brightdata.ready_scrapers.reddit.RedditScraper
#   ▸ all methods run in async mode → return snapshot-ids
#   ▸ use poll_until_ready_and_show to block until results arrive
#
# Run with:
#   python -m brightdata.ready_scrapers.reddit.tests
# ─────────────────────────────────────────────────────────────
import os
import sys
from dotenv import load_dotenv

from brightdata.ready_scrapers.reddit import RedditScraper
from brightdata.utils import poll_until_ready_and_show

def main():
    # ─────────────────────────────────────────────────────────
    # 0.  credentials
    # ─────────────────────────────────────────────────────────
    load_dotenv()
    token = os.getenv("BRIGHTDATA_TOKEN")
    if not token:
        sys.exit("Set BRIGHTDATA_TOKEN environment variable first")

    # ─────────────────────────────────────────────────────────
    # 1.  instantiate scraper
    # ─────────────────────────────────────────────────────────
    scraper = RedditScraper()   # reads token from env

    # ─────────────────────────────────────────────────────────
    # 2.  posts__collect_by_url
    # ─────────────────────────────────────────────────────────
    post_urls = [
        "https://www.reddit.com/r/battlefield2042/comments/1cmqs1d/official_update_on_the_next_battlefield_game/",
        "https://www.reddit.com/r/singularity/comments/1cmoa52/former_google_ceo_on_ai_its_underhyped/",
        "https://www.reddit.com/r/datascience/comments/1cmnf0m/technical_interview_python_sql_problem_but_not/",
    ]
    snap = scraper.posts__collect_by_url(post_urls)
    poll_until_ready_and_show(scraper, "posts__collect_by_url", snap)

    # ─────────────────────────────────────────────────────────
    # 3.  posts__discover_by_keyword
    # ─────────────────────────────────────────────────────────
    keyword_queries = [
        {"keyword": "datascience",    "date": "All time",   "sort_by": "Hot"},
        {"keyword": "battlefield2042", "date": "Past year",  "num_of_posts": 10, "sort_by": "Top"},
        {"keyword": "cats",            "date": "Past month","num_of_posts": 50, "sort_by": "New"},
    ]
    snap = scraper.posts__discover_by_keyword(keyword_queries)
    poll_until_ready_and_show(scraper, "posts__discover_by_keyword", snap)

    # ─────────────────────────────────────────────────────────
    # 4.  posts__discover_by_subreddit_url
    # ─────────────────────────────────────────────────────────
    subreddit_queries = [
        {"url": "https://www.reddit.com/r/battlefield2042", "sort_by": "Hot",   "sort_by_time": "Today"},
        {"url": "https://www.reddit.com/r/singularity/",     "sort_by": "New",   "sort_by_time": ""},
        {"url": "https://www.reddit.com/r/datascience/",      "sort_by": "Rising","sort_by_time": "All Time"},
    ]
    snap = scraper.posts__discover_by_subreddit_url(subreddit_queries)
    poll_until_ready_and_show(scraper, "posts__discover_by_subreddit_url", snap)

    # ─────────────────────────────────────────────────────────
    # 5.  comments__collect_by_url
    # ─────────────────────────────────────────────────────────
    comment_queries = [
        {
          "url":           "https://www.reddit.com/r/datascience/comments/1cmnf0m/comment/l32204i/",
          "days_back":     10,
          "load_all_replies": False,
          "comment_limit": 10
        },
        {
          "url":           "https://www.reddit.com/r/singularity/comments/1cmoa52/comment/l31pwza/",
          "days_back":     30,
          "load_all_replies": True,
          "comment_limit": 5
        },
        {
          "url":           "https://www.reddit.com/r/battlefield2042/comments/1cmqs1d/comment/l32778k/",
          "days_back":     183,
          "load_all_replies": False,
          "comment_limit": ""
        },
    ]
    snap = scraper.comments__collect_by_url(comment_queries)
    poll_until_ready_and_show(scraper, "comments__collect_by_url", snap)

if __name__ == "__main__":
    main()
