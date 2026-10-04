import json
from pathlib import Path
from urllib.parse import quote


DEFAULT_SETTINGS_PATH = Path("settings.json")


class SettingsError(ValueError):
    pass


def load_settings(path=DEFAULT_SETTINGS_PATH):
    settings_path = Path(path)
    try:
        with settings_path.open("r", encoding="utf-8") as f:
            settings = json.load(f)
    except FileNotFoundError as exc:
        raise SettingsError(f"Settings file not found: {settings_path}") from exc
    except json.JSONDecodeError as exc:
        raise SettingsError(f"Invalid JSON in settings file: {settings_path}") from exc

    validate_settings(settings, settings_path)
    return settings


def validate_settings(settings, settings_path):
    required_fields = {
        "hours": int,
        "max_pages": int,
        "page_size": int,
        "max_send_per_run": int,
        "request_timeout": list,
        "db_path": str,
        "cookies_path": str,
        "work_type_filters": dict,
        "locations": list,
        "keyword_groups": list,
        "title_keywords": list,
    }

    for field, expected_type in required_fields.items():
        if field not in settings:
            raise SettingsError(f"{settings_path}: missing required field '{field}'.")
        if not isinstance(settings[field], expected_type):
            raise SettingsError(
                f"{settings_path}: field '{field}' must be {expected_type.__name__}."
            )

    for field in ["hours", "max_pages", "page_size", "max_send_per_run"]:
        if settings[field] < 1:
            raise SettingsError(f"{settings_path}: field '{field}' must be at least 1.")

    timeout = settings["request_timeout"]
    valid_timeout = (
        len(timeout) == 2
        and all(isinstance(value, (int, float)) and value > 0 for value in timeout)
    )
    if not valid_timeout:
        raise SettingsError(
            f"{settings_path}: field 'request_timeout' must contain two positive numbers."
        )

    if not settings["locations"]:
        raise SettingsError(f"{settings_path}: at least one location is required.")
    if not settings["keyword_groups"]:
        raise SettingsError(f"{settings_path}: at least one keyword group is required.")
    if not settings["title_keywords"]:
        raise SettingsError(f"{settings_path}: at least one title keyword is required.")

    for location in settings["locations"]:
        validate_location(location, settings)

    for group in settings["keyword_groups"]:
        validate_keyword_group(group, settings_path)


def validate_location(location, settings):
    for field in ["name", "work_type", "enabled"]:
        if field not in location:
            raise SettingsError(f"Location is missing required field '{field}'.")

    if location["work_type"] not in settings["work_type_filters"]:
        raise SettingsError(
            f"Location '{location['name']}' uses unknown work_type '{location['work_type']}'."
        )

    if not isinstance(location["enabled"], bool):
        raise SettingsError(f"Location '{location['name']}' field 'enabled' must be boolean.")

    easy_apply = location.get("easy_apply")
    if easy_apply is not None and not isinstance(easy_apply, bool):
        raise SettingsError(
            f"Location '{location['name']}' field 'easy_apply' must be boolean or null."
        )


def validate_keyword_group(group, settings_path):
    for field in ["name", "keywords", "enabled"]:
        if field not in group:
            raise SettingsError(f"{settings_path}: keyword group is missing required field '{field}'.")

    if not isinstance(group["keywords"], list) or not group["keywords"]:
        raise SettingsError(f"Keyword group '{group['name']}' must define at least one keyword.")

    if not isinstance(group["enabled"], bool):
        raise SettingsError(f"Keyword group '{group['name']}' field 'enabled' must be boolean.")


def build_search_url(settings, location, keyword):
    time_period = settings["hours"] * 3600
    query_parts = [
        f"f_TPR=r{time_period}",
        f"keywords={quote(keyword)}",
    ]

    easy_apply = location.get("easy_apply")
    if easy_apply is not None:
        query_parts.insert(0, f"f_AL={str(easy_apply).lower()}")

    geo_id = location.get("geo_id")
    if geo_id:
        query_parts.insert(1 if easy_apply is not None else 0, f"geoId={geo_id}")

    work_type = location.get("work_type")
    if work_type:
        query_parts.append(f"f_WT={settings['work_type_filters'][work_type]}")

    query_parts.extend(
        [
            "origin=JOB_SEARCH_PAGE_JOB_FILTER",
            "refresh=true",
        ]
    )

    return "https://www.linkedin.com/jobs/search/?" + "&".join(query_parts)


def build_searches(settings):
    return [
        {
            "url": build_search_url(settings, location, keyword),
            "location": location["name"],
            "keyword_group": group["name"],
            "keyword": keyword,
        }
        for location in settings["locations"]
        if location["enabled"]
        for group in settings["keyword_groups"]
        if group["enabled"]
        for keyword in group["keywords"]
    ]


def build_search_urls(settings):
    return [
        search["url"]
        for search in build_searches(settings)
    ]


SETTINGS = load_settings()
SEARCHES = build_searches(SETTINGS)
SEARCH_URLS = [search["url"] for search in SEARCHES]
TITLE_KEYWORDS = SETTINGS["title_keywords"]
