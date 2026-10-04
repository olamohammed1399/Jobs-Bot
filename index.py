import re
import json
import time
import random
import sqlite3
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup

from config import (
    BOT_TOKEN,
    CHAT_ID,
    DB_PATH,
    COOKIES_PATH,
    MAX_PAGES,
    PAGE_SIZE,
    MAX_SEND_PER_RUN
)

from search_config import (
    SEARCH_URLS,
    TITLE_KEYWORDS
)

MAX_FETCH_RETRIES = 3
REQUEST_TIMEOUT = (10, 30)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sent (
            url TEXT PRIMARY KEY,
            sent_at TEXT
        )
        """
    )
    con.commit()
    return con


def already_sent(con, url: str) -> bool:
    cur = con.cursor()
    cur.execute("SELECT 1 FROM sent WHERE url = ?", (url,))
    return cur.fetchone() is not None


def mark_sent(con, url: str):
    cur = con.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO sent(url, sent_at) VALUES(?, ?)",
        (url, datetime.now().isoformat()),
    )
    con.commit()


def telegram_send(text: str):
    token = BOT_TOKEN
    chat_id = CHAT_ID
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars.")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(
        url,
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=20,
    )
    r.raise_for_status()


def load_cookies(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    jar = requests.cookies.RequestsCookieJar()
    for c in data:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain")
        if name and value:
            jar.set(name, value, domain=domain, path=c.get("path", "/"))
    return jar


def build_guest_api_url(base_url: str, start: int) -> str:
    # Convert the search URL into the guest API endpoint for easier parsing
    parsed = urlparse(base_url)
    q = parse_qs(parsed.query)
    q["start"] = [str(start)]
    query = urlencode({k: v[0] for k, v in q.items()})
    return "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?" + query


def normalize_url(url: str) -> str:
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("/jobs/view/"):
        url = "https://www.linkedin.com" + url
    url = url.split("?")[0]
    return url


def title_matches(title: str) -> bool:
    t = (title or "").lower()
    return any(k in t for k in TITLE_KEYWORDS)


def extract_jobs(html: str):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for a in soup.select("a.base-card__full-link"):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if not href:
            continue
        url = normalize_url(href)
        results.append((title, url))

    if results:
        return results

    # Fallback: regex for job links
    for m in re.findall(r"https?://www\.linkedin\.com/jobs/view/\d+", html):
        results.append((None, normalize_url(m)))

    return results


def fetch_with_backoff(session, url: str):
    last_error = None

    for attempt in range(MAX_FETCH_RETRIES):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as exc:
            last_error = exc
            wait_seconds = (2 ** attempt) * 15 + random.uniform(2, 8)
            print(
                f"LinkedIn request failed ({exc.__class__.__name__}). "
                f"Retrying in {wait_seconds:.1f}s..."
            )
            time.sleep(wait_seconds)
            continue

        if resp.status_code not in RETRYABLE_STATUS_CODES:
            return resp

        retry_after = resp.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            wait_seconds = int(retry_after)
        else:
            wait_seconds = (2 ** attempt) * 30

        wait_seconds += random.uniform(2, 8)
        print(
            f"LinkedIn returned {resp.status_code}. "
            f"Retrying in {wait_seconds:.1f}s..."
        )
        time.sleep(wait_seconds)

    if last_error:
        print(f"Skipping page after repeated request failures: {last_error}")
        return None

    print(f"Skipping page after repeated LinkedIn status {resp.status_code}.")
    return resp


def main():
    con = init_db()
    session = requests.Session()
    session.cookies.update(load_cookies(COOKIES_PATH))
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    sent_count = 0
    seen = set()

    for search_url in SEARCH_URLS:
        for page in range(MAX_PAGES):
            start = page * PAGE_SIZE
            url = build_guest_api_url(search_url, start)
            resp = fetch_with_backoff(session, url)
            if resp is None:
                break

            if resp.status_code != 200:
                print(f"Failed to fetch page {page} for {search_url}: {resp.status_code}")
                break

            if "signin" in resp.text.lower() or "challenge" in resp.text.lower():
                print("LinkedIn returned a login or challenge page. Cookies may be invalid.")
                return

            jobs = extract_jobs(resp.text)
            if not jobs:
                print(f"No jobs found for {search_url}.")
                break

            for title, job_url in jobs:
                if not job_url or job_url in seen:
                    continue
                seen.add(job_url)

                if title and not title_matches(title):
                    continue

                if already_sent(con, job_url):
                    continue

                msg_title = title or "LinkedIn job"
                telegram_send(f"{msg_title}\n{job_url}")
                mark_sent(con, job_url)
                sent_count += 1

                if sent_count >= MAX_SEND_PER_RUN:
                    telegram_send("Reached max jobs for this run. Next run will continue.")
                    return

            time.sleep(random.uniform(8, 15))

    if sent_count:
        telegram_send(f"Sent {sent_count} new job(s).")
    else:
        telegram_send("No new jobs found.")


if __name__ == "__main__":
    main()

