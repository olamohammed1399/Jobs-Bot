# Job Scraper Bot

This bot scrapes job listings from LinkedIn and sends them to a Telegram channel.

## Prerequisites

- Python 3.x
- `cookies.json` file (exported from LinkedIn, providing valid session cookies).

## Setup

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment**:
   - Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - Mac/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**:
   - Ensure `cookies.json` is in the project root.
   - Create a `.env` file in the project root (copied from an example or created manually) containing:
     ```
     TELEGRAM_BOT_TOKEN="your_token_here"
     TELEGRAM_CHAT_ID="your_chat_id_here"
     TELEGRAM_DISABLE_WEB_PAGE_PREVIEW="true"
     CRON_SECRET="use-a-long-random-secret-for-the-web-trigger"
     ```
   - Edit `settings.json` to tune runtime behavior and job searches:
     - Update `hours`, `max_pages`, `page_size`, `max_send_per_run`, or `request_timeout`.
     - Add or update entries in `locations` for each target market.
     - Set a location's `enabled` value to `true` or `false`.
     - Add or update entries in `keyword_groups` for role families.
     - Set a keyword group's `enabled` value to `true` or `false`.
     - Use `work_type` values defined in `work_type_filters`, such as `all` or `remote`.
   - Use `settings.example.json` as a safe reference for the expected structure.

## Usage

Run the scraper:
```bash
python index.py
```

Preview matching jobs without sending Telegram messages or marking jobs as sent:
```bash
python index.py --dry-run
```

Limit a one-off run:
```bash
python index.py --max-pages 1 --max-send 5
```

Print extra skip details while testing:
```bash
python index.py --dry-run --debug
```

Collect matching jobs in the terminal without Telegram delivery:
```bash
python index.py --no-telegram
```

Run with a different settings file:
```bash
python index.py --config settings.example.json --dry-run
```

## HTTP Trigger

The bot can expose a small HTTP app for schedulers such as cron-job.org. The
scheduled request calls the hosted app, and the app starts a scraper run.

Start the web app locally:
```bash
uvicorn web_app:app --host 0.0.0.0 --port 8000
```

Health check:
```bash
curl http://localhost:8000/health
```

Trigger a run:
```bash
curl -X POST http://localhost:8000/run -H "X-Cron-Secret: your-secret"
```

Required web environment variables:

- `CRON_SECRET`: shared secret required by `POST /run`.
- `BOT_SETTINGS_PATH`: optional path to the runtime settings JSON. Defaults to
  `settings.json`.
- `LINKEDIN_COOKIES_JSON`: optional full `cookies.json` content used by
  zero-cost cloud hosts to rebuild runtime files at startup.
- `BOT_SETTINGS_JSON`: optional full settings JSON used by zero-cost cloud hosts
  to override the committed settings file at startup.

The `/run` endpoint returns `202 Accepted` when the request is authorized and
the scraper run is scheduled. It returns `409 Conflict` when another scraper run
is already active, `401 Unauthorized` when the `X-Cron-Secret` header is missing
or invalid, and `503 Service Unavailable` when `CRON_SECRET` is not configured
on the server.

For a zero-cost cloud deployment path, see
[docs/zero-cost-hosting.md](docs/zero-cost-hosting.md).

## Tests

Install development dependencies:
```bash
python -m pip install -r requirements-dev.txt
```

Run the test suite:
```bash
pytest
```

Tests cover core parsing, filtering, URL generation, dry-run delivery, and SQLite
dedupe/metadata behavior without calling LinkedIn or Telegram.

## Logs

The bot writes run diagnostics to the console and `logs/bot.log`.
Use `--debug` to include extra skip details while testing.

## Scheduled Runs

The recommended first production setup is Windows Task Scheduler on the machine
that owns the LinkedIn browser session and `cookies.json` file.

Before scheduling:
- Create the virtual environment with `python -m venv venv`.
- Install dependencies with `.\venv\Scripts\python.exe -m pip install -r requirements.txt`.
- Keep `.env` and `cookies.json` in the project root.
- Run a safe preview with `.\scripts\run_bot.ps1 --dry-run --max-pages 1`.

Create the scheduled task:
1. Open **Task Scheduler**.
2. Choose **Create Basic Task**.
3. Pick the cadence you want, such as every 30 minutes or hourly.
4. Choose **Start a program**.
5. Use this program:
   ```text
   powershell.exe
   ```
6. Use these arguments:
   ```text
   -NoProfile -ExecutionPolicy Bypass -File "D:\Hasssan\My-Work(2023 + 2024)\Web\Projects\Bot\scripts\run_bot.ps1"
   ```
7. Set **Start in** to the project root:
   ```text
   D:\Hasssan\My-Work(2023 + 2024)\Web\Projects\Bot
   ```

For a smaller scheduled run, pass CLI options through the script:
```text
-NoProfile -ExecutionPolicy Bypass -File "D:\Hasssan\My-Work(2023 + 2024)\Web\Projects\Bot\scripts\run_bot.ps1" --max-pages 1 --max-send 10
```

### Runtime Files

- `.env`: Telegram credentials and notification settings. Do not commit it.
- `CRON_SECRET`: secret value in `.env` or the production host environment used
  to protect the scheduled HTTP trigger.
- `settings.json`: runtime settings, locations, keyword groups, and title filters.
- `cookies.json`: exported LinkedIn cookies. Do not commit it.
- `scrape_jobs.sqlite`: local database used to avoid sending duplicates.
- `logs/bot.log`: run diagnostics for scheduled executions.
- `render.yaml`: Render Free Web Service blueprint for the zero-cost hosting
  path.

### Inspecting The Database

The bot stores richer job metadata in the `jobs` table while keeping the older
`sent` table for compatibility with existing databases.

Scheduled HTTP runs are tracked in `scraper_runs`, and the active run lock is
stored in `run_locks` so overlapping cron calls cannot start duplicate scraper
instances.

Count jobs by status:
```bash
sqlite3 scrape_jobs.sqlite "SELECT status, COUNT(*) FROM jobs GROUP BY status;"
```

Show recent scheduled runs:
```bash
sqlite3 scrape_jobs.sqlite "SELECT id, source, status, started_at, finished_at, error FROM scraper_runs ORDER BY id DESC LIMIT 10;"
```

Show recently discovered jobs:
```bash
sqlite3 scrape_jobs.sqlite "SELECT discovered_at, status, title, company, location FROM jobs ORDER BY discovered_at DESC LIMIT 10;"
```

## Troubleshooting

- **Login Challenge**: If you see "LinkedIn returned a login or challenge page", your `cookies.json` might be expired or invalid. Refresh them by logging into LinkedIn in your browser and re-exporting the cookies.
- **No logs after scheduled run**: confirm the task's **Start in** value is the project root and that the Windows user can write to the project folder.
- **Python not found**: create the project virtual environment at `venv\Scripts\python.exe` and install dependencies again.
- **No jobs sent**: run `.\scripts\run_bot.ps1 --dry-run --debug --max-pages 1` and inspect `logs/bot.log`.
