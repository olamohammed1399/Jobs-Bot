import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DB_PATH = "scrape_jobs.sqlite"
COOKIES_PATH = "cookies.json"
HOURS = 5                          # 1 hour
TIME_PERIOD = HOURS * 3600         # 3600 seconds * HOURS
EGYPT_GEO_ID = "106155005"         # Egypt
CAIRO_GEO_ID = "102007122"         # Cairo
SUA_GEO_ID = "100459316"           # Saudi Arabia
RIYADH_GEO_ID = "101336206"        # Riyadh
JEDDAH_GEO_ID = "117963601"        # Jeddah
SPAIN_GEO_ID = "105646813"         # Spain
QATTA_GEO_ID = "104170880"         # Qatta
DOHA_GEO_ID = "106203786"          # Doha
UNITED_ARAB_EMIRATES_GEO_ID = "104305776"  # United Arab Emirates
ABU_DHABI_GEO_ID = "103720977"     # Abu Dhabi
KUWAIT_GEO_ID = "103239229"        # Kuwait

EGYPT_IS_EASY_APPLY = 'true'       # for easy apply filter
CAIRO_IS_EASY_APPLY = 'true'       # for easy apply filter
SUA_IS_EASY_APPLY = 'true'         # for easy apply filter
RIYADH_IS_EASY_APPLY = 'true'      # for easy apply filter
JEDDAH_IS_EASY_APPLY = 'true'      # for easy apply filter
SPAIN_IS_EASY_APPLY = 'true'       # for easy apply filter
QATTA_IS_EASY_APPLY = 'true'       # for easy apply filter
DOHA_IS_EASY_APPLY = 'true'        # for easy apply filter
UNITED_ARAB_EMIRATES_IS_EASY_APPLY = 'true'  # for easy apply filter
ABU_DHABI_IS_EASY_APPLY = 'true'   # for easy apply filter
KUWAIT_IS_EASY_APPLY = 'true'      # for easy apply filter
IS_EASY_APPLY = 'true'             # for easy apply filter

MAX_PAGES = 5
PAGE_SIZE = 25
MAX_SEND_PER_RUN = 20

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars.")
