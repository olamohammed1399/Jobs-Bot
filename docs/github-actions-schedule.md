# GitHub Actions Schedule

GitHub Actions is the no-card deployment path for this bot. It does not host the
FastAPI `/run` endpoint. Instead, GitHub runs the scraper directly on a schedule:

```text
GitHub Actions schedule -> python index.py -> Telegram
```

## When To Use This

Use this path when you want:

- no Render account;
- no payment card;
- no cron-job.org dependency;
- scheduled runs while your laptop is closed.

GitHub Pages cannot run this bot because GitHub Pages only serves static files.
GitHub Actions can run Python jobs on a schedule.

## Important GitHub Behavior

Scheduled workflows run from the repository's default branch. If the workflow is
merged only into `dev-v2-with-cron-job`, it can be run manually from that branch,
but the hourly schedule starts only after the workflow reaches the default
branch.

## Required Repository Secrets

In GitHub:

```text
Settings -> Secrets and variables -> Actions -> Repository secrets
```

Add:

| Secret | Required | Purpose |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token. |
| `TELEGRAM_CHAT_ID` | Yes | Telegram chat/channel id. |
| `LINKEDIN_COOKIES_JSON` | Yes | Full contents of `cookies.json`. |
| `LINKEDIN_COOKIES_BASE64` | Optional | Base64 alternative to `LINKEDIN_COOKIES_JSON`. |
| `BOT_SETTINGS_JSON` | Optional | Full settings JSON if GitHub should override committed `settings.json`. |

Do not add secrets to repository files.

## Optional Repository Variables

In GitHub:

```text
Settings -> Secrets and variables -> Actions -> Variables
```

Add:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SCRAPE_MAX_PAGES` | `1` | Limits pages fetched per run. |
| `SCRAPE_MAX_SEND` | `10` | Limits matching jobs processed per run. |

The defaults are conservative to reduce LinkedIn rate-limit and challenge risk.

## Manual Run

After the workflow is merged:

1. Open the repository on GitHub.
2. Go to **Actions**.
3. Choose **Scheduled Scrape**.
4. Click **Run workflow**.
5. Pick the branch that contains the workflow.
6. Watch the logs.

The workflow:

1. installs dependencies;
2. rebuilds runtime files from secrets;
3. restores `scrape_jobs.sqlite` from the `github-actions-state` branch;
4. runs `python index.py --max-pages 1 --max-send 10`;
5. saves the updated `scrape_jobs.sqlite` back to `github-actions-state`.

## Schedule

The default schedule is hourly:

```yaml
schedule:
  - cron: "17 * * * *"
```

GitHub schedules use UTC. For Cairo time, this still runs once per hour; only
the displayed hour changes. The workflow runs at minute 17 instead of minute 0
to avoid GitHub's busiest scheduling window. Keep the schedule hourly until the
workflow is stable.

## Persistent State

GitHub runners start fresh each time, so local files do not naturally persist.
The workflow stores only `scrape_jobs.sqlite` on a dedicated branch named:

```text
github-actions-state
```

That branch is force-updated after each run.

If the repository is public, the state branch is also visible. The SQLite file
contains job URLs and run metadata, not Telegram or LinkedIn secrets. If that is
too much public metadata, keep the repository private or use another persistence
method.

## Troubleshooting

### Workflow does not run on schedule

Confirm the workflow file exists on the repository's default branch. GitHub
scheduled workflows do not run from non-default branches.

### Missing cookies

Confirm `LINKEDIN_COOKIES_JSON` contains the full JSON content from
`cookies.json`, not a path to the file.

### Duplicate Telegram messages

Confirm the `github-actions-state` branch exists after the first run and contains
`scrape_jobs.sqlite`.

### Login challenge

Refresh LinkedIn cookies in your browser and update `LINKEDIN_COOKIES_JSON`.

### Workflow fails after scraper error

Check the workflow logs. The final database save step still runs with
`if: always()` so discovered/sent state is preserved when possible.
