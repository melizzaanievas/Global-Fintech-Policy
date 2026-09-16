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

PALETTE = ["#7C3AED", "#3B82F6", "#2DD4BF", "#FB7185", "#F59E0B"]

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


def _replace_or_verify(source, old, new, marker):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise RuntimeError(f"Could not locate the {marker} block to replace")


def patch_app_source(source):
    """Patch the known-good dashboard source with dynamic news and chart theming."""
    if "import feedparser" not in source:
        source = source.replace(
            "from urllib.parse import quote",
            "from urllib.parse import quote\nimport feedparser\nimport urllib.parse",
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
    source = _replace_or_verify(
        source,
        legacy_render,
        dynamic_render,
        "regional update render",
    )

    legacy_jurisdiction_update = '''def jurisdiction_update(jurisdiction):
    """Return the reviewed update matched to the named featured jurisdiction."""
    return JURISDICTION_UPDATES.get(
        jurisdiction,
        (f"{jurisdiction} — official fintech update", ""),
    )'''
    dynamic_jurisdiction_update = '''def jurisdiction_update(jurisdiction, df_row=None):
    """Return the best available update for the named jurisdiction."""
    return get_latest_jurisdiction_news(jurisdiction, df_row or {})'''
    source = _replace_or_verify(
        source,
        legacy_jurisdiction_update,
        dynamic_jurisdiction_update,
        "jurisdiction update helper",
    )

    source = _replace_or_verify(
        source,
        '        trace_color = RADAR_COLORS[idx % len(RADAR_COLORS)]',
        '        trace_color = PALETTE[idx % len(PALETTE)]',
        "radar palette",
    )
    source = _replace_or_verify(
        source,
        '                line=dict(color=trace_color, width=3),',
        '                line=dict(color=trace_color, width=2.5),',
        "radar trace width",
    )

    radar_layout_old = '''        radar_fig.update_layout(
            polar=dict(
                bgcolor="rgba(15,23,42,0.96)",
                radialaxis=dict(
                    visible=True,
                    range=[0, 10],
                    tickfont=dict(size=10, color="#E2E8F0"),
                    tickvals=[2, 4, 6, 8, 10],
                    gridcolor="#52627A",
                    linecolor="#718096",
                ),
                angularaxis=dict(
                    showticklabels=True,
                    tickmode="array",
                    tickvals=dim_labels,
                    ticktext=dim_labels,
                    tickfont=dict(color="#1E293B", size=13, weight="bold"),
                    gridcolor="#52627A",
                    linecolor="#718096",
                    layer="above traces",
                ),
            ),
            template="plotly_dark",
            height=520,
            margin=dict(l=110, r=110, t=55, b=70),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                font=dict(size=12, color="#F8FAFC"),
                bgcolor="rgba(15,23,42,0.96)",
                bordercolor="#718096",
                borderwidth=1,
            ),
        )'''
    radar_layout_new = '''        radar_fig.update_layout(
            template="plotly_white",
            height=520,
            margin=dict(l=110, r=110, t=55, b=70),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#0F172A"),
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(
                    visible=True,
                    range=[0, 10],
                    tickfont=dict(size=10, color="#0F172A"),
                    tickvals=[2, 4, 6, 8, 10],
                    gridcolor="#E2E8F0",
                    linecolor="#E2E8F0",
                    showline=True,
                ),
                angularaxis=dict(
                    showticklabels=True,
                    tickmode="array",
                    tickvals=dim_labels,
                    ticktext=dim_labels,
                    tickfont=dict(color="#0F172A", size=13, weight="bold"),
                    gridcolor="#E2E8F0",
                    linecolor="#E2E8F0",
                    layer="above traces",
                ),
            ),
            legend=dict(
                font=dict(size=12, color="#0F172A"),
                bgcolor="rgba(0,0,0,0)",
                bordercolor="#E2E8F0",
                borderwidth=1,
            ),
        )'''
    source = _replace_or_verify(
        source,
        radar_layout_old,
        radar_layout_new,
        "radar layout",
    )

    source = _replace_or_verify(
        source,
        '                font=dict(size=11, color="#F1F5F9"),',
        '                font=dict(size=11, color="#0F172A"),',
        "trajectory annotation font",
    )

    traj_layout_old = '''        traj_fig.update_layout(
            barmode="stack",
            template="plotly_dark",
            height=420,
            xaxis=dict(title="Composite Score (1–10)", range=[0, 11.5], gridcolor="#1E3A5F"),
            yaxis=dict(title="", tickfont=dict(size=11)),
            margin=dict(l=20, r=60, t=30, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )'''
    traj_layout_new = '''        traj_fig.update_layout(
            barmode="stack",
            template="plotly_white",
            height=420,
            margin=dict(l=20, r=60, t=30, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#0F172A"),
            xaxis=dict(
                title="Composite Score (1–10)",
                range=[0, 11.5],
                gridcolor="#E2E8F0",
                zerolinecolor="#E2E8F0",
            ),
            yaxis=dict(
                title="",
                tickfont=dict(size=11, color="#0F172A"),
                gridcolor="#E2E8F0",
                zerolinecolor="#E2E8F0",
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="#0F172A"),
            ),
        )
        for idx, trace in enumerate(traj_fig.data):
            trace.marker.color = PALETTE[idx % len(PALETTE)]'''
    source = _replace_or_verify(
        source,
        traj_layout_old,
        traj_layout_new,
        "trajectory layout",
    )

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
