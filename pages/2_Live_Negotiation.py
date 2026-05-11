"""
Live Negotiation — 4-agent conversation view (Centrica + 3 vendors).
Shows the negotiation as a unified chat thread, plus per-supplier price journey.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database as db
from demo_data import seed_demo_data
from negotiation_engine import PERSONAS

st.set_page_config(page_title="Live Negotiation | Centrica", page_icon="🔄", layout="wide")

# ── Brand CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root { --navy:#0F2067; --mint:#85DB9C; --lav:#B999F6; --pale:#DECFFF; --purple:#9B2BF7; }
[data-testid="stSidebar"] { background: var(--navy) !important; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] a { color: var(--mint) !important; }
.logo-text { font-size: 1.4rem; font-weight: 800; color: white; }
.logo-sub  { font-size: 0.75rem; color: var(--mint); letter-spacing: 0.08em; font-weight: 500; }

/* Persona avatars + colour coding */
.chat-row { display: flex; gap: 0.75rem; margin-bottom: 0.8rem; align-items: flex-start; }
.chat-row.right { flex-direction: row-reverse; }
.avatar {
    width: 42px; height: 42px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; color: white; flex-shrink: 0; font-size: 0.95rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}
.av-centrica  { background: linear-gradient(135deg,#0F2067,#9B2BF7); }
.av-trusted   { background: linear-gradient(135deg,#85DB9C,#16A34A); color: #0F2067; }
.av-cheap     { background: linear-gradient(135deg,#F59E0B,#DC2626); }
.av-premium   { background: linear-gradient(135deg,#B999F6,#7C3AED); }

.bubble {
    flex: 1;
    border-radius: 14px;
    padding: 0.7rem 1rem;
    font-size: 0.9rem;
    line-height: 1.5;
    border: 1px solid #E5E7EB;
    background: white;
    max-width: 75%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.bubble.centrica   { background: #EEF2FF; border-color: #C7D2FE; }
.bubble.trusted    { background: #F0FDF4; border-color: #BBF7D0; }
.bubble.cheap      { background: #FFFBEB; border-color: #FDE68A; }
.bubble.premium    { background: #F5F3FF; border-color: #DDD6FE; }
.bubble.po         { background: linear-gradient(135deg,#DCFCE7,#F0FDF4); border: 2px solid #16A34A; font-weight: 500; }
.bubble.rejection  { background: #FEF2F2; border-color: #FECACA; opacity: 0.85; }

.bubble-meta {
    font-size: 0.72rem;
    color: #6B7280;
    margin-bottom: 4px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.persona-tag {
    display: inline-block;
    font-size: 0.65rem;
    background: #F3F4F6;
    color: #374151;
    padding: 1px 6px;
    border-radius: 4px;
    font-weight: 600;
    margin-left: 6px;
    letter-spacing: 0;
    text-transform: none;
}

/* Supplier summary cards */
.supplier-card {
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    background: white;
    height: 100%;
}
.supplier-card.winner { border: 2px solid #16A34A; background: #F0FDF4; }
.supplier-card.withdrawn { opacity: 0.65; }

.tag { display:inline-block; padding:2px 8px; border-radius:99px; font-size:0.72rem; font-weight:700; margin-right:4px; }
.tag-existing { background:#EEF2FF; color:#4F46E5; }
.tag-scouted  { background:#FEF3C7; color:#D97706; }
.tag-cheap    { background:#FEE2E2; color:#DC2626; }
.tag-premium  { background:#EDE9FE; color:#7C3AED; }
.tag-trusted  { background:#DCFCE7; color:#16A34A; }
.tag-winner   { background:#16A34A; color:white; }
.tag-withdrawn { background:#F3F4F6; color:#6B7280; }
</style>
""", unsafe_allow_html=True)

db.init_db()
if not db.db_has_demo_data():
    seed_demo_data()

with st.sidebar:
    st.markdown('<div class="logo-text">⚡ Centrica</div><div class="logo-sub">TAIL-SPEND AGENT</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.page_link("app.py", label="🛒  New Purchase Request")
    st.page_link("pages/2_Live_Negotiation.py", label="🔄  Live Negotiation")
    st.page_link("pages/3_Stakeholder_Dashboard.py", label="📊  Stakeholder Dashboard")
    st.page_link("pages/4_Audit_Trail.py", label="🔍  Audit Trail")
    st.markdown("---")

st.markdown("## 🔄 Live Negotiation")
st.caption("4-agent negotiation conversation: Centrica Procurement Agent vs. 3 vendors with distinct strategies.")

# ── Request selector ───────────────────────────────────────────────────────────
all_requests = db.get_all_requests()
if not all_requests:
    st.info("No requests yet. Go to **New Purchase Request** to start one.")
    st.stop()

request_options = {
    f"{r['id']} — {r['category']} ({r['status'].title()}) · {r['buyer_name']}": r["id"]
    for r in all_requests
}
selected_label = st.selectbox("Select request", list(request_options.keys()), index=0)
request_id = request_options[selected_label]
request = db.get_request(request_id)
negotiations = db.get_negotiations_for_request(request_id)
po = db.get_po_for_request(request_id)

# ── Header ─────────────────────────────────────────────────────────────────────
status_color = {"completed":"🟢","awarded":"🟢","negotiating":"🟡","escalated":"🔴","intake":"🔵"}.get(request["status"],"⚪")
st.markdown(f"### {status_color} {request['category']}")
st.caption(f"_{request['description']}_")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Buyer", request["buyer_name"])
col2.metric("Budget", f"£{request.get('max_budget', 0):,.0f}")
col3.metric("Risk", (request.get("risk_tier") or "low").upper())
col4.metric("Status", request["status"].title())

if request["status"] == "escalated" and not negotiations:
    st.error("⚠️ This request was escalated to the Category Manager due to high risk / value.")
    st.stop()

if not negotiations:
    st.info("Negotiation not started for this request.")
    st.stop()

if po:
    st.success(
        f"✅ **{po['po_number']} issued** — Awarded for **£{po['total_value']:,.2f}**  ·  "
        f"Savings: **£{po['savings_vs_budget']:,.0f}** ({po['savings_pct']:.1f}%)  ·  "
        f"Delivery: {po.get('delivery_date', '—')}"
    )

# ── Supplier summary cards ─────────────────────────────────────────────────────
st.markdown("### Supplier Lineup")
cols = st.columns(len(negotiations))

PERSONA_LABEL_MAP = {
    "trusted_partner": ("Trusted Partner", "tag-trusted"),
    "aggressive_cheap": ("Always Cheapest", "tag-cheap"),
    "premium_walk": ("Premium / Walk-away", "tag-premium"),
    # legacy strategy names
    "terms-flex": ("Trusted Partner", "tag-trusted"),
    "price-firm": ("Premium / Walk-away", "tag-premium"),
    "walk-away": ("Premium / Walk-away", "tag-premium"),
}

for col, neg in zip(cols, negotiations):
    is_winner = bool(neg.get("winner"))
    is_withdrawn = neg.get("status") == "rejected"
    card_cls = "winner" if is_winner else ("withdrawn" if is_withdrawn else "")

    src_tag = "tag-existing" if neg.get("supplier_type") == "existing" else "tag-scouted"
    src_lbl = "Existing Supplier" if neg.get("supplier_type") == "existing" else "Internet Scout"
    p_lbl, p_tag = PERSONA_LABEL_MAP.get(neg.get("strategy") or "", ("—", "tag-existing"))

    status_tag = ("tag-winner", "WINNER") if is_winner else (("tag-withdrawn", "WITHDREW") if is_withdrawn else ("tag-existing", "No deal"))
    if neg.get("status") == "active" or (neg.get("status") == "rfq_sent" and not is_winner and not is_withdrawn):
        status_tag = ("tag-existing", "Active")

    with col:
        st.markdown(f"""
        <div class="supplier-card {card_cls}">
            <div style="font-weight:800; font-size:1.0rem; margin-bottom:6px;">{neg['supplier_name']}</div>
            <div style="margin-bottom:8px;">
                <span class="tag {src_tag}">{src_lbl}</span>
                <span class="tag {p_tag}">{p_lbl}</span>
            </div>
            <div style="font-size:0.78rem; color:#6B7280; margin-bottom:8px;">{neg.get('location','') or ''}</div>
            <span class="tag {status_tag[0]}">{status_tag[1]}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        init_price = neg.get("initial_price") or 0
        current = neg.get("agreed_price") or neg.get("current_offer") or init_price
        m1, m2 = st.columns(2)
        m1.metric("Initial", f"£{init_price:,.0f}")
        if is_winner and neg.get("agreed_price"):
            m2.metric("Agreed", f"£{neg['agreed_price']:,.0f}", delta=f"−£{init_price - neg['agreed_price']:,.0f}")
        elif is_withdrawn:
            m2.metric("Withdrew", "—")
        else:
            m2.metric("Final", f"£{current:,.0f}")

        if is_winner and neg.get("savings"):
            st.markdown(f"**💰 Savings: £{neg['savings']:,.0f}**")
        st.caption(f"Target £{neg.get('centrica_target',0):,.0f}  ·  {neg.get('payment_terms','—')}  ·  Rounds: {neg.get('round_number') or 1}")

# ── Unified conversation thread ────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 💬 Live Conversation")
st.caption("All 4 agents in one thread — chronological order, as the negotiation actually happened.")

# Build sender → persona+avatar map
sender_meta = {"Centrica Procurement Agent": ("centrica", "av-centrica", "🤖", "Centrica")}
for neg in negotiations:
    pkey = neg.get("strategy") or ""
    if pkey in ("trusted_partner", "terms-flex"):
        cls, avc, icon, label = "trusted", "av-trusted", "🤝", "Trusted Partner"
    elif pkey in ("aggressive_cheap",):
        cls, avc, icon, label = "cheap", "av-cheap", "💰", "Always Cheapest"
    elif pkey in ("premium_walk", "walk-away", "price-firm"):
        cls, avc, icon, label = "premium", "av-premium", "💎", "Premium Specialist"
    else:
        cls, avc, icon, label = "trusted", "av-trusted", "🏢", "Vendor"
    initials = "".join([w[0] for w in neg["supplier_name"].split()[:2]]).upper()
    sender_meta[neg["supplier_name"]] = (cls, avc, initials, label)

# Aggregate all negotiation messages for this request, sorted
all_msgs = []
for neg in negotiations:
    for m in db.get_messages_for_negotiation(neg["id"]):
        m["_persona"] = neg.get("strategy")
        all_msgs.append(m)
all_msgs.sort(key=lambda m: m.get("timestamp") or "")

# Render conversation
for msg in all_msgs:
    sender = msg["sender"]
    meta = sender_meta.get(sender, ("centrica", "av-centrica", "?", "Agent"))
    cls, avc, icon, persona_label = meta
    is_centrica = sender == "Centrica Procurement Agent"
    is_po = msg.get("message_type") == "po"
    is_rejection = msg.get("message_type") == "rejection"

    bubble_cls = cls
    if is_po:
        bubble_cls = "po"
    elif is_rejection:
        bubble_cls = f"{cls} rejection"

    row_dir = "right" if is_centrica else ""
    ts = (msg.get("timestamp") or "")[:16].replace("T", " ")

    content_html = msg["content"].replace("\n", "<br>")

    st.markdown(f"""
    <div class="chat-row {row_dir}">
        <div class="avatar {avc}">{icon}</div>
        <div class="bubble {bubble_cls}">
            <div class="bubble-meta">{sender}<span class="persona-tag">{persona_label}</span> · {ts}</div>
            {content_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption(f"💡 Negotiation between **{len(negotiations)+1} agents** · {len(all_msgs)} messages exchanged · Full audit available in 🔍 Audit Trail")
