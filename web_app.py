import hmac
import logging
import os

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, status

from config import CRON_SECRET
from index import (
    finish_scraper_run,
    get_active_run,
    init_db,
    run_bot,
    start_scraper_run,
)
from search_config import DEFAULT_SETTINGS_PATH, load_settings

LOGGER = logging.getLogger("job_scraper_bot.web")

APP_NAME = "Job Scraper Bot"
SETTINGS_PATH_ENV = "BOT_SETTINGS_PATH"

app = FastAPI(title=APP_NAME)


def get_settings_path() -> str:
    return os.getenv(SETTINGS_PATH_ENV, str(DEFAULT_SETTINGS_PATH))


def require_cron_secret(x_cron_secret: str | None):
    if not CRON_SECRET:
        LOGGER.error("CRON_SECRET is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cron trigger is not configured.",
        )

    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, CRON_SECRET):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret.",
        )


def get_db_connection(settings):
    return init_db(settings["db_path"])


def run_scheduled_scraper(run_id: int, config_path: str):
    settings = load_settings(config_path)
    try:
        run_bot(config_path=config_path)
    except Exception as exc:
        LOGGER.exception("Scheduled scraper run failed. run_id=%s", run_id)
        with get_db_connection(settings) as con:
            finish_scraper_run(con, run_id, "failed", str(exc))
        raise

    with get_db_connection(settings) as con:
        finish_scraper_run(con, run_id, "succeeded")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
    }


@app.post("/run", status_code=status.HTTP_202_ACCEPTED)
def run(
    background_tasks: BackgroundTasks,
    x_cron_secret: str | None = Header(default=None),
):
    require_cron_secret(x_cron_secret)
    config_path = get_settings_path()
    settings = load_settings(config_path)

    with get_db_connection(settings) as con:
        run_record = start_scraper_run(con, "cron-http")
        if not run_record:
            active_run = get_active_run(con)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Scraper run is already active.",
                    "run_id": active_run.id if active_run else None,
                    "started_at": active_run.started_at if active_run else None,
                },
            )

    background_tasks.add_task(run_scheduled_scraper, run_record.id, config_path)
    return {
        "status": "accepted",
        "message": "Scraper run scheduled.",
        "run_id": run_record.id,
    }
