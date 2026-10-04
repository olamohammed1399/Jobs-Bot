import argparse
import logging
import re
import json
import time
import random
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup

from config import (
    BOT_TOKEN,
    CHAT_ID,
    TELEGRAM_DISABLE_WEB_PAGE_PREVIEW,
)

from search_config import (
    DEFAULT_SETTINGS_PATH,
    build_searches,
    load_settings,
)

MAX_FETCH_RETRIES = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "bot.log"
LOGGER = logging.getLogger("job_scraper_bot")


@dataclass
class RuntimeOptions:
    dry_run: bool = False
    no_telegram: bool = False
    debug: bool = False
    config_path: str = str(DEFAULT_SETTINGS_PATH)
    max_pages: int | None = None
    max_send: int | None = None


@dataclass
class RunRecord:
    id: int
    status: str
    started_at: str
    source: str


def setup_logging(debug: bool = False):
    LOG_DIR.mkdir(exist_ok=True)

    level = logging.DEBUG if debug else logging.INFO
    LOGGER.setLevel(level)
    LOGGER.handlers.clear()
    LOGGER.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    LOGGER.addHandler(console_handler)
    LOGGER.addHandler(file_handler)


def init_db(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sent (
            url TEXT PRIMARY KEY,
            sent_at TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            url TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            source_search_url TEXT,
            source_location TEXT,
            source_keyword_group TEXT,
            source_keyword TEXT,
            discovered_at TEXT NOT NULL,
            sent_at TEXT,
            status TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        INSERT OR IGNORE INTO jobs(url, sent_at, discovered_at, status)
        SELECT url, sent_at, COALESCE(sent_at, ?), 'sent'
        FROM sent
        """,
        (datetime.now().isoformat(),),
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS scraper_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            error TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS run_locks (
            name TEXT PRIMARY KEY,
            run_id INTEGER NOT NULL,
            acquired_at TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES scraper_runs(id)
        )
        """
    )
    con.commit()
    return con


def get_active_run(con) -> RunRecord | None:
    cur = con.cursor()
    row = cur.execute(
        """
        SELECT scraper_runs.id,
               scraper_runs.status,
               scraper_runs.started_at,
               scraper_runs.source
        FROM run_locks
        JOIN scraper_runs ON scraper_runs.id = run_locks.run_id
        WHERE run_locks.name = 'scraper'
        """,
    ).fetchone()
    if not row:
        return None
    return RunRecord(id=row[0], status=row[1], started_at=row[2], source=row[3])


def start_scraper_run(con, source: str) -> RunRecord | None:
    now = datetime.now().isoformat()
    cur = con.cursor()
    try:
        cur.execute("BEGIN IMMEDIATE")
        if get_active_run(con):
            con.rollback()
            return None
        cur.execute(
            """
            INSERT INTO scraper_runs(source, status, started_at)
            VALUES(?, 'running', ?)
            """,
            (source, now),
        )
        run_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO run_locks(name, run_id, acquired_at)
            VALUES('scraper', ?, ?)
            """,
            (run_id, now),
        )
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise

    return RunRecord(id=run_id, status="running", started_at=now, source=source)


def finish_scraper_run(con, run_id: int, status: str, error: str | None = None):
    now = datetime.now().isoformat()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE scraper_runs
        SET status = ?,
            finished_at = ?,
            error = ?
        WHERE id = ?
        """,
        (status, now, error, run_id),
    )
    cur.execute(
        """
        DELETE FROM run_locks
        WHERE name = 'scraper'
          AND run_id = ?
        """,
        (run_id,),
    )
    con.commit()


def already_sent(con, url: str) -> bool:
    cur = con.cursor()
    cur.execute(
        """
        SELECT 1
        FROM jobs
        WHERE url = ?
          AND (sent_at IS NOT NULL OR status = 'sent')
        """,
        (url,),
    )
    return cur.fetchone() is not None


def record_job(con, job, search, status: str):
    now = datetime.now().isoformat()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO jobs(
            url,
            title,
            company,
            location,
            source_search_url,
            source_location,
            source_keyword_group,
            source_keyword,
            discovered_at,
            status
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            title = COALESCE(excluded.title, jobs.title),
            company = COALESCE(excluded.company, jobs.company),
            location = COALESCE(excluded.location, jobs.location),
            source_search_url = COALESCE(excluded.source_search_url, jobs.source_search_url),
            source_location = COALESCE(excluded.source_location, jobs.source_location),
            source_keyword_group = COALESCE(excluded.source_keyword_group, jobs.source_keyword_group),
            source_keyword = COALESCE(excluded.source_keyword, jobs.source_keyword),
            status = CASE
                WHEN jobs.status = 'sent' THEN jobs.status
                ELSE excluded.status
            END
        """,
        (
            job["url"],
            job.get("title"),
            job.get("company"),
            job.get("location"),
            search.get("url"),
            search.get("location"),
            search.get("keyword_group"),
            search.get("keyword"),
            now,
            status,
        ),
    )
    con.commit()


def mark_sent(con, job, search):
    now = datetime.now().isoformat()
    record_job(con, job, search, "sent")
    cur = con.cursor()
    cur.execute(
        """
        UPDATE jobs
        SET status = 'sent',
            sent_at = COALESCE(sent_at, ?)
        WHERE url = ?
        """,
        (now, job["url"]),
    )
    cur.execute(
        "INSERT OR IGNORE INTO sent(url, sent_at) VALUES(?, ?)",
        (job["url"], now),
    )
    con.commit()


def telegram_send(text: str):
    token = BOT_TOKEN
    chat_id = CHAT_ID
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars.")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": TELEGRAM_DISABLE_WEB_PAGE_PREVIEW,
            },
            timeout=20,
        )
        r.raise_for_status()
    except requests.exceptions.RequestException:
        LOGGER.exception("Telegram send failed.")
        raise


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


def title_matches(title: str, title_keywords) -> bool:
    t = (title or "").lower()
    return any(k in t for k in title_keywords)


def clean_text(text: str | None) -> str | None:
    if not text:
        return None
    return " ".join(text.split()) or None


def first_text(parent, selectors):
    if not parent:
        return None
    for selector in selectors:
        node = parent.select_one(selector)
        if node:
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                return text
    return None


def find_job_card(link):
    return link.find_parent(
        lambda tag: tag.name in {"li", "div"}
        and any(
            class_name in {
                "base-card",
                "base-search-card",
                "job-search-card",
            }
            for class_name in tag.get("class", [])
        )
    )


def build_job(title, url, company=None, location=None):
    return {
        "title": clean_text(title) or "LinkedIn job",
        "url": normalize_url(url),
        "company": clean_text(company),
        "location": clean_text(location),
    }


def extract_jobs(html: str):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for a in soup.select("a.base-card__full-link"):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if not href:
            continue
        card = find_job_card(a)
        company = first_text(
            card,
            [
                ".base-search-card__subtitle",
                ".job-search-card__subtitle",
                ".hidden-nested-link",
            ],
        )
        location = first_text(
            card,
            [
                ".job-search-card__location",
                ".base-search-card__metadata",
            ],
        )
        results.append(build_job(title, href, company, location))

    if results:
        return results

    # Fallback: regex for job links
    for m in re.findall(r"https?://www\.linkedin\.com/jobs/view/\d+", html):
        results.append(build_job(None, m))

    return results


def format_job_message(job, search):
    lines = [job["title"]]

    if job.get("company"):
        lines.append(f"Company: {job['company']}")

    if job.get("location"):
        lines.append(f"Location: {job['location']}")

    if search:
        lines.append(
            "Search: "
            f"{search['location']} / {search['keyword_group']} / {search['keyword']}"
        )

    lines.append(job["url"])
    return "\n".join(lines)


def deliver_message(text: str, options: RuntimeOptions) -> bool:
    if options.dry_run or options.no_telegram:
        mode = "DRY RUN" if options.dry_run else "NO TELEGRAM"
        LOGGER.info("%s would send message:\n%s", mode, text)
        return False

    telegram_send(text)
    LOGGER.info("Telegram message sent.")
    return True


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape LinkedIn jobs and send matching jobs to Telegram."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_SETTINGS_PATH),
        help=f"Path to runtime settings JSON. Default: {DEFAULT_SETTINGS_PATH}.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print matching jobs without sending Telegram messages or marking them sent.",
    )
    parser.add_argument(
        "--no-telegram",
        action="store_true",
        help="Print matching jobs without sending Telegram messages or marking them sent.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Override pages fetched per search for one run.",
    )
    parser.add_argument(
        "--max-send",
        type=int,
        default=None,
        help="Override max matching jobs processed for one run.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print extra skip/debug information while running.",
    )
    return parser.parse_args()


def build_runtime_options(args, settings):
    max_pages = args.max_pages if args.max_pages is not None else settings["max_pages"]
    max_send = args.max_send if args.max_send is not None else settings["max_send_per_run"]

    if max_pages < 1:
        raise ValueError("--max-pages must be at least 1.")
    if max_send < 1:
        raise ValueError("--max-send must be at least 1.")

    return RuntimeOptions(
        dry_run=args.dry_run,
        no_telegram=args.no_telegram,
        debug=args.debug,
        config_path=args.config,
        max_pages=max_pages,
        max_send=max_send,
    )


def build_runtime_options_from_values(
    settings,
    *,
    config_path: str = str(DEFAULT_SETTINGS_PATH),
    dry_run: bool = False,
    no_telegram: bool = False,
    debug: bool = False,
    max_pages: int | None = None,
    max_send: int | None = None,
):
    args = argparse.Namespace(
        config=config_path,
        dry_run=dry_run,
        no_telegram=no_telegram,
        debug=debug,
        max_pages=max_pages,
        max_send=max_send,
    )
    return build_runtime_options(args, settings)


def run_bot(
    *,
    config_path: str = str(DEFAULT_SETTINGS_PATH),
    dry_run: bool = False,
    no_telegram: bool = False,
    debug: bool = False,
    max_pages: int | None = None,
    max_send: int | None = None,
):
    settings = load_settings(config_path)
    options = build_runtime_options_from_values(
        settings,
        config_path=config_path,
        dry_run=dry_run,
        no_telegram=no_telegram,
        debug=debug,
        max_pages=max_pages,
        max_send=max_send,
    )
    main(options, settings)


def fetch_with_backoff(session, url: str, request_timeout):
    last_error = None

    for attempt in range(MAX_FETCH_RETRIES):
        try:
            resp = session.get(url, timeout=request_timeout)
        except requests.exceptions.RequestException as exc:
            last_error = exc
            wait_seconds = (2 ** attempt) * 15 + random.uniform(2, 8)
            LOGGER.warning(
                "LinkedIn request failed (%s). Retrying in %.1fs.",
                exc.__class__.__name__,
                wait_seconds,
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
        LOGGER.warning(
            "LinkedIn returned retryable status %s. Retrying in %.1fs.",
            resp.status_code,
            wait_seconds,
        )
        time.sleep(wait_seconds)

    if last_error:
        LOGGER.error("Skipping page after repeated request failures: %s", last_error)
        return None

    LOGGER.error("Skipping page after repeated LinkedIn status %s.", resp.status_code)
    return resp


def main(options: RuntimeOptions, settings):
    setup_logging(options.debug)
    searches = build_searches(settings)
    title_keywords = settings["title_keywords"]
    page_size = settings["page_size"]
    request_timeout = tuple(settings["request_timeout"])

    LOGGER.info(
        "Bot started. config=%s searches=%s max_pages=%s max_send=%s dry_run=%s no_telegram=%s debug=%s",
        options.config_path,
        len(searches),
        options.max_pages,
        options.max_send,
        options.dry_run,
        options.no_telegram,
        options.debug,
    )
    con = init_db(settings["db_path"])
    session = requests.Session()
    session.cookies.update(load_cookies(settings["cookies_path"]))
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    sent_count = 0
    processed_count = 0
    extracted_count = 0
    duplicate_count = 0
    title_skip_count = 0
    seen = set()

    for search in searches:
        search_url = search["url"]
        LOGGER.info(
            "Starting search. location=%s keyword_group=%s keyword=%s",
            search["location"],
            search["keyword_group"],
            search["keyword"],
        )
        for page in range(options.max_pages):
            start = page * page_size
            url = build_guest_api_url(search_url, start)
            LOGGER.info(
                "Fetching page. location=%s keyword=%s page=%s start=%s",
                search["location"],
                search["keyword"],
                page,
                start,
            )
            resp = fetch_with_backoff(session, url, request_timeout)
            if resp is None:
                break

            if resp.status_code != 200:
                LOGGER.warning(
                    "Failed to fetch page. location=%s keyword=%s page=%s status=%s",
                    search["location"],
                    search["keyword"],
                    page,
                    resp.status_code,
                )
                break

            if "signin" in resp.text.lower() or "challenge" in resp.text.lower():
                LOGGER.error("LinkedIn returned a login or challenge page. Cookies may be invalid.")
                return

            jobs = extract_jobs(resp.text)
            extracted_count += len(jobs)
            LOGGER.info(
                "Extracted jobs. location=%s keyword=%s page=%s count=%s",
                search["location"],
                search["keyword"],
                page,
                len(jobs),
            )
            if not jobs:
                LOGGER.info(
                    "No jobs found. location=%s keyword=%s page=%s",
                    search["location"],
                    search["keyword"],
                    page,
                )
                break

            for job in jobs:
                title = job["title"]
                job_url = job["url"]

                if not job_url or job_url in seen:
                    duplicate_count += 1
                    continue
                seen.add(job_url)
                record_job(con, job, search, "discovered")

                if title and not title_matches(title, title_keywords):
                    title_skip_count += 1
                    record_job(con, job, search, "skipped_title")
                    if options.debug:
                        LOGGER.debug("Skipped title mismatch: %s", title)
                    continue

                if already_sent(con, job_url):
                    duplicate_count += 1
                    if options.debug:
                        LOGGER.debug("Skipped previously sent job: %s", job_url)
                    continue

                sent = deliver_message(format_job_message(job, search), options)
                if sent:
                    mark_sent(con, job, search)
                    sent_count += 1
                processed_count += 1

                if processed_count >= options.max_send:
                    deliver_message(
                        "Run paused.\n"
                        f"Processed: {processed_count} matching job(s)\n"
                        "Reason: reached max jobs for this run.",
                        options,
                    )
                    LOGGER.info(
                        "Run paused. processed=%s sent=%s extracted=%s duplicates=%s title_skips=%s",
                        processed_count,
                        sent_count,
                        extracted_count,
                        duplicate_count,
                        title_skip_count,
                    )
                    return

            time.sleep(random.uniform(8, 15))

    if processed_count:
        deliver_message(
            f"Run complete.\nProcessed: {processed_count} matching job(s).\n"
            f"Sent: {sent_count} job(s).",
            options,
        )
    else:
        deliver_message("Run complete.\nNo new jobs found.", options)

    LOGGER.info(
        "Run complete. processed=%s sent=%s extracted=%s duplicates=%s title_skips=%s",
        processed_count,
        sent_count,
        extracted_count,
        duplicate_count,
        title_skip_count,
    )


if __name__ == "__main__":
    cli_args = parse_args()
    run_bot(
        config_path=cli_args.config,
        dry_run=cli_args.dry_run,
        no_telegram=cli_args.no_telegram,
        debug=cli_args.debug,
        max_pages=cli_args.max_pages,
        max_send=cli_args.max_send,
    )

