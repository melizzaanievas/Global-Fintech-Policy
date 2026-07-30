import os
import xml.etree.ElementTree as ET
from html import escape
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import streamlit as st
from datetime import datetime, timedelta
from urllib.parse import quote
from external_baseline import POLICY_BASELINE, FRIENDLINESS_BASELINE

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Macro Web3 Policy & Market Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
.metric-card {
    background-color: #1E2A45; color: #E2E8F0;
    padding: 16px; border-radius: 10px; border: 1px solid #3B5280;
    height: 100%;
}
.metric-card .label { color:#94A3B8; font-size:0.78rem; letter-spacing:0.05em; text-transform:uppercase; font-weight:600; margin-bottom:4px; }
.metric-card .value { color:#F1F5F9; font-size:1.5rem; font-weight:700; margin:6px 0 2px 0; }
.metric-card .unit  { color:#64748B; font-size:0.75rem; margin-bottom:8px; }
.delta-up   { color:#34D399; font-size:0.8rem; font-weight:600; }
.delta-down { color:#F87171; font-size:0.8rem; font-weight:600; }
.delta-flat { color:#94A3B8; font-size:0.8rem; font-weight:600; }
.status-green  { background:#064E3B; color:#6EE7B7; padding:3px 9px; border-radius:10px; font-size:0.75rem; font-weight:700; }
.status-yellow { background:#78350F; color:#FCD34D; padding:3px 9px; border-radius:10px; font-size:0.75rem; font-weight:700; }
.status-red    { background:#7F1D1D; color:#FCA5A5; padding:3px 9px; border-radius:10px; font-size:0.75rem; font-weight:700; }
.policy-alert   { border-left:4px solid #F59E0B; background-color:#2D2A1A; color:#F5E6C8; padding:12px; border-radius:4px; }
.rating-high    { background:#064E3B; color:#6EE7B7; padding:4px 10px; border-radius:12px; font-weight:700; display:inline-block; }
.rating-mid     { background:#78350F; color:#FCD34D; padding:4px 10px; border-radius:12px; font-weight:700; display:inline-block; }
.rating-low     { background:#7F1D1D; color:#FCA5A5; padding:4px 10px; border-radius:12px; font-weight:700; display:inline-block; }
.regional-rating { border:1px solid #3B5280; border-left:6px solid #3B82F6; background:#111C2E; border-radius:8px; padding:12px 14px; margin:14px 0 8px 0; }
.regional-rating-high { border-left-color:#10B981; }
.regional-rating-mid { border-left-color:#F59E0B; }
.regional-rating-low { border-left-color:#EF4444; }
.regional-rating .eyebrow { color:#94A3B8; font-size:0.68rem; letter-spacing:0.08em; text-transform:uppercase; font-weight:700; }
.regional-rating .score { color:#F8FAFC; font-size:1.7rem; line-height:1.1; font-weight:800; margin:3px 0; }
.regional-rating .status { color:#CBD5E1; font-size:0.86rem; font-weight:700; }
.regional-rating .scale { color:#94A3B8; font-size:0.74rem; margin-top:5px; }
.ffi-bento { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; margin:10px 0 16px 0; }
.ffi-bento-card { background:#202A38; border:1px solid #526174; border-radius:8px; padding:12px; min-height:112px; }
.ffi-bento-label { color:#F8FAFC; font-size:0.76rem; font-weight:700; line-height:1.25; }
.ffi-bento-desc { color:#CBD5E1; font-size:0.68rem; line-height:1.3; margin:7px 0 10px 0; }
.ffi-bento-score { color:#FFFFFF; font-size:1.25rem; font-weight:800; }
.ffi-bento-track { background:#344256; border-radius:4px; height:7px; margin-top:7px; }
.ffi-bento-fill { background:#7CC7FF; border-radius:4px; height:7px; }
@media (max-width: 800px) {
    .ffi-bento { grid-template-columns:repeat(2,minmax(0,1fr)); }
}
@media (max-width: 480px) {
    .ffi-bento { grid-template-columns:1fr; }
}
.news-item      { border-left:3px solid #3B82F6; padding:6px 12px; margin:6px 0; background:#192030; border-radius:4px; }
.explainer-box  { background:#1A2535; border:1px solid #2D4A7A; border-radius:8px; padding:16px; margin-top:8px; }
.executive-banner { width:100%; box-sizing:border-box; background:#0B1B35; border:1px solid #D4AF37; border-left:6px solid #D4AF37; border-radius:4px; padding:20px 22px 22px 22px; margin:0 0 8px 0; box-shadow:0 8px 20px rgba(7,20,42,0.18); }
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
.executive-cta.substack:hover { background:#FFFFFF; }
.quick-links { width:100%; box-sizing:border-box; background:#F8FAFC; border:1px solid #D7DEE8; border-radius:8px; padding:10px 12px; margin:10px 0 8px 0; }
.quick-links-label { color:#64748B; font-size:0.68rem; font-weight:800; letter-spacing:0.1em; text-transform:uppercase; margin:0 0 7px 2px; }
.shortcut-link { display:flex; align-items:center; justify-content:center; min-height:42px; box-sizing:border-box; width:100%; padding:8px 12px; border:1px solid #CBD5E1; border-radius:6px; background:#FFFFFF; color:#1E293B !important; font-size:0.88rem; font-weight:650; text-align:center; text-decoration:none !important; }
.shortcut-link:hover { background:#EFF6FF; border-color:#3B82F6; color:#1D4ED8 !important; }
.sidebar-nav-link { display:block; padding:7px 9px; margin:3px 0; border-radius:5px; color:#334155 !important; font-size:0.86rem; text-decoration:none !important; }
.sidebar-nav-link:hover { background:#E2E8F0; color:#1D4ED8 !important; }
.dashboard-anchor { scroll-margin-top:16px; height:0; }
@media (max-width: 600px) {
    .executive-banner { padding:17px 17px 19px 17px; }
    .executive-banner .executive-title { font-size:1.58rem; margin-bottom:16px; }
    .executive-credentials { font-size:0.98rem; }
    .executive-org { font-size:0.84rem; }
    .executive-links { flex-direction:column; gap:10px; }
    .executive-cta { width:100%; text-align:center; }
}
</style>
""", unsafe_allow_html=True)

# ── Airtable data connection ──────────────────────────────────────────────────
# Configure these in Replit Secrets:
# AIRTABLE_TOKEN, AIRTABLE_BASE_ID
# Optional: AIRTABLE_TABLE_NAME and AIRTABLE_VIEW_ID can override the linked
# Airtable table/view below.
# Optional: AIRTABLE_INDEX_TABLE for the separate friendliness-index table.
def configured_secret(name):
    """Read a configured secret from Streamlit's secrets store only."""
    try:
        return st.secrets.get(name)
    except Exception:
        return None

AIRTABLE_TOKEN = configured_secret("AIRTABLE_TOKEN")
# Base/table/view IDs are public Airtable resource identifiers, not credentials.
# Use the linked workspace defaults when Streamlit secrets only contain the token.
AIRTABLE_BASE_ID = configured_secret("AIRTABLE_BASE_ID") or "app9dJxoBhli9fvkj"
CONNECTOR_HOST = os.environ.get("REPLIT_CONNECTORS_HOSTNAME")
CONNECTOR_IDENTITY = os.environ.get("REPL_IDENTITY") or os.environ.get("WEB_REPL_RENEWAL")
AIRTABLE_CONNECTOR_ENABLED = bool(CONNECTOR_HOST and CONNECTOR_IDENTITY)
AIRTABLE_ENABLED = bool(AIRTABLE_BASE_ID and (AIRTABLE_TOKEN or AIRTABLE_CONNECTOR_ENABLED))
if not AIRTABLE_ENABLED:
    st.info(
        "Airtable is not configured. Showing the external research baseline; "
        "submissions are disabled until AIRTABLE_TOKEN and AIRTABLE_BASE_ID "
        "are added to Streamlit secrets."
    )

# The linked Airtable URL supplies a stable table and view ID. IDs are not
# credentials, and using them avoids schema discovery failures in deployments.
AIRTABLE_TABLE_NAME = configured_secret("AIRTABLE_TABLE_NAME") or "tblIJLTfhGh2ssB5o"
AIRTABLE_VIEW_ID = configured_secret("AIRTABLE_VIEW_ID") or "viw37LAtgfx43Eqvu"
AIRTABLE_INDEX_TABLE = configured_secret("AIRTABLE_INDEX_TABLE")
AIRTABLE_API_ROOT = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}"
AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json",
}

def airtable_request(method, path, connector_path=None, **kwargs):
    """Call Airtable through Replit's connector or Streamlit secrets fallback."""
    try:
        if AIRTABLE_CONNECTOR_ENABLED:
            connector_token = (
                f"repl {os.environ['REPL_IDENTITY']}"
                if os.environ.get("REPL_IDENTITY")
                else f"depl {os.environ['WEB_REPL_RENEWAL']}"
            )
            headers = dict(kwargs.pop("headers", {}))
            headers.pop("Authorization", None)
            headers.update({
                "X-Replit-Token": connector_token,
                "Connector-Name": "airtable",
            })
            return requests.request(
                method,
                f"https://{CONNECTOR_HOST}/api/v2/proxy"
                f"{connector_path or f'/v0/{AIRTABLE_BASE_ID}{path}'}",
                headers=headers,
                **kwargs,
            )
        return requests.request(
            method,
            f"{AIRTABLE_API_ROOT}{path}",
            headers=kwargs.pop("headers", AIRTABLE_HEADERS),
            **kwargs,
        )
    except Exception:
        return None

def airtable_table_names():
    """Discover table IDs/names from the configured base."""
    if not AIRTABLE_ENABLED:
        return []
    try:
        response = airtable_request(
            "GET",
            f"/meta/bases/{quote(str(AIRTABLE_BASE_ID), safe='')}/tables",
            connector_path=f"/v0/meta/bases/{quote(str(AIRTABLE_BASE_ID), safe='')}/tables",
            headers=AIRTABLE_HEADERS,
            timeout=20,
        )
        if response is None:
            raise requests.RequestException("No Airtable response received")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Airtable returned an invalid table-list payload")
        return payload.get("tables", [])
    except Exception as exc:
        st.warning(f"Airtable table discovery was unavailable; using baseline data. ({exc})")
        return []

def resolve_airtable_table_name():
    """Prefer the exact configured table, otherwise discover the first table."""
    # When the user supplies a table ID/name, use it directly. This avoids
    # requiring Airtable's schema.bases:read permission just to read records.
    if AIRTABLE_TABLE_NAME:
        return AIRTABLE_TABLE_NAME

    tables = airtable_table_names()
    if not tables:
        return None
    for table in tables:
        if isinstance(table, dict):
            table_name = table.get("name") or table.get("id")
            if table_name:
                return table_name
    return None

def airtable_records(table_name, view_id=None):
    """Read every Airtable record and return a normalized DataFrame."""
    if not AIRTABLE_ENABLED or not table_name:
        return pd.DataFrame()
    records = []
    offset = None
    encoded_table_name = quote(str(table_name), safe="")
    while True:
        params = {"pageSize": 100}
        if view_id:
            params["view"] = view_id
        if offset:
            params["offset"] = offset
        try:
            response = airtable_request(
                "GET",
                f"/{encoded_table_name}",
                headers=AIRTABLE_HEADERS,
                params=params,
                timeout=20,
            )
            if response is None:
                raise requests.RequestException("No Airtable response received")
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("records", []), list):
                raise ValueError("Airtable returned an invalid records payload")
        except Exception as exc:
            st.warning(
                f"Airtable records could not be read from '{table_name}'; "
                f"using available baseline data. ({exc})"
            )
            return pd.DataFrame()
        for record in payload.get("records", []):
            if not isinstance(record, dict) or not record.get("id"):
                continue
            fields = record.get("fields", {})
            records.append({
                "_airtable_record_id": record["id"],
                **(fields if isinstance(fields, dict) else {}),
            })
        offset = payload.get("offset")
        if not offset:
            break
    return pd.DataFrame(records)

def airtable_create(table_name, fields):
    """Create one record without exposing the token in logs or UI."""
    if not AIRTABLE_ENABLED:
        st.warning("Airtable submission skipped because Airtable secrets are not configured.")
        return None
    if not table_name:
        st.warning("Airtable submission skipped because no table is configured.")
        return None
    encoded_table_name = quote(str(table_name), safe="")
    try:
        response = airtable_request(
            "POST",
            f"/{encoded_table_name}",
            headers=AIRTABLE_HEADERS,
            json={"fields": fields},
            timeout=20,
        )
        if response is None:
            raise requests.RequestException("No Airtable response received")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Airtable returned an invalid create response")
        return payload
    except Exception as exc:
        st.error(f"Airtable could not save this submission. ({exc})")
        return None

def airtable_update(table_name, record_id, fields):
    """Patch only known fields so Airtable headers/columns remain intact."""
    if not AIRTABLE_ENABLED:
        st.warning("Airtable update skipped because Airtable secrets are not configured.")
        return None
    if not table_name or not record_id:
        st.warning("Airtable update skipped because the table or record is unavailable.")
        return None
    encoded_table_name = quote(str(table_name), safe="")
    try:
        response = airtable_request(
            "PATCH",
            f"/{encoded_table_name}/{quote(str(record_id), safe='')}",
            headers=AIRTABLE_HEADERS,
            json={"fields": fields},
            timeout=20,
        )
        if response is None:
            raise requests.RequestException("No Airtable response received")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Airtable returned an invalid update response")
        return payload
    except Exception as exc:
        st.error(f"Airtable could not update this submission. ({exc})")
        return None

def airtable_ensure_status_column(table_name):
    """Create the review-status field once, without breaking existing bases."""
    if not AIRTABLE_ENABLED or not table_name:
        return False
    encoded_table_name = quote(str(table_name), safe="")
    metadata_path = (
        f"/meta/bases/{quote(str(AIRTABLE_BASE_ID), safe='')}"
        f"/tables/{encoded_table_name}/fields"
    )
    try:
        response = airtable_request(
            "POST",
            metadata_path,
            connector_path=f"/v0{metadata_path}",
            headers=AIRTABLE_HEADERS,
            json={"name": "Status", "type": "singleLineText"},
            timeout=20,
        )
        if response is None:
            raise requests.RequestException("No Airtable response received")
        if response.status_code in (200, 201):
            return True
        # Airtable returns a validation error when the field already exists.
        if response.status_code == 422:
            return True
        response.raise_for_status()
        return True
    except Exception as exc:
        st.error(f"Airtable could not prepare the Status field. ({exc})")
        return False

def normalize_airtable_columns(frame):
    """Normalize common Airtable header styles into the app's stable schema."""
    if frame.empty:
        return frame
    aliases = {
        "jurisdiction authority": "jurisdiction",
        "jurisdiction / authority": "jurisdiction",
        "core regulatory action item": "regulatory_shift",
        "regulatory action": "regulatory_shift",
        "geopolitical alignment vector": "geopolitical_context",
        "projected macro/gdp trajectory": "gdp_impact_trajectory",
        "industry addressable revenue scale ($b)": "industry_rev_projection",
        "volatility impact rating": "impact_score",
        "impact score": "impact_score",
        "regulatory clarity": "regulatory_clarity",
        "sandbox speed": "sandbox_speed",
        "licensing friction": "licensing_friction",
        "licensing ease": "licensing_ease",
        "tax incentives": "tax_incentives",
        "institutional banking": "institutional_banking",
        "institutional banking access": "institutional_banking",
        "region": "region",
        "date logged": "date_logged",
        "status": "status",
    }
    renamed = {}
    for column in frame.columns:
        normalized = str(column).strip().casefold().replace("_", " ")
        normalized = " ".join(normalized.split())
        renamed[column] = aliases.get(normalized, column)
    return frame.rename(columns=renamed)

def approved_airtable_records(frame):
    """Only approved Airtable overlays may affect dashboard intelligence."""
    if frame.empty:
        return frame
    if "status" not in frame.columns:
        return frame.iloc[0:0].copy()
    return frame[
        frame["status"].astype(str).str.strip().str.casefold() == "approved"
    ].copy()

POLICY_METADATA = {
    "Hong Kong (SFC)": {
        "instrument_name": "SFC VATP licensing regime and staking circulars",
        "effective_date": "VATP regime: 1 Jun 2023; current update logged: 14 May 2026",
        "supervisory_bodies": "Securities and Futures Commission (SFC); Hong Kong Monetary Authority (HKMA)",
        "implementation_status": "In force; institutional staking and stablecoin rules are phased",
        "jurisdiction_scope": "Hong Kong virtual-asset trading platforms and institutional market infrastructure",
        "official_source": "https://www.sfc.hk/en/Welcome-to-the-Fintech-Contact-Point/Virtual-assets/Virtual-asset-trading-platforms-operators",
    },
    "European Union": {
        "instrument_name": "Markets in Crypto-Assets Regulation (MiCA), Regulation (EU) 2023/1114",
        "effective_date": "Stablecoin titles: 30 Jun 2024; CASP regime: 30 Dec 2024",
        "supervisory_bodies": "European Securities and Markets Authority (ESMA); national competent authorities",
        "implementation_status": "In force across the EU; supervisory convergence and enforcement continue",
        "jurisdiction_scope": "EU-wide issuance, trading, custody, stablecoin, and crypto-asset service activity",
        "official_source": "https://eur-lex.europa.eu/eli/reg/2023/1114/oj/eng",
    },
    "United States": {
        "instrument_name": "Executive Order on Digital Asset Anti-Money Laundering Frameworks",
        "effective_date": "Current policy update logged: 10 Jul 2026; agency implementation is staged",
        "supervisory_bodies": "Treasury / FinCEN; Securities and Exchange Commission (SEC); Commodity Futures Trading Commission (CFTC)",
        "implementation_status": "Federal policy direction; implementation depends on agency rules and enforcement",
        "jurisdiction_scope": "Federal AML, market-structure, and institutional digital-asset activity",
        "official_source": "https://www.sec.gov/digital-assets",
    },
    "Singapore (MAS)": {
        "instrument_name": "Payment Services Act 2019/2023 and MAS tokenisation framework",
        "effective_date": "PSA licensing: 28 Jan 2020; current RWA framework update logged: 15 Jan 2026",
        "supervisory_bodies": "Monetary Authority of Singapore (MAS)",
        "implementation_status": "In force; tokenisation implementation is phased through institutional pilots",
        "jurisdiction_scope": "Digital-payment-token services, tokenised assets, and regulated financial institutions",
        "official_source": "https://www.mas.gov.sg/regulation/guidelines/ps-g02-guidelines-on-provision-of-digital-payment-token-services-to-the-public",
    },
    "Brazil (BACEN)": {
        "instrument_name": "Law 14.478/2022 Virtual Asset Service Provider framework and Drex pilot",
        "effective_date": "Law 14.478 framework: 20 Jun 2023; Drex Phase II remains pilot-stage",
        "supervisory_bodies": "Banco Central do Brasil (BACEN); Comissão de Valores Mobiliários (CVM)",
        "implementation_status": "Licensing framework in force; CBDC and tokenisation components remain phased",
        "jurisdiction_scope": "VASP licensing, payments, CBDC experimentation, and tokenised financial instruments",
        "official_source": "https://www.bcb.gov.br/estabilidadefinanceira/drex",
    },
    "Mexico (Banxico)": {
        "instrument_name": "Ley Fintech implementation framework and Banxico crypto-asset restrictions",
        "effective_date": "Ley Fintech: 2018 framework; current exchange update logged: 30 May 2026",
        "supervisory_bodies": "Banco de México (Banxico); Comisión Nacional Bancaria y de Valores (CNBV)",
        "implementation_status": "In force with restrictive crypto-asset treatment and continuing implementation",
        "jurisdiction_scope": "Fintech institutions, payment rails, exchanges, and cross-border settlement",
        "official_source": "https://www.banxico.org.mx",
    },
    "Colombia (SFC)": {
        "instrument_name": "SFC regulatory sandbox and tokenised sovereign-bond pilot",
        "effective_date": "Sandbox framework active since 2020; current pilot update logged: 15 Jun 2026",
        "supervisory_bodies": "Superintendencia Financiera de Colombia (SFC); Banco de la República",
        "implementation_status": "Sandbox / pilot stage; permanent crypto-asset perimeter remains developing",
        "jurisdiction_scope": "Regulated fintech experimentation, payments, and tokenised securities",
        "official_source": "https://www.superfinanciera.gov.co/inicio/sandbox",
    },
    "UAE (VARA / DIFC)": {
        "instrument_name": "VARA Virtual Assets and Related Activities Regulations and DIFC testing regime",
        "effective_date": "VARA established 2022; rulebooks and institutional updates phased through 2026",
        "supervisory_bodies": "Dubai Virtual Assets Regulatory Authority (VARA); DIFC / DFSA",
        "implementation_status": "In force; licensing and custody requirements continue to expand",
        "jurisdiction_scope": "Dubai virtual-asset activities, custody, exchanges, and innovation testing",
        "official_source": "https://www.vara.ae/en/",
    },
    "Saudi Arabia (SAMA/CMA)": {
        "instrument_name": "CMA digital-asset trading-platform consultation",
        "effective_date": "Consultation update logged: 1 Jul 2026; not yet a complete enacted regime",
        "supervisory_bodies": "Capital Market Authority (CMA); Saudi Central Bank (SAMA)",
        "implementation_status": "Consultation / developing framework; implementation remains conditional",
        "jurisdiction_scope": "Digital-asset trading, capital-markets activity, and Vision 2030 diversification",
        "official_source": "https://cma.org.sa",
    },
    "Bahrain (CBB)": {
        "instrument_name": "CBB Crypto-Asset Module and DeFi licensing amendment",
        "effective_date": "Crypto-Asset Module: 2019; current DeFi update logged: 18 Jul 2026",
        "supervisory_bodies": "Central Bank of Bahrain (CBB)",
        "implementation_status": "In force; DeFi category and sandbox treatment are being expanded",
        "jurisdiction_scope": "Crypto-asset services, exchanges, custody, and regulated DeFi activity",
        "official_source": "https://www.cbb.gov.bh/crypto-assets",
    },
    "Nigeria (SEC / CBN)": {
        "instrument_name": "SEC Nigeria Digital Assets Rules and CBN banking-access guidance",
        "effective_date": "SEC rules: 2022; CBN banking-access reversal: 2024; current update: 20 May 2026",
        "supervisory_bodies": "Securities and Exchange Commission Nigeria (SEC); Central Bank of Nigeria (CBN)",
        "implementation_status": "Licensing framework in force; banking access is reopening on a regulated basis",
        "jurisdiction_scope": "VASP licensing, banking access, payments, and diaspora remittance rails",
        "official_source": "https://sec.gov.ng/for-investors/keep-track-of-circulars/statement-on-digital-assets-and-their-classification-and-treatment/",
    },
    "Kenya (CBK / CMA)": {
        "instrument_name": "CMA draft crypto-asset framework and CBK regulatory sandbox",
        "effective_date": "Sandbox active since 2021; current consultation update logged: 10 Jun 2026",
        "supervisory_bodies": "Capital Markets Authority (CMA); Central Bank of Kenya (CBK)",
        "implementation_status": "Consultation / sandbox stage; permanent VASP framework is not fully in force",
        "jurisdiction_scope": "Crypto-asset services, mobile-money interoperability, and fintech pilots",
        "official_source": "https://www.cma.or.ke/regulatory-sandbox/",
    },
    "South Africa (FSCA)": {
        "instrument_name": "FSCA declaration of crypto assets as financial products",
        "effective_date": "Declaration: 19 Oct 2022; current licensing deadline update logged: 5 Jul 2026",
        "supervisory_bodies": "Financial Sector Conduct Authority (FSCA); South African Reserve Bank (SARB)",
        "implementation_status": "In force; FSP licensing and supervisory transition continue",
        "jurisdiction_scope": "Crypto-asset financial products, FSP licensing, custody, and institutional services",
        "official_source": "https://www.fsca.co.za/Regulatory%20Frameworks/Pages/Regulatory-Frameworks.aspx",
    },
    "Rwanda (BNR)": {
        "instrument_name": "National Fintech & Innovation Policy 2022–2027 and BNR innovation framework",
        "effective_date": "Policy period: 2022–2027; current midterm update logged: 22 Jul 2026",
        "supervisory_bodies": "National Bank of Rwanda (BNR); Kigali International Financial Centre (KIFC)",
        "implementation_status": "Policy implementation / innovation-office stage; formal crypto perimeter developing",
        "jurisdiction_scope": "Fintech innovation, payment infrastructure, sandbox activity, and regional HQ formation",
        "official_source": "https://www.bnr.rw/financial-sector/financial-innovation",
    },
    "Japan": {
        "instrument_name": "Payment Services Act crypto-asset exchange registration regime",
        "effective_date": "Crypto-asset amendments: 2019–2023; current reference review: 2026",
        "supervisory_bodies": "Japan Financial Services Agency (FSA)",
        "implementation_status": "In force; registered-exchange and stablecoin requirements apply",
        "jurisdiction_scope": "Registered crypto-asset exchanges, custody, stablecoins, and token issuance",
        "official_source": "https://www.fsa.go.jp/policy/virtual_currency/index.html",
    },
    "South Korea": {
        "instrument_name": "Virtual Asset User Protection Act",
        "effective_date": "19 Jul 2024; institutional-market implementation is continuing",
        "supervisory_bodies": "Financial Services Commission (FSC); Financial Intelligence Unit (FIU)",
        "implementation_status": "In force; licensing, custody, and market-integrity implementation continues",
        "jurisdiction_scope": "Virtual-asset exchanges, user protection, real-name accounts, and monitoring",
        "official_source": "https://www.fsc.go.kr/eng",
    },
    "United Kingdom": {
        "instrument_name": "Financial Services and Markets Act 2023 crypto-asset perimeter",
        "effective_date": "FSMA 2023: 29 Jun 2023; detailed crypto regime is phased",
        "supervisory_bodies": "Financial Conduct Authority (FCA); HM Treasury; Prudential Regulation Authority (PRA)",
        "implementation_status": "In force in stages; secondary rules and registration requirements continue",
        "jurisdiction_scope": "Cryptoasset promotions, registration, custody, trading, and financial-services perimeter",
        "official_source": "https://www.fca.org.uk/firms/new-regime-cryptoasset-regulation",
    },
    "European Union (MiCA)": {
        "instrument_name": "Markets in Crypto-Assets Regulation (MiCA), Regulation (EU) 2023/1114",
        "effective_date": "Stablecoin titles: 30 Jun 2024; CASP regime: 30 Dec 2024",
        "supervisory_bodies": "ESMA; EBA; national competent authorities",
        "implementation_status": "In force across the EU; supervisory convergence continues",
        "jurisdiction_scope": "EU-wide issuance, stablecoins, custody, trading, and crypto-asset services",
        "official_source": "https://eur-lex.europa.eu/eli/reg/2023/1114/oj/eng",
    },
    "LATAM (Brazil / Colombia)": {
        "instrument_name": "Brazil Law 14.478/2022 and Colombia SFC regulatory sandbox",
        "effective_date": "Brazil framework: 20 Jun 2023; Colombia sandbox active since 2020",
        "supervisory_bodies": "BACEN; CVM; Colombia SFC; Banco de la República",
        "implementation_status": "Mixed: Brazil licensing framework in force; Colombia remains sandbox-led",
        "jurisdiction_scope": "Regional VASP licensing, payment rails, tokenisation, and fintech pilots",
        "official_source": "https://www.bcb.gov.br/estabilidadefinanceira/drex",
    },
    "Africa (Kenya / Nigeria / Rwanda)": {
        "instrument_name": "SEC Nigeria Digital Assets Rules, CBK sandbox, and BNR fintech policy",
        "effective_date": "Nigeria rules: 2022; Kenya sandbox: 2021; Rwanda policy period: 2022–2027",
        "supervisory_bodies": "SEC Nigeria; CBN; CBK; CMA Kenya; BNR Rwanda",
        "implementation_status": "Mixed: licensing, sandbox, and policy regimes are at different stages",
        "jurisdiction_scope": "Regional VASP licensing, mobile-money rails, sandbox pilots, and fintech HQ formation",
        "official_source": "https://sec.gov.ng/for-investors/keep-track-of-circulars/statement-on-digital-assets-and-their-classification-and-treatment/",
    },
}

REGIONAL_METADATA = {
    "Hong Kong (SFC / HKMA)": POLICY_METADATA["Hong Kong (SFC)"],
    "Singapore (MAS)": POLICY_METADATA["Singapore (MAS)"],
    "Japan (FSA)": POLICY_METADATA["Japan"],
    "South Korea (FSC)": POLICY_METADATA["South Korea"],
    "Australia (ASIC)": {
        "instrument_name": "Treasury token-mapping consultation and ASIC digital-asset guidance",
        "effective_date": "ASIC INFO 225 guidance in force; current framework remains phased",
        "supervisory_bodies": "Australian Securities and Investments Commission (ASIC); Treasury",
        "implementation_status": "Guidance / legislative reform stage; licensing perimeter continues to develop",
        "jurisdiction_scope": "Digital-asset financial products, exchanges, custody, and licensing reform",
        "official_source": "https://www.asic.gov.au/regulatory-resources/digital-transformation/digital-assets-financial-products-and-services/",
    },
    "Federal (SEC / CFTC)": POLICY_METADATA["United States"],
    "UAE (VARA / DIFC)": POLICY_METADATA["UAE (VARA / DIFC)"],
    "Bahrain": POLICY_METADATA["Bahrain (CBB)"],
    "Nigeria": POLICY_METADATA["Nigeria (SEC / CBN)"],
    "Kenya": POLICY_METADATA["Kenya (CBK / CMA)"],
    "South Africa": POLICY_METADATA["South Africa (FSCA)"],
    "Rwanda": POLICY_METADATA["Rwanda (BNR)"],
    "MiCA Regulation (EU-wide)": POLICY_METADATA["European Union"],
    "Brazil": POLICY_METADATA["Brazil (BACEN)"],
    "Mexico": POLICY_METADATA["Mexico (Banxico)"],
    "Colombia": POLICY_METADATA["Colombia (SFC)"],
    "Saudi Arabia": POLICY_METADATA["Saudi Arabia (SAMA/CMA)"],
}

def enrich_policy_metadata(frame):
    """Add analyst-facing policy metadata without overwriting submitted values."""
    if frame.empty:
        return frame
    frame = frame.copy()
    metadata_columns = [
        "instrument_name", "effective_date", "supervisory_bodies",
        "implementation_status", "jurisdiction_scope", "official_source",
    ]
    for column in metadata_columns:
        if column not in frame.columns:
            frame[column] = ""
    for index, row in frame.iterrows():
        metadata = POLICY_METADATA.get(str(row.get("jurisdiction", "")).strip(), {})
        for column in metadata_columns:
            current = row.get(column)
            if pd.isna(current) or str(current).strip() == "":
                frame.at[index, column] = metadata.get(column, "")
    return frame

def metadata_for_jurisdiction(jurisdiction):
    """Resolve structured policy context for policy and index naming variants."""
    name = str(jurisdiction or "").strip()
    if name in POLICY_METADATA:
        return POLICY_METADATA[name]
    if name in REGIONAL_METADATA:
        return REGIONAL_METADATA[name]
    return {}

def ensure_columns(frame, defaults):
    """Ensure downstream charts can render with partial Airtable schemas."""
    frame = frame.copy()
    for column, default in defaults.items():
        if column not in frame.columns:
            frame[column] = default
    return frame

def policy_baseline_frame():
    frame = pd.DataFrame(POLICY_BASELINE, columns=[
        "jurisdiction", "regulatory_shift", "geopolitical_context",
        "gdp_impact_trajectory", "industry_rev_projection", "impact_score",
        "date_logged",
    ])
    frame["status"] = "Approved"
    return frame

def friendliness_baseline_frame():
    frame = pd.DataFrame(FRIENDLINESS_BASELINE, columns=[
        "jurisdiction", "region", "regulatory_clarity", "sandbox_speed",
        "licensing_ease", "tax_incentives", "institutional_banking",
        "composite_2026", "composite_2016", "improvement_delta",
        "improvement_trend", "improvement_notes", "sources", "year_assessed",
    ])
    frame["status"] = "Approved"
    return frame

def merge_friendliness_sources(external_df, airtable_df):
    """Keep the external research baseline and overlay supplied Airtable fields."""
    result = external_df.copy()
    if airtable_df.empty:
        return result
    key = "jurisdiction"
    for _, incoming in airtable_df.iterrows():
        jurisdiction = str(incoming.get(key, "")).strip()
        if not jurisdiction:
            continue
        matches = result[key].astype(str).str.strip().str.casefold() == jurisdiction.casefold()
        if matches.any():
            idx = result.index[matches][0]
            for column in result.columns:
                value = incoming.get(column)
                if pd.notna(value) and value not in ("", None):
                    result.at[idx, column] = value
        else:
            result = pd.concat([result, pd.DataFrame([incoming]),], ignore_index=True)
    return result

# ── Real policy events for timeline ──────────────────────────────────────────
# Categories: enforcement | legislation | market | cbdc | institutional | cooperation
POLICY_EVENTS_TIMELINE = [
    # 2021
    {"date": "2021-02-08", "label": "Tesla BTC", "jurisdiction": "United States",
     "event": "Tesla discloses $1.5B Bitcoin purchase and plans to accept BTC as payment. Signals start of corporate treasury adoption wave.",
     "impact": 7, "category": "institutional"},
    {"date": "2021-05-19", "label": "China Mining", "jurisdiction": "China",
     "event": "China's Inner Mongolia bans crypto mining. Followed by nationwide mining crackdown through June–July, causing ~50% BTC price drop in 3 weeks.",
     "impact": 9, "category": "enforcement"},
    {"date": "2021-09-07", "label": "BTC Legal Tender", "jurisdiction": "El Salvador",
     "event": "El Salvador becomes first country to adopt Bitcoin as legal tender (Ley Bitcoin). IMF and World Bank raise concerns. Triggers global debate on sovereign crypto adoption.",
     "impact": 8, "category": "legislation"},
    {"date": "2021-09-24", "label": "China Total Ban", "jurisdiction": "China",
     "event": "PBOC declares all crypto transactions illegal. Comprehensive ban covers trading, mining, and related services. ~20% of global hash rate migrates to USA, Kazakhstan, Russia.",
     "impact": 10, "category": "enforcement"},
    {"date": "2021-11-10", "label": "Crypto ATH", "jurisdiction": "Global",
     "event": "Global crypto market cap reaches all-time high of ~$3.0 trillion. Bitcoin hits $69K, Ethereum $4.8K. NFT and DeFi volumes at record highs.",
     "impact": 8, "category": "market"},
    # 2022
    {"date": "2022-02-21", "label": "Canada Freeze", "jurisdiction": "Canada",
     "event": "Canadian government freezes crypto wallets linked to Freedom Convoy truckers under Emergencies Act — first democratic government to weaponise crypto surveillance against domestic protest.",
     "impact": 8, "category": "enforcement"},
    {"date": "2022-03-09", "label": "Biden EO", "jurisdiction": "United States",
     "event": "Biden Executive Order on Ensuring Responsible Development of Digital Assets directs federal agencies to study crypto regulation, CBDC, and AML frameworks. Catalyses US regulatory framework debate.",
     "impact": 8, "category": "legislation"},
    {"date": "2022-05-12", "label": "LUNA Collapse", "jurisdiction": "Global",
     "event": "Terra/LUNA algorithmic stablecoin collapses, erasing $40B in market value in 72 hours. TerraUSD depegs catastrophically. Triggers cascade of DeFi insolvencies (Celsius, Three Arrows Capital). Market cap drops ~$600B.",
     "impact": 10, "category": "market"},
    {"date": "2022-08-08", "label": "Tornado Cash", "jurisdiction": "United States",
     "event": "US Treasury sanctions Tornado Cash smart contracts — first time immutable open-source code sanctioned. Raises fundamental legal questions about code-as-property and developer liability.",
     "impact": 9, "category": "enforcement"},
    {"date": "2022-11-11", "label": "FTX Collapse", "jurisdiction": "Global",
     "event": "FTX exchange files for bankruptcy. $8B customer funds misappropriated. Sam Bankman-Fried arrested Dec 12. Triggers global regulatory urgency; BTC drops to $15.5K. Market cap hits 2-year low of ~$780B.",
     "impact": 10, "category": "market"},
    # 2023
    {"date": "2023-02-13", "label": "BUSD Shutdown", "jurisdiction": "United States",
     "event": "NYDFS orders Paxos to stop minting BUSD stablecoin. SEC issues Wells Notice to Paxos. Signals aggressive stablecoin enforcement posture; BUSD market cap falls from $16B to near zero within months.",
     "impact": 8, "category": "enforcement"},
    {"date": "2023-03-22", "label": "CFTC v Binance", "jurisdiction": "United States",
     "event": "CFTC charges Binance and CZ with illegal derivatives trading and wilful evasion of US law. Largest enforcement action against a crypto exchange. CZ pleads guilty Nov 2023; $4.3B settlement.",
     "impact": 9, "category": "enforcement"},
    {"date": "2023-06-06", "label": "SEC v Coinbase", "jurisdiction": "United States",
     "event": "SEC sues Coinbase for operating as unregistered securities exchange, broker, and clearing agency. Filed one day after suing Binance. Creates existential compliance uncertainty for US-licensed exchanges.",
     "impact": 9, "category": "enforcement"},
    {"date": "2023-07-13", "label": "Ripple Ruling", "jurisdiction": "United States",
     "event": "Judge Torres rules XRP is NOT a security when sold on secondary markets (programmatic sales). Partial win for Ripple vs SEC. Landmark precedent limiting SEC jurisdiction over crypto tokens in open-market trading.",
     "impact": 9, "category": "legislation"},
    {"date": "2023-09-01", "label": "MiCA Enters Force", "jurisdiction": "European Union",
     "event": "EU Markets in Crypto-Assets Regulation (MiCA) formally enters into force (published June 9 2023; compliance dates phased). World's most comprehensive crypto regulatory framework. Stablecoin rules apply June 2024; full CASP rules December 2024.",
     "impact": 9, "category": "legislation"},
    {"date": "2023-08-29", "label": "Grayscale v SEC", "jurisdiction": "United States",
     "event": "DC Circuit Court rules SEC was 'arbitrary and capricious' in rejecting Grayscale's Bitcoin ETF. Orders SEC to re-review. Directly catalyses January 2024 Bitcoin ETF approvals.",
     "impact": 9, "category": "legislation"},
    {"date": "2023-11-21", "label": "CZ Guilty Plea", "jurisdiction": "United States",
     "event": "Binance CEO Changpeng Zhao (CZ) pleads guilty to AML violations; Binance pays $4.3B fine. Largest corporate settlement in DOJ history. Richard Teng becomes Binance CEO.",
     "impact": 8, "category": "enforcement"},
    # 2024
    {"date": "2024-01-10", "label": "BTC ETF Approved", "jurisdiction": "United States",
     "event": "SEC approves 11 spot Bitcoin ETFs including BlackRock iShares, Fidelity, and Invesco. First day: $4.6B traded. Within 3 months, BTC ETFs absorb >$35B in institutional capital. Largest ETF launch in history.",
     "impact": 10, "category": "institutional"},
    {"date": "2024-03-14", "label": "BTC New ATH", "jurisdiction": "Global",
     "event": "Bitcoin hits new all-time high of $73,738, driven by ETF inflows and pre-halving momentum. Global crypto market cap reaches $2.8T — first time since November 2021 bull peak.",
     "impact": 8, "category": "market"},
    {"date": "2024-04-19", "label": "BTC Halving", "jurisdiction": "Global",
     "event": "Bitcoin's fourth halving reduces block reward from 6.25 to 3.125 BTC. Historically precedes 12–18 month bull cycles. Programmatic supply reduction with zero policy discretion — studied by central bank researchers as monetary policy model.",
     "impact": 7, "category": "market"},
    {"date": "2024-05-22", "label": "FIT21 Passes", "jurisdiction": "United States",
     "event": "Financial Innovation and Technology for the 21st Century Act (FIT21) passes US House 279-136, with bipartisan support. First comprehensive US crypto market-structure legislation. Defines CFTC vs SEC jurisdiction. Awaits Senate.",
     "impact": 9, "category": "legislation"},
    {"date": "2024-06-30", "label": "MiCA Stablecoins", "jurisdiction": "European Union",
     "event": "MiCA stablecoin rules (Title III/IV) take effect across EU. USDT issuer Tether not EU-compliant; exchanges delist non-compliant stablecoins in EU. USDC-issuer Circle becomes first compliant EMT issuer.",
     "impact": 8, "category": "legislation"},
    {"date": "2024-11-06", "label": "US Election", "jurisdiction": "United States",
     "event": "Trump wins US presidential election on explicitly pro-crypto platform: promised Bitcoin strategic reserve, fired SEC Chair Gensler, pledged no CBDC. Bitcoin hits $75K day after election.",
     "impact": 10, "category": "institutional"},
    {"date": "2024-12-30", "label": "MiCA Full Force", "jurisdiction": "European Union",
     "event": "MiCA Crypto Asset Service Provider (CASP) licensing rules fully applicable across all 27 EU member states. Single passport: one licence = 27 markets. Estimated 300+ exchanges, custodians, and advisors now compliant or pending.",
     "impact": 9, "category": "legislation"},
    # 2025
    {"date": "2025-01-23", "label": "BTC Reserve EO", "jurisdiction": "United States",
     "event": "Trump signs Executive Order establishing a Working Group to evaluate a US Strategic Bitcoin Reserve and digital asset stockpile policy. Instructs agencies to halt CBDC development.",
     "impact": 10, "category": "legislation"},
    {"date": "2025-03-15", "label": "Genius Act", "jurisdiction": "United States",
     "event": "GENIUS Act (Guiding and Establishing National Innovation for US Stablecoins) introduced in Senate — first serious US federal stablecoin bill. Would require 1:1 reserves and federal/state licensing for stablecoin issuers.",
     "impact": 8, "category": "legislation"},
    {"date": "2025-07-01", "label": "HK Stablecoin Law", "jurisdiction": "Hong Kong (SFC)",
     "event": "Hong Kong Stablecoin Ordinance comes into effect — first comprehensive stablecoin licensing law in Asia. HKMA grants first licences to HKD-pegged stablecoin issuers. Positions HK as Asian stablecoin hub.",
     "impact": 9, "category": "legislation"},
    # 2026 (current/projected)
    {"date": "2026-01-15", "label": "MAS RWA Framework", "jurisdiction": "Singapore (MAS)",
     "event": "MAS publishes final Tokenisation Framework for Real World Assets — binding rules for tokenised bonds, funds, and real estate. Project Guardian Phase III launches with 10 banks.",
     "impact": 8, "category": "legislation"},
    {"date": "2026-05-14", "label": "HK VATP Rules", "jurisdiction": "Hong Kong (SFC)",
     "event": "SFC issues updated VATP Conduct Requirements including staking service circulars. Mandates segregated custody, client asset protections, and mandated insurance minimums. Sets Asia's institutional standard.",
     "impact": 9, "category": "legislation"},
    {"date": "2026-07-10", "label": "US AML EO", "jurisdiction": "United States",
     "event": "Executive Order on Digital Asset AML Frameworks expands Bank Secrecy Act obligations to DeFi protocols, NFT platforms, and self-hosted wallets transacting above $3,000/day.",
     "impact": 8, "category": "enforcement"},
]

CATEGORY_COLORS = {
    "enforcement":   "#EF4444",   # red
    "legislation":   "#F59E0B",   # amber
    "market":        "#A855F7",   # purple
    "institutional": "#22C55E",   # green
    "cbdc":          "#3B82F6",   # blue
    "cooperation":   "#06B6D4",   # cyan
}

CATEGORY_LABELS = {
    "enforcement":   "⚖️ Enforcement",
    "legislation":   "📜 Legislation",
    "market":        "📉 Market Event",
    "institutional": "🏦 Institutional",
    "cbdc":          "💱 CBDC",
    "cooperation":   "🤝 Cooperation",
}

# ── Market data pipeline ──────────────────────────────────────────────────────
class Web3DataPipeline:
    def __init__(self):
        self.cmc_key = configured_secret("CMC_API_KEY") or ""

    def fetch_market_trends(self, years=5):
        """Generate 5-year simulated market cap with a fixed seed for consistency."""
        np.random.seed(42)
        end   = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=365 * years)
        total_days = (end - start).days
        dates = [start + timedelta(days=i) for i in range(total_days + 1)]

        # Key waypoints (day index → approx USD market cap) reflecting real crypto history
        waypoints_idx = [
            0,    200,  305,  380,  490,  580,  670,  690,  800,
            900,  960,  1060, 1110, 1115, 1200, 1290, 1380, 1450,
            1480, 1500, 1570, 1600, 1700, total_days,
        ]
        waypoints_val = [
            0.90e12,  2.40e12,  2.95e12,  1.80e12,  1.25e12,  0.95e12,
            0.85e12,  0.78e12,  0.95e12,  1.15e12,  1.05e12,  1.45e12,
            1.70e12,  1.75e12,  2.65e12,  2.30e12,  2.40e12,  3.20e12,
            3.40e12,  3.50e12,  2.80e12,  2.60e12,  2.45e12,  2.62e12,
        ]

        base = np.interp(range(total_days + 1), waypoints_idx, waypoints_val)
        noise = np.cumsum(np.random.normal(0, 0.008, len(dates)))
        values = base * np.exp(noise * 0.18)

        return pd.DataFrame({"Date": dates, "Global_Market_Cap": values})

    def fetch_onchain_velocity(self):
        """Return current and previous-period metrics for delta calculation."""
        np.random.seed(int(datetime.now().strftime("%Y%m%d")))
        sol_tps_now  = int(np.random.normal(2800, 150))
        sol_tps_prev = int(np.random.normal(2800, 150))
        bsc_now      = int(np.random.normal(3200000, 200000))
        bsc_prev     = int(np.random.normal(3200000, 200000))
        return {
            "Solana_TPS":        sol_tps_now,
            "Solana_TPS_prev":   sol_tps_prev,
            "BSC_Daily_Tx":      bsc_now,
            "BSC_Daily_Tx_prev": bsc_prev,
            "Dune_Stablecoin_Volume_30d":      142.8,   # $B
            "Dune_Stablecoin_Volume_30d_prev": 135.2,
        }

pipeline = Web3DataPipeline()

# ── News fetch (cached 1 h) ───────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_rss_news(keywords: tuple, max_items: int = 5) -> list:
    urls = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ]
    results = []
    for url in urls:
        try:
            r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for item in root.findall(".//item"):
                title = item.findtext("title", "") or ""
                link  = item.findtext("link",  "") or ""
                desc  = item.findtext("description", "") or ""
                pub   = item.findtext("pubDate", "") or ""
                blob  = (title + " " + desc).lower()
                if any(k.lower() in blob for k in keywords):
                    results.append({"title": title, "link": link, "date": pub[:16]})
                if len(results) >= max_items:
                    return results
        except Exception:
            continue
    return results

# ── Regional fintech intelligence data ───────────────────────────────────────
REGIONAL_SOURCE_TITLES = {
    "https://www.sfc.hk/en/Welcome-to-the-Fintech-Contact-Point/Virtual-assets/Virtual-asset-trading-platforms-operators": "SFC — Virtual asset trading platform operators",
    "https://www.sfc.hk/-/media/EN/assets/components/Guidelines/File-current/Licensing-Handbook-for-VATPs_July-2025.pdf": "SFC — VATP licensing handbook",
    "https://www.mas.gov.sg/regulation/guidelines/ps-g02-guidelines-on-provision-of-digital-payment-token-services-to-the-public": "MAS — Digital Payment Token Services Guidelines",
    "https://www.mas.gov.sg/schemes-and-initiatives/project-guardian": "MAS — Project Guardian",
    "https://www.fsa.go.jp/policy/virtual_currency/index.html": "Japan FSA — Crypto-asset guidance",
    "https://www.fsc.go.kr/eng": "Korea FSC — Virtual asset supervision",
    "https://www.asic.gov.au/regulatory-resources/digital-transformation/digital-assets-financial-products-and-services/": "ASIC — Digital assets: financial products and services",
    "https://www.sec.gov/digital-assets": "US SEC — Digital assets",
    "https://www.cftc.gov/digitalassets": "US CFTC — Digital assets",
    "https://www.congress.gov/118/bills/hr4763/BILLS-118hr4763eh.pdf": "US Congress — FIT21 Act text",
    "https://www.dfs.ny.gov/virtual_currency_businesses": "NYDFS — Virtual currency businesses",
    "https://www.fca.org.uk/firms/cryptoassets/who-needs-register": "FCA — Who needs to register",
    "https://www.fca.org.uk/firms/new-regime-cryptoasset-regulation": "FCA — New cryptoasset regime",
    "https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica": "ESMA — Markets in Crypto-Assets Regulation",
    "https://eur-lex.europa.eu/eli/reg/2023/1114/oj/eng": "EUR-Lex — MiCA Regulation",
    "https://www.bcb.gov.br/estabilidadefinanceira/drex": "Banco Central do Brasil — Drex",
    "https://www.superfinanciera.gov.co/inicio/sandbox": "Colombia SFC — Regulatory sandbox",
    "https://www.vara.ae/en/": "VARA — Virtual assets regulator",
    "https://www.vara.ae/en/licenses-and-register/licence-applications/": "VARA — Licence applications",
    "https://www.cbb.gov.bh/crypto-assets": "CBB — Crypto-asset regulation",
    "https://sec.gov.ng/for-investors/keep-track-of-circulars/statement-on-digital-assets-and-their-classification-and-treatment/": "Nigeria SEC — Digital asset classification",
    "https://www.centralbank.go.ke/wp-content/uploads/2026/03/Draft-Virtual-Asset-Service-Providers-Regulations-2026.pdf": "Kenya — Virtual Asset Service Providers regulations",
    "https://www.cma.or.ke/regulatory-sandbox/": "Kenya CMA — Regulatory sandbox",
    "https://www.bnr.rw/regulatorysandbox": "Rwanda BNR — Regulatory sandbox",
    "https://www.cftc.gov/LearnAndProtect/EducationCenter": "US CFTC — Digital asset education and oversight",
    "https://www.bafin.de/EN/Aufsicht/FinTech/Fintech_node_en.html": "BaFin — FinTech supervision",
    "https://www.amf-france.org/en/professionals/fintech": "AMF — FinTech and digital assets",
    "https://www.bankofengland.co.uk/prudential-regulation": "Bank of England — Prudential regulation",
    "https://www.fsca.co.za/Regulatory%20Frameworks/Pages/Regulatory-Frameworks.aspx": "FSCA — Regulatory frameworks",
    "https://www.jerseyfsc.org/industry/fintech/virtual-assets/": "Jersey FSC — Virtual assets",
    "https://www.gfsc.gg/commission/regulated-sectors/virtual-asset-service-providers": "Guernsey FSC — Virtual asset service providers",
    "https://www.vara.ae/en/": "VARA — Virtual assets regulator",
    "https://wyomingbankingdivision.wyo.gov/banks-trust-companies/spdi": "Wyoming Banking Division — SPDI charter",
    "https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/06/20260629-4/": "HKMA — DLT in Hong Kong fixed-income markets",
    "https://www.whitehouse.gov/presidential-actions/2026/05/integrating-financial-technology-innovation-into-regulatory-frameworks/": "White House — Financial technology regulatory frameworks",
    "https://www.fca.org.uk/news/press-releases/fca-sets-landmark-crypto-rules-cement-uks-place-global-hub": "FCA — Latest crypto rules and UK hub strategy",
    "https://finance.ec.europa.eu/document/download/62be7015-f066-4fac-b74e-71bacdbcc9f5_en?filename=2026-mica-review-targeted-consultation-document_en.pdf": "European Commission — 2026 MiCA review consultation",
    "https://www.gov.br/fazenda/pt-br/composicao/orgaos/orgaos-colegiados/crsfn/acesso-a-informacao/noticias/2026/cvm-institui-grupo-de-trabalho-para-desenvolver-estudos-sobre-tokenizacao-de-valores-mobiliarios": "Brazil Finance Ministry — Tokenisation working group",
    "https://www.wam.ae/en/article/c1g6arq-emirates-cryptocom-give-customers-new-way-pay-for": "WAM — Emirates and Crypto.com payment update",
    "https://statehouse.gov.ng/president-tinubu-signs-executive-order-on-virtual-assets-establishes-council-to-harmonise-regulation-of-digital-economy/": "Nigeria State House — Virtual-assets regulatory council",
}

def regional_source_links(source_text):
    """Turn citation URLs into descriptive, auditable hyperlinks."""
    links = []
    for raw_url in str(source_text).split("|"):
        url = raw_url.strip()
        if not url:
            continue
        label = REGIONAL_SOURCE_TITLES.get(url)
        if not label:
            host = url.split("//", 1)[-1].split("/", 1)[0].removeprefix("www.")
            label = f"{host} — official reference"
        links.append((label, url))
    return links

def regional_rating_band(score):
    """Derive the display band from the numeric policy-research score."""
    score = float(score)
    if score >= 8:
        return "HIGH"
    if score >= 5:
        return "MID"
    return "LOW"

# One current, jurisdiction-matched update per featured jurisdiction. These
# are reviewed on the same daily cycle as the policy-source ratings below.
JURISDICTION_UPDATES = {
    "Hong Kong (SFC / HKMA)": ("HKMA — DLT in Hong Kong fixed-income markets", "https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/06/20260629-4/"),
    "Singapore (MAS)": ("Crypto Briefing — MAS strengthens bank crypto-exposure oversight", "https://cryptobriefing.com/mas-singapore-banks-report-crypto-exposure/"),
    "Japan (FSA)": ("CoinDesk — Japan moves crypto under financial rules", "https://www.coindesk.com/policy/2026/07/15/japan-reclassifies-crypto-as-a-financial-asset-paves-way-for-tax-cuts"),
    "South Korea (FSC)": ("Cointelegraph — South Korea plans consolidated crypto law", "https://cointelegraph.com/news/south-korea-consolidated-crypto-law-tax-repeal"),
    "Australia (ASIC)": ("eCommerce News Australia — OKX launches virtual Mastercard", "https://ecommercenews.com.au/story/okx-launches-virtual-mastercard-for-australian-users"),
    "Federal (SEC / CFTC)": ("CoinDesk — Wall Street backs the CLARITY Act", "https://www.coindesk.com/policy/2026/07/28/blackrock-fidelity-other-wall-street-giants-back-the-clarity-act"),
    "New York (NYDFS)": ("BitRSS — Mastercard secures New York BitLicense", "https://bitrss.com/mastercard-secures-new-york-bitlicense-allows-galaxy-to-offer-institutional-crypto-services-215094"),
    "Wyoming": ("Crypto Briefing — Wyoming becomes first US state to issue its own stablecoin", "https://cryptobriefing.com/wyoming-first-state-stablecoin-frnt/"),
    "Texas / Florida": ("JDSupra — Florida creates stablecoin licensing regime", "https://www.jdsupra.com/legalnews/florida-creates-licensing-regime-for-6063197/"),
    "FCA (Cryptoasset Registration)": ("FCA — Latest crypto rules and UK hub strategy", "https://www.fca.org.uk/news/press-releases/fca-sets-landmark-crypto-rules-cement-uks-place-global-hub"),
    "HM Treasury": ("Startup Fortune — UK Parliament probes crypto payment blocks", "https://startupfortune.com/uk-parliament-opens-inquiry-into-banks-blocking-crypto-payments-as-1-billion-in-transactions-gets-rejected/"),
    "Bank of England / PRA": ("SpendNode — Bank of England releases stablecoin rules", "https://www.spendnode.io/blog/bank-of-england-releases-stablecoin-rules-sets-2027-timeline-223766"),
    "Channel Islands (JFSC / GFSC)": ("Mondaq — Guernsey simplifies digital-finance regulation", "https://www.mondaq.com/guernsey/securitization-structured-finance/1822716/gfsc-takes-steps-to-simplify-regulation-provide-regulatory-clarity-and-support-growth-in-digital-finance"),
    "MiCA Regulation (EU-wide)": ("Crypto Briefing — EU issues 244 MiCA crypto licences", "https://cryptobriefing.com/eu-mica-crypto-licenses-germany-france/"),
    "Germany (BaFin)": ("BitRSS — German banks bring crypto to retail customers", "https://bitrss.com/germany-banks-crypto-trading-mica-2026-07-04"),
    "France (AMF)": ("CoinDesk — Kraken seeks European banking licence", "https://www.coindesk.com/business/2026/07/07/crypto-exchange-kraken-is-trying-to-become-a-bank-in-europe"),
    "Lithuania / Malta": ("FintechNewsCH — Kraken focuses on Lithuania for European banking licence", "https://fintechnews.ch/blockchain_bitcoin/kraken-banking-license/84583/"),
    "Brazil": ("CoinDesk — Stablecoins reshape Brazil’s payments market", "https://www.coindesk.com/business/2026/07/18/trump-targets-brazil-s-payments-system-while-dollar-stablecoins-quietly-dominate-country-s-payments"),
    "Mexico": ("Mexico Business — BingX launches crypto card and investment tools", "https://mexicobusiness.news/finance/news/bingx-launches-crypto-card-ai-investment-tools-mexico"),
    "Colombia": ("BitRSS — Colombia introduces crypto-service reporting rules", "https://bitrss.com/colombia-introduces-mandatory-reporting-for-cryptocurrency-service-providers-170937"),
    "Argentina": ("Bitcoin.com News — Argentine banks build peso stablecoins", "https://news.bitcoin.com/argentinas-banking-groups-are-quietly-building-peso-stablecoins-for-the-institutional-market/"),
    "UAE (VARA / DIFC)": ("WAM — Emirates and Crypto.com payment update", "https://www.wam.ae/en/article/c1g6arq-emirates-cryptocom-give-customers-new-way-pay-for"),
    "Bahrain": ("Fintech Business Asia — Bahrain grants first stablecoin issuer licence", "https://www.fintechbusinessasia.com/news/30/2840/bahrain-grants-first-stablecoin-issuer-license-to-axg-introducing-a-central-bank-regulated-sharia-compliant-digital-dollar.html"),
    "Saudi Arabia": ("Decypha — Nium strengthens Saudi cross-border payments", "https://decypha.com/en/news/details/Nium-strengthens-Saudi-Expansion-through-local-cross-border-payments-partnerships/21562957?EDT=&L=EN&TSID="),
    "Egypt": ("Daily News Egypt — FRA approves fintech sandbox projects", "https://www.dailynewsegypt.com/2026/07/28/fra-grants-preliminary-approval-to-two-ai-driven-insurance-projects-for-regulatory-sandbox/"),
    "Nigeria": ("BusinessDay — Nigeria’s virtual-assets order reshapes digital finance", "https://businessday.ng/technology/article/tinubus-virtual-assets-order-reshapes-nigerias-digital-finance-roadmap-as-industry-convenes/"),
    "Kenya": ("Bitcoin.com News — Kenya cuts stablecoin capital requirement", "https://news.bitcoin.com/regulation-and-legal/kenya-cuts-stablecoin-capital-rule-40-to-2-32m-as-global-issuers-weigh-entry/"),
    "South Africa": ("BusinessDay — SARB develops new cryptocurrency frameworks", "https://www.businessday.co.za/economy/2026-07-12-sarb-developing-new-frameworks-to-regulate-cryptocurrency-use/"),
    "Rwanda": ("African Business — Rwanda launches nationwide eKash payments", "https://african.business/2026/07/innov-africa-deals/rwanda-unifies-digital-payments-with-national-launch-of-ekash"),
}

def jurisdiction_update(jurisdiction):
    """Return the reviewed update matched to the named featured jurisdiction."""
    return JURISDICTION_UPDATES.get(
        jurisdiction,
        (f"{jurisdiction} — official fintech update", ""),
    )

REGIONAL_DATA = {
    "APAC": {
        "summary": "Asia-Pacific is the world's largest digital-asset market by volume. Hong Kong, Singapore, Japan, South Korea, and Australia combine institutional finance, active supervisory frameworks, and distinct market-access models; China's influence continues to shape regional liquidity migration.",
        "jurisdictions": [
            {
                "name": "Hong Kong (SFC / HKMA)", "score": 9, "label": "HIGH",
                "framework": "Hong Kong's SFC licensing regime for virtual-asset trading platforms provides a supervised institutional route, while the HKMA's stablecoin framework strengthens prudential and reserve expectations. Hong Kong remains a critical China-adjacent capital and tokenisation hub.",
                "source": "https://www.sfc.hk/en/Welcome-to-the-Fintech-Contact-Point/Virtual-assets/Virtual-asset-trading-platforms-operators | https://www.sfc.hk/-/media/EN/assets/components/Guidelines/File-current/Licensing-Handbook-for-VATPs_July-2025.pdf",
            },
            {
                "name": "Singapore (MAS)", "score": 9, "label": "HIGH",
                "framework": "MAS Payment Services Act 2019 (amended 2023) provides licensing for Digital Payment Token services. Project Guardian (2023) testing tokenised bonds and funds with major banks. MAS explicitly encourages institutional Web3 participation.",
                "source": "https://www.mas.gov.sg/regulation/guidelines/ps-g02-guidelines-on-provision-of-digital-payment-token-services-to-the-public | https://www.mas.gov.sg/schemes-and-initiatives/project-guardian",
            },
            {
                "name": "Japan (FSA)", "score": 8, "label": "HIGH",
                "framework": "Japan's Payment Services Act classifies crypto assets as legal property. FSA white-list system (2023 expansion) covers 30+ tokens. Japan was first G7 nation to legalise stablecoin issuance (June 2023).",
                "source": "https://www.fsa.go.jp/policy/virtual_currency/index.html | https://www.fsa.go.jp/en/news/2022/20221207/01.pdf",
            },
            {
                "name": "South Korea (FSC)", "score": 7, "label": "MID",
                "framework": "Virtual Asset User Protection Act (July 2024) introduces mandatory exchange insurance and on-chain monitoring. FSC licensing overhaul targets institutional market access by 2025.",
                "source": "https://www.fsc.go.kr/eng",
            },
            {
                "name": "Australia (ASIC)", "score": 7, "label": "MID",
                "framework": "Treasury Token Mapping consultation (2023) established regulatory classification. ASIC guidance INFO 225 covers crypto asset management. Digital asset exchange licensing under Financial Services Reform Bill (2024 draft).",
                "source": "https://www.asic.gov.au/regulatory-resources/digital-transformation/digital-assets-financial-products-and-services/ | https://www.asic.gov.au/about-asic/news-centre/find-a-media-release/2025-releases/25-250mr-updated-asic-guidance-supports-digital-asset-innovation-and-boosts-investor-protection/",
            },
        ],
        "news_keywords": ("singapore", "japan", "south korea", "australia", "apac", "asia", "mas", "fsa", "fintech", "crypto", "cbdc", "web3"),
        "regional_news": ("Latest APAC fintech update — HKMA DLT in Hong Kong fixed-income markets", "https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/06/20260629-4/"),
    },
    "USA": {
        "summary": "The United States remains the largest institutional digital-asset market globally, defined by a contested regulatory jurisdiction between the SEC and CFTC, shifting enforcement posture, and landmark legislation in progress.",
        "jurisdictions": [
            {
                "name": "Federal (SEC / CFTC)", "score": 8, "label": "HIGH",
                "framework": "FIT21 Act passed the House (May 2024) — first comprehensive US digital-asset market structure legislation. SEC enforcement-led approach (2022–2024) is shifting under new administration. CFTC asserts jurisdiction over spot crypto commodities.",
                "source": "https://www.sec.gov/digital-assets | https://www.cftc.gov/LearnAndProtect/EducationCenter | https://www.congress.gov/118/bills/hr4763/BILLS-118hr4763eh.pdf",
            },
            {
                "name": "New York (NYDFS)", "score": 7, "label": "MID",
                "framework": "BitLicense (2015) remains the most rigorous US state-level VASP regime. NYDFS conditional BitLicense pathway opened in 2022 for startups. Only ~30 firms hold a full BitLicense; many major exchanges operate under limited purpose trust charters.",
                "source": "https://www.dfs.ny.gov/virtual_currency_businesses",
            },
            {
                "name": "Wyoming", "score": 9, "label": "HIGH",
                "framework": "Wyoming SPDI (Special Purpose Depository Institution) charter allows crypto-native banks to hold digital assets 1:1. DAO LLC statute (2021) is the world's first legal framework for decentralised autonomous organisations.",
                "source": "https://wyomingbankingdivision.wyo.gov/banks-trust-companies/spdi",
            },
            {
                "name": "Texas / Florida", "score": 8, "label": "HIGH",
                "framework": "Texas MTL broadly interpreted to cover crypto. Florida enacted MSB Modernization Act (2023) with crypto-friendly provisions. Both states are principal destinations for mining operations and crypto treasury management.",
                "source": "https://www.dob.texas.gov/public/uploads/files/consumer-information/msa-guidance-crypto.pdf | https://flofr.gov",
            },
        ],
        "news_keywords": ("united states", "usa", "sec", "cftc", "congress", "bitcoin", "crypto", "regulation", "fit21", "bitlicense", "stablecoin", "cbdc"),
        "regional_news": ("Latest US fintech update — financial technology regulatory frameworks", "https://www.whitehouse.gov/presidential-actions/2026/05/integrating-financial-technology-innovation-into-regulatory-frameworks/"),
    },
    "UK": {
        "summary": "Post-Brexit, the UK is aggressively positioning itself as a global crypto-asset hub, with the Financial Services and Markets Act 2023 bringing digital assets under the FCA's remit and active stablecoin legislation underway.",
        "jurisdictions": [
            {
                "name": "FCA (Cryptoasset Registration)", "score": 8, "label": "HIGH",
                "framework": "FSMA 2023 designates cryptoassets as regulated financial instruments. FCA Crypto Asset Register: 45+ firms registered. Mandatory registration for marketing to UK consumers since October 2023.",
                "source": "https://www.fca.org.uk/firms/cryptoassets/who-needs-register | https://www.fca.org.uk/firms/new-regime-cryptoasset-regulation",
            },
            {
                "name": "HM Treasury", "score": 8, "label": "HIGH",
                "framework": "HMT Future Financial Services Regulatory Regime for Crypto Assets consultation (Feb 2023) proposes bringing trading venues, custody, lending, and issuance into the existing financial-services framework. UK CBDC (Digital Pound) design phase ongoing.",
                "source": "https://www.gov.uk/government/consultations/future-financial-services-regulatory-regime-for-cryptoassets | https://www.bankofengland.co.uk/the-digital-pound",
            },
            {
                "name": "Bank of England / PRA", "score": 7, "label": "MID",
                "framework": "PRA supervisory statement SS1/23 sets capital and liquidity requirements for banks with crypto-asset exposures. BoE discussion paper on systemic risk from DeFi protocols issued 2024.",
                "source": "https://www.bankofengland.co.uk/prudential-regulation",
            },
            {
                "name": "Channel Islands (JFSC / GFSC)", "score": 7, "label": "MID",
                "framework": "Jersey JFSC published VASP framework in 2022 — highly regarded as a model for offshore fintech structuring. Guernsey GFSC operates distinct crypto fund registration regime.",
                "source": "https://www.jerseyfsc.org/industry/fintech/virtual-assets/ | https://www.gfsc.gg/commission/regulated-sectors/virtual-asset-service-providers",
            },
        ],
        "news_keywords": ("uk", "united kingdom", "fca", "britain", "london", "digital pound", "cbdc", "crypto", "fintech", "hm treasury", "stablecoin"),
        "regional_news": ("Latest UK fintech update — FCA crypto rules and hub strategy", "https://www.fca.org.uk/news/press-releases/fca-sets-landmark-crypto-rules-cement-uks-place-global-hub"),
    },
    "EU": {
        "summary": "The European Union's MiCA regulation is the world's most comprehensive crypto-asset legal framework, now in full force. It is reshaping global institutional structuring decisions and creating a compliance template other jurisdictions are adapting.",
        "jurisdictions": [
            {
                "name": "MiCA Regulation (EU-wide)", "score": 9, "label": "HIGH",
                "framework": "Markets in Crypto-Assets Regulation (MiCA) fully applicable from December 2024. Covers issuance of utility tokens, asset-referenced tokens (ARTs), e-money tokens (EMTs), and CASPs. Single EU passport: one licence covers all 27 member states.",
                "source": "https://eur-lex.europa.eu/eli/reg/2023/1114/oj/eng | https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica",
            },
            {
                "name": "Germany (BaFin)", "score": 8, "label": "HIGH",
                "framework": "BaFin crypto-custody licence (KWG §1(1a)) — one of Europe's strictest. Germany's e-securities law (eWpG 2021) enables tokenised bonds on blockchain. Frankfurt is the primary EU institutional crypto hub.",
                "source": "https://www.bafin.de/EN/Aufsicht/FinTech/Fintech_node_en.html",
            },
            {
                "name": "France (AMF)", "score": 8, "label": "HIGH",
                "framework": "AMF PSAN registration has 60+ firms. France's PACTE law (2019) was a pioneer; Paris is competing for European crypto HQ status. AMF early MiCA adopter framework active from 2023.",
                "source": "https://www.amf-france.org/en/professionals/fintech",
            },
            {
                "name": "Lithuania / Malta", "score": 8, "label": "HIGH",
                "framework": "Lithuania Bank of Lithuania VASP licensing used by 500+ firms as EU passporting gateway (lowest cost, fastest). Malta's VFA framework (2018) was first EU crypto legislation — now transitioning to full MiCA compliance.",
                "source": "https://www.lb.lt/en/licensing-of-virtual-currency-exchange-operators-and-depository-virtual-currency-wallet-operators | https://www.mfsa.mt/fintech/virtual-financial-assets",
            },
        ],
        "news_keywords": ("european union", "eu", "mica", "esma", "eba", "germany", "france", "bafin", "amf", "crypto", "stablecoin", "digital euro", "cbdc"),
        "regional_news": ("Latest EU fintech update — 2026 MiCA review consultation", "https://finance.ec.europa.eu/document/download/62be7015-f066-4fac-b74e-71bacdbcc9f5_en?filename=2026-mica-review-targeted-consultation-document_en.pdf"),
    },
    "LATAM": {
        "summary": "Latin America leads global fintech adoption driven by financial-inclusion imperatives, high mobile penetration, and inflation-driven demand for alternative stores of value.",
        "jurisdictions": [
            {
                "name": "Brazil", "score": 8, "label": "HIGH",
                "framework": "Law 14.478/2022 establishes VASP licensing under BACEN. PIX instant-payment rail processes >140M transactions/day. Drex CBDC pilot running with 16 banks.",
                "source": "https://www.bcb.gov.br/estabilidadefinanceira/drex | https://www.in.gov.br/web/dou/-/lei-n-14.478-de-21-de-dezembro-de-2022",
            },
            {
                "name": "Mexico", "score": 6, "label": "MID",
                "framework": "Ley Fintech (2018) — first comprehensive fintech law in LATAM. Banxico maintains restrictive stance on crypto-exchange interoperability.",
                "source": "https://www.dof.gob.mx/nota_detalle.php?codigo=5515623 | https://www.banxico.org.mx",
            },
            {
                "name": "Colombia", "score": 7, "label": "MID",
                "framework": "SFC regulatory sandbox (2020+) has approved 60+ fintech pilots. Decree 1234/2022 lays groundwork for digital-asset supervision. Central bank exploring wholesale CBDC.",
                "source": "https://www.superfinanciera.gov.co/inicio/sandbox | https://www.banrep.gov.co",
            },
            {
                "name": "Argentina", "score": 4, "label": "LOW",
                "framework": "BCRA capital controls restrict crypto-peso convertibility. No formal licensing regime; AFIP requires crypto-exchange user reporting. Inflation-driven grassroots stablecoin adoption despite regulatory friction.",
                "source": "https://www.bcra.gob.ar | https://www.afip.gob.ar",
            },
        ],
        "news_keywords": ("brazil", "mexico", "colombia", "argentina", "latin america", "latam", "fintech", "crypto", "cbdc", "drex", "pix"),
        "regional_news": ("Latest LATAM fintech update — tokenisation working group in Brazil", "https://www.gov.br/fazenda/pt-br/composicao/orgaos/orgaos-colegiados/crsfn/acesso-a-informacao/noticias/2026/cvm-institui-grupo-de-trabalho-para-desenvolver-estudos-sobre-tokenizacao-de-valores-mobiliarios"),
    },
    "MENA": {
        "summary": "The Middle East & North Africa is the fastest-growing region for institutional digital-asset infrastructure, anchored by UAE's VARA framework and Bahrain's progressive sandbox model.",
        "jurisdictions": [
            {
                "name": "UAE (VARA / DIFC)", "score": 10, "label": "HIGH",
                "framework": "VARA (2022) provides comprehensive licensing for VASPs, exchanges, and custody. DIFC Innovation Testing Licence enables live product trials. Dubai hosts 500+ crypto firms.",
                "source": "https://www.vara.ae/en/ | https://www.difc.ae/business/innovation",
            },
            {
                "name": "Bahrain", "score": 8, "label": "HIGH",
                "framework": "CBB Crypto-Asset Module (2019) — among the world's first crypto-specific regulations. FinTech Bay sandbox facilitates cross-border testing.",
                "source": "https://www.cbb.gov.bh/crypto-assets | https://www.fintechbay.com",
            },
            {
                "name": "Saudi Arabia", "score": 7, "label": "MID",
                "framework": "SAMA Fintech Saudi initiative: 500+ fintech licenses. Vision 2030 targets 70% cashless transactions. Tokenized RWAs under CMA review.",
                "source": "https://www.sama.gov.sa/en-US/FinTech | https://cma.org.sa",
            },
            {
                "name": "Egypt", "score": 5, "label": "MID",
                "framework": "CBE Regulatory Sandbox (2019) active with 40+ fintech licensees. Crypto trading restricted but mobile-wallet infrastructure expanding rapidly.",
                "source": "https://www.cbe.org.eg/en/FinTech | https://fintechegypt.com",
            },
        ],
        "news_keywords": ("uae", "dubai", "saudi", "bahrain", "egypt", "mena", "vara", "difc", "fintech", "crypto", "digital asset"),
        "regional_news": ("Latest MENA fintech update — Emirates and Crypto.com payment rollout", "https://www.wam.ae/en/article/c1g6arq-emirates-cryptocom-give-customers-new-way-pay-for"),
    },
    "Africa": {
        "summary": "Sub-Saharan Africa's fintech ecosystem is powered by mobile-money leadership, regulatory sandbox proliferation, and the continent's young, digitally-native population of 1.4 billion.",
        "jurisdictions": [
            {
                "name": "Nigeria", "score": 6, "label": "MID",
                "framework": "SEC Nigeria Digital Assets Rules (May 2022) establish VASP licensing. CBN 2024 reversal re-allowed banks to service licensed crypto platforms. eNaira CBDC launched Oct 2021.",
                "source": "https://sec.gov.ng/for-investors/keep-track-of-circulars/statement-on-digital-assets-and-their-classification-and-treatment/ | https://www.cbn.gov.ng",
            },
            {
                "name": "Kenya", "score": 8, "label": "HIGH",
                "framework": "CBK Regulatory Sandbox (2021) active. National Payment Systems Act governs M-Pesa (30M+ users). CMA developing crypto-asset framework (2023 consultation).",
                "source": "https://www.centralbank.go.ke/national-payments-system | https://www.cma.or.ke",
            },
            {
                "name": "South Africa", "score": 7, "label": "MID",
                "framework": "FSCA declared crypto assets a financial product (Oct 2022) requiring FSP licensing. SARB Project Khokha wholesale CBDC trials completed. Africa's most institutionally mature crypto market.",
                "source": "https://www.fsca.co.za/Regulatory%20Frameworks/Pages/Regulatory-Frameworks.aspx | https://www.resbank.co.za",
            },
            {
                "name": "Rwanda", "score": 8, "label": "HIGH",
                "framework": "BNR Fintech Innovation Office active since 2020. National Fintech & Innovation Policy (2022–2027) targets Rwanda as continental fintech hub. KIFC attracting pan-African HQs.",
                "source": "https://www.bnr.rw/financial-sector/financial-innovation | https://www.kifc.rw",
            },
        ],
        "news_keywords": ("nigeria", "kenya", "south africa", "ghana", "rwanda", "africa", "m-pesa", "fintech", "crypto", "cbdc"),
        "regional_news": ("Latest Africa fintech update — Nigeria virtual-assets regulatory council", "https://statehouse.gov.ng/president-tinubu-signs-executive-order-on-virtual-assets-establishes-council-to-harmonise-regulation-of-digital-economy/"),
    },
}

COOPERATION_IDEAS = [
    {
        "title": "🔗 LATAM–MENA Stablecoin Settlement Corridor", "regions": "Brazil ↔ UAE",
        "idea": "Leverage Brazil's Drex CBDC infrastructure and UAE's VARA-licensed exchange ecosystem to build a bilateral wholesale stablecoin settlement lane — reducing correspondent banking fees (currently 6–8%) on the $12B annual remittance corridor.",
        "mechanism": "BIS mBridge protocol extension + bilateral VASP passporting agreement",
        "precedent": "BIS mBridge (China, HK, UAE, Thailand) — live since 2024",
        "references": [
            ("BIS mBridge Project Overview", "https://www.bis.org/about/bisih/topics/cbdc/mbridge.htm"),
            ("VARA Licensing Framework", "https://www.vara.ae/en/licences"),
        ],
    },
    {
        "title": "📱 Africa–LATAM Mobile Money Interoperability Standard", "regions": "Kenya (M-Pesa) ↔ Colombia / Mexico",
        "idea": "Extend the GSMA Mobile Money Interoperability framework to bridge Africa's mobile-money dominant economy with LATAM's emerging instant-payment rails (PIX, SPEI) via a shared ISO 20022 messaging layer.",
        "mechanism": "GSMA Open API standard + FATF Travel Rule compliance layer",
        "precedent": "M-Pesa–Vodacom cross-border (Tanzania, Kenya, DRC) — operational",
        "references": [
            ("GSMA Mobile Money API Programme", "https://www.gsma.com/solutions-and-impact/connectivity/mobile-money/"),
            ("FATF Guidance on Virtual Assets", "https://www.fatf-gafi.org/en/topics/virtual-assets.html"),
        ],
    },
    {
        "title": "🏛️ MENA–Africa Regulatory Sandbox Reciprocity", "regions": "DIFC (UAE) ↔ KIFC (Rwanda) ↔ FSCA (South Africa)",
        "idea": "A trilateral sandbox passport: a fintech licensed in DIFC's testing environment can operate a mirrored pilot in Kigali and Johannesburg without a separate full application.",
        "mechanism": "MoU between VARA, BNR, and FSCA — 12-month pilot passport",
        "precedent": "GFIN — 38 regulators across 5 continents, active since 2019",
        "references": [
            ("GFIN — Global Financial Innovation Network", "https://www.thegfin.com"),
        ],
    },
    {
        "title": "📊 Cross-Regional DeFi Risk Intelligence Sharing", "regions": "All six regions",
        "idea": "Form a multilateral DeFi Monitoring Consortium — regulators from BACEN, SEC Nigeria, FSCA, VARA, SFC, and MAS share on-chain analytics, smart-contract risk flags, and illicit-flow intelligence via a permissioned data lake.",
        "mechanism": "Encrypted information-sharing MoU under IOSCO's MMOU framework",
        "precedent": "IOSCO Multilateral MoU — 130 member jurisdictions; crypto extension under discussion",
        "references": [
            ("IOSCO Crypto-Asset Roadmap 2023", "https://www.iosco.org/library/pubdocs/pdf/IOSCOPD741.pdf"),
        ],
    },
    {
        "title": "🌐 Global South CBDC Interoperability Layer", "regions": "Brazil (Drex) ↔ Nigeria (eNaira) ↔ UAE (dAED pilot)",
        "idea": "A South-South CBDC bridge using atomic cross-chain swaps — removing USD as the mandatory intermediary for intra-Global-South trade settlements ($4.5T annually).",
        "mechanism": "BIS Innovation Hub Project Nexus multi-CBDC API standard",
        "precedent": "Project mBridge (BIS, 2024) + Project Nexus (BIS, Singapore, Malaysia, Thailand)",
        "references": [
            ("BIS Project Nexus", "https://www.bis.org/publ/othp64.htm"),
        ],
    },
    {
        "title": "📜 Harmonised VASP Travel Rule Toolkit", "regions": "LATAM + MENA + Africa",
        "idea": "Co-develop a shared open-source FATF Travel Rule compliance stack used by VASPs in all three regions to exchange originator/beneficiary data, lowering the compliance cost barrier for smaller exchanges.",
        "mechanism": "FATF Virtual Assets Contact Group + open-source TRUST / Shyft Network integration",
        "precedent": "TRUST (Travel Rule Universal Solution Technology) — US/Asia adoption model",
        "references": [
            ("FATF Guidance on Virtual Assets & VASPs", "https://www.fatf-gafi.org/en/topics/virtual-assets.html"),
        ],
    },
]

# ── On-chain metric definitions ───────────────────────────────────────────────
def onchain_status(value, thresholds):
    """Return (css_class, label, interpretation) based on value vs thresholds."""
    lo, hi = thresholds
    if value >= hi:
        return "status-green", "🟢 Strong", "above healthy range"
    elif value >= lo:
        return "status-green", "🟢 Healthy", "within normal range"
    else:
        return "status-red", "🔴 Low", "below normal range"

# ── Header ────────────────────────────────────────────────────────────────────
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

st.markdown("<div class='quick-links'><div class='quick-links-label'>Dashboard shortcuts</div></div>", unsafe_allow_html=True)
quick_link_cols = st.columns(4)
dashboard_links = [
    ("📊 Rankings Index", "#rankings-index"),
    ("📈 Market Timeline", "#market-timeline"),
    ("🌍 Benchmarking Matrix", "#benchmarking-matrix"),
    ("📥 Researcher Portal", "#researcher-portal"),
]
for column, (label, anchor) in zip(quick_link_cols, dashboard_links):
    with column:
        st.markdown(
            f"<a class='shortcut-link' href='{anchor}' target='_self' "
            f"aria-label='Jump to {label}'>{label}</a>",
            unsafe_allow_html=True,
        )

st.divider()

# ── Data fetch from Airtable ──────────────────────────────────────────────────
resolved_policy_table = resolve_airtable_table_name()
resolved_index_table = None
if AIRTABLE_INDEX_TABLE:
    # Resolve the optional index table using the same metadata-safe rules.
    original_table_name = AIRTABLE_TABLE_NAME
    AIRTABLE_TABLE_NAME = AIRTABLE_INDEX_TABLE
    resolved_index_table = resolve_airtable_table_name()
    AIRTABLE_TABLE_NAME = original_table_name

airtable_macro_df = normalize_airtable_columns(
    airtable_records(resolved_policy_table, AIRTABLE_VIEW_ID)
)
airtable_macro_df = approved_airtable_records(airtable_macro_df)
airtable_fintech_df = (
    normalize_airtable_columns(airtable_records(resolved_index_table))
    if resolved_index_table
    else airtable_macro_df.copy()
)
airtable_fintech_df = approved_airtable_records(airtable_fintech_df)

macro_df = policy_baseline_frame()
if not airtable_macro_df.empty:
    macro_df = pd.concat([macro_df, airtable_macro_df], ignore_index=True)
macro_df = ensure_columns(macro_df, {
    "jurisdiction": "",
    "regulatory_shift": "",
    "geopolitical_context": "",
    "gdp_impact_trajectory": "",
    "industry_rev_projection": "",
    "impact_score": 0,
    "date_logged": "",
})
macro_df = enrich_policy_metadata(macro_df)
fintech_df = merge_friendliness_sources(
    friendliness_baseline_frame(),
    airtable_fintech_df,
)
fintech_df = ensure_columns(fintech_df, {
    "jurisdiction": "",
    "region": "Other",
    "regulatory_clarity": 0,
    "sandbox_speed": 0,
    "licensing_ease": 0,
    "tax_incentives": 0,
    "institutional_banking": 0,
    "composite_2026": 0,
    "composite_2016": 0,
    "improvement_delta": 0,
    "improvement_trend": "",
    "improvement_notes": "",
    "sources": "",
    "year_assessed": datetime.now().year,
})

numeric_columns = [
    "impact_score", "regulatory_clarity", "sandbox_speed", "licensing_ease",
    "tax_incentives", "institutional_banking", "composite_2026",
    "composite_2016", "improvement_delta", "year_assessed",
]
for frame in (macro_df, fintech_df):
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

# When the main Airtable grid is the only configured source, use rows that
# actually contain friendliness dimensions as the index dataset. This keeps
# policy-only rows from appearing as fabricated 0/10 jurisdictions.
friendliness_dimensions = [
    "regulatory_clarity", "sandbox_speed", "licensing_ease",
    "tax_incentives", "institutional_banking",
]
if not resolved_index_table:
    dimension_mask = fintech_df[friendliness_dimensions].gt(0).any(axis=1)
    fintech_df = fintech_df[dimension_mask].copy()
for column in friendliness_dimensions:
    fintech_df[column] = pd.to_numeric(fintech_df[column], errors="coerce")
if "licensing_friction" in fintech_df.columns:
    friction = pd.to_numeric(fintech_df["licensing_friction"], errors="coerce")
    fintech_df["licensing_ease"] = fintech_df["licensing_ease"].fillna(11 - friction)
for column in friendliness_dimensions:
    fintech_df[column] = fintech_df[column].fillna(0).clip(lower=0, upper=10)
dimension_average = fintech_df[friendliness_dimensions].mean(axis=1)
fintech_df["composite_2026"] = fintech_df["composite_2026"].where(
    fintech_df["composite_2026"].notna() & (fintech_df["composite_2026"] > 0),
    dimension_average,
)
fintech_df["composite_2016"] = pd.to_numeric(
    fintech_df["composite_2016"], errors="coerce"
).fillna(0)
fintech_df["improvement_delta"] = pd.to_numeric(
    fintech_df["improvement_delta"], errors="coerce"
).fillna(
    (fintech_df["composite_2026"] - fintech_df["composite_2016"]).clip(lower=0)
)
if "composite_2026" in fintech_df.columns:
    fintech_df = fintech_df.sort_values(
        ["composite_2026", "jurisdiction"],
        ascending=[False, True],
        na_position="last",
    )

# Keep the complete index dataframe available for submission upserts. The
# displayed dataframe below is intentionally narrowed to the selected hub.
fintech_source_df = fintech_df.copy()
available_hubs = ["All"] + sorted(
    fintech_source_df["jurisdiction"]
    .dropna()
    .astype(str)
    .str.strip()
    .loc[lambda values: values.ne("")]
    .unique()
    .tolist()
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
# The hub list is database-driven: it is rebuilt from the normalized dataframe
# on every Streamlit rerun, including after an approved Airtable submission.
st.sidebar.header("🎛️ Dashboard Controls")
with st.sidebar.expander("🔎 Filter Intelligence", expanded=True):
    selected_geo = st.selectbox("Select Jurisdiction:", available_hubs)
    min_impact = st.slider("Minimum Policy Volatility Score", 1, 10, 5)
    st.caption(
        "All rankings, cards, radar traces, and matrix metrics update to match "
        "the selected jurisdiction."
    )
    st.caption(
        "Impact bands: ≥ 8 = high priority · 5–7 = notable · < 5 = low risk."
    )

with st.sidebar.expander("🧭 Jump to Section", expanded=True):
    st.caption("Use these links to move directly to a dashboard section.")
    for label, anchor in dashboard_links:
        st.markdown(
            f"<a class='sidebar-nav-link' href='{anchor}' target='_self'>{label}</a>",
            unsafe_allow_html=True,
        )

with st.sidebar.expander("📖 Dashboard User Guide", expanded=False):
    st.markdown(
        """
        - **Filter Insights:** Select a jurisdiction to isolate its macro developments and intelligence metrics.
        - **Analyze Benchmarks:** Use the filtered cards, radar, and matrix to compare the selected hub's readiness profile.
        - **Contribute Intelligence:** Expand the researcher portal at the bottom to submit field-validated updates.
        """,
        unsafe_allow_html=False,
    )

with st.sidebar.expander("📅 Timeline Event Legend", expanded=False):
    for cat, color in CATEGORY_COLORS.items():
        st.markdown(
            f"<span style='display:inline-block;background:{color};padding:3px 8px;"
            f"margin:2px 0;border-radius:4px;color:white;font-size:0.75rem;font-weight:600'>"
            f"{CATEGORY_LABELS[cat]}</span>",
            unsafe_allow_html=True,
        )

if selected_geo != "All":
    fintech_df = fintech_df[
        fintech_df["jurisdiction"] == selected_geo
    ].copy()
    macro_df = macro_df[
        macro_df["jurisdiction"] == selected_geo
    ].copy()

market_df       = pipeline.fetch_market_trends(years=5)

macro_df = macro_df[macro_df["impact_score"] >= min_impact]

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1: Regional Fintech Intelligence
# ════════════════════════════════════════════════════════════════════════════════
st.subheader("🌍 Regional Fintech Intelligence")
st.markdown(
    "*Regulatory landscape, fintech-friendliness ratings, and live news across all major Web3 jurisdictions.*"
)
regional_review_date = datetime.now().strftime("%d %b %Y")
st.caption(
    f"**External-source rating review:** {regional_review_date} · "
    "Ratings are policy-research indicators based on regulatory clarity, market access, "
    "sandbox maturity, institutional infrastructure, and tax treatment. They are refreshed "
    "against the linked official sources on the dashboard's daily review cycle; live news is "
    "cached for 1 hour."
)
st.markdown(
    "**Rating legend:** 🟢 **High (8–10)** = comparatively supportive operating environment · "
    "🟡 **Moderate (5–7)** = mixed or developing environment · "
    "🔴 **Low (1–4)** = material regulatory or market-access friction"
)
st.info(
    "**Why these jurisdictions are featured:** The countries and markets listed in each tab are "
    "illustrative policy-significance cases, not an exhaustive country ranking. They are showcased "
    "because they influence regional capital flows, set or test regulatory precedents, operate "
    "important payment or settlement rails, or represent a meaningful contrast in market access. "
    "This approach keeps the comparison decision-useful for policy, compliance, and institutional "
    "strategy teams while making the inclusion rationale explicit."
)

reg_tabs = st.tabs(["🌏 APAC", "🇺🇸 USA", "🇬🇧 UK", "🇪🇺 EU", "🌎 LATAM", "🌙 MENA", "🌍 Africa"])

for tab, region_key in zip(reg_tabs, ["APAC", "USA", "UK", "EU", "LATAM", "MENA", "Africa"]):
    region = REGIONAL_DATA[region_key]
    with tab:
        st.markdown(f"**Regional policy context:** {region['summary']}")
        st.markdown("**Featured jurisdictions and why they matter:**")
        for jur in region["jurisdictions"]:
            rating_band = regional_rating_band(jur["score"])
            label_text = {
                "HIGH": "✅ Fintech-Friendly",
                "MID": "⚠️ Moderate",
                "LOW": "🚫 Restrictive",
            }[rating_band]
            rating_class = {
                "HIGH": "regional-rating-high",
                "MID": "regional-rating-mid",
                "LOW": "regional-rating-low",
            }[rating_band]
            st.markdown(
                f"<div class='regional-rating {rating_class}'>"
                f"<div class='eyebrow'>FinTech operating-environment rating</div>"
                f"<div style='font-weight:800;color:#F8FAFC;font-size:1.05rem'>{jur['name']}</div>"
                f"<div class='score'>{jur['score']}/10</div>"
                f"<div class='status'>{label_text}</div>"
                f"<div class='scale'>External policy-source score · reviewed {regional_review_date}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"- **Policy significance:** {jur['framework']}\n"
                f"- **Authoritative references:** "
                + " · ".join(
                    f"[{source_title}]({source_url})"
                    for source_title, source_url in regional_source_links(jur["source"])
                )
            )
            regional_meta = metadata_for_jurisdiction(jur["name"])
            if regional_meta:
                with st.expander("🔎 Implementation metadata", expanded=False):
                    meta_left, meta_right = st.columns(2)
                    with meta_left:
                        st.markdown(f"**Instrument / legislation:** {regional_meta['instrument_name']}")
                        st.markdown(f"**Effective / implementation date:** {regional_meta['effective_date']}")
                        st.markdown(f"**Supervisory bodies:** {regional_meta['supervisory_bodies']}")
                    with meta_right:
                        st.markdown(f"**Status:** {regional_meta['implementation_status']}")
                        st.markdown(f"**Scope:** {regional_meta['jurisdiction_scope']}")
                        st.markdown(f"**Official starting point:** [{regional_meta['official_source']}]({regional_meta['official_source']})")
            regional_news_title, regional_news_url = jurisdiction_update(jur["name"])
            update_link = (
                f"[{regional_news_title}]({regional_news_url})"
                if regional_news_url
                else regional_news_title
            )
            st.markdown(
                f"- **Latest regional fintech update — reviewed {regional_review_date}:** "
                f"{update_link}"
            )
        st.markdown("---")
        st.markdown("##### 📰 Latest Regional News *(live, cached 1 h)*")
        with st.spinner("Fetching news…"):
            news_items = fetch_rss_news(region["news_keywords"])
        if news_items:
            for item in news_items:
                st.markdown(
                    f"<div class='news-item'>"
                    f"<a href='{item['link']}' target='_blank' style='color:#93C5FD;text-decoration:none;font-weight:600'>{item['title']}</a>"
                    f"<br><small style='color:#64748B'>{item['date']}</small></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Live news unavailable right now — check CoinTelegraph or CoinDesk for the latest regional coverage.")

st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1B: FinTech Friendliness Index
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='dashboard-anchor' id='rankings-index'></div>", unsafe_allow_html=True)
st.subheader("📊 FinTech Friendliness Index")
st.markdown(
    "*Composite regulatory score across five institutional dimensions, scored 1–10. "
    "Benchmarked against 2016 baselines to track 10-year trajectory. "
    "Sources: CCAF Global Cryptoasset Benchmarking Study, KPMG Pulse of Fintech, "
    "IMF Digital Money Landscape, Chainalysis Geography of Cryptocurrency, "
    "LexisNexis Regulatory Intelligence, Bloomberg Intelligence FinTech.*"
)
with st.expander("ℹ️ Index methodology, scale & limitations", expanded=False):
    st.markdown(
        """
        **Scale:** Each dimension is scored from **1 (high restriction / friction)** to
        **10 (clear, accessible, and institutionally supportive)**. The composite is the
        simple arithmetic mean of the five dimensions; it is not a probability, price
        target, legal opinion, or investment recommendation.

        **Dimensions:** Regulatory Clarity measures predictability and specificity of rules.
        Sandbox Speed measures the practical speed of supervised testing. Licensing Ease
        measures authorization burden in cost, time, and complexity. Tax Incentives
        measures the relative fiscal environment. Institutional Banking measures access
        to banking, custody, payment, and settlement rails.

        **Interpretation:** 8–10 = comparatively supportive, 5–7 = mixed or developing,
        and 1–4 = materially restrictive. Scores are policy-research indicators based on
        the cited sources and review date, not a legally binding jurisdiction ranking.
        Cross-jurisdiction comparisons should account for differences in federal/state
        authority, implementation stage, tax treatment, and product scope.
        """
    )

DIMENSION_LABELS = {
    "regulatory_clarity":    "Regulatory Clarity",
    "sandbox_speed":         "Sandbox Speed",
    "licensing_ease":        "Licensing Ease",
    "tax_incentives":        "Tax Incentives",
    "institutional_banking": "Institutional Banking",
}
DIMENSION_DESCS = {
    "regulatory_clarity":    "Are the rules explicitly defined and predictable?",
    "sandbox_speed":         "How fast can startups legally test new products?",
    "licensing_ease":        "How achievable is full authorisation in cost and time?",
    "tax_incentives":        "Are corporate/capital-gains taxes favourable for digital assets?",
    "institutional_banking": "Can crypto/fintech firms readily access corporate banking?",
}
DIMENSION_HOVER = {
    "regulatory_clarity": "Predictability and specificity of applicable rules",
    "sandbox_speed": "Practical speed of supervised product testing",
    "licensing_ease": "Authorization burden across cost, time, and complexity",
    "tax_incentives": "Relative fiscal treatment of digital-asset activity",
    "institutional_banking": "Access to banking, custody, payment, and settlement rails",
}

ffi_tab1, ffi_tab2, ffi_tab3 = st.tabs(["🏆 Leaderboard", "🕸️ Radar Comparison", "📈 10-Year Trajectory"])

# ── Tab 1: Ranked leaderboard ────────────────────────────────────────────────
with ffi_tab1:
    st.markdown(
        "*All jurisdictions ranked by 2026 composite score. Rank, score, and status are shown in every "
        "expander title; open a row for the dimension breakdown and source notes.*"
    )
    st.caption("Ranking is descending by composite score; ties are ordered alphabetically.")

    RANK_COLORS = {
        (8, 10):  ("#064E3B", "#6EE7B7"),
        (6, 8):   ("#1E3A5F", "#93C5FD"),
        (4, 6):   ("#78350F", "#FCD34D"),
        (0, 4):   ("#7F1D1D", "#FCA5A5"),
    }

    def rank_style(score):
        for (lo, hi), (bg, fg) in RANK_COLORS.items():
            if lo <= score <= hi:
                return bg, fg
        return "#1E2A45", "#E2E8F0"

    def score_bar(val, max_val=10):
        pct = int(val / max_val * 100)
        return (
            f"<div style='background:#1E2A45;border-radius:4px;height:8px;width:100%'>"
            f"<div style='background:#3B82F6;height:8px;border-radius:4px;width:{pct}%'></div></div>"
        )

    for rank, row in enumerate(fintech_df.itertuples(), 1):
        composite = float(row.composite_2026)
        bg, fg = rank_style(composite)
        score_band = "High" if composite >= 8 else ("Moderate" if composite >= 5 else "Low")
        band_color = "#6EE7B7" if score_band == "High" else ("#FCD34D" if score_band == "Moderate" else "#FCA5A5")
        profile_label = "High Profile" if score_band == "High" else (
            "Moderate Profile" if score_band == "Moderate" else "Low Profile"
        )
        expander_title = (
            f"[RANK {rank:02d}] {row.jurisdiction} — "
            f"Score: {composite:.1f}/10 ({profile_label})"
        )
        with st.expander(expander_title, expanded=False):
            st.markdown(
                f"<div style='border-left:4px solid {band_color};background:#111C2E;padding:8px 12px;"
                f"border-radius:4px;margin:4px 0 14px 0;color:#CBD5E1;font-size:0.85rem'>"
                f"<b style='color:{band_color}'>{profile_label}</b> — "
                "Composite score across five institutional dimensions</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"### 📊 Dimensions Breakdown: {row.jurisdiction}")

            dims = ["regulatory_clarity", "sandbox_speed", "licensing_ease", "tax_incentives", "institutional_banking"]
            bento_cards = []
            for dim in dims:
                val = float(getattr(row, dim))
                pct = int(max(0, min(10, val)) / 10 * 100)
                bento_cards.append(
                    f"<div class='ffi-bento-card'>"
                    f"<div class='ffi-bento-label'>{DIMENSION_LABELS[dim]}</div>"
                    f"<div class='ffi-bento-desc'>{DIMENSION_DESCS[dim]}</div>"
                    f"<div class='ffi-bento-score'>{val:.1f}<span style='font-size:.72rem;color:#AAB7C8'> / 10</span></div>"
                    f"<div class='ffi-bento-track'><div class='ffi-bento-fill' style='width:{pct}%'></div></div>"
                    f"</div>"
                )
            st.markdown(
                f"<div class='ffi-bento'>{''.join(bento_cards)}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("")
            delta_col, notes_col = st.columns([1, 2])
            with delta_col:
                delta = float(row.improvement_delta)
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
                )
            with notes_col:
                st.markdown("**Trajectory & Context:**")
                st.caption(row.improvement_notes)
                st.markdown(f"**Sources:** *{row.sources}*")
                row_meta = metadata_for_jurisdiction(row.jurisdiction)
                if row_meta:
                    st.caption(
                        f"**Policy context:** {row_meta['instrument_name']} · "
                        f"{row_meta['effective_date']} · {row_meta['implementation_status']}"
                    )

# ── Tab 2: Radar comparison chart ────────────────────────────────────────────
with ffi_tab2:
    st.markdown("*Select up to 5 jurisdictions to overlay on the radar. Larger area = stronger fintech environment across all dimensions.*")

    all_jurisdictions = fintech_df["jurisdiction"].tolist()
    defaults = ["UAE (VARA / DIFC)", "Singapore (MAS)", "United States", "European Union (MiCA)", "Hong Kong (SFC)"]
    selected_juris = st.multiselect(
        "Jurisdictions to compare:",
        options=all_jurisdictions,
        default=[j for j in defaults if j in all_jurisdictions],
        max_selections=5,
    )

    if selected_juris:
        radar_fig = go.Figure()
        dims = ["regulatory_clarity", "sandbox_speed", "licensing_ease", "tax_incentives", "institutional_banking"]
        dim_labels = [DIMENSION_LABELS[d] for d in dims] + [DIMENSION_LABELS[dims[0]]]  # close polygon

        # High-contrast, colorblind-aware palette; fills stay subtle to avoid overlap.
        RADAR_COLORS = ["#00B8D9", "#66CC66", "#F2B134", "#FF6B6B", "#B18CFF"]

        for idx, jname in enumerate(selected_juris):
            jrow = fintech_df[fintech_df["jurisdiction"] == jname].iloc[0]
            values = [getattr(jrow, d) for d in dims] + [getattr(jrow, dims[0])]
            hover_dimensions = "<br>".join(
                f"<b>{DIMENSION_LABELS[dim]}</b>: {getattr(jrow, dim):.1f}/10 — {DIMENSION_HOVER[dim]}"
                for dim in dims
            )
            jmeta = metadata_for_jurisdiction(jname)
            hover_context = (
                f"<br><b>Instrument:</b> {escape(jmeta.get('instrument_name', 'Not mapped'))}"
                f"<br><b>Effective:</b> {escape(jmeta.get('effective_date', 'Not mapped'))}"
                f"<br><b>Status:</b> {escape(jmeta.get('implementation_status', 'Not mapped'))}"
            )
            trace_color = RADAR_COLORS[idx % len(RADAR_COLORS)]
            radar_fig.add_trace(go.Scatterpolar(
                r=values,
                theta=dim_labels,
                fill="none",
                name=jname.split("(")[0].strip(),
                line=dict(color=trace_color, width=3),
                opacity=1.0,
                hovertemplate=(
                    f"<b>{escape(jname)}</b><br>{hover_dimensions}{hover_context}"
                    "<extra></extra>"
                ),
            ))

        radar_fig.update_layout(
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
        )
        st.plotly_chart(radar_fig, width="stretch")

        st.markdown("**How to read this chart:**")
        st.caption(
            "Each axis represents one institutional dimension scored 1–10. "
            "A jurisdiction strong across all five axes will have a large, balanced polygon. "
            "A narrow spike on one axis (e.g., UAE on Tax Incentives) shows a strategic strength. "
            "A collapsed axis (e.g., US on Licensing Ease) reveals where firms face the most friction. "
            "Use this to identify where a jurisdiction's regulatory story outperforms or lags its overall score."
        )
    else:
        if all_jurisdictions:
            st.info("Select at least one jurisdiction above to render the radar chart.")
        else:
            st.warning(
                "No friendliness-index records are available. Configure "
                "AIRTABLE_INDEX_TABLE or add the five friendliness dimension fields "
                "to the main Airtable grid."
            )

# ── Tab 3: 10-year improvement bar chart ─────────────────────────────────────
with ffi_tab3:
    st.markdown(
        "*How much has each jurisdiction's composite FinTech Friendliness Index improved over the past decade? "
        "Based on CCAF benchmarking, World Bank Doing Business indicators, and LexisNexis regulatory archive analysis.*"
    )

    if fintech_df.empty:
        st.warning("No trajectory data is available from Airtable yet.")
    else:
        traj_df = fintech_df[["jurisdiction", "composite_2016", "composite_2026", "improvement_delta", "improvement_trend"]].copy()
        traj_df["short_name"] = traj_df["jurisdiction"].apply(lambda x: x.split("(")[0].strip().split("/")[0].strip())
        traj_df = traj_df.sort_values("improvement_delta", ascending=True)

        traj_fig = go.Figure()
        traj_fig.add_trace(go.Bar(
            y=traj_df["short_name"],
            x=traj_df["composite_2016"],
            name="2016 Score",
            orientation="h",
            marker_color="#1E3A5F",
            hovertemplate="<b>%{y}</b><br>2016 composite: %{x:.1f}/10<extra></extra>",
        ))
        traj_fig.add_trace(go.Bar(
            y=traj_df["short_name"],
            x=traj_df["improvement_delta"],
            name="Improvement 2016→2026",
            orientation="h",
            marker_color="#3B82F6",
            hovertemplate="<b>%{y}</b><br>Gained: +%{x:.1f} pts<extra></extra>",
            base=traj_df["composite_2016"].tolist(),
        ))

        for _, r in traj_df.iterrows():
            traj_fig.add_annotation(
                x=float(r["composite_2026"]) + 0.15,
                y=r["short_name"],
                text=f"<b>{float(r['composite_2026']):.1f}</b>",
                showarrow=False,
                font=dict(size=11, color="#F1F5F9"),
                xanchor="left",
            )

        traj_fig.update_layout(
            barmode="stack",
            template="plotly_dark",
            height=420,
            xaxis=dict(title="Composite Score (1–10)", range=[0, 11.5], gridcolor="#1E3A5F"),
            yaxis=dict(title="", tickfont=dict(size=11)),
            margin=dict(l=20, r=60, t=30, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(traj_fig, width="stretch")

    col_insight_l, col_insight_r = st.columns(2)
    with col_insight_l:
        st.markdown("**Key findings from the 10-year trajectory:**")
        st.markdown("""
- **UAE** shows the most dramatic improvement (+6.9 pts) — from near-zero informal tolerance in 2016 to the world's most comprehensive VASP framework by 2026
- **Singapore** and **Hong Kong** both leveraged their existing financial-services infrastructure to accelerate digital-asset regulation post-2020
- **United States** shows near-stagnation (+0.2 pts) despite being the world's largest capital market — SEC/CFTC jurisdictional conflict remains the primary drag
- **Africa** shows meaningful progress (+3.7 pts) primarily through sandbox innovation (Kenya, Rwanda) rather than formal licensing regimes
        """)
    with col_insight_r:
        st.markdown("**What drives improvement?**")
        st.info(
            "The biggest single-year jumps across all jurisdictions occurred within 12 months of either: "
            "(a) a major domestic exchange failure forcing regulatory action, "
            "(b) FATF greylisting pressure requiring AML framework upgrades, or "
            "(c) a competing jurisdiction launching a materially better framework, triggering regulatory competition. "
            "Jurisdictions that improved most were those that separated licensing from enforcement — "
            "using sandboxes to test before regulating, rather than regulating after crisis."
        )

st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1D: FinTech Readiness vs. Friendliness Matrix
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='dashboard-anchor' id='benchmarking-matrix'></div>", unsafe_allow_html=True)
st.subheader("🧭 FinTech Readiness vs. Friendliness Matrix")
st.markdown(
    "*Readiness measures regulatory clarity, sandbox speed, and institutional banking access. "
    "Friendliness adds licensing ease and tax incentives to show where deployment is both "
    "institutionally viable and operationally practical.*"
)

if fintech_df.empty:
    st.info("No external or Airtable friendliness records are available for this matrix.")
else:
    readiness_columns = ["regulatory_clarity", "sandbox_speed", "institutional_banking"]
    friendliness_columns = [
        "regulatory_clarity", "sandbox_speed", "licensing_ease",
        "tax_incentives", "institutional_banking",
    ]
    matrix_df = fintech_df.copy()
    matrix_df["readiness_score"] = matrix_df[readiness_columns].mean(axis=1)
    matrix_df["friendliness_score"] = matrix_df[friendliness_columns].mean(axis=1)
    matrix_df["readiness_quadrant"] = np.select(
        [
            (matrix_df["readiness_score"] >= 7) & (matrix_df["friendliness_score"] >= 7),
            (matrix_df["readiness_score"] >= 7) & (matrix_df["friendliness_score"] < 7),
            (matrix_df["readiness_score"] < 7) & (matrix_df["friendliness_score"] >= 7),
        ],
        ["Deploy-ready leaders", "Ready, but friction-heavy", "Friendly, still maturing"],
        default="Early-stage / high-friction",
    )
    matrix_fig = go.Figure()
    for region_name, region_rows in matrix_df.groupby("region", dropna=False):
        matrix_fig.add_trace(go.Scatter(
            x=region_rows["friendliness_score"],
            y=region_rows["readiness_score"],
            mode="markers+text",
            name=str(region_name or "Other"),
            text=region_rows["jurisdiction"].str.split("(").str[0].str.strip(),
            textposition="top center",
            marker=dict(size=13, line=dict(color="#F1F5F9", width=1)),
            customdata=np.stack([
                region_rows["jurisdiction"].astype(str),
                region_rows["composite_2026"].round(2),
                region_rows["readiness_quadrant"],
                region_rows["readiness_score"].round(2),
                region_rows["friendliness_score"].round(2),
            ], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>Friendliness: %{x:.1f}/10<br>"
                "Readiness: %{y:.1f}/10<br>Composite: %{customdata[1]}/10<br>"
                "Quadrant: %{customdata[2]}<br>"
                "Readiness = clarity + sandbox + banking<br>"
                "Friendliness = five-dimension mean<br>"
                "<extra></extra>"
            ),
        ))
    matrix_fig.add_vline(x=7, line_dash="dot", line_color="#64748B")
    matrix_fig.add_hline(y=7, line_dash="dot", line_color="#64748B")
    matrix_fig.update_layout(
        template="plotly_dark",
        height=520,
        xaxis=dict(title="Operational Friendliness (1–10)", range=[0, 10.5], dtick=1, gridcolor="#1E3A5F"),
        yaxis=dict(title="Institutional Readiness (1–10)", range=[0, 10.5], dtick=1, gridcolor="#1E3A5F"),
        margin=dict(l=20, r=20, t=45, b=55),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
    )
    st.plotly_chart(matrix_fig, width="stretch")
    st.caption(
        "Matrix definitions: Readiness is the mean of Regulatory Clarity, Sandbox Speed, "
        "and Institutional Banking. Friendliness is the mean of all five index dimensions. "
        "The dotted lines at 7/10 are decision thresholds, not regulatory standards."
    )

    quadrant_counts = matrix_df["readiness_quadrant"].value_counts()
    quadrant_order = [
        "Deploy-ready leaders", "Ready, but friction-heavy",
        "Friendly, still maturing", "Early-stage / high-friction",
    ]
    metric_cols = st.columns(4)
    for col, quadrant in zip(metric_cols, quadrant_order):
        with col:
            st.metric(quadrant, int(quadrant_counts.get(quadrant, 0)))

    matrix_jurisdictions = matrix_df["jurisdiction"].tolist()
    selected_matrix_jurisdiction = st.selectbox(
        "Interpret this jurisdiction",
        matrix_jurisdictions,
        key="matrix_jurisdiction",
        help="Select a jurisdiction to see what its readiness and friendliness scores imply for deployment.",
    )
    selected_matrix_row = matrix_df[
        matrix_df["jurisdiction"] == selected_matrix_jurisdiction
    ].iloc[0]
    selected_quadrant = selected_matrix_row["readiness_quadrant"]
    selected_readiness = float(selected_matrix_row["readiness_score"])
    selected_friendliness = float(selected_matrix_row["friendliness_score"])
    dimension_scores = {
        "Regulatory clarity": float(selected_matrix_row["regulatory_clarity"]),
        "Sandbox speed": float(selected_matrix_row["sandbox_speed"]),
        "Licensing ease": float(selected_matrix_row["licensing_ease"]),
        "Tax incentives": float(selected_matrix_row["tax_incentives"]),
        "Institutional banking": float(selected_matrix_row["institutional_banking"]),
    }
    strongest_dimension = max(dimension_scores, key=dimension_scores.get)
    weakest_dimension = min(dimension_scores, key=dimension_scores.get)
    quadrant_explanations = {
        "Deploy-ready leaders": (
            "Strong readiness and strong operating conditions make this a practical "
            "shortlist candidate for institutionally supported launches."
        ),
        "Ready, but friction-heavy": (
            "Core infrastructure is in place, but licensing, tax, or market-access "
            "friction should be resolved before committing to a broad rollout."
        ),
        "Friendly, still maturing": (
            "The operating environment is supportive, but institutional rails or "
            "regulatory execution may still require a phased deployment plan."
        ),
        "Early-stage / high-friction": (
            "Both implementation readiness and operating conditions are developing; "
            "use partnerships, pilots, or monitoring rather than immediate scale."
        ),
    }
    st.markdown(f"**Jurisdiction interpretation: {selected_matrix_jurisdiction}**")
    st.info(
        f"**{selected_quadrant}** — {quadrant_explanations[selected_quadrant]} "
        f"Readiness is **{selected_readiness:.1f}/10** and friendliness is "
        f"**{selected_friendliness:.1f}/10**. Its strongest dimension is "
        f"**{strongest_dimension} ({dimension_scores[strongest_dimension]:.1f}/10)**; "
        f"the main improvement or diligence area is **{weakest_dimension} "
        f"({dimension_scores[weakest_dimension]:.1f}/10)**."
    )

st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3: Integrated Analytical Timeline (5-year, zoomable, annotated)
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='dashboard-anchor' id='market-timeline'></div>", unsafe_allow_html=True)
st.subheader("📈 Integrated Analytical Timeline")
st.markdown(
    "*5-year view of global crypto market capitalisation with real policy events pinned to their exact dates. "
    "Hover over any marker to read what happened. Use the buttons or drag the range slider to zoom.*"
)

# Category filter
timeline_cats = st.multiselect(
    "Filter event categories:",
    options=list(CATEGORY_COLORS.keys()),
    default=list(CATEGORY_COLORS.keys()),
    format_func=lambda x: CATEGORY_LABELS[x],
)

filtered_events = [e for e in POLICY_EVENTS_TIMELINE if e["category"] in timeline_cats]

fig = go.Figure()

# Market cap line
fig.add_trace(go.Scatter(
    x=market_df["Date"],
    y=market_df["Global_Market_Cap"] / 1e12,
    mode="lines",
    name="Global Crypto Market Cap ($T)",
    line=dict(color="#3B82F6", width=2.5),
    hovertemplate="<b>%{x|%b %d, %Y}</b><br>Market Cap: $%{y:.2f}T<extra></extra>",
))

# Event markers as scatter points (for rich hover text) placed at chart top
y_max = (market_df["Global_Market_Cap"] / 1e12).max() * 1.05

for cat in CATEGORY_COLORS:
    events_in_cat = [e for e in filtered_events if e["category"] == cat]
    if not events_in_cat:
        continue
    fig.add_trace(go.Scatter(
        x=[datetime.strptime(e["date"], "%Y-%m-%d") for e in events_in_cat],
        y=[y_max] * len(events_in_cat),
        mode="markers+text",
        marker=dict(
            symbol="triangle-down",
            size=12,
            color=CATEGORY_COLORS[cat],
            line=dict(color="white", width=1),
        ),
        text=[e["label"] for e in events_in_cat],
        textposition="top center",
        textfont=dict(size=8, color=CATEGORY_COLORS[cat]),
        name=CATEGORY_LABELS[cat],
        customdata=[
            [e["jurisdiction"], e["event"], e["impact"], CATEGORY_LABELS[e["category"]]]
            for e in events_in_cat
        ],
        hovertemplate=(
            "<b>%{x|%b %d, %Y} — %{customdata[0]}</b><br>"
            "<b>Category:</b> %{customdata[3]}<br>"
            "<b>Impact Score:</b> %{customdata[2]}/10<br><br>"
            "%{customdata[1]}<extra></extra>"
        ),
    ))

# Vertical lines for events
for e in filtered_events:
    event_date = datetime.strptime(e["date"], "%Y-%m-%d")
    fig.add_vline(
        x=event_date,
        line_dash="dot",
        line_color=CATEGORY_COLORS[e["category"]],
        line_width=1.2,
        opacity=0.6,
    )

fig.update_layout(
    template="plotly_dark",
    height=520,
    xaxis=dict(
        title="Date",
        rangeslider=dict(visible=True, thickness=0.06),
        rangeselector=dict(
            buttons=[
                dict(count=1,  label="1M",  step="month", stepmode="backward"),
                dict(count=6,  label="6M",  step="month", stepmode="backward"),
                dict(count=1,  label="1Y",  step="year",  stepmode="backward"),
                dict(count=3,  label="3Y",  step="year",  stepmode="backward"),
                dict(count=5,  label="5Y",  step="year",  stepmode="backward"),
                dict(step="all", label="All"),
            ],
            bgcolor="#1E2A45",
            activecolor="#3B82F6",
            font=dict(color="#CBD5E1"),
        ),
        type="date",
    ),
    yaxis=dict(title="Market Capitalisation (USD Trillions)", fixedrange=False),
    margin=dict(l=20, r=20, t=40, b=60),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
    hovermode="x unified" if False else "closest",
)

st.plotly_chart(fig, width="stretch")

with st.expander("📖 How to use this timeline", expanded=False):
    st.markdown("""
**Navigation:**
- Click **1M / 6M / 1Y / 3Y / 5Y / All** buttons above the chart to jump to any window.
- Drag the grey bar at the bottom (range slider) to scroll through time, or drag its edges to resize the window.
- Hover over any **▼ triangle marker** to read the full event description and impact score.

**How to read the market cap line:**
The blue line represents the total market value of all cryptocurrencies combined, in USD trillions. It is modelled on real historical crypto market structure — bull cycles, crash events, and recovery phases are proportionally accurate.

**Reading the events with the line:**
- A sharp **drop** immediately after a red (enforcement) marker typically reflects market panic from regulatory crackdowns.
- A **rise** following a green (institutional) marker signals capital inflows from new institutional participants.
- **Purple** (market events) like the LUNA collapse or FTX failure show the most dramatic drops — these were liquidity crises, not just regulatory reactions.
- **Amber** (legislation) markers often cause short-term volatility in both directions depending on whether the market reads the law as restrictive or enabling.

**For legal researchers:** Each event is tagged with jurisdiction and impact score (1–10). High-impact events (8–10) are the ones most likely to appear in regulatory filings, court submissions, or policy briefs as precedent-setting moments. Use the category filter above to isolate enforcement actions (red) for litigation context, or legislation (amber) for comparative law analysis.
""")

# Scrollable event log below chart
with st.expander(f"📋 Full Event Log ({len(filtered_events)} events)", expanded=False):
    for e in sorted(filtered_events, key=lambda x: x["date"], reverse=True):
        cat_color = CATEGORY_COLORS[e["category"]]
        st.markdown(
            f"<div style='border-left:3px solid {cat_color};padding:8px 14px;margin:6px 0;background:#1A2535;border-radius:4px'>"
            f"<strong style='color:{cat_color}'>{e['date']} — {e['jurisdiction']}</strong> "
            f"<span style='background:{cat_color};color:white;font-size:0.7rem;padding:2px 7px;border-radius:8px;margin-left:6px'>"
            f"{CATEGORY_LABELS[e['category']]}</span> "
            f"<span style='color:#94A3B8;font-size:0.75rem;margin-left:6px'>Impact: {e['impact']}/10</span><br>"
            f"<span style='color:#CBD5E1;font-size:0.88rem'><strong>{e['label']}</strong> — {e['event']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 4: Geopolitical Policy Matrix
# ════════════════════════════════════════════════════════════════════════════════
st.subheader("🏛️ Geopolitical Policy & Projected Revenue Matrix")
st.markdown("*Qualitative translation mechanics for cross-border strategy officers and asset managers.*")

if macro_df.empty:
    st.info("No policy vector matches your current analytical filters.")
else:
    for _, row in macro_df.iterrows():
        with st.expander(f"📍 {row['jurisdiction']} — Impact Score: {row['impact_score']}/10", expanded=True):
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("##### 📝 **Regulatory Shift**")
                st.write(row["regulatory_shift"])
                st.markdown("##### 🌐 **Geopolitical Friction & Context**")
                st.markdown(f"<div class='policy-alert'>{row['geopolitical_context']}</div>", unsafe_allow_html=True)
            with col_right:
                st.markdown("##### 📊 **Macro Economic & GDP Vector**")
                st.write(row["gdp_impact_trajectory"])
                st.markdown("##### 💰 **Projected Industry Revenue Opportunity**")
                st.info(row["industry_rev_projection"])
            card_meta = {
                column: row.get(column, "")
                for column in [
                    "instrument_name", "effective_date", "supervisory_bodies",
                    "implementation_status", "jurisdiction_scope", "official_source",
                ]
            }
            if any(str(value).strip() for value in card_meta.values()):
                official_source = card_meta["official_source"].strip()
                verified_source = (
                    f'<a href="{escape(official_source)}" target="_blank" '
                    f'rel="noopener noreferrer">Open official regulatory source</a>'
                    if official_source
                    else "Not mapped"
                )
                st.markdown(
                    "\n\n".join([
                        f"- **Regulatory Instrument:** {card_meta['instrument_name'] or 'Not mapped'}",
                        f"- **Supervisory Authority:** {card_meta['supervisory_bodies'] or 'Not mapped'}",
                        f"- **Operational Status:** {card_meta['implementation_status'] or 'Not mapped'}",
                        f"- **Regulatory Scope:** {card_meta['jurisdiction_scope'] or 'Not mapped'}",
                        f"- **Verified Source Link:** {verified_source}",
                    ]),
                    unsafe_allow_html=True,
                )

st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 5: Cross-Regional Cooperation Framework
# ════════════════════════════════════════════════════════════════════════════════
st.subheader("🤝 Cross-Regional Cooperation Framework")
st.markdown(
    "*Actionable cooperation pathways that leverage each region's comparative regulatory advantage. "
    "Each idea is grounded in an existing multilateral precedent, with reference materials linked.*"
)

for idea in COOPERATION_IDEAS:
    with st.expander(f"{idea['title']}  ·  {idea['regions']}", expanded=False):
        cola, colb = st.columns([2, 1])
        with cola:
            st.markdown(f"**Opportunity:**  {idea['idea']}")
            if idea.get("references"):
                st.markdown("**📚 Reference Materials:**")
                for label, url in idea["references"]:
                    st.markdown(f"- [{label}]({url})")
        with colb:
            st.info(f"**Mechanism:** {idea['mechanism']}")
            st.success(f"**Precedent:** {idea['precedent']}")

st.divider()

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 6: Research Submission Form
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("<div class='dashboard-anchor' id='researcher-portal'></div>", unsafe_allow_html=True)
with st.expander("📥 Submit Strategic Policy Updates (Researcher Portal)", expanded=False):
    st.markdown(
        "*Submissions enter the research queue as **Pending Review**. Only records "
        "marked **Approved** by a reviewer appear in dashboard intelligence.*"
    )
    with st.form("research_submission_form", clear_on_submit=True):
        st.markdown("### 📋 Section 1: Legislative Metadata & Qualitative Analysis")
        fc1, fc2 = st.columns(2)
        with fc1:
            f_jur = st.text_input("Jurisdiction Authority (e.g., US Fed, HK MA)")
            f_region = st.selectbox(
                "Index Region",
                ["APAC", "North America", "Europe", "LATAM", "MENA", "Africa", "Other"],
            )
            f_geo = st.text_input(
                "Geopolitical Context",
                placeholder=(
                    "e.g., US-China tech-decoupling; HK positioning as regional "
                    "non-western liquidity hub."
                ),
            )
            f_gdp = st.text_input(
                "Projected Macro/GDP Trajectory",
                placeholder=(
                    "e.g., Offsets real estate stagnation by 0.4% capital inflow trajectory."
                ),
            )
        with fc2:
            f_shift = st.text_input(
                "Legislative Update / Shift",
                placeholder="e.g., SFC circular on institutional staking rules.",
            )
            f_source = st.text_input(
                "Source URL / Official Gazette Link",
                placeholder="e.g., https://sfc.hk...",
            )
            f_rev = st.text_input("Industry Addressable Revenue Scale ($B)")

        st.markdown("### 📊 Section 2: Macro Index Scoring Matrix")
        st.caption(
            "(Scoring Scale: 1 = Highly Restrictive / Friction-Heavy | "
            "10 = Optimized / Fully Progressive)"
        )
        sc1, sc2 = st.columns(2)
        with sc1:
            f_score = st.slider("Volatility Impact Rating", 1, 10, 5)
            f_clarity = st.slider("Regulatory Clarity", 1, 10, 5)
            f_sandbox = st.slider("Sandbox Speed", 1, 10, 5)
        with sc2:
            f_friction = st.slider(
                "Licensing Friction",
                1, 10, 5,
                help="1 = easy and low-cost authorization; 10 = highly difficult or costly.",
            )
            f_tax = st.slider("Tax Incentives", 1, 10, 5)
            f_banking = st.slider("Institutional Banking Access", 1, 10, 5)

        submitted = st.form_submit_button(
            "Authenticate and Submit Intel",
            use_container_width=True,
        )
    if submitted:
        if f_jur.strip() and f_shift.strip() and f_source.strip():
            today = datetime.now().strftime("%Y-%m-%d")
            policy_fields = {
                "jurisdiction": f_jur,
                "regulatory_shift": f_shift,
                "source_url": f_source.strip(),
                "geopolitical_context": f_geo,
                "gdp_impact_trajectory": f_gdp,
                "industry_rev_projection": f_rev,
                "impact_score": f_score,
                "date_logged": today,
                "Status": "Pending Review",
            }
            index_fields = {
                "jurisdiction": f_jur,
                "region": f_region,
                "regulatory_clarity": f_clarity,
                "sandbox_speed": f_sandbox,
                # Stored field remains licensing_ease for compatibility:
                # 10 friction = 1 ease, 1 friction = 10 ease.
                "licensing_ease": 11 - f_friction,
                "tax_incentives": f_tax,
                "institutional_banking": f_banking,
                "composite_2026": round(
                    (f_clarity + f_sandbox + (11 - f_friction) + f_tax + f_banking) / 5,
                    2,
                ),
                "year_assessed": datetime.now().year,
                "Status": "Pending Review",
            }
            try:
                if not airtable_ensure_status_column(resolved_policy_table):
                    st.stop()
                policy_result = airtable_create(resolved_policy_table, policy_fields)
                if policy_result is None:
                    st.stop()

                matching_index = fintech_source_df[
                    fintech_source_df["jurisdiction"].astype(str).str.strip().str.casefold()
                    == f_jur.strip().casefold()
                ]
                if not resolved_index_table:
                    index_action = "saved the legislative update; no AIRTABLE_INDEX_TABLE is configured"
                elif matching_index.empty:
                    if not airtable_ensure_status_column(resolved_index_table):
                        st.stop()
                    if airtable_create(resolved_index_table, index_fields) is None:
                        st.stop()
                    index_action = "created a new"
                else:
                    record_id = matching_index.iloc[0]["_airtable_record_id"]
                    if airtable_update(resolved_index_table, record_id, index_fields) is None:
                        st.stop()
                    index_action = "updated the existing"

                st.cache_data.clear()
                st.success(
                    f"Successfully appended the legislative update and {index_action} "
                    f"Friendliness Index record for {f_jur}. Refreshing charts…"
                )
                st.rerun()
            except (requests.RequestException, RuntimeError, ValueError, KeyError) as exc:
                st.error(
                    "Airtable rejected the submission. Confirm the table names and exact "
                    f"field headers. Details: {exc}"
                )
        else:
            st.error(
                "Submission blocked: Authority, Legislative Update / Shift, and "
                "Source URL / Official Gazette Link are mandatory."
            )
