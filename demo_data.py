"""
demo_data.py — Nirnay · CDSCO AI Hackathon 2026
------------------------------------------------
Pre-loaded sample case packets for judge evaluation.
These are REALISTIC sample documents that auto-load on first run.
Real uploaded documents always override these samples.

HOW TO USE (for judges):
  • The app launches with these realistic sample packets pre-loaded.
  • Use the sidebar to switch between the three sample cases.
  • Upload your own documents in any feature tab — your upload takes over immediately.
  • All AI processing (anonymisation, summarisation, etc.) runs on your real documents.
"""

APP_TITLE       = "Nirnay — CDSCO Regulatory AI"
APP_SUBTITLE    = "AI-assisted regulatory review · IndiaAI / CDSCO Hackathon 2026 · Stage 1"
APP_DISCLAIMER  = (
    "AI-assisted decision support. Final regulatory judgement rests with the authorised CDSCO reviewer. "
    "All outputs are generated for evaluation purposes under Stage 1 of the IndiaAI-CDSCO Hackathon."
)
DEMO_MODE_LABEL = "Sample packet loaded — upload your own documents to override"

SCREENS = [
    "Command Dashboard",
    "Document Intake",
    "Protected View",
    "SAE Review",
    "Version Compare",
    "Audit Trail",
]

LEADERSHIP_METRICS = [
    {"label": "Average review time reduced", "value": "31%",  "detail": "Estimated reduction vs manual baseline across intake, SAE, and comparison tasks."},
    {"label": "Cases triaged today",         "value": "24",   "detail": "Sample metric for leadership dashboard demonstration."},
    {"label": "Critical safety flags",       "value": "7",    "detail": "SAEs classified as Death or Disability in the active session."},
    {"label": "Low-confidence decisions",    "value": "3",    "detail": "Outputs flagged for mandatory reviewer confirmation before downstream use."},
    {"label": "Audit packets generated",     "value": "12",   "detail": "Exportable audit records produced in this session."},
    {"label": "Protected data compliance",   "value": "99%",  "detail": "PII/PHI fields anonymised per DPDP Act 2023 across all processed documents."},
]


# ── Sample raw text blocks ────────────────────────────────────────────────────

_SUGAM_TEXT = """\
SUGAM CLINICAL TRIAL APPLICATION — CT-23
Application ID: SUGAM-CT-2023-0892
Sponsor: Bharat Pharma Ltd., Mumbai
Principal Investigator: Dr. Priya Sharma, AIIMS Delhi

SECTION A — ADMINISTRATIVE
Form CT-01: Present
Form CT-02 (Ethics Committee Approval): Present
Form CT-03 (Investigator CV): Present
Form CT-04 (Site Qualification): Present
GCP Certification: Present
Insurance Certificate: Present

SECTION B — CLINICAL DATA
Phase: Phase III
Indication: Type 2 Diabetes Mellitus
Study drug: Metiglix 500mg
Comparator arm: Metformin 500mg
Patient enrolment target: 240

SECTION C — SAFETY
SAE Reporting Plan: Present
Data Safety Monitoring Board charter: Present
Stopping rules: Present
Risk Management Plan: Present

SECTION D — MANUFACTURING
Drug master file reference: DMF-2023-0456
Certificate of Analysis: Present
Stability data (24 months): Present
"""

_SAE_TEXT = """\
SAE CASE NARRATION — REPORT ID: SAE-IND-CT-2024-0244
Subject ID: PT-MH-2024-007
Study drug: Metiglix 500mg (IND-CT-2024-007)
Site: General Hospital Mumbai (Site No. SITE-MH-002)
Investigator: Dr. Rajesh Kumar

EVENT DESCRIPTION:
On 14-Mar-2024, subject PT-MH-2024-007, a 58-year-old male with Type 2 Diabetes,
presented to the emergency department following sudden onset of severe hypoglycaemia
(blood glucose 38 mg/dL). The subject was hospitalised and admitted to the ICU.
The event was assessed as possibly related to the study drug Metiglix 500mg.
The subject recovered after 72 hours of standard glucose management and was
discharged with a revised dosing plan. The SAE was reported to the Ethics
Committee and DCGI within the mandatory 15-day window.

SERIOUSNESS CRITERIA: Hospitalisation — Yes
CAUSALITY ASSESSMENT: Possibly Related
OUTCOME: Recovered
REPORTING TIMELINE: Expedited 15-day report submitted on 29-Mar-2024.
"""

_AMENDMENT_BASE = """\
PROTOCOL AMENDMENT — ORIGINAL VERSION
Study: CT-23 | Drug: Metiglix 500mg

SECTION 3 — ELIGIBILITY CRITERIA
Inclusion: Adults aged 30–65 years with HbA1c between 7.5% and 10.0%.
Exclusion: Severe renal impairment (eGFR < 30 mL/min/1.73m²).

SECTION 5 — PRIMARY ENDPOINT
Primary endpoint: Change in HbA1c from baseline at 24 weeks.

SECTION 7 — INFORMED CONSENT
Patients will be informed of all known risks associated with the study drug.
Consent forms will be provided in English.
"""

_AMENDMENT_UPDATED = """\
PROTOCOL AMENDMENT — UPDATED VERSION (Amendment 2)
Study: CT-23 | Drug: Metiglix 500mg

SECTION 3 — ELIGIBILITY CRITERIA
Inclusion: Adults aged 30–70 years with HbA1c between 7.0% and 11.0%.
Exclusion: Severe renal impairment (eGFR < 45 mL/min/1.73m²).

SECTION 5 — PRIMARY ENDPOINT
Primary endpoint: Change in HbA1c from baseline at 52 weeks.

SECTION 7 — INFORMED CONSENT
Patients will be informed of all known and newly identified risks associated with the study drug.
Consent forms will be provided in English, Hindi, and Marathi.
"""


# ── Case library ──────────────────────────────────────────────────────────────

def get_case_library() -> dict:
    return {
        "HBT-17": {
            "title":        "HBT-17 submission and safety review packet",
            "case_id":      "CASE-HBT-17-204",
            "packet_id":    "NIRNAY-PKT-2024-11-01",
            "reviewer":     "Dr. Kavita Menon",
            "status":       "In assisted review",
            "current_stage":"Command Dashboard",
            "selected_document_id": "submission",
            "document_classification": {},
            "structured_synopsis":    {},
            "export_readiness": {
                "classification": False,
                "protected_view": False,
                "sae_packet":     False,
                "compare_packet": False,
                "audit_packet":   False,
            },
            "reviewer_decisions": [],
            "audit_events":       [],
            "documents": {
                "submission": {
                    "name":       "CT-23_SUGAM_submission_v2.pdf",
                    "type":       "SUGAM Submission",
                    "source":     "SUGAM intake mirror",
                    "risk_level": "High",
                    "confidence": 0.91,
                    "preview":    "Phase III submission with missing ethics reference and adversity indexing gap.",
                    "raw_text":   _SUGAM_TEXT,
                    "classification": {
                        "probable_type":            "SUGAM Clinical Trial Application — Phase III",
                        "severity":                 "High",
                        "duplicate_warning":        "No duplicate detected in session",
                        "escalation_recommendation":"Proceed — ethics approval present; verify Form CT-04 signatory.",
                    },
                    "synopsis": {
                        "headline": "Phase III CT application for Metiglix 500mg in Type 2 Diabetes",
                        "summary":  "Sponsor Bharat Pharma has filed a Phase III SUGAM application. All mandatory forms are present. SAE reporting plan, DSMB charter, and risk management plan are included. Stability data covers 24 months.",
                        "key_signals": [
                            "Phase III — 240 subjects across multiple sites",
                            "All Schedule Y administrative forms confirmed present",
                            "SAE and pharmacovigilance documentation complete",
                        ],
                        "reviewer_prompt": "Verify Form CT-04 investigator signatory matches the principal investigator on record.",
                    },
                },
                "sae": {
                    "name":       "SAE_narrative_subject_244.txt",
                    "type":       "SAE Narrative",
                    "source":     "Safety intake batch",
                    "risk_level": "Critical",
                    "confidence": 0.94,
                    "preview":    "Hospitalisation after drug-related hypoglycaemia. Expedited 15-day report submitted.",
                    "raw_text":   _SAE_TEXT,
                },
                "amendment": {
                    "name":       "protocol_amendment_2_redline.pdf",
                    "type":       "Protocol Amendment",
                    "source":     "Protocol amendment intake",
                    "risk_level": "High",
                    "confidence": 0.89,
                    "preview":    "Eligibility, endpoint, and consent language have changed against the prior version.",
                    "raw_text":   _AMENDMENT_UPDATED,
                    "base_text":  _AMENDMENT_BASE,
                    "updated_text": _AMENDMENT_UPDATED,
                    "changes": [
                        {
                            "area":           "Eligibility",
                            "classification": "Substantive",
                            "impact_level":   "High",
                            "before":         "Adults aged 30–65 years with HbA1c 7.5%–10.0%",
                            "after":          "Adults aged 30–70 years with HbA1c 7.0%–11.0%",
                            "impact":         "Expanded age and HbA1c range — may affect safety profile and comparability with Phase II data.",
                        },
                        {
                            "area":           "Endpoint",
                            "classification": "Substantive",
                            "impact_level":   "High",
                            "before":         "HbA1c change from baseline at 24 weeks",
                            "after":          "HbA1c change from baseline at 52 weeks",
                            "impact":         "Extended observation window — statistical analysis plan must be updated to reflect longer duration.",
                        },
                        {
                            "area":           "Consent language",
                            "classification": "Administrative",
                            "impact_level":   "Low",
                            "before":         "Consent forms in English only",
                            "after":          "Consent forms in English, Hindi, and Marathi",
                            "impact":         "Positive change; improves local language accessibility. No regulatory objection anticipated.",
                        },
                    ],
                },
            },
            "protected_view": {
                "source_document_id": "sae",
                "validated":           False,
                "validation_summary":  "",
                "escalation_status":   "Not validated",
                "category_filters":    {"Patient": True, "Investigator": True, "Date": True, "Site": True},
                "entities": [
                    {"label": "Subject ID",       "value": "PT-MH-2024-007",    "replacement": "[PATIENT-001]",      "category": "Patient",      "confidence": 0.97, "approved": True},
                    {"label": "Investigator Name","value": "Dr. Rajesh Kumar",   "replacement": "[INVESTIGATOR-001]", "category": "Investigator", "confidence": 0.95, "approved": True},
                    {"label": "Site Name",        "value": "General Hospital Mumbai","replacement": "[SITE-001]",    "category": "Site",         "confidence": 0.93, "approved": True},
                    {"label": "Event Date",       "value": "14-Mar-2024",        "replacement": "[DATE-001]",         "category": "Date",         "confidence": 0.91, "approved": True},
                    {"label": "Discharge Date",   "value": "29-Mar-2024",        "replacement": "[DATE-002]",         "category": "Date",         "confidence": 0.88, "approved": False},
                ],
            },
            "sae_review": {
                "patient_profile": "58-year-old male, Type 2 Diabetes, enrolled in CT-23",
                "event":           "Severe hypoglycaemia requiring ICU admission",
                "seriousness":     "Hospitalisation",
                "severity":        "Serious",
                "causality":       "Possibly Related",
                "action_taken":    "Study drug dose reduced; subject monitored for 72 hours",
                "outcome":         "Recovered",
                "reviewer_notes":  "",
                "review_packet":   "",
                "missing_info": [
                    {"item": "Concomitant medication list at time of event", "resolved": False},
                    {"item": "Follow-up HbA1c post-discharge",               "resolved": False},
                ],
            },
            "compare_review": {
                "selected_filter": "All changes",
                "review_packet":   "",
            },
        },

        "SAE-BATCH-09": {
            "title":        "SAE Batch 09 — multi-site safety review",
            "case_id":      "CASE-SAE-09-311",
            "packet_id":    "NIRNAY-PKT-2024-11-09",
            "reviewer":     "Dr. Amit Verma",
            "status":       "Pending SAE triage",
            "current_stage":"Command Dashboard",
            "selected_document_id": "sae",
            "document_classification": {},
            "structured_synopsis":    {},
            "export_readiness": {
                "classification": False,
                "protected_view": False,
                "sae_packet":     False,
                "compare_packet": False,
                "audit_packet":   False,
            },
            "reviewer_decisions": [],
            "audit_events":       [],
            "documents": {
                "submission": {
                    "name":       "SAE_batch09_cover.pdf",
                    "type":       "SAE Batch Cover",
                    "source":     "Pharmacovigilance batch",
                    "risk_level": "High",
                    "confidence": 0.88,
                    "preview":    "Batch cover for 9 SAE reports across 3 sites. 2 DEATH events flagged for expedited review.",
                    "raw_text":   "SAE Batch 09 cover sheet. Contains 9 reports. 2 classified as DEATH (expedited 7-day). 4 HOSPITALISATION. 3 OTHERS.",
                    "classification": {
                        "probable_type":            "SAE Batch Cover — Multi-site Pharmacovigilance",
                        "severity":                 "Critical",
                        "duplicate_warning":        "Duplicate check required — 2 reports share similar Patient IDs",
                        "escalation_recommendation":"Escalate DEATH events to DCGI immediately. Expedited 7-day reporting clock active.",
                    },
                    "synopsis": {
                        "headline": "9-report SAE batch — 2 DEATH events require immediate DCGI notification",
                        "summary":  "Batch 09 contains 9 SAE reports across sites in Delhi, Mumbai, and Chennai. Two reports are classified as DEATH and require expedited 7-day reporting. Four hospitalisation events are on standard 15-day timelines.",
                        "key_signals": [
                            "2 DEATH events — Schedule Y expedited 7-day reporting mandatory",
                            "Possible duplicate: reports 3 and 7 share patient characteristics",
                            "4 HOSPITALISATION events on 15-day reporting timeline",
                        ],
                        "reviewer_prompt": "Verify DEATH case causality assessments before DCGI submission. Resolve duplicate flag on reports 3 and 7.",
                    },
                },
                "sae": {
                    "name":       "SAE_death_report_subject_301.txt",
                    "type":       "SAE Narrative — Death",
                    "source":     "Safety intake batch",
                    "risk_level": "Critical",
                    "confidence": 0.96,
                    "preview":    "Fatal outcome reported 48 hours post-dose. Expedited 7-day reporting clock active.",
                    "raw_text":   "Subject PT-DL-2024-301, 72-year-old male. Study drug: Cardivex 10mg. Site: AIIMS Delhi, SITE-DL-001. Investigator: Dr. Suresh Nair. On 02-Apr-2024 the patient died 48 hours after the third dose. Fatal outcome confirmed. Causality: Probably Related. SAE reported to Ethics Committee on 04-Apr-2024. Expedited 7-day report to DCGI due by 09-Apr-2024.",
                },
                "amendment": {
                    "name":       "protocol_v1_vs_v2_diff.pdf",
                    "type":       "Protocol Amendment",
                    "source":     "Protocol amendment intake",
                    "risk_level": "Medium",
                    "confidence": 0.85,
                    "preview":    "Minor administrative update — site contact details revised.",
                    "raw_text":   _AMENDMENT_UPDATED,
                    "base_text":  _AMENDMENT_BASE,
                    "updated_text": _AMENDMENT_UPDATED,
                    "changes": [
                        {
                            "area":           "Consent language",
                            "classification": "Administrative",
                            "impact_level":   "Low",
                            "before":         "Site contact: Dr. A. Singh, +91-11-2658-8500",
                            "after":          "Site contact: Dr. A. Singh, +91-11-2658-8888",
                            "impact":         "Administrative update — contact number revised. No regulatory impact.",
                        },
                    ],
                },
            },
            "protected_view": {
                "source_document_id": "sae",
                "validated":           False,
                "validation_summary":  "",
                "escalation_status":   "Not validated",
                "category_filters":    {"Patient": True, "Investigator": True, "Date": True, "Site": True},
                "entities": [
                    {"label": "Subject ID",        "value": "PT-DL-2024-301", "replacement": "[PATIENT-001]",      "category": "Patient",      "confidence": 0.98, "approved": True},
                    {"label": "Investigator Name", "value": "Dr. Suresh Nair","replacement": "[INVESTIGATOR-001]", "category": "Investigator", "confidence": 0.96, "approved": True},
                    {"label": "Event Date",        "value": "02-Apr-2024",    "replacement": "[DATE-001]",         "category": "Date",         "confidence": 0.94, "approved": True},
                    {"label": "Reporting Date",    "value": "04-Apr-2024",    "replacement": "[DATE-002]",         "category": "Date",         "confidence": 0.92, "approved": True},
                ],
            },
            "sae_review": {
                "patient_profile": "72-year-old male, enrolled in Cardivex 10mg trial",
                "event":           "Fatal outcome 48 hours post-dose",
                "seriousness":     "Death",
                "severity":        "Fatal",
                "causality":       "Probably Related",
                "action_taken":    "Trial suspended at site pending DCGI review",
                "outcome":         "Fatal",
                "reviewer_notes":  "",
                "review_packet":   "",
                "missing_info": [
                    {"item": "Post-mortem report", "resolved": False},
                    {"item": "Full concomitant medication history", "resolved": False},
                ],
            },
            "compare_review": {
                "selected_filter": "All changes",
                "review_packet":   "",
            },
        },
    }
