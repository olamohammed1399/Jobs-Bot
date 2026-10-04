import base64
import json

import pytest

from scripts import prepare_runtime_files


def test_prepare_runtime_files_writes_settings_and_cookies(monkeypatch, tmp_path):
    settings_path = tmp_path / "settings.json"
    cookies_path = tmp_path / "runtime" / "cookies.json"
    settings = {
        "db_path": "scrape_jobs.sqlite",
        "cookies_path": str(cookies_path),
    }
    cookies = [
        {
            "name": "li_at",
            "value": "secret",
            "domain": ".linkedin.com",
            "path": "/",
        }
    ]

    monkeypatch.setenv("BOT_SETTINGS_PATH", str(settings_path))
    monkeypatch.setenv("BOT_SETTINGS_JSON", json.dumps(settings))
    monkeypatch.setenv("LINKEDIN_COOKIES_JSON", json.dumps(cookies))

    prepare_runtime_files.prepare_runtime_files()

    assert json.loads(settings_path.read_text(encoding="utf-8")) == settings
    assert json.loads(cookies_path.read_text(encoding="utf-8")) == cookies


def test_prepare_runtime_files_supports_base64_cookies(monkeypatch, tmp_path):
    settings_path = tmp_path / "settings.json"
    cookies_path = tmp_path / "cookies.json"
    settings_path.write_text(
        json.dumps({"cookies_path": str(cookies_path)}),
        encoding="utf-8",
    )
    encoded = base64.b64encode(b'[{"name": "li_at", "value": "secret"}]').decode(
        "utf-8"
    )

    monkeypatch.setenv("BOT_SETTINGS_PATH", str(settings_path))
    monkeypatch.setenv("LINKEDIN_COOKIES_BASE64", encoded)

    prepare_runtime_files.prepare_runtime_files()

    assert json.loads(cookies_path.read_text(encoding="utf-8")) == [
        {"name": "li_at", "value": "secret"}
    ]


def test_prepare_runtime_files_rejects_invalid_settings_json(monkeypatch, tmp_path):
    monkeypatch.setenv("BOT_SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setenv("BOT_SETTINGS_JSON", "{not-json")

    with pytest.raises(ValueError, match="BOT_SETTINGS_JSON must contain valid JSON"):
        prepare_runtime_files.prepare_runtime_files()
