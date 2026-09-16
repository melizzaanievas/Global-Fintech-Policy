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


DELTA_BADGE_STYLE_PATCH = """
.success-pill { background:#DCFCE7; color:#16A34A; padding:3px 9px; border-radius:999px; font-size:0.8rem; font-weight:700; display:inline-block; }
.negative-pill { background:#FEE2E2; color:#B91C1C; padding:3px 9px; border-radius:999px; font-size:0.8rem; font-weight:700; display:inline-block; }
"""


DELTA_BADGE_HELPER_PATCH = '''
def delta_badge(value, suffix="pts", show_plus=True, decimals=1):
    value = float(value)
    sign = "+" if show_plus and value >= 0 else ""
    formatted = f"{sign}{value:.{decimals}f}"
    if suffix:
        formatted = f"{formatted} {suffix}"
    badge_class = "success-pill" if value >= 0 else "negative-pill"
    return f"<span class='{badge_class}'>{formatted}</span>"
'''


def patch_app_source(source):
    """Inject runtime source patches into the known-good dashboard source."""
    if "import feedparser" not in source:
        source = source.replace(
            "from urllib.parse import quote",
            "from urllib.parse import quote\nimport feedparser\nimport urllib.parse",
            1,
        )

    if ".success-pill" not in source:
        source = source.replace(
            '.delta-flat { color:#94A3B8; font-size:0.8rem; font-weight:600; }',
            '.delta-flat { color:#94A3B8; font-size:0.8rem; font-weight:600; }\n'
            + DELTA_BADGE_STYLE_PATCH.strip(),
            1,
        )
    if ".success-pill" not in source:
        raise RuntimeError("Could not locate the CSS block to inject delta badge styles")

    marker = "# One current, jurisdiction-matched update per featured jurisdiction."
    if marker in source and "def get_latest_jurisdiction_news" not in source:
        source = source.replace(marker, DYNAMIC_NEWS_PATCH + "\n" + marker, 1)

    helper_marker = "# ── On-chain metric definitions ───────────────────────────────────────────────"
    if helper_marker in source and "def delta_badge(" not in source:
        source = source.replace(
            helper_marker,
            DELTA_BADGE_HELPER_PATCH + "\n" + helper_marker,
            1,
        )
    if "def delta_badge(" not in source:
        raise RuntimeError("Could not locate the helper insertion point for delta badges")

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

    legacy_delta_render = '''                delta = float(row.improvement_delta)
                delta_color = "#6EE7B7" if delta > 3 else ("#FCD34D" if delta > 1 else "#FCA5A5")
                st.markdown(
                    f"<div style='background:#1A2535;border:1px solid #2D4A7A;border-radius:8px;padding:12px;text-align:center'>"
                    f"<div style='color:#94A3B8;font-size:0.75rem;margin-bottom:4px'>2016 → 2026 Composite</div>"
                    f"<div style='font-size:1.1rem;font-weight:700;color:#94A3B8'>{float(row.composite_2016):.1f}"
                    f" → <span style='color:#F1F5F9'>{composite:.1f}</span></div>"
                    f"<div style='color:{delta_color};font-size:1rem;font-weight:800;margin-top:4px'>"
                    f"+{delta:.1f} pts over 10 years</div>"
                    f"<div style='color:#64748B;font-size:0.75rem;margin-top:2px'>{row.improvement_trend}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )'''
    dynamic_delta_render = '''                delta = float(row.improvement_delta)
                delta_badge_html = delta_badge(delta)
                st.markdown(
                    f"<div style='background:#1A2535;border:1px solid #2D4A7A;border-radius:8px;padding:12px;text-align:center'>"
                    f"<div style='color:#94A3B8;font-size:0.75rem;margin-bottom:4px'>2016 → 2026 Composite</div>"
                    f"<div style='font-size:1.1rem;font-weight:700;color:#94A3B8'>{float(row.composite_2016):.1f}"
                    f" → <span style='color:#F1F5F9'>{composite:.1f}</span></div>"
                    f"<div style='margin-top:8px'>{delta_badge_html} <span style='color:#64748B;font-size:0.78rem;font-weight:600;margin-left:6px'>over 10 years</span></div>"
                    f"<div style='color:#64748B;font-size:0.75rem;margin-top:2px'>{row.improvement_trend}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )'''
    if legacy_delta_render in source:
        source = source.replace(legacy_delta_render, dynamic_delta_render, 1)
    elif "delta_badge_html = delta_badge(delta)" not in source:
        raise RuntimeError("Could not locate the improvement delta render block to replace")

    return source


def load_known_good_main():
    """Load the known-good dashboard source and apply the dynamic RSS refactor."""
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
