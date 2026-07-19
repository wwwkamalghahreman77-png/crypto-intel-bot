"""
analysis/fundamental.py

تحلیل فاندامنتال پروژه با داده‌های CoinGecko.
"""

import requests


COINGECKO_BASE = (
    "https://api.coingecko.com/api/v3"
)


NARRATIVE_KEYWORDS = {

    "AI": [
        "ai",
        "artificial intelligence",
        "machine learning",
        "agent"
    ],

    "RWA": [
        "real world asset",
        "rwa",
        "tokenized",
        "treasury"
    ],

    "DePIN": [
        "depin",
        "decentralized physical infrastructure",
        "wireless",
        "storage network"
    ],

    "Layer2": [
        "layer 2",
        "layer-2",
        "rollup",
        "zk-rollup",
        "optimistic rollup",
        "scaling"
    ],

    "Gaming": [
        "gaming",
        "game",
        "gamefi",
        "metaverse",
        "play to earn",
        "p2e"
    ],

    "DeFi": [
        "defi",
        "decentralized finance",
        "lending",
        "dex",
        "yield"
    ],

    "Infrastructure": [
        "infrastructure",
        "oracle",
        "middleware",
        "node",
        "protocol"
    ],
}


def fetch_coin_info(
    coin_id: str
) -> dict:

    url = (
        f"{COINGECKO_BASE}"
        f"/coins/{coin_id}"
    )

    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "true",
        "developer_data": "true",
    }

    try:

        resp = requests.get(
            url,
            params=params,
            timeout=10
        )

        resp.raise_for_status()

        return resp.json()

    except requests.RequestException as e:

        print(
            f"[Fundamental] "
            f"خطا در دریافت اطلاعات "
            f"{coin_id}: {e}"
        )

        return {}

    except Exception as e:

        print(
            f"[Fundamental] "
            f"خطای پردازش اطلاعات "
            f"{coin_id}: {e}"
        )

        return {}


def detect_narrative(
    description: str,
    categories: list
) -> str:

    text = (
        description or ""
    ).lower()

    text += " "

    text += " ".join(
        categories or []
    ).lower()

    for narrative, keywords in (
        NARRATIVE_KEYWORDS.items()
    ):

        if any(
            keyword in text
            for keyword in keywords
        ):

            return narrative

    return "Uncategorized"


def analyze_fundamental(
    coin_id: str
) -> dict:

    info = fetch_coin_info(
        coin_id
    )

    if not info:

        return {
            "available": False,
            "score": 0,
            "reasons": [],
            "risks": []
        }

    description = (
        info
        .get(
            "description",
            {}
        )
        .get(
            "en",
            ""
        )
    )

    categories = (
        info.get(
            "categories"
        )
        or []
    )

    narrative = detect_narrative(
        description,
        categories
    )

    dev_data = (
        info.get(
            "developer_data"
        )
        or {}
    )

    community_data = (
        info.get(
            "community_data"
        )
        or {}
    )

    links = (
        info.get(
            "links"
        )
        or {}
    )

    github_stars = (
        dev_data.get(
            "stars",
            0
        )
        or 0
    )

    commit_data = (
        dev_data.get(
            "code_additions_deletions_4_weeks"
        )
        or {}
    )

    github_commits_4w = sum(
        abs(
            value or 0
        )
        for value in commit_data.values()
        if isinstance(
            value,
            (int, float)
        )
    )

    twitter_followers = (
        community_data.get(
            "twitter_followers",
            0
        )
        or 0
    )

    telegram_users = (
        community_data.get(
            "telegram_channel_user_count",
            0
        )
        or 0
    )

    has_whitepaper = bool(
        links.get(
            "whitepaper"
        )
    )

    github_repos = (
        links.get(
            "repos_url"
        )
        or {}
    )

    has_github = bool(
        github_repos.get(
            "github"
        )
    )

    score = 0

    reasons = []

    risks = []

    if has_github:

        score += 20

        reasons.append(
            "کد منبع باز روی گیت‌هاب موجود است ✅"
        )

    else:

        risks.append(
            "مخزن گیت‌هاب یافت نشد ⚠️"
        )

    if github_stars > 100:

        score += 15

        reasons.append(
            f"پروژه {github_stars:,} "
            f"ستاره در گیت‌هاب دارد ✅"
        )

    if github_commits_4w > 0:

        score += 10

        reasons.append(
            "فعالیت توسعه در ۴ هفته اخیر وجود دارد ✅"
        )

    else:

        risks.append(
            "فعالیت توسعه اخیر قابل مشاهده نیست ⚠️"
        )

    if has_whitepaper:

        score += 15

        reasons.append(
            "وایت‌پیپر منتشر شده است ✅"
        )

    else:

        risks.append(
            "وایت‌پیپر یافت نشد ⚠️"
        )

    if twitter_followers > 10000:

        score += 15

        reasons.append(
            f"جامعه توییتر بزرگ "
            f"({twitter_followers:,} فالوور) ✅"
        )

    if telegram_users > 5000:

        score += 15

        reasons.append(
            f"جامعه تلگرام فعال "
            f"({telegram_users:,} عضو) ✅"
        )

    if narrative != "Uncategorized":

        score += 20

        reasons.append(
            f"حوزه پروژه مشخص و ترند است: "
            f"{narrative} ✅"
        )

    else:

        risks.append(
            "حوزه (Narrative) پروژه مشخص نیست ⚠️"
        )

    return {

        "available": True,

        "narrative": narrative,

        "github_stars": github_stars,

        "github_commits_4w":
            github_commits_4w,

        "twitter_followers":
            twitter_followers,

        "telegram_users":
            telegram_users,

        "has_whitepaper":
            has_whitepaper,

        "has_github":
            has_github,

        "investors":
            "نامشخص",

        "unlock_schedule":
            "نامشخص",

        "score": round(
            min(
                100,
                score
            ),
            1
        ),

        "reasons": reasons,

        "risks": risks,
    }
