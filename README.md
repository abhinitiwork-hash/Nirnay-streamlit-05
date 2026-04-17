Nirnay — AI-Driven Regulatory Workflow Automation for CDSCO
CDSCO-IndiaAI Health Innovation Acceleration Hackathon · Stage 1 Submission
**🚀 Live Demo: https://nirnay-app.streamlit.app/**

🏛️ What Is Nirnay?
Nirnay (निर्णय — Hindi for decision) is a comprehensive, reviewer-centric AI platform that automates and accelerates the CDSCO regulatory review lifecycle — from document intake to inspection-ready audit packets — while keeping the human reviewer firmly in control at every decision gate.

Built for the CDSCO-IndiaAI Hackathon 2026, Nirnay directly addresses all six mandated features of the problem statement (Section 3.I), with special depth on the first four priority features: Anonymisation, Summarisation, Completeness Assessment, and Categorisation.

🎯 Problem Being Solved
CDSCO processes thousands of submissions annually — new drug applications, clinical trial approvals, SAE reports, and protocol amendments. The current process is manual, document-intensive, and prone to delays that slow life-saving drug approvals. Nirnay replaces repetitive reviewer burden with structured AI assistance, cutting assessment time while maintaining regulatory integrity and full auditability.

✅ Features Implemented (All 6 Mandated, Section 3.I)
#	Feature	Status	Description
01	Anonymisation	✅ Full	Two-step DPDP Act 2023 process — pseudonymisation + irreversible generalisation. PII/PHI detection via hybrid NLP + regex. Compliance audit log generated per document.
02	Summarisation	✅ Full	Three modes: SAE Case Narration, SUGAM Application Checklist, Meeting Transcript/Audio. AI-enhanced via Claude + rule-based structured fallback.
03	Completeness Assessment	✅ Full	Validates mandatory NDCT Rules 2019 / Form CT fields. RAG (Red-Amber-Green) status per field. Approve / Return / Reject recommendation with source evidence.
04	Categorisation & Classification	✅ Full	SAE severity grading (DEATH / DISABILITY / HOSPITALISATION / OTHERS). ICD-10 mapping. Session-based duplicate detection. Priority queue assignment.
05	Document Comparison	✅ Full	Semantic diff between two document versions. Substantive vs administrative change classification. Colour-coded table with downloadable CSV report.
06	Inspection Report Generation	✅ Full	Converts raw site observations into CDSCO-formatted inspection reports. Critical / Major / Minor finding classification. CAPA timelines per NDCT Rules 2019.
🧠 AI Architecture & Methodology
Anonymisation Engine
Hybrid approach: Regular expression rules for structured PII (dates, IDs, phone numbers) combined with NLP-based Named Entity Recognition for contextual PHI (patient names, investigator names, institution names).
Two-step pipeline:
Step 1 — Pseudonymisation: Each detected entity is replaced with a secure, reversible token (e.g., [PATIENT-001]). A token registry (JSON) maps tokens to original values — encrypted at rest in production.
Step 2 — Irreversible Generalisation: Tokens are further abstracted (age bands, date ranges, anonymised site codes), making the document safe for external review circulation.
Compliance: Outputs are tagged against DPDP Act 2023, NDHM Health Data Management Policy, and ICMR Ethical Guidelines.
Low-confidence escalation: Ambiguous entities are surfaced in an approval queue for reviewer confirmation rather than auto-suppressed.
Summarisation Engine
SAE Narration: Extracts seriousness criteria, causality assessment, outcome, and reporting timeline. Outputs priority (URGENT / STANDARD / LOW) with applicable regulatory deadlines under NDCT Rules 2019.
SUGAM Checklist: Field-by-field completeness scoring with actionable gaps listed for reviewer follow-up.
Meeting Transcripts: Extracts key decisions, action items, and next steps from long transcripts or pasted audio transcriptions.
AI Enhancement: Where the Claude API is available, outputs are enriched with an abstractive summary layer before the rule-based structured analysis.
Completeness Assessment
Deterministic field mapping against 20 mandatory fields derived from NDCT Rules 2019 and Form CT requirements.
Each field assigned a RAG status with a human-readable note and source reference.
Reviewer-facing recommendation (Approve / Return / Reject) derived from field coverage and critical gap count.
Classification & Duplicate Detection
Severity grading uses keyword-weighted logic mapped to CDSCO's four severity categories, with ICD-10 code assignment.
Session-based duplicate detection cross-references Patient IDs and drug names across all documents uploaded in a browser session — DPDP compliant (no external storage, cleared on session end).
Priority queue assigns 1–4 routing priority based on severity and causality signals.
Document Comparison
Text segmented into logical units (sentences, clauses). Units compared semantically rather than character-by-character.
Changes labelled ADDED / REMOVED / CHANGED, then classified as Substantive (affecting dosage, endpoints, safety, patient eligibility, consent language) or Administrative (formatting, language localisation).
Outputs a colour-coded table with downloadable CSV and impact annotations.
🔄 Full Reviewer Workflow
Nirnay implements a complete end-to-end review pipeline accessible from the Command Dashboard:

Document Intake → Protected View (Anonymisation) → SAE Review → Version Compare → Audit Trail
Each stage is a reviewer decision gate — AI outputs are recommendations, not final decisions. Reviewers can: - Confirm the AI recommendation - Escalate low-confidence outputs - Create a review packet for downstream use - Proceed to the next workflow stage

🔒 Responsible AI & Data Governance
Reviewer-in-control design: No AI output auto-advances the workflow without explicit reviewer confirmation.
Source-linked outputs: Every summary, completeness flag, and classification can be traced to the source document text.
Low-confidence escalation events are retained in the audit trail — not silently discarded.
DPDP Act 2023 compliant: Session-scoped storage only; no patient data persisted externally.
Audit-ready logging: All reviewer actions, AI outputs, confidence scores, timestamps, and source references are retained in a structured, exportable audit trail.
🗂️ Project Structure
nirnay/
├── app.py              # Main entry point — all 6 features + reviewer workflow
├── engine.py           # All processing engines (anonymisation, summarisation, etc.)
├── components.py       # UI components, session state, audit trail, sidebar
├── demo_data.py        # Pre-loaded sample case packets (HBT-17, DRUG-2024-0044)
└── requirements.txt    # Python dependencies
🚀 How to Run
Prerequisites
Python 3.10+
Streamlit
See requirements.txt for full dependency list
Installation
git clone https://github.com/<your-repo>/nirnay
cd nirnay
pip install -r requirements.txt
Running the App
streamlit run app.py
For Judges / Evaluators
The app opens on the Command Dashboard with a pre-loaded sample case packet (HBT-17).
Use the left sidebar to switch between the two sample cases or navigate workflow screens.
Use the tabs at the top to access all 6 AI feature modules.
Upload your own documents inside any feature tab — AI engines process real files immediately; sample data is only a fallback.
All outputs (PDF, CSV, JSON, TXT) are downloadable from within each tab.
Login Credentials (Demo)
Field	Value
Username	admin
Password	nirnay2026
📊 Sample Outputs
Anonymisation
Input: Raw SAE narrative with patient name, investigator, site, and dates.
Step 1 Output: Pseudonymised document with token registry JSON.
Step 2 Output: Irreversibly generalised document safe for external circulation.
Audit Log: Entity-level CSV with type, action, replacement, and timestamp.
Completeness Assessment
Input: SUGAM clinical trial application text.
Output: RAG table across 20 fields, completeness score (%), reviewer recommendation, and downloadable CSV report.
SAE Classification
Input: SAE report narrative.
Output: Severity label (e.g., HOSPITALISATION), ICD-10 code, confidence score, reporting timeline, and priority queue position (1–4).
Document Comparison
Input: Baseline protocol + amended protocol.
Output: Change log with ADDED / REMOVED / CHANGED labels, Substantive vs Administrative classification, downloadable CSV.
📏 Technical Robustness Metrics
Task	Metric	Approach
Anonymisation	k-anonymity, l-diversity	Two-step pipeline with token registry and generalisation
Summarisation	ROUGE-1, ROUGE-2, ROUGE-L	Evaluated against CNN/DailyMail equivalent; Claude-enhanced abstractive layer
Classification	Macro-F1, MCC	Confusion matrix available per severity class
Completeness	Field-level precision/recall	Deterministic against 20-field NDCT Rules 2019 schema
Comparison	Semantic similarity + change F1	Substantive/administrative split validated on protocol amendment samples
Latency	<3 seconds per document	Rule-based engines; Claude API adds 2–5s for AI-enhanced outputs
🛠️ Technology Stack
Layer	Technology
Frontend / App	Streamlit (Python)
AI/LLM	Anthropic Claude (Haiku) via API
PII Detection	Hybrid regex + NLP (spaCy-compatible)
Document Processing	python-docx, pdfplumber, openpyxl, Pillow
Data	Pandas, session-scoped state (no external DB)
Export	CSV, JSON, TXT downloads
🔮 Future Roadmap (Stage 2 / Production)
SUGAM & MD Online portal integration — Direct API hooks for live submission ingestion.
Whisper API integration — Real-time audio transcription for meeting summarisation.
Fine-tuned NER models — Domain-specific models trained on CDSCO-provided anonymised datasets.
Formal k-anonymity certification — Statistical privacy guarantees per benchmark.
Role-based access control — Multi-reviewer workflows with reviewer assignment queues.
Cloud deployment — Containerised deployment on MeitY-approved cloud infrastructure (AWS GovCloud / NIC).
SUGAM feedback loop — Completeness flags fed back into the SUGAM portal UI for applicants.
⚖️ Compliance & Ethics
Compliant with DPDP Act 2023, NDHM Health Data Management Policy, ICMR Ethical Guidelines, and CDSCO standards.
Adheres to Responsible AI Principles: Safety, Reliability, Transparency, Accountability, Non-discrimination, Privacy.
Follows Government of India Cybersecurity guidelines for data handling and session management.
All source code is original. Pre-trained models (Claude API) are properly attributed.
No patient data is stored externally or transmitted beyond the active browser session.
👥 Team
Role	Responsibility
Team Leader	Architecture, AI pipeline, submission lead
Backend Engineer	Engine development, API integration
Frontend Engineer	Streamlit UI, UX, reviewer workflow
📄 Submission Checklist
[x] Source code on GitHub (private repository with indiaaihackathon25 added as collaborator)
[x] All 6 mandated features implemented
[x] Project report (PDF) with methodology, sample outputs, and evaluation
[x] Model card with security, privacy, and architecture details
[x] Demo video (2–3 minutes)
[x] README with setup instructions and feature documentation
[x] Certificate of Incorporation / Registration
Nirnay — Calm, source-linked CDSCO review from intake to audit packet.
