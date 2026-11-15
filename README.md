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
```

> Place any additional Excel or PDF files in the project root or in `uploaded_kb/`. They are discovered automatically on startup (and after admin upload).

---

## ⚙️ Installation & Setup

### 1. Clone / copy the project
```bash
# If using git
git clone <repository-url>
cd flame-behavior-in-space
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

**Minimal `requirements.txt` example:**
```text
streamlit>=1.28.0
pandas>=2.0.0
pypdf>=3.0.0
# Optional AI SDKs (install only what you need)
cosmo-ai          # for Cosmo Realtime
# google-generativeai or just use the REST helper already in the app
# openai          # only if you prefer the official SDK (app uses urllib)
```

### 4. Environment variables (optional but recommended)

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_PASSWORD` | Password that unlocks the Admin Settings panel | `Password@123` |
| `COSMO_API_KEY` | Cosmo AI API key (overrides the default/hard-coded fallback) | — |

You can also set the Cosmo key via Streamlit secrets (`st.secrets["COSMO_API_KEY"]`) or through the Admin panel at runtime.

```bash
# Example
export ADMIN_PASSWORD="YourSecurePassword"
export COSMO_API_KEY="cosmo_xxxxxxxxxxxxxxxx"
```

### 5. Run the app
```bash
streamlit run app.py
```
(or `streamlit run streamlit_app.py` depending on the filename you chose)

The app will open in your browser (usually `http://localhost:8501`).

---

## 🔐 Admin Panel

1. In the sidebar expand **🔒 Admin Access**.
2. Enter the admin password (default: `Password@123` or the value of `ADMIN_PASSWORD`).
3. Once unlocked you can:
   - Choose the active AI provider (Cosmo / Gemini / Groq / OpenAI / Local-only).
   - Paste and **verify** a Cosmo API key.
   - Supply an optional backup API key + model name.
   - Upload additional `.xlsx` or `.pdf` files — they are saved under `uploaded_kb/` and the knowledge base is re-indexed automatically.
4. Click **💾 Save AI Settings**.
5. Use **🔒 Lock Admin Panel** when finished.

Public visitors never see the Admin Settings navigation item until the session is unlocked.

---

## 💬 Using the “Ask Me” Assistant

- Type questions in **English** or **Arabic**. Arabic is normalized (Alef, Teh Marbuta, digits, diacritics) and mapped to English domain terms (SAFFIRE, cool flame, oxygen %, burn time, etc.).
- The system first tries exact Excel sample/test ID matching (e.g. `S1`, `S2`, `B14`, `CF1`).
- Then it falls back to high-signal keyword retrieval over the curated chunks.
- Answers are intentionally concise (1–3 sentences) and only contain information present in the knowledge base.
- Expand **🔍 Sources Consulted** under any answer to see which chunks were used.

**Example questions**
- “Compare the burn time in SAFFIRE-I (PSI-98) between S1 and S2.”
- “What did PSI-159 (ACME CFI-G) discover about cool flames and what safety tip does it give?”
- “What caused the oxygen tank explosion on Apollo 13?”
- “How many tests were cleaned for BASS-II?”
- “نسبه الاكسجين في سافاير 2” (Arabic → oxygen percentage for SAFFIRE-II)

---

## 🧠 Local Retrieval Highlights (`knowledge_base.py`)

- **Arabic support**: `_normalize_arabic`, phrase map, and word map convert common Arabic queries into English retrieval terms.
- **Exact row lookup**: Recognizes sample/test IDs (`S1`, `B14`, `CF1`, `2-5`, etc.) and returns only the requested attributes (burn time, O₂, flow direction, material, …).
- **Scoring**: High weight for PSI codes, experiment names, and domain terms; low weight for generic words (“experiment”, “test”, “fire”…).
- **Strict grounding**: The local answer engine and the LLM system prompt both refuse to invent numbers or use outside knowledge.

---

## 🚀 Deployment Notes

- **Streamlit Cloud / Hugging Face Spaces / similar**  
  - Add `ADMIN_PASSWORD` and `COSMO_API_KEY` (or other keys) as secrets.  
  - Make sure `uploaded_kb/` is writable or pre-populate the knowledge base.  
  - The app creates `.admin_config.json` at runtime; persist it if you want settings to survive restarts.

- **Docker** (example skeleton)
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 8501
  CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
  ```

---

## ⚠️ Important Safety & Scope Notes

- This application is an **educational and research exploration tool**. It is **not** a substitute for official NASA safety documentation, flight rules, or certified fire-protection engineering.
- All numerical values (burn times, oxygen concentrations, test counts, etc.) come from the curated Excel summaries and Researcher’s Guide excerpts included in the repository. Always cross-check critical figures against the original NASA reports when needed.
- The AI assistant is deliberately constrained: if the knowledge base does not contain the answer, it will say so.

---

## 📄 License & Attribution

- Scientific content is derived from publicly available NASA materials, including:
  - *A Researcher’s Guide to: International Space Station Combustion Science* (NP-2015-10-034-JSC)
  - Publicly reported results of the SAFFIRE, BASS-II, SAME, SLICE, ACME, STDCE and related investigations
  - Historical accounts of Apollo 1, Apollo 13, and the 1997 Mir fire
- Please attribute NASA and the original principal investigators when reusing scientific statements.
- Application code is provided as-is for educational purposes. Add an explicit license (MIT, Apache-2.0, etc.) according to your project policy.

---

## 🤝 Contributing / Extending

1. Add new experiments to the `EXPERIMENTS` list in `knowledge_base.py` (keep the same dict schema).
2. Drop additional `.xlsx` or `.pdf` files into the project root or `uploaded_kb/`.
3. Extend the Arabic phrase/word maps if you need broader Arabic coverage.
4. Improve the local scorer or add vector embeddings if you want higher-quality retrieval for very large corpora.

---

## 📬 Support

For issues related to the Streamlit UI, retrieval quality, or admin configuration, open an issue in the repository or contact the project maintainer.

**Enjoy exploring how flames behave when gravity is removed.** 🔥🚀
