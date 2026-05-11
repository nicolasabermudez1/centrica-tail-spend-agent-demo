"""
Centrica Tail-Spend Agent — Buyer Intake Chat
Entry point: streamlit run app.py
"""
# Use OS certificate store (Windows trust store for Accenture corporate SSL interception).
# No-op on Linux (Streamlit Cloud) where the default certifi bundle works.
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import uuid
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

import database as db
from intake_bot import chat_stream, extract_intake_json, force_extract_intake
import negotiation_engine as engine
from demo_data import seed_demo_data


def _commit_intake(intake_json: dict) -> None:
    """Persist the extracted intake JSON to DB and mark session as intake-complete."""
    intake_json.setdefault("buyer_name", st.session_state.buyer_name)
    intake_json.setdefault("buyer_department", st.session_state.get("buyer_dept", "Operations"))
    st.session_state.intake_data = intake_json
    st.session_state.intake_complete = True
    req_id = f"req-live-{uuid.uuid4().hex[:8]}"
    st.session_state.request_id = req_id
    now = datetime.utcnow().isoformat()
    db.insert_request({
        **intake_json,
        "id": req_id,
        "status": "intake",
        "created_at": now,
        "updated_at": now,
    })
    for m in st.session_state.messages:
        db.insert_message({
            "request_id": req_id,
            "sender": "buyer" if m["role"] == "user" else "bot",
            "content": m["content"].split("INTAKE_COMPLETE:")[0].strip(),
            "message_type": "chat",
            "timestamp": now,
        })


def _has_api_key() -> bool:
    """Return True if a Gemini key is configured (via Streamlit secrets or env)."""
    try:
        if "GEMINI_API_KEY" in st.secrets and not str(st.secrets["GEMINI_API_KEY"]).startswith("AIzaSy..."):
            return True
    except Exception:
        pass
    k = os.getenv("GEMINI_API_KEY", "")
    return bool(k) and not k.startswith("AIzaSy...")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Centrica | Tail-Spend Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Centrica palette */
  :root {
    --navy:    #0F2067;
    --mint:    #85DB9C;
    --lav:     #B999F6;
    --pale:    #DECFFF;
    --purple:  #9B2BF7;
  }

  /* Top header bar */
  [data-testid="stHeader"] { background: var(--navy); }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: var(--navy) !important;
  }
  [data-testid="stSidebar"] * { color: white !important; }
  [data-testid="stSidebar"] a { color: var(--mint) !important; }
  [data-testid="stSidebar"] .stSelectbox label { color: white !important; }

  /* Main page background */
  .main .block-container { padding-top: 1.5rem; }

  /* Chat bubbles */
  .chat-bubble-bot {
    background: #EEF2FF;
    border-left: 4px solid var(--navy);
    padding: 0.75rem 1rem;
    border-radius: 0 12px 12px 12px;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
  }
  .chat-bubble-user {
    background: var(--pale);
    border-right: 4px solid var(--purple);
    padding: 0.75rem 1rem;
    border-radius: 12px 0 12px 12px;
    margin-bottom: 0.5rem;
    margin-left: 4rem;
    font-size: 0.95rem;
    text-align: right;
  }

  /* Metric cards */
  .metric-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .metric-label { font-size: 0.8rem; color: #6B7280; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
  .metric-value { font-size: 2rem; font-weight: 700; color: var(--navy); line-height: 1.2; }
  .metric-delta { font-size: 0.85rem; color: #16A34A; margin-top: 0.2rem; }

  /* Status badges */
  .badge { display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 0.78rem; font-weight: 600; }
  .badge-completed   { background: #DCFCE7; color: #16A34A; }
  .badge-negotiating { background: #FEF3C7; color: #D97706; }
  .badge-escalated   { background: #FEE2E2; color: #DC2626; }
  .badge-intake      { background: #EEF2FF; color: #4F46E5; }

  /* Winner highlight */
  .winner-badge { background: var(--mint); color: var(--navy); font-weight: 700; padding: 2px 10px; border-radius: 99px; font-size: 0.78rem; }
  .rejected-badge { background: #F3F4F6; color: #9CA3AF; padding: 2px 10px; border-radius: 99px; font-size: 0.78rem; }

  /* Dividers */
  hr { border-color: #E5E7EB; }

  /* Centrica logo text */
  .logo-text { font-size: 1.4rem; font-weight: 800; color: white; letter-spacing: -0.02em; }
  .logo-sub  { font-size: 0.75rem; color: var(--mint); letter-spacing: 0.08em; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── Initialise DB & seed demo data ─────────────────────────────────────────────
db.init_db()
if not db.db_has_demo_data():
    seed_demo_data()

# ── Sidebar navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 1rem 0 1.5rem;">
        <div class="logo-text">⚡ Centrica</div>
        <div class="logo-sub">TAIL-SPEND AGENT</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.page_link("app.py", label="🛒  New Purchase Request", icon=None)
    st.page_link("pages/2_Live_Negotiation.py", label="🔄  Live Negotiation", icon=None)
    st.page_link("pages/3_Stakeholder_Dashboard.py", label="📊  Stakeholder Dashboard", icon=None)
    st.page_link("pages/4_Audit_Trail.py", label="🔍  Audit Trail", icon=None)
    st.markdown("---")

    # API key warning
    if not _has_api_key():
        st.warning("⚠️ Gemini key not set.\nSet `GEMINI_API_KEY` in Streamlit secrets (cloud) or `.env` (local), then reload.")

# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "intake_complete" not in st.session_state:
    st.session_state.intake_complete = False
if "intake_data" not in st.session_state:
    st.session_state.intake_data = None
if "request_id" not in st.session_state:
    st.session_state.request_id = None
if "buyer_name" not in st.session_state:
    st.session_state.buyer_name = ""
if "negotiation_result" not in st.session_state:
    st.session_state.negotiation_result = None

# ── Header ─────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("## 🛒 New Purchase Request")
    st.caption("Describe what you need and our agent will handle sourcing and negotiation automatically.")
with col_h2:
    if st.button("🔄 Start New Request", use_container_width=True):
        st.session_state.messages = []
        st.session_state.intake_complete = False
        st.session_state.intake_data = None
        st.session_state.request_id = None
        st.session_state.negotiation_result = None
        st.rerun()

# ── Buyer name input (only at start) ──────────────────────────────────────────
if not st.session_state.messages:
    with st.container():
        st.markdown("#### Your details")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your name", placeholder="e.g. Sarah Mitchell", key="name_input")
        with col2:
            dept = st.text_input("Department", placeholder="e.g. Digital Technology", key="dept_input")
        if st.button("Start Chat →", type="primary", disabled=not name.strip()):
            st.session_state.buyer_name = name.strip()
            st.session_state.buyer_dept = dept.strip()
            # Trigger initial bot greeting
            st.session_state.messages = []
            st.rerun()

# ── Chat interface ─────────────────────────────────────────────────────────────
if st.session_state.buyer_name and not st.session_state.intake_complete:
    st.markdown(f"---\n**Chatting as:** {st.session_state.buyer_name}")

    # Render existing messages
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            # Strip INTAKE_COMPLETE JSON from display
            display = msg["content"]
            if "INTAKE_COMPLETE:" in display:
                display = display.split("INTAKE_COMPLETE:")[0].strip()
            with st.chat_message("assistant", avatar="⚡"):
                st.markdown(display)
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])

    # Auto-send greeting on first load
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="⚡"):
            if not _has_api_key():
                greeting = (
                    f"Hello {st.session_state.buyer_name.split()[0]}! I'm your Centrica Procurement Agent. "
                    "I'll help you source what you need quickly and at the best price. "
                    "*(Demo mode — set GEMINI_API_KEY to enable live AI responses.)* "
                    "\n\nWhat are you looking to procure today?"
                )
                st.markdown(greeting)
                st.session_state.messages.append({"role": "assistant", "content": greeting})
            else:
                streamed = st.write_stream(
                    chat_stream([], buyer_name=st.session_state.buyer_name)
                )
                st.session_state.messages.append({"role": "assistant", "content": streamed})
        st.rerun()

    # User input
    if user_input := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="⚡"):
            if not _has_api_key():
                # Demo fallback responses
                responses = [
                    "Got it! Could you tell me the quantity you need and any specific requirements?",
                    f"Thanks. What is your maximum budget for this (in £ GBP)?",
                    "And which business unit / department is this for?",
                    (
                        "Great — I have everything I need.\n\n"
                        "INTAKE_COMPLETE:\n"
                        '{"buyer_name": "' + st.session_state.buyer_name + '", '
                        '"buyer_department": "' + st.session_state.get("buyer_dept", "Operations") + '", '
                        '"business_unit": "British Gas Services", '
                        '"category": "IT Equipment & Software", '
                        '"subcategory": "Laptops", '
                        '"description": "' + (user_input[:80]) + '", '
                        '"quantity": 10, "unit": "units", '
                        '"max_budget": 15000, '
                        '"required_by": "2026-07-01", '
                        '"priority": "standard", "risk_tier": "low"}'
                    ),
                ]
                idx = min(len(st.session_state.messages) // 2, len(responses) - 1)
                response = responses[idx]
                st.markdown(response.split("INTAKE_COMPLETE:")[0].strip() or "Intake captured — launching agent...")
            else:
                response = st.write_stream(
                    chat_stream(st.session_state.messages, buyer_name=st.session_state.buyer_name)
                )

        st.session_state.messages.append({"role": "assistant", "content": response})

        # Check if intake is complete via inline marker
        intake_json = extract_intake_json(response)
        if intake_json:
            _commit_intake(intake_json)

        st.rerun()

    # ── Manual launch button (fallback if bot doesn't emit INTAKE_COMPLETE) ────
    user_turns = sum(1 for m in st.session_state.messages if m["role"] == "user")
    if user_turns >= 2 and not st.session_state.intake_complete:
        st.markdown("")
        col_a, col_b = st.columns([3, 1])
        with col_b:
            if st.button("🚀 Launch Sourcing Agent", type="primary", use_container_width=True):
                with st.spinner("Extracting requirement..."):
                    if _has_api_key():
                        intake_json = force_extract_intake(
                            st.session_state.messages,
                            buyer_name=st.session_state.buyer_name,
                            buyer_dept=st.session_state.get("buyer_dept", ""),
                        )
                    else:
                        # Demo-mode fallback
                        intake_json = {
                            "buyer_name": st.session_state.buyer_name,
                            "buyer_department": st.session_state.get("buyer_dept", "Operations"),
                            "business_unit": "British Gas Services",
                            "category": "IT Equipment & Software",
                            "subcategory": "—",
                            "description": next((m["content"] for m in st.session_state.messages if m["role"] == "user"), "Procurement request"),
                            "quantity": 10, "unit": "units", "max_budget": 25000,
                            "required_by": "2026-07-01", "priority": "standard", "risk_tier": "low",
                        }
                    if intake_json:
                        _commit_intake(intake_json)
                        st.rerun()
                    else:
                        st.error("Could not extract a structured request from the conversation. Please add a bit more detail and try again.")
        with col_a:
            st.caption("💡 Once you've shared the basics, click **Launch Sourcing Agent** to send RFQs to suppliers.")

# ── Post-intake: show summary + run negotiation ────────────────────────────────
if st.session_state.intake_complete and st.session_state.intake_data:
    intake = st.session_state.intake_data
    request_id = st.session_state.request_id

    st.success("✅ Intake complete — requirement captured")

    # Intake summary card
    with st.expander("📋 Requirement Summary", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Category", intake.get("category", "—"))
        col2.metric("Budget", f"£{intake.get('max_budget', 0):,.0f}")
        col3.metric("Risk Tier", intake.get("risk_tier", "low").upper())
        st.markdown(f"**Description:** {intake.get('description', '')}")
        st.markdown(f"**Quantity:** {intake.get('quantity', '')} {intake.get('unit', '')}  |  "
                    f"**Required by:** {intake.get('required_by', '—')}  |  "
                    f"**Priority:** {intake.get('priority', 'standard').title()}")

    # Run negotiation
    if st.session_state.negotiation_result is None:
        st.markdown("---")
        st.markdown("### 🤖 Agent Running — Sourcing & Negotiating")
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_cb(msg, pct):
            status_text.markdown(f"**{msg}**")
            progress_bar.progress(pct)

        try:
            result = engine.run_negotiation(request_id, intake, progress_cb=progress_cb)
            st.session_state.negotiation_result = result
            st.session_state.last_request_id = request_id
            st.session_state.just_completed = True   # banner trigger for Live Negotiation page
            if not result.get("escalated"):
                # Auto-navigate to the Live Negotiation monitoring view
                st.switch_page("pages/2_Live_Negotiation.py")
            else:
                st.rerun()
        except Exception as e:
            st.error(f"Negotiation failed: {e}")
            st.session_state.negotiation_result = {"escalated": True, "reason": str(e)}
            st.rerun()

    # If we land here, negotiation result already exists. Show it + offer manual jump.
    result = st.session_state.negotiation_result
    st.markdown("---")

    if result.get("escalated"):
        st.error(f"⚠️ **Escalated to Category Manager** — {result.get('reason', 'High-risk request requires human review.')}")
    else:
        st.markdown("### 🎉 Deal Secured")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Awarded to", result.get("winner_supplier", "—"))
        col2.metric("Agreed Price", f"£{result.get('agreed_price', 0):,.2f}")
        col3.metric("Savings vs Budget", f"£{result.get('savings', 0):,.0f}", f"{result.get('savings_pct', 0):.1f}%")
        col4.metric("PO Number", result.get("po_number", "—"))

        st.info(f"📄 Purchase order **{result.get('po_number')}** issued. Delivery by **{result.get('delivery_date', '—')}**.")
        if st.button("📺 View Live Negotiation →", type="primary"):
            st.session_state.last_request_id = st.session_state.get("request_id")
            st.session_state.just_completed = True
            st.switch_page("pages/2_Live_Negotiation.py")
