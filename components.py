"""
components.py — Nirnay · CDSCO AI Hackathon 2026
-------------------------------------------------
UI components, session state management, sidebar, audit trail helpers.
Imports from demo_data.py (sample packets) and engine.py (processing).
"""

from __future__ import annotations

import csv
import io
import json
from copy import deepcopy
from datetime import datetime

import pandas as pd
import streamlit as st

from demo_data import (
    APP_DISCLAIMER,
    APP_SUBTITLE,
    APP_TITLE,
    DEMO_MODE_LABEL,
    LEADERSHIP_METRICS,
    SCREENS,
    get_case_library,
)

# ── Re-export engine availability flags so app.py can check ──────────────────
from engine import CLAUDE_OK, CLAUDE_MODEL  # noqa: F401


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & STYLES
# ═══════════════════════════════════════════════════════════════════════════════

def configure_page() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="⚖️", layout="wide",
                       initial_sidebar_state="expanded")


def apply_styles() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',system-ui,-apple-system,sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
/* Sidebar collapse button (sidebar open) — Streamlit 1.40+ */
[data-testid="stSidebarCollapseButton"]{display:flex!important;visibility:visible!important;opacity:1!important;}
[data-testid="stSidebarCollapseButton"] button{background-color:#0a1e3d!important;border:none!important;border-radius:6px!important;width:32px!important;height:32px!important;display:flex!important;align-items:center!important;justify-content:center!important;cursor:pointer!important;}
[data-testid="stSidebarCollapseButton"] svg{display:none!important;}
[data-testid="stSidebarCollapseButton"] button::before{content:'☰';font-size:16px;color:rgba(255,255,255,0.9);font-family:Arial,sans-serif;line-height:1;}
/* Sidebar expand control (sidebar collapsed) — Streamlit 1.40+ */
[data-testid="stSidebarCollapsedControl"]{display:flex!important;visibility:visible!important;opacity:1!important;position:fixed!important;top:60px!important;left:0!important;z-index:99999!important;}
[data-testid="stSidebarCollapsedControl"] button{background-color:#0a1e3d!important;border:none!important;border-radius:0 8px 8px 0!important;width:28px!important;height:44px!important;display:flex!important;align-items:center!important;justify-content:center!important;cursor:pointer!important;box-shadow:2px 0 8px rgba(0,0,0,0.25)!important;}
[data-testid="stSidebarCollapsedControl"] svg{display:none!important;}
[data-testid="stSidebarCollapsedControl"] button::before{content:'☰';font-size:16px;color:rgba(255,255,255,0.9);font-family:Arial,sans-serif;line-height:1;}

.stApp{background-color:#f0f4f8;}

section[data-testid="stSidebar"]{background-color:#0a1e3d;}
section[data-testid="stSidebar"] *{color:white;}
section[data-testid="stSidebar"] p{color:rgba(255,255,255,0.75);}
section[data-testid="stSidebar"] .stSelectbox>div>div{background-color:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:8px;}
section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:white;}

.hero{background-color:#0a1e3d;border-radius:14px;padding:28px 32px;margin-bottom:16px;}
.hero h1{color:white;font-size:22px;font-weight:800;margin:0;}
.hero .sub{color:rgba(255,255,255,0.65);font-size:13px;margin:5px 0 0;line-height:1.6;}
.hero-badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;}
.hbadge{background-color:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:4px 12px;font-size:11px;color:rgba(255,255,255,0.85);font-weight:500;}
.hbadge.g{border-color:#4ade80;color:#4ade80;background-color:rgba(74,222,128,0.08);}

.card{background-color:white;border:1px solid #e2e8f0;border-radius:14px;padding:18px 20px;margin-bottom:14px;box-shadow:0 1px 4px rgba(0,0,0,0.06);}
.case-chip{display:inline-block;background-color:#eff6ff;color:#1e40af;border:1px solid #bfdbfe;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600;}
.small-note{color:#64748b;font-size:13px;}

.sec-hd{display:flex;align-items:center;gap:12px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid #e2e8f0;}
.sec-ic{width:44px;height:44px;border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;}
.ic-blue{background-color:#dbeafe;}.ic-teal{background-color:#ccfbf1;}.ic-purple{background-color:#ede9fe;}
.ic-amber{background-color:#fef3c7;}.ic-sky{background-color:#e0f2fe;}.ic-pink{background-color:#fce7f3;}
.sec-hd h2{font-size:17px;font-weight:700;color:#0f172a;margin:0;}
.sec-hd p{font-size:12px;color:#64748b;margin:3px 0 0;line-height:1.5;}

.upload-card{background-color:white;border:2px dashed #cbd5e1;border-radius:14px;padding:20px 22px;margin-bottom:14px;}
.upload-card h4{color:#0f172a;font-size:14px;font-weight:600;margin:0 0 10px;}
.or-line{display:flex;align-items:center;gap:10px;margin:10px 0;color:#94a3b8;font-size:12px;}
.or-line::before,.or-line::after{content:'';flex:1;height:1px;background-color:#e2e8f0;}

.pii-chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0;}
.chip{display:inline-flex;align-items:center;gap:4px;border-radius:20px;padding:4px 11px;font-size:12px;font-weight:600;}
.cr{background-color:#fee2e2;color:#991b1b;}.ca{background-color:#fef3c7;color:#92400e;}
.cb{background-color:#dbeafe;color:#1e40af;}.cp{background-color:#ede9fe;color:#5b21b6;}
.ct{background-color:#ccfbf1;color:#065f46;}.cg{background-color:#f1f5f9;color:#475569;}

.rc{background-color:white;border-radius:8px;padding:13px 16px;margin:8px 0;border-left:4px solid #003087;font-size:13px;line-height:1.6;}
.rc.ok{border-left-color:#16a34a;background-color:#f0fdf4;color:#15803d;}
.rc.warn{border-left-color:#d97706;background-color:#fffbeb;color:#92400e;}
.rc.err{border-left-color:#dc2626;background-color:#fef2f2;color:#b91c1c;}
.rc.info{border-left-color:#0284c7;background-color:#f0f9ff;color:#0369a1;}

.tw{background-color:white;border-radius:10px;padding:4px;margin:8px 0;border:1px solid #e2e8f0;}
.dup-session{background-color:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:12px 16px;margin-bottom:10px;font-size:13px;color:#0369a1;line-height:1.6;}
.audio-note{background-color:#fefce8;border:1px solid #fbbf24;border-radius:8px;padding:8px 12px;font-size:12px;color:#78350f;margin:8px 0;}
.entity-box{background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;font-size:13px;min-height:140px;white-space:pre-wrap;line-height:1.6;}

.stTabs [data-baseweb="tab-list"]{background-color:#0a1628;border-radius:10px;padding:4px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:7px;font-size:12px;font-weight:500;color:rgba(255,255,255,0.55);padding:8px 14px;}
.stTabs [aria-selected="true"]{background-color:#0052cc!important;color:white!important;}
.stTabs [data-baseweb="tab"]:hover{color:white!important;}
.stTabs [data-baseweb="tab-border"]{display:none;}
.stTabs [data-baseweb="tab-panel"]{background-color:white;border-radius:0 0 12px 12px;padding:20px!important;}

.stButton>button[kind="primary"]{background-color:#003087!important;color:white!important;border:none!important;border-radius:8px!important;font-weight:600!important;font-size:13px!important;padding:9px 18px!important;}
.stButton>button[kind="primary"]:hover{background-color:#0052cc!important;}
.stButton>button:not([kind="primary"]){border-radius:8px!important;font-size:13px!important;font-weight:500!important;}
.stDownloadButton>button{border-radius:8px!important;border:1.5px solid #003087!important;color:#003087!important;font-weight:500!important;font-size:13px!important;}
.stTextArea textarea{border:1.5px solid #e2e8f0!important;border-radius:8px!important;font-size:13px!important;background-color:#fafbfc!important;}
.stTextInput input{border-radius:8px!important;font-size:13px!important;}
[data-testid="stMetricValue"]{font-size:24px!important;font-weight:700!important;}
[data-testid="stMetricLabel"]{font-size:12px!important;color:#64748b!important;}
[data-testid="stExpander"]{border:1px solid #e2e8f0!important;border-radius:10px!important;}
[data-testid="stProgressBar"]>div>div{background-color:#003087!important;border-radius:99px!important;}
[data-testid="stProgressBar"]>div{border-radius:99px!important;background-color:#e2e8f0!important;}

/* Top nav breadcrumb button row */
.nav-btn-active>button{background-color:#003087!important;color:white!important;border:none!important;border-radius:8px!important;font-weight:600!important;}
.nav-btn-inactive>button{background-color:white!important;color:#374151!important;border:1.5px solid #e2e8f0!important;border-radius:8px!important;font-weight:500!important;}
.nav-btn-inactive>button:hover{border-color:#003087!important;color:#003087!important;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

def init_state() -> None:
    # Workflow case state
    if "demo_cases" not in st.session_state:
        st.session_state.demo_cases = get_case_library()
    if "active_case_key" not in st.session_state:
        st.session_state.active_case_key = next(iter(st.session_state.demo_cases))
    if "active_case" not in st.session_state:
        st.session_state.active_case = deepcopy(
            st.session_state.demo_cases[st.session_state.active_case_key])
    if "screen" not in st.session_state:
        st.session_state.screen = SCREENS[0]
    if "compare_filter" not in st.session_state:
        st.session_state.compare_filter = "All changes"
    # Feature tab state
    for k in ["anon_text","sum_text","comp_text","class_text","v1_text","v2_text",
              "anon_textarea","sum_ta","comp_ta","class_ta","v1ta","v2ta"]:
        if k not in st.session_state:
            st.session_state[k] = ""
    if "dup_files" not in st.session_state:
        st.session_state["dup_files"] = {}
    if "active_tab" not in st.session_state:
        st.session_state["active_tab"] = 0


def get_active_case() -> dict:
    return st.session_state.active_case


def save_active_case(case: dict) -> None:
    st.session_state.active_case = case


def set_active_case(case_key: str) -> None:
    st.session_state.active_case_key = case_key
    st.session_state.active_case = deepcopy(st.session_state.demo_cases[case_key])


def set_screen(screen: str) -> None:
    st.session_state.screen = screen


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT TRAIL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def add_audit_event(module: str, action: str, confidence: float,
                    reviewer_action: str, final_status: str,
                    source_reference: str, note: str) -> None:
    case = get_active_case()
    case["audit_events"].append({
        "timestamp":        timestamp(),
        "module":           module,
        "action":           action,
        "confidence":       round(confidence, 2),
        "reviewer_action":  reviewer_action,
        "final_status":     final_status,
        "source_reference": source_reference,
        "note":             note,
    })
    save_active_case(case)


def confirm_reviewer_action(module: str, decision: str, note: str,
                             source_reference: str, confidence: float = 1.0,
                             final_status: str = "Confirmed") -> None:
    case = get_active_case()
    case["reviewer_decisions"].append({
        "timestamp": timestamp(), "module": module,
        "decision":  decision,   "note": note,
    })
    save_active_case(case)
    add_audit_event(module=module, action="Reviewer confirmation recorded",
                    confidence=confidence, reviewer_action=decision,
                    final_status=final_status, source_reference=source_reference, note=note)


def audit_dataframe(case: dict) -> pd.DataFrame:
    return pd.DataFrame(case["audit_events"])


# ═══════════════════════════════════════════════════════════════════════════════
# WORKFLOW ACTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def run_classification() -> None:
    case     = get_active_case()
    document = case["documents"][case["selected_document_id"]]
    if "classification" not in document:
        st.warning("This document does not have a seeded classification. Upload a real document to generate AI output.")
        return
    case["document_classification"] = deepcopy(document["classification"])
    case["structured_synopsis"]     = deepcopy(document["synopsis"])
    case["export_readiness"]["classification"] = True
    case["current_stage"] = "Document Intake"
    save_active_case(case)
    add_audit_event("Document Intake", "Classification completed", document["confidence"],
                    "AI output generated", "Generated", document["name"],
                    "Probable document type and structured synopsis recorded on the active case packet.")


def apply_redaction_filters(case: dict) -> str:
    source_text = case["documents"][case["protected_view"]["source_document_id"]]["raw_text"]
    redacted    = source_text
    for entity in case["protected_view"]["entities"]:
        show = case["protected_view"]["category_filters"].get(entity["category"], True)
        if entity["approved"] and show:
            redacted = redacted.replace(entity["value"], entity["replacement"])
    return redacted


def validate_redaction() -> None:
    case          = get_active_case()
    low_conf      = [e["label"] for e in case["protected_view"]["entities"] if e["confidence"] < 0.9]
    approved_count = sum(1 for e in case["protected_view"]["entities"] if e["approved"])
    summary       = (f"{approved_count} identifiers approved for protected review. "
                     f"{len(low_conf)} low-confidence entities remain subject to reviewer confirmation.")
    case["protected_view"]["validated"]         = True
    case["protected_view"]["validation_summary"]= summary
    case["protected_view"]["escalation_status"] = "Escalation required" if low_conf else "No escalation required"
    case["export_readiness"]["protected_view"]  = True
    case["current_stage"] = "Protected View"
    save_active_case(case)
    add_audit_event("Protected View", "Protected view validated", 0.93,
                    "Reviewer confirmation pending", "Validated",
                    case["documents"][case["protected_view"]["source_document_id"]]["name"], summary)


def create_sae_packet() -> str:
    case = get_active_case()
    sae  = case["sae_review"]
    missing = ", ".join(i["item"] for i in sae["missing_info"] if not i["resolved"]) or "None"
    packet  = (f"Nirnay SAE Review Packet\nCase ID: {case['case_id']}\n"
               f"Source: {case['documents']['sae']['name']}\n"
               f"Patient profile: {sae['patient_profile']}\n"
               f"Event: {sae['event']}\nSeriousness: {sae['seriousness']}\n"
               f"Reviewer severity: {sae['severity']}\nCausality: {sae['causality']}\n"
               f"Action taken: {sae['action_taken']}\nOutcome: {sae['outcome']}\n"
               f"Missing information: {missing}\nReviewer notes: {sae['reviewer_notes']}\n"
               f"{APP_DISCLAIMER}")
    case["sae_review"]["review_packet"]    = packet
    case["export_readiness"]["sae_packet"] = True
    case["current_stage"] = "SAE Review"
    save_active_case(case)
    add_audit_event("SAE Review", "SAE review packet created", 0.94, "Packet ready", "Generated",
                    case["documents"]["sae"]["name"],
                    "Structured safety review packet generated from deterministic seeded outputs.")
    return packet


def create_compare_packet() -> str:
    case      = get_active_case()
    amendment = case["documents"]["amendment"]
    lines     = ["Nirnay Version Review Packet", f"Case ID: {case['case_id']}",
                 f"Source: {amendment['name']}", ""]
    for c in amendment["changes"]:
        lines += [f"- {c['area']} | {c['classification']} | {c['impact_level']}",
                  f"  Before: {c['before']}", f"  After: {c['after']}",
                  f"  Regulatory impact: {c['impact']}"]
    lines += ["", APP_DISCLAIMER]
    packet = "\n".join(lines)
    case["compare_review"]["review_packet"]    = packet
    case["export_readiness"]["compare_packet"] = True
    case["current_stage"] = "Version Compare"
    save_active_case(case)
    add_audit_event("Version Compare", "Comparison review packet created",
                    amendment["confidence"], "Packet ready", "Generated", amendment["name"],
                    "Substantive and administrative changes summarised for reviewer use.")
    return packet


def generate_audit_packet() -> dict:
    case   = get_active_case()
    packet = {
        "case_id":              case["case_id"],
        "packet_id":            case["packet_id"],
        "reviewer":             case["reviewer"],
        "status":               case["status"],
        "document_classification": case["document_classification"],
        "structured_synopsis":     case["structured_synopsis"],
        "protected_view": {
            "validated":         case["protected_view"]["validated"],
            "escalation_status": case["protected_view"]["escalation_status"],
            "validation_summary":case["protected_view"]["validation_summary"],
        },
        "sae_review_packet_ready":    bool(case["sae_review"]["review_packet"]),
        "compare_review_packet_ready":bool(case["compare_review"]["review_packet"]),
        "reviewer_decisions": case["reviewer_decisions"],
        "audit_events":       case["audit_events"],
    }
    case["export_readiness"]["audit_packet"] = True
    case["current_stage"] = "Audit Trail"
    save_active_case(case)
    add_audit_event("Audit Trail", "Audit packet generated", 1.0, "Audit packet ready", "Generated",
                    case["packet_id"], "Consolidated audit packet prepared from the active case state.")
    return packet


# ═══════════════════════════════════════════════════════════════════════════════
# RENDER HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def render_banner(title: str, subtitle: str) -> None:
    st.markdown(f"""
<div class="hero">
  <p style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,153,51,0.9);margin:0 0 8px;">{DEMO_MODE_LABEL}</p>
  <h1>{title}</h1>
  <p class="sub">{subtitle}</p>
  <div class="hero-badges">
    <span class="hbadge g">&#10003; DPDP Act 2023</span>
    <span class="hbadge g">&#10003; NDCT Rules 2019</span>
    <span class="hbadge g">&#10003; Schedule Y</span>
    <span class="hbadge g">&#10003; ICMR GCP</span>
    <span class="hbadge g">&#10003; MeitY AI Ethics</span>
  </div>
  <p style="margin-top:10px;font-size:11px;color:rgba(255,255,255,0.4);line-height:1.5;">{APP_DISCLAIMER}</p>
</div>
""", unsafe_allow_html=True)


def render_sidebar() -> str:
    case = get_active_case()
    with st.sidebar:
        st.markdown(f"## {APP_TITLE}")
        st.caption(APP_SUBTITLE)

        # Judge notice
        st.markdown("""
<div style="background:rgba(255,153,51,0.15);border:1px solid rgba(255,153,51,0.4);border-radius:8px;padding:10px 12px;margin:8px 0;">
  <p style="font-size:10px;font-weight:700;color:#FF9933;margin:0 0 4px;">📋 FOR JUDGES — EVALUATION GUIDE</p>
  <p style="font-size:10px;color:rgba(255,255,255,0.85);margin:0;line-height:1.5;">
  Sample packets are pre-loaded for quick review.<br>
  Upload <b>your own documents</b> in any feature tab — the AI engines process your files live.<br>
  Use <b>Review workflow</b> below to walk through the full CDSCO case review pipeline.
  </p>
</div>
""", unsafe_allow_html=True)

        case_key = st.selectbox(
            "Active sample packet",
            options=list(st.session_state.demo_cases.keys()),
            index=list(st.session_state.demo_cases.keys()).index(st.session_state.active_case_key),
            format_func=lambda k: st.session_state.demo_cases[k]["title"],
        )
        if case_key != st.session_state.active_case_key:
            set_active_case(case_key)
            case = get_active_case()

        screen = st.radio("Review workflow", options=SCREENS,
                          index=SCREENS.index(st.session_state.screen))
        st.session_state.screen = screen

        with st.expander("Current case packet", expanded=True):
            st.write(f"**Case ID:** {case['case_id']}")
            st.write(f"**Packet ID:** {case['packet_id']}")
            st.write(f"**Reviewer:** {case['reviewer']}")
            st.write(f"**Status:** {case['status']}")
            st.write(f"**Stage:** {case['current_stage']}")

        st.info(APP_DISCLAIMER)
    return screen


def render_top_nav() -> str:
    """Always-visible nav bar: case packet selector + workflow breadcrumb buttons."""
    _STEP_LABELS = {
        "Command Dashboard": "🏠 Dashboard",
        "Document Intake":   "📥 Intake",
        "Protected View":    "🔒 Protected",
        "SAE Review":        "🧪 SAE Review",
        "Version Compare":   "🔍 Compare",
        "Audit Trail":       "📋 Audit Trail",
    }

    # Row 1: Case packet selector + live status
    c1, c2, c3 = st.columns([3, 5, 2])
    with c1:
        st.caption("CASE PACKET")
        case_key = st.selectbox(
            "Active packet",
            options=list(st.session_state.demo_cases.keys()),
            index=list(st.session_state.demo_cases.keys()).index(
                st.session_state.active_case_key),
            format_func=lambda k: st.session_state.demo_cases[k]["title"],
            key="tnav_pkt",
            label_visibility="collapsed",
        )
        if case_key != st.session_state.active_case_key:
            set_active_case(case_key)

    case = get_active_case()
    with c2:
        st.caption("ACTIVE CASE")
        st.markdown(
            f'<p style="font-size:12px;color:#374151;margin:0;line-height:1.5;">'
            f'<b style="color:#0a2240;">{case["title"]}</b> &nbsp;·&nbsp; '
            f'Stage: <b style="color:#1d4ed8;">{case["current_stage"]}</b> &nbsp;·&nbsp; '
            f'Status: <b style="color:#15803d;">{case["status"]}</b></p>',
            unsafe_allow_html=True,
        )
    with c3:
        st.caption("HACKATHON")
        st.markdown(
            '<p style="font-size:11px;color:#6b7280;margin:0;">IndiaAI / CDSCO 2026<br>'
            '<span style="color:#f97316;font-weight:600;">Stage 1</span></p>',
            unsafe_allow_html=True,
        )

    st.divider()

    # Row 2: Workflow step breadcrumb
    st.caption("REVIEW WORKFLOW")
    step_cols = st.columns(len(SCREENS))
    for i, (scr, col) in enumerate(zip(SCREENS, step_cols)):
        with col:
            is_active = st.session_state.screen == scr
            label = _STEP_LABELS.get(scr, scr)
            if st.button(
                label,
                key=f"tnav_{i}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.screen = scr
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    return st.session_state.screen


def render_metrics() -> None:
    cols = st.columns(3)
    for i, m in enumerate(LEADERSHIP_METRICS):
        with cols[i % 3]:
            st.metric(m["label"], m["value"], help=m["detail"])


def render_case_header(case: dict) -> None:
    st.markdown(f"""
<div class="card">
  <span class="case-chip">{case['packet_id']}</span>
  <h3 style="margin-top:0.75rem;">{case['title']}</h3>
  <p class="small-note">Reviewer: {case['reviewer']} | Status: {case['status']} | Stage: {case['current_stage']}</p>
</div>
""", unsafe_allow_html=True)


def ai_recommendation_card(finding: str, risk_level: str, action: str, detail: str = "") -> None:
    palette = {
        "Critical": {"bg":"#fef2f2","border_l":"#dc2626","badge_bg":"#fee2e2","badge_fg":"#991b1b","icon":"🔴"},
        "High":     {"bg":"#fff7ed","border_l":"#ea580c","badge_bg":"#ffedd5","badge_fg":"#9a3412","icon":"🟠"},
        "Medium":   {"bg":"#fefce8","border_l":"#ca8a04","badge_bg":"#fef9c3","badge_fg":"#854d0e","icon":"🟡"},
        "Low":      {"bg":"#f0fdf4","border_l":"#16a34a","badge_bg":"#dcfce7","badge_fg":"#166534","icon":"🟢"},
    }
    p = palette.get(risk_level, palette["Medium"])
    st.markdown(f"""
<div style="border-radius:12px;padding:18px 22px;margin:14px 0;background-color:{p['bg']};border-left:5px solid {p['border_l']};border-top:1px solid {p['badge_bg']};border-right:1px solid {p['badge_bg']};border-bottom:1px solid {p['badge_bg']};">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap;">
    <div style="flex:1;min-width:0;">
      <p style="font-size:10px;font-weight:700;color:{p['border_l']};letter-spacing:.1em;text-transform:uppercase;margin:0 0 6px;">AI Recommendation</p>
      <p style="font-size:15px;font-weight:700;color:#0f172a;margin:0 0 5px;line-height:1.4;">{finding}</p>
      <p style="font-size:13px;color:#475569;margin:0;line-height:1.6;">{action}</p>
      {f'<p style="font-size:11px;color:#64748b;margin:6px 0 0;padding-top:6px;border-top:1px solid rgba(0,0,0,0.08);">{detail}</p>' if detail else ""}
    </div>
    <div style="flex-shrink:0;">
      <span style="display:inline-block;background-color:{p['badge_bg']};color:{p['badge_fg']};border-radius:8px;padding:8px 16px;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;">{p['icon']} {risk_level} Risk</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def compliance_ribbon() -> None:
    st.markdown("""
<div style="margin-top:32px;padding:14px 20px;border-top:1px solid #e2e8f0;display:flex;align-items:center;flex-wrap:wrap;gap:14px;background-color:white;border-radius:12px;border:1px solid #e2e8f0;">
  <div style="display:flex;gap:14px;flex-wrap:wrap;flex:1;align-items:center;">
    <span style="font-size:11px;font-weight:600;color:#059669;">&#10003; DPDP Act 2023</span>
    <span style="font-size:11px;font-weight:600;color:#059669;">&#10003; NDCT Rules 2019</span>
    <span style="font-size:11px;font-weight:600;color:#059669;">&#10003; ICMR GCP Guidelines</span>
    <span style="font-size:11px;font-weight:600;color:#059669;">&#10003; MeitY AI Ethics</span>
    <span style="font-size:11px;font-weight:600;color:#1d4ed8;">&#10003; Schedule Y</span>
  </div>
  <span style="font-size:10px;color:#9ca3af;">&#169; 2026 Nirnay &middot; IndiaAI / CDSCO Hackathon</span>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def to_json_bytes(payload: object) -> bytes:
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def to_csv_bytes(rows: list[dict]) -> bytes:
    if not rows:
        return b""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")
