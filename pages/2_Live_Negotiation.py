"""
Live Negotiation — separate vendor tabs.

Each tab is a 1-on-1 conversation between the Sourcing Agent and a single vendor:
  RFQ + specs  →  vendor quote  →  commercial analysis + counter  →  vendor response
                                                                  →  award / decline.

A final "Award Decision" tab summarises the cheapest-accepted-offer comparison.
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

/* Chat bubbles in vendor tabs */
.chat-row { display: flex; gap: 0.75rem; margin-bottom: 0.9rem; align-items: flex-start; }
.chat-row.right { flex-direction: row-reverse; }
.avatar {
    width: 44px; height: 44px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; color: white; flex-shrink: 0; font-size: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}
.av-centrica  { background: linear-gradient(135deg,#0F2067,#9B2BF7); }
.av-trusted   { background: linear-gradient(135deg,#85DB9C,#16A34A); color: #0F2067; }
.av-cheap     { background: linear-gradient(135deg,#F59E0B,#DC2626); }
.av-premium   { background: linear-gradient(135deg,#B999F6,#7C3AED); }

.bubble {
    flex: 1;
    border-radius: 14px;
    padding: 0.85rem 1.05rem;
    font-size: 0.9rem;
    line-height: 1.55;
    border: 1px solid #E5E7EB;
    background: white;
    max-width: 78%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.bubble.centrica   { background: #EEF2FF; border-color: #C7D2FE; }
.bubble.trusted    { background: #F0FDF4; border-color: #BBF7D0; }
.bubble.cheap      { background: #FFFBEB; border-color: #FDE68A; }
.bubble.premium    { background: #F5F3FF; border-color: #DDD6FE; }
.bubble.po         { background: linear-gradient(135deg,#DCFCE7,#F0FDF4); border: 2px solid #16A34A; }
.bubble.decline    { background: #FEF2F2; border-color: #FECACA; opacity: 0.92; }

.bubble-meta {
    font-size: 0.72rem;
    color: #6B7280;
    margin-bottom: 6px;
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

/* Vendor header card inside each tab */
.vendor-header {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
}
.vendor-header.winner    { border: 2px solid #16A34A; background: #F0FDF4; }
.vendor-header.withdrawn { opacity: 0.7; }

.tag { display:inline-block; padding:2px 8px; border-radius:99px; font-size:0.72rem; font-weight:700; margin-right:4px; }
.tag-existing  { background:#EEF2FF; color:#4F46E5; }
.tag-scouted   { background:#FEF3C7; color:#D97706; }
.tag-cheap     { background:#FEE2E2; color:#DC2626; }
.tag-premium   { background:#EDE9FE; color:#7C3AED; }
.tag-trusted   { background:#DCFCE7; color:#16A34A; }
.tag-winner    { background:#16A34A; color:white; }
.tag-withdrawn { background:#F3F4F6; color:#6B7280; }

/* Decision tab table */
.decision-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
.decision-table th { background: #0F2067; color: white; padding: 8px 12px; font-size: 0.82rem; text-align: left; }
.decision-table td { padding: 9px 12px; font-size: 0.88rem; border-bottom: 1px solid #F3F4F6; }
.decision-table tr.winner-row td { background: #F0FDF4; font-weight: 600; }
.decision-table tr.withdrawn-row td { background: #FAFAFA; color: #9CA3AF; }
</style>
""", unsafe_allow_html=True)

db.init_db()
if not db.db_has_demo_data():
    seed_demo_data()

with st.sidebar:
    st.markdown('<div class="logo-text">⚡ Centrica</div><div class="logo-sub">TAIL-SPEND AGENT</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.page_link("app.py", label="👤  Business User View")
    st.page_link("pages/2_Live_Negotiation.py", label="🔄  Live Negotiation")
    st.page_link("pages/3_Stakeholder_Dashboard.py", label="📊  Procurement View")
    st.page_link("pages/4_Audit_Trail.py", label="🔍  Audit Trail")
    st.markdown("---")

st.markdown("## 🔄 Live Negotiation")
st.caption("The Sourcing Agent runs a separate, structured negotiation with each vendor — pick a tab to follow each conversation.")

# ── Celebration banner if user just completed a request ──────────────────────
if st.session_state.get("just_completed") and st.session_state.get("negotiation_result"):
    result = st.session_state.negotiation_result
    if not result.get("escalated"):
        st.markdown(f"""
        <div style="background: linear-gradient(135deg,#0F2067,#9B2BF7);
                    color: white; padding: 1.2rem 1.5rem; border-radius: 14px;
                    margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.12);">
            <div style="font-size: 1.15rem; font-weight: 800; margin-bottom: 6px;">
                🎉 Deal secured — {result.get('po_number', 'PO issued')}
            </div>
            <div style="font-size: 0.95rem; opacity: 0.95;">
                Awarded to <b>{result.get('winner_supplier', '—')}</b> at
                <b>£{result.get('agreed_price', 0):,.2f}</b> ·
                Savings <b>£{result.get('savings', 0):,.0f}</b>
                ({result.get('savings_pct', 0):.1f}%) ·
                Delivery by <b>{result.get('delivery_date', '—')}</b>
            </div>
            <div style="font-size: 0.85rem; opacity: 0.85; margin-top: 8px;">
                Open each vendor tab below to see the full 1-on-1 negotiation. The Award Decision tab shows the comparison.
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.session_state.just_completed = False

# ── Request selector ───────────────────────────────────────────────────────────
all_requests = db.get_all_requests()
if not all_requests:
    st.info("No requests yet. Go to **Business User View** to start one.")
    st.stop()

request_options = {
    f"{r['id']} — {r['category']} ({r['status'].title()}) · {r['buyer_name']}": r["id"]
    for r in all_requests
}

default_index = 0
preferred_id = st.session_state.get("last_request_id")
if preferred_id:
    for i, (_, rid) in enumerate(request_options.items()):
        if rid == preferred_id:
            default_index = i
            break

selected_label = st.selectbox("Select request", list(request_options.keys()), index=default_index)
request_id = request_options[selected_label]
request = db.get_request(request_id)
negotiations = db.get_negotiations_for_request(request_id)
po = db.get_po_for_request(request_id)

if not request:
    st.error("Request not found.")
    st.stop()

# ── Request header ─────────────────────────────────────────────────────────────
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
    st.info("Negotiation has not started for this request.")
    st.stop()

# ── Persona → avatar/colour map ───────────────────────────────────────────────
PERSONA_VISUAL = {
    "trusted_partner": ("trusted", "av-trusted", "🤝", "Trusted Partner",   "tag-trusted"),
    "aggressive_cheap": ("cheap",  "av-cheap",   "💰", "Always Cheapest",   "tag-cheap"),
    "premium_walk":    ("premium", "av-premium", "💎", "Premium Specialist","tag-premium"),
    # legacy fallbacks
    "terms-flex":      ("trusted", "av-trusted", "🤝", "Trusted Partner",   "tag-trusted"),
    "price-firm":      ("premium", "av-premium", "💎", "Premium Specialist","tag-premium"),
    "walk-away":       ("premium", "av-premium", "💎", "Premium Specialist","tag-premium"),
}

CENTRICA_VISUAL = ("centrica", "av-centrica", "🤖", "Sourcing Agent")


def _render_message(msg: dict, supplier_persona: str, supplier_name: str):
    sender = msg["sender"]
    mtype = msg.get("message_type", "chat")
    ts = (msg.get("timestamp") or "")[:16].replace("T", " ")
    is_centrica = sender == "Centrica Procurement Agent"
    content_html = msg["content"].replace("\n", "<br>")

    if is_centrica:
        cls, avc, icon, lbl = CENTRICA_VISUAL
        row_dir = "right"
        bubble_cls = "centrica"
        if mtype == "po":
            bubble_cls = "po"
        elif mtype == "rejection":
            bubble_cls = "decline"
    else:
        v = PERSONA_VISUAL.get(supplier_persona, ("trusted", "av-trusted", "🏢", "Vendor", "tag-trusted"))
        cls, avc, icon, lbl = v[0], v[1], v[2], v[3]
        row_dir = ""
        bubble_cls = cls
        if mtype == "rejection":
            bubble_cls = f"{cls} decline"

    st.markdown(f"""
    <div class="chat-row {row_dir}">
        <div class="avatar {avc}">{icon}</div>
        <div class="bubble {bubble_cls}">
            <div class="bubble-meta">{sender}<span class="persona-tag">{lbl}</span> · {ts}</div>
            {content_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_vendor_tab(neg: dict):
    persona = neg.get("strategy") or ""
    is_winner = bool(neg.get("winner"))
    is_withdrawn = neg.get("status") == "rejected"
    visual = PERSONA_VISUAL.get(persona, ("trusted", "av-trusted", "🏢", "Vendor", "tag-trusted"))
    persona_label, persona_tag_cls = visual[3], visual[4]

    src_tag = "tag-existing" if neg.get("supplier_type") == "existing" else "tag-scouted"
    src_lbl = "Existing Supplier" if neg.get("supplier_type") == "existing" else "Internet Scout"

    header_cls = "winner" if is_winner else ("withdrawn" if is_withdrawn else "")
    init_price = neg.get("initial_price") or 0
    current = neg.get("agreed_price") or neg.get("current_offer") or init_price

    if is_winner:
        status_html = '<span class="tag tag-winner">🏆 WINNER</span>'
    elif is_withdrawn:
        status_html = '<span class="tag tag-withdrawn">WITHDREW</span>'
    elif neg.get("agreed_price"):
        status_html = '<span class="tag tag-trusted">Accepted (runner-up)</span>'
    else:
        status_html = '<span class="tag tag-existing">In progress</span>'

    st.markdown(f"""
    <div class="vendor-header {header_cls}">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
                <div style="font-weight:800; font-size:1.05rem;">{neg['supplier_name']}</div>
                <div style="font-size:0.8rem; color:#6B7280; margin-top:2px;">{neg.get('location','') or ''}</div>
            </div>
            <div>
                <span class="tag {src_tag}">{src_lbl}</span>
                <span class="tag {persona_tag_cls}">{persona_label}</span>
                {status_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Initial Quote", f"£{init_price:,.0f}")
    if is_winner and neg.get("agreed_price"):
        m2.metric("Final Agreed", f"£{neg['agreed_price']:,.0f}", delta=f"−£{init_price - neg['agreed_price']:,.0f}")
    elif is_withdrawn:
        m2.metric("Final", "Withdrew")
    else:
        m2.metric("Final", f"£{current:,.0f}")
    m3.metric("Payment", neg.get('payment_terms', '—'))
    m4.metric("Rounds", neg.get('round_number') or 1)

    st.markdown("**Conversation**")
    msgs = db.get_messages_for_negotiation(neg["id"])
    for m in msgs:
        _render_message(m, persona, neg["supplier_name"])


# ── Build tab labels with persona + status icons ─────────────────────────────
def _tab_label(neg: dict) -> str:
    persona = neg.get("strategy") or ""
    visual = PERSONA_VISUAL.get(persona, ("trusted", "av-trusted", "🏢", "Vendor", "tag-trusted"))
    icon = visual[2]
    suffix = " 🏆" if neg.get("winner") else (" 🚫" if neg.get("status") == "rejected" else "")
    return f"{icon} {neg['supplier_name']}{suffix}"


tab_labels = [_tab_label(n) for n in negotiations] + ["📊 Award Decision"]
tabs = st.tabs(tab_labels)

for tab, neg in zip(tabs[:-1], negotiations):
    with tab:
        _render_vendor_tab(neg)

# ── Award Decision tab ────────────────────────────────────────────────────────
with tabs[-1]:
    st.markdown("### Sourcing Agent — Award Decision")
    st.caption("Rule: the **lowest accepted offer** wins. Walk-aways and declined counters are excluded.")

    rows_html = ""
    accepted_count = 0
    for neg in negotiations:
        persona = neg.get("strategy") or ""
        visual = PERSONA_VISUAL.get(persona, ("trusted", "av-trusted", "🏢", "Vendor", "tag-trusted"))
        persona_label = visual[3]

        if neg.get("winner"):
            row_cls = "winner-row"
            verdict = "🏆 <b>AWARDED</b>"
        elif neg.get("status") == "rejected":
            row_cls = "withdrawn-row"
            verdict = "Withdrew"
        elif neg.get("agreed_price"):
            row_cls = ""
            verdict = "Runner-up"
        else:
            row_cls = ""
            verdict = "No deal"

        if neg.get("agreed_price"):
            final_str = f"£{neg['agreed_price']:,.0f}"
            accepted_count += 1
        elif neg.get("status") == "rejected":
            final_str = "—"
        else:
            final_str = f"£{neg.get('current_offer', 0):,.0f}"

        source_lbl = "Existing" if neg.get('supplier_type') == 'existing' else "Scouted"
        rows_html += (
            f'<tr class="{row_cls}">'
            f'<td><b>{neg["supplier_name"]}</b></td>'
            f'<td>{persona_label}</td>'
            f'<td>{source_lbl}</td>'
            f'<td>£{neg.get("initial_price", 0):,.0f}</td>'
            f'<td>{final_str}</td>'
            f'<td>{neg.get("payment_terms", "—")}</td>'
            f'<td>{neg.get("delivery_days", "—")} days</td>'
            f'<td>{verdict}</td>'
            f'</tr>'
        )

    table_html = (
        '<table class="decision-table">'
        '<thead><tr>'
        '<th>Vendor</th><th>Persona</th><th>Source</th>'
        '<th>Initial</th><th>Final</th>'
        '<th>Payment</th><th>Delivery</th><th>Outcome</th>'
        '</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
    )
    # Flat single-line HTML (no leading whitespace) so markdown doesn't treat it as a code block
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("")

    if po:
        budget = request.get("max_budget", 0) or 0
        st.success(
            f"**Purchase Order {po['po_number']} issued** — total **£{po['total_value']:,.2f}** · "
            f"Savings vs buyer budget £{budget:,.0f}: **£{po['savings_vs_budget']:,.0f}** ({po['savings_pct']:.1f}%) · "
            f"Payment **{po.get('payment_terms','—')}** · Delivery by **{po.get('delivery_date','—')}**"
        )

        st.markdown(f"""
        **Sourcing Agent reasoning:**
        - {accepted_count} of {len(negotiations)} suppliers reached agreement.
        - Of those, the **lowest accepted bid** was selected.
        - Total negotiation: {sum(len(db.get_messages_for_negotiation(n['id'])) for n in negotiations)} messages exchanged
          across {len(negotiations)} parallel vendor conversations.
        """)
    elif request["status"] == "escalated":
        st.error("⚠️ No supplier reached agreement within budget. Request escalated to Category Manager.")
    else:
        st.info("Negotiation still in progress.")
