# Zero-Cost Hosting

This guide uses a zero-cost-first setup for running the bot from cron-job.org
while the laptop is closed.

## Recommended Free Path

Use Render Free Web Service as the default deployment target for this branch:

- It can host a public Python/FastAPI web service.
- It provides a public HTTPS URL for cron-job.org.
- This repository includes `render.yaml` so the service can be created from a
  blueprint.

Render's free web services can spin down after idle time, and Render documents
the local filesystem as ephemeral for free web services. That means files
created at runtime, including SQLite databases and uploaded local files, can be
lost after a restart, redeploy, or spin-down.

Sources:

- [Render Deploy for Free](https://render.com/docs/free)
- [Render Web Services](https://render.com/docs/web-services)

## Free-Tier Reality Check

Zero-cost hosting is good for proving the cron-job.org flow:

```text
cron-job.org -> hosted /run endpoint -> background scraper -> Telegram
```

It is not the most reliable long-term production setup because:

- Free web services can sleep.
- Cold starts can make the first request slower.
- Local SQLite state may be lost on redeploy/restart/spin-down.
- LinkedIn cookies still expire and must be refreshed manually.

For the first free version, keep the scraper conservative and use Telegram output
as the main result. If duplicate prevention and run history must survive host
restarts, move the database to a persistent external database or a small paid
host later.

## Required Environment Variables

Set these in the hosting dashboard:

| Variable | Required | Purpose |
| --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token. |
| `TELEGRAM_CHAT_ID` | Yes | Telegram channel/chat id. |
| `CRON_SECRET` | Yes | Secret required by `POST /run`. |
| `TELEGRAM_DISABLE_WEB_PAGE_PREVIEW` | No | Defaults to `true`. |
| `BOT_SETTINGS_PATH` | No | Defaults to `settings.json`. |
| `LINKEDIN_COOKIES_JSON` | Yes for cloud | Full `cookies.json` content pasted as JSON. |
| `LINKEDIN_COOKIES_BASE64` | Optional | Base64 alternative to `LINKEDIN_COOKIES_JSON`. |
| `BOT_SETTINGS_JSON` | Optional | Full settings JSON if host config should override committed `settings.json`. |

Use only one of `LINKEDIN_COOKIES_JSON` or `LINKEDIN_COOKIES_BASE64`.
`LINKEDIN_COOKIES_JSON` is easier to maintain in most dashboards.

## Runtime File Preparation

The Render start command runs:

```bash
python scripts/prepare_runtime_files.py && uvicorn web_app:app --host 0.0.0.0 --port $PORT
```

The preparation script:

- writes `BOT_SETTINGS_JSON` to `BOT_SETTINGS_PATH` when provided;
- writes `LINKEDIN_COOKIES_JSON` or `LINKEDIN_COOKIES_BASE64` to the cookies
  path from settings;
- validates JSON before writing files;
- never commits secrets.

## Render Deployment Steps

1. Push this branch to GitHub.
2. Open Render and create a new Blueprint from the repository.
3. Select the `dev-v2-with-cron-job` branch when creating the service.
4. Confirm the service uses the included `render.yaml`.
5. Fill the secret environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `CRON_SECRET`
   - `LINKEDIN_COOKIES_JSON`
6. Deploy the service.
7. Open the generated `onrender.com` URL and test:

```bash
curl https://your-service.onrender.com/health
```

Then test the secured run endpoint:

```bash
curl -X POST https://your-service.onrender.com/run -H "X-Cron-Secret: your-secret"
```

Expected responses:

- `202 Accepted`: run scheduled.
- `401 Unauthorized`: missing or wrong `X-Cron-Secret`.
- `409 Conflict`: another scraper run is already active.
- `503 Service Unavailable`: `CRON_SECRET` is not configured.

## Koyeb Manual Fallback

Koyeb also has a free web service instance, but its free instance has limitations:
one free instance per organization, no volumes for persistent storage, and
scale-to-zero after inactivity.

Source:

- [Koyeb Instances](https://www.koyeb.com/docs/reference/instances)

Manual settings:

- Type: Web Service
- Build command: `pip install -r requirements.txt`
- Run command:

```bash
python scripts/prepare_runtime_files.py && uvicorn web_app:app --host 0.0.0.0 --port $PORT
```

Use the same environment variables listed above.

## cron-job.org Setup Preview

After the host is deployed, cron-job.org should call:

```text
POST https://your-service.example/run
Header: X-Cron-Secret: your-secret
```

For the full dashboard setup, schedule recommendations, and troubleshooting
steps, see [cron-job.org Setup](cron-job-org-setup.md).
