import sqlite3
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

from index import (
    RuntimeOptions,
    already_sent,
    build_guest_api_url,
    build_runtime_options,
    deliver_message,
    extract_jobs,
    format_job_message,
    init_db,
    mark_sent,
    normalize_url,
    record_job,
    title_matches,
)
from search_config import SettingsError, build_search_url, build_searches, validate_settings


def sample_settings():
    return {
        "hours": 5,
        "max_pages": 5,
        "page_size": 25,
        "max_send_per_run": 20,
        "request_timeout": [10, 30],
        "db_path": "scrape_jobs.sqlite",
        "cookies_path": "cookies.json",
        "work_type_filters": {
            "remote": "2",
            "all": "1%2C2%2C3",
        },
        "locations": [
            {
                "name": "Cairo",
                "geo_id": "102007122",
                "easy_apply": True,
                "work_type": "all",
                "enabled": True,
            },
            {
                "name": "Remote",
                "geo_id": None,
                "easy_apply": None,
                "work_type": "remote",
                "enabled": False,
            },
        ],
        "keyword_groups": [
            {
                "name": "frontend",
                "keywords": ["frontend", "reactjs"],
                "enabled": True,
            },
            {
                "name": "backend",
                "keywords": ["backend"],
                "enabled": False,
            },
        ],
        "title_keywords": ["frontend", "react", "backend"],
    }


def sample_search():
    return {
        "url": "https://www.linkedin.com/jobs/search/?keywords=frontend",
        "location": "Cairo",
        "keyword_group": "frontend",
        "keyword": "frontend",
    }


def sample_job():
    return {
        "title": "Frontend Developer",
        "url": "https://www.linkedin.com/jobs/view/123456",
        "company": "Example Co",
        "location": "Cairo, Egypt",
    }


def test_normalize_url_handles_relative_protocol_and_tracking_params():
    assert (
        normalize_url("//www.linkedin.com/jobs/view/1?x=1")
        == "https://www.linkedin.com/jobs/view/1"
    )
    assert normalize_url("/jobs/view/2?trk=abc") == "https://www.linkedin.com/jobs/view/2"
    assert (
        normalize_url("https://www.linkedin.com/jobs/view/3?ref=abc")
        == "https://www.linkedin.com/jobs/view/3"
    )


def test_build_guest_api_url_preserves_query_and_adds_start():
    url = build_guest_api_url(
        "https://www.linkedin.com/jobs/search/?keywords=frontend&geoId=102007122",
        25,
    )

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "www.linkedin.com"
    assert parsed.path == "/jobs-guest/jobs/api/seeMoreJobPostings/search"
    assert query["keywords"] == ["frontend"]
    assert query["geoId"] == ["102007122"]
    assert query["start"] == ["25"]


def test_title_matches_is_case_insensitive():
    assert title_matches("Senior React Developer", ["react"])
    assert not title_matches("Product Manager", ["react", "frontend"])


def test_build_searches_generates_enabled_location_keyword_pairs():
    settings = sample_settings()
    searches = build_searches(settings)

    assert len(searches) == 2
    assert [search["keyword"] for search in searches] == ["frontend", "reactjs"]
    assert all(search["location"] == "Cairo" for search in searches)


def test_build_search_url_formats_linkedin_filters():
    settings = sample_settings()
    location = settings["locations"][0]
    url = build_search_url(settings, location, "frontend developer")

    assert "f_AL=true" in url
    assert "geoId=102007122" in url
    assert "f_TPR=r18000" in url
    assert "keywords=frontend%20developer" in url
    assert "f_WT=1%2C2%2C3" in url


def test_validate_settings_rejects_missing_required_fields():
    settings = sample_settings()
    del settings["locations"]

    with pytest.raises(SettingsError, match="missing required field 'locations'"):
        validate_settings(settings, Path("settings.json"))


def test_extract_jobs_reads_card_metadata_from_fixture():
    html = Path("tests/fixtures/linkedin_jobs.html").read_text(encoding="utf-8")
    jobs = extract_jobs(html)

    assert jobs == [
        {
            "title": "Frontend Developer",
            "url": "https://www.linkedin.com/jobs/view/123456",
            "company": "Example Co",
            "location": "Cairo, Egypt",
        },
        {
            "title": "Backend Engineer",
            "url": "https://www.linkedin.com/jobs/view/789012",
            "company": "API Studio",
            "location": "Remote",
        },
    ]


def test_extract_jobs_falls_back_to_regex_links():
    jobs = extract_jobs("see https://www.linkedin.com/jobs/view/555 and apply")

    assert jobs == [
        {
            "title": "LinkedIn job",
            "url": "https://www.linkedin.com/jobs/view/555",
            "company": None,
            "location": None,
        }
    ]


def test_format_job_message_omits_missing_fields():
    job = {
        "title": "LinkedIn job",
        "url": "https://www.linkedin.com/jobs/view/555",
        "company": None,
        "location": None,
    }

    assert format_job_message(job, sample_search()) == (
        "LinkedIn job\n"
        "Search: Cairo / frontend / frontend\n"
        "https://www.linkedin.com/jobs/view/555"
    )


def test_init_db_migrates_existing_sent_urls(tmp_path):
    db_path = tmp_path / "jobs.sqlite"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE sent (url TEXT PRIMARY KEY, sent_at TEXT)")
    con.execute(
        "INSERT INTO sent(url, sent_at) VALUES(?, ?)",
        ("https://www.linkedin.com/jobs/view/1", "2026-01-01T00:00:00"),
    )
    con.commit()
    con.close()

    con = init_db(db_path)

    assert already_sent(con, "https://www.linkedin.com/jobs/view/1")
    row = con.execute(
        "SELECT status, sent_at FROM jobs WHERE url = ?",
        ("https://www.linkedin.com/jobs/view/1",),
    ).fetchone()
    assert row == ("sent", "2026-01-01T00:00:00")


def test_record_job_and_mark_sent_store_metadata(tmp_path):
    con = init_db(tmp_path / "jobs.sqlite")
    job = sample_job()
    search = sample_search()

    record_job(con, job, search, "discovered")
    assert not already_sent(con, job["url"])

    mark_sent(con, job, search)

    assert already_sent(con, job["url"])
    row = con.execute(
        """
        SELECT title, company, location, source_location,
               source_keyword_group, source_keyword, status
        FROM jobs
        WHERE url = ?
        """,
        (job["url"],),
    ).fetchone()
    assert row == (
        "Frontend Developer",
        "Example Co",
        "Cairo, Egypt",
        "Cairo",
        "frontend",
        "frontend",
        "sent",
    )


def test_deliver_message_dry_run_does_not_send(monkeypatch):
    called = False

    def fake_telegram_send(_text):
        nonlocal called
        called = True

    monkeypatch.setattr("index.telegram_send", fake_telegram_send)

    sent = deliver_message("hello", RuntimeOptions(dry_run=True))

    assert sent is False
    assert called is False


def test_build_runtime_options_uses_settings_defaults_and_cli_overrides():
    settings = sample_settings()
    args = SimpleNamespace(
        dry_run=True,
        no_telegram=False,
        debug=True,
        config="settings.json",
        max_pages=None,
        max_send=3,
    )

    options = build_runtime_options(args, settings)

    assert options.dry_run is True
    assert options.debug is True
    assert options.max_pages == settings["max_pages"]
    assert options.max_send == 3
