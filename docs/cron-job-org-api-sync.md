# cron-job.org API Sync

Manual dashboard setup is the safest first path. Use API sync only after the
hosted `/run` endpoint works and you want schedule changes to be repeatable from
configuration.

cron-job.org's REST API uses:

- endpoint: `https://api.cron-job.org/`
- auth header: `Authorization: Bearer <api-key>`
- create job: `PUT /jobs`
- update job: `PATCH /jobs/<jobId>`
- POST request method value: `1`
- custom request headers in `extendedData.headers`

Source:

- [cron-job.org REST API](https://docs.cron-job.org/rest-api.html)

## Setup

1. Generate a cron-job.org API key in the cron-job.org Console settings.
2. Add it to `.env` or your shell:

```bash
CRON_JOB_ORG_API_KEY="your-api-key"
```

3. Keep the API key private. Do not commit `.env`.
4. Copy the example config:

```bash
cp cron-job.example.json cron-job.json
```

On Windows PowerShell:

```powershell
Copy-Item cron-job.example.json cron-job.json
```

5. Edit `cron-job.json`:

```json
{
  "job_id": null,
  "title": "LinkedIn scrape bot",
  "enabled": true,
  "url": "https://your-service.onrender.com/run",
  "cron_secret_env": "CRON_SECRET",
  "timezone": "Africa/Cairo",
  "schedule": {
    "minutes": [0],
    "hours": [-1],
    "mdays": [-1],
    "months": [-1],
    "wdays": [-1],
    "expiresAt": 0
  }
}
```

`cron-job.json` is ignored by git because it describes the real hosted URL and
references local secrets. Commit changes to `cron-job.example.json` only when the
shared example should change.

## Dry Run

Always dry-run first:

```bash
python scripts/sync_cron_job.py --config cron-job.json --dry-run
```

Dry-run prints the payload with `X-Cron-Secret` masked:

```json
{
  "job": {
    "requestMethod": 1,
    "extendedData": {
      "headers": {
        "X-Cron-Secret": "***"
      }
    }
  }
}
```

Dry-run requires `CRON_SECRET`, but does not require `CRON_JOB_ORG_API_KEY` and
does not call cron-job.org.

## Create A Job

For a new cron-job.org job, keep:

```json
"job_id": null
```

Then run:

```bash
python scripts/sync_cron_job.py --config cron-job.json
```

cron-job.org returns the new job id:

```json
{
  "jobId": 12345
}
```

Copy that value into `cron-job.json`:

```json
"job_id": 12345
```

## Update A Job

When `job_id` is set, the script updates the existing job:

```bash
python scripts/sync_cron_job.py --config cron-job.json
```

This sends `PATCH /jobs/<job_id>`.

## Schedule Format

The schedule object uses cron-job.org's API shape:

| Field | Meaning |
| --- | --- |
| `timezone` | Timezone name such as `Africa/Cairo`. |
| `expiresAt` | Expiry date as `YYYYMMDDhhmmss`, or `0` for no expiry. |
| `minutes` | Minutes `0-59`, or `[-1]` for every minute. |
| `hours` | Hours `0-23`, or `[-1]` for every hour. |
| `mdays` | Days of month `1-31`, or `[-1]` for every day. |
| `months` | Months `1-12`, or `[-1]` for every month. |
| `wdays` | Days of week, `0` Sunday through `6` Saturday, or `[-1]`. |

Examples:

Every hour at minute zero:

```json
"schedule": {
  "minutes": [0],
  "hours": [-1],
  "mdays": [-1],
  "months": [-1],
  "wdays": [-1],
  "expiresAt": 0
}
```

Every two hours during the work day:

```json
"schedule": {
  "minutes": [0],
  "hours": [9, 11, 13, 15, 17],
  "mdays": [-1],
  "months": [-1],
  "wdays": [0, 1, 2, 3, 4],
  "expiresAt": 0
}
```

## Safety Notes

- Use `--dry-run` before every real update.
- Keep the schedule conservative; every 60 minutes is the normal baseline.
- Keep `save_responses` false unless actively debugging.
- Keep `CRON_JOB_ORG_API_KEY` and `CRON_SECRET` out of git.
- If cron-job.org returns `401`, check the API key.
- If cron-job.org returns `403`, check API key IP restrictions in the Console.
- If cron-job.org returns `429`, wait and retry later.
