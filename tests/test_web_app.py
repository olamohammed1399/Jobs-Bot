import pytest
from fastapi import HTTPException

import web_app


class FakeBackgroundTasks:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)


def test_health_endpoint_returns_service_status():
    assert web_app.health() == {
        "status": "ok",
        "service": web_app.APP_NAME,
    }


def test_run_endpoint_rejects_missing_secret(monkeypatch):
    monkeypatch.setattr(web_app, "CRON_SECRET", "secret-token")

    with pytest.raises(HTTPException) as error:
        web_app.require_cron_secret(None)

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid cron secret."


def test_run_endpoint_reports_unconfigured_secret(monkeypatch):
    monkeypatch.setattr(web_app, "CRON_SECRET", None)

    with pytest.raises(HTTPException) as error:
        web_app.require_cron_secret("secret-token")

    assert error.value.status_code == 503
    assert error.value.detail == "Cron trigger is not configured."


def test_run_endpoint_accepts_valid_secret(monkeypatch):
    monkeypatch.setattr(web_app, "CRON_SECRET", "secret-token")
    background_tasks = FakeBackgroundTasks()

    response = web_app.run(background_tasks, x_cron_secret="secret-token")

    assert response == {
        "status": "accepted",
        "message": "Scraper run scheduled.",
    }
    assert background_tasks.tasks == [web_app.run_scheduled_scraper]
