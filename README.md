# Centrica Tail-Spend Agent Demo

Autonomous procurement agent that guides buyers through a chat, scouts suppliers, negotiates automatically, and issues a PO.

## Quick Start (Windows)

**Option A — double-click:**
```
install_and_run.bat
```

**Option B — manual:**
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt   # or: pip install openai streamlit plotly python-dotenv pydantic tenacity python-docx
cp .env.example .env              # then paste your OpenAI key into .env
streamlit run app.py
```

Open **http://localhost:8501**

## Pages

| Page | Who uses it | What it shows |
|---|---|---|
| 🛒 New Purchase Request | Buyer (internal Centrica staff) | Guided chat → agent auto-sources and negotiates |
| 🔄 Live Negotiation | Anyone | Real-time 3-supplier negotiation view |
| 📊 Stakeholder Dashboard | Centrica stakeholders | Spend by category, savings, KPIs, all deals table |
| 🔍 Audit Trail | Category Managers, compliance | Full conversation log per request |

## Demo Flow

1. Open the app → go to **New Purchase Request**
2. Enter your name and department → click **Start Chat**
3. Describe what you want to buy (the bot will ask follow-up questions)
4. Once intake is complete, the agent automatically:
   - Identifies 1 Centrica-approved existing supplier
   - Scouts 2 additional market suppliers
   - Sends RFQ to all 3 simultaneously
   - Runs up to 3 negotiation rounds per supplier
   - Awards the contract to the best accepted offer
   - Issues a mock Purchase Order
5. View the negotiation in **Live Negotiation**
6. See spend analytics in **Stakeholder Dashboard**
7. Review full audit in **Audit Trail**

## Configuration

Copy `.env.example` to `.env` and set:
```
OPENAI_API_KEY=sk-proj-...
```

The app runs in **demo mode** without an API key (scripted bot responses, no live AI).

## Demo Data

10 pre-seeded negotiations across 8 categories are loaded on first run:
- IT Equipment & Software (2 deals — £47k + £173k)
- Facilities Management (2 deals — £84k + £50k)
- Professional Services (£120k)
- Fleet & Transport (£34k)
- Engineering & Maintenance (active — £72k)
- Office Supplies & Furniture (£24k)
- Health & Safety (£12k)
- Marketing (escalated — high risk)

Total seeded spend: ~£556k | Total savings: ~£55k (~9.4% avg)
