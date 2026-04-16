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
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800;1,14..32,400&display=swap');
html,body,[class*="css"]{font-family:'Inter',system-ui,-apple-system,sans-serif;}
#MainMenu,footer{visibility:hidden;}
header{visibility:hidden;}
/* Always keep the sidebar collapse/expand toggle visible */
[data-testid="collapsedControl"]{visibility:visible!important;display:flex!important;}

/* ── App background ── */
.stApp{background:linear-gradient(155deg,#edf1f7 0%,#f4f7fb 55%,#eaeff7 100%)!important;}

/* ── Sidebar ── */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#050d1a 0%,#0a1e3d 50%,#0d2a52 100%)!important;border-right:1px solid rgba(255,255,255,0.04)!important;}
section[data-testid="stSidebar"] *{color:white!important;}
section[data-testid="stSidebar"] .stMarkdown p{color:rgba(255,255,255,0.78)!important;}
section[data-testid="stSidebar"] .stSelectbox>div>div{background:rgba(255,255,255,0.09)!important;border:1px solid rgba(255,255,255,0.18)!important;border-radius:9px!important;}
section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:white!important;font-weight:700!important;}

/* ── Hero / Banner ── */
.hero{background:linear-gradient(135deg,#050d1a 0%,#0a1e3d 40%,#0d3366 100%);border-radius:16px;padding:28px 36px;margin-bottom:18px;box-shadow:0 8px 32px rgba(5,13,26,0.25),inset 0 1px 0 rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.05);position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;top:-40%;right:-5%;width:380px;height:380px;background:radial-gradient(circle,rgba(255,153,51,0.07) 0%,transparent 70%);pointer-events:none;}
.hero h1{color:white;font-size:22px;font-weight:800;margin:0;letter-spacing:-0.3px;}
.hero .sub{color:rgba(255,255,255,0.62);font-size:13px;margin:5px 0 0;line-height:1.6;}
.hero-badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;}
.hbadge{background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:20px;padding:4px 12px;font-size:11px;color:rgba(255,255,255,0.82);font-weight:500;}
.hbadge.g{border-color:rgba(74,222,128,0.5);color:#4ade80;background:rgba(74,222,128,0.08);}

/* ── Cards ── */
.card{background:white;border:1px solid rgba(10,34,64,0.09);border-radius:16px;padding:1.1rem 1.25rem;box-shadow:0 4px 16px rgba(10,34,64,0.07),0 1px 4px rgba(10,34,64,0.04);margin-bottom:1rem;}
.case-chip{display:inline-block;background:rgba(0,82,204,0.08);color:#0052cc;border:1px solid rgba(0,82,204,0.2);border-radius:999px;padding:0.2rem 0.65rem;font-size:0.75rem;font-weight:600;}
.small-note{color:#5c6b7a;font-size:0.9rem;}

/* ── Section headers ── */
.sec-hd{display:flex;align-items:center;gap:14px;margin-bottom:22px;padding-bottom:16px;border-bottom:1.5px solid #e8edf4;}
.sec-ic{width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
.ic-blue{background:linear-gradient(135deg,#dbeafe,#bfdbfe);}.ic-teal{background:linear-gradient(135deg,#ccfbf1,#99f6e4);}
.ic-purple{background:linear-gradient(135deg,#ede9fe,#ddd6fe);}.ic-amber{background:linear-gradient(135deg,#fef3c7,#fde68a);}
.ic-sky{background:linear-gradient(135deg,#e0f2fe,#bae6fd);}.ic-pink{background:linear-gradient(135deg,#fce7f3,#fbcfe8);}
.sec-hd h2{font-size:18px;font-weight:700;color:#0f1c2e;margin:0;letter-spacing:-0.2px;}
.sec-hd p{font-size:12.5px;color:#64748b;margin:3px 0 0;line-height:1.5;}

/* ── Upload card ── */
.upload-card{background:white;border:2px dashed #c8d8eb;border-radius:16px;padding:22px 24px;box-shadow:0 2px 12px rgba(10,34,64,0.04);margin-bottom:14px;transition:border-color 0.2s;}
.upload-card:hover{border-color:#FF9933;}
.upload-card h4{color:#0f1c2e;font-size:14px;font-weight:600;margin:0 0 10px;}
.or-line{display:flex;align-items:center;gap:10px;margin:12px 0;color:#94a3b8;font-size:12px;font-weight:500;}
.or-line::before,.or-line::after{content:'';flex:1;height:1px;background:#e2e8f0;}

/* ── PII chips ── */
.pii-chips{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0;}
.chip{display:inline-flex;align-items:center;gap:4px;border-radius:20px;padding:4px 12px;font-size:11.5px;font-weight:600;}
.cr{background:#fee2e2;color:#991b1b;}.ca{background:#fef3c7;color:#92400e;}
.cb{background:#dbeafe;color:#1e40af;}.cp{background:#ede9fe;color:#5b21b6;}
.ct{background:#ccfbf1;color:#065f46;}.cg{background:#f1f5f9;color:#475569;}

/* ── Result / status cards ── */
.rc{background:white;border-radius:10px;padding:14px 18px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin:8px 0;border-left:4px solid #0052cc;font-size:13px;line-height:1.6;}
.rc.ok{border-left-color:#16a34a;background:#f0fdf4;color:#14532d;}
.rc.warn{border-left-color:#d97706;background:#fffbeb;color:#78350f;}
.rc.err{border-left-color:#dc2626;background:#fef2f2;color:#7f1d1d;}
.rc.info{border-left-color:#0284c7;background:#f0f9ff;color:#0c4a6e;}

/* ── Table wrapper ── */
.tw{background:white;border-radius:12px;padding:6px;box-shadow:0 2px 8px rgba(0,0,0,0.05);margin:8px 0;border:1px solid rgba(10,34,64,0.07);}

/* ── Misc helpers ── */
.dup-session{background:#f0f9ff;border:1px solid #bae6fd;border-radius:12px;padding:14px 18px;margin-bottom:12px;font-size:13px;color:#0369a1;line-height:1.6;}
.audio-note{background:#fef9c3;border:1px solid #fbbf24;border-radius:8px;padding:10px 14px;font-size:12px;color:#78350f;margin:8px 0;}
.entity-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;font-size:13px;min-height:160px;white-space:pre-wrap;line-height:1.6;}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{background:#0a1628!important;border-radius:12px!important;padding:5px!important;gap:2px!important;box-shadow:0 4px 16px rgba(5,13,26,0.3)!important;}
.stTabs [data-baseweb="tab"]{border-radius:8px!important;font-size:12px!important;font-weight:500!important;color:rgba(255,255,255,0.5)!important;padding:8px 14px!important;transition:all 0.2s!important;}
.stTabs [data-baseweb="tab"]:hover{color:rgba(255,255,255,0.85)!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#0052cc,#0077cc)!important;color:white!important;box-shadow:0 2px 8px rgba(0,82,204,0.35)!important;}
.stTabs [data-baseweb="tab-border"]{display:none!important;}
.stTabs [data-baseweb="tab-panel"]{background:white!important;border-radius:0 0 14px 14px!important;padding:22px!important;box-shadow:0 4px 16px rgba(10,34,64,0.06)!important;border:1px solid rgba(10,34,64,0.07)!important;border-top:none!important;}

/* ── Buttons ── */
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#0a2240 0%,#003087 100%)!important;color:white!important;border:none!important;border-radius:9px!important;font-weight:600!important;font-size:13px!important;padding:9px 18px!important;box-shadow:0 4px 12px rgba(10,34,64,0.25)!important;transition:all 0.2s!important;letter-spacing:0.01em!important;}
.stButton>button[kind="primary"]:hover{background:linear-gradient(135deg,#003087 0%,#0052cc 100%)!important;box-shadow:0 6px 18px rgba(10,34,64,0.35)!important;transform:translateY(-1px)!important;}
.stButton>button:not([kind="primary"]){border-radius:9px!important;font-size:13px!important;font-weight:500!important;transition:all 0.2s!important;}
.stButton>button:not([kind="primary"]):hover{border-color:#0052cc!important;color:#0052cc!important;}
.stDownloadButton>button{border-radius:9px!important;border:1.5px solid #0052cc!important;color:#0052cc!important;font-weight:500!important;font-size:13px!important;transition:all 0.2s!important;}
.stDownloadButton>button:hover{background:rgba(0,82,204,0.05)!important;box-shadow:0 2px 8px rgba(0,82,204,0.15)!important;}

/* ── Form fields ── */
.stTextArea textarea{border:1.5px solid #e2e8f0!important;border-radius:10px!important;font-size:13px!important;background:#fafbfc!important;line-height:1.6!important;transition:border-color 0.2s!important;}
.stTextArea textarea:focus{border-color:#0052cc!important;box-shadow:0 0 0 2px rgba(0,82,204,0.08)!important;}
.stTextInput input{border-radius:9px!important;border:1.5px solid #e2e8f0!important;font-size:13px!important;transition:border-color 0.2s!important;}
.stTextInput input:focus{border-color:#0052cc!important;box-shadow:0 0 0 2px rgba(0,82,204,0.08)!important;}

/* ── Metrics ── */
[data-testid="stMetricValue"]{font-size:26px!important;font-weight:800!important;color:#0a1628!important;}
[data-testid="stMetricLabel"]{font-size:12px!important;color:#64748b!important;font-weight:500!important;}
[data-testid="metric-container"]{background:white!important;border-radius:12px!important;padding:14px 18px!important;box-shadow:0 2px 8px rgba(10,34,64,0.07)!important;border:1px solid rgba(10,34,64,0.07)!important;}

/* ── Expanders ── */
.streamlit-expanderHeader{font-weight:600!important;font-size:13px!important;color:#0f1c2e!important;}
[data-testid="stExpander"]{border:1px solid #e2e8f0!important;border-radius:12px!important;box-shadow:0 1px 4px rgba(0,0,0,0.04)!important;}

/* ── Progress bar ── */
[data-testid="stProgressBar"]>div>div{background:linear-gradient(90deg,#0052cc,#0077b6)!important;border-radius:99px!important;}
[data-testid="stProgressBar"]>div{border-radius:99px!important;background:#e2e8f0!important;}

/* ── Alerts ── */
[data-testid="stAlert"]{border-radius:10px!important;font-size:13px!important;}

/* ── Selectbox ── */
[data-testid="stSelectbox"]>div>div{border-radius:9px!important;font-size:13px!important;}
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
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
    <span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:rgba(255,153,51,0.9);background:rgba(255,153,51,0.12);border:1px solid rgba(255,153,51,0.25);border-radius:20px;padding:3px 10px;">{DEMO_MODE_LABEL}</span>
  </div>
  <h1>{title}</h1>
  <p class="sub">{subtitle}</p>
  <div class="hero-badges">
    <span class="hbadge g">✓ DPDP Act 2023</span>
    <span class="hbadge g">✓ NDCT Rules 2019</span>
    <span class="hbadge g">✓ Schedule Y</span>
    <span class="hbadge g">✓ ICMR GCP</span>
    <span class="hbadge g">✓ MeitY AI Ethics</span>
  </div>
  <p style="margin-top:10px;font-size:11px;color:rgba(255,255,255,0.45);line-height:1.5;">{APP_DISCLAIMER}</p>
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
        "Critical": {"bg":"#fef2f2","border":"#fca5a5","accent":"#dc2626","badge_bg":"#fee2e2","badge_fg":"#991b1b","icon":"🔴"},
        "High":     {"bg":"#fff7ed","border":"#fed7aa","accent":"#ea580c","badge_bg":"#ffedd5","badge_fg":"#9a3412","icon":"🟠"},
        "Medium":   {"bg":"#fefce8","border":"#fef08a","accent":"#ca8a04","badge_bg":"#fef9c3","badge_fg":"#854d0e","icon":"🟡"},
        "Low":      {"bg":"#f0fdf4","border":"#bbf7d0","accent":"#16a34a","badge_bg":"#dcfce7","badge_fg":"#166534","icon":"🟢"},
    }
    p = palette.get(risk_level, palette["Medium"])
    st.markdown(f"""
<div style="border-radius:14px;padding:20px 24px;margin:16px 0;background:{p['bg']};border:1px solid {p['border']};border-left:5px solid {p['accent']};box-shadow:0 2px 12px rgba(0,0,0,0.06);">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap;">
    <div style="flex:1;min-width:0;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
        <div style="width:5px;height:5px;border-radius:50%;background:{p['accent']};flex-shrink:0;"></div>
        <span style="font-size:10px;font-weight:700;color:{p['accent']};letter-spacing:.12em;text-transform:uppercase;">AI Recommendation</span>
      </div>
      <div style="font-size:15px;font-weight:700;color:#0f1c2e;margin-bottom:6px;line-height:1.4;">{finding}</div>
      <div style="font-size:13px;color:#475569;line-height:1.6;">{action}</div>
      {f'<div style="font-size:11px;color:#64748b;margin-top:8px;padding-top:8px;border-top:1px solid rgba(0,0,0,0.07);">{detail}</div>' if detail else ""}
    </div>
    <div style="flex-shrink:0;text-align:center;">
      <div style="background:{p['badge_bg']};color:{p['badge_fg']};border-radius:10px;padding:9px 18px;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;border:1px solid {p['border']};white-space:nowrap;">{p['icon']} {risk_level} Risk</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def compliance_ribbon() -> None:
    st.markdown("""
<div style="margin-top:40px;padding:16px 20px;border-top:1px solid #e2e8f0;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:white;border-radius:12px;box-shadow:0 1px 4px rgba(10,34,64,0.05);border:1px solid rgba(10,34,64,0.07);">
  <div style="display:flex;gap:12px;flex-wrap:wrap;flex:1;align-items:center;">
    <span style="font-size:10px;font-weight:700;color:#059669;display:inline-flex;align-items:center;gap:4px;"><span style="background:rgba(5,150,105,0.1);border:1px solid rgba(5,150,105,0.25);border-radius:4px;padding:1px 5px;">✓</span>DPDP Act 2023</span>
    <span style="font-size:10px;font-weight:700;color:#059669;display:inline-flex;align-items:center;gap:4px;"><span style="background:rgba(5,150,105,0.1);border:1px solid rgba(5,150,105,0.25);border-radius:4px;padding:1px 5px;">✓</span>NDCT Rules 2019</span>
    <span style="font-size:10px;font-weight:700;color:#059669;display:inline-flex;align-items:center;gap:4px;"><span style="background:rgba(5,150,105,0.1);border:1px solid rgba(5,150,105,0.25);border-radius:4px;padding:1px 5px;">✓</span>ICMR GCP Guidelines</span>
    <span style="font-size:10px;font-weight:700;color:#059669;display:inline-flex;align-items:center;gap:4px;"><span style="background:rgba(5,150,105,0.1);border:1px solid rgba(5,150,105,0.25);border-radius:4px;padding:1px 5px;">✓</span>MeitY AI Ethics</span>
    <span style="font-size:10px;font-weight:700;color:#0052cc;display:inline-flex;align-items:center;gap:4px;"><span style="background:rgba(0,82,204,0.08);border:1px solid rgba(0,82,204,0.2);border-radius:4px;padding:1px 5px;">✓</span>Schedule Y</span>
  </div>
  <span style="font-size:10px;color:#94a3b8;font-weight:500;white-space:nowrap;">© 2026 Nirnay · IndiaAI / CDSCO Hackathon</span>
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
