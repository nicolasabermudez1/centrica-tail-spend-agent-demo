"""
Centrica Stakeholder Dashboard — spend analytics, savings, and all negotiations.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database as db
from demo_data import seed_demo_data

st.set_page_config(page_title="Stakeholder Dashboard | Centrica", page_icon="📊", layout="wide")

# ── Brand CSS ──────────────────────────────────────────────────────────────────
NAVY   = "#0F2067"
MINT   = "#85DB9C"
LAV    = "#B999F6"
PALE   = "#DECFFF"
PURPLE = "#9B2BF7"

CHART_COLORS = [NAVY, MINT, LAV, PURPLE, PALE, "#4F46E5", "#0EA5E9", "#F59E0B"]

st.markdown(f"""
<style>
:root {{ --navy:{NAVY}; --mint:{MINT}; --lav:{LAV}; --pale:{PALE}; --purple:{PURPLE}; }}
[data-testid="stSidebar"] {{ background: var(--navy) !important; }}
[data-testid="stSidebar"] * {{ color: white !important; }}
[data-testid="stSidebar"] a {{ color: var(--mint) !important; }}
.logo-text {{ font-size: 1.4rem; font-weight: 800; color: white; }}
.logo-sub  {{ font-size: 0.75rem; color: var(--mint); letter-spacing: 0.08em; font-weight: 500; }}

.kpi-card {{
    background: white;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    border: 1px solid #E5E7EB;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    height: 110px;
}}
.kpi-label {{ font-size: 0.75rem; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; }}
.kpi-value {{ font-size: 2rem; font-weight: 800; color: var(--navy); line-height: 1.15; margin-top: 4px; }}
.kpi-sub   {{ font-size: 0.82rem; color: #16A34A; font-weight: 600; }}

.section-header {{ font-size: 1.1rem; font-weight: 700; color: var(--navy); margin: 1.5rem 0 0.75rem; border-bottom: 2px solid var(--mint); padding-bottom: 4px; }}

table {{ width: 100%; border-collapse: collapse; }}
th {{ background: var(--navy); color: white; padding: 8px 12px; text-align: left; font-size: 0.82rem; font-weight: 600; }}
td {{ padding: 7px 12px; font-size: 0.85rem; border-bottom: 1px solid #F3F4F6; }}
tr:hover td {{ background: #F9FAFB; }}

.badge {{ display:inline-block; padding:2px 10px; border-radius:99px; font-size:0.75rem; font-weight:700; }}
.b-completed {{ background:#DCFCE7; color:#16A34A; }}
.b-negotiating {{ background:#FEF3C7; color:#D97706; }}
.b-escalated {{ background:#FEE2E2; color:#DC2626; }}
.b-intake {{ background:#EEF2FF; color:#4F46E5; }}
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

# ── Data ───────────────────────────────────────────────────────────────────────
metrics = db.get_dashboard_metrics()
spend_by_cat = db.get_spend_by_category()
all_requests = db.get_all_requests()

# ── Header ─────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("## 📊 Stakeholder Dashboard")
    st.caption("Real-time view of all Tail-Spend Agent activity — spend, savings, and negotiation outcomes.")
with col_h2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# ── KPI Row ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Key Metrics</div>', unsafe_allow_html=True)
k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Spend</div>
        <div class="kpi-value">£{metrics['total_spend']/1000:.0f}k</div>
        <div class="kpi-sub">Contracted via agent</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Savings</div>
        <div class="kpi-value" style="color:#16A34A;">£{metrics['total_savings']/1000:.0f}k</div>
        <div class="kpi-sub">vs. buyer budgets</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Avg Saving</div>
        <div class="kpi-value">{metrics['avg_savings_pct']:.1f}%</div>
        <div class="kpi-sub">per deal</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Deals Completed</div>
        <div class="kpi-value">{metrics['completed_deals']}</div>
        <div class="kpi-sub">POs issued</div>
    </div>""", unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Active Now</div>
        <div class="kpi-value" style="color:#D97706;">{metrics['active_negotiations']}</div>
        <div class="kpi-sub">negotiations</div>
    </div>""", unsafe_allow_html=True)

with k6:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Escalated</div>
        <div class="kpi-value" style="color:#DC2626;">{metrics['escalated']}</div>
        <div class="kpi-sub">to Category Manager</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts row ─────────────────────────────────────────────────────────────────
chart_col1, chart_col2 = st.columns([3, 2])

with chart_col1:
    st.markdown('<div class="section-header">Spend by Category</div>', unsafe_allow_html=True)
    if spend_by_cat:
        cats = [r["category"] for r in spend_by_cat]
        spends = [r["total_spend"] for r in spend_by_cat]
        savings_vals = [r["total_savings"] for r in spend_by_cat]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Contracted Spend",
            x=cats,
            y=spends,
            marker_color=NAVY,
            text=[f"£{v/1000:.0f}k" for v in spends],
            textposition="auto",
        ))
        fig.add_trace(go.Bar(
            name="Savings Achieved",
            x=cats,
            y=savings_vals,
            marker_color=MINT,
            text=[f"£{v/1000:.0f}k" for v in savings_vals],
            textposition="auto",
        ))
        fig.update_layout(
            barmode="group",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_family="Arial",
            margin=dict(t=20, b=40, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_tickangle=-25,
            height=320,
            yaxis=dict(tickprefix="£", tickformat=",.0f", gridcolor="#F3F4F6"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No completed deals yet.")

with chart_col2:
    st.markdown('<div class="section-header">Spend Distribution</div>', unsafe_allow_html=True)
    if spend_by_cat:
        fig2 = px.pie(
            values=[r["total_spend"] for r in spend_by_cat],
            names=[r["category"] for r in spend_by_cat],
            color_discrete_sequence=CHART_COLORS,
            hole=0.5,
        )
        fig2.update_layout(
            paper_bgcolor="white",
            font_family="Arial",
            margin=dict(t=20, b=10, l=10, r=10),
            height=320,
            legend=dict(font_size=11),
            showlegend=True,
        )
        fig2.update_traces(textinfo="percent", textfont_size=11)
        st.plotly_chart(fig2, use_container_width=True)

# ── Savings rate bar ───────────────────────────────────────────────────────────
if spend_by_cat:
    st.markdown('<div class="section-header">Average Savings Rate by Category</div>', unsafe_allow_html=True)
    fig3 = go.Figure(go.Bar(
        x=[r["category"] for r in spend_by_cat],
        y=[r["avg_savings_pct"] for r in spend_by_cat],
        marker_color=[PURPLE if v >= 8 else (MINT if v >= 5 else LAV) for v in [r["avg_savings_pct"] for r in spend_by_cat]],
        text=[f"{v:.1f}%" for v in [r["avg_savings_pct"] for r in spend_by_cat]],
        textposition="auto",
    ))
    fig3.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Arial",
        margin=dict(t=10, b=40, l=10, r=10),
        height=220,
        xaxis_tickangle=-20,
        yaxis=dict(ticksuffix="%", gridcolor="#F3F4F6", range=[0, 20]),
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── All negotiations table ─────────────────────────────────────────────────────
st.markdown('<div class="section-header">All Requests & Negotiations</div>', unsafe_allow_html=True)

if all_requests:
    status_badge = {
        "completed": '<span class="badge b-completed">Completed</span>',
        "awarded":   '<span class="badge b-completed">Awarded</span>',
        "negotiating": '<span class="badge b-negotiating">Negotiating</span>',
        "escalated": '<span class="badge b-escalated">Escalated</span>',
        "intake":    '<span class="badge b-intake">Intake</span>',
    }

    rows_html = ""
    for r in all_requests:
        badge = status_badge.get(r["status"], f'<span class="badge">{r["status"]}</span>')
        budget = f"£{r.get('max_budget', 0):,.0f}"
        spend = f"£{r.get('po_value') or 0:,.0f}" if r.get("po_value") else "—"
        savings = f"£{r.get('savings_vs_budget') or 0:,.0f}" if r.get("savings_vs_budget") else "—"
        savings_pct = f"{r.get('po_savings_pct') or 0:.1f}%" if r.get("po_savings_pct") else "—"
        rows_html += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{r['buyer_name']}</td>
            <td>{r.get('business_unit','—')}</td>
            <td><b>{r['category']}</b></td>
            <td>{r['description'][:55]}{'...' if len(r.get('description',''))>55 else ''}</td>
            <td>{budget}</td>
            <td>{spend}</td>
            <td><b style="color:#16A34A;">{savings}</b></td>
            <td>{savings_pct}</td>
            <td>{badge}</td>
            <td>{(r.get('created_at') or '')[:10]}</td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table>
        <thead>
            <tr>
                <th>ID</th><th>Buyer</th><th>Business Unit</th><th>Category</th>
                <th>Description</th><th>Budget</th><th>Contracted</th>
                <th>Savings £</th><th>Savings %</th><th>Status</th><th>Date</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("No requests yet.")

st.markdown("---")
st.caption("Data refreshed from live SQLite database. All negotiations auditable in 🔍 Audit Trail.")
