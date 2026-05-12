"""
Audit Trail — full conversation log for any request: buyer intake + all supplier negotiations.
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database as db
from demo_data import seed_demo_data

st.set_page_config(page_title="Audit Trail | Centrica", page_icon="🔍", layout="wide")

st.markdown("""
<style>
:root { --navy:#0F2067; --mint:#85DB9C; --lav:#B999F6; --pale:#DECFFF; --purple:#9B2BF7; }
[data-testid="stSidebar"] { background: var(--navy) !important; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] a { color: var(--mint) !important; }
.logo-text { font-size: 1.4rem; font-weight: 800; color: white; }
.logo-sub  { font-size: 0.75rem; color: var(--mint); letter-spacing: 0.08em; font-weight: 500; }

.timeline-item {
    display: flex;
    gap: 1rem;
    margin-bottom: 0.75rem;
    align-items: flex-start;
}
.timeline-dot {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    flex-shrink: 0;
    margin-top: 2px;
}
.dot-bot      { background: #EEF2FF; color: var(--navy); }
.dot-buyer    { background: var(--pale); color: var(--purple); }
.dot-supplier { background: #F3F4F6; color: #374151; }
.dot-accept   { background: #DCFCE7; color: #16A34A; }
.dot-reject   { background: #FEE2E2; color: #DC2626; }
.dot-po       { background: var(--mint); color: var(--navy); font-weight: 800; }
.dot-rfq      { background: #F5F3FF; color: var(--purple); }

.msg-bubble {
    flex: 1;
    border-radius: 0 10px 10px 10px;
    padding: 0.65rem 0.9rem;
    font-size: 0.87rem;
    line-height: 1.5;
    border: 1px solid #E5E7EB;
    background: white;
}
.msg-meta {
    font-size: 0.72rem;
    color: #9CA3AF;
    margin-bottom: 3px;
    font-weight: 600;
}

.section-header { font-size: 1rem; font-weight: 700; color: var(--navy); margin: 1.25rem 0 0.5rem; border-bottom: 2px solid var(--mint); padding-bottom: 3px; }

.info-row { display: flex; gap: 2rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.info-item { font-size: 0.85rem; }
.info-label { font-weight: 700; color: #374151; }
.info-val { color: #6B7280; }
</style>
""", unsafe_allow_html=True)

db.init_db()
if not db.db_has_demo_data():
    seed_demo_data()

with st.sidebar:
    st.markdown('<div class="logo-text">⚡ Centrica</div><div class="logo-sub">TAIL-SPEND AGENT</div>', unsafe_allow_html=True)
    st.markdown("---")
    _neg_locked = st.session_state.get("negotiation_locked", False)
    st.page_link("app.py", label="👤  Business User View")
    st.page_link("pages/2_Live_Negotiation.py",
                 label="🔒  Live Negotiation (locked)" if _neg_locked else "🔄  Live Negotiation",
                 disabled=_neg_locked)
    st.page_link("pages/3_Stakeholder_Dashboard.py", label="📊  Procurement View")
    st.page_link("pages/4_Audit_Trail.py", label="🔍  Audit Trail")
    st.markdown("---")

st.markdown("## 🔍 Audit Trail")
st.caption("Full conversation and negotiation log for compliance, review, and Category Manager oversight.")

# ── Request selector ───────────────────────────────────────────────────────────
all_requests = db.get_all_requests()
if not all_requests:
    st.info("No requests to audit yet. Start a new request from the Business User View page.")
    st.stop()

col_sel, col_filter = st.columns([3, 1])
with col_filter:
    filter_status = st.selectbox("Filter by status", ["All", "completed", "negotiating", "escalated", "intake"])
with col_sel:
    filtered = all_requests if filter_status == "All" else [r for r in all_requests if r["status"] == filter_status]
    request_labels = {
        f"[{r['status'].upper()}] {r['id']} — {r['category']} · {r['buyer_name']} · £{r.get('max_budget',0):,.0f}": r["id"]
        for r in filtered
    }
    if not request_labels:
        st.info(f"No requests with status '{filter_status}'.")
        st.stop()
    selected_label = st.selectbox("Select request to audit", list(request_labels.keys()))
    request_id = request_labels[selected_label]

request = db.get_request(request_id)
negotiations = db.get_negotiations_for_request(request_id)
po = db.get_po_for_request(request_id)

if not request:
    st.error("Request not found.")
    st.stop()

# ── Request detail header ──────────────────────────────────────────────────────
STATUS_COLOR = {"completed": "#16A34A", "awarded": "#16A34A", "negotiating": "#D97706",
                "escalated": "#DC2626", "intake": "#4F46E5"}
status_col = STATUS_COLOR.get(request["status"], "#6B7280")

st.markdown(f"""
<div style="background:white; border:1px solid #E5E7EB; border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1rem;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
        <div style="font-size:1.15rem; font-weight:800; color:#0F2067;">{request['category']} — {request['id']}</div>
        <span style="background:{status_col}22; color:{status_col}; font-weight:700; font-size:0.82rem;
              padding:3px 12px; border-radius:99px;">{request['status'].upper()}</span>
    </div>
    <div class="info-row">
        <div class="info-item"><span class="info-label">Buyer: </span><span class="info-val">{request['buyer_name']}</span></div>
        <div class="info-item"><span class="info-label">Department: </span><span class="info-val">{request.get('buyer_department','—')}</span></div>
        <div class="info-item"><span class="info-label">BU: </span><span class="info-val">{request.get('business_unit','—')}</span></div>
        <div class="info-item"><span class="info-label">Budget: </span><span class="info-val">£{request.get('max_budget',0):,.0f}</span></div>
        <div class="info-item"><span class="info-label">Risk: </span><span class="info-val">{(request.get('risk_tier') or 'low').upper()}</span></div>
        <div class="info-item"><span class="info-label">Priority: </span><span class="info-val">{request.get('priority','standard').title()}</span></div>
        <div class="info-item"><span class="info-label">Required by: </span><span class="info-val">{request.get('required_by','—')}</span></div>
        <div class="info-item"><span class="info-label">Created: </span><span class="info-val">{(request.get('created_at') or '')[:10]}</span></div>
    </div>
    <div style="font-size:0.88rem; color:#374151; margin-top:6px;"><b>Description:</b> {request.get('description','')}</div>
</div>
""", unsafe_allow_html=True)

# ── PO details ─────────────────────────────────────────────────────────────────
if po:
    st.success(
        f"**Purchase Order: {po['po_number']}** · Value: £{po['total_value']:,.2f} · "
        f"Savings: £{po['savings_vs_budget']:,.0f} ({po['savings_pct']:.1f}%) · "
        f"Terms: {po.get('payment_terms','—')} · Delivery: {po.get('delivery_date','—')} · "
        f"Issued: {(po.get('issued_at') or '')[:10]}"
    )

# ── Helper: render timeline messages ──────────────────────────────────────────
def _dot_class(sender, mtype):
    if mtype == "po":
        return "dot-po", "PO"
    if mtype == "rfq" or sender == "centrica_agent":
        return "dot-bot", "🤖"
    if sender == "buyer":
        return "dot-buyer", "👤"
    if mtype == "acceptance":
        return "dot-accept", "✓"
    if mtype == "rejection":
        return "dot-reject", "✗"
    return "dot-supplier", "🏢"


def render_messages(messages, show_sender=True):
    for msg in messages:
        dot_cls, icon = _dot_class(msg["sender"], msg.get("message_type", "chat"))
        ts = (msg.get("timestamp") or "")[:16].replace("T", " ")
        sender_label = msg["sender"]
        content = msg["content"].replace("\n", "<br>")

        st.markdown(f"""
        <div class="timeline-item">
            <div class="timeline-dot {dot_cls}">{icon}</div>
            <div class="msg-bubble">
                <div class="msg-meta">{"<b>" + sender_label + "</b> · " if show_sender else ""}{ts}</div>
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Tab layout: intake | per-supplier | all messages ──────────────────────────
tab1, tab2, tab3 = st.tabs(["💬 Business User Chat", "🏢 Supplier Negotiations", "📜 Full Log"])

with tab1:
    st.markdown('<div class="section-header">Business User Chat</div>', unsafe_allow_html=True)
    intake_msgs = [m for m in db.get_messages_for_request(request_id) if not m.get("negotiation_id")]
    if intake_msgs:
        render_messages(intake_msgs)
    else:
        st.info("No intake conversation recorded for this request.")

with tab2:
    if not negotiations:
        st.info("No supplier negotiations found for this request.")
    else:
        for neg in negotiations:
            is_winner = bool(neg.get("winner"))
            label = f"{'🏆 WINNER — ' if is_winner else ''}{neg['supplier_name']} ({neg.get('supplier_type','').title()})"
            border_color = "#85DB9C" if is_winner else "#E5E7EB"
            with st.expander(label, expanded=is_winner):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Initial Offer", f"£{neg.get('initial_price', 0):,.0f}")
                col2.metric("Agreed / Final", f"£{neg.get('agreed_price', 0) or neg.get('current_offer', 0):,.0f}")
                col3.metric("Strategy", (neg.get("strategy") or "—").title())
                col4.metric("Rounds", neg.get("round_number") or 1)

                if is_winner and neg.get("savings"):
                    st.markdown(f"**💰 Savings: £{neg['savings']:,.0f}** | Payment: {neg.get('payment_terms','—')} | Delivery: {neg.get('delivery_days','—')} days")

                neg_msgs = db.get_messages_for_negotiation(neg["id"])
                if neg_msgs:
                    render_messages(neg_msgs, show_sender=True)
                else:
                    st.info("No messages recorded for this negotiation.")

with tab3:
    st.markdown('<div class="section-header">Complete Audit Log — All Messages</div>', unsafe_allow_html=True)
    all_msgs = db.get_messages_for_request(request_id)
    if all_msgs:
        # Sort by timestamp
        all_msgs_sorted = sorted(all_msgs, key=lambda m: m.get("timestamp") or "")
        render_messages(all_msgs_sorted, show_sender=True)
    else:
        st.info("No messages recorded.")

    st.markdown("---")
    st.caption(f"Total messages: {len(all_msgs)} · Request ID: {request_id} · Supplier negotiations: {len(negotiations)}")

# ── Export note ────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("This audit trail is stored in SQLite and includes all buyer intake messages, RFQs, offer rounds, counter-offers, acceptances, rejections, and PO issuance. Compliant with Centrica procurement audit requirements.")
