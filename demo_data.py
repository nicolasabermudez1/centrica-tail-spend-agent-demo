"""
Seeds the SQLite database with realistic Centrica-flavoured demo data.
Run once at app startup if the DB is empty.
"""
from datetime import datetime, timedelta
import uuid
import database as db


# ── Existing Centrica-approved suppliers ───────────────────────────────────────

EXISTING_SUPPLIERS = [
    {
        "id": "sup-exist-001",
        "name": "Integral UK Ltd",
        "type": "existing",
        "category": "Facilities Management",
        "contact_email": "procurement@integral.co.uk",
        "location": "Birmingham, UK",
        "accreditations": "ISO 9001, ISO 14001, SafeContractor",
        "rating": 4.3,
        "source": "approved_list",
        "description": "Established FM provider with 12-year Centrica relationship. Strong on HVAC, electrical, and planned maintenance.",
    },
    {
        "id": "sup-exist-002",
        "name": "XMA Technology Ltd",
        "type": "existing",
        "category": "IT Equipment & Software",
        "contact_email": "centrica@xma.co.uk",
        "location": "Nottingham, UK",
        "accreditations": "ISO 27001, Cyber Essentials Plus",
        "rating": 4.6,
        "source": "approved_list",
        "description": "Preferred IT hardware & software reseller. Volume agreements in place for Dell, HP, and Microsoft.",
    },
    {
        "id": "sup-exist-003",
        "name": "DWF Law LLP",
        "type": "existing",
        "category": "Professional Services",
        "contact_email": "centrica@dwf.law",
        "location": "London, UK",
        "accreditations": "SRA Regulated, ISO 27001",
        "rating": 4.4,
        "source": "approved_list",
        "description": "Panel law firm for commercial and regulatory matters. Pre-agreed blended rate card in place.",
    },
    {
        "id": "sup-exist-004",
        "name": "Senator Group",
        "type": "existing",
        "category": "Office Supplies & Furniture",
        "contact_email": "contracts@senator-group.com",
        "location": "Nelson, Lancashire, UK",
        "accreditations": "ISO 9001, FIRA Gold",
        "rating": 4.1,
        "source": "approved_list",
        "description": "UK manufacturer of office furniture. Framework agreement covering desks, seating, storage.",
    },
    {
        "id": "sup-exist-005",
        "name": "Speedy Hire PLC",
        "type": "existing",
        "category": "Engineering & Maintenance",
        "contact_email": "national.accounts@speedyhire.co.uk",
        "location": "Newton-le-Willows, UK",
        "accreditations": "ISO 9001, ISO 45001, RISQS",
        "rating": 4.2,
        "source": "approved_list",
        "description": "Plant hire and engineering equipment. National coverage with 24/7 emergency response.",
    },
    {
        "id": "sup-exist-006",
        "name": "Arval UK Ltd",
        "type": "existing",
        "category": "Fleet & Transport",
        "contact_email": "centrica@arval.co.uk",
        "location": "Swindon, UK",
        "accreditations": "ISO 9001, BVRLA Member",
        "rating": 4.5,
        "source": "approved_list",
        "description": "Fleet management and vehicle leasing. Current contract covers 1,200+ Centrica vehicles.",
    },
    {
        "id": "sup-exist-007",
        "name": "Lyreco UK & Ireland",
        "type": "existing",
        "category": "Health & Safety Equipment",
        "contact_email": "business@lyreco.com",
        "location": "Telford, UK",
        "accreditations": "ISO 9001, ISO 14001",
        "rating": 4.0,
        "source": "approved_list",
        "description": "Workplace products including PPE, safety supplies, and office consumables.",
    },
    {
        "id": "sup-exist-008",
        "name": "Wunderman Thompson",
        "type": "existing",
        "category": "Marketing & Communications",
        "contact_email": "centrica@wundermanthompson.com",
        "location": "London, UK",
        "accreditations": "ISO 27001",
        "rating": 4.2,
        "source": "approved_list",
        "description": "Creative and digital marketing agency. On-roster for British Gas and Centrica brand campaigns.",
    },
]

# ── Demo requests + full negotiation histories ────────────────────────────────

def _ts(days_ago, hour=9, minute=0):
    dt = datetime.utcnow() - timedelta(days=days_ago)
    return dt.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()


DEMO_SCENARIOS = [
    # ── 1. IT Laptops – COMPLETED ──────────────────────────────────────────────
    {
        "request": {
            "id": "req-001",
            "buyer_name": "Sarah Mitchell",
            "buyer_department": "Digital Technology",
            "business_unit": "British Gas Services",
            "category": "IT Equipment & Software",
            "subcategory": "Laptops & Peripherals",
            "description": "50 Dell Latitude 5540 laptops for new field engineer cohort starting in Sheffield. Requires Windows 11 Pro, 16GB RAM, 512GB SSD. Delivery required before onboarding date.",
            "quantity": 50,
            "unit": "units",
            "max_budget": 52500.00,
            "required_by": "2026-06-15",
            "priority": "urgent",
            "risk_tier": "low",
            "status": "completed",
            "created_at": _ts(21),
            "updated_at": _ts(18),
        },
        "existing_supplier": "sup-exist-002",
        "scouted_suppliers": [
            {
                "id": "sup-scout-001a",
                "name": "Insight Direct (UK) Ltd",
                "type": "scouted",
                "category": "IT Equipment & Software",
                "contact_email": "quotes@insight.com",
                "location": "Coventry, UK",
                "accreditations": "ISO 9001, Cyber Essentials",
                "rating": 4.4,
                "source": "internet_scout",
                "description": "Leading IT solutions provider. Strong volume pricing on Dell and Lenovo hardware.",
            },
            {
                "id": "sup-scout-001b",
                "name": "Stone Group International",
                "type": "scouted",
                "category": "IT Equipment & Software",
                "contact_email": "enterprise@stonegroup.co.uk",
                "location": "Stafford, UK",
                "accreditations": "ISO 9001, ISO 14001",
                "rating": 4.1,
                "source": "internet_scout",
                "description": "UK IT manufacturer and reseller. Public sector specialist with competitive bulk pricing.",
            },
        ],
        "negotiations": [
            {"supplier_id": "sup-exist-002", "strategy": "terms-flex",
             "initial_price": 49500.00, "centrica_target": 46000.00,
             "agreed_price": 47250.00, "payment_terms": "Net 45",
             "delivery_days": 7, "winner": True, "savings": 5250.00},
            {"supplier_id": "sup-scout-001a", "strategy": "price-firm",
             "initial_price": 51000.00, "centrica_target": 46000.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 10, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-001b", "strategy": "walk-away",
             "initial_price": 53500.00, "centrica_target": 46000.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 14, "winner": False, "savings": 0},
        ],
    },

    # ── 2. HVAC Maintenance Contract – COMPLETED ───────────────────────────────
    {
        "request": {
            "id": "req-002",
            "buyer_name": "Tom Hendricks",
            "buyer_department": "Facilities & Real Estate",
            "business_unit": "Centrica plc",
            "category": "Facilities Management",
            "subcategory": "HVAC Maintenance",
            "description": "Annual HVAC planned preventive maintenance for Windsor HQ campus (6 buildings, 240 AHUs). Includes quarterly inspections, 24/7 reactive callout within 4-hour SLA.",
            "quantity": 1,
            "unit": "contract/year",
            "max_budget": 92000.00,
            "required_by": "2026-04-01",
            "priority": "standard",
            "risk_tier": "medium",
            "status": "completed",
            "created_at": _ts(45),
            "updated_at": _ts(40),
        },
        "existing_supplier": "sup-exist-001",
        "scouted_suppliers": [
            {
                "id": "sup-scout-002a",
                "name": "Mitie Group PLC",
                "type": "scouted",
                "category": "Facilities Management",
                "contact_email": "bids@mitie.com",
                "location": "London, UK",
                "accreditations": "ISO 9001, ISO 45001, SafeContractor",
                "rating": 4.3,
                "source": "internet_scout",
                "description": "FTSE 250 FM provider. National coverage, strong in commercial and energy sector facilities.",
            },
            {
                "id": "sup-scout-002b",
                "name": "Dalkia Engineering Services",
                "type": "scouted",
                "category": "Facilities Management",
                "contact_email": "contracts@dalkia.co.uk",
                "location": "Manchester, UK",
                "accreditations": "ISO 9001, REFCOM Elite",
                "rating": 4.0,
                "source": "internet_scout",
                "description": "Specialist M&E and HVAC engineering. EDF Energy subsidiary with strong utility sector track record.",
            },
        ],
        "negotiations": [
            {"supplier_id": "sup-exist-001", "strategy": "terms-flex",
             "initial_price": 88500.00, "centrica_target": 82000.00,
             "agreed_price": 84200.00, "payment_terms": "Net 30, monthly",
             "delivery_days": 0, "winner": True, "savings": 7800.00},
            {"supplier_id": "sup-scout-002a", "strategy": "price-firm",
             "initial_price": 91000.00, "centrica_target": 82000.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 0, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-002b", "strategy": "terms-flex",
             "initial_price": 86000.00, "centrica_target": 82000.00,
             "agreed_price": 85500.00, "payment_terms": "Net 45",
             "delivery_days": 0, "winner": False, "savings": 0},
        ],
    },

    # ── 3. Legal Consulting – COMPLETED ───────────────────────────────────────
    {
        "request": {
            "id": "req-003",
            "buyer_name": "Claire Dunmore",
            "buyer_department": "Legal & Regulatory",
            "business_unit": "Centrica plc",
            "category": "Professional Services",
            "subcategory": "Legal Consulting",
            "description": "Commercial contract review and regulatory advisory for new Ofgem licence condition changes. Estimated 400 partner hours, 600 associate hours over 6 months.",
            "quantity": 1000,
            "unit": "hours",
            "max_budget": 135000.00,
            "required_by": "2026-05-01",
            "priority": "urgent",
            "risk_tier": "medium",
            "status": "completed",
            "created_at": _ts(60),
            "updated_at": _ts(54),
        },
        "existing_supplier": "sup-exist-003",
        "scouted_suppliers": [
            {
                "id": "sup-scout-003a",
                "name": "Addleshaw Goddard LLP",
                "type": "scouted",
                "category": "Professional Services",
                "contact_email": "energy@addleshawgoddard.com",
                "location": "Leeds / London, UK",
                "accreditations": "SRA Regulated, ISO 27001",
                "rating": 4.5,
                "source": "internet_scout",
                "description": "Top-20 UK law firm with specialist energy and utilities practice. Competitive on blended rate cards.",
            },
            {
                "id": "sup-scout-003b",
                "name": "Osborne Clarke LLP",
                "type": "scouted",
                "category": "Professional Services",
                "contact_email": "energy@osborneclarke.com",
                "location": "Bristol / London, UK",
                "accreditations": "SRA Regulated",
                "rating": 4.3,
                "source": "internet_scout",
                "description": "International firm with deep energy transition expertise. Known for innovative fee arrangements.",
            },
        ],
        "negotiations": [
            {"supplier_id": "sup-exist-003", "strategy": "terms-flex",
             "initial_price": 130000.00, "centrica_target": 118000.00,
             "agreed_price": 119500.00, "payment_terms": "Monthly milestone",
             "delivery_days": 0, "winner": True, "savings": 15500.00},
            {"supplier_id": "sup-scout-003a", "strategy": "price-firm",
             "initial_price": 128000.00, "centrica_target": 118000.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 0, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-003b", "strategy": "terms-flex",
             "initial_price": 122000.00, "centrica_target": 118000.00,
             "agreed_price": 120800.00, "payment_terms": "Net 30",
             "delivery_days": 0, "winner": False, "savings": 0},
        ],
    },

    # ── 4. Standing Desks – COMPLETED ─────────────────────────────────────────
    {
        "request": {
            "id": "req-004",
            "buyer_name": "Paul Watkins",
            "buyer_department": "Workplace Experience",
            "business_unit": "British Gas Services",
            "category": "Office Supplies & Furniture",
            "subcategory": "Height-Adjustable Desks",
            "description": "60 sit-stand desks for Manchester office refurbishment (Activity-Based Working project). Electric adjustment, 180x80cm worktop, Centrica navy frame preferred.",
            "quantity": 60,
            "unit": "units",
            "max_budget": 26400.00,
            "required_by": "2026-03-28",
            "priority": "standard",
            "risk_tier": "low",
            "status": "completed",
            "created_at": _ts(55),
            "updated_at": _ts(50),
        },
        "existing_supplier": "sup-exist-004",
        "scouted_suppliers": [
            {
                "id": "sup-scout-004a",
                "name": "Orangebox Ltd",
                "type": "scouted",
                "category": "Office Supplies & Furniture",
                "contact_email": "projects@orangebox.com",
                "location": "Nantgarw, Wales, UK",
                "accreditations": "ISO 9001, FIRA",
                "rating": 4.4,
                "source": "internet_scout",
                "description": "Premium workplace furniture designer. Strong ABW credentials and bespoke colour options.",
            },
            {
                "id": "sup-scout-004b",
                "name": "Connection (formerly Samas)",
                "type": "scouted",
                "category": "Office Supplies & Furniture",
                "contact_email": "contracts@connection.co.uk",
                "location": "Corsham, Wiltshire, UK",
                "accreditations": "ISO 9001",
                "rating": 3.9,
                "source": "internet_scout",
                "description": "Volume office furniture supplier. Competitive pricing on bulk orders with fast lead times.",
            },
        ],
        "negotiations": [
            {"supplier_id": "sup-exist-004", "strategy": "terms-flex",
             "initial_price": 25800.00, "centrica_target": 23500.00,
             "agreed_price": 24300.00, "payment_terms": "Net 60",
             "delivery_days": 21, "winner": True, "savings": 2100.00},
            {"supplier_id": "sup-scout-004a", "strategy": "price-firm",
             "initial_price": 27600.00, "centrica_target": 23500.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 28, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-004b", "strategy": "walk-away",
             "initial_price": 24900.00, "centrica_target": 23500.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 14, "winner": False, "savings": 0},
        ],
    },

    # ── 5. Server Upgrade – COMPLETED ─────────────────────────────────────────
    {
        "request": {
            "id": "req-005",
            "buyer_name": "Raj Patel",
            "buyer_department": "Infrastructure & Cloud",
            "business_unit": "British Gas Connected Home",
            "category": "IT Equipment & Software",
            "subcategory": "Server & Storage",
            "description": "4× Dell PowerEdge R760 rack servers + 2× Dell PowerVault ME5024 storage arrays for Peterborough data centre expansion (Hive smart home platform capacity increase).",
            "quantity": 6,
            "unit": "units",
            "max_budget": 195000.00,
            "required_by": "2026-05-30",
            "priority": "urgent",
            "risk_tier": "medium",
            "status": "completed",
            "created_at": _ts(35),
            "updated_at": _ts(30),
        },
        "existing_supplier": "sup-exist-002",
        "scouted_suppliers": [
            {
                "id": "sup-scout-005a",
                "name": "CDW UK Ltd",
                "type": "scouted",
                "category": "IT Equipment & Software",
                "contact_email": "enterprise@uk.cdw.com",
                "location": "London, UK",
                "accreditations": "ISO 9001, ISO 27001",
                "rating": 4.5,
                "source": "internet_scout",
                "description": "Global IT solutions provider. Direct Dell partner with strong data centre practice.",
            },
            {
                "id": "sup-scout-005b",
                "name": "Computacenter PLC",
                "type": "scouted",
                "category": "IT Equipment & Software",
                "contact_email": "public.sector@computacenter.com",
                "location": "Hatfield, UK",
                "accreditations": "ISO 9001, ISO 27001, Cyber Essentials Plus",
                "rating": 4.6,
                "source": "internet_scout",
                "description": "FTSE 250 IT infrastructure group. Premier Dell partner with managed deployment services.",
            },
        ],
        "negotiations": [
            {"supplier_id": "sup-exist-002", "strategy": "terms-flex",
             "initial_price": 189500.00, "centrica_target": 173000.00,
             "agreed_price": 175000.00, "payment_terms": "Net 60",
             "delivery_days": 10, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-005a", "strategy": "price-firm",
             "initial_price": 184000.00, "centrica_target": 173000.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 14, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-005b", "strategy": "terms-flex",
             "initial_price": 181000.00, "centrica_target": 173000.00,
             "agreed_price": 173000.00, "payment_terms": "Net 45 + 3% early pay",
             "delivery_days": 7, "winner": True, "savings": 22000.00},
        ],
    },

    # ── 6. Vehicle Servicing – COMPLETED ──────────────────────────────────────
    {
        "request": {
            "id": "req-006",
            "buyer_name": "Karen Hollis",
            "buyer_department": "Fleet Operations",
            "business_unit": "British Gas Services",
            "category": "Fleet & Transport",
            "subcategory": "Vehicle Servicing & MOT",
            "description": "Annual service, MOT, and tyre replacement programme for 180-vehicle north-east region fleet (vans and LCVs). Must include mobile servicing at depots.",
            "quantity": 180,
            "unit": "vehicles",
            "max_budget": 37800.00,
            "required_by": "2026-04-30",
            "priority": "standard",
            "risk_tier": "low",
            "status": "completed",
            "created_at": _ts(50),
            "updated_at": _ts(45),
        },
        "existing_supplier": "sup-exist-006",
        "scouted_suppliers": [
            {
                "id": "sup-scout-006a",
                "name": "ATS Euromaster Ltd",
                "type": "scouted",
                "category": "Fleet & Transport",
                "contact_email": "fleet@ats-euromaster.co.uk",
                "location": "Coventry, UK",
                "accreditations": "ISO 9001, DVSA Authorised",
                "rating": 4.2,
                "source": "internet_scout",
                "description": "National fleet service network with 350+ locations. Competitive tyre pricing and mobile unit capability.",
            },
            {
                "id": "sup-scout-006b",
                "name": "Halfords Autocentre",
                "type": "scouted",
                "category": "Fleet & Transport",
                "contact_email": "fleetaccounts@halfords.co.uk",
                "location": "Redditch, UK",
                "accreditations": "DVSA Authorised, ISO 9001",
                "rating": 3.8,
                "source": "internet_scout",
                "description": "600+ UK service centres. B2B fleet accounts with consolidated billing and online booking.",
            },
        ],
        "negotiations": [
            {"supplier_id": "sup-exist-006", "strategy": "terms-flex",
             "initial_price": 36500.00, "centrica_target": 33800.00,
             "agreed_price": 34000.00, "payment_terms": "Net 30, monthly",
             "delivery_days": 0, "winner": True, "savings": 3800.00},
            {"supplier_id": "sup-scout-006a", "strategy": "price-firm",
             "initial_price": 35200.00, "centrica_target": 33800.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 0, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-006b", "strategy": "walk-away",
             "initial_price": 39500.00, "centrica_target": 33800.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 0, "winner": False, "savings": 0},
        ],
    },

    # ── 7. PPE / Health & Safety – COMPLETED ──────────────────────────────────
    {
        "request": {
            "id": "req-007",
            "buyer_name": "Dave Ashworth",
            "buyer_department": "Health, Safety & Environment",
            "business_unit": "Centrica Energy Storage",
            "category": "Health & Safety Equipment",
            "subcategory": "PPE & Safety Consumables",
            "description": "Annual PPE stock replenishment: hard hats (EN397), safety boots (EN ISO 20345 S3), hi-vis vests, cut-resistant gloves, safety glasses. For 320 field engineers.",
            "quantity": 320,
            "unit": "sets",
            "max_budget": 13500.00,
            "required_by": "2026-06-01",
            "priority": "standard",
            "risk_tier": "low",
            "status": "completed",
            "created_at": _ts(30),
            "updated_at": _ts(26),
        },
        "existing_supplier": "sup-exist-007",
        "scouted_suppliers": [
            {
                "id": "sup-scout-007a",
                "name": "JSP Ltd",
                "type": "scouted",
                "category": "Health & Safety Equipment",
                "contact_email": "sales@jsp.co.uk",
                "location": "Chipping Norton, UK",
                "accreditations": "ISO 9001, CE marked products",
                "rating": 4.3,
                "source": "internet_scout",
                "description": "UK PPE manufacturer. Own-brand certified head, eye and respiratory protection. Direct pricing advantage.",
            },
            {
                "id": "sup-scout-007b",
                "name": "Safety Supply Direct Ltd",
                "type": "scouted",
                "category": "Health & Safety Equipment",
                "contact_email": "accounts@safetysupplydirect.co.uk",
                "location": "Leeds, UK",
                "accreditations": "ISO 9001",
                "rating": 3.7,
                "source": "internet_scout",
                "description": "Online PPE distributor. Very competitive on volume orders, fast fulfilment from UK warehouse.",
            },
        ],
        "negotiations": [
            {"supplier_id": "sup-exist-007", "strategy": "terms-flex",
             "initial_price": 13200.00, "centrica_target": 11800.00,
             "agreed_price": 12300.00, "payment_terms": "Net 45",
             "delivery_days": 5, "winner": True, "savings": 1200.00},
            {"supplier_id": "sup-scout-007a", "strategy": "price-firm",
             "initial_price": 12800.00, "centrica_target": 11800.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 7, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-007b", "strategy": "terms-flex",
             "initial_price": 11500.00, "centrica_target": 11800.00,
             "agreed_price": 11500.00, "payment_terms": "Prepay -2%",
             "delivery_days": 3, "winner": False, "savings": 0},
        ],
    },

    # ── 8. Office Cleaning – COMPLETED ────────────────────────────────────────
    {
        "request": {
            "id": "req-008",
            "buyer_name": "Angela Price",
            "buyer_department": "Facilities & Real Estate",
            "business_unit": "Centrica plc",
            "category": "Facilities Management",
            "subcategory": "Cleaning Services",
            "description": "Daily office cleaning contract for Staines and Stockport offices (combined 12,000 sqm). Includes washroom, window cleaning quarterly, deep clean twice yearly. 3-year contract.",
            "quantity": 3,
            "unit": "years",
            "max_budget": 55000.00,
            "required_at": "2026-03-01",
            "priority": "standard",
            "risk_tier": "low",
            "status": "completed",
            "created_at": _ts(70),
            "updated_at": _ts(65),
        },
        "existing_supplier": "sup-exist-001",
        "scouted_suppliers": [
            {
                "id": "sup-scout-008a",
                "name": "Atalian Servest",
                "type": "scouted",
                "category": "Facilities Management",
                "contact_email": "bids@atalianservest.co.uk",
                "location": "Chertsey, UK",
                "accreditations": "ISO 9001, ISO 14001, Living Wage Employer",
                "rating": 4.1,
                "source": "internet_scout",
                "description": "Large FM group with strong cleaning division. Sustainability credentials and detailed service reporting.",
            },
            {
                "id": "sup-scout-008b",
                "name": "Elior UK",
                "type": "scouted",
                "category": "Facilities Management",
                "contact_email": "fm@elior.co.uk",
                "location": "London, UK",
                "accreditations": "ISO 9001, ISO 14001",
                "rating": 4.0,
                "source": "internet_scout",
                "description": "Integrated FM and catering group. Competitive 3-year contract pricing with performance SLA framework.",
            },
        ],
        "negotiations": [
            {"supplier_id": "sup-exist-001", "strategy": "terms-flex",
             "initial_price": 53500.00, "centrica_target": 48000.00,
             "agreed_price": 49800.00, "payment_terms": "Monthly, Net 30",
             "delivery_days": 0, "winner": True, "savings": 5200.00},
            {"supplier_id": "sup-scout-008a", "strategy": "terms-flex",
             "initial_price": 51000.00, "centrica_target": 48000.00,
             "agreed_price": 50200.00, "payment_terms": "Monthly",
             "delivery_days": 0, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-008b", "strategy": "walk-away",
             "initial_price": 58000.00, "centrica_target": 48000.00,
             "agreed_price": None, "payment_terms": "Monthly",
             "delivery_days": 0, "winner": False, "savings": 0},
        ],
    },

    # ── 9. Digital Signage – ESCALATED (high risk) ────────────────────────────
    {
        "request": {
            "id": "req-009",
            "buyer_name": "Fiona Lester",
            "buyer_department": "Brand & Marketing",
            "business_unit": "British Gas Services",
            "category": "Marketing & Communications",
            "subcategory": "Digital Signage & AV",
            "description": "75× 55-inch 4K commercial display installation across 14 BGS regional offices for internal comms and safety messaging. Includes content management system licence and 3-year maintenance.",
            "quantity": 75,
            "unit": "units",
            "max_budget": 310000.00,
            "required_by": "2026-07-01",
            "priority": "standard",
            "risk_tier": "high",
            "status": "escalated",
            "created_at": _ts(14),
            "updated_at": _ts(13),
        },
        "existing_supplier": "sup-exist-008",
        "scouted_suppliers": [
            {
                "id": "sup-scout-009a",
                "name": "Kinetic Digital UK",
                "type": "scouted",
                "category": "Marketing & Communications",
                "contact_email": "projects@kineticdigital.co.uk",
                "location": "London, UK",
                "accreditations": "ISO 9001",
                "rating": 4.2,
                "source": "internet_scout",
                "description": "Digital signage specialist with enterprise CMS platform. Strong retail and corporate sector track record.",
            },
            {
                "id": "sup-scout-009b",
                "name": "Signagelive Ltd",
                "type": "scouted",
                "category": "Marketing & Communications",
                "contact_email": "enterprise@signagelive.com",
                "location": "Cambridge, UK",
                "accreditations": "ISO 27001",
                "rating": 4.0,
                "source": "internet_scout",
                "description": "Cloud-based digital signage platform provider. Samsung and LG certified. Competitive SaaS licensing model.",
            },
        ],
        "negotiations": [],
    },

    # ── 10. Transformer Maintenance – ACTIVE (negotiating) ────────────────────
    {
        "request": {
            "id": "req-010",
            "buyer_name": "Mike Torres",
            "buyer_department": "Asset Management",
            "business_unit": "Centrica Energy Storage",
            "category": "Engineering & Maintenance",
            "subcategory": "Electrical Equipment Maintenance",
            "description": "Inspection, testing, and refurbishment of 8 power transformers (11kV/415V, 500–1000 kVA) at Rough storage facility. Includes thermal imaging, oil sampling, bushing replacement where required.",
            "quantity": 8,
            "unit": "transformers",
            "max_budget": 72000.00,
            "required_by": "2026-07-15",
            "priority": "urgent",
            "risk_tier": "medium",
            "status": "negotiating",
            "created_at": _ts(3),
            "updated_at": _ts(1),
        },
        "existing_supplier": "sup-exist-005",
        "scouted_suppliers": [
            {
                "id": "sup-scout-010a",
                "name": "Wilson Power Solutions",
                "type": "scouted",
                "category": "Engineering & Maintenance",
                "contact_email": "contracts@wilson-power.com",
                "location": "Leeds, UK",
                "accreditations": "ISO 9001, ISO 45001, NICEIC",
                "rating": 4.4,
                "source": "internet_scout",
                "description": "Transformer specialist with 40 years experience. Own test lab, 24/7 emergency response.",
            },
            {
                "id": "sup-scout-010b",
                "name": "Brush Transformers Ltd",
                "type": "scouted",
                "category": "Engineering & Maintenance",
                "contact_email": "service@brushtransformers.com",
                "location": "Loughborough, UK",
                "accreditations": "ISO 9001, ISO 14001, BS EN 60076",
                "rating": 4.6,
                "source": "internet_scout",
                "description": "OEM and independent transformer manufacturer and servicer. Preferred partner for National Grid.",
            },
        ],
        "negotiations": [
            {"supplier_id": "sup-exist-005", "strategy": "terms-flex",
             "initial_price": 69500.00, "centrica_target": 63000.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 21, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-010a", "strategy": "price-firm",
             "initial_price": 71000.00, "centrica_target": 63000.00,
             "agreed_price": None, "payment_terms": "Net 30",
             "delivery_days": 28, "winner": False, "savings": 0},
            {"supplier_id": "sup-scout-010b", "strategy": "terms-flex",
             "initial_price": 67500.00, "centrica_target": 63000.00,
             "agreed_price": None, "payment_terms": "Net 45",
             "delivery_days": 14, "winner": False, "savings": 0},
        ],
    },
]


def _neg_messages(request_id, neg_id, supplier_name, strategy, initial_price, target, agreed, is_active=False):
    """Build realistic negotiation message history for a supplier."""
    msgs = []
    ts_base = datetime.utcnow() - timedelta(days=20)

    msgs.append({
        "request_id": request_id,
        "negotiation_id": neg_id,
        "sender": "centrica_agent",
        "content": (
            f"RFQ sent to {supplier_name}. Request for quotation issued. "
            f"Centrica target price: £{target:,.0f}. Awaiting initial offer."
        ),
        "message_type": "rfq",
        "timestamp": (ts_base + timedelta(minutes=2)).isoformat(),
    })

    msgs.append({
        "request_id": request_id,
        "negotiation_id": neg_id,
        "sender": supplier_name,
        "content": (
            f"Thank you for the RFQ. We are pleased to submit our initial offer of £{initial_price:,.2f}. "
            "This includes all specified requirements, delivery within our standard lead time, and our standard Net 30 payment terms. "
            "We look forward to working with Centrica."
        ),
        "message_type": "offer",
        "timestamp": (ts_base + timedelta(hours=4)).isoformat(),
    })

    if strategy == "walk-away" or (initial_price > target * 1.08 and not agreed):
        msgs.append({
            "request_id": request_id,
            "negotiation_id": neg_id,
            "sender": "centrica_agent",
            "content": (
                f"Counter-offer submitted: £{target * 1.04:,.2f}. Centrica requires a reduction of "
                f"approximately {((initial_price - target) / initial_price * 100):.1f}% to align with our budget envelope. "
                "We remain open to discussion on payment terms if price flexibility is limited."
            ),
            "message_type": "counter",
            "timestamp": (ts_base + timedelta(hours=6)).isoformat(),
        })
        if strategy == "walk-away":
            msgs.append({
                "request_id": request_id,
                "negotiation_id": neg_id,
                "sender": supplier_name,
                "content": (
                    "We have reviewed your counter-offer carefully. Unfortunately, our cost base does not allow us "
                    "to reduce beyond our initial submission without compromising quality and service levels. "
                    "We must respectfully withdraw from this tender. We hope to work with Centrica on future opportunities."
                ),
                "message_type": "rejection",
                "timestamp": (ts_base + timedelta(hours=8)).isoformat(),
            })
        else:
            msgs.append({
                "request_id": request_id,
                "negotiation_id": neg_id,
                "sender": supplier_name,
                "content": (
                    f"We appreciate your feedback. Our best and final offer is £{initial_price * 0.97:,.2f}. "
                    "We cannot move further on price but can offer Net 45 payment terms and include extended warranty at no charge. "
                    "This represents our maximum discount position."
                ),
                "message_type": "counter",
                "timestamp": (ts_base + timedelta(hours=10)).isoformat(),
            })
            msgs.append({
                "request_id": request_id,
                "negotiation_id": neg_id,
                "sender": "centrica_agent",
                "content": "Offer evaluated. Gap to target remains above threshold. This supplier was not selected for award.",
                "message_type": "rejection",
                "timestamp": (ts_base + timedelta(hours=12)).isoformat(),
            })

    elif agreed:
        msgs.append({
            "request_id": request_id,
            "negotiation_id": neg_id,
            "sender": "centrica_agent",
            "content": (
                f"Counter-offer submitted: £{agreed * 0.985:,.2f} with improved payment terms (Net 45). "
                "We ask you to consider an early payment discount of 2% for settlement within 10 days."
            ),
            "message_type": "counter",
            "timestamp": (ts_base + timedelta(hours=5)).isoformat(),
        })
        msgs.append({
            "request_id": request_id,
            "negotiation_id": neg_id,
            "sender": supplier_name,
            "content": (
                f"We are pleased to accept your revised terms. Final agreed price: £{agreed:,.2f} "
                f"with the payment schedule as discussed. We confirm our commitment to deliver within the agreed timeline."
            ),
            "message_type": "acceptance",
            "timestamp": (ts_base + timedelta(hours=7)).isoformat(),
        })
        msgs.append({
            "request_id": request_id,
            "negotiation_id": neg_id,
            "sender": "centrica_agent",
            "content": f"Agreement reached at £{agreed:,.2f}. PO will be issued within 24 hours. Supplier selected as WINNER.",
            "message_type": "acceptance",
            "timestamp": (ts_base + timedelta(hours=7, minutes=30)).isoformat(),
        })
    elif is_active:
        msgs.append({
            "request_id": request_id,
            "negotiation_id": neg_id,
            "sender": "centrica_agent",
            "content": (
                f"Counter-offer submitted: £{target * 1.02:,.2f}. Please review and respond at your earliest convenience."
            ),
            "message_type": "counter",
            "timestamp": (ts_base + timedelta(hours=5)).isoformat(),
        })

    return msgs


def seed_demo_data():
    """Insert all demo suppliers, requests, negotiations, messages and POs."""
    # 1. Existing suppliers
    for s in EXISTING_SUPPLIERS:
        db.insert_supplier(s)

    po_counter = 1
    for scenario in DEMO_SCENARIOS:
        req = scenario["request"]
        db.insert_request(req)

        # 2. Scouted suppliers
        for s in scenario.get("scouted_suppliers", []):
            db.insert_supplier(s)

        # 3. Intake conversation messages
        buyer_name = req["buyer_name"]
        ts0 = req["created_at"]
        db.insert_message({
            "request_id": req["id"],
            "sender": "bot",
            "content": f"Hello {buyer_name.split()[0]}! I'm your Centrica Procurement Agent. I'll help you source what you need quickly and at the best price. What are you looking to procure today?",
            "message_type": "chat",
            "timestamp": ts0,
        })
        db.insert_message({
            "request_id": req["id"],
            "sender": "buyer",
            "content": req["description"],
            "message_type": "chat",
            "timestamp": (datetime.fromisoformat(ts0) + timedelta(minutes=1)).isoformat(),
        })
        db.insert_message({
            "request_id": req["id"],
            "sender": "bot",
            "content": (
                f"Got it. I've classified this as **{req['category']}** with risk tier **{req['risk_tier'].upper()}**. "
                f"Budget validated at £{req.get('max_budget', 0):,.0f}. "
                "I'm now identifying your existing Centrica supplier and scouting 2 additional market options. "
                "The agent will run parallel negotiations and report back with the best deal."
            ),
            "message_type": "chat",
            "timestamp": (datetime.fromisoformat(ts0) + timedelta(minutes=2)).isoformat(),
        })

        # 4. Negotiations
        winner_neg_id = None
        winner_supplier_id = None
        winner_data = None

        for neg_data in scenario.get("negotiations", []):
            neg_id = f"neg-{req['id']}-{neg_data['supplier_id'][-4:]}"
            is_active = req["status"] == "negotiating"
            db.insert_negotiation({
                "id": neg_id,
                "request_id": req["id"],
                "supplier_id": neg_data["supplier_id"],
                "strategy": neg_data["strategy"],
                "initial_price": neg_data["initial_price"],
                "centrica_target": neg_data["centrica_target"],
                "payment_terms": neg_data["payment_terms"],
                "delivery_days": neg_data["delivery_days"],
                "status": "agreed" if neg_data.get("agreed_price") else ("active" if is_active else "rejected"),
                "created_at": req["created_at"],
                "updated_at": req["updated_at"],
            })

            if neg_data.get("agreed_price") or is_active:
                db.update_negotiation(neg_id, {
                    "current_offer": neg_data.get("agreed_price") or neg_data["initial_price"],
                    "agreed_price": neg_data.get("agreed_price"),
                    "winner": 1 if neg_data.get("winner") else 0,
                    "savings": neg_data.get("savings", 0),
                    "round_number": 2 if neg_data.get("agreed_price") else 1,
                    "discount_pct": round(
                        (neg_data["initial_price"] - (neg_data.get("agreed_price") or neg_data["initial_price"]))
                        / neg_data["initial_price"] * 100, 1
                    ),
                })

            # Messages
            supplier_row = next(
                (s for s in EXISTING_SUPPLIERS if s["id"] == neg_data["supplier_id"]),
                next((s for sc in DEMO_SCENARIOS for s in sc.get("scouted_suppliers", [])
                      if s["id"] == neg_data["supplier_id"]), None)
            )
            if supplier_row:
                for msg in _neg_messages(
                    req["id"], neg_id, supplier_row["name"],
                    neg_data["strategy"], neg_data["initial_price"],
                    neg_data["centrica_target"], neg_data.get("agreed_price"),
                    is_active=is_active,
                ):
                    db.insert_message(msg)

            if neg_data.get("winner"):
                winner_neg_id = neg_id
                winner_supplier_id = neg_data["supplier_id"]
                winner_data = neg_data

        # 5. PO for completed requests
        if req["status"] in ("completed", "awarded") and winner_data:
            agreed = winner_data["agreed_price"]
            savings = winner_data["savings"]
            db.insert_po({
                "id": f"po-{req['id']}",
                "request_id": req["id"],
                "supplier_id": winner_supplier_id,
                "negotiation_id": winner_neg_id,
                "po_number": f"PO-2026-{po_counter:04d}",
                "total_value": agreed,
                "payment_terms": winner_data["payment_terms"],
                "delivery_date": req.get("required_by", "2026-07-01"),
                "savings_vs_budget": savings,
                "savings_pct": round(savings / req["max_budget"] * 100, 1),
                "issued_at": req["updated_at"],
            })
            po_counter += 1
