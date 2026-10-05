import json

import pytest

from scripts import sync_cron_job


def sample_config():
    return {
        "job_id": 12345,
        "title": "LinkedIn scrape bot",
        "enabled": True,
        "url": "https://example.onrender.com",
        "cron_secret_env": "CRON_SECRET",
        "timezone": "Africa/Cairo",
        "schedule": {
            "minutes": [0],
            "hours": [-1],
            "mdays": [-1],
            "months": [-1],
            "wdays": [-1],
            "expiresAt": 0,
        },
        "request_timeout": 30,
        "save_responses": False,
        "notification": {
            "onFailure": True,
            "onFailureCount": 1,
        },
    }


def test_build_job_payload_targets_run_endpoint_and_post_method():
    payload = sync_cron_job.build_job_payload(sample_config(), "secret-token")
    job = payload["job"]

    assert job["url"] == "https://example.onrender.com/run"
    assert job["requestMethod"] == sync_cron_job.POST_REQUEST_METHOD
    assert job["extendedData"]["headers"] == {"X-Cron-Secret": "secret-token"}
    assert job["schedule"] == {
        "timezone": "Africa/Cairo",
        "expiresAt": 0,
        "minutes": [0],
        "hours": [-1],
        "mdays": [-1],
        "months": [-1],
        "wdays": [-1],
    }


def test_masked_payload_hides_cron_secret():
    payload = sync_cron_job.build_job_payload(sample_config(), "secret-token")

    masked = sync_cron_job.masked_payload(payload)

    assert masked["job"]["extendedData"]["headers"]["X-Cron-Secret"] == "***"
    assert payload["job"]["extendedData"]["headers"]["X-Cron-Secret"] == "secret-token"


def test_build_job_payload_rejects_invalid_schedule_minute():
    config = sample_config()
    config["schedule"]["minutes"] = [60]

    with pytest.raises(
        sync_cron_job.CronJobConfigError,
        match="schedule.minutes values must be between 0 and 59",
    ):
        sync_cron_job.build_job_payload(config, "secret-token")


def test_sync_cron_job_updates_existing_job(monkeypatch):
    calls = []

    class FakeResponse:
        content = b"{}"

        def raise_for_status(self):
            return None

        def json(self):
            return {}

    def fake_request(method, url, headers, json, timeout):
        calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        return FakeResponse()

    monkeypatch.setattr(sync_cron_job.requests, "request", fake_request)

    result = sync_cron_job.sync_cron_job(sample_config(), "api-key", "secret-token")

    assert result == {}
    assert calls[0]["method"] == "patch"
    assert calls[0]["url"] == "https://api.cron-job.org/jobs/12345"
    assert calls[0]["headers"]["Authorization"] == "Bearer api-key"
    assert calls[0]["json"]["job"]["extendedData"]["headers"] == {
        "X-Cron-Secret": "secret-token"
    }


def test_sync_cron_job_creates_new_job(monkeypatch):
    calls = []
    config = sample_config()
    config["job_id"] = None

    class FakeResponse:
        content = b'{"jobId": 67890}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"jobId": 67890}

    def fake_request(method, url, headers, json, timeout):
        calls.append({"method": method, "url": url})
        return FakeResponse()

    monkeypatch.setattr(sync_cron_job.requests, "request", fake_request)

    result = sync_cron_job.sync_cron_job(config, "api-key", "secret-token")

    assert result == {"jobId": 67890}
    assert calls == [{"method": "put", "url": "https://api.cron-job.org/jobs"}]


def test_main_dry_run_does_not_require_api_key(monkeypatch, tmp_path, capsys):
    config_path = tmp_path / "cron-job.json"
    config_path.write_text(json.dumps(sample_config()), encoding="utf-8")
    monkeypatch.setenv("CRON_SECRET", "secret-token")
    monkeypatch.delenv(sync_cron_job.API_KEY_ENV, raising=False)
    monkeypatch.setattr(
        sync_cron_job,
        "parse_args",
        lambda: type("Args", (), {"config": str(config_path), "dry_run": True})(),
    )

    exit_code = sync_cron_job.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"X-Cron-Secret": "***"' in output
    assert "secret-token" not in output
