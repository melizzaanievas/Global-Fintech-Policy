import os
import traceback
import urllib.parse

import feedparser
import requests

GOOD_MAIN_URL = (
    "https://raw.githubusercontent.com/melizzaanievas/Global-Fintech-Policy/"
    "70907d1d149d303fb19366e2302f467deaab5515/main.py"
)
FALLBACK_MAIN_URL = (
    "https://raw.githubusercontent.com/melizzaanievas/Global-Fintech-Policy/"
    "13397710d3d5beb7fec26beca2ba04ba5349764c/main.py"
)

DYNAMIC_NEWS_PATCH = '''
import feedparser
import urllib.parse

REGULATORY_RSS_FEEDS = {
    "Hong Kong (SFC / HKMA)": "https://www.hkma.gov.hk/eng/news-and-media/press-releases/rss/",
    "Hong Kong (SFC)": "https://www.hkma.gov.hk/eng/news-and-media/press-releases/rss/",
    "Singapore (MAS)": "https://www.mas.gov.sg/rss/feeds/press-releases.xml",
    "Japan (FSA)": "https://www.fsa.go.jp/en/news/rss.xml",
    "South Korea (FSC)": "https://www.fsc.go.kr/eng/rss.xml",
    "FCA (Cryptoasset Registration)": "https://www.fca.org.uk/news/rss.xml",
    "United Kingdom": "https://www.fca.org.uk/news/rss.xml",
    "Federal (SEC / CFTC)": "https://www.sec.gov/rss/pressreleases.xml",
    "United States": "https://www.sec.gov/rss/pressreleases.xml",
    "MiCA Regulation (EU-wide)": "https://www.esma.europa.eu/rss.xml",
    "European Union (MiCA)": "https://www.esma.europa.eu/rss.xml",
    "UAE (VARA / DIFC)": "https://www.vara.ae/en/rss.xml",
    "Bahrain": "https://www.cbb.gov.bh/rss.xml",
    "Nigeria": "https://sec.gov.ng/feed/",
    "Kenya": "https://www.centralbank.go.ke/feed/",
    "South Africa": "https://www.fsca.co.za/Pages/Feed.aspx",
    "Rwanda": "https://www.bnr.rw/feed/",
    "Brazil": "https://www.bcb.gov.br/api/feeds/noticias",
    "Mexico": "https://www.banxico.org.mx/rss.xml",
    "Colombia": "https://www.superfinanciera.gov.co/feed",
}

@st.cache_data(ttl=3600)
def get_latest_jurisdiction_news(jurisdiction_name, df_row):
    """Return a cached RSS update with Google News and row-data fallbacks."""
    jurisdiction = str(jurisdiction_name or "").strip()
    row = df_row if isinstance(df_row, dict) else {}
    search_url = (
        "https://news.google.com/rss/search?q="
        f"{urllib.parse.quote(jurisdiction + ' fintech regulation policy')}"
        "&hl=en-US&gl=US&ceid=US:en"
    )
    feed_urls = []
    direct_url = REGULATORY_RSS_FEEDS.get(jurisdiction)
    if direct_url:
        feed_urls.append(direct_url)
    feed_urls.append(search_url)

    for rss_url in feed_urls:
        try:
            parsed = feedparser.parse(rss_url)
            for entry in getattr(parsed, "entries", []) or []:
                headline = str(entry.get("title") or "").strip()
                link = str(entry.get("link") or "").strip()
                if headline and link:
                    return headline, link
        except Exception:
            continue

    fallback_headline = (
        row.get("Latest Update Headline")
        or row.get("latest_update_headline")
        or row.get("Core Action Item / Shift")
        or row.get("core_action_item_shift")
        or row.get("regulatory_shift")
        or "Latest policy shift pending review"
    )
    fallback_url = (
        row.get("Latest Update URL")
        or row.get("latest_update_url")
        or row.get("Source URL")
        or row.get("source_url")
        or "#"
    )
    return str(fallback_headline), str(fallback_url)
'''


def patch_app_source(source):
    """Inject the dynamic news helper and replace the legacy render call."""
    source = source.replace(
        "from urllib.parse import quote",
        "from urllib.parse import quote\nimport feedparser\nimport urllib.parse",
        1,
    )

    marker = "# One current, jurisdiction-matched update per featured jurisdiction."
    if marker in source and "def get_latest_jurisdiction_news" not in source:
        source = source.replace(marker, DYNAMIC_NEWS_PATCH + "\n" + marker, 1)

    legacy = '''            regional_news_title, regional_news_url = jurisdiction_update(jur["name"])
            update_link = (
                f"[{regional_news_title}]({regional_news_url})"
                if regional_news_url
                else regional_news_title
            )
            st.markdown(
                f"- **Latest regional fintech update — reviewed {regional_review_date}:** "
                f"{update_link}"
            )'''
    replacement = '''            headline, link = get_latest_jurisdiction_news(jur["name"], jur)
            st.markdown(
                f"- **Latest regional fintech update — reviewed {regional_review_date}:** "
                f"[{headline}]({link})"
            )'''
    source = source.replace(legacy, replacement, 1)
    return source


def load_known_good_main():
    """Load and patch the last known-good app source from repository history."""
    urls = [GOOD_MAIN_URL, FALLBACK_MAIN_URL]
    last_error = None

    for url in urls:
        try:
            response = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            source = response.text
            if not source.strip():
                raise ValueError("Downloaded source is empty")
            source = patch_app_source(source)
            namespace = {"__name__": "__main__", "__file__": __file__}
            exec(compile(source, str(__file__), "exec"), namespace, namespace)
            return
        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        "Failed to load the last known-good main.py from git history. "
        f"Tried: {urls}. Last error: {last_error}"
    )


if __name__ == "__main__":
    try:
        load_known_good_main()
    except Exception:
        traceback.print_exc()
        print(
            "\nStreamlit app startup failed because the known-good app source could not "
            "be fetched or patched. Restore the repository source manually and redeploy."
        )
        raise
