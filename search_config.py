from pickle import TRUE
from config import (
    EGYPT_IS_EASY_APPLY,
    CAIRO_IS_EASY_APPLY,
    EGYPT_GEO_ID,
    CAIRO_GEO_ID,
    TIME_PERIOD,
    SUA_IS_EASY_APPLY,
    SUA_GEO_ID,
    RIYADH_IS_EASY_APPLY,
    RIYADH_GEO_ID,
    JEDDAH_IS_EASY_APPLY,
    JEDDAH_GEO_ID,
    SPAIN_IS_EASY_APPLY,
    SPAIN_GEO_ID,
    QATTA_IS_EASY_APPLY,
    QATTA_GEO_ID,
    DOHA_IS_EASY_APPLY,
    DOHA_GEO_ID,
    UNITED_ARAB_EMIRATES_IS_EASY_APPLY,
    UNITED_ARAB_EMIRATES_GEO_ID,
    ABU_DHABI_IS_EASY_APPLY,
    ABU_DHABI_GEO_ID,
    KUWAIT_IS_EASY_APPLY,
    KUWAIT_GEO_ID,
)

FRONTEND_KEYWORDS = [
    "frontend",
    "frontend%20developer",
    "reactjs",
    "reactjs%20developer",
    "nextjs",
    "javascript%20developer",
]

BACKEND_KEYWORDS = [
    "backend",
    "backend%20developer",
    "nodejs",
    "nodejs%20developer",
    "expressjs",
    "api%20developer",
]

MERN_STACK_KEYWORDS = [
    "mern",
    "mern%20stack",
    "full%20stack%20developer",
    "mongodb%20nodejs",
]


def build_location_search_urls(is_easy_apply, geo_id, keywords):
    isRemote = 2
    isAll = "1%2C2%2C3"
    remote = False
    remoteValue = isRemote if remote else isAll
    return [
        (
            f"https://www.linkedin.com/jobs/search/?f_AL={is_easy_apply}"
            f"&geoId={geo_id}&f_TPR=r{TIME_PERIOD}&keywords={keyword}"
            f"&f_WT={remoteValue}"
            "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"
        )
        for keyword in keywords
    ]


EGYPT_FRONTEND_SEARCH_URLS = build_location_search_urls(
    EGYPT_IS_EASY_APPLY,
    CAIRO_GEO_ID,
    FRONTEND_KEYWORDS,
)

EGYPT_BACKEND_SEARCH_URLS = build_location_search_urls(
    EGYPT_IS_EASY_APPLY,
    CAIRO_GEO_ID,
    BACKEND_KEYWORDS,
)

EGYPT_MERN_STACK_SEARCH_URLS = build_location_search_urls(
    EGYPT_IS_EASY_APPLY,
    CAIRO_GEO_ID,
    MERN_STACK_KEYWORDS,
)

SAUDI_ARABIA_FRONTEND_SEARCH_URLS = build_location_search_urls(
    SUA_IS_EASY_APPLY,
    SUA_GEO_ID,
    FRONTEND_KEYWORDS,
)

SAUDI_ARABIA_BACKEND_SEARCH_URLS = build_location_search_urls(
    SUA_IS_EASY_APPLY,
    SUA_GEO_ID,
    BACKEND_KEYWORDS,
)

SAUDI_ARABIA_MERN_STACK_SEARCH_URLS = build_location_search_urls(
    SUA_IS_EASY_APPLY,
    SUA_GEO_ID,
    MERN_STACK_KEYWORDS,
)

JEDDAH_FRONTEND_SEARCH_URLS = build_location_search_urls(
    JEDDAH_IS_EASY_APPLY,
    JEDDAH_GEO_ID,
    FRONTEND_KEYWORDS,
)

JEDDAH_BACKEND_SEARCH_URLS = build_location_search_urls(
    JEDDAH_IS_EASY_APPLY,
    JEDDAH_GEO_ID,
    BACKEND_KEYWORDS,
)

JEDDAH_MERN_STACK_SEARCH_URLS = build_location_search_urls(
    JEDDAH_IS_EASY_APPLY,
    JEDDAH_GEO_ID,
    MERN_STACK_KEYWORDS,
)

SPAIN_FRONTEND_SEARCH_URLS = build_location_search_urls(
    SPAIN_IS_EASY_APPLY,
    SPAIN_GEO_ID,
    FRONTEND_KEYWORDS,
)

SPAIN_BACKEND_SEARCH_URLS = build_location_search_urls(
    SPAIN_IS_EASY_APPLY,
    SPAIN_GEO_ID,
    BACKEND_KEYWORDS,
)

SPAIN_MERN_STACK_SEARCH_URLS = build_location_search_urls(
    SPAIN_IS_EASY_APPLY,
    SPAIN_GEO_ID,
    MERN_STACK_KEYWORDS,
)

QATTA_FRONTEND_SEARCH_URLS = build_location_search_urls(
    QATTA_IS_EASY_APPLY,
    QATTA_GEO_ID,
    FRONTEND_KEYWORDS,
)

QATTA_BACKEND_SEARCH_URLS = build_location_search_urls(
    QATTA_IS_EASY_APPLY,
    QATTA_GEO_ID,
    BACKEND_KEYWORDS,
)

QATTA_MERN_STACK_SEARCH_URLS = build_location_search_urls(
    QATTA_IS_EASY_APPLY,
    QATTA_GEO_ID,
    MERN_STACK_KEYWORDS,
)

DOHA_FRONTEND_SEARCH_URLS = build_location_search_urls(
    DOHA_IS_EASY_APPLY,
    DOHA_GEO_ID,
    FRONTEND_KEYWORDS,
)

DOHA_BACKEND_SEARCH_URLS = build_location_search_urls(
    DOHA_IS_EASY_APPLY,
    DOHA_GEO_ID,
    BACKEND_KEYWORDS,
)

DOHA_MERN_STACK_SEARCH_URLS = build_location_search_urls(
    DOHA_IS_EASY_APPLY,
    DOHA_GEO_ID,
    MERN_STACK_KEYWORDS,
)

UNITED_ARAB_EMIRATES_FRONTEND_SEARCH_URLS = build_location_search_urls(
    UNITED_ARAB_EMIRATES_IS_EASY_APPLY,
    UNITED_ARAB_EMIRATES_GEO_ID,
    FRONTEND_KEYWORDS,
)

UNITED_ARAB_EMIRATES_BACKEND_SEARCH_URLS = build_location_search_urls(
    UNITED_ARAB_EMIRATES_IS_EASY_APPLY,
    UNITED_ARAB_EMIRATES_GEO_ID,
    BACKEND_KEYWORDS,
)

UNITED_ARAB_EMIRATES_MERN_STACK_SEARCH_URLS = build_location_search_urls(
    UNITED_ARAB_EMIRATES_IS_EASY_APPLY,
    UNITED_ARAB_EMIRATES_GEO_ID,
    MERN_STACK_KEYWORDS,
)

ABU_DHABI_FRONTEND_SEARCH_URLS = build_location_search_urls(
    ABU_DHABI_IS_EASY_APPLY,
    ABU_DHABI_GEO_ID,
    FRONTEND_KEYWORDS,
)

ABU_DHABI_BACKEND_SEARCH_URLS = build_location_search_urls(
    ABU_DHABI_IS_EASY_APPLY,
    ABU_DHABI_GEO_ID,
    BACKEND_KEYWORDS,
)

ABU_DHABI_MERN_STACK_SEARCH_URLS = build_location_search_urls(
    ABU_DHABI_IS_EASY_APPLY,
    ABU_DHABI_GEO_ID,
    MERN_STACK_KEYWORDS,
)

KUWAIT_FRONTEND_SEARCH_URLS = build_location_search_urls(
    KUWAIT_IS_EASY_APPLY,
    KUWAIT_GEO_ID,
    FRONTEND_KEYWORDS,
)

KUWAIT_BACKEND_SEARCH_URLS = build_location_search_urls(
    KUWAIT_IS_EASY_APPLY,
    KUWAIT_GEO_ID,
    BACKEND_KEYWORDS,
)

KUWAIT_MERN_STACK_SEARCH_URLS = build_location_search_urls(
    KUWAIT_IS_EASY_APPLY,
    KUWAIT_GEO_ID,
    MERN_STACK_KEYWORDS,
)

FRONTEND_SEARCH_URLS = [
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=frontend"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
    
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=frontend%20developer"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
    
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=reactjs"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
    
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=reactjs%20developer"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
]

BACKEND_SEARCH_URLS = [
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=backend"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
    
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=backend%20developer"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
    
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=nodejs"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
    
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=nodejs%20developer"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
]

MERN_STACK_SEARCH_URLS = [
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=mern"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
    
    (f"https://www.linkedin.com/jobs/search/?f_TPR=r{TIME_PERIOD}&f_WT=2&keywords=mern%20stack"
    "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"),
]

# Add more search URLs here

SEARCH_URLS = [
    *EGYPT_FRONTEND_SEARCH_URLS,
    *EGYPT_BACKEND_SEARCH_URLS,
    *EGYPT_MERN_STACK_SEARCH_URLS,

    # *SAUDI_ARABIA_FRONTEND_SEARCH_URLS,
    # *SAUDI_ARABIA_BACKEND_SEARCH_URLS,
    # *SAUDI_ARABIA_MERN_STACK_SEARCH_URLS,

    # *JEDDAH_FRONTEND_SEARCH_URLS,
    # *JEDDAH_BACKEND_SEARCH_URLS,
    # *JEDDAH_MERN_STACK_SEARCH_URLS,

    # *SPAIN_FRONTEND_SEARCH_URLS,
    # *SPAIN_BACKEND_SEARCH_URLS,
    # *SPAIN_MERN_STACK_SEARCH_URLS,

    # *QATTA_FRONTEND_SEARCH_URLS,
    # *QATTA_BACKEND_SEARCH_URLS,
    # *QATTA_MERN_STACK_SEARCH_URLS,

    # *DOHA_FRONTEND_SEARCH_URLS,
    # *DOHA_BACKEND_SEARCH_URLS,
    # *DOHA_MERN_STACK_SEARCH_URLS,

    # *UNITED_ARAB_EMIRATES_FRONTEND_SEARCH_URLS,
    # *UNITED_ARAB_EMIRATES_BACKEND_SEARCH_URLS,
    # *UNITED_ARAB_EMIRATES_MERN_STACK_SEARCH_URLS,

    # *ABU_DHABI_FRONTEND_SEARCH_URLS,
    # *ABU_DHABI_BACKEND_SEARCH_URLS,
    # *ABU_DHABI_MERN_STACK_SEARCH_URLS,

    # *KUWAIT_FRONTEND_SEARCH_URLS,
    # *KUWAIT_BACKEND_SEARCH_URLS,
    # *KUWAIT_MERN_STACK_SEARCH_URLS,

    # *FRONTEND_SEARCH_URLS,
    # *BACKEND_SEARCH_URLS,
    # *MERN_STACK_SEARCH_URLS,
]

TITLE_KEYWORDS = [
    "frontend", "front-end", "front end", "react", "reactjs", "next.js", "nextjs",
    "javascript", "typescript", "web", "backend", "back-end", "back end", "node",
    "nodejs", "express", "expressjs", "api", "rest api", "mern", "mern stack",
    "mongodb", "mongo",
    "Fullstack", "fullstack", "full-stack", "full stack", "software", "software developer", "software engineer",
    "full stack developer", "full stack engineer", "full-stack developer", "full-stack engineer",
    "developer", "engineer", "developer engineer", "engineer developer",
    "frontend", "front end", "front-end", "web developer", "ui developer", "ux developer", "design"
]