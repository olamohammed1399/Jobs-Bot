from urllib.parse import quote

from config import (
    ABU_DHABI_GEO_ID,
    ABU_DHABI_IS_EASY_APPLY,
    CAIRO_GEO_ID,
    CAIRO_IS_EASY_APPLY,
    DOHA_GEO_ID,
    DOHA_IS_EASY_APPLY,
    EGYPT_GEO_ID,
    EGYPT_IS_EASY_APPLY,
    JEDDAH_GEO_ID,
    JEDDAH_IS_EASY_APPLY,
    KUWAIT_GEO_ID,
    KUWAIT_IS_EASY_APPLY,
    QATTA_GEO_ID,
    QATTA_IS_EASY_APPLY,
    RIYADH_GEO_ID,
    RIYADH_IS_EASY_APPLY,
    SPAIN_GEO_ID,
    SPAIN_IS_EASY_APPLY,
    SUA_GEO_ID,
    SUA_IS_EASY_APPLY,
    TIME_PERIOD,
    UNITED_ARAB_EMIRATES_GEO_ID,
    UNITED_ARAB_EMIRATES_IS_EASY_APPLY,
)


WORK_TYPE_FILTERS = {
    "remote": "2",
    "all": "1%2C2%2C3",
}

LOCATIONS = [
    {
        "name": "Cairo",
        "geo_id": CAIRO_GEO_ID,
        "easy_apply": CAIRO_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": True,
    },
    {
        "name": "Egypt",
        "geo_id": EGYPT_GEO_ID,
        "easy_apply": EGYPT_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "Saudi Arabia",
        "geo_id": SUA_GEO_ID,
        "easy_apply": SUA_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "Riyadh",
        "geo_id": RIYADH_GEO_ID,
        "easy_apply": RIYADH_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "Jeddah",
        "geo_id": JEDDAH_GEO_ID,
        "easy_apply": JEDDAH_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "Spain",
        "geo_id": SPAIN_GEO_ID,
        "easy_apply": SPAIN_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "Qatar",
        "geo_id": QATTA_GEO_ID,
        "easy_apply": QATTA_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "Doha",
        "geo_id": DOHA_GEO_ID,
        "easy_apply": DOHA_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "United Arab Emirates",
        "geo_id": UNITED_ARAB_EMIRATES_GEO_ID,
        "easy_apply": UNITED_ARAB_EMIRATES_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "Abu Dhabi",
        "geo_id": ABU_DHABI_GEO_ID,
        "easy_apply": ABU_DHABI_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "Kuwait",
        "geo_id": KUWAIT_GEO_ID,
        "easy_apply": KUWAIT_IS_EASY_APPLY,
        "work_type": "all",
        "enabled": False,
    },
    {
        "name": "Global remote",
        "geo_id": None,
        "easy_apply": None,
        "work_type": "remote",
        "enabled": False,
    },
]

KEYWORD_GROUPS = [
    {
        "name": "frontend",
        "keywords": [
            "frontend",
            "frontend developer",
            "reactjs",
            "reactjs developer",
            "nextjs",
            "javascript developer",
        ],
        "enabled": True,
    },
    {
        "name": "backend",
        "keywords": [
            "backend",
            "backend developer",
            "nodejs",
            "nodejs developer",
            "expressjs",
            "api developer",
        ],
        "enabled": True,
    },
    {
        "name": "mern stack",
        "keywords": [
            "mern",
            "mern stack",
            "full stack developer",
            "mongodb nodejs",
        ],
        "enabled": True,
    },
]

TITLE_KEYWORDS = [
    "frontend",
    "front-end",
    "front end",
    "react",
    "reactjs",
    "next.js",
    "nextjs",
    "javascript",
    "typescript",
    "web",
    "backend",
    "back-end",
    "back end",
    "node",
    "nodejs",
    "express",
    "expressjs",
    "api",
    "rest api",
    "mern",
    "mern stack",
    "mongodb",
    "mongo",
    "fullstack",
    "full-stack",
    "full stack",
    "software",
    "software developer",
    "software engineer",
    "full stack developer",
    "full stack engineer",
    "full-stack developer",
    "full-stack engineer",
    "developer",
    "engineer",
    "developer engineer",
    "engineer developer",
    "web developer",
    "ui developer",
    "ux developer",
    "design",
]


def build_search_url(location, keyword):
    query_parts = [
        f"f_TPR=r{TIME_PERIOD}",
        f"keywords={quote(keyword)}",
    ]

    easy_apply = location.get("easy_apply")
    if easy_apply is not None:
        query_parts.insert(0, f"f_AL={easy_apply}")

    geo_id = location.get("geo_id")
    if geo_id:
        query_parts.insert(1 if easy_apply is not None else 0, f"geoId={geo_id}")

    work_type = location.get("work_type")
    if work_type:
        query_parts.append(f"f_WT={WORK_TYPE_FILTERS[work_type]}")

    query_parts.extend(
        [
            "origin=JOB_SEARCH_PAGE_JOB_FILTER",
            "refresh=true",
        ]
    )

    return "https://www.linkedin.com/jobs/search/?" + "&".join(query_parts)


def build_searches(locations=LOCATIONS, keyword_groups=KEYWORD_GROUPS):
    return [
        {
            "url": build_search_url(location, keyword),
            "location": location["name"],
            "keyword_group": group["name"],
            "keyword": keyword,
        }
        for location in locations
        if location["enabled"]
        for group in keyword_groups
        if group["enabled"]
        for keyword in group["keywords"]
    ]


def build_search_urls(locations=LOCATIONS, keyword_groups=KEYWORD_GROUPS):
    return [
        search["url"]
        for search in build_searches(locations, keyword_groups)
    ]


SEARCHES = build_searches()
SEARCH_URLS = [search["url"] for search in SEARCHES]
