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

## Troubleshooting

- **Login Challenge**: If you see "LinkedIn returned a login or challenge page", your `cookies.json` might be expired or invalid. Refresh them by logging into LinkedIn in your browser and re-exporting the cookies.
