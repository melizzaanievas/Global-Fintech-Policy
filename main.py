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


def jurisdiction_update(jurisdiction, df_row=None):
    """Backward-compatible wrapper for jurisdiction update retrieval."""
    return get_latest_jurisdiction_news(jurisdiction, df_row or {})
'''


def patch_app_source(source):
    """Patch the known-good dashboard source with dynamic news and presentation updates."""
    def replace_once(old, new, description, already_present=None):
        nonlocal source
        if old in source:
            source = source.replace(old, new, 1)
            return
        if already_present and already_present in source:
            return
        raise RuntimeError(f"Could not locate the {description} block to replace")

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
    replace_once(
        legacy_render,
        dynamic_render,
        "regional update render",
        'headline, link = get_latest_jurisdiction_news(jur["name"], jur)',
    )

    legacy_jurisdiction_update = '''def jurisdiction_update(jurisdiction):
    """Return the reviewed update matched to the named featured jurisdiction."""
    return JURISDICTION_UPDATES.get(
        jurisdiction,
        (f"{jurisdiction} — official fintech update", ""),
    )
'''
    compatibility_jurisdiction_update = '''def jurisdiction_update(jurisdiction, df_row=None):
    """Backward-compatible wrapper for jurisdiction update retrieval."""
    return get_latest_jurisdiction_news(jurisdiction, df_row or {})
'''
    replace_once(
        legacy_jurisdiction_update,
        compatibility_jurisdiction_update,
        "jurisdiction update helper",
        "def jurisdiction_update(jurisdiction, df_row=None):",
    )

    legacy_success_pill_css = '''.status-red    { background:#7F1D1D; color:#FCA5A5; padding:3px 9px; border-radius:10px; font-size:0.75rem; font-weight:700; }
.policy-alert   { border-left:4px solid #F59E0B; background-color:#2D2A1A; color:#F5E6C8; padding:12px; border-radius:4px; }'''
    success_pill_css = '''.status-red    { background:#7F1D1D; color:#FCA5A5; padding:3px 9px; border-radius:10px; font-size:0.75rem; font-weight:700; }
.success-pill  { background:#DCFCE7; color:#16A34A; padding:4px 10px; border-radius:999px; font-size:0.82rem; font-weight:800; display:inline-block; }
.policy-alert   { border-left:4px solid #F59E0B; background-color:#2D2A1A; color:#F5E6C8; padding:12px; border-radius:4px; }'''
    replace_once(
        legacy_success_pill_css,
        success_pill_css,
        "success pill CSS",
        ".success-pill  { background:#DCFCE7; color:#16A34A;",
    )

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
    delta_badge_render = '''                delta = float(row.improvement_delta)
                delta_badge = (
                    f'<span class="success-pill">+{delta:.1f} pts</span>'
                    if delta >= 0
                    else (
                        '<span class="success-pill" '
                        'style="background:#FEE2E2;color:#B91C1C;">'
                        f'{delta:.1f} pts</span>'
                    )
                )
                st.markdown(
                    f"<div style='background:#1A2535;border:1px solid #2D4A7A;border-radius:8px;padding:12px;text-align:center'>"
                    f"<div style='color:#94A3B8;font-size:0.75rem;margin-bottom:4px'>2016 → 2026 Composite</div>"
                    f"<div style='font-size:1.1rem;font-weight:700;color:#94A3B8'>{float(row.composite_2016):.1f}"
                    f" → <span style='color:#F1F5F9'>{composite:.1f}</span></div>"
                    f"<div style='margin-top:8px'>{delta_badge}</div>"
                    f"<div style='color:#64748B;font-size:0.75rem;margin-top:2px'>{row.improvement_trend}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )'''
    replace_once(
        legacy_delta_render,
        delta_badge_render,
        "leaderboard delta badge",
        'delta_badge = (\n                    f\'<span class="success-pill">+{delta:.1f} pts</span>\'',
    )

    shared_tabs = '''ffi_tab1, ffi_tab2, ffi_tab3 = st.tabs(["🏆 Leaderboard", "🕸️ Radar Comparison", "📈 10-Year Trajectory"])'''
    shared_palette_tabs = '''PALETTE = ["#7C3AED", "#3B82F6", "#2DD4BF", "#FB7185", "#F59E0B"]

ffi_tab1, ffi_tab2, ffi_tab3 = st.tabs(["🏆 Leaderboard", "🕸️ Radar Comparison", "📈 10-Year Trajectory"])'''
    replace_once(
        shared_tabs,
        shared_palette_tabs,
        "shared comparison chart palette",
        'PALETTE = ["#7C3AED", "#3B82F6", "#2DD4BF", "#FB7185", "#F59E0B"]',
    )

    legacy_radar_colors = '''        # High-contrast, colorblind-aware palette; fills stay subtle to avoid overlap.
        RADAR_COLORS = ["#00B8D9", "#66CC66", "#F2B134", "#FF6B6B", "#B18CFF"]
'''
    palette_colors = ""
    replace_once(
        legacy_radar_colors,
        palette_colors,
        "radar palette",
        'PALETTE = ["#7C3AED", "#3B82F6", "#2DD4BF", "#FB7185", "#F59E0B"]',
    )

    replace_once(
        '            trace_color = RADAR_COLORS[idx % len(RADAR_COLORS)]',
        '            trace_color = PALETTE[idx % len(PALETTE)]',
        "radar trace color assignment",
        'trace_color = PALETTE[idx % len(PALETTE)]',
    )
    replace_once(
        '                line=dict(color=trace_color, width=3),',
        '                line=dict(color=trace_color, width=2.5),',
        "radar trace line width",
        'line=dict(color=trace_color, width=2.5)',
    )

    legacy_radar_layout = '''        radar_fig.update_layout(
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
    themed_radar_layout = '''        radar_fig.update_layout(
            template="plotly_white",
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
                    tickfont=dict(color="#0F172A", size=13),
                    gridcolor="#E2E8F0",
                    linecolor="#E2E8F0",
                    layer="above traces",
                ),
            ),
            height=520,
            margin=dict(l=110, r=110, t=55, b=70),
            legend=dict(font=dict(size=11, color="#0F172A")),
        )'''
    replace_once(
        legacy_radar_layout,
        themed_radar_layout,
        "radar chart layout",
        'template="plotly_white"',
    )

    legacy_traj_layout = '''        traj_fig.update_layout(
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
    themed_traj_layout = '''        traj_fig.update_layout(
            barmode="stack",
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#0F172A"),
            height=420,
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
            margin=dict(l=20, r=60, t=30, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11, color="#0F172A"),
            ),
        )

        for idx, trace in enumerate(traj_fig.data):
            trace.marker.color = PALETTE[idx % len(PALETTE)]'''
    replace_once(
        legacy_traj_layout,
        themed_traj_layout,
        "trajectory chart layout",
        'trace.marker.color = PALETTE[idx % len(PALETTE)]',
    )
    replace_once(
        '                font=dict(size=11, color="#F1F5F9"),',
        '                font=dict(size=11, color="#0F172A"),',
        "trajectory annotation font color",
        'font=dict(size=11, color="#0F172A")',
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
