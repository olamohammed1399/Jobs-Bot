import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


API_ENDPOINT = "https://api.cron-job.org"
API_KEY_ENV = "CRON_JOB_ORG_API_KEY"
CONFIG_PATH = Path("cron-job.json")
POST_REQUEST_METHOD = 1


class CronJobConfigError(ValueError):
    pass


def load_json_file(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CronJobConfigError(f"Config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CronJobConfigError(f"Invalid JSON in {path}: {exc}") from exc


def validate_int_list(name: str, values, minimum: int, maximum: int, allow_any=True):
    if not isinstance(values, list) or not values:
        raise CronJobConfigError(f"{name} must be a non-empty list.")

    if allow_any and values == [-1]:
        return values

    for value in values:
        if not isinstance(value, int):
            raise CronJobConfigError(f"{name} values must be integers.")
        if value < minimum or value > maximum:
            raise CronJobConfigError(
                f"{name} values must be between {minimum} and {maximum}."
            )

    return values


def validate_schedule(schedule):
    if not isinstance(schedule, dict):
        raise CronJobConfigError("schedule must be an object.")

    return {
        "timezone": schedule.get("timezone"),
        "expiresAt": schedule.get("expiresAt", 0),
        "minutes": validate_int_list("schedule.minutes", schedule.get("minutes"), 0, 59),
        "hours": validate_int_list("schedule.hours", schedule.get("hours"), 0, 23),
        "mdays": validate_int_list("schedule.mdays", schedule.get("mdays"), 1, 31),
        "months": validate_int_list("schedule.months", schedule.get("months"), 1, 12),
        "wdays": validate_int_list("schedule.wdays", schedule.get("wdays"), 0, 6),
    }


def build_schedule(config):
    schedule = validate_schedule(config.get("schedule"))
    timezone = config.get("timezone", schedule.get("timezone") or "UTC")
    expires_at = schedule["expiresAt"]
    if not isinstance(expires_at, int) or expires_at < 0:
        raise CronJobConfigError("schedule.expiresAt must be a non-negative integer.")

    return {
        "timezone": timezone,
        "expiresAt": expires_at,
        "minutes": schedule["minutes"],
        "hours": schedule["hours"],
        "mdays": schedule["mdays"],
        "months": schedule["months"],
        "wdays": schedule["wdays"],
    }


def require_string(config, key: str) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CronJobConfigError(f"{key} must be a non-empty string.")
    return value.strip()


def build_job_payload(config, cron_secret: str):
    url = require_string(config, "url")
    try:
        request_timeout = int(config.get("request_timeout", 30))
    except (TypeError, ValueError) as exc:
        raise CronJobConfigError("request_timeout must be an integer.") from exc
    if request_timeout < 1:
        raise CronJobConfigError("request_timeout must be at least 1.")

    job = {
        "title": config.get("title", "LinkedIn scrape bot"),
        "enabled": bool(config.get("enabled", True)),
        "url": url.rstrip("/") + "/run" if not url.endswith("/run") else url,
        "requestMethod": POST_REQUEST_METHOD,
        "requestTimeout": request_timeout,
        "saveResponses": bool(config.get("save_responses", False)),
        "schedule": build_schedule(config),
        "extendedData": {
            "headers": {
                "X-Cron-Secret": cron_secret,
            },
            "body": "",
        },
    }

    notification = config.get("notification")
    if notification is not None:
        if not isinstance(notification, dict):
            raise CronJobConfigError("notification must be an object.")
        job["notification"] = notification

    return {"job": job}


def masked_payload(payload):
    masked = json.loads(json.dumps(payload))
    headers = masked["job"].setdefault("extendedData", {}).setdefault("headers", {})
    if "X-Cron-Secret" in headers:
        headers["X-Cron-Secret"] = "***"
    return masked


def request_headers(api_key: str):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def sync_cron_job(config, api_key: str, cron_secret: str):
    payload = build_job_payload(config, cron_secret)
    job_id = config.get("job_id")
    method = "patch" if job_id else "put"
    path = f"/jobs/{job_id}" if job_id else "/jobs"
    response = requests.request(
        method,
        API_ENDPOINT + path,
        headers=request_headers(api_key),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create or update the cron-job.org schedule from a JSON config."
    )
    parser.add_argument(
        "--config",
        default=str(CONFIG_PATH),
        help=f"Path to cron-job.org sync config. Default: {CONFIG_PATH}.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the API payload without calling cron-job.org.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    try:
        config = load_json_file(Path(args.config))
        cron_secret_env = config.get("cron_secret_env", "CRON_SECRET")
        cron_secret = os.getenv(cron_secret_env)
        if not cron_secret:
            raise CronJobConfigError(f"Missing {cron_secret_env} environment variable.")

        payload = build_job_payload(config, cron_secret)
        if args.dry_run:
            print(json.dumps(masked_payload(payload), indent=2))
            return 0

        api_key = os.getenv(API_KEY_ENV)
        if not api_key:
            raise CronJobConfigError(f"Missing {API_KEY_ENV} environment variable.")

        result = sync_cron_job(config, api_key, cron_secret)
    except (CronJobConfigError, requests.RequestException) as exc:
        print(f"cron-job.org sync failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
