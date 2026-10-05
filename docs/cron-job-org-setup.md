# cron-job.org Setup

Use cron-job.org after the bot is deployed to a public HTTPS URL. cron-job.org
does not run Python directly. It sends an HTTP request to the hosted `/run`
endpoint, and the hosted app starts the scraper in the background.

## Prerequisites

- A deployed bot URL, such as `https://your-service.onrender.com`.
- A configured `CRON_SECRET` value on the host.
- A working health check:

```bash
curl https://your-service.onrender.com/health
```

- A successful manual secured trigger:

```bash
curl -X POST https://your-service.onrender.com/run -H "X-Cron-Secret: your-secret"
```

Expected manual trigger result:

```json
{
  "status": "accepted",
  "message": "Scraper run scheduled.",
  "run_id": 1
}
```

## Create The cron-job.org Job

1. Sign in to [cron-job.org](https://cron-job.org/).
2. Create a new cron job.
3. Set the request URL:

```text
https://your-service.onrender.com/run
```

4. Set the HTTP method to `POST`.
5. Add a custom request header:

```text
X-Cron-Secret: your-secret
```

6. Do not add the Telegram token, LinkedIn cookies, or settings JSON to
   cron-job.org. Those belong in the host environment.
7. Save the job.
8. Use cron-job.org's manual execution/test action once before enabling a
   recurring schedule.

cron-job.org supports custom headers and request methods, which is why the bot
uses the `X-Cron-Secret` header for authorization.

Sources:

- [cron-job.org FAQ](https://cron-job.org/en/faq/)
- [cron-job.org Creating cron jobs](https://docs.cron-job.org/creating-cron-jobs.html)

## Recommended Schedule

Start conservatively:

```text
Every 60 minutes
```

Use the timezone that matches how you reason about job alerts. For this project,
`Africa/Cairo` is a good default when the deployment and Telegram usage are tied
to Cairo working hours.

Avoid schedules like every minute or every five minutes. LinkedIn scraping is
sensitive to rate limits, cookies can expire, and the hosted app already
deduplicates sent jobs. A slower cadence is safer and easier to debug.

Suggested first schedules:

| Phase | Schedule | Why |
| --- | --- | --- |
| Smoke test | Manual run only | Confirms host, secret, cookies, and Telegram. |
| First day | Every 2 hours | Reduces risk while validating behavior. |
| Normal free-tier use | Every 60 minutes | Reasonable balance for job alerts. |
| Aggressive use | Every 30 minutes | Only after logs look healthy. |

## Expected Responses

| Response | Meaning | Action |
| --- | --- | --- |
| `202 Accepted` | cron-job.org reached the bot and a run was scheduled. | Good. Check Telegram or host logs for scraper results. |
| `401 Unauthorized` | The `X-Cron-Secret` header is missing or wrong. | Update the cron-job.org custom header or host `CRON_SECRET`. |
| `409 Conflict` | A previous scraper run is still active. | Keep the schedule slower or inspect run history. |
| `503 Service Unavailable` | The host is missing `CRON_SECRET`. | Add the env var on the host and redeploy/restart. |
| Timeout | cron-job.org did not receive a fast response. | Check whether the host is cold-starting or unhealthy. |

cron-job.org's timeout guidance explains that long-running scripts should not
hold the HTTP request open. This project avoids that by returning `202 Accepted`
after scheduling background work.

Source:

- [cron-job.org timeout explanation](https://blog.cron-job.org/service/2021/12/01/errors-explained-timeout.html)

## Notifications And Logs

In cron-job.org:

- enable failure notifications for the job;
- inspect execution history after the first manual run;
- keep saved responses small if you enable response saving.

On the host:

- inspect deployment/runtime logs after each cron-job.org failure;
- check `/health` first when cron-job.org reports connection problems;
- check the SQLite run history when the filesystem is still available:

```bash
sqlite3 scrape_jobs.sqlite "SELECT id, source, status, started_at, finished_at, error FROM scraper_runs ORDER BY id DESC LIMIT 10;"
```

## Troubleshooting

### The job says unauthorized

Check that the custom header name is exactly:

```text
X-Cron-Secret
```

The value must match the host's `CRON_SECRET` exactly.

### The job times out

Open the hosted `/health` URL. On free hosting, the first request can wake a
sleeping service. After the service is awake, rerun the cron-job.org job.

### The job returns conflict

The previous scrape has not released the run lock yet. Keep the schedule at 60
minutes or longer until the scraper consistently finishes faster.

### The job succeeds but no Telegram message appears

Check host logs for LinkedIn login/challenge messages and verify that
`LINKEDIN_COOKIES_JSON` is current. The bot can run successfully and still find
no new matching jobs.

### The job works locally but not from cron-job.org

Make sure cron-job.org points to the public hosted URL, not `localhost`, a local
network address, or your laptop.

## REST API Note

cron-job.org also has a REST API for programmatic job management. That belongs
to the optional API sync flow. For the first zero-cost setup, use the dashboard
manually. After the dashboard flow works, see
[cron-job.org API Sync](cron-job-org-api-sync.md).

Source:

- [cron-job.org REST API](https://docs.cron-job.org/rest-api.html)
