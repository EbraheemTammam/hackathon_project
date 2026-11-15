# 🔥 Flame Behavior in Space  
### ISS Combustion Science Hub

An interactive **Streamlit** web application that explores microgravity combustion science, spacecraft fire safety experiments, historical spaceflight fire incidents, and NASA technology spinoffs that improve firefighting on Earth.

The app combines curated scientific knowledge (experiments, stories, applications, and a Researcher’s Guide summary) with optional Excel/PDF uploads and a **strictly grounded AI assistant** that answers only from the provided NASA datasets.

---

## ✨ Features

| Section | Description |
|---------|-------------|
| **Overview** | High-level introduction to why flames behave differently in microgravity, key metrics (9 investigations, 391 cleaned tests, 3 stories, 3 applications). |
| **Ask Me (AI Assistant)** | Grounded Q&A chatbot. Answers only from the loaded knowledge base. Supports English and Arabic queries (Arabic is normalized and mapped to English domain terms). Falls back gracefully if external LLMs fail. |
| **Help (Experiments)** | Browse all **9 PSI investigations** in fixed order as expandable cards. Each card shows objective, execution method, results, scientific conclusion, safety tip, and (when available) the raw Excel table. |
| **What about story** | Three historical spacecraft fire incidents: Apollo 1, Apollo 13, and the 1997 Mir fire. |
| **NASA Applications** | Three terrestrial spinoffs: Firefighters’ Air Tanks, Brunswick Incipient Fire Detector, and Project FIRES. |
| **Admin Settings** | Password-protected panel to configure AI providers/API keys, verify Cosmo keys, and upload additional `.xlsx` / `.pdf` files that are automatically indexed. |

### AI Engine Behavior
1. **Cosmo AI** (primary) — realtime agent with system instructions that enforce strict grounding.
2. Optional backup providers: **Gemini**, **Groq**, or **OpenAI**.
3. **Built-in Local Grounded Knowledge Engine** — keyword + domain-phrase retrieval + exact Excel row matching. Always available as a seamless fallback.
4. Out-of-scope questions receive a clear “Insufficient information…” response (no hallucination).

---

## 🧪 Included Knowledge Base

### 9 PSI Investigations (exact order)
| Code | Name | Category | Tests | Avg O₂ |
|------|------|----------|-------|--------|
| PSI-99 | SAFFIRE-II | Prevention & Flammability | 13 | 22.01% |
| PSI-98 | SAFFIRE-I | Prevention & Flammability | 2 | 21.55% |
| PSI-100 | SAFFIRE-III | Prevention & Flammability | 2 | 21.50% |
| PSI-102 | SAME (Smoke & Aerosol) | Fire Detection & Smoke | 8 | 21.00% |
| PSI-25 | BASS-II | Prevention & Flammability | 129 | 18.57% |
| PSI-106 | SLICE | Combustion Fundamentals | 12 | 21.00% |
| PSI-159 | ACME CFI-G (Cool Flames) | Suppression & Cool Flames | 179 | 32.18% |
| PSI-142 | Counterflow Cool Flame Transitions | Suppression & Cool Flames | 8 | N/A |
| PSI-108 | STDCE-1 | Fluid Physics / Convection | 38 | N/A |

**Total cleaned tests: 391**

### Stories
- Apollo 13 (April 1970 oxygen-tank explosion & survival)
- Apollo 1 Accident (January 1967 pure-oxygen cabin flash fire)
- Fire Aboard the Mir Space Station (February 1997 solid-fuel oxygen generator fire)

### NASA Applications / Spinoffs
- Firefighters’ Air Tanks (Lightweight Composite Breathing System, 1976)
- Brunswick Incipient Fire Detector (1970s)
- Project FIRES (Firefighters’ Integrated Response Equipment System)

### Core Document Chunks
Summaries extracted from *A Researcher’s Guide to: International Space Station Combustion Science* (NP-2015-10-034-JSC) covering microgravity advantages, historical misconceptions, FLEX/cool flames, gaseous diffusion flames, facilities (CIR, MSG, ACME, SoFIE), etc.

---

## 🛠️ Tech Stack

- **Frontend / App**: [Streamlit](https://streamlit.io/)
- **Data handling**: pandas
- **PDF extraction**: pypdf (optional — gracefully degrades if missing)
- **AI providers**:
  - Cosmo AI (`cosmo_ai` RealtimeClient)
  - Google Gemini
  - Groq / OpenAI (OpenAI-compatible endpoint)
- **Local retrieval**: custom keyword-overlap + Arabic-normalized domain mapping + exact Excel row matcher
- **Persistence**: JSON config file (`.admin_config.json`) + uploaded files in `uploaded_kb/`

---

## 📁 Project Structure

```text
.
├── app.py                    # Main Streamlit application (or streamlit_app.py)
├── knowledge_base.py         # Experiments, stories, applications, retrieval & local answer engine
├── requirements.txt          # Python dependencies
├── .admin_config.json        # Auto-created admin settings (API keys, provider)
├── uploaded_kb/              # Directory for admin-uploaded .xlsx / .pdf files
├── *.xlsx                    # Optional local Excel workbooks (auto-discovered)
├── *.pdf                     # Optional local PDFs (auto-discovered)
└── README.md