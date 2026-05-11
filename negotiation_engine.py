"""
Autonomous negotiation engine — 4-agent demo conversation.

Roles:
  • Centrica Procurement Agent — sources, sends RFQ, counter-offers, awards PO.
  • Vendor A (existing supplier) — "Trusted Partner": mid-price, flexible, terms-driven.
  • Vendor B (scouted, ALWAYS CHEAPEST) — "Aggressive Newcomer": low price, hungry for the deal.
  • Vendor C (scouted, ALWAYS MOST EXPENSIVE) — "Premium Specialist": high price, walks away if pushed.

Vendor B usually wins. Vendor A is a strong second on relationship/terms.
Vendor C usually withdraws. Fully deterministic; runs in <1 second.
"""
import random
from datetime import datetime, timedelta
import database as db


# ── Supplier catalogue ─────────────────────────────────────────────────────────

SCOUTED_BY_CATEGORY = {
    "IT Equipment & Software": [
        {"name": "Insight Direct (UK) Ltd", "location": "Coventry", "rating": 4.4,
         "desc": "IT solutions disruptor. Aggressive volume pricing on Dell, HP and Lenovo."},
        {"name": "Computacenter PLC", "location": "Hatfield", "rating": 4.6,
         "desc": "FTSE 250 premium IT infrastructure group. Tier-1 service standards."},
    ],
    "Facilities Management": [
        {"name": "Mitie Group PLC", "location": "London", "rating": 4.3,
         "desc": "National FM provider with competitive volume pricing model."},
        {"name": "Bilfinger UK", "location": "Tamworth", "rating": 4.5,
         "desc": "Premium industrial services specialist. Energy sector accreditation."},
    ],
    "Professional Services": [
        {"name": "Addleshaw Goddard LLP", "location": "Leeds / London", "rating": 4.5,
         "desc": "Top-20 UK law firm — competitive on blended rate cards."},
        {"name": "PwC UK", "location": "London", "rating": 4.6,
         "desc": "Big Four firm. Premium positioning, partner-led engagements."},
    ],
    "Fleet & Transport": [
        {"name": "ATS Euromaster Ltd", "location": "Coventry", "rating": 4.2,
         "desc": "National network with aggressive fleet account pricing."},
        {"name": "Enterprise Fleet Management", "location": "Egham", "rating": 4.4,
         "desc": "Premium fleet management with white-glove service."},
    ],
    "Engineering & Maintenance": [
        {"name": "Wilson Power Solutions", "location": "Leeds", "rating": 4.4,
         "desc": "Independent transformer specialist. Sharp pricing, own test lab."},
        {"name": "Brush Transformers Ltd", "location": "Loughborough", "rating": 4.6,
         "desc": "OEM transformer manufacturer. Premium, National Grid preferred."},
    ],
    "Office Supplies & Furniture": [
        {"name": "Sven Christiansen Ltd", "location": "Wetherby", "rating": 4.0,
         "desc": "UK manufacturer with volume pricing, fast lead times."},
        {"name": "Orangebox Ltd", "location": "Nantgarw, Wales", "rating": 4.4,
         "desc": "Premium workplace furniture designer."},
    ],
    "Health & Safety Equipment": [
        {"name": "Safety Supply Direct Ltd", "location": "Leeds", "rating": 3.7,
         "desc": "Online PPE distributor. Aggressive on volume orders."},
        {"name": "JSP Ltd", "location": "Chipping Norton", "rating": 4.3,
         "desc": "UK PPE manufacturer. Premium-grade certified protection."},
    ],
    "Marketing & Communications": [
        {"name": "Kinetic Digital UK", "location": "London", "rating": 4.2,
         "desc": "Digital signage challenger. Competitive enterprise pricing."},
        {"name": "Ogilvy UK", "location": "London", "rating": 4.5,
         "desc": "Global premium creative agency. Top-tier brand experience."},
    ],
}

_DEFAULT_SCOUTED = [
    {"name": "Veolia UK", "location": "London", "rating": 4.1,
     "desc": "Environmental services. Competitive national pricing."},
    {"name": "Amey PLC", "location": "Oxford", "rating": 4.0,
     "desc": "Premium infrastructure services group."},
]


def scout_internet_suppliers(category: str, request_id: str) -> list[dict]:
    """Returns [cheapest_vendor, premium_vendor]."""
    templates = SCOUTED_BY_CATEGORY.get(category, _DEFAULT_SCOUTED)
    suppliers = []
    for i, t in enumerate(templates[:2]):
        sup_id = f"sup-live-{request_id[-6:]}-{i+1}"
        s = {
            "id": sup_id,
            "name": t["name"],
            "type": "scouted",
            "category": category,
            "contact_email": f"procurement@{t['name'].lower().replace(' ', '').replace(',', '')[:16]}.co.uk",
            "location": t["location"] + ", UK",
            "accreditations": "ISO 9001",
            "rating": t["rating"],
            "source": "internet_scout",
            "description": t["desc"],
        }
        db.insert_supplier(s)
        suppliers.append(s)
    return suppliers


# ── Persona archetypes ────────────────────────────────────────────────────────

# Each persona has: pricing multipliers, payment terms, delivery, voice.
PERSONAS = {
    "trusted_partner": {
        "label": "Trusted Partner",
        "initial_mult": 0.95,   # 95% of budget
        "best_mult":    0.87,   # can drop to 87%
        "payment":      "Net 45",
        "delivery":     7,
        "will_walk_away": False,
        "will_accept_threshold": 0.92,  # accepts counters above 92% of own initial
    },
    "aggressive_cheap": {
        "label": "Aggressive Newcomer",
        "initial_mult": 0.85,   # 85% of budget — cheapest start
        "best_mult":    0.79,   # can drop to 79%
        "payment":      "Net 30",
        "delivery":     10,
        "will_walk_away": False,
        "will_accept_threshold": 0.94,  # very eager to win
    },
    "premium_walk": {
        "label": "Premium Specialist",
        "initial_mult": 1.07,   # 107% of budget — most expensive
        "best_mult":    1.02,   # won't go below 102% of budget
        "payment":      "Net 30",
        "delivery":     14,
        "will_walk_away": True,
        "will_accept_threshold": 0.99,  # only accepts if hardly any concession needed
    },
}


# ── Voice templates per persona ───────────────────────────────────────────────

def _rfq_message(sup_name: str, target: float, source_label: str) -> str:
    return (
        f"RFQ issued to **{sup_name}** ({source_label}). "
        f"Target price communicated: £{target:,.0f}. Standard Centrica T&Cs apply. Response requested within 24 hours."
    )


def _initial_offer_msg(sup_name: str, price: float, persona_key: str, intake: dict) -> str:
    qty = intake.get('quantity', 1)
    unit = intake.get('unit', 'units')
    if persona_key == "trusted_partner":
        return (
            f"Hello Centrica team — thank you for the opportunity. As your long-standing partner, "
            f"{sup_name} is pleased to submit £{price:,.2f} for {qty} {unit}, on Net 45 terms with "
            f"7-day delivery from our Birmingham hub. Given our existing framework agreement, we can "
            f"flex on payment terms or include an extended SLA at no charge. Happy to discuss."
        )
    if persona_key == "aggressive_cheap":
        return (
            f"Many thanks for the RFQ. {sup_name} is going in sharp at £{price:,.2f} for the full {qty} {unit} "
            f"scope — this is our most aggressive market price and beats our list by 15%. Net 30 terms, "
            f"10-day delivery, full warranty included. We're actively building our Centrica relationship "
            f"and are highly motivated to win this contract."
        )
    # premium_walk
    return (
        f"Thank you for inviting {sup_name} to tender. Our quotation is £{price:,.2f} for the specified "
        f"scope of {qty} {unit}. This reflects our premium service standard: dedicated account team, "
        f"24/7 priority support, 5-year extended warranty, and ISO 27001-certified delivery. We don't "
        f"compete on headline price — we compete on total cost of ownership and risk."
    )


def _centrica_counter_msg(sup_name: str, persona_key: str, current_offer: float, target: float, round_num: int) -> str:
    gap_pct = (current_offer - target) / current_offer * 100
    counter = target * (1.02 if round_num == 1 else 1.0)

    if persona_key == "aggressive_cheap":
        return (
            f"@{sup_name} — strong opening price, thank you. We see room to align further at "
            f"£{counter:,.2f}. Given the volume and our pipeline, we believe this represents fair value "
            f"for both parties. Open to early-pay discount in exchange. Centrica Procurement Agent."
        )
    if persona_key == "premium_walk":
        return (
            f"@{sup_name} — we acknowledge the premium positioning, but £{current_offer:,.2f} is {gap_pct:.1f}% "
            f"above our budget envelope. To progress, we need to see £{counter:,.2f}. We can offer Net 60 "
            f"payment terms or a multi-year volume commitment in exchange. Please review."
        )
    # trusted_partner
    return (
        f"@{sup_name} — thank you for the constructive proposal. To stay within budget, we are countering "
        f"at £{counter:,.2f}. As a valued partner, we'd like to maintain this relationship — we can offer "
        f"a 24-month framework extension and earlier payment if the price works for you. Let us know."
    )


def _supplier_counter_response_msg(sup_name: str, persona_key: str, final: float | None,
                                    accepted: bool, round_num: int) -> str:
    if final is None:  # walk away
        return (
            f"After careful review, {sup_name} regrets that the requested price does not allow us to "
            f"maintain our service standards. We must respectfully withdraw from this tender. "
            f"We remain interested in future opportunities where total value, not just price, is the "
            f"deciding factor. Thank you for the engagement."
        )
    if accepted:
        if persona_key == "trusted_partner":
            return (
                f"Centrica team — we appreciate the partnership-led approach. {sup_name} confirms acceptance "
                f"at £{final:,.2f} with Net 45 payment, plus the 24-month framework extension. "
                f"Our team is ready to mobilise on PO receipt. Thank you."
            )
        if persona_key == "aggressive_cheap":
            return (
                f"Deal. {sup_name} confirms £{final:,.2f} — best price in market for this spec. "
                f"Locked in with 10-day delivery and full warranty. PO received and we'll start "
                f"production immediately. Looking forward to a long Centrica relationship."
            )
        return (
            f"{sup_name} confirms acceptance at £{final:,.2f}. The Net 60 payment term works for us. "
            f"This price preserves our service standards and we commit to flawless delivery. "
            f"Welcome to the {sup_name} client portfolio."
        )
    # countered back (price-firm or partial concession)
    if persona_key == "premium_walk":
        return (
            f"{sup_name} can move to £{final:,.2f} as our absolute best-and-final position. "
            f"This is below our standard margin and only viable given the volume on offer. "
            f"We trust this demonstrates our commitment without compromising service quality."
        )
    if persona_key == "trusted_partner":
        return (
            f"Thank you. {sup_name} can come down to £{final:,.2f} — a meaningful concession from our "
            f"side that reflects the value of the Centrica relationship. We hope this lands us in "
            f"contract-award position."
        )
    return (
        f"Centrica — we can sharpen to £{final:,.2f}, marginally below our initial offer. This is our "
        f"hungry-for-the-business price. Hope this gets us over the line."
    )


def _centrica_acceptance_msg(sup_name: str, price: float) -> str:
    return (
        f"@{sup_name} — offer within target range. Acceptance confirmed at £{price:,.2f}. "
        f"Centrica Procurement Agent."
    )


def _pick_winner(negs: list) -> str | None:
    accepted = [n for n in negs if n.get("agreed_price")]
    return min(accepted, key=lambda n: n["agreed_price"])["id"] if accepted else None


# ── Orchestrator ───────────────────────────────────────────────────────────────

def run_negotiation(request_id: str, intake: dict, progress_cb=None) -> dict:
    def _p(msg, pct):
        if progress_cb:
            try:
                progress_cb(msg, pct)
            except Exception:
                pass

    now_iso = datetime.utcnow().isoformat()
    base_dt = datetime.fromisoformat(now_iso)
    budget = intake.get("max_budget", 10000)
    category = intake.get("category", "Other")
    target = budget * 0.88  # internal Centrica target: 12% below buyer budget

    if intake.get("risk_tier") == "high":
        db.update_request_status(request_id, "escalated")
        _p("⚠️ High-risk request — escalated to Category Manager", 100)
        return {"escalated": True, "risk_tier": "high"}

    _p("Identifying Centrica-approved supplier...", 15)
    existing = db.get_existing_suppliers_by_category(category)
    if not existing:
        from demo_data import EXISTING_SUPPLIERS
        fb = random.choice(EXISTING_SUPPLIERS)
        db.insert_supplier(fb)
        existing = [fb]
    existing_sup = existing[0]

    _p("Scouting 2 market suppliers via internet search...", 30)
    scouted = scout_internet_suppliers(category, request_id)

    # Assign personas: trusted_partner (existing), aggressive_cheap (first scout), premium_walk (second scout)
    all_sups = [existing_sup, scouted[0], scouted[1]]
    persona_keys = ["trusted_partner", "aggressive_cheap", "premium_walk"]

    _p("Broadcasting RFQ to all 3 suppliers...", 45)
    db.update_request_status(request_id, "negotiating")

    negs = []
    minute_offset = 0

    for i, (sup, pkey) in enumerate(zip(all_sups, persona_keys)):
        persona = PERSONAS[pkey]
        neg_id = f"neg-{request_id[-8:]}-{i+1}"
        price = round(budget * persona["initial_mult"], -1)
        payment = persona["payment"]
        delivery = persona["delivery"]

        db.insert_negotiation({
            "id": neg_id, "request_id": request_id, "supplier_id": sup["id"],
            "strategy": pkey, "initial_price": price, "centrica_target": target,
            "payment_terms": payment, "delivery_days": delivery,
            "status": "rfq_sent", "created_at": now_iso, "updated_at": now_iso,
        })
        db.update_negotiation(neg_id, {"current_offer": price, "round_number": 1})

        # 1) Centrica sends RFQ
        minute_offset += 1
        db.insert_message({
            "request_id": request_id, "negotiation_id": neg_id,
            "sender": "Centrica Procurement Agent",
            "content": _rfq_message(sup["name"], target, sup["source"].replace("_", " ").title()),
            "message_type": "rfq",
            "timestamp": (base_dt + timedelta(minutes=minute_offset)).isoformat(),
        })

        # 2) Vendor sends initial offer
        minute_offset += 3
        db.insert_message({
            "request_id": request_id, "negotiation_id": neg_id,
            "sender": sup["name"],
            "content": _initial_offer_msg(sup["name"], price, pkey, intake),
            "message_type": "offer",
            "timestamp": (base_dt + timedelta(minutes=minute_offset)).isoformat(),
        })

        negs.append({
            "id": neg_id, "supplier_id": sup["id"], "supplier_name": sup["name"],
            "supplier_type": sup["type"], "persona": pkey, "initial_price": price,
            "current_offer": price, "centrica_target": target, "agreed_price": None,
            "payment_terms": payment, "delivery_days": delivery, "round_number": 1,
        })

    _p("Evaluating offers — Centrica Agent preparing counter-offers...", 60)

    # ── Counter rounds (up to 2) ─────────────────────────────────────────────
    for rnd in range(1, 3):
        any_open = False
        for neg in negs:
            if neg.get("agreed_price") or neg.get("withdrawn"):
                continue
            any_open = True
            sup = next(s for s in all_sups if s["id"] == neg["supplier_id"])
            persona = PERSONAS[neg["persona"]]
            gap_pct = (neg["current_offer"] - target) / neg["current_offer"] * 100

            minute_offset += 5
            ts_counter = (base_dt + timedelta(minutes=minute_offset)).isoformat()
            minute_offset += 3
            ts_response = (base_dt + timedelta(minutes=minute_offset)).isoformat()

            # If already within 3% of target, accept directly
            if gap_pct <= 3:
                neg["agreed_price"] = neg["current_offer"]
                db.update_negotiation(neg["id"], {
                    "agreed_price": neg["current_offer"], "status": "agreed", "round_number": rnd + 1,
                })
                db.insert_message({
                    "request_id": request_id, "negotiation_id": neg["id"],
                    "sender": "Centrica Procurement Agent",
                    "content": _centrica_acceptance_msg(sup["name"], neg["current_offer"]),
                    "message_type": "acceptance", "timestamp": ts_counter,
                })
                continue

            counter_price = round(target * (1.02 if rnd == 1 else 1.0), -1)

            # Centrica counter-offer
            db.insert_message({
                "request_id": request_id, "negotiation_id": neg["id"],
                "sender": "Centrica Procurement Agent",
                "content": _centrica_counter_msg(sup["name"], neg["persona"], neg["current_offer"], target, rnd),
                "message_type": "counter", "timestamp": ts_counter,
            })

            # Vendor response — deterministic per persona
            initial = neg["initial_price"]
            best_price = round(budget * persona["best_mult"], -1)
            accept_threshold = initial * persona["will_accept_threshold"]

            if persona["will_walk_away"] and counter_price < best_price * 0.97:
                # Premium specialist walks away
                final, accepted = None, False
            elif counter_price >= accept_threshold:
                # Accept counter directly
                final, accepted = counter_price, True
            elif counter_price >= best_price:
                # Meet in the middle: vendor accepts at counter price
                final, accepted = counter_price, True
            else:
                # Vendor offers their best price (may or may not be accepted)
                final = best_price
                # If best_price is still meaningfully above target and we're past round 1, accept it
                if rnd >= 2 and final <= target * 1.04:
                    accepted = True
                else:
                    accepted = False

            db.insert_message({
                "request_id": request_id, "negotiation_id": neg["id"],
                "sender": sup["name"],
                "content": _supplier_counter_response_msg(sup["name"], neg["persona"], final, accepted, rnd),
                "message_type": "acceptance" if accepted else ("rejection" if final is None else "counter"),
                "timestamp": ts_response,
            })

            if final is None:
                neg["withdrawn"] = True
                db.update_negotiation(neg["id"], {"status": "rejected", "round_number": rnd + 1})
            elif accepted:
                neg["agreed_price"] = final
                neg["current_offer"] = final
                db.update_negotiation(neg["id"], {
                    "agreed_price": final, "current_offer": final, "status": "agreed",
                    "round_number": rnd + 1,
                })
            else:
                neg["current_offer"] = final
                db.update_negotiation(neg["id"], {"current_offer": final, "round_number": rnd + 1})

        if not any_open:
            break

    _p("Selecting best offer and issuing Purchase Order...", 85)

    winner_id = _pick_winner(negs)
    result = {"escalated": False, "negotiations": negs}

    if winner_id:
        w = next(n for n in negs if n["id"] == winner_id)
        sup = next(s for s in all_sups if s["id"] == w["supplier_id"])
        savings = budget - w["agreed_price"]
        savings_pct = savings / budget * 100
        db.update_negotiation(winner_id, {"winner": 1, "savings": savings})

        po_num = f"PO-{datetime.utcnow().year}-{random.randint(1000, 9999)}"
        del_date = (datetime.utcnow() + timedelta(days=w["delivery_days"])).strftime("%Y-%m-%d")
        db.insert_po({
            "id": f"po-{request_id}", "request_id": request_id,
            "supplier_id": w["supplier_id"], "negotiation_id": winner_id,
            "po_number": po_num, "total_value": w["agreed_price"],
            "payment_terms": w["payment_terms"], "delivery_date": del_date,
            "savings_vs_budget": savings, "savings_pct": round(savings_pct, 1),
            "issued_at": datetime.utcnow().isoformat(),
        })
        db.update_request_status(request_id, "completed")

        minute_offset += 5
        db.insert_message({
            "request_id": request_id, "negotiation_id": winner_id,
            "sender": "Centrica Procurement Agent",
            "content": (
                f"🏆 **CONTRACT AWARDED — PO {po_num} issued.**\n\n"
                f"**Winner:** {sup['name']} ({PERSONAS[w['persona']]['label']})\n"
                f"**Value:** £{w['agreed_price']:,.2f}\n"
                f"**Payment:** {w['payment_terms']}\n"
                f"**Delivery by:** {del_date}\n"
                f"**Savings vs buyer budget:** £{savings:,.0f} ({savings_pct:.1f}%)\n\n"
                f"Notifications sent to losing bidders. Thank you all for participating."
            ),
            "message_type": "po",
            "timestamp": (base_dt + timedelta(minutes=minute_offset)).isoformat(),
        })
        result.update({
            "winner_supplier": sup["name"], "winner_supplier_type": sup["type"],
            "winner_persona": PERSONAS[w["persona"]]["label"],
            "agreed_price": w["agreed_price"], "savings": savings,
            "savings_pct": round(savings_pct, 1), "po_number": po_num, "delivery_date": del_date,
        })
    else:
        db.update_request_status(request_id, "escalated")
        result["escalated"] = True
        result["reason"] = "No supplier reached agreement within budget. Escalated to Category Manager."

    _p("Complete", 100)
    return result
