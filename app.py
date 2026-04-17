"""
app.py — Nirnay · CDSCO AI Hackathon 2026
------------------------------------------
Entry point. All 6 guideline-mandated features + full reviewer workflow.

HOW TO RUN:
    streamlit run app.py

FOR JUDGES:
    • The app opens on the Command Dashboard with a pre-loaded sample packet.
    • Use the LEFT SIDEBAR to switch between the two sample case packets
      or to walk through the CDSCO review workflow screens.
    • Use the TABS at the top of the main panel to access all 6 AI features.
    • Upload your own documents inside any feature tab — the AI engines
      process your real files immediately. Sample data is only a fallback.
    • All outputs (PDF, CSV, JSON, TXT) are downloadable from within each tab.

FEATURES (per CDSCO-IndiaAI Hackathon Guidelines, Section 3.I):
    01 Anonymisation     — PII/PHI detection, two-step DPDP Act 2023 process
    02 Summarisation     — SAE narration, SUGAM checklist, meeting transcripts
    03 Completeness      — NDCT Rules 2019 / Form CT mandatory field assessment
    04 Classification    — SAE severity grading + duplicate detection
    05 Comparison        — Semantic document diff, substantive change flagging
    06 Inspection Report — CDSCO GCP site inspection report generator

ARCHITECTURE:
    app.py          — Main entry point (this file)
    components.py   — UI components, session state, audit trail, sidebar
    engine.py       — All processing engines (anonymisation, summarisation, etc.)
    demo_data.py    — Sample case packets (pre-loaded for evaluation)
    requirements.txt
"""

from __future__ import annotations

import datetime
import hashlib
import json as _json
import re
from copy import deepcopy

import pandas as pd
import streamlit as st
import streamlit.components.v1 as _cv1

from demo_data import get_case_library
from components import (
    APP_DISCLAIMER,
    CLAUDE_OK,
    HINDI_LOGO_DATA_URI,
    SCREENS,
    add_audit_event,
    ai_recommendation_card,
    apply_redaction_filters,
    apply_styles,
    audit_dataframe,
    compliance_ribbon,
    confirm_reviewer_action,
    configure_page,
    create_compare_packet,
    create_sae_packet,
    generate_audit_packet,
    get_active_case,
    init_state,
    render_banner,
    render_case_header,
    render_metrics,
    render_top_nav,
    run_categorisation,
    save_active_case,
    set_screen,
    to_csv_bytes,
    to_json_bytes,
    validate_redaction,
)
from engine import (
    CHIP_MAP,
    assess_completeness,
    classify_sae,
    claude_summarise,
    compare_documents,
    detect_duplicates,
    extract_text,
    generate_inspection_report,
    run_anonymisation,
    summarise_checklist,
    summarise_meeting,
    summarise_sae,
)

# ── Bootstrap ─────────────────────────────────────────────────────────────────
configure_page()
init_state()
apply_styles()

# ── Login state ───────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "_login_failed" not in st.session_state:
    st.session_state["_login_failed"] = False

VALID_USER = "admin"
VALID_PASS = "nirnay2026"

LANDING_STAGE_ROUTES = {
    "Intake": {"screen": "Document Intake", "active_tab": 1, "active_ribbon_tab": "📥 Document Intake"},
    "Protected View": {"screen": "Protected View", "active_tab": 2, "active_ribbon_tab": "🕵️ Anonymisation"},
    "Triage": {"screen": "Command Dashboard", "active_tab": 5, "active_ribbon_tab": "🏷️ Categorisation"},
    "Validation": {"screen": "Command Dashboard", "active_tab": 4, "active_ribbon_tab": "✅ Completeness"},
    "Compare": {"screen": "Version Compare", "active_tab": 6, "active_ribbon_tab": "🔄 Version Compare"},
    "Audit Packet": {"screen": "Audit Trail", "active_tab": 8, "active_ribbon_tab": "📜 Audit Trail"},
}


def apply_landing_stage_route(stage_name: str) -> None:
    route = LANDING_STAGE_ROUTES.get(stage_name, LANDING_STAGE_ROUTES["Intake"])
    st.session_state.screen = route["screen"]
    st.session_state.active_tab = route["active_tab"]
    st.session_state.active_ribbon_tab = route["active_ribbon_tab"]

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE — native Streamlit inputs, full CSS dark styling
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state["logged_in"]:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
*{font-family:'Inter',system-ui,sans-serif;box-sizing:border-box;}
section[data-testid="stSidebar"]{display:none!important;}
header{display:none!important;}
footer{display:none!important;}
.stApp{
  background:
    radial-gradient(circle at top left, rgba(255,159,47,0.12), transparent 26%),
    radial-gradient(circle at 86% 18%, rgba(37,99,235,0.11), transparent 24%),
    #06101f!important;
  color:#e2e8f0!important;
}
.block-container{
  max-width:1360px!important;
  padding:28px 26px 56px!important;
}
[data-testid="column"]{
  min-width:0!important;
}
.landing-shell{
  display:flex;
  flex-direction:column;
  gap:28px;
}
.authority-bar{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:18px;
  flex-wrap:wrap;
  padding-bottom:18px;
  border-bottom:1px solid rgba(255,255,255,0.08);
}
.authority-left{
  display:flex;
  align-items:center;
  gap:18px;
  flex-wrap:wrap;
  min-width:0;
}
.authority-left img{
  display:block;
  max-width:240px;
  width:100%;
  height:auto;
  border-radius:18px;
  box-shadow:0 18px 34px rgba(0,0,0,0.18);
}
.authority-stack{
  display:flex;
  flex-direction:column;
  gap:6px;
  max-width:720px;
}
.authority-kicker{
  font-size:11px;
  font-weight:700;
  letter-spacing:.18em;
  text-transform:uppercase;
  color:rgba(255,255,255,0.45);
}
.authority-title{
  font-size:15px;
  line-height:1.6;
  color:#cbd5e1;
}
.authority-right{
  display:flex;
  align-items:center;
  gap:10px;
  flex-wrap:wrap;
  justify-content:flex-end;
}
.authority-chip{
  display:inline-flex;
  align-items:center;
  border:1px solid rgba(255,255,255,0.12);
  border-radius:999px;
  padding:7px 12px;
  font-size:11px;
  font-weight:700;
  color:#e2e8f0;
  background:rgba(255,255,255,0.04);
}
.authority-wordmark{
  display:flex;
  align-items:center;
  justify-content:center;
  padding:8px 12px;
  border-radius:16px;
  border:1px solid rgba(255,255,255,0.12);
  background:rgba(255,255,255,0.04);
}
.authority-wordmark img{
  display:block;
  max-width:160px;
  width:100%;
  height:auto;
  border-radius:10px;
}
.section-kicker{
  font-size:11px;
  font-weight:700;
  letter-spacing:.18em;
  text-transform:uppercase;
  color:rgba(255,255,255,0.42);
  margin-bottom:10px;
}
.hero-title{
  font-size:58px;
  line-height:1.02;
  font-weight:800;
  letter-spacing:-0.04em;
  color:#f8fafc;
  margin:0 0 14px;
}
.hero-sub{
  font-size:18px;
  line-height:1.65;
  color:#94a3b8;
  max-width:760px;
  margin-bottom:20px;
}
.live-metric{
  background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:18px;
  padding:16px 18px;
  min-height:118px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,0.04);
}
.live-metric-label{
  font-size:11px;
  font-weight:700;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:rgba(255,255,255,0.44);
  margin-bottom:12px;
}
.live-metric-value{
  font-size:28px;
  font-weight:800;
  color:#f8fafc;
  margin-bottom:6px;
}
.live-metric-detail{
  font-size:13px;
  line-height:1.55;
  color:#94a3b8;
}
.workflow-detail{
  background:linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.03));
  border:1px solid rgba(255,255,255,0.08);
  border-radius:20px;
  padding:18px 20px;
  margin-top:14px;
}
.workflow-status{
  display:inline-flex;
  align-items:center;
  gap:8px;
  border-radius:999px;
  background:rgba(255,159,47,0.12);
  border:1px solid rgba(255,159,47,0.26);
  color:#ffd7a4;
  padding:6px 12px;
  font-size:11px;
  font-weight:700;
  letter-spacing:.08em;
  text-transform:uppercase;
  margin-bottom:14px;
}
.workflow-title{
  font-size:24px;
  font-weight:700;
  color:#f8fafc;
  margin-bottom:8px;
}
.workflow-copy{
  font-size:14px;
  line-height:1.7;
  color:#94a3b8;
  margin-bottom:16px;
}
.workflow-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:12px;
}
.workflow-cell{
  border-top:1px solid rgba(255,255,255,0.08);
  padding-top:10px;
}
.workflow-cell-label{
  font-size:11px;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:rgba(255,255,255,0.4);
  margin-bottom:4px;
}
.workflow-cell-value{
  font-size:13px;
  line-height:1.55;
  color:#e2e8f0;
}
.signal-panel,
.access-panel,
.trust-detail{
  background:linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.035));
  border:1px solid rgba(255,255,255,0.08);
  border-radius:22px;
  padding:20px 22px;
  box-shadow:0 20px 34px rgba(0,0,0,0.16);
}
.signal-panel{
  min-height:430px;
}
.panel-eyebrow{
  font-size:11px;
  font-weight:700;
  letter-spacing:.18em;
  text-transform:uppercase;
  color:rgba(255,255,255,0.44);
  margin-bottom:10px;
}
.panel-title{
  font-size:28px;
  font-weight:800;
  color:#f8fafc;
  line-height:1.1;
  margin-bottom:10px;
}
.panel-sub{
  font-size:14px;
  line-height:1.7;
  color:#94a3b8;
  margin-bottom:18px;
}
.panel-chip-row{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-bottom:18px;
}
.panel-chip{
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  border:1px solid rgba(255,255,255,0.1);
  background:rgba(255,255,255,0.04);
  color:#e2e8f0;
  padding:6px 10px;
  font-size:11px;
  font-weight:700;
}
.panel-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:12px;
}
.panel-stat{
  background:rgba(255,255,255,0.03);
  border:1px solid rgba(255,255,255,0.07);
  border-radius:16px;
  padding:14px;
}
.panel-stat-label{
  font-size:11px;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:rgba(255,255,255,0.4);
  margin-bottom:5px;
}
.panel-stat-value{
  font-size:15px;
  font-weight:700;
  color:#f8fafc;
  line-height:1.45;
}
.panel-note{
  margin-top:16px;
  padding-top:14px;
  border-top:1px solid rgba(255,255,255,0.08);
  font-size:13px;
  line-height:1.6;
  color:#cbd5e1;
}
.landing-section-head{
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:18px;
  flex-wrap:wrap;
  margin-bottom:14px;
}
.landing-section-title{
  font-size:28px;
  font-weight:800;
  color:#f8fafc;
  letter-spacing:-0.03em;
}
.landing-section-copy{
  font-size:14px;
  color:#94a3b8;
  max-width:760px;
  line-height:1.6;
}
.workflow-row{
  display:grid;
  grid-template-columns:90px 1.05fr 1.2fr 1fr;
  gap:14px;
  align-items:start;
  padding:14px 0;
  border-top:1px solid rgba(255,255,255,0.08);
}
.workflow-row:first-child{
  border-top:none;
  padding-top:0;
}
.workflow-row-step{
  font-size:12px;
  font-weight:700;
  color:#ffd7a4;
  letter-spacing:.12em;
  text-transform:uppercase;
}
.workflow-row-title{
  font-size:15px;
  font-weight:700;
  color:#f8fafc;
  margin-bottom:4px;
}
.workflow-row-copy,
.workflow-row-gate{
  font-size:13px;
  line-height:1.6;
  color:#94a3b8;
}
[data-testid="stExpander"]{
  background:rgba(255,255,255,0.04)!important;
  border:1px solid rgba(255,255,255,0.08)!important;
  border-radius:18px!important;
  overflow:hidden!important;
}
[data-testid="stExpander"] details{
  background:transparent!important;
}
[data-testid="stExpander"] details summary{
  padding:2px 0!important;
}
[data-testid="stExpander"] details summary p{
  font-size:14px!important;
  font-weight:700!important;
  color:#f8fafc!important;
}
[data-testid="stExpanderDetails"]{
  padding-top:6px!important;
}
.capability-note{
  font-size:13px;
  line-height:1.65;
  color:#94a3b8;
}
.trust-title{
  font-size:20px;
  font-weight:700;
  color:#f8fafc;
  margin-bottom:6px;
}
.trust-copy{
  font-size:14px;
  line-height:1.7;
  color:#cbd5e1;
  margin-bottom:10px;
}
.trust-signal{
  font-size:13px;
  line-height:1.6;
  color:#94a3b8;
}
.landing-footer{
  margin-top:10px;
  padding-top:18px;
  border-top:1px solid rgba(255,255,255,0.08);
  font-size:12px;
  color:rgba(255,255,255,0.42);
  text-align:center;
}
.stButton>button{
  border-radius:14px!important;
  border:1px solid rgba(255,255,255,0.12)!important;
  background:rgba(255,255,255,0.035)!important;
  color:#e2e8f0!important;
  font-size:13px!important;
  font-weight:700!important;
  min-height:46px!important;
  box-shadow:none!important;
}
.stButton>button:hover{
  border-color:rgba(255,159,47,0.45)!important;
  color:white!important;
}
.stButton>button[kind="primary"],
[data-testid="stFormSubmitButton"] button{
  background:#ff9f2f!important;
  color:#07111f!important;
  border:1px solid #ffbf73!important;
}
[data-testid="stFormSubmitButton"] button:hover{
  background:#ffb14e!important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextInput"] p{
  color:rgba(255,255,255,0.62)!important;
  font-size:11px!important;
  font-weight:700!important;
  letter-spacing:.12em!important;
  text-transform:uppercase!important;
}
[data-testid="stTextInput"] input{
  background:#071426!important;
  border:1.5px solid rgba(255,255,255,0.14)!important;
  border-radius:12px!important;
  color:#f8fafc!important;
  font-size:14px!important;
}
[data-testid="stTextInput"] input::placeholder{
  color:rgba(255,255,255,0.28)!important;
}
[data-testid="stTextInput"] input:focus{
  border-color:#ff9f2f!important;
  outline:none!important;
}
[data-testid="stForm"]{
  background:transparent!important;
  border:none!important;
  padding:0!important;
}
@media (max-width: 1080px){
  .hero-title{font-size:44px;}
  .panel-grid,
  .workflow-grid{grid-template-columns:1fr;}
  .workflow-row{grid-template-columns:70px 1fr;}
}
@media (max-width: 768px){
  .block-container{padding:18px 16px 42px!important;}
  .hero-title{font-size:36px;}
  .hero-sub{font-size:16px;}
  .authority-left img{max-width:190px;}
}
.stApp{
  background:
    radial-gradient(circle at 12% 8%, rgba(135, 208, 196, 0.26), transparent 26%),
    radial-gradient(circle at 86% 10%, rgba(150, 209, 244, 0.3), transparent 30%),
    linear-gradient(180deg, #f5fcfb 0%, #eef7fb 48%, #eef8f2 100%)!important;
  color:#1f2937!important;
}
.block-container{padding:8px 24px 48px!important;}
.landing-topbar{
  display:flex;
  align-items:flex-start;
  justify-content:flex-start;
  gap:10px;
  flex-wrap:wrap;
  padding-bottom:14px;
  margin-bottom:14px;
  border-bottom:1px solid #dbe4ef;
}
.landing-brand-stack{
  display:flex;
  flex-direction:column;
  align-items:flex-start;
  gap:8px;
}
.landing-brand img{
  display:block;
  max-width:170px;
  width:100%;
  height:auto;
  border-radius:12px;
}
.landing-markers{
  display:flex;
  align-items:center;
  gap:0;
  flex-wrap:wrap;
  justify-content:flex-start;
  margin-left:0;
}
.landing-marker{
  display:inline-flex;
  align-items:center;
  padding:0 12px;
  font-size:12px;
  font-weight:600;
  color:#6b7d92;
  background:none;
  border:none;
  line-height:1;
}
.landing-marker + .landing-marker{
  border-left:1px solid #dbe4ef;
}
.hero-card,.preview-card,.access-card,.stage-panel{
  background:rgba(255,255,255,0.94);
  border:1px solid #dbe4ef;
  border-radius:24px;
  box-shadow:0 18px 42px rgba(51,74,107,0.08);
}
.hero-card{
  padding:28px 30px;
  background:
    radial-gradient(circle at top right, rgba(255,153,51,0.10), transparent 26%),
    radial-gradient(circle at bottom left, rgba(19,92,175,0.07), transparent 30%),
    rgba(255,255,255,0.95);
}
.hero-kicker{
  font-size:12px;
  font-weight:700;
  color:#5d748d;
  margin-bottom:10px;
}
.hero-title{font-size:52px;color:#1f2937;line-height:1.05;margin:0 0 12px;}
.hero-sub{font-size:17px;line-height:1.7;color:#69798e;max-width:720px;margin-bottom:0;}
.metric-tile{
  background:#f8fafc;
  border:1px solid #dde6f0;
  border-radius:18px;
  padding:16px 18px;
  min-height:102px;
}
.metric-label{font-size:11px;font-weight:600;color:#6c7d91;margin-bottom:10px;}
.metric-value{font-size:28px;font-weight:800;color:#184d8d;margin-bottom:4px;}
.metric-detail{font-size:13px;line-height:1.55;color:#6b7b90;}
.preview-card{padding:24px 24px 20px;min-height:318px;}
.preview-eyebrow{font-size:12px;font-weight:700;color:#5e7490;margin-bottom:10px;}
.preview-title{font-size:26px;line-height:1.15;font-weight:800;color:#1f2937;margin-bottom:10px;}
.preview-copy{font-size:14px;line-height:1.65;color:#6b7b90;margin-bottom:16px;}
.preview-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:12px;
}
.preview-field{
  padding:13px 14px;
  border-radius:16px;
  border:1px solid #e0e8f1;
  background:#f8fafc;
}
.preview-label{font-size:11px;color:#708196;margin-bottom:4px;}
.preview-value{font-size:15px;font-weight:700;color:#1f2937;line-height:1.45;}
.access-card{padding:18px 22px 16px;margin-top:14px;}
.access-title{font-size:22px;font-weight:800;color:#1f2937;margin-bottom:6px;}
.access-copy{font-size:13px;line-height:1.6;color:#718197;margin-bottom:12px;}
.workflow-strip-title{font-size:13px;font-weight:700;color:#61768f;margin:18px 0 8px;}
[data-testid="stRadio"] > label{display:none!important;}
[data-testid="stRadio"] [role="radiogroup"]{
  display:flex;
  gap:22px;
  flex-wrap:wrap;
  border-bottom:1px solid #dbe4ef;
  padding:0 0 10px;
}
[data-testid="stRadio"] label{
  display:flex!important;
  align-items:center;
  padding:0 0 10px 0!important;
  border-bottom:2px solid transparent;
  margin:0!important;
  color:#73859c!important;
  font-size:14px!important;
  font-weight:600!important;
  background:transparent!important;
}
[data-testid="stRadio"] label > div:first-child{display:none!important;}
[data-testid="stRadio"] label:has(input:checked){
  color:#1d4d8d!important;
  border-bottom-color:#1d4d8d;
}
.stage-panel{margin-top:18px;padding:22px 24px;}
.stage-panel-head{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:16px;
  flex-wrap:wrap;
  margin-bottom:12px;
}
.stage-name{font-size:24px;font-weight:800;color:#1f2937;margin-bottom:6px;}
.stage-copy{font-size:14px;line-height:1.7;color:#68788e;max-width:780px;}
.stage-accent{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:7px 12px;
  border-radius:999px;
  background:#eef5ff;
  border:1px solid #cfe0f7;
  color:#22508d;
  font-size:12px;
  font-weight:700;
}
.stage-signal-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:14px;
  margin:16px 0 18px;
}
.stage-signal{
  padding:14px 16px;
  border-radius:16px;
  background:#f8fafc;
  border:1px solid #dfe7f0;
}
.stage-signal-label{font-size:11px;color:#708297;margin-bottom:5px;}
.stage-signal-value{font-size:14px;font-weight:700;color:#223246;line-height:1.55;}
.landing-footer{
  margin-top:18px;
  padding-top:18px;
  border-top:1px solid #dbe4ef;
  text-align:center;
  font-size:11px!important;
  color:#7b8795;
}
.stButton>button{
  min-height:44px!important;
  border-radius:14px!important;
  border:1px solid #d6dfeb!important;
  background:#ffffff!important;
  color:#26456f!important;
  font-size:13px!important;
  font-weight:600!important;
  box-shadow:none!important;
}
.stButton>button:hover{border-color:#aac1df!important;color:#1b4c8c!important;}
.stButton>button[kind="primary"],[data-testid="stFormSubmitButton"] button{
  background:#20528f!important;
  color:#ffffff!important;
  border:1px solid #20528f!important;
}
[data-testid="stFormSubmitButton"] button:hover{background:#17457f!important;}
[data-testid="stTextInput"] label,[data-testid="stTextInput"] p{
  color:#6b7d93!important;
  font-size:11px!important;
  font-weight:600!important;
  letter-spacing:0!important;
  text-transform:none!important;
}
[data-testid="stTextInput"] input{
  background:#f8fafc!important;
  border:1.4px solid #d7e1ec!important;
  border-radius:12px!important;
  color:#1f2937!important;
  font-size:14px!important;
}
[data-testid="stTextInput"] input:focus{border-color:#7aa0d5!important;outline:none!important;}
[data-testid="stForm"]{background:transparent!important;border:none!important;padding:0!important;}
@media (max-width: 1100px){
  .hero-title{font-size:42px;}
  .preview-grid,.stage-signal-grid{grid-template-columns:1fr 1fr;}
}
@media (max-width: 760px){
  .block-container{padding:8px 16px 38px!important;}
  .hero-title{font-size:34px;}
  .hero-sub{font-size:15px;}
  .landing-brand img{max-width:180px;}
  .preview-grid,.stage-signal-grid{grid-template-columns:1fr;}
}
</style>
""", unsafe_allow_html=True)
    sample_case = deepcopy(st.session_state.demo_cases[st.session_state.active_case_key])
    protected_count = len(sample_case["protected_view"]["entities"])
    compare_count = len(sample_case["documents"]["amendment"]["changes"])
    missing_count = len([item for item in sample_case["sae_review"]["missing_info"] if not item["resolved"]])

    if "landing_stage" not in st.session_state:
        st.session_state["landing_stage"] = "Intake"
    if "landing_show_workflow" not in st.session_state:
        st.session_state["landing_show_workflow"] = False
    if "landing_stage_selector" in st.session_state:
        st.session_state["landing_stage"] = st.session_state["landing_stage_selector"]

    workflow_stages = [
        {
            "key": "Intake",
            "step": "01",
            "title": "Intake",
            "status": "Source ingestion live",
            "headline": "Packet intake is indexing the submission and source chain before reviewer routing.",
            "summary": "SUGAM submission metadata, source integrity, and packet identity are normalised as the first operational gate.",
            "document_type": sample_case["documents"]["submission"]["type"],
            "document_name": sample_case["documents"]["submission"]["name"],
            "pii_masked": "Queued after routing",
            "seriousness_score": "74 / 100",
            "packet_readiness": "2 of 6 stages primed",
            "latest_action": "Submission packet mirrored from SUGAM intake",
            "metrics": [
                {"label": "Signals indexed", "value": "12", "detail": "Sponsor, site, investigator, and packet identity fields mapped."},
                {"label": "Reviewer gate", "value": "Ready", "detail": "Packet can route into protected review without manual re-entry."},
                {"label": "Escalations", "value": "1 open", "detail": "Form CT-04 signatory verification remains queued."},
            ],
            "input": "Submission packet mirrored from source intake and normalised into the active review queue.",
            "output": "Document category, source fingerprint, and routing recommendation generated with source references.",
            "gate": "Reviewer confirms the intake lane before protected processing begins.",
        },
        {
            "key": "Protected View",
            "step": "02",
            "title": "Protected View",
            "status": "Masking map ready",
            "headline": "PII/PHI masking is staged for reviewer-safe circulation without losing source traceability.",
            "summary": "Structured pseudonymisation keeps the source chain intact while removing patient, investigator, date, and site identifiers from working views.",
            "document_type": sample_case["documents"]["sae"]["type"],
            "document_name": sample_case["documents"]["sae"]["name"],
            "pii_masked": f"{protected_count} entities staged",
            "seriousness_score": "88 / 100",
            "packet_readiness": "Protected view token map ready",
            "latest_action": "One low-confidence date token remains for reviewer approval",
            "metrics": [
                {"label": "PII entities", "value": str(protected_count), "detail": "Patient, investigator, date, and site tokens detected from the SAE narrative."},
                {"label": "Low confidence", "value": "1", "detail": "A discharge-date entity is intentionally held for reviewer confirmation."},
                {"label": "Audit trace", "value": "100%", "detail": "Every replacement token remains source-linked for later inspection."},
            ],
            "input": "Narrative text passes through entity detection, category filters, and reversible tokenisation.",
            "output": "Protected reviewer-safe document view with entity map and approval queue.",
            "gate": "Reviewer approves or escalates low-confidence masking before downstream use.",
        },
        {
            "key": "Triage",
            "step": "03",
            "title": "Triage",
            "status": "Safety severity elevated",
            "headline": "Safety triage is surfacing seriousness, causality, and duplicate risk before review packet assembly.",
            "summary": "The SAE lane scores seriousness, likely causality, and session duplicates so urgent cases surface with the right operational weight.",
            "document_type": sample_case["documents"]["sae"]["type"],
            "document_name": sample_case["documents"]["sae"]["name"],
            "pii_masked": f"{protected_count} entities protected",
            "seriousness_score": "92 / 100",
            "packet_readiness": "Hospitalisation lane active",
            "latest_action": "Causality remains marked as Possibly Related",
            "metrics": [
                {"label": "Seriousness", "value": "High", "detail": "ICU admission and hospitalisation push this case into urgent review."},
                {"label": "Duplicate scan", "value": "Clean", "detail": "No session-level duplicate found against the current review queue."},
                {"label": "Missing info", "value": str(missing_count), "detail": "Open follow-up items remain visible before packet confirmation."},
            ],
            "input": "Protected narrative plus event timeline and causality cues flow into the safety engine.",
            "output": "Severity grade, reviewer-facing event synopsis, and duplicate recommendation.",
            "gate": "Reviewer decides whether to confirm the safety lane or escalate low-confidence cues.",
        },
        {
            "key": "Validation",
            "step": "04",
            "title": "Validation",
            "status": "Completeness variance open",
            "headline": "Submission validation is checking mandatory CT fields and routing exceptions before formal review.",
            "summary": "Mandatory clinical trial application fields are assessed with deterministic gaps surfaced as reviewer-visible validation signals.",
            "document_type": sample_case["documents"]["submission"]["type"],
            "document_name": sample_case["documents"]["submission"]["name"],
            "pii_masked": "Not applicable",
            "seriousness_score": "63 / 100",
            "packet_readiness": "19 of 20 mapped",
            "latest_action": "Form CT-04 signatory remains flagged for confirmation",
            "metrics": [
                {"label": "Required fields", "value": "19 / 20", "detail": "Administrative and safety sections are largely complete for reviewer validation."},
                {"label": "Blocking gaps", "value": "1", "detail": "A signatory mismatch remains queued as the main validation hold."},
                {"label": "Source links", "value": "Ready", "detail": "Every field can be traced back to the original submission text."},
            ],
            "input": "Submission sections, CT forms, and safety references are compared against required field maps.",
            "output": "RAG-style completeness status and reviewer-facing validation exceptions.",
            "gate": "Reviewer confirms whether the packet can proceed or should be returned for correction.",
        },
        {
            "key": "Compare",
            "step": "05",
            "title": "Compare",
            "status": "Amendment deltas indexed",
            "headline": "Version comparison is isolating substantive protocol changes from administrative edits.",
            "summary": "The compare engine lifts protocol amendments into structured deltas so reviewers can focus on the changes that affect risk, endpoints, and consent.",
            "document_type": sample_case["documents"]["amendment"]["type"],
            "document_name": sample_case["documents"]["amendment"]["name"],
            "pii_masked": "Not required for protocol diff",
            "seriousness_score": "71 / 100",
            "packet_readiness": f"{compare_count} key deltas indexed",
            "latest_action": "Endpoint extension has been elevated as substantive",
            "metrics": [
                {"label": "Tracked changes", "value": str(compare_count), "detail": "Eligibility, endpoint window, and consent language are isolated with impact notes."},
                {"label": "Substantive", "value": "2", "detail": "Two amendment lines materially affect safety or analysis planning."},
                {"label": "Administrative", "value": "1", "detail": "Language localisation is retained but does not block progression."},
            ],
            "input": "Base protocol and amendment text are aligned semantically and structurally.",
            "output": "Source-linked change log with substantive vs administrative classification.",
            "gate": "Reviewer confirms whether the amendment can proceed without further clarification.",
        },
        {
            "key": "Audit Packet",
            "step": "06",
            "title": "Audit Packet",
            "status": "Review chain exportable",
            "headline": "Audit packet generation is keeping every AI output tied to the reviewer decision trail.",
            "summary": "Each module contributes source-linked outputs and explicit reviewer actions so the packet is inspection-ready when required.",
            "document_type": "Cross-packet review bundle",
            "document_name": sample_case["packet_id"],
            "pii_masked": f"{protected_count} entity actions logged",
            "seriousness_score": "83 / 100",
            "packet_readiness": "Audit trail ready on demand",
            "latest_action": "Decision chain remains anchored to source-linked evidence",
            "metrics": [
                {"label": "Audit chain", "value": "Live", "detail": "Reviewer actions, AI outputs, and source references remain chronologically linked."},
                {"label": "Packet export", "value": "Ready", "detail": "Structured audit packet can be generated once review decisions are confirmed."},
                {"label": "Escalation record", "value": "Tracked", "detail": "Low-confidence events remain visible in the final packet narrative."},
            ],
            "input": "Validated outputs from intake, protection, safety, validation, and comparison are consolidated.",
            "output": "Inspection-ready review packet with reviewer decisions and source-linked evidence.",
            "gate": "Authorised reviewer remains the final decision authority before packet issuance.",
        },
    ]
    stage_lookup = {stage["key"]: stage for stage in workflow_stages}
    selected_stage = stage_lookup.get(st.session_state["landing_stage"], workflow_stages[0])

    capability_cards = [
        {
            "key": "anon",
            "label": "01 · Privacy",
            "title": "Anonymisation",
            "signal": f"{protected_count} entities detected · reviewer approval queue live",
            "summary": "Two-step masking keeps operational review moving without losing source-level reversibility.",
            "bullets": [
                "Category-aware filters separate patient, investigator, site, and date handling.",
                "Low-confidence entities remain reviewer visible instead of being auto-suppressed.",
                "Protected views stay source-linked for future audit reconstruction.",
            ],
            "stage": "Protected View",
        },
        {
            "key": "sum",
            "label": "02 · Intelligence",
            "title": "Summarisation",
            "signal": "SAE, checklist, and meeting modes available from the same console",
            "summary": "Narratives are compressed into review-ready summaries with explicit prompts for reviewer follow-up.",
            "bullets": [
                "Structured synopsis keeps key signals and reviewer prompts visible together.",
                "SAE summarisation preserves seriousness, causality, and outcome fields.",
                "Checklist and meeting lanes keep source modes aligned instead of splitting tools.",
            ],
            "stage": "Triage",
        },
        {
            "key": "complete",
            "label": "03 · Validation",
            "title": "Completeness Check",
            "signal": "20 required CT fields tracked with deterministic validation notes",
            "summary": "Submission quality is framed as operational readiness instead of a passive checklist.",
            "bullets": [
                "Mandatory field validation is tied directly to source evidence.",
                "Reviewer-return vs proceed decisions stay visible alongside the gap summary.",
                "Validation variance is explicit before the packet moves downstream.",
            ],
            "stage": "Validation",
        },
        {
            "key": "triage",
            "label": "04 · Triage",
            "title": "Categorisation & Safety",
            "signal": "Hospitalisation signal elevated · duplicate scan running in-session",
            "summary": "Safety triage puts severity, seriousness, and duplicate risk into one reviewer-facing lane.",
            "bullets": [
                "Severity grading and causality remain visible with the active case context.",
                "Duplicate detection is session-aware and does not rely on generic heuristics.",
                "Reviewer escalation is a first-class output, not an afterthought.",
            ],
            "stage": "Triage",
        },
        {
            "key": "compare",
            "label": "05 · Diff Engine",
            "title": "Version Compare",
            "signal": f"{compare_count} amendment deltas mapped with impact annotations",
            "summary": "Protocol change review is focused on the few changes that materially affect the case.",
            "bullets": [
                "Substantive vs administrative splits are source-linked and explainable.",
                "Endpoint, eligibility, and consent changes remain review-ready in one pane.",
                "Reviewer packets can be assembled without manually rebuilding the amendment story.",
            ],
            "stage": "Compare",
        },
        {
            "key": "audit",
            "label": "06 · Audit",
            "title": "Audit Packet",
            "signal": "Source-linked decision chain preserved across all workflow stages",
            "summary": "Audit readiness is designed into the workflow instead of appended at the end.",
            "bullets": [
                "All reviewer actions stay attached to timestamps, confidence, and source references.",
                "Low-confidence events are retained in the packet instead of being flattened out.",
                "Inspection-ready exports remain structured for downstream scrutiny.",
            ],
            "stage": "Audit Packet",
        },
    ]
    trust_items = {
        "Reviewer remains in control": {
            "title": "Reviewer remains in control",
            "copy": "No AI output is final by itself. Each stage is framed as a reviewer decision gate with explicit confirm, return, or escalate paths.",
            "signal": "Final judgement never auto-advances without an authorised reviewer action.",
        },
        "Source-linked outputs": {
            "title": "Source-linked outputs",
            "copy": "Operational summaries, comparisons, and safety packets stay tied to underlying packet text so reviewers can trace every assertion.",
            "signal": "Evidence remains inspectable instead of being reduced to opaque model prose.",
        },
        "Low-confidence escalation": {
            "title": "Low-confidence escalation",
            "copy": "Ambiguous masking, incomplete fields, and safety uncertainty are surfaced as visible reviewer tasks rather than hidden system failures.",
            "signal": "Confidence thresholds produce escalation events instead of silent automation.",
        },
        "Audit-ready logging": {
            "title": "Audit-ready logging",
            "copy": "Each reviewer action, packet mutation, and AI output is retained in sequence so the command chain is reconstructable during inspection.",
            "signal": "The system keeps a usable audit narrative, not just raw event exhaust.",
        },
    }

    selected_stage = stage_lookup.get(st.session_state["landing_stage"], workflow_stages[0])
    if st.session_state["landing_show_workflow"]:
        stage_copy = f"{selected_stage['summary']} {selected_stage['status']}."
    else:
        stage_copy = selected_stage["summary"]

    st.markdown('<div class="landing-shell">', unsafe_allow_html=True)
    st.markdown(f"""
<div class="landing-topbar">
  <div class="landing-brand-stack">
    <div class="landing-brand">
      <img src="{HINDI_LOGO_DATA_URI}" alt="Nirnay Hindi logo">
    </div>
    <div class="landing-markers">
      <span class="landing-marker">IndiaAI</span>
      <span class="landing-marker">CDSCO</span>
      <span class="landing-marker">Stage 1</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    hero_left, hero_right = st.columns([1.7, 0.9], gap="large")
    with hero_left:
        st.markdown("""
<div class="hero-card">
  <div class="hero-kicker">Regulatory review operations</div>
  <h1 class="hero-title">Calm, source-linked CDSCO review from intake to audit packet.</h1>
  <div class="hero-sub">Nirnay keeps the reviewer in control while the system organises intake, protected handling, safety triage, validation, comparison, and audit-ready outputs.</div>
</div>
""", unsafe_allow_html=True)
    with hero_right:
        st.markdown("""
<div class="access-card">
  <div class="access-title">Authorised reviewer sign-in</div>
  <div class="access-copy">Use your reviewer credentials to open the live CDSCO review workspace.</div>
</div>
""", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            _uname = st.text_input("Username", placeholder="Username", key="login_uname")
            _pwd = st.text_input("Password", placeholder="Password", type="password", key="login_pwd")
            if st.session_state["_login_failed"]:
                st.markdown(
                    '<p style="color:#c2410c;font-size:12px;margin:2px 0 8px;">Invalid credentials. Review the access details and try again.</p>',
                    unsafe_allow_html=True,
                )
            _submitted = st.form_submit_button("Sign in →", use_container_width=True)
        st.caption("Authorised CDSCO personnel only. Sessions remain logged for compliance and audit review.")

    if _submitted:
        if _uname.strip() == VALID_USER and _pwd == VALID_PASS:
            set_screen("Command Dashboard")
            st.session_state["logged_in"] = True
            st.session_state["_login_failed"] = False
            st.rerun()
        st.session_state["_login_failed"] = True
        st.rerun()

    st.markdown('<div class="workflow-strip-title">Workflow</div>', unsafe_allow_html=True)
    selected_key = st.radio(
        "Workflow",
        options=[stage["key"] for stage in workflow_stages],
        index=[stage["key"] for stage in workflow_stages].index(st.session_state["landing_stage"]),
        horizontal=True,
        label_visibility="collapsed",
        key="landing_stage_selector",
    )
    if selected_key != st.session_state["landing_stage"]:
        st.session_state["landing_stage"] = selected_key
        selected_stage = stage_lookup[selected_key]
        stage_copy = f"{selected_stage['summary']} {selected_stage['status']}." if st.session_state["landing_show_workflow"] else selected_stage["summary"]

    st.markdown(f"""
<div class="stage-panel">
  <div class="stage-panel-head">
    <div>
      <div class="stage-name">{selected_stage["title"]}</div>
      <div class="stage-copy">{selected_stage["headline"]} {stage_copy}</div>
    </div>
    <div class="stage-accent">{selected_stage["status"]}</div>
  </div>
  <div class="stage-signal-grid">
    <div class="stage-signal">
      <div class="stage-signal-label">Current input</div>
      <div class="stage-signal-value">{selected_stage["input"]}</div>
    </div>
    <div class="stage-signal">
      <div class="stage-signal-label">Live output</div>
      <div class="stage-signal-value">{selected_stage["output"]}</div>
    </div>
    <div class="stage-signal">
      <div class="stage-signal-label">Reviewer gate</div>
      <div class="stage-signal-value">{selected_stage["gate"]}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
    stage_cta = st.button(f"Open {selected_stage['title']} in Demo", key="landing_stage_cta", use_container_width=False)

    st.markdown(f'<div class="landing-footer">{APP_DISCLAIMER}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if stage_cta:
        apply_landing_stage_route(selected_stage["key"])
        st.session_state["logged_in"] = True
        st.session_state["_login_failed"] = False
        st.rerun()

    st.stop()

# ── Past login gate ───────────────────────────────────────────────────────────
case = get_active_case()


def go_to(screen_name: str) -> None:
    set_screen(screen_name)
    st.rerun()


def go_to_anonymisation() -> None:
    st.session_state.screen = "Protected View"
    st.session_state.active_tab = 2
    st.session_state.active_ribbon_tab = "🕵️ Anonymisation"
    st.rerun()


def get_command_dashboard_snapshot() -> dict:
    # The dashboard stays on the seeded HBT-17 baseline until Phase 2.
    # Live intake/uploads should not alter this screen.
    snapshot = deepcopy(get_case_library()["HBT-17"])
    snapshot["current_stage"] = "Command Dashboard"
    snapshot["selected_document_id"] = "submission"
    snapshot["document_classification"] = {}
    snapshot["structured_synopsis"] = {}
    snapshot["reviewer_decisions"] = []
    snapshot["audit_events"] = []
    snapshot["export_readiness"] = {
        "classification": False,
        "protected_view": False,
        "sae_packet": False,
        "compare_packet": False,
        "audit_packet": False,
    }
    snapshot["protected_view"]["validated"] = False
    snapshot["protected_view"]["validation_summary"] = ""
    snapshot["protected_view"]["escalation_status"] = "Not validated"
    snapshot["sae_review"]["review_packet"] = ""
    snapshot["compare_review"]["review_packet"] = ""
    return snapshot


def render_quick_redirects() -> None:
    current_screen = st.session_state.get("screen", SCREENS[0])
    quick_links = [
        ("quick_dashboard", "Dashboard", "Command Dashboard"),
        ("quick_intake", "Document Intake", "Document Intake"),
        ("quick_anon", "Anonymisation", "Protected View"),
        ("quick_sae", "SAE Review", "SAE Review"),
        ("quick_audit", "Audit Trail", "Audit Trail"),
    ]

    st.caption("Quick redirects")
    for key, label, screen_name in quick_links:
        if st.button(
            label,
            key=key,
            use_container_width=True,
            type="primary" if current_screen == screen_name else "secondary",
        ):
            go_to(screen_name)


DOCUMENT_UPLOAD_TYPES = [
    "docx", "pdf", "txt", "csv", "xlsx", "xls",
    "png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff",
]
DOCUMENT_UPLOAD_LABEL = "Word / PDF / TXT / CSV / Excel / Image"
AUDIO_UPLOAD_TYPES = DOCUMENT_UPLOAD_TYPES + ["mp3", "wav", "m4a"]
AUDIO_UPLOAD_LABEL = f"{DOCUMENT_UPLOAD_LABEL} / Audio"


def _preview_text(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _build_spreadsheet_synopsis(name: str, text: str, duplicate_warning: str) -> tuple[dict, dict, float]:
    sections: list[tuple[str, list[str]]] = []
    current_sheet = "Sheet1"
    current_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        sheet_match = re.match(r"^\[Sheet:\s*(.+?)\]\s*$", line)
        if sheet_match:
            if current_lines:
                sections.append((current_sheet, [item for item in current_lines if item.strip()]))
            current_sheet = sheet_match.group(1)
            current_lines = []
            continue
        if line.strip():
            current_lines.append(line)
    if current_lines or not sections:
        sections.append((current_sheet, [item for item in current_lines if item.strip()]))

    non_empty_sections = [(sheet, lines) for sheet, lines in sections if lines]
    section_rows = [max(0, len(lines) - 1) for _, lines in non_empty_sections]
    total_rows = sum(section_rows)
    sheet_names = [sheet for sheet, _ in non_empty_sections] or [current_sheet]

    first_sheet_lines = non_empty_sections[0][1] if non_empty_sections else []
    header_line = first_sheet_lines[0].strip() if first_sheet_lines else ""
    header_guess = [part.strip() for part in re.split(r"\s{2,}", header_line) if part.strip()]
    if len(header_guess) <= 1 and header_line:
        header_guess = header_line.split()[:4]
    header_preview = ", ".join(header_guess[:4]) if header_guess else "Headers not clearly inferred from extracted workbook text"

    summary_bits = [f"Workbook with {len(sheet_names)} visible sheet(s)"]
    if total_rows:
        summary_bits.append(f"approximately {total_rows} data row(s)")
    if header_guess:
        summary_bits.append(f"primary columns include {header_preview}")
    summary = ". ".join(summary_bits) + "."

    classification = {
        "probable_type": "Spreadsheet Intake Register",
        "severity": "Medium",
        "duplicate_warning": duplicate_warning,
        "escalation_recommendation": "Reviewer should confirm the spreadsheet category and route it to the relevant workflow.",
    }
    synopsis = {
        "headline": f"Spreadsheet uploaded for intake review: {name}",
        "summary": summary,
        "key_signals": [
            f"Sheets: {', '.join(sheet_names[:3])}" + ("…" if len(sheet_names) > 3 else ""),
            f"Approximate data rows: {total_rows or len(first_sheet_lines)}",
            f"Primary columns: {header_preview}",
        ],
        "reviewer_prompt": "Review the sheet structure and key columns before deciding whether this workbook belongs in SAE, completeness, or comparison review.",
    }
    return classification, synopsis, 0.82


def _build_uploaded_intake_artifacts(name: str, text: str, documents: dict, doc_id: str) -> tuple[dict, dict, float]:
    tl = text.lower()
    sibling_docs = {
        key: {"name": value["name"], "text": value.get("raw_text", "")}
        for key, value in documents.items()
        if key != doc_id and value.get("raw_text")
    }
    duplicate_hits = detect_duplicates(text, sibling_docs)
    duplicate_warning = (
        "Potential duplicate with " + ", ".join(hit["file"] for hit in duplicate_hits[:3])
        if duplicate_hits
        else "No duplicate detected in active case packet"
    )

    if any(
        token in tl
        for token in ("serious adverse event", "sae", "causality assessment", "seriousness criteria", "subject id")
    ):
        sae_summary = summarise_sae(text)
        severity = {"URGENT": "Critical", "STANDARD": "High", "LOW": "Medium"}[sae_summary["priority"]]
        classification = {
            "probable_type": "SAE Narrative",
            "severity": severity,
            "duplicate_warning": duplicate_warning,
            "escalation_recommendation": (
                f"{sae_summary['timeline']} review required. "
                + (
                    "Immediate DCGI escalation recommended."
                    if sae_summary["priority"] == "URGENT"
                    else "Route to safety reviewer queue."
                )
            ),
        }
        synopsis = {
            "headline": f"{sae_summary['priority']} SAE narrative uploaded for intake review",
            "summary": (
                f"Uploaded document reads like an SAE narrative with {sae_summary['causality'].lower()} causality, "
                f"{sae_summary['outcome'].lower()} outcome, and {sae_summary['timeline'].lower()} reporting."
            ),
            "key_signals": [
                f"Priority: {sae_summary['priority']}",
                f"Causality: {sae_summary['causality']}",
                f"Outcome: {sae_summary['outcome']}",
            ],
            "reviewer_prompt": "Confirm patient identifiers and reporting dates before routing to Protected View.",
        }
        return classification, synopsis, 0.91

    if any(
        token in tl
        for token in (
            "sugam",
            "form ct-",
            "ethics committee",
            "clinical trial application",
            "investigator brochure",
            "phase iii",
            "phase ii",
            "phase i",
        )
    ):
        completeness = assess_completeness(text)
        severity = "High" if completeness["critical_missing"] else "Medium" if completeness["major_missing"] else "Low"
        classification = {
            "probable_type": "SUGAM Clinical Trial Application",
            "severity": severity,
            "duplicate_warning": duplicate_warning,
            "escalation_recommendation": completeness["recommendation"],
        }
        synopsis = {
            "headline": f"SUGAM submission uploaded with {completeness['score']}% completeness",
            "summary": (
                f"Uploaded submission contains {completeness['present']} of {completeness['total']} tracked intake fields. "
                f"Critical missing fields: {len(completeness['critical_missing'])}. "
                f"Major missing fields: {len(completeness['major_missing'])}."
            ),
            "key_signals": [
                f"Completeness score: {completeness['score']}%",
                f"Critical missing: {len(completeness['critical_missing'])}",
                f"Major missing: {len(completeness['major_missing'])}",
            ],
            "reviewer_prompt": "Validate missing critical fields before forwarding for technical review.",
        }
        return classification, synopsis, 0.9

    if any(token in tl for token in ("protocol amendment", "amendment", "redline", "eligibility criteria", "primary endpoint", "consent")):
        substantive_flags = [
            label
            for label, present in (
                ("Eligibility", "eligibility" in tl),
                ("Endpoint", "endpoint" in tl),
                ("Consent", "consent" in tl),
                ("Dose", "dose" in tl or "dosage" in tl),
            )
            if present
        ]
        classification = {
            "probable_type": "Protocol Amendment",
            "severity": "High" if substantive_flags else "Medium",
            "duplicate_warning": duplicate_warning,
            "escalation_recommendation": "Review substantive amendment changes before downstream comparison or approval.",
        }
        synopsis = {
            "headline": "Protocol amendment uploaded for intake review",
            "summary": (
                "Document appears to contain protocol or consent changes that should be routed through version comparison "
                "before reviewer approval."
            ),
            "key_signals": substantive_flags[:3] or ["Amendment language detected in uploaded document"],
            "reviewer_prompt": "Link the uploaded amendment to its baseline version before final routing.",
        }
        return classification, synopsis, 0.84

    if name.lower().endswith((".csv", ".xlsx", ".xls")):
        return _build_spreadsheet_synopsis(name, text, duplicate_warning)

    classification = {
        "probable_type": "General Regulatory Document",
        "severity": "Medium",
        "duplicate_warning": duplicate_warning,
        "escalation_recommendation": "Reviewer should confirm document type before downstream routing.",
    }
    synopsis = {
        "headline": f"Uploaded intake document: {name}",
        "summary": _preview_text(text, limit=260),
        "key_signals": [
            f"Filename: {name}",
            f"Length: {len(text.split())} words",
            "Uploaded directly from Document Intake",
        ],
        "reviewer_prompt": "Confirm the document category before using feature-specific review tools.",
    }
    return classification, synopsis, 0.78


def _ingest_document_intake_upload(uploaded_file) -> tuple[str | None, str | None]:
    text, err = extract_text(uploaded_file)
    if err:
        return None, err
    if not text.strip():
        return None, "No extractable text was found in the uploaded document."

    file_bytes = uploaded_file.getvalue()
    doc_id = f"upload_{hashlib.sha1(file_bytes).hexdigest()[:12]}"
    active_case = get_active_case()
    existing = active_case["documents"].get(doc_id)

    if existing and existing.get("raw_text") == text:
        active_case["selected_document_id"] = doc_id
        active_case["document_classification"] = existing.get("classification", {})
        active_case["structured_synopsis"] = existing.get("synopsis", {})
        save_active_case(active_case)
        return doc_id, None

    classification, synopsis, confidence = _build_uploaded_intake_artifacts(
        uploaded_file.name,
        text,
        active_case["documents"],
        doc_id,
    )
    active_case["documents"][doc_id] = {
        "name": uploaded_file.name,
        "type": classification["probable_type"],
        "source": "Manual upload — Document Intake",
        "risk_level": classification["severity"],
        "confidence": confidence,
        "preview": synopsis["headline"],
        "raw_text": text,
        "classification": classification,
        "synopsis": synopsis,
    }
    active_case["selected_document_id"] = doc_id
    active_case["document_classification"] = classification
    active_case["structured_synopsis"] = synopsis
    active_case["export_readiness"]["classification"] = True
    save_active_case(active_case)
    add_audit_event(
        "Document Intake",
        f"Uploaded document added to case packet — {uploaded_file.name}",
        confidence,
        "Uploaded",
        "Generated",
        uploaded_file.name,
        f"{classification['probable_type']} inferred from uploaded content and selected for intake review.",
    )
    return doc_id, None


def _render_document_intake_uploader(widget_key: str) -> str | None:
    st.markdown('<div class="upload-card"><h4>📁 Upload your document</h4>', unsafe_allow_html=True)
    intake_file = st.file_uploader(DOCUMENT_UPLOAD_LABEL, type=DOCUMENT_UPLOAD_TYPES, key=widget_key)
    if intake_file:
        # Enforce 200MB limit (200 * 1024 * 1024 bytes)
        if intake_file.size > 200 * 1024 * 1024:
            st.error("File size exceeds 200 MB limit. Please select a smaller file.")
            return None

        doc_id, err = _ingest_document_intake_upload(intake_file)
        if err:
            st.error(f"Extraction error: {err}")
        else:
            active_case = get_active_case()
            selected_doc = active_case["documents"][doc_id]
            st.success(
                f"✓ Added **{selected_doc['name']}** to the active case packet and selected it for intake review."
            )
            st.caption("The processed upload is now displayed below in Intake controls.")
            return doc_id
    st.caption("Uploaded documents are added to the active case packet and override the sample document you select next.")
    st.markdown('</div>', unsafe_allow_html=True)
    return None


def _find_sentence(text: str, keywords: tuple[str, ...]) -> str | None:
    for chunk in re.split(r"(?<=[.!?])\s+|\n+", text):
        cleaned = " ".join(chunk.split())
        if cleaned and any(keyword in cleaned.lower() for keyword in keywords):
            return cleaned
    return None


def _workflow_entity_category(entity_type: str) -> str | None:
    lowered = entity_type.lower()
    if "patient" in lowered:
        return "Patient"
    if "investigator" in lowered:
        return "Investigator"
    if "date" in lowered or "dob" in lowered:
        return "Date"
    if any(token in lowered for token in ("site", "institution", "study id", "regulatory")):
        return "Site"
    return None


def _build_workflow_protected_entities(text: str) -> list[dict]:
    entities: list[dict] = []
    anonymised = run_anonymisation(text)
    for token in anonymised["tokens"]:
        category = _workflow_entity_category(token["Entity Type"])
        if not category:
            continue
        entities.append({
            "label": token["Entity Type"],
            "value": token["Original Value"],
            "replacement": token["Token"],
            "category": category,
            "confidence": 0.9,
            "approved": True,
        })
    return entities


def _build_sae_missing_items(text: str) -> list[dict]:
    tl = text.lower()
    items: list[str] = []
    if not any(token in tl for token in ("concomitant", "medication", "medicine", "drug history")):
        items.append("Concomitant medication list at time of event")
    if not any(token in tl for token in ("causality", "possibly related", "probably related", "definitely related", "unrelated")):
        items.append("Investigator causality assessment")
    if not any(token in tl for token in ("recovered", "recovering", "outcome", "fatal", "deceased", "resolved", "discharged")):
        items.append("Follow-up outcome update")
    if not any(token in tl for token in ("hospital", "icu", "seriousness criteria", "admitted", "emergency")):
        items.append("Seriousness criterion confirmation")
    return [{"item": item, "resolved": False} for item in items[:3]]


def _build_uploaded_sae_review(text: str) -> dict:
    sae_summary = summarise_sae(text)
    sae_classification = classify_sae(text)
    compact = " ".join(text.split())

    patient_match = re.search(r"\b(\d{1,3})-year-old\s+(male|female|man|woman)\b([^.]*)", compact, re.I)
    patient_profile = _preview_text(compact, 96)
    if patient_match:
        patient_profile = f"{patient_match.group(1)}-year-old {patient_match.group(2).lower()}"
        trailing = patient_match.group(3).strip(" ,;")
        if trailing.lower().startswith("with "):
            patient_profile = _preview_text(f"{patient_profile} {trailing}", 96)
    else:
        subject_match = re.search(r"\b(?:subject|patient)\s*id[:\s-]*([A-Z0-9-]+)\b", compact, re.I)
        if subject_match:
            patient_profile = f"Subject {subject_match.group(1)}"

    event = _find_sentence(
        text,
        ("adverse", "event", "hypogly", "reaction", "hospital", "icu", "death", "serious"),
    ) or _preview_text(compact, 150)
    action_taken = _find_sentence(
        text,
        ("action taken", "dose", "discontinu", "withdraw", "treated", "management", "monitor", "discharged"),
    ) or "Reviewer to confirm action taken from uploaded SAE narrative."

    severity_label = {
        "DEATH": "Critical",
        "DISABILITY": "Serious",
        "HOSPITALISATION": "Serious",
        "OTHERS": "Review Required",
    }[sae_classification["severity"]]

    return {
        "patient_profile": patient_profile,
        "event": _preview_text(event, 180),
        "seriousness": sae_classification["severity"].replace("_", " ").title(),
        "severity": severity_label,
        "causality": sae_summary["causality"],
        "action_taken": _preview_text(action_taken, 180),
        "outcome": sae_summary["outcome"],
        "reviewer_notes": "",
        "review_packet": "",
        "missing_info": _build_sae_missing_items(text),
    }


def _ingest_sae_review_upload(uploaded_file) -> str | None:
    text, err = extract_text(uploaded_file)
    if err:
        return err
    if not text.strip():
        return "No extractable text was found in the uploaded SAE document."

    active_case = get_active_case()
    classification, synopsis, confidence = _build_uploaded_intake_artifacts(
        uploaded_file.name,
        text,
        active_case["documents"],
        "sae",
    )

    active_case["documents"]["sae"] = {
        "name": uploaded_file.name,
        "type": classification["probable_type"],
        "source": "Manual upload — SAE Review",
        "risk_level": classification["severity"],
        "confidence": confidence,
        "preview": synopsis["headline"],
        "raw_text": text,
        "classification": classification,
        "synopsis": synopsis,
    }
    active_case["sae_review"] = _build_uploaded_sae_review(text)
    active_case["selected_document_id"] = "sae"
    active_case["document_classification"] = classification
    active_case["structured_synopsis"] = synopsis
    active_case["export_readiness"]["classification"] = True
    active_case["export_readiness"]["protected_view"] = False
    active_case["export_readiness"]["sae_packet"] = False
    active_case["protected_view"]["source_document_id"] = "sae"
    active_case["protected_view"]["validated"] = False
    active_case["protected_view"]["validation_summary"] = ""
    active_case["protected_view"]["escalation_status"] = "Not validated"
    active_case["protected_view"]["category_filters"] = {
        "Patient": True,
        "Investigator": True,
        "Date": True,
        "Site": True,
    }
    active_case["protected_view"]["entities"] = _build_workflow_protected_entities(text)
    save_active_case(active_case)
    add_audit_event(
        "SAE Review",
        f"Uploaded SAE document added to review packet — {uploaded_file.name}",
        confidence,
        "Uploaded",
        "Generated",
        uploaded_file.name,
        "SAE review summary and protected-view source were refreshed from the uploaded narrative.",
    )
    return None


def _render_sae_review_uploader(widget_key: str) -> None:
    st.markdown('<div class="upload-card"><h4>📁 Upload SAE document</h4>', unsafe_allow_html=True)
    sae_file = st.file_uploader(DOCUMENT_UPLOAD_LABEL, type=DOCUMENT_UPLOAD_TYPES, key=widget_key)
    if sae_file:
        err = _ingest_sae_review_upload(sae_file)
        if err:
            st.error(f"Extraction error: {err}")
        else:
            active_case = get_active_case()
            st.success(
                f"✓ Added **{active_case['documents']['sae']['name']}** as the active SAE review source."
            )
    active_case = get_active_case()
    st.caption(f"Active SAE source: {active_case['documents']['sae']['name']}")
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TOP BAR
# ═══════════════════════════════════════════════════════════════════════════════
_brand_col, _signout_col = st.columns([12, 1.2])
with _brand_col:
    st.markdown(f"""
    <div class="top-brand-shell">
      <img src="{HINDI_LOGO_DATA_URI}" alt="Nirnay Hindi logo" class="top-brand-logo-hi">
    </div>
    """, unsafe_allow_html=True)

with _signout_col:
    if st.button("Sign out", key="signout"):
        st.session_state["logged_in"] = False
        st.query_params.clear()
        st.rerun()


# ── Always-visible nav bar: case selector + workflow breadcrumb ───────────────
screen = render_top_nav()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TABS — Features + Workflow
# ═══════════════════════════════════════════════════════════════════════════════
(t_cmd_dash, t_doc_intake, t_anon, t_sum, t_comp, t_cls, t_cmp, t_sae_review,
 t_audit_trail) = st.tabs([
    "🖥️ Command Dashboard",
    "📥 Document Intake",
    "🕵️ Anonymisation",
    "📄 Summarisation",
    "✅ Completeness",
    "🏷️ Categorisation",
    "🔄 Version Compare",
    "🏥 SAE Review",
    "📜 Audit Trail",
])

# ── Tab-jump JS helper ────────────────────────────────────────────────────────
_active_tab_idx = st.session_state.get("active_tab", 0)
if _active_tab_idx > 0:
    st.session_state["active_tab"] = 0
    _cv1.html(f"""<script>
(function(){{
  var idx={_active_tab_idx};
  function clickTab(){{
    var tabs=window.parent.document.querySelectorAll('[data-baseweb="tab"]');
    if(tabs.length>idx)tabs[idx].click();
    else setTimeout(clickTab,100);
  }}
  setTimeout(clickTab,200);
}})();
</script>""", height=0)



# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANONYMISATION (Protected View)
# ═══════════════════════════════════════════════════════════════════════════════
with t_anon:
    render_banner("Protected View", "PII/PHI detection and anonymisation · Two-step DPDP Act 2023 process · Full audit log")
    st.markdown("""
<div class="sec-hd">
  <div class="sec-ic ic-blue" style="font-size:14px;font-weight:700;color:#1e40af;">01</div>
  <div><h2>Data Anonymisation — DPDP Act 2023</h2>
  <p>Two-step PII/PHI removal · Step 1: Reversible pseudonymisation · Step 2: Irreversible generalisation · Full audit log</p></div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="upload-card"><h4>📁 Upload document</h4>', unsafe_allow_html=True)
    anon_file = st.file_uploader(DOCUMENT_UPLOAD_LABEL, type=DOCUMENT_UPLOAD_TYPES, key="anon_up")
    if anon_file:
        txt, err = extract_text(anon_file)
        if err:
            st.error(f"Extraction error: {err}")
        elif txt.strip():
            st.session_state["anon_text"]    = txt
            st.session_state["anon_textarea"] = txt
            st.success(f"✓ Extracted **{len(txt.split())} words** from {anon_file.name}")
    st.markdown('<div class="or-line">or paste text below</div>', unsafe_allow_html=True)
    st.text_area("Document content", height=200,
                 placeholder="Paste SAE report, clinical trial document, or any regulatory text with PII/PHI...",
                 key="anon_textarea")
    st.session_state["anon_text"] = st.session_state.get("anon_textarea","")
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2, _ = st.columns([1,1,3])
    with c1: run_anon = st.button("Analyse & protect document", type="primary", use_container_width=True)
    with c2:
        if st.button("🗑 Clear", use_container_width=True, key="anon_clear"):
            st.session_state["anon_text"] = st.session_state["anon_textarea"] = ""
            st.rerun()

    if run_anon:
        content = st.session_state["anon_text"].strip()
        if not content:
            st.markdown('<div class="rc warn">⚠️ Please upload a file or paste text first.</div>', unsafe_allow_html=True)
        else:
            with st.spinner("Detecting PII/PHI entities..."):
                result = run_anonymisation(content)
            n = result["count"]
            risk   = "High" if n >= 5 else "Medium" if n > 0 else "Low"
            action = (f"{n} sensitive items detected and anonymised. Download the anonymised version for external sharing. DPDP Act 2023 audit log generated."
                      if n > 0 else "No standard PII/PHI patterns found. Verify manually before external sharing.")
            ai_recommendation_card(
                f"{n} sensitive item(s) detected and anonymised" if n else "No sensitive information detected",
                risk, action, f"Entity types: {', '.join(result['types'])}" if result['types'] else "")

            if result["types"]:
                chips = '<div class="pii-chips">'
                for pt in result["types"]:
                    cls = CHIP_MAP.get(pt, "cg")
                    chips += f'<span class="chip {cls}">● {pt}</span>'
                chips += f'<span class="chip cg">Total: {n}</span></div>'
                st.markdown(chips, unsafe_allow_html=True)

            col_s1, col_s2 = st.columns(2, gap="large")
            fname = anon_file.name if anon_file else "document"
            base  = fname.rsplit(".",1)[0] if "." in fname else fname
            now   = datetime.datetime.now().isoformat()

            with col_s1:
                st.markdown('<span style="background:#003087;color:white;border-radius:20px;padding:3px 12px;font-size:11px;font-weight:600;">Step 1 — Reversible pseudonymisation</span>', unsafe_allow_html=True)
                st.text_area("", result["step1"], height=260, key="s1o", label_visibility="collapsed")
                tok_json = _json.dumps({
                    "document": fname, "generatedAt": now,
                    "note": "In production, encrypt this file with AES-256 at rest.",
                    "mappings": [{"token": r["Token"], "originalValue": r["Original Value"],
                                  "entityType": r["Entity Type"]} for r in result["tokens"]]
                }, indent=2)
                st.download_button("⬇ Token Registry (JSON)", tok_json,
                                   file_name=f"{base}_TokenRegistry.json", mime="application/json",
                                   use_container_width=True)

            with col_s2:
                st.markdown('<span style="background:#0f766e;color:white;border-radius:20px;padding:3px 12px;font-size:11px;font-weight:600;">Step 2 — Irreversible generalisation</span>', unsafe_allow_html=True)
                st.text_area("", result["step2"], height=260, key="s2o", label_visibility="collapsed")
                st.download_button("⬇ Anonymised Document (TXT)", result["step2"],
                                   file_name=f"{base}_Anonymised.txt", mime="text/plain",
                                   use_container_width=True)

            with st.expander("Compliance audit log (DPDP Act 2023)", expanded=False):
                st.markdown('<div class="tw">', unsafe_allow_html=True)
                st.dataframe(
                    pd.DataFrame(result["audit"]),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Entity":      st.column_config.TextColumn("Entity",      width="medium"),
                        "Type":        st.column_config.TextColumn("Type",        width="small"),
                        "Action":      st.column_config.TextColumn("Action",      width="medium"),
                        "Replacement": st.column_config.TextColumn("Replacement", width="medium"),
                    },
                )
                st.markdown('</div>', unsafe_allow_html=True)

            if result["tokens"]:
                with st.expander("Token mapping table (Step 1 registry)", expanded=False):
                    st.markdown('<div class="tw">', unsafe_allow_html=True)
                    st.dataframe(
                        pd.DataFrame(result["tokens"]),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Token":    st.column_config.TextColumn("Token",    width="medium"),
                            "Original": st.column_config.TextColumn("Original", width="medium"),
                            "Type":     st.column_config.TextColumn("Type",     width="small"),
                        },
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

            add_audit_event("Anonymisation", f"Anonymised document — {n} PII/PHI entities",
                            0.93, "AI output generated", "Generated", fname,
                            f"Two-step DPDP Act 2023 anonymisation. Entities: {', '.join(result['types'])}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SUMMARISATION
# ═══════════════════════════════════════════════════════════════════════════════
with t_sum:
    render_banner("Summarisation", "Structured summaries for SAE narratives · SUGAM checklists · Meeting transcripts")
    st.markdown("""
<div class="sec-hd">
  <div class="sec-ic ic-teal">📄</div>
  <div><h2>Document Summarisation</h2>
  <p>Three source types: SAE Case Narration · Application Checklist (SUGAM) · Meeting Transcript/Audio</p></div>
</div>
""", unsafe_allow_html=True)

    if CLAUDE_OK:
        st.markdown('<div class="rc info">✓ Claude AI active — summaries will be AI-enhanced where available.</div>', unsafe_allow_html=True)

    doc_type = st.selectbox("Document type",
        ["SAE Case Narration", "Application Checklist (SUGAM)", "Meeting Transcript / Audio"])

    st.markdown('<div class="upload-card"><h4>📁 Upload document</h4>', unsafe_allow_html=True)
    if doc_type == "Meeting Transcript / Audio":
        st.markdown('<div class="audio-note">Audio accepted. Automatic transcription requires Stage 2 Whisper API integration. Paste transcript text below.</div>', unsafe_allow_html=True)
        sum_file = st.file_uploader(AUDIO_UPLOAD_LABEL, type=AUDIO_UPLOAD_TYPES, key="sum_up")
    else:
        sum_file = st.file_uploader(DOCUMENT_UPLOAD_LABEL, type=DOCUMENT_UPLOAD_TYPES, key="sum_up2")

    if sum_file:
        name_l = sum_file.name.lower()
        if any(name_l.endswith(x) for x in [".mp3",".wav",".m4a"]):
            st.success(f"✓ Audio received: {sum_file.name} — paste transcript text below")
        else:
            txt, err = extract_text(sum_file)
            if err: st.error(err)
            elif txt.strip():
                st.session_state["sum_text"] = st.session_state["sum_ta"] = txt
                st.success(f"✓ Extracted {len(txt.split())} words from {sum_file.name}")

    st.markdown('<div class="or-line">or paste text manually</div>', unsafe_allow_html=True)
    st.text_area("Document content", height=200, placeholder="Paste content here...", key="sum_ta")
    st.session_state["sum_text"] = st.session_state.get("sum_ta","")
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2, _ = st.columns([1,1,3])
    with c1: run_sum = st.button("Summarise document", type="primary", use_container_width=True)
    with c2:
        if st.button("🗑 Clear ", use_container_width=True, key="sum_clear"):
            st.session_state["sum_text"] = st.session_state["sum_ta"] = ""
            st.rerun()

    if run_sum:
        content = st.session_state["sum_text"].strip()
        if not content:
            st.markdown('<div class="rc warn">Please upload or paste content first.</div>', unsafe_allow_html=True)
        else:
            # Try Claude AI first, fall back to rule-based
            ai_result = claude_summarise(content, doc_type) if CLAUDE_OK else None
            if ai_result:
                st.markdown('<div class="rc info">AI-enhanced summary (Claude Haiku)</div>', unsafe_allow_html=True)
                st.markdown(ai_result)
                st.markdown("---")
                st.caption("Rule-based structured analysis below:")

            if doc_type == "SAE Case Narration":
                r = summarise_sae(content)
                cc = "err" if r["priority"]=="URGENT" else "warn" if r["priority"]=="STANDARD" else "ok"
                risk_map = {"URGENT":"Critical","STANDARD":"Medium","LOW":"Low"}
                action_map = {
                    "URGENT": f"Immediate escalation to DCGI required. {r['timeline']} report applicable under NDCT Rules 2019.",
                    "STANDARD": "Route to standard SAE review queue. Expedited 15-day report required.",
                    "LOW": "Log as periodic SAE. Standard 90-day reporting timeline applies.",
                }
                ai_recommendation_card(
                    f"SAE classified as {r['priority']} · {r['causality']} · Outcome: {r['outcome']}",
                    risk_map[r["priority"]], action_map[r["priority"]], "CDSCO Form 12A")
                st.markdown(f'<div class="rc {cc}"><b>Priority: {r["priority"]}</b> · Causality: {r["causality"]} · Outcome: {r["outcome"]}</div>', unsafe_allow_html=True)
                c1,c2,c3 = st.columns(3)
                c1.metric("Priority", r["priority"]); c2.metric("Causality", r["causality"]); c3.metric("Outcome", r["outcome"])
                with st.expander("Full Structured SAE Summary", expanded=True):
                    st.markdown(f"| Field | Value |\n|---|---|\n| Priority | {r['priority']} |\n| Causality | {r['causality']} |\n| Outcome | {r['outcome']} |\n| Setting | {r['setting']} |\n| Reporting Timeline | {r['timeline']} |")
                st.download_button("⬇ SAE Summary (TXT)",
                    f"Priority:{r['priority']}\nCausality:{r['causality']}\nOutcome:{r['outcome']}\nTimeline:{r['timeline']}",
                    file_name="sae_summary.txt")

            elif doc_type == "Application Checklist (SUGAM)":
                r = summarise_checklist(content)
                cc = "ok" if r["score"] >= 80 else "warn" if r["score"] >= 50 else "err"
                risk_c = "Low" if r["score"] >= 80 else "Medium" if r["score"] >= 50 else "High"
                ai_recommendation_card(f"Checklist score: {r['score']}% · {r['recommendation']}",
                    risk_c, f"{r['missing']} fields missing, {r['incomplete']} incomplete.", "SUGAM portal")
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Total",r["total"]); c2.metric("Complete",r["complete"])
                c3.metric("Incomplete",r["incomplete"]); c4.metric("Missing",r["missing"])
                st.progress(r["score"]/100, text=f"Score: {r['score']}%")
                st.markdown(f'<div class="rc {cc}"><b>Recommendation:</b> {r["recommendation"]}</div>', unsafe_allow_html=True)
                if r["actions"]:
                    with st.expander("Actionable Items", expanded=True):
                        for i,a in enumerate(r["actions"][:10],1): st.markdown(f"{i}. {a}")

            else:  # Meeting
                r = summarise_meeting(content)
                ai_recommendation_card("Meeting transcript summarised", "Low",
                    f"{len(r['decisions'])} decisions, {len(r['actions'])} action items, {len(r['next_steps'])} next steps extracted.", "Meeting summary")
                if r["decisions"]:
                    with st.expander("✅ Key Decisions", expanded=True):
                        for d in r["decisions"]: st.write(f"• {d}")
                if r["actions"]:
                    with st.expander("📌 Action Items", expanded=True):
                        for a in r["actions"]: st.write(f"• {a}")
                if r["next_steps"]:
                    with st.expander("📅 Next Steps", expanded=False):
                        for n in r["next_steps"]: st.write(f"• {n}")

            add_audit_event("Summarisation", f"Document summarised — {doc_type}", 0.90,
                            "AI output generated", "Generated", doc_type, "")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — COMPLETENESS
# ═══════════════════════════════════════════════════════════════════════════════
with t_comp:
    render_banner("Completeness Check", "NDCT Rules 2019 / Form CT mandatory field assessment · RAG status · Approve / Return / Reject")
    st.markdown("""
<div class="sec-hd">
  <div class="sec-ic ic-purple">✅</div>
  <div><h2>Completeness Assessment — NDCT Rules 2019 / Form CT</h2>
  <p>Checks 20 mandatory fields · RAG status per field · Approve / Return / Reject recommendation · Critical gap flagging</p></div>
</div>
""", unsafe_allow_html=True)

    col_a, col_b = st.columns([3,1])
    with col_a:
        st.markdown('<div class="upload-card"><h4>📁 Upload application document</h4>', unsafe_allow_html=True)
        comp_file = st.file_uploader(DOCUMENT_UPLOAD_LABEL, type=DOCUMENT_UPLOAD_TYPES, key="comp_up")
        if comp_file:
            txt, err = extract_text(comp_file)
            if err: st.error(err)
            elif txt.strip():
                st.session_state["comp_text"] = st.session_state["comp_ta"] = txt
                st.success(f"✓ Extracted {len(txt.split())} words from {comp_file.name}")
        st.markdown('<div class="or-line">or paste text manually</div>', unsafe_allow_html=True)
        st.text_area("Application content", height=180,
                     placeholder="Paste SUGAM application or checklist content...", key="comp_ta")
        st.session_state["comp_text"] = st.session_state.get("comp_ta","")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_b:
        app_id = st.text_input("Application ID", placeholder="SUGAM-CT-2024-0892")
        st.markdown("<br>", unsafe_allow_html=True)
        run_comp = st.button("✅ Check Completeness", type="primary", use_container_width=True)

    if run_comp:
        content = st.session_state["comp_text"].strip()
        if not content:
            st.markdown('<div class="rc warn">Please upload or paste content first.</div>', unsafe_allow_html=True)
        else:
            r = assess_completeness(content)
            cc = "ok" if r["score"] >= 85 and not r["critical_missing"] else "warn" if r["score"] >= 60 else "err"
            risk_c = "Critical" if r["critical_missing"] else "High" if r["score"] < 60 else "Medium" if r["score"] < 85 else "Low"
            action = (f"Reject — {len(r['critical_missing'])} critical field(s) missing: {', '.join(r['critical_missing'][:3])}."
                      if r["critical_missing"] else
                      f"Return — {r['total'] - r['present']} field(s) need attention."
                      if r["score"] < 85 else "Approve for technical review — all critical fields present.")
            ai_recommendation_card(f"Application completeness: {r['score']}% · {r['recommendation']}",
                risk_c, action, f"Fields checked: {r['total']} · Present: {r['present']} · Missing: {r['total']-r['present']}")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total",r["total"]); c2.metric("Present",r["present"])
            c3.metric("Missing",r["total"]-r["present"])
            c4.metric("Score",f"{r['score']}%")
            st.progress(r["score"]/100, text=f"Application completeness: {r['score']}%")
            st.markdown(f'<div class="rc {cc}"><b>Recommendation:</b> {r["recommendation"]}</div>', unsafe_allow_html=True)
            if r["critical_missing"]: st.error(f"Critical missing: {', '.join(r['critical_missing'])}")
            if r["major_missing"]: st.warning(f"Major missing: {', '.join(r['major_missing'])}")
            with st.expander("Full Field Status (RAG)", expanded=True):
                def srag(v):
                    if "Green" in str(v): return "background-color:#dcfce7;color:#15803d;font-weight:600"
                    if "Amber" in str(v): return "background-color:#fef9c3;color:#a16207;font-weight:600"
                    if "Red"   in str(v): return "background-color:#fee2e2;color:#b91c1c;font-weight:600"
                    return ""
                df = pd.DataFrame(r["rows"])
                st.markdown('<div class="tw">', unsafe_allow_html=True)
                st.dataframe(
                    df.style.map(srag, subset=["RAG"]),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Field":       st.column_config.TextColumn("Field",       width="medium"),
                        "Status":      st.column_config.TextColumn("Status",      width="small"),
                        "RAG":         st.column_config.TextColumn("RAG",         width="small"),
                        "Note":        st.column_config.TextColumn("Note",        width="large"),
                        "Requirement": st.column_config.TextColumn("Requirement", width="medium"),
                    },
                )
                st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("⬇ Completeness Report (CSV)", df.to_csv(index=False),
                               file_name="completeness_report.csv", mime="text/csv")
            add_audit_event("Completeness", f"Assessment — score {r['score']}%", 0.91,
                            "AI output generated", "Generated",
                            app_id or "unknown", r["recommendation"])

    st.markdown("---")
    st.markdown("**Reviewer Actions**")
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        if st.button("Confirm Reviewer Action", use_container_width=True, key="comp_confirm"):
            confirm_reviewer_action("Completeness Check", "Reviewer confirmed completeness assessment", "Completeness accepted.", app_id or "unknown", confidence=0.91)
            st.success("Confirmed.")
    with cc2:
        if st.button("Escalate Low-Confidence", use_container_width=True, key="comp_escalate"):
            confirm_reviewer_action("Completeness Check", "Escalated", "Escalated due to critical missing fields.", app_id or "unknown", confidence=0.91, final_status="Escalated")
            st.warning("Escalated.")
    with cc3:
        if st.button("Create Review Packet", use_container_width=True, key="comp_packet"):
            pkt_comp = generate_audit_packet()
            st.success("Review packet generated.")
    with cc4:
        if st.button("Open Audit Trail", use_container_width=True, key="comp_audit"):
            go_to("Audit Trail")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CATEGORISATION
# ═══════════════════════════════════════════════════════════════════════════════
with t_cls:
    render_banner("Categorisation", "SAE severity grading · ICD-10 mapping · Session-based duplicate detection")
    st.markdown("""
<div class="sec-hd">
  <div class="sec-ic ic-amber">🏷️</div>
  <div><h2>SAE Categorisation &amp; Duplicate Detection</h2>
  <p>DEATH · DISABILITY · HOSPITALISATION · OTHERS · ICD-10 mapping · Session-based duplicate detection</p></div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="dup-session"><b>Duplicate detection:</b> Upload multiple SAE reports below.
The system cross-checks Patient IDs and drug names across all session files to flag duplicates.
Files are cleared on browser refresh — DPDP compliant (no external storage).</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="upload-card"><h4>📁 Primary SAE Report</h4>', unsafe_allow_html=True)
    cls_file = st.file_uploader(DOCUMENT_UPLOAD_LABEL, type=DOCUMENT_UPLOAD_TYPES, key="class_up")
    if cls_file:
        txt, err = extract_text(cls_file)
        if err: st.error(err)
        elif txt.strip():
            st.session_state["class_text"] = st.session_state["class_ta"] = txt
            st.session_state["dup_files"]["SAE-1"] = {"name": cls_file.name, "text": txt}
            st.success(f"✓ Loaded: {cls_file.name}")
    st.markdown('<div class="or-line">or paste text</div>', unsafe_allow_html=True)
    st.text_area("SAE report content", height=160, key="class_ta")
    st.session_state["class_text"] = st.session_state.get("class_ta","")
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("+ Add more SAE reports for duplicate detection", expanded=False):
        dcols = st.columns(2)
        for idx, (slot, label) in enumerate([("SAE-2","SAE Report 2"),("SAE-3","SAE Report 3")]):
            with dcols[idx]:
                f2 = st.file_uploader(label, type=DOCUMENT_UPLOAD_TYPES, key=f"dup_{slot}")
                if f2:
                    t2, e2 = extract_text(f2)
                    if not e2 and t2.strip():
                        st.session_state["dup_files"][slot] = {"name": f2.name, "text": t2}
                        st.success(f"✓ {f2.name}")
        if st.session_state["dup_files"]:
            st.write(f"**Files in session:** {', '.join(v['name'] for v in st.session_state['dup_files'].values())}")
        if st.button("🗑 Clear session files"):
            st.session_state["dup_files"] = {}; st.rerun()

    c1, _, _ = st.columns([1,1,3])
    with c1: run_cls = st.button("🏷️ Categorise & Check Duplicates", type="primary", use_container_width=True)

    if run_cls:
        content = st.session_state["class_text"].strip()
        if not content:
            st.markdown('<div class="rc warn">Please upload or paste an SAE report first.</div>', unsafe_allow_html=True)
        else:
            r = classify_sae(content)
            risk_map = {"DEATH":"Critical","DISABILITY":"High","HOSPITALISATION":"Medium","OTHERS":"Low"}
            action_map = {
                "DEATH":          "Expedited 7-day report mandatory. Immediate notification to DCGI and Ethics Committee required under NDCT Rules 2019.",
                "DISABILITY":     "Expedited 15-day report required. Notify sponsor and Ethics Committee. Assess causality.",
                "HOSPITALISATION":"Expedited 15-day report required. Monitor patient outcome and submit follow-up report.",
                "OTHERS":         "Periodic reporting within 90 days. Document in safety database.",
            }
            sev_colours = {"DEATH":"background:#fee2e2;color:#991b1b","DISABILITY":"background:#ffedd5;color:#9a3412",
                           "HOSPITALISATION":"background:#fef9c3;color:#92400e","OTHERS":"background:#dbeafe;color:#1e40af"}
            ai_recommendation_card(
                f"SAE classified as {r['severity']} · Confidence: {r['confidence']} · Priority queue: {r['priority']}/4",
                risk_map[r["severity"]], action_map[r["severity"]],
                f"ICD-10: {r['icd10']} · Reporting timeline: {r['timeline']}")
            st.markdown(f'<div style="{sev_colours[r["severity"]]};border-radius:10px;padding:10px 20px;font-size:18px;font-weight:700;display:inline-block;margin-bottom:12px;">⬤ {r["severity"]}</div>', unsafe_allow_html=True)
            c1,c2,c3 = st.columns(3)
            c1.metric("Severity",r["severity"]); c2.metric("Confidence",r["confidence"]); c3.metric("Priority Queue",f"{r['priority']} / 4")
            with st.expander("Classification Evidence", expanded=True):
                st.markdown(f'<div class="rc info"><b>Keywords detected:</b> {", ".join(r["keywords"])}<br><b>ICD-10:</b> {r["icd10"]} · <b>Reporting:</b> {r["timeline"]}</div>', unsafe_allow_html=True)

            st.markdown("**Duplicate detection across session files**")
            dups = detect_duplicates(content, st.session_state["dup_files"])
            if len(st.session_state["dup_files"]) > 1:
                if dups:
                    for d in dups:
                        st.markdown(f'<div class="rc err">⚠️ DUPLICATE DETECTED — matches <b>{d["file"]}</b> · Patient IDs: {d["shared_ids"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="rc ok">✓ No duplicates found across session files.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="rc info">Upload additional SAE reports above to enable duplicate cross-checking.</div>', unsafe_allow_html=True)

            report_txt = f"Severity:{r['severity']}\nConfidence:{r['confidence']}\nKeywords:{', '.join(r['keywords'])}\nPriority:{r['priority']}/4\nICD-10:{r['icd10']}\nTimeline:{r['timeline']}"
            st.download_button("⬇ Classification Report (TXT)", report_txt, file_name="classification_report.txt")
            add_audit_event("Classification", f"SAE classified as {r['severity']}", 0.93,
                            "AI output generated", "Generated", "SAE upload", action_map[r["severity"]])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════
with t_cmp:
    render_banner("Version Compare", "Semantic document diff · Substantive vs administrative change flagging · Downloadable report")
    st.markdown("""
<div class="sec-hd">
  <div class="sec-ic ic-sky">🔍</div>
  <div><h2>Document Comparison</h2>
  <p>Upload two filing versions · Substantive vs administrative diff · Colour-coded table · Downloadable PDF report</p></div>
</div>
""", unsafe_allow_html=True)

    cv1, cv2 = st.columns(2)
    with cv1:
        st.markdown("**Version 1 — Original**")
        v1f = st.file_uploader("Upload V1", type=DOCUMENT_UPLOAD_TYPES, key="v1f")
        if v1f:
            t, e = extract_text(v1f)
            if not e and t.strip():
                st.session_state["v1_text"] = st.session_state["v1ta"] = t
                st.success(f"✓ {v1f.name}")
        st.text_area("or paste V1", height=200, key="v1ta", placeholder="Original document...")
        st.session_state["v1_text"] = st.session_state.get("v1ta","")
    with cv2:
        st.markdown("**Version 2 — Updated**")
        v2f = st.file_uploader("Upload V2", type=DOCUMENT_UPLOAD_TYPES, key="v2f")
        if v2f:
            t, e = extract_text(v2f)
            if not e and t.strip():
                st.session_state["v2_text"] = st.session_state["v2ta"] = t
                st.success(f"✓ {v2f.name}")
        st.text_area("or paste V2", height=200, key="v2ta", placeholder="Updated document...")
        st.session_state["v2_text"] = st.session_state.get("v2ta","")

    c1, _, _ = st.columns([1,1,3])
    with c1: run_cmp = st.button("🔍 Compare Documents", type="primary", use_container_width=True)

    if run_cmp:
        t1c = st.session_state["v1_text"].strip()
        t2c = st.session_state["v2_text"].strip()
        if not t1c or not t2c:
            st.markdown('<div class="rc warn">Please provide both document versions.</div>', unsafe_allow_html=True)
        else:
            changes = compare_documents(t1c, t2c)
            sc = sum(1 for c in changes if c["Substantive"] == "Yes")
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Total",len(changes)); c2.metric("Added",sum(1 for c in changes if c["Type"]=="ADDED"))
            c3.metric("Removed",sum(1 for c in changes if c["Type"]=="REMOVED"))
            c4.metric("Changed",sum(1 for c in changes if c["Type"]=="CHANGED")); c5.metric("Substantive",sc)
            risk_c = "High" if sc >= 3 else "Medium" if sc >= 1 else "Low"
            action = (f"{sc} substantive change(s) detected — formal review and possible amended submission to CDSCO required."
                      if sc > 0 else "No substantive changes. Administrative edits only — may proceed without re-review.")
            ai_recommendation_card(f"{len(changes)} changes · {sc} substantive · {len(changes)-sc} administrative",
                risk_c, action, "Substantive: changes affecting dosage, safety, outcomes, or patient information.")
            cc = "err" if sc > 0 else "ok"
            st.markdown(f'<div class="rc {cc}">{"⚠️ "+str(sc)+" substantive change(s) — regulatory review required." if sc > 0 else "✓ No substantive changes detected."}</div>', unsafe_allow_html=True)
            if changes:
                def sd(row):
                    if row["Type"]=="ADDED": return ["background-color:#dcfce7"]*len(row)
                    if row["Type"]=="REMOVED": return ["background-color:#fee2e2"]*len(row)
                    if row["Substantive"]=="Yes": return ["background-color:#fef9c3"]*len(row)
                    return [""]*len(row)
                df = pd.DataFrame(changes)
                with st.expander("Full Change Table", expanded=True):
                    st.markdown('<div class="tw">', unsafe_allow_html=True)
                    st.dataframe(
                        df.style.apply(sd, axis=1),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Type":        st.column_config.TextColumn("Type",        width="small"),
                            "Original":    st.column_config.TextColumn("Original",    width="large"),
                            "New":         st.column_config.TextColumn("New",         width="large"),
                            "Substantive": st.column_config.TextColumn("Substantive", width="small"),
                        },
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.caption("🟢 Added · 🔴 Removed · 🟡 Changed (Substantive)")
                st.download_button("⬇ Comparison Report (CSV)", df.to_csv(index=False),
                                   file_name="comparison_report.csv", mime="text/csv")
            add_audit_event("Comparison", f"{len(changes)} changes — {sc} substantive", 0.91,
                            "AI output generated", "Generated", "Document comparison", action)



# ═══════════════════════════════════════════════════════════════════════════════
# INSPECTION REPORT — removed from ribbon per spec; logic preserved for audit
# ═══════════════════════════════════════════════════════════════════════════════
# (Content retained below for reference; no longer rendered in a tab)
if False:  # Inspection Report tab removed from ribbon
    st.markdown("""
<div class="sec-hd">
  <div class="sec-ic ic-pink">📋</div>
  <div><h2>Inspection Report Generation</h2>
  <p>Raw site observations → Formal CDSCO GCP report · Critical / Major / Minor grading · CAPA timelines · NDCT Rules 2019</p></div>
</div>
""", unsafe_allow_html=True)

    ic1,ic2,ic3,ic4 = st.columns(4)
    with ic1: insp_name = st.text_input("Inspector Name", placeholder="Dr. A.K. Sharma")
    with ic2: insp_site = st.text_input("Site Name", placeholder="AIIMS Delhi")
    with ic3: insp_sno  = st.text_input("Site Number", placeholder="SITE-DEL-001")
    with ic4: insp_date = st.date_input("Inspection Date")

    obs = st.text_area("Raw inspection observations — one per line", height=180, key="obs_ta",
        placeholder="No record of drug accountability for subjects 3 and 7\nInformed consent missing local language version\nMinor labelling error on storage box")

    c1, _, _ = st.columns([1,1,3])
    with c1: run_insp = st.button("📋 Generate Report", type="primary", use_container_width=True)

    if run_insp and obs.strip():
        rpt = generate_inspection_report(obs, insp_site, insp_sno, insp_name, insp_date)
        risk_label = "Critical" if rpt["critical"] > 0 else "High" if rpt["major"] > 0 else "Low"
        action_insp = (f"{rpt['critical']} Critical GCP deviation(s). Immediate CAPA required. Report to DCGI within 15 days."
                       if rpt["critical"] > 0 else
                       f"{rpt['major']} Major deviation(s). CAPA plan within 30 days."
                       if rpt["major"] > 0 else
                       f"No Critical or Major findings. {rpt['minor']} Minor deviation(s) to be logged within 60 days.")
        ai_recommendation_card(
            f"Inspection: {rpt['critical']} Critical · {rpt['major']} Major · {rpt['minor']} Minor",
            risk_label, action_insp,
            f"Site: {insp_site or '[Site]'} · {insp_date.strftime('%d %B %Y')} · Inspector: {insp_name or '[Inspector]'}")
        cc = "err" if rpt["critical"] > 0 else "warn" if rpt["major"] > 0 else "ok"
        st.markdown(f'<div class="rc {cc}">{"⚠️ "+str(rpt["critical"])+" Critical findings — CAPA required." if rpt["critical"] > 0 else "⚠️ "+str(rpt["major"])+" Major findings — CAPA due in 30 days." if rpt["major"] > 0 else "✓ No Critical or Major findings."}</div>', unsafe_allow_html=True)
        ic1,ic2,ic3 = st.columns(3)
        ic1.metric("Critical",rpt["critical"]); ic2.metric("Major",rpt["major"]); ic3.metric("Minor",rpt["minor"])
        df = pd.DataFrame(rpt["rows"])
        def sr(v):
            if v=="Critical": return "background-color:#fee2e2;color:#991b1b;font-weight:700"
            if v=="Major":    return "background-color:#fef9c3;color:#92400e;font-weight:700"
            if v=="Minor":    return "background-color:#dcfce7;color:#166534"
            return ""
        with st.expander("Full Inspection Report Table", expanded=True):
            st.markdown('<div class="tw">', unsafe_allow_html=True)
            st.dataframe(
                df.style.map(sr, subset=["Risk"]),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Obs":                   st.column_config.TextColumn("Obs",            width="small"),
                    "Raw":                   st.column_config.TextColumn("Raw Observation", width="medium"),
                    "Formal Finding":        st.column_config.TextColumn("Formal Finding",  width="large"),
                    "Risk":                  st.column_config.TextColumn("Risk",            width="small"),
                    "Corrective Action":     st.column_config.TextColumn("Corrective Action", width="medium"),
                    "Deadline":              st.column_config.TextColumn("Deadline",        width="small"),
                    "Regulatory Reference":  st.column_config.TextColumn("Regulatory Ref.", width="medium"),
                },
            )
            st.markdown('</div>', unsafe_allow_html=True)
        st.download_button("⬇ Inspection Report (TXT)", rpt["full_text"],
                           file_name=f"inspection_report_{insp_date}.txt", mime="text/plain")
        add_audit_event("Inspection Report",
                        f"Report generated — {rpt['critical']} Critical, {rpt['major']} Major, {rpt['minor']} Minor",
                        0.92, "AI output generated", "Generated",
                        insp_site or "unknown site", action_insp)
    elif run_insp:
        st.markdown('<div class="rc warn">Please enter at least one observation.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# REVIEW WORKFLOW — routing logic; functions defined here, called from ribbon tabs
# ═══════════════════════════════════════════════════════════════════════════════
if True:  # scope block — functions promoted to module level via exec pattern
    case = get_active_case()

    def command_dashboard() -> None:
        active_case = get_active_case()
        active_case["current_stage"] = "Command Dashboard"
        save_active_case(active_case)
        dashboard_case = get_command_dashboard_snapshot()
        selected_doc = dashboard_case["documents"][dashboard_case["selected_document_id"]]
        render_metrics()
        render_case_header(dashboard_case)
        sc1,sc2,sc3 = st.columns(3)
        with sc1:
            st.metric("Selected document", selected_doc["type"])
            st.metric("Reviewer confirmations", len(dashboard_case["reviewer_decisions"]))
        with sc2:
            st.metric("Protected-view status", "Validated" if dashboard_case["protected_view"]["validated"] else "Pending")
            st.metric("SAE packet", "Ready" if dashboard_case["sae_review"]["review_packet"] else "Pending")
        with sc3:
            st.metric("Compare packet", "Ready" if dashboard_case["compare_review"]["review_packet"] else "Pending")
            st.metric("Audit packet", "Ready" if dashboard_case["export_readiness"]["audit_packet"] else "Pending")
        st.caption("Live Integration coming in Phase 2")
        st.caption("Dashboard → Document Intake → Protected View → SAE Review → Version Compare → Audit Trail")
        ac1,ac2,ac3 = st.columns(3)
        with ac1:
            if st.button("Open Document Intake", use_container_width=True):
                add_audit_event("Command Dashboard","Workflow routed",1.0,"Opened Document Intake","Completed",active_case["packet_id"],""); go_to("Document Intake")
        with ac2:
            if st.button("Jump to SAE Review", use_container_width=True):
                add_audit_event("Command Dashboard","Workflow routed",1.0,"Opened SAE Review","Completed",active_case["packet_id"],""); go_to("SAE Review")
        with ac3:
            if st.button("Open Audit Trail", use_container_width=True): go_to("Audit Trail")
        st.markdown("### Source packet overview")
        dc1,dc2,dc3 = st.columns(3)
        for idx, doc in enumerate(dashboard_case["documents"].values()):
            with [dc1,dc2,dc3][idx % 3]:
                with st.container(border=True):
                    st.write(f"**{doc['name']}**"); st.write(f"Type: {doc['type']}")
                    st.write(f"Source: {doc['source']}"); st.write(f"Risk: {doc['risk_level']}")
                    st.caption(doc["preview"])

    def document_intake(widget_scope: str = "main") -> None:
        active_case = get_active_case()
        active_case["current_stage"] = "Document Intake"; save_active_case(active_case)
        
        doc_ids  = [None] + list(active_case["documents"].keys()) + ["__upload__"]
        
        # Ensure selected_document_id is None if it's the first time
        if "selected_document_id" not in active_case:
             active_case["selected_document_id"] = None

        selected = st.selectbox("Case packet document", 
                                options=doc_ids,
                                index=doc_ids.index(active_case["selected_document_id"]) if active_case["selected_document_id"] in doc_ids else 0,
                                format_func=lambda d: "📂 Browse files to upload (Limit 200 MB per file)" if d == "__upload__" else (active_case["documents"][d]["name"] if d else ""),
                                key=f"di_selectbox_{widget_scope}")
        
        if selected == "__upload__":
            selected = _render_document_intake_uploader("workflow_doc_upload")
            if not selected:
                return
            active_case = get_active_case()

        if selected is None:
            st.info("Please select a document from the dropdown or upload a new one to view details.")
            return

        if selected != active_case["selected_document_id"]:
            active_case["selected_document_id"] = selected; save_active_case(active_case)
            active_case = get_active_case()
        
        sel_doc = active_case["documents"][active_case["selected_document_id"]]
        st.markdown("### Intake controls")
        ic1,ic3,ic4 = st.columns([1,1,1]) # Removed ic2 for Confirm action
        with ic1:
            if st.button("Run Categorisation", key=f"di_run_categorisation_{widget_scope}", use_container_width=True): run_categorisation(); st.success("Categorisation recorded.")
        with ic3:
            if st.button("Escalate low-confidence", key=f"di_escalate_{widget_scope}", use_container_width=True):
                confirm_reviewer_action("Document Intake","Escalated",sel_doc.get("classification",{}).get("escalation_recommendation","Escalation requested."),sel_doc["name"],confidence=sel_doc["confidence"],final_status="Escalated"); st.warning("Escalation recorded.")
        with ic4:
            if st.button("→ Anonymisation", key=f"di_to_anonymisation_{widget_scope}", use_container_width=True): go_to_anonymisation()
            
        dt1, dt2, dt3 = st.tabs(["Categorisation","Synopsis","Source"])
        with dt1:
            clf = active_case.get("document_classification") or sel_doc.get("classification", {})
            with st.container(border=True):
                st.write(f"**Probable type:** {clf.get('probable_type','Pending')}"); st.write(f"**Severity:** {clf.get('severity',sel_doc['risk_level'])}")
                st.write(f"**Duplicate warning:** {clf.get('duplicate_warning','Pending')}"); st.write(f"**Escalation:** {clf.get('escalation_recommendation','Pending')}"); st.write(f"**Confidence:** {int(sel_doc['confidence']*100)}%")
        with dt2:
            syn = active_case.get("structured_synopsis") or sel_doc.get("synopsis", {})
            with st.container(border=True):
                st.write(f"**Headline:** {syn.get('headline','Pending')}"); st.write(syn.get("summary","Run Categorisation to generate synopsis."))
                for sig in syn.get("key_signals",[]): st.write(f"- {sig}")
                if syn.get("reviewer_prompt"): st.info(syn["reviewer_prompt"])
        with dt3:
            with st.container(border=True): st.write(sel_doc["raw_text"])

    def protected_view_screen() -> None:
        case["current_stage"] = "Protected View"; save_active_case(case)
        protected = case["protected_view"]
        pv_doc    = case["documents"][protected["source_document_id"]]
        fc1,fc2,fc3,fc4 = st.columns(4)
        cats = protected["category_filters"]
        with fc1: cats["Patient"]      = st.checkbox("Patient identifiers",      value=cats["Patient"])
        with fc2: cats["Investigator"] = st.checkbox("Investigator identifiers", value=cats["Investigator"])
        with fc3: cats["Date"]         = st.checkbox("Dates",                    value=cats["Date"])
        with fc4: cats["Site"]         = st.checkbox("Site identifiers",         value=cats["Site"])
        save_active_case(case)
        ent_cols = st.columns(2)
        with ent_cols[0]:
            st.markdown("**Original document**")
            st.markdown(f'<div class="entity-box">{pv_doc["raw_text"]}</div>', unsafe_allow_html=True)
        with ent_cols[1]:
            st.markdown("**Protected view**")
            st.markdown(f'<div class="entity-box">{apply_redaction_filters(case)}</div>', unsafe_allow_html=True)
        st.markdown("### Entity review")
        for entity in protected["entities"]:
            with st.container(border=True):
                ec1,ec2,ec3 = st.columns([2,2,1])
                with ec1: st.write(f"**{entity['label']}** — `{entity['value']}`")
                with ec2: st.write(f"Replacement: `{entity['replacement']}` | Confidence: {int(entity['confidence']*100)}%")
                with ec3: entity["approved"] = st.checkbox("Approve",value=entity["approved"],key=f"ent_{entity['label']}")
        save_active_case(case)
        pa1,pa2,pa3 = st.columns(3)
        with pa1:
            if st.button("Validate protected view", use_container_width=True): validate_redaction(); st.success("Protected view validated.")
        with pa2:
            if st.button("Confirm reviewer action", use_container_width=True):
                confirm_reviewer_action("Protected View","Reviewer confirmed protected view","Redaction confirmed.",pv_doc["name"],confidence=0.93); st.success("Confirmed.")
        with pa3:
            if st.button("→ SAE Review", use_container_width=True): go_to("SAE Review")
        if protected["validated"]: st.success(f"✓ {protected['validation_summary']} — {protected['escalation_status']}")

    def sae_review_screen() -> None:
        active_case = get_active_case()
        active_case["current_stage"] = "SAE Review"; save_active_case(active_case)
        _render_sae_review_uploader("workflow_sae_upload")
        active_case = get_active_case()
        sae = active_case["sae_review"]
        with st.container(border=True):
            sc1,sc2,sc3 = st.columns(3)
            with sc1: st.write(f"**Patient:** {sae['patient_profile']}"); st.write(f"**Event:** {sae['event']}")
            with sc2: st.write(f"**Seriousness:** {sae['seriousness']}"); st.write(f"**Causality:** {sae['causality']}")
            with sc3: st.write(f"**Action:** {sae['action_taken']}"); st.write(f"**Outcome:** {sae['outcome']}")
        st.markdown("**Missing information**")
        for item in sae["missing_info"]:
            item["resolved"] = st.checkbox(item["item"], value=item["resolved"], key=f"mi_{item['item']}")
        sae["reviewer_notes"] = st.text_area("Reviewer notes", value=sae["reviewer_notes"], height=80)
        save_active_case(active_case)
        sa1,sa2,sa3,sa4 = st.columns(4)
        with sa1:
            if st.button("Confirm reviewer action", use_container_width=True):
                confirm_reviewer_action("SAE Review","Reviewer confirmed SAE output","SAE output accepted.",active_case["documents"]["sae"]["name"],confidence=active_case["documents"]["sae"]["confidence"]); st.success("Confirmed.")
        with sa2:
            if st.button("Escalate low-confidence", use_container_width=True):
                confirm_reviewer_action("SAE Review","Escalated","Escalated due to source gaps.",active_case["documents"]["sae"]["name"],confidence=active_case["documents"]["sae"]["confidence"],final_status="Escalated"); st.warning("Escalated.")
        with sa3:
            if st.button("Create review packet", use_container_width=True):
                packet = create_sae_packet(); st.success("SAE packet created."); st.text_area("Generated packet", value=packet, height=200)
        with sa4:
            if st.button("→ Version Compare", use_container_width=True): go_to("Version Compare")
        if sae["review_packet"]:
            st.download_button("⬇ SAE Review Packet", sae["review_packet"].encode(),
                               file_name=f"{active_case['case_id']}_sae_packet.txt", mime="text/plain", use_container_width=True)

    def version_compare_screen() -> None:
        case["current_stage"] = "Version Compare"; save_active_case(case)
        amendment = case["documents"]["amendment"]
        compare   = case["compare_review"]
        filt = st.radio("Change filter",["All changes","Eligibility","Endpoint","Consent language"],horizontal=True,
                        index=["All changes","Eligibility","Endpoint","Consent language"].index(st.session_state.compare_filter))
        st.session_state.compare_filter = compare["selected_filter"] = filt; save_active_case(case)
        vc1,vc2 = st.columns(2)
        with vc1: st.text_area("Baseline version",value=amendment["base_text"],height=180,disabled=True)
        with vc2: st.text_area("Updated version",value=amendment["updated_text"],height=180,disabled=True)
        st.markdown("### Change analysis")
        visible = [c for c in amendment["changes"] if filt == "All changes" or c["area"] == filt]
        for c in visible:
            with st.expander(f"{c['area']} | {c['classification']} | {c['impact_level']} impact"):
                st.write(f"**Before:** {c['before']}"); st.write(f"**After:** {c['after']}"); st.write(f"**Regulatory impact:** {c['impact']}")
        vc1a,vc2a,vc3a,vc4a = st.columns(4)
        with vc1a:
            if st.button("Confirm reviewer action ", use_container_width=True):
                confirm_reviewer_action("Version Compare","Reviewer confirmed comparison","Material changes accepted.",amendment["name"],confidence=amendment["confidence"]); st.success("Confirmed.")
        with vc2a:
            if st.button("Escalate substantive change", use_container_width=True):
                confirm_reviewer_action("Version Compare","Escalated","Substantive change escalated.",amendment["name"],confidence=0.91,final_status="Escalated"); st.warning("Escalated.")
        with vc3a:
            if st.button("Create review packet ", use_container_width=True):
                packet = create_compare_packet(); st.success("Comparison packet created."); st.text_area("Generated packet", value=packet, height=220)
        with vc4a:
            if st.button("→ Audit Trail", use_container_width=True): go_to("Audit Trail")
        if compare["review_packet"]:
            st.download_button("⬇ Comparison Packet", compare["review_packet"].encode(),
                               file_name=f"{case['case_id']}_compare_packet.txt", mime="text/plain", use_container_width=True)

    def audit_trail_screen() -> None:
        case["current_stage"] = "Audit Trail"; save_active_case(case)
        df = audit_dataframe(case)
        search = st.text_input("Search audit events")
        if search:
            low = search.lower()
            df  = df[df.astype(str).apply(lambda col: col.str.lower().str.contains(low, na=False)).any(axis=1)]
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp":        st.column_config.TextColumn("Timestamp",        width="medium"),
                "module":           st.column_config.TextColumn("Module",           width="medium"),
                "action":           st.column_config.TextColumn("Action",           width="large"),
                "confidence":       st.column_config.NumberColumn("Confidence",     width="small", format="%.2f"),
                "reviewer_action":  st.column_config.TextColumn("Reviewer Action",  width="medium"),
                "final_status":     st.column_config.TextColumn("Status",           width="small"),
                "source_reference": st.column_config.TextColumn("Source",           width="medium"),
                "note":             st.column_config.TextColumn("Note",             width="large"),
            },
        )
        for evt in case["audit_events"][-5:][::-1]:
            with st.expander(f"{evt['timestamp']} | {evt['module']} | {evt['reviewer_action']}"):
                st.write(f"**Action:** {evt['action']}"); st.write(f"**Confidence:** {evt['confidence']}")
                st.write(f"**Status:** {evt['final_status']}"); st.write(f"**Source:** {evt['source_reference']}"); st.write(f"**Detail:** {evt['note']}")
        with st.container(border=True):
            st.write(f"**Protected view:** {case['protected_view']['escalation_status']}")
            st.write(f"**SAE packet ready:** {'Yes' if case['sae_review']['review_packet'] else 'No'}")
            st.write(f"**Compare packet ready:** {'Yes' if case['compare_review']['review_packet'] else 'No'}")
            st.write(f"**Reviewer confirmations:** {len(case['reviewer_decisions'])}")
        at1,at2,at3 = st.columns(3)
        with at1:
            if st.button("Confirm reviewer action  ", use_container_width=True):
                confirm_reviewer_action("Audit Trail","Reviewer confirmed audit record","Audit record accepted.",case["packet_id"]); st.success("Confirmed.")
        with at2:
            if st.button("Generate audit packet", use_container_width=True):
                pkt = generate_audit_packet(); st.success("Audit packet generated.")
                st.download_button("⬇ Audit Packet (JSON)", to_json_bytes(pkt),
                                   file_name=f"{case['case_id']}_audit_packet.json", mime="application/json", use_container_width=True)
        with at3:
            st.download_button("⬇ Audit Log (CSV)", to_csv_bytes(case["audit_events"]),
                               file_name=f"{case['case_id']}_audit_log.csv", mime="text/csv", use_container_width=True)
        st.info(APP_DISCLAIMER)

    # ── Global action button group — pinned bottom of each reviewer screen ─────
    def _global_action_buttons(module_label: str, doc_name: str, confidence: float = 0.92) -> None:
        """Consistent 4-button action group rendered at the bottom of each reviewer screen."""
        st.markdown("---")
        st.markdown("**Reviewer Actions**")
        ga1, ga2, ga3, ga4 = st.columns(4)
        with ga1:
            if module_label != "Document Intake":
                if st.button("Confirm Reviewer Action", use_container_width=True, key=f"gab_confirm_{module_label}"):
                    confirm_reviewer_action(module_label, f"Reviewer confirmed {module_label}", "Action confirmed.", doc_name, confidence=confidence)
                    st.success("Confirmed.")
            else:
                st.info("Intake categorisation pending.")
        with ga2:
            if st.button("Escalate Low-Confidence", use_container_width=True, key=f"gab_escalate_{module_label}"):
                confirm_reviewer_action(module_label, "Escalated", "Escalated due to low confidence.", doc_name, confidence=confidence, final_status="Escalated")
                st.warning("Escalated.")
        with ga3:
            if st.button("Create Review Packet", use_container_width=True, key=f"gab_packet_{module_label}"):
                if module_label == "SAE Review":
                    pkt = create_sae_packet(); st.success("SAE packet created.")
                elif module_label == "Version Compare":
                    pkt = create_compare_packet(); st.success("Comparison packet created.")
                else:
                    pkt = generate_audit_packet(); st.success("Review packet generated.")
        with ga4:
            if st.button("Open Audit Trail", use_container_width=True, key=f"gab_audit_{module_label}"):
                go_to("Audit Trail")

    # Route map — defined at module level (if True: doesn't create a new scope)
    WORKFLOW_ROUTES = {
        "Command Dashboard": command_dashboard,
        "Document Intake":   lambda: document_intake("workflow"),
        "Protected View":    protected_view_screen,
        "SAE Review":        sae_review_screen,
        "Version Compare":   version_compare_screen,
        "Audit Trail":       audit_trail_screen,
    }

# Render the selected workflow screen inside the Command Dashboard ribbon tab
with t_cmd_dash:
    render_banner("CDSCO Review Workflow", "Full reviewer pipeline: intake → protected view → SAE review → version compare → audit trail.")
    workflow_screen = screen
    if screen in ("Document Intake", "SAE Review", "Audit Trail"):
        # These screens already render in dedicated tabs below; avoid duplicate widget trees.
        workflow_screen = "Command Dashboard"
    WORKFLOW_ROUTES[workflow_screen]()
    if workflow_screen in ("Protected View", "SAE Review", "Version Compare"):
        _doc_ref = case["documents"].get(case.get("selected_document_id", ""), {}).get("name", case["packet_id"])
        _global_action_buttons(workflow_screen, _doc_ref)

# ── New ribbon tabs: Document Intake, SAE Review, Audit Trail ─────────────

with t_doc_intake:
    render_banner("Document Intake", "Select and categorise the incoming case packet document before routing to review.")
    document_intake("tab")

with t_sae_review:

    render_banner("SAE Review", "Review SAE classification output, resolve missing information, and confirm or escalate.")
    _render_sae_review_uploader("workflow_sae_upload_tab")
    case3 = get_active_case()
    sae3 = case3["sae_review"]
    with st.container(border=True):
        sr1,sr2,sr3 = st.columns(3)
        with sr1: st.write(f"**Patient:** {sae3['patient_profile']}"); st.write(f"**Event:** {sae3['event']}")
        with sr2: st.write(f"**Seriousness:** {sae3['seriousness']}"); st.write(f"**Causality:** {sae3['causality']}")
        with sr3: st.write(f"**Action:** {sae3['action_taken']}"); st.write(f"**Outcome:** {sae3['outcome']}")
    st.markdown("**Missing information**")
    for item3 in sae3["missing_info"]:
        item3["resolved"] = st.checkbox(item3["item"], value=item3["resolved"], key=f"srt_mi_{item3['item']}")
    sae3["reviewer_notes"] = st.text_area("Reviewer notes", value=sae3["reviewer_notes"], height=80, key="srt_notes")
    save_active_case(case3)
    st.markdown("---"); st.markdown("**Reviewer Actions**")
    srt1,srt2,srt3,srt4 = st.columns(4)
    with srt1:
        if st.button("Confirm Reviewer Action", use_container_width=True, key="srt_confirm"):
            confirm_reviewer_action("SAE Review","Reviewer confirmed SAE output","SAE output accepted.",case3["documents"]["sae"]["name"],confidence=case3["documents"]["sae"]["confidence"]); st.success("Confirmed.")
    with srt2:
        if st.button("Escalate Low-Confidence", use_container_width=True, key="srt_esc"):
            confirm_reviewer_action("SAE Review","Escalated","Escalated due to source gaps.",case3["documents"]["sae"]["name"],confidence=case3["documents"]["sae"]["confidence"],final_status="Escalated"); st.warning("Escalated.")
    with srt3:
        if st.button("Create Review Packet", use_container_width=True, key="srt_pkt"):
            pkt3 = create_sae_packet(); st.success("SAE packet created."); st.text_area("Generated packet", value=pkt3, height=200, key="srt_pkt_out")
    with srt4:
        if st.button("Open Audit Trail", use_container_width=True, key="srt_audit"): go_to("Audit Trail")

with t_audit_trail:
    render_banner("Audit Trail", "Full audit log of all AI outputs and reviewer decisions for the active case packet.")
    case4 = get_active_case()
    df4 = audit_dataframe(case4)
    search4 = st.text_input("Search audit events", key="at_tab_search")
    if search4:
        low4 = search4.lower()
        df4  = df4[df4.astype(str).apply(lambda col: col.str.lower().str.contains(low4, na=False)).any(axis=1)]
    st.dataframe(
        df4,
        use_container_width=True,
        hide_index=True,
        column_config={
            "timestamp":        st.column_config.TextColumn("Timestamp",       width="medium"),
            "module":           st.column_config.TextColumn("Module",          width="medium"),
            "action":           st.column_config.TextColumn("Action",          width="large"),
            "confidence":       st.column_config.NumberColumn("Confidence",    width="small", format="%.2f"),
            "reviewer_action":  st.column_config.TextColumn("Reviewer Action", width="medium"),
            "final_status":     st.column_config.TextColumn("Status",          width="small"),
            "source_reference": st.column_config.TextColumn("Source",          width="medium"),
            "note":             st.column_config.TextColumn("Note",            width="large"),
        },
    )
    for evt4 in case4["audit_events"][-5:][::-1]:
        with st.expander(f"{evt4['timestamp']} | {evt4['module']} | {evt4['reviewer_action']}"):
            st.write(f"**Action:** {evt4['action']}"); st.write(f"**Confidence:** {evt4['confidence']}")
            st.write(f"**Status:** {evt4['final_status']}"); st.write(f"**Source:** {evt4['source_reference']}"); st.write(f"**Detail:** {evt4['note']}")
    with st.container(border=True):
        st.write(f"**Protected view:** {case4['protected_view']['escalation_status']}")
        st.write(f"**SAE packet ready:** {'Yes' if case4['sae_review']['review_packet'] else 'No'}")
        st.write(f"**Compare packet ready:** {'Yes' if case4['compare_review']['review_packet'] else 'No'}")
        st.write(f"**Reviewer confirmations:** {len(case4['reviewer_decisions'])}")
    st.markdown("---"); st.markdown("**Reviewer Actions**")
    att1,att2,att3,att4 = st.columns(4)
    with att1:
        if st.button("Confirm Reviewer Action", use_container_width=True, key="att_confirm"):
            confirm_reviewer_action("Audit Trail","Reviewer confirmed audit record","Audit record accepted.",case4["packet_id"]); st.success("Confirmed.")
    with att2:
        if st.button("Escalate Low-Confidence", use_container_width=True, key="att_esc"):
            confirm_reviewer_action("Audit Trail","Escalated","Escalated from audit review.",case4["packet_id"],final_status="Escalated"); st.warning("Escalated.")
    with att3:
        if st.button("Create Review Packet", use_container_width=True, key="att_pkt"):
            pkt4 = generate_audit_packet(); st.success("Audit packet generated.")
            st.download_button("⬇ Audit Packet (JSON)", to_json_bytes(pkt4),
                               file_name=f"{case4['case_id']}_audit_packet.json", mime="application/json", use_container_width=True)
    with att4:
        st.download_button("⬇ Audit Log (CSV)", to_csv_bytes(case4["audit_events"]),
                           file_name=f"{case4['case_id']}_audit_log.csv", mime="text/csv", use_container_width=True)
    st.info(APP_DISCLAIMER)


# ── Compliance ribbon ─────────────────────────────────────────────────────────
compliance_ribbon()
