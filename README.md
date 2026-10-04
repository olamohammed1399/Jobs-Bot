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
     ```
   - Edit `search_config.py` to tune job searches:
     - Add or update entries in `LOCATIONS` for each target market.
     - Set a location's `enabled` value to `True` or `False`.
     - Add or update entries in `KEYWORD_GROUPS` for role families.
     - Set a keyword group's `enabled` value to `True` or `False`.
     - Use `work_type` values of `all` or `remote`.

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
- `cookies.json`: exported LinkedIn cookies. Do not commit it.
- `scrape_jobs.sqlite`: local database used to avoid sending duplicates.
- `logs/bot.log`: run diagnostics for scheduled executions.

## Troubleshooting

- **Login Challenge**: If you see "LinkedIn returned a login or challenge page", your `cookies.json` might be expired or invalid. Refresh them by logging into LinkedIn in your browser and re-exporting the cookies.
- **No logs after scheduled run**: confirm the task's **Start in** value is the project root and that the Windows user can write to the project folder.
- **Python not found**: create the project virtual environment at `venv\Scripts\python.exe` and install dependencies again.
- **No jobs sent**: run `.\scripts\run_bot.ps1 --dry-run --debug --max-pages 1` and inspect `logs/bot.log`.
