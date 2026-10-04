import base64
import json
import os
import sys
from pathlib import Path


DEFAULT_SETTINGS_PATH = "settings.json"
DEFAULT_COOKIES_PATH = "cookies.json"


def load_json_env(name: str):
    value = os.getenv(name)
    if not value:
        return None

    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} must contain valid JSON: {exc}") from exc


def load_base64_json_env(name: str):
    value = os.getenv(name)
    if not value:
        return None

    try:
        decoded = base64.b64decode(value).decode("utf-8")
        return json.loads(decoded)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name} must contain base64-encoded JSON: {exc}") from exc


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote runtime JSON file: {path}")


def settings_path() -> Path:
    return Path(os.getenv("BOT_SETTINGS_PATH", DEFAULT_SETTINGS_PATH))


def cookies_path(settings_file: Path) -> Path:
    if not settings_file.exists():
        return Path(DEFAULT_COOKIES_PATH)

    settings = json.loads(settings_file.read_text(encoding="utf-8"))
    return Path(settings.get("cookies_path", DEFAULT_COOKIES_PATH))


def prepare_runtime_files():
    settings_file = settings_path()
    settings_data = load_json_env("BOT_SETTINGS_JSON")
    if settings_data is not None:
        write_json(settings_file, settings_data)

    cookies_data = load_json_env("LINKEDIN_COOKIES_JSON")
    if cookies_data is None:
        cookies_data = load_base64_json_env("LINKEDIN_COOKIES_BASE64")

    if cookies_data is not None:
        write_json(cookies_path(settings_file), cookies_data)


def main() -> int:
    try:
        prepare_runtime_files()
    except ValueError as exc:
        print(f"Runtime file preparation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
