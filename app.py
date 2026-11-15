import asyncio
import concurrent.futures
import json
import os
import urllib.error
import urllib.request
from typing import Dict, List, Tuple,Optional

import streamlit as st

from knowledge_base import (
    EXPERIMENTS,
    NASA_APPLICATIONS,
    STORIES,
    answer_from_knowledge_base_local,
    build_base_knowledge_chunks,
    discover_local_files,
    extract_excel_chunks,
    extract_pdf_chunks,
    retrieve_relevant_context,
)

# ==============================================================================
# CONFIGURATION & ADMIN PERSISTENCE
# ==============================================================================
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Password@123") 
CONFIG_FILE = ".admin_config.json"
UPLOAD_DIR = "uploaded_kb"

st.set_page_config(
    page_title="Flame Behavior in Space | ISS Combustion Science Hub",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _get_default_cosmo_key() -> str:
    env_key = os.environ.get("COSMO_API_KEY")
    if env_key:
        return env_key.strip()
    try:
        return str(st.secrets["COSMO_API_KEY"]).strip()
    except Exception:
        return "cosmo_ABReRRCtqsFlyVBrKsl4Nawv7EGTefIXob9v9lcHar4"


def load_admin_config() -> Dict[str, str]:
    default_cfg = {
        "provider": "Cosmo AI (with Local Grounded Fallback)",
        "cosmo_api_key": _get_default_cosmo_key(),
        "backup_api_key": "",
        "backup_model": "",
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_cfg.update({k: v for k, v in saved.items() if v is not None})
        except Exception:
            pass
    return default_cfg


def save_admin_config(cfg: Dict[str, str]) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


# ==============================================================================
# SPACE-FLAME THEME STYLING
# ==============================================================================
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #161b33 0%, #0b0e1a 55%, #06070f 100%);
        color: #eef2ff;
    }
    section[data-testid="stSidebar"] {
        background-color: #0d1122;
        border-right: 1px solid rgba(255, 138, 61, 0.25);
    }
    .hero-banner {
        background: linear-gradient(135deg, rgba(255, 107, 43, 0.16), rgba(56, 189, 248, 0.12));
        border: 1px solid rgba(255, 138, 61, 0.35);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff8a3d, #ffd166, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .hero-sub {
        color: #cbd5e1;
        font-size: 1rem;
    }
    .exp-card {
        background: rgba(19, 25, 48, 0.85);
        border: 1px solid rgba(96, 165, 250, 0.28);
        border-left: 5px solid #ff7b29;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .exp-card:hover {
        border-color: #ff9f43;
        transform: translateY(-1px);
    }
    .exp-code {
        display: inline-block;
        background: rgba(255, 123, 41, 0.2);
        color: #ffb076;
        border: 1px solid rgba(255, 123, 41, 0.45);
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .exp-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f8fafc;
    }
    .exp-meta {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    .detail-box {
        background: rgba(15, 23, 42, 0.92);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 14px;
        padding: 1.4rem;
        margin-top: 0.5rem;
        margin-bottom: 1.25rem;
    }
    .story-card, .app-card {
        background: rgba(19, 25, 48, 0.88);
        border: 1px solid rgba(255, 138, 61, 0.32);
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
    }
    .safety-box {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 10px;
        padding: 0.9rem 1rem;
        margin-top: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# AI ENGINE HELPERS (COSMO AI + OPTIONAL BACKUP + LOCAL GROUNDED FALLBACK)
# ==============================================================================
def _run_async(coro):
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    if running_loop and running_loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def verify_cosmo_key(api_key: str) -> Tuple[bool, str]:
    """Verifies a Cosmo API key against Cosmo's official credential endpoint."""
    key = (api_key or "").strip()
    if not key:
        return False, "API key is empty."
    req = urllib.request.Request(
        "https://platform.askcosmo.ai/api/v1/external/realtime/verify",
        headers={"Authorization": f"Bearer {key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return True, f"HTTP {resp.status}: {body}"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        return False, f"HTTP {e.code}: {err_body}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


async def _query_cosmo_async(api_key: str, instructions: str, user_prompt: str) -> str:
    from cosmo_ai import (
        RealtimeClient,
        ReadyEvent,
        SessionEndedEvent,
        TranscriptDeltaEvent,
        TranscriptRole,
    )

    client = RealtimeClient(api_key=api_key.strip())
    agent = client.agent(instructions=instructions, voice="Puck")

    collected_parts: List[str] = []
    final_reply = ""

    async with agent.start() as session:
        await session.send_text(user_prompt)

        async for event in session:
            if isinstance(event, ReadyEvent):
                continue
            elif isinstance(event, TranscriptDeltaEvent):
                role_val = getattr(event.role, "value", str(event.role)).lower()
                is_agent = (
                    event.role is getattr(TranscriptRole, "AGENT", None)
                    or "agent" in role_val
                    or "assistant" in role_val
                    or "model" in role_val
                )
                if is_agent and event.text:
                    if event.is_final:
                        final_reply = event.text.strip()
                        break
                    else:
                        collected_parts.append(event.text)
            elif isinstance(event, SessionEndedEvent):
                break

    return final_reply or "".join(collected_parts).strip()


def _query_openai_compatible(
    endpoint: str, api_key: str, model: str, system_prompt: str, user_prompt: str
) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip()}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()


def _query_gemini(api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key.strip()}"
    payload = json.dumps(
        {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.1},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def generate_grounded_answer(
    cfg: Dict[str, str],
    question: str,
    relevant_chunks: List[Dict[str, str]],
    excel_sheets=None,
) -> Tuple[str, str]:
    """
    Returns (answer_text, engine_note).
    Strictly rejects out-of-scope questions before or during LLM generation.
    Falls back gracefully to the Built-in Grounded Engine if external API fails.
    """
    if not relevant_chunks:
        return (
            "Insufficient information: The provided NASA combustion datasets, Researcher's Guide, "
            "and curated documents do not contain enough information to answer this question.",
            "Grounded Scope Check",
        )

    context_text = "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in relevant_chunks
    )

    system_instructions = (
        "You are an expert NASA Microgravity Combustion Science Assistant for the "
        "'Flame Behavior in Space' platform. Always reply ONLY in English.\n\n"
        "STRICT GROUNDING RULES:\n"
        "1. Answer ONLY using facts from the PROVIDED KNOWLEDGE CONTEXT below "
        "(NASA ISS Combustion Science Researcher's Guide PDF, 9 PSI Excel datasets, "
        "3 spacefire stories, and 3 NASA applications).\n"
        "2. Do NOT use outside knowledge and do NOT guess or invent numbers.\n"
        "3. If the context does not contain enough information to answer the user's question, reply ONLY:\n"
        "'Insufficient information: The provided NASA combustion datasets, Researcher\\'s Guide, "
        "and curated documents do not contain enough information to answer this question.'\n"
        "4. Be strictly concise: answer ONLY what was specifically asked in 1 to 3 direct sentences. "
        "Do NOT add extra background details, unrequested fields, or outside information."
    )

    grounded_prompt = (
        f"PROVIDED KNOWLEDGE CONTEXT:\n{context_text}\n\n"
        f"USER QUESTION:\n{question}\n\n"
        "Answer in English strictly based on the context above:"
    )

    provider = cfg.get("provider", "Cosmo AI (with Local Grounded Fallback)")

    # 1. Try Cosmo AI
    if "Cosmo AI" in provider and cfg.get("cosmo_api_key", "").strip():
        try:
            ans = _run_async(
                asyncio.wait_for(
                    _query_cosmo_async(
                        cfg["cosmo_api_key"], system_instructions, grounded_prompt
                    ),
                    timeout=35.0,
                )
            )
            if ans:
                return ans, "Cosmo AI"
        except Exception as exc:
            # Silently fall back for public visitors; log note for Admin diagnostics
            st.session_state.last_api_error = f"Cosmo AI error: {type(exc).__name__}: {exc}"

    # 2. Try Optional Backup Provider (Gemini / OpenAI / Groq)
    b_key = cfg.get("backup_api_key", "").strip()
    if b_key:
        try:
            if "Gemini" in provider:
                model = cfg.get("backup_model") or "gemini-2.0-flash"
                return _query_gemini(b_key, model, system_instructions, grounded_prompt), "Gemini"
            elif "Groq" in provider:
                model = cfg.get("backup_model") or "llama-3.3-70b-versatile"
                return (
                    _query_openai_compatible(
                        "https://api.groq.com/openai/v1/chat/completions",
                        b_key,
                        model,
                        system_instructions,
                        grounded_prompt,
                    ),
                    "Groq",
                )
            elif "OpenAI" in provider:
                model = cfg.get("backup_model") or "gpt-4o-mini"
                return (
                    _query_openai_compatible(
                        "https://api.openai.com/v1/chat/completions",
                        b_key,
                        model,
                        system_instructions,
                        grounded_prompt,
                    ),
                    "OpenAI",
                )
        except Exception as exc:
            st.session_state.last_api_error = f"Backup API error: {type(exc).__name__}: {exc}"

    # 3. Seamless Local Grounded Knowledge Engine Fallback
    local_ans = answer_from_knowledge_base_local(
        question, relevant_chunks, excel_sheets=excel_sheets
    )
    return local_ans, "Built-in NASA Knowledge Engine"


# ==============================================================================
# CACHED KNOWLEDGE BASE LOADER
# ==============================================================================
@st.cache_resource(show_spinner="Loading NASA Combustion Science Knowledge Base...")
def load_knowledge_base():
    local_excels, local_pdfs = discover_local_files(".")
    base_chunks = build_base_knowledge_chunks()
    excel_chunks, excel_sheets = extract_excel_chunks(local_excels)
    pdf_chunks = extract_pdf_chunks(local_pdfs)
    all_chunks = base_chunks + excel_chunks + pdf_chunks
    return all_chunks, excel_sheets, len(local_excels), len(local_pdfs)


# ==============================================================================
# SESSION STATE & SIDEBAR (CLEAN PUBLIC UI + LOCKED ADMIN ACCESS)
# ==============================================================================
if "active_section" not in st.session_state:
    st.session_state.active_section = "Help"
if "selected_experiment" not in st.session_state:
    st.session_state.selected_experiment = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "admin_unlocked" not in st.session_state:
    st.session_state.admin_unlocked = False
if "last_api_error" not in st.session_state:
    st.session_state.last_api_error = ""

admin_cfg = load_admin_config()
all_chunks, excel_sheets, n_excels, n_pdfs = load_knowledge_base()

with st.sidebar:
    st.markdown("## 🔥 Flame Behavior in Space")
    st.caption("Microgravity Combustion & Spacecraft Fire Safety Explorer")

    nav_options = [
        "🏠 Overview",
        "🤖 Ask Me",
        "🧪 Help",
        "📖 What about story",
        "🚀 NASA Applications",
    ]
    if st.session_state.admin_unlocked:
        nav_options.append("⚙️ Admin Settings")

    current_idx = 2
    for idx, label in enumerate(nav_options):
        if st.session_state.active_section in label:
            current_idx = idx
            break

    selected_nav = st.radio("Navigation", nav_options, index=current_idx)

    if "Overview" in selected_nav:
        st.session_state.active_section = "Overview"
    elif "Ask Me" in selected_nav:
        st.session_state.active_section = "Ask Me"
    elif "Help" in selected_nav:
        st.session_state.active_section = "Help"
    elif "What about story" in selected_nav:
        st.session_state.active_section = "What about story"
    elif "NASA Applications" in selected_nav:
        st.session_state.active_section = "NASA Applications"
    elif "Admin Settings" in selected_nav:
        st.session_state.active_section = "Admin Settings"

    st.divider()

    # Discrete Password-Protected Admin Access (hidden from normal visitors)
    if not st.session_state.admin_unlocked:
        with st.expander("🔒 Admin Access"):
            pwd_input = st.text_input("Admin Password", type="password", key="admin_pwd_box")
            if st.button("Unlock", use_container_width=True):
                if pwd_input.strip() == ADMIN_PASSWORD:
                    st.session_state.admin_unlocked = True
                    st.session_state.active_section = "Admin Settings"
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    else:
        st.success("🔓 Admin Mode Active")
        if st.button("🔒 Lock Admin Panel", use_container_width=True):
            st.session_state.admin_unlocked = False
            if st.session_state.active_section == "Admin Settings":
                st.session_state.active_section = "Help"
            st.rerun()


# ==============================================================================
# HERO HEADER
# ==============================================================================
st.markdown(
    """
    <div class="hero-banner">
        <div class="hero-title">🔥 Flame Behavior in Space</div>
        <div class="hero-sub">
            International Space Station (ISS) Combustion Science • Microgravity Fire Experiments,
            Historical Spaceflight Incidents, Terrestrial Spinoffs & Grounded AI Assistant
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# SECTION 1: OVERVIEW
# ==============================================================================
if st.session_state.active_section == "Overview":
    st.subheader("Why Study Flames in Microgravity?")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("PSI Investigations", "9")
    col2.metric("Total Cleaned Tests", "391")
    col3.metric("Spacefire Stories", "3")
    col4.metric("NASA Applications", "3")

    st.markdown(
        """
        On Earth, typical flames (~2,300 K) surrounded by ~300 K ambient air create an eight-fold
        density gradient that drives strong buoyant convection (~1 m/s). This buoyancy causes
        flames to elongate, flicker, and obscure underlying chemical and physical mechanisms.

        In the **microgravity environment aboard the International Space Station (ISS)**, buoyancy
        is eliminated—revealing spherical flames, low-stretch flames near spacecraft ventilation
        speeds (~10 cm/s), and invisible **cool flames** that challenge traditional terrestrial fire
        safety assumptions.
        """
    )

    st.markdown("### Quick Navigation")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🤖 Open Ask Me AI", use_container_width=True):
        st.session_state.active_section = "Ask Me"
        st.rerun()
    if c2.button("🧪 Open Help (Experiments)", use_container_width=True):
        st.session_state.active_section = "Help"
        st.rerun()
    if c3.button("📖 What about story", use_container_width=True):
        st.session_state.active_section = "What about story"
        st.rerun()
    if c4.button("🚀 NASA Applications", use_container_width=True):
        st.session_state.active_section = "NASA Applications"
        st.rerun()


# ==============================================================================
# SECTION 2: ASK ME (AI CHATBOT)
# ==============================================================================
elif st.session_state.active_section == "Ask Me":
    st.subheader("🤖 Ask Me — NASA Combustion Science AI Assistant")
    st.info(
        "Ask any question about the 9 ISS combustion experiments, the Excel test records, "
        "the *ISS Combustion Science Researcher's Guide* PDF, the 3 space fire stories, or the 3 NASA applications. "
        "If a question is outside these sources, the assistant will state that the available information is insufficient."
    )

    st.caption("Try asking:")
    sc1, sc2, sc3 = st.columns(3)
    sample_q = None
    if sc1.button("Compare SAFFIRE-I concurrent vs opposed burn time", use_container_width=True):
        sample_q = "Compare the burn time in SAFFIRE-I (PSI-98) between S1 and S2."
    if sc2.button("What did ACME CFI-G discover about cool flames?", use_container_width=True):
        sample_q = "What did PSI-159 (ACME CFI-G) discover about cool flames and what safety tip does it give?"
    if sc3.button("What caused the Apollo 13 oxygen tank explosion?", use_container_width=True):
        sample_q = "What caused the oxygen tank explosion on Apollo 13?"

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input(
        "Ask a question in English about microgravity combustion, experiments, stories, or applications..."
    )
    prompt_to_run = sample_q or user_input

    if prompt_to_run:
        st.session_state.chat_history.append({"role": "user", "content": prompt_to_run})
        with st.chat_message("user"):
            st.markdown(prompt_to_run)

        with st.chat_message("assistant"):
            with st.spinner("Searching NASA datasets & generating grounded answer..."):
                relevant_chunks = retrieve_relevant_context(prompt_to_run, all_chunks, top_k=5 ,excel_sheets=excel_sheets)
                reply, _engine = generate_grounded_answer(admin_cfg, prompt_to_run, relevant_chunks ,excel_sheets=excel_sheets)
                st.markdown(reply)

                if relevant_chunks:
                    with st.expander("🔍 Sources Consulted"):
                        for ch in relevant_chunks:
                            st.markdown(f"- **{ch['source']}**")

        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()


# ==============================================================================
# SECTION 3: HELP (9 EXPERIMENTS STACKED IN EXACT ORDER AS CLICKABLE CARDS)
# ==============================================================================
elif st.session_state.active_section == "Help":
    st.subheader("🧪 Help — Space Combustion & Flammability Experiments")
    st.write(
        "Explore all **9 ISS investigations** in mission order below. "
        "Click any experiment card to open its full scientific objective, execution method, "
        "results, conclusion, safety recommendation, and dataset metrics."
    )

    for exp in EXPERIMENTS:
        code = exp["code"]
        is_open = st.session_state.selected_experiment == code

        st.markdown(
            f"""
            <div class="exp-card">
                <span class="exp-code">{code}</span>
                <div class="exp-title">{code} - {exp['name']}</div>
                <div class="exp-meta">
                    Category: {exp['category']} &nbsp;|&nbsp;
                    Tests: {exp['total_tests']} &nbsp;|&nbsp;
                    Avg O₂: {exp['avg_o2']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        btn_label = f"🔽 Close {code} Details" if is_open else f"📄 Open {code} — {exp['name']}"
        if st.button(btn_label, key=f"card_btn_{code}", use_container_width=True):
            st.session_state.selected_experiment = None if is_open else code
            st.rerun()

        if is_open:
            st.markdown(
                f"""
                <div class="detail-box">
                    <h4>{code} — {exp['name']}</h4>
                    <p><strong>🎯 Objective:</strong> {exp['objective']}</p>
                    <p><strong>🔬 Execution Method:</strong> {exp['execution']}</p>
                    <p><strong>📊 Key Results:</strong> {exp['results']}</p>
                    <p><strong>🧠 Scientific Conclusion:</strong> {exp['conclusion']}</p>
                    <div class="safety-box">
                        <strong>🛡️ Safety Lesson Learned:</strong> {exp['safety_tip']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if code in excel_sheets:
                with st.expander(f"📑 View Raw Excel Data Table for {code} ({len(excel_sheets[code])} rows)"):
                    st.dataframe(excel_sheets[code], use_container_width=True)
            elif "Master_Unified_Data" in excel_sheets:
                mdf = excel_sheets["Master_Unified_Data"]
                sub = mdf[mdf["Investigation_Code"] == code]
                if not sub.empty:
                    with st.expander(f"📑 View Unified Dataset Rows for {code} ({len(sub)} rows)"):
                        st.dataframe(sub, use_container_width=True)


# ==============================================================================
# SECTION 4: WHAT ABOUT STORY (3 SEPARATE STORIES)
# ==============================================================================
elif st.session_state.active_section == "What about story":
    st.subheader("📖 What about story — Historical Spacecraft Fire Incidents")
    st.write("Select each historical incident separately below to learn how fire shaped spacecraft safety.")

    story_tabs = st.tabs([f"🔥 {s['title']}" for s in STORIES])
    for tab, story in zip(story_tabs, STORIES):
        with tab:
            st.markdown(
                f"""
                <div class="story-card">
                    <h3>{story['title']}</h3>
                    <p style="color:#ffb076; font-weight:600;">{story['subtitle']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write(story["content"])


# ==============================================================================
# SECTION 5: NASA APPLICATIONS (3 SEPARATE SPINOFF APPLICATIONS)
# ==============================================================================
elif st.session_state.active_section == "NASA Applications":
    st.subheader("🚀 NASA Applications — Space Fire Technology Saving Lives on Earth")
    st.write("Discover how NASA research into space fire safety led to life-saving firefighting technologies on Earth.")

    app_tabs = st.tabs([f"🛡️ {a['title']}" for a in NASA_APPLICATIONS])
    for tab, app_item in zip(app_tabs, NASA_APPLICATIONS):
        with tab:
            st.markdown(
                f"""
                <div class="app-card">
                    <h3>{app_item['title']}</h3>
                    <p style="color:#60a5fa; font-weight:600;">{app_item['subtitle']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write(app_item["content"])


# ==============================================================================
# SECTION 6: LOCKED ADMIN SETTINGS (ONLY VISIBLE WHEN UNLOCKED)
# ==============================================================================
elif st.session_state.active_section == "Admin Settings" and st.session_state.admin_unlocked:
    st.subheader("⚙️ Admin Settings (Private Owner Panel)")
    st.success(
        f"Knowledge Base currently indexed: **{len(all_chunks)} chunks** "
        f"({n_excels} Excel file(s), {n_pdfs} PDF file(s))."
    )

    if st.session_state.last_api_error:
        st.warning(f"Last API Diagnostic: `{st.session_state.last_api_error}`")

    st.markdown("### 1. AI Provider & API Key Configuration")
    provider_options = [
        "Cosmo AI (with Local Grounded Fallback)",
        "Gemini (with Local Grounded Fallback)",
        "Groq (with Local Grounded Fallback)",
        "OpenAI (with Local Grounded Fallback)",
        "Local Grounded Knowledge Engine Only",
    ]
    cur_provider = admin_cfg.get("provider", provider_options[0])
    if cur_provider not in provider_options:
        cur_provider = provider_options[0]

    chosen_provider = st.selectbox("Active AI Provider", provider_options, index=provider_options.index(cur_provider))
    cosmo_key_input = st.text_input(
        "Cosmo AI Key (cosmo_...)",
        value=admin_cfg.get("cosmo_api_key", ""),
        type="password",
    )

    col_v1, col_v2 = st.columns([1, 2])
    with col_v1:
        if st.button("🧪 Verify Cosmo Key", use_container_width=True):
            ok, msg = verify_cosmo_key(cosmo_key_input)
            if ok:
                st.success(f"Cosmo Key Valid! {msg}")
            else:
                st.error(f"Cosmo rejected this key: {msg}")
    with col_v2:
        st.caption(
            "Note: If Cosmo rejects the key (`Invalid or missing API key`), make sure it was "
            "generated on platform.askcosmo.ai with Realtime permissions, or use a backup key below. "
            "Public visitors will still receive grounded answers automatically via the Built-in Knowledge Engine."
        )

    backup_key_input = st.text_input(
        "Optional Backup API Key (Gemini / Groq / OpenAI)",
        value=admin_cfg.get("backup_api_key", ""),
        type="password",
    )
    backup_model_input = st.text_input(
        "Optional Backup Model Name (leave blank for default)",
        value=admin_cfg.get("backup_model", ""),
        placeholder="e.g., gemini-2.0-flash, llama-3.3-70b-versatile, gpt-4o-mini",
    )

    if st.button("💾 Save AI Settings", type="primary"):
        new_cfg = {
            "provider": chosen_provider,
            "cosmo_api_key": cosmo_key_input.strip(),
            "backup_api_key": backup_key_input.strip(),
            "backup_model": backup_model_input.strip(),
        }
        save_admin_config(new_cfg)
        st.session_state.last_api_error = ""
        st.success("Admin AI settings saved!")
        st.rerun()

    st.divider()
    st.markdown("### 2. Upload Additional Knowledge Base Files (.xlsx / .pdf)")
    st.caption(f"Files uploaded here are saved in `./{UPLOAD_DIR}/` and automatically indexed for all users.")
    uploaded_files = st.file_uploader(
        "Upload Excel (.xlsx) or PDF (.pdf)",
        type=["xlsx", "pdf"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        saved_names = []
        for uf in uploaded_files:
            out_path = os.path.join(UPLOAD_DIR, uf.name)
            with open(out_path, "wb") as f:
                f.write(uf.getbuffer())
            saved_names.append(uf.name)
        st.cache_resource.clear()
        st.success(f"Saved & re-indexed: {', '.join(saved_names)}")
        st.rerun()