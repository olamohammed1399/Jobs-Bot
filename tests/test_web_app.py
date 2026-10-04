import pytest
from fastapi import HTTPException

from index import get_active_run, init_db, start_scraper_run
import web_app


class FakeBackgroundTasks:
    def __init__(self):
        self.tasks = []

    def add_task(self, task, *args):
        self.tasks.append((task, args))


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


def test_run_endpoint_accepts_valid_secret(monkeypatch, tmp_path):
    monkeypatch.setattr(web_app, "CRON_SECRET", "secret-token")
    monkeypatch.setattr(web_app, "get_settings_path", lambda: "settings.json")
    monkeypatch.setattr(
        web_app,
        "load_settings",
        lambda _path: {"db_path": str(tmp_path / "jobs.sqlite")},
    )
    background_tasks = FakeBackgroundTasks()

    response = web_app.run(background_tasks, x_cron_secret="secret-token")

    assert response == {
        "status": "accepted",
        "message": "Scraper run scheduled.",
        "run_id": 1,
    }
    assert background_tasks.tasks == [(web_app.run_scheduled_scraper, (1, "settings.json"))]


def test_run_endpoint_rejects_overlapping_run(monkeypatch, tmp_path):
    db_path = tmp_path / "jobs.sqlite"
    con = init_db(db_path)
    start_scraper_run(con, "cron-http")

    monkeypatch.setattr(web_app, "CRON_SECRET", "secret-token")
    monkeypatch.setattr(web_app, "get_settings_path", lambda: "settings.json")
    monkeypatch.setattr(web_app, "load_settings", lambda _path: {"db_path": str(db_path)})

    with pytest.raises(HTTPException) as error:
        web_app.run(FakeBackgroundTasks(), x_cron_secret="secret-token")

    assert error.value.status_code == 409
    assert error.value.detail["message"] == "Scraper run is already active."
    assert error.value.detail["run_id"] == 1


def test_scheduled_scraper_records_failed_run(monkeypatch, tmp_path):
    db_path = tmp_path / "jobs.sqlite"
    con = init_db(db_path)
    run_record = start_scraper_run(con, "cron-http")

    def failing_run_bot(*, config_path):
        raise RuntimeError("boom")

    monkeypatch.setattr(web_app, "load_settings", lambda _path: {"db_path": str(db_path)})
    monkeypatch.setattr(web_app, "run_bot", failing_run_bot)

    with pytest.raises(RuntimeError, match="boom"):
        web_app.run_scheduled_scraper(run_record.id, "settings.json")

    con = init_db(db_path)
    assert get_active_run(con) is None
    row = con.execute(
        """
        SELECT status, error
        FROM scraper_runs
        WHERE id = ?
        """,
        (run_record.id,),
    ).fetchone()
    assert row == ("failed", "boom")
