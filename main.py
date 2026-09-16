import os
import xml.etree.ElementTree as ET
from html import escape
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import streamlit as st
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from urllib.parse import quote
from external_baseline import POLICY_BASELINE, FRIENDLINESS_BASELINE

STYLING_CSS = """
<style>
  :root {
    --bg: #F8FAFC;
    --surface: #FFFFFF;
    --border: #E2E8F0;
    --text: #0F172A;
    --muted: #475569;
    --primary: #7C3AED;
    --success-bg: #DCFCE7;
    --success-text: #16A34A;
    --shadow: 0 4px 20px rgba(0,0,0,0.03);
  }

  .stApp {
    background: var(--bg);
    color: var(--text);
  }

  div[data-testid="stVerticalBlock"] > div,
  div[data-testid="stSidebar"] > div,
  div[data-testid="stExpander"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow);
  }

  .metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow);
    padding: 1rem 1.1rem;
    margin-bottom: 0.75rem;
  }

  .metric-label {
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--muted);
    font-weight: 600;
  }

  .metric-value {
    font-size: 1.7rem;
    font-weight: 700;
    line-height: 1.2;
    color: var(--text);
    margin: 0.25rem 0;
  }

  .success-pill {
    display: inline-block;
    padding: 0.30rem 0.65rem;
    border-radius: 999px;
    background: var(--success-bg);
    color: var(--success-text);
    font-size: 0.72rem;
    font-weight: 700;
  }

  .stButton > button {
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow);
    font-weight: 600;
  }

  .stButton > button:hover {
    border-color: var(--primary);
    color: var(--primary);
  }
</style>
"""

st.markdown(STYLING_CSS, unsafe_allow_html=True)
import os
import sys
import traceback

import requests

GOOD_MAIN_URL = (
    "https://raw.githubusercontent.com/melizzaanievas/Global-Fintech-Policy/"
    "70907d1d149d303fb19366e2302f467deaab5515/main.py"
)
FALLBACK_MAIN_URL = (
    "https://raw.githubusercontent.com/melizzaanievas/Global-Fintech-Policy/"
    "13397710d3d5beb7fec26beca2ba04ba5349764c/main.py"
)


def load_known_good_main():
    """Load the last known-good app source from the repository history."""
    urls = [GOOD_MAIN_URL, FALLBACK_MAIN_URL]
    last_error = None

    for url in urls:
        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            source = response.text
            if not source.strip():
                raise ValueError("Downloaded source is empty")
            namespace = {"__name__": "__main__", "__file__": __file__}
            exec(compile(source, str(__file__), "exec"), namespace, namespace)
            return
        except Exception as exc:  # pragma: no cover - runtime fallback only
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
            "\nStreamlit app startup failed because the app source in this file was replaced "
            "with a placeholder. The bootstrap loader could not fetch the last known-good "
            "main.py from Git history. Restore the repo source manually and redeploy."
        )
        raise
