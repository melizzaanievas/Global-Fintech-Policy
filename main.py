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

UPDATED_EXECUTIVE_CSS = """.executive-banner { width:100%; box-sizing:border-box; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:16px; margin:0 0 16px 0; box-shadow:0 10px 24px rgba(15,23,42,0.06); }
.executive-kicker { color:#6366F1; font-size:0.68rem; letter-spacing:0.1em; text-transform:uppercase; font-weight:800; margin-bottom:8px; }
.executive-credentials { color:#475569; font-size:0.88rem; line-height:1.45; font-weight:500; }
.executive-credentials .name { display:block; color:#0F172A; font-size:1.1rem; font-weight:800; margin-bottom:4px; }
.executive-credentials .role { color:#475569; }
.executive-org { color:#475569; font-size:0.88rem; font-weight:600; margin-top:6px; }
.executive-links { display:flex; flex-direction:column; align-items:stretch; gap:10px; margin-top:14px; }
.executive-cta { width:100%; min-height:44px; display:flex; align-items:center; justify-content:center; text-align:center; box-sizing:border-box; background:linear-gradient(135deg, #6366F1 0%, #4F46E5 100%); color:#FFFFFF !important; border:1px solid #6366F1; border-radius:10px; padding:10px 14px; font-size:0.84rem; font-weight:700; text-decoration:none !important; letter-spacing:0.01em; }
.executive-cta.substack { background:#FFFFFF; color:#0F172A !important; border-color:#E2E8F0; }
.executive-cta:hover { background:linear-gradient(135deg, #5B5FEF 0%, #4338CA 100%); color:#FFFFFF !important; }
.executive-cta.substack:hover { background:#F8FAFC; color:#0F172A !important; }"""
UPDATED_EXECUTIVE_MOBILE_CSS = """@media (max-width: 600px) {
    .executive-banner { padding:14px; }
    .executive-credentials { font-size:0.84rem; }
    .executive-credentials .name { font-size:1rem; }
    .executive-org { font-size:0.82rem; }
    .executive-cta { width:100%; text-align:center; }
}"""
UPDATED_MAIN_HEADER = '''# ── Header ────────────────────────────────────────────────────────────────────
st.title("Web3 Global Regulatory & Macroeconomic Intelligence Matrix")
'''
UPDATED_SIDEBAR_EXECUTIVE_BLOCK = """st.sidebar.markdown(\"\"\"
<div class="executive-banner">
  <div class="executive-kicker">Executive Leadership</div>
  <div class="executive-credentials">
    <span class="name">Melizza Anievas, LLB</span>
    <span class="role">Global FinTech Policy &amp; Geopolitical Macro Advisor | Co-Founder, Women in Web3 Hong Kong</span>
  </div>
  <div class="executive-links">
    <a class="executive-cta" href="https://www.linkedin.com/in/melizza-anievas/" target="_blank" rel="noopener noreferrer" aria-label="Book Strategic Consulting">📅 Book Strategic Consulting</a>
    <a class="executive-cta substack" href="https://ruleofinnovation.substack.com/" target="_blank" rel="noopener noreferrer" aria-label="Substack: Rule of Innovation">📩 Substack: Rule of Innovation</a>
  </div>
</div>
\"\"\", unsafe_allow_html=True)"""


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

    legacy_executive_css = """.executive-banner { width:100%; box-sizing:border-box; background:#0B1B35; border:1px solid #D4AF37; border-left:6px solid #D4AF37; border-radius:4px; padding:20px 22px 22px 22px; margin:0 0 8px 0; box-shadow:0 8px 20px rgba(7,20,42,0.18); }
.executive-banner .executive-title { color:#F8FAFC !important; font-size:clamp(1.65rem,3vw,2.55rem); line-height:1.12; font-weight:850; letter-spacing:-0.02em; margin:0 0 18px 0; }
.executive-kicker { color:#E7C75F; font-size:0.7rem; letter-spacing:0.13em; text-transform:uppercase; font-weight:800; margin-bottom:8px; }
.executive-credentials { color:#F8FAFC; font-size:1.08rem; line-height:1.45; font-weight:800; }
.executive-credentials .name { color:#FFFFFF; }
.executive-credentials .role { color:#E7C75F; }
.executive-org { color:#CBD5E1; font-size:0.9rem; font-weight:600; margin-top:5px; }
.executive-links { display:flex; justify-content:center; align-items:stretch; gap:12px; margin-top:16px; }
.executive-cta { flex:1 1 0; min-height:44px; display:flex; align-items:center; justify-content:center; text-align:center; box-sizing:border-box; background:#D4AF37; color:#07142A !important; border:1px solid #F3D675; border-radius:3px; padding:9px 14px; font-size:0.82rem; font-weight:800; text-decoration:none !important; letter-spacing:0.01em; }
.executive-cta.substack { background:#F8FAFC; color:#0B1B35 !important; border-color:#CBD5E1; }
.executive-cta:hover { background:#F3D675; color:#07142A !important; }
.executive-cta.substack:hover { background:#FFFFFF; }"""
    if legacy_executive_css in source:
        source = source.replace(legacy_executive_css, UPDATED_EXECUTIVE_CSS, 1)
    elif UPDATED_EXECUTIVE_CSS not in source:
        raise RuntimeError("Could not locate the executive header styles to replace")

    legacy_mobile_css = """@media (max-width: 600px) {
    .executive-banner { padding:17px 17px 19px 17px; }
    .executive-banner .executive-title { font-size:1.58rem; margin-bottom:16px; }
    .executive-credentials { font-size:0.98rem; }
    .executive-org { font-size:0.84rem; }
    .executive-links { flex-direction:column; gap:10px; }
    .executive-cta { width:100%; text-align:center; }
}"""
    if legacy_mobile_css in source:
        source = source.replace(legacy_mobile_css, UPDATED_EXECUTIVE_MOBILE_CSS, 1)
    elif UPDATED_EXECUTIVE_MOBILE_CSS not in source:
        raise RuntimeError("Could not locate the executive mobile styles to replace")

    legacy_header = '''# ── Header ────────────────────────────────────────────────────────────────────
_, col_title = st.columns([1, 6])
with col_title:
    st.markdown("""
<div class="executive-banner">
  <h1 class="executive-title">Web3 Global Regulatory &amp; Macroeconomic Intelligence Matrix</h1>
  <div class="executive-kicker">Executive Research Leadership</div>
  <div class="executive-credentials">
    PRINCIPAL RESEARCHER:
    <span class="name">Melizza Anievas, LLB</span>
    <span class="role">| Global FinTech Regulation &amp; Geopolitical Macro Strategy Advisor</span>
  </div>
  <div class="executive-org">Co-Founder, Women in Web3 Hong Kong</div>
  <div class="executive-links">
    <a class="executive-cta" href="https://www.linkedin.com/in/melizza-anievas/" target="_blank" rel="noopener noreferrer">💼 Book Strategic Consulting</a>
    <a class="executive-cta substack" href="https://ruleofinnovation.substack.com/" target="_blank" rel="noopener noreferrer">✍️ Read &amp; Subscribe: Rule of Innovation Substack</a>
  </div>
</div>
""", unsafe_allow_html=True)
'''
    if legacy_header in source:
        source = source.replace(legacy_header, UPDATED_MAIN_HEADER, 1)
    elif UPDATED_MAIN_HEADER not in source:
        raise RuntimeError("Could not locate the main header block to replace")

    legacy_sidebar_header = '''# ── Sidebar ───────────────────────────────────────────────────────────────────
# The hub list is database-driven: it is rebuilt from the normalized dataframe
# on every Streamlit rerun, including after an approved Airtable submission.
st.sidebar.header("🎛️ Dashboard Controls")'''
    updated_sidebar_header = f'''# ── Sidebar ───────────────────────────────────────────────────────────────────
# The hub list is database-driven: it is rebuilt from the normalized dataframe
# on every Streamlit rerun, including after an approved Airtable submission.
{UPDATED_SIDEBAR_EXECUTIVE_BLOCK}
st.sidebar.header("🎛️ Dashboard Controls")'''
    if legacy_sidebar_header in source:
        source = source.replace(legacy_sidebar_header, updated_sidebar_header, 1)
    elif updated_sidebar_header not in source:
        raise RuntimeError("Could not locate the sidebar header insertion point")

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
