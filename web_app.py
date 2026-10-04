import hmac
import logging
import os

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, status

from config import CRON_SECRET
from index import run_bot
from search_config import DEFAULT_SETTINGS_PATH

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


def run_scheduled_scraper():
    run_bot(config_path=get_settings_path())


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
    background_tasks.add_task(run_scheduled_scraper)
    return {
        "status": "accepted",
        "message": "Scraper run scheduled.",
    }
