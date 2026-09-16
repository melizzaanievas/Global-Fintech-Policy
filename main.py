import importlib.util
import os
from pathlib import Path
import sys
import traceback
import urllib.parse

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
import urllib.parse

try:
    import feedparser
except ImportError:
    feedparser = None

REGULATORY_RSS_FEEDS = {
    "Hong Kong": "https://www.hkma.gov.hk/eng/news-and-media/press-releases/rss/",
    "Hong Kong (SFC / HKMA)": "https://www.hkma.gov.hk/eng/news-and-media/press-releases/rss/",
    "Hong Kong (SFC)": "https://www.hkma.gov.hk/eng/news-and-media/press-releases/rss/",
    "Singapore": "https://www.mas.gov.sg/rss/feeds/press-releases.xml",
    "Singapore (MAS)": "https://www.mas.gov.sg/rss/feeds/press-releases.xml",
    "United Kingdom": "https://www.fca.org.uk/news/rss.xml",
    "UK FCA": "https://www.fca.org.uk/news/rss.xml",
    "FCA": "https://www.fca.org.uk/news/rss.xml",
    "United States": "https://www.sec.gov/rss/pressreleases.xml",
    "US SEC": "https://www.sec.gov/rss/pressreleases.xml",
    "SEC": "https://www.sec.gov/rss/pressreleases.xml",
    "European Union": "https://www.esma.europa.eu/rss.xml",
    "EU MiCA": "https://www.esma.europa.eu/rss.xml",
    "MiCA Regulation (EU-wide)": "https://www.esma.europa.eu/rss.xml",
    "Japan": "https://www.fsa.go.jp/en/news/rss.xml",
    "Japan (FSA)": "https://www.fsa.go.jp/en/news/rss.xml",
    "South Korea": "https://www.fsc.go.kr/eng/rss.xml",
    "South Korea (FSC)": "https://www.fsc.go.kr/eng/rss.xml",
    "UAE": "https://www.vara.ae/en/rss.xml",
    "UAE (VARA / DIFC)": "https://www.vara.ae/en/rss.xml",
    "Bahrain": "https://www.cbb.gov.bh/rss.xml",
    "Nigeria": "https://sec.gov.ng/feed/",
    "Kenya": "https://www.centralbank.go.ke/feed/",
    "South Africa": "https://www.fsca.co.za/Pages/Feed.aspx",
    "Rwanda": "https://www.bnr.rw/feed/",
    "Brazil": "https://www.bcb.gov.br/api/feeds/noticias",
    "Mexico": "https://www.banxico.org.mx/rss.xml",
    "Colombia": "https://www.superfinanciera.gov.co/feed",
    "Australia": "https://asic.gov.au/about-asic/news-centre/rss/",
    "ASIC": "https://asic.gov.au/about-asic/news-centre/rss/",
}


def _news_fallback(row):
    """Return the row-provided update safely when external feeds are unavailable."""
    headline = (
        row.get("Latest Update Headline")
        or row.get("Core Action Item / Shift")
        or row.get("regulatory_shift")
        or row.get("framework")
        or "Latest policy shift pending review"
    )
    link = (
        row.get("Latest Update URL")
        or row.get("Source URL")
        or row.get("source_url")
        or "#"
    )
    return str(headline), str(link)


@st.cache_data(ttl=3600)
def get_latest_jurisdiction_news(jurisdiction_name, df_row):
    """Return the latest jurisdiction-specific regulatory update or safe row fallback."""
    jurisdiction = str(jurisdiction_name or "").strip()
    row = df_row if isinstance(df_row, dict) else {}

    rss_url = REGULATORY_RSS_FEEDS.get(jurisdiction)
    if not rss_url:
        search_query = f"{jurisdiction} fintech regulation policy"
        rss_url = (
            "https://news.google.com/rss/search?q="
            f"{urllib.parse.quote(search_query)}&hl=en-US&gl=US&ceid=US:en"
        )

    if feedparser is None:
        return _news_fallback(row)

    try:
        response = requests.get(
            rss_url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        entries = getattr(parsed, "entries", []) or []
        if entries:
            first = entries[0]
            title = str(first.get("title") or "").strip()
            link = str(first.get("link") or "").strip()
            if title and link:
                return title, link
    except Exception:
        pass

    return _news_fallback(row)
'''


def patch_app_source(source):
    """Inject dynamic jurisdiction news lookup into the known-good dashboard source."""
    if "import feedparser" not in source:
        source = source.replace(
            "from urllib.parse import quote",
            "from urllib.parse import quote\nimport urllib.parse\n\ntry:\n    import feedparser\nexcept ImportError:\n    feedparser = None",
            1,
        )

    marker = "# One current, jurisdiction-matched update per featured jurisdiction."
    if marker in source and "def get_latest_jurisdiction_news" not in source:
        source = source.replace(marker, DYNAMIC_NEWS_PATCH + "\n" + marker, 1)

    legacy_render = '''            regional_news_title, regional_news_url = jurisdiction_update(jur["name"])
            update_link = (
                f"[{regional_news_title}]({regional_news_url})"
                if regional_news_url
                else regional_news_title
            )
            st.markdown(
                f"- **Latest regional fintech update — reviewed {regional_review_date}:** "
                f"{update_link}"
            )'''
    dynamic_render = '''            headline, link = get_latest_jurisdiction_news(jur["name"], jur)
            st.markdown(
                f"- **Latest regional fintech update — reviewed {regional_review_date}:** "
                f"[{headline}]({link})"
            )'''
    if legacy_render in source:
        source = source.replace(legacy_render, dynamic_render, 1)
    elif "get_latest_jurisdiction_news(jur[\"name\"], jur)" not in source:
        raise RuntimeError("Could not locate the regional update render block to replace")

    return source


def ensure_cgi_compat():
    """Preload a local `cgi` compatibility module when stdlib `cgi` is unavailable."""
    try:
        import cgi  # noqa: F401
        return
    except ImportError:
        pass

    shim_path = Path(__file__).with_name("cgi.py")
    if not shim_path.exists():
        return

    spec = importlib.util.spec_from_file_location("cgi", shim_path)
    if spec is None or spec.loader is None:
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules["cgi"] = module
    spec.loader.exec_module(module)


def load_known_good_main():
    """Load the known-good dashboard source and apply the dynamic RSS refactor."""
    ensure_cgi_compat()
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
        "Failed to load the known-good main.py from git history. "
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
