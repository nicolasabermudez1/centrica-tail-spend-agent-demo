"""
Autonomous negotiation engine — sourcing agent vs. 3 vendor agents in parallel.

The sourcing agent runs a SEPARATE structured conversation with each vendor:
  1. Sends RFQ with full specifications.
  2. Receives initial quote (price + breakdown + value-add).
  3. Sends commercial analysis + counter-offer.
  4. Receives vendor response (accept / counter / walk away).
  5. Optional second round.
  6. Sends final award or polite decline notification.

The award rule is explicit: the LOWEST accepted offer wins. Walk-aways and
declined counters are excluded. The award notification quotes the comparison.

Personas (fully deterministic):
  • Trusted Partner (existing supplier) — mid price, relationship-led, flexible
  • Aggressive Newcomer (scouted)       — ALWAYS cheapest initial bid
  • Premium Specialist (scouted)        — ALWAYS most expensive, often walks away
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

PERSONAS = {
    "trusted_partner": {
        "label": "Trusted Partner",
        "initial_mult": 0.95,
        "best_mult":    0.87,
        "payment":      "Net 45",
        "delivery":     7,
        "will_walk_away": False,
        "will_accept_threshold": 0.92,
    },
    "aggressive_cheap": {
        "label": "Aggressive Newcomer",
        "initial_mult": 0.85,
        "best_mult":    0.79,
        "payment":      "Net 30",
        "delivery":     10,
        "will_walk_away": False,
        "will_accept_threshold": 0.94,
    },
    "premium_walk": {
        "label": "Premium Specialist",
        "initial_mult": 1.07,
        "best_mult":    1.02,
        "payment":      "Net 30",
        "delivery":     14,
        "will_walk_away": True,
        "will_accept_threshold": 0.99,
    },
}


# ── Category-specific spec hints (lifts realism) ──────────────────────────────

CATEGORY_SPECS = {
    "IT Equipment & Software": (
        "Tier-1 OEM hardware (Dell / HP / Lenovo); UK keyboard layout; 3-year warranty; "
        "asset-tagging and pre-configured Centrica SOE image; secure disposal of any returned units."
    ),
    "Facilities Management": (
        "Site access compliance (Centrica passport scheme); ISO 9001 + ISO 45001; "
        "DBS-checked engineers; 4-hour reactive SLA; quarterly KPI reporting."
    ),
    "Professional Services": (
        "SRA-regulated / chartered practitioners; conflict-check clearance; agreed rate card; "
        "fixed-fee or capped-fee preferred; monthly burn-down reporting."
    ),
    "Fleet & Transport": (
        "DVSA-authorised facilities; mobile servicing option; BVRLA membership; "
        "consolidated monthly invoicing; downtime SLA."
    ),
    "Engineering & Maintenance": (
        "NICEIC / IET registered engineers; method statements + RAMS; "
        "24/7 emergency callout; spare-parts holding included."
    ),
    "Office Supplies & Furniture": (
        "FIRA Gold or equivalent; 5-year warranty on mechanism; "
        "Centrica navy frame option; delivery + installation included."
    ),
    "Health & Safety Equipment": (
        "EN ISO standards-compliant; CE / UKCA marked; "
        "lot traceability; volume discount tiering."
    ),
    "Marketing & Communications": (
        "Brand-compliant deliverables; IP transfer in deliverables; "
        "ISO 27001 for any data-handling; agreed milestone payment plan."
    ),
}


# ── Voice templates ──────────────────────────────────────────────────────────

def _rfq_message(sup_name: str, intake: dict, target: float, source_label: str) -> str:
    qty = intake.get("quantity", 1)
    unit = intake.get("unit", "units")
    cat = intake.get("category", "Goods/Services")
    bu = intake.get("business_unit", "Centrica")
    required_by = intake.get("required_by", "TBC")
    description = intake.get("description", "")
    specs = CATEGORY_SPECS.get(cat, "Standard Centrica supplier T&Cs apply.")

    return (
        f"**📋 RFQ-{datetime.utcnow().year}-{random.randint(1000,9999)} — Centrica Procurement**\n\n"
        f"To: {sup_name} _( {source_label} )_\n"
        f"From: Centrica Procurement Agent\n\n"
        f"Centrica is sourcing the following:\n\n"
        f"• **Category:** {cat}\n"
        f"• **Item:** {description}\n"
        f"• **Quantity:** {qty} {unit}\n"
        f"• **Business Unit:** {bu}\n"
        f"• **Required by:** {required_by}\n"
        f"• **Technical specifications:** {specs}\n"
        f"• **Payment terms:** Net 30 (standard); Net 45/60 considered in exchange for sharper pricing\n"
        f"• **Centrica indicative target:** £{target:,.0f}\n\n"
        f"Please submit your best initial quotation within 24 hours. "
        f"Include unit price, total, delivery timeline, warranty and any value-adds."
    )


def _initial_offer_msg(sup_name: str, price: float, persona_key: str, intake: dict, delivery: int) -> str:
    qty = intake.get('quantity', 1)
    unit = intake.get('unit', 'units')
    unit_price = price / max(qty, 1)

    if persona_key == "trusted_partner":
        return (
            f"Hello Centrica team — thank you for inviting us to tender.\n\n"
            f"As your long-standing partner, **{sup_name}** is pleased to submit:\n\n"
            f"• **Unit price:** £{unit_price:,.2f} × {qty} {unit}\n"
            f"• **Total:** **£{price:,.2f}**\n"
            f"• **Payment terms:** Net 45\n"
            f"• **Delivery:** {delivery} working days from PO\n"
            f"• **Warranty:** Standard 3-year, extendable to 5-year at no charge given our framework\n"
            f"• **Value-add:** Account director continuity, free annual service review, priority callout\n\n"
            f"Given the existing relationship we'd welcome a discussion on payment terms "
            f"or a multi-year extension if helpful. Happy to flex."
        )
    if persona_key == "aggressive_cheap":
        return (
            f"Many thanks for the RFQ — **{sup_name}** is going in sharp.\n\n"
            f"• **Unit price:** £{unit_price:,.2f} × {qty} {unit}\n"
            f"• **Total:** **£{price:,.2f}**  _(15% below our published list)_\n"
            f"• **Payment terms:** Net 30\n"
            f"• **Delivery:** {delivery} working days, expedite available\n"
            f"• **Warranty:** Full 3-year manufacturer + 1-year {sup_name} extended\n"
            f"• **Value-add:** Free deployment kit, dedicated implementation manager, named SLA\n\n"
            f"We're actively building our Centrica relationship and are **highly motivated** "
            f"to win this contract. Open to a sharper price for a 2-year commitment."
        )
    # premium_walk
    return (
        f"Thank you for inviting **{sup_name}** to tender.\n\n"
        f"Our quotation reflects premium service standards — we don't compete on headline price.\n\n"
        f"• **Unit price:** £{unit_price:,.2f} × {qty} {unit}\n"
        f"• **Total:** **£{price:,.2f}**\n"
        f"• **Payment terms:** Net 30\n"
        f"• **Delivery:** {delivery} working days\n"
        f"• **Warranty:** 5-year extended, full parts + labour, on-site response\n"
        f"• **Value-add:** Dedicated account team, ISO 27001-certified delivery, "
        f"24/7 priority support, executive QBRs\n\n"
        f"This represents fair value when total cost of ownership is considered."
    )


def _centrica_analysis_msg(sup_name: str, current_offer: float, target: float, persona_key: str, round_num: int) -> str:
    gap_pct = (current_offer - target) / current_offer * 100
    counter = round(target * (1.02 if round_num == 1 else 1.0), -1)
    persona_lbl = PERSONAS[persona_key]["label"]

    header = (
        f"**🤖 Sourcing Agent — Commercial Analysis**\n\n"
        f"Reviewing {sup_name}'s offer ({persona_lbl}):\n\n"
        f"• Submitted: **£{current_offer:,.2f}**\n"
        f"• Centrica target: **£{target:,.0f}**\n"
        f"• Variance: **{gap_pct:+.1f}%**\n"
        f"• Round: **{round_num} of 2**\n\n"
    )

    if persona_key == "aggressive_cheap":
        body = (
            f"Strong opening — already the most competitive bid received. "
            f"To finalise within budget, we propose **£{counter:,.0f}**. "
            f"In exchange we can offer:\n\n"
            f"• 2% early-pay discount in return for the sharper price, OR\n"
            f"• 24-month volume commitment to lock in the relationship.\n\n"
            f"Please confirm — keen to close quickly given your pricing."
        )
    elif persona_key == "premium_walk":
        body = (
            f"We recognise the premium positioning. However, £{current_offer:,.2f} is "
            f"materially above our budget envelope and would require executive sign-off. "
            f"To progress, we need to see **£{counter:,.0f}**.\n\n"
            f"In exchange we can offer:\n\n"
            f"• Net 60 payment terms, OR\n"
            f"• Multi-year framework commitment.\n\n"
            f"Please confirm whether this is feasible."
        )
    else:  # trusted_partner
        body = (
            f"Thank you for the constructive proposal. To stay within the buyer's budget, "
            f"we are countering at **£{counter:,.0f}**. We'd like to preserve this relationship — "
            f"in exchange we can offer:\n\n"
            f"• 24-month framework renewal with annual price review, AND\n"
            f"• Net 30 (vs your Net 45) with 1.5% early-pay discount.\n\n"
            f"Let us know if this works."
        )

    return header + body


def _supplier_counter_response_msg(sup_name: str, persona_key: str, final: float | None,
                                    accepted: bool, round_num: int) -> str:
    if final is None:  # walk-away
        return (
            f"Centrica team — thank you for the engagement.\n\n"
            f"After careful review, **{sup_name}** regrets that the requested price does not "
            f"preserve our service standards. We must respectfully **withdraw from this tender**.\n\n"
            f"We remain interested in future opportunities where total value, not just price, "
            f"is the deciding factor. Best wishes for a successful procurement."
        )

    if accepted:
        if persona_key == "trusted_partner":
            return (
                f"We appreciate the partnership-led approach. \n\n"
                f"**{sup_name} confirms acceptance** at **£{final:,.2f}** with:\n\n"
                f"• Payment terms: Net 45 (as offered)\n"
                f"• 24-month framework extension agreed\n"
                f"• Delivery within original commitment\n\n"
                f"Our team is ready to mobilise on PO receipt. Thank you for your continued partnership."
            )
        if persona_key == "aggressive_cheap":
            return (
                f"**Deal — {sup_name} confirms £{final:,.2f}.**\n\n"
                f"• Sharpest price in market for this specification\n"
                f"• Net 30 payment terms locked in\n"
                f"• Full delivery + warranty as quoted\n"
                f"• Production starts immediately on PO receipt\n\n"
                f"Looking forward to a long and successful Centrica relationship. "
                f"Please send the PO to our enterprise team."
            )
        # premium_walk accepted (rare)
        return (
            f"**{sup_name} confirms acceptance at £{final:,.2f}.**\n\n"
            f"Net 60 payment term works for us. This price preserves our service standards. "
            f"We commit to flawless delivery and welcome Centrica to our enterprise client portfolio."
        )

    # countered back (not accepted)
    if persona_key == "premium_walk":
        return (
            f"**{sup_name}** can move to **£{final:,.2f}** as our absolute best-and-final position.\n\n"
            f"This is below our standard margin and only viable given the volume on offer. "
            f"We trust this demonstrates our commitment without compromising the service standards "
            f"that Centrica requires."
        )
    if persona_key == "trusted_partner":
        return (
            f"Thank you. **{sup_name}** can come down to **£{final:,.2f}** — a meaningful concession "
            f"that reflects the value we place on the Centrica relationship.\n\n"
            f"We hope this lands us in award position. Open to further conversation if needed."
        )
    return (
        f"Centrica — **{sup_name}** can sharpen to **£{final:,.2f}**, below our initial offer. "
        f"This is our hungry-for-the-business price. Hope this gets us over the line."
    )


def _award_winner_msg(sup_name: str, price: float, po_number: str, all_offers: list, savings: float, savings_pct: float) -> str:
    """The award notification sent to the WINNING vendor."""
    comparison = "\n".join(
        f"• {o['name']} ({PERSONAS[o['persona']]['label']}): "
        + (f"£{o['final']:,.0f}" if o['final'] else "withdrew")
        for o in all_offers
    )
    return (
        f"🏆 **AWARD NOTIFICATION — PO {po_number}**\n\n"
        f"After comparing all three offers, the Sourcing Agent has selected **{sup_name}** "
        f"as the **lowest accepted bid** at **£{price:,.2f}**.\n\n"
        f"**Comparison summary:**\n{comparison}\n\n"
        f"**Outcome:**\n"
        f"• Savings vs buyer budget: £{savings:,.0f} ({savings_pct:.1f}%)\n"
        f"• PO {po_number} issued to {sup_name}\n"
        f"• Other suppliers being notified now\n\n"
        f"Congratulations — please confirm PO acknowledgement within 48 hours."
    )


def _decline_msg(sup_name: str, winning_price: float, your_price: float | None, winner_name: str) -> str:
    """Polite decline message to losing vendors."""
    if your_price is None:
        # they withdrew earlier - just acknowledge
        return (
            f"Centrica acknowledges {sup_name}'s withdrawal from this tender. "
            f"For your information, the contract has been awarded to **{winner_name}** "
            f"at **£{winning_price:,.2f}**.\n\n"
            f"We will keep {sup_name} engaged for future opportunities — thank you for your participation."
        )
    return (
        f"**Thank you for your participation — Tender outcome notification**\n\n"
        f"After careful evaluation of all three offers, Centrica has selected another supplier "
        f"for this requirement.\n\n"
        f"• Awarded supplier: **{winner_name}**\n"
        f"• Winning price: **£{winning_price:,.2f}**\n"
        f"• Your final offer: £{your_price:,.2f}\n\n"
        f"We value the time {sup_name} invested in this RFQ and look forward to inviting you "
        f"to future tenders. The Sourcing Agent will keep your account active on our pre-qualified list."
    )


def _centrica_inline_acceptance_msg(sup_name: str, price: float) -> str:
    """When the initial offer is already within target — accept immediately."""
    return (
        f"**🤖 Sourcing Agent — Offer Accepted**\n\n"
        f"{sup_name}'s offer of £{price:,.2f} is within our target range. "
        f"No counter required. Provisional acceptance recorded pending final award decision."
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
    target = budget * 0.88

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

    all_sups = [existing_sup, scouted[0], scouted[1]]
    persona_keys = ["trusted_partner", "aggressive_cheap", "premium_walk"]

    _p("Sourcing Agent dispatching RFQs to all 3 suppliers...", 45)
    db.update_request_status(request_id, "negotiating")

    negs = []
    minute_offset = 0

    # ── Stage 1: RFQ + initial offers per vendor ─────────────────────────────
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

        # 1. RFQ with full specs
        minute_offset += 1
        db.insert_message({
            "request_id": request_id, "negotiation_id": neg_id,
            "sender": "Centrica Procurement Agent",
            "content": _rfq_message(sup["name"], intake, target, sup["source"].replace("_", " ").title()),
            "message_type": "rfq",
            "timestamp": (base_dt + timedelta(minutes=minute_offset)).isoformat(),
        })

        # 2. Vendor initial quote
        minute_offset += 4
        db.insert_message({
            "request_id": request_id, "negotiation_id": neg_id,
            "sender": sup["name"],
            "content": _initial_offer_msg(sup["name"], price, pkey, intake, delivery),
            "message_type": "offer",
            "timestamp": (base_dt + timedelta(minutes=minute_offset)).isoformat(),
        })

        negs.append({
            "id": neg_id, "supplier_id": sup["id"], "supplier_name": sup["name"],
            "supplier_type": sup["type"], "persona": pkey, "initial_price": price,
            "current_offer": price, "centrica_target": target, "agreed_price": None,
            "payment_terms": payment, "delivery_days": delivery, "round_number": 1,
        })

    _p("Evaluating offers — preparing counter-offers...", 60)

    # ── Stage 2: Counter rounds (up to 2 per vendor) ─────────────────────────
    for rnd in range(1, 3):
        any_open = False
        for neg in negs:
            if neg.get("agreed_price") or neg.get("withdrawn"):
                continue
            any_open = True
            sup = next(s for s in all_sups if s["id"] == neg["supplier_id"])
            persona = PERSONAS[neg["persona"]]
            gap_pct = (neg["current_offer"] - target) / neg["current_offer"] * 100

            minute_offset += 6
            ts_centrica = (base_dt + timedelta(minutes=minute_offset)).isoformat()
            minute_offset += 4
            ts_vendor = (base_dt + timedelta(minutes=minute_offset)).isoformat()

            # If already within 3% of target, accept directly with analysis message
            if gap_pct <= 3:
                neg["agreed_price"] = neg["current_offer"]
                db.update_negotiation(neg["id"], {
                    "agreed_price": neg["current_offer"], "status": "agreed", "round_number": rnd + 1,
                })
                db.insert_message({
                    "request_id": request_id, "negotiation_id": neg["id"],
                    "sender": "Centrica Procurement Agent",
                    "content": _centrica_inline_acceptance_msg(sup["name"], neg["current_offer"]),
                    "message_type": "acceptance", "timestamp": ts_centrica,
                })
                continue

            # Centrica's commercial analysis + counter
            db.insert_message({
                "request_id": request_id, "negotiation_id": neg["id"],
                "sender": "Centrica Procurement Agent",
                "content": _centrica_analysis_msg(sup["name"], neg["current_offer"], target, neg["persona"], rnd),
                "message_type": "counter", "timestamp": ts_centrica,
            })

            # Vendor response — deterministic per persona
            initial = neg["initial_price"]
            best_price = round(budget * persona["best_mult"], -1)
            accept_threshold = initial * persona["will_accept_threshold"]
            counter_price = round(target * (1.02 if rnd == 1 else 1.0), -1)

            if persona["will_walk_away"] and counter_price < best_price * 0.97:
                final, accepted = None, False
            elif counter_price >= accept_threshold:
                final, accepted = counter_price, True
            elif counter_price >= best_price:
                final, accepted = counter_price, True
            else:
                final = best_price
                if rnd >= 2 and final <= target * 1.04:
                    accepted = True
                else:
                    accepted = False

            db.insert_message({
                "request_id": request_id, "negotiation_id": neg["id"],
                "sender": sup["name"],
                "content": _supplier_counter_response_msg(sup["name"], neg["persona"], final, accepted, rnd),
                "message_type": "acceptance" if accepted else ("rejection" if final is None else "counter"),
                "timestamp": ts_vendor,
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

    _p("Selecting cheapest accepted offer and issuing PO...", 85)

    # ── Stage 3: Award + per-vendor notifications ────────────────────────────
    winner_id = _pick_winner(negs)
    result = {"escalated": False, "negotiations": negs}

    # Build comparison data for award message
    all_offers = []
    for n in negs:
        final_p = n.get("agreed_price") or (None if n.get("withdrawn") else n.get("current_offer"))
        all_offers.append({
            "name": n["supplier_name"],
            "persona": n["persona"],
            "final": final_p,
        })

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

        # Award message to the winner (in their conversation thread)
        minute_offset += 6
        db.insert_message({
            "request_id": request_id, "negotiation_id": winner_id,
            "sender": "Centrica Procurement Agent",
            "content": _award_winner_msg(sup["name"], w["agreed_price"], po_num, all_offers, savings, savings_pct),
            "message_type": "po",
            "timestamp": (base_dt + timedelta(minutes=minute_offset)).isoformat(),
        })

        # Decline messages to losers (in each of their threads)
        for neg in negs:
            if neg["id"] == winner_id:
                continue
            minute_offset += 1
            their_price = neg.get("agreed_price") if not neg.get("withdrawn") else None
            if their_price is None and not neg.get("withdrawn"):
                their_price = neg.get("current_offer")
            db.insert_message({
                "request_id": request_id, "negotiation_id": neg["id"],
                "sender": "Centrica Procurement Agent",
                "content": _decline_msg(neg["supplier_name"], w["agreed_price"], their_price, sup["name"]),
                "message_type": "rejection",
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
