import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "state.sqlite"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS requests (
            id TEXT PRIMARY KEY,
            buyer_name TEXT NOT NULL,
            buyer_department TEXT,
            business_unit TEXT,
            category TEXT NOT NULL,
            subcategory TEXT,
            description TEXT NOT NULL,
            quantity INTEGER,
            unit TEXT,
            max_budget REAL,
            required_by TEXT,
            priority TEXT DEFAULT 'standard',
            risk_tier TEXT DEFAULT 'low',
            status TEXT DEFAULT 'intake',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT,
            contact_email TEXT,
            location TEXT,
            accreditations TEXT,
            rating REAL,
            source TEXT,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS negotiations (
            id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            supplier_id TEXT NOT NULL,
            strategy TEXT,
            round_number INTEGER DEFAULT 0,
            initial_price REAL,
            current_offer REAL,
            centrica_target REAL,
            agreed_price REAL,
            payment_terms TEXT,
            delivery_days INTEGER,
            discount_pct REAL DEFAULT 0,
            status TEXT DEFAULT 'rfq_sent',
            winner INTEGER DEFAULT 0,
            savings REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            negotiation_id TEXT,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'chat',
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            supplier_id TEXT NOT NULL,
            negotiation_id TEXT NOT NULL,
            po_number TEXT NOT NULL,
            total_value REAL NOT NULL,
            payment_terms TEXT,
            delivery_date TEXT,
            savings_vs_budget REAL,
            savings_pct REAL,
            issued_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# ── reads ──────────────────────────────────────────────────────────────────────

def get_all_requests():
    conn = get_connection()
    rows = conn.execute("""
        SELECT r.*, po.total_value as po_value, po.savings_vs_budget, po.savings_pct as po_savings_pct
        FROM requests r
        LEFT JOIN purchase_orders po ON po.request_id = r.id
        ORDER BY r.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_request(request_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_negotiations_for_request(request_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT n.*, s.name as supplier_name, s.type as supplier_type,
               s.source, s.location, s.rating, s.description as supplier_desc
        FROM negotiations n
        JOIN suppliers s ON n.supplier_id = s.id
        WHERE n.request_id = ?
        ORDER BY n.created_at ASC
    """, (request_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_messages_for_request(request_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages WHERE request_id = ? ORDER BY timestamp ASC",
        (request_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_messages_for_negotiation(negotiation_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages WHERE negotiation_id = ? ORDER BY timestamp ASC",
        (negotiation_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_po_for_request(request_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM purchase_orders WHERE request_id = ?", (request_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_spend_by_category():
    conn = get_connection()
    rows = conn.execute("""
        SELECT r.category,
               COUNT(r.id) as deal_count,
               COALESCE(SUM(po.total_value), 0) as total_spend,
               COALESCE(SUM(po.savings_vs_budget), 0) as total_savings,
               COALESCE(AVG(po.savings_pct), 0) as avg_savings_pct
        FROM requests r
        LEFT JOIN purchase_orders po ON po.request_id = r.id
        WHERE r.status IN ('completed', 'awarded')
        GROUP BY r.category
        ORDER BY total_spend DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dashboard_metrics():
    conn = get_connection()
    m = {}
    m['total_spend'] = conn.execute(
        "SELECT COALESCE(SUM(total_value), 0) FROM purchase_orders"
    ).fetchone()[0]
    m['total_savings'] = conn.execute(
        "SELECT COALESCE(SUM(savings_vs_budget), 0) FROM purchase_orders"
    ).fetchone()[0]
    m['completed_deals'] = conn.execute(
        "SELECT COUNT(*) FROM requests WHERE status IN ('completed', 'awarded')"
    ).fetchone()[0]
    m['active_negotiations'] = conn.execute(
        "SELECT COUNT(*) FROM requests WHERE status = 'negotiating'"
    ).fetchone()[0]
    m['avg_savings_pct'] = conn.execute(
        "SELECT COALESCE(AVG(savings_pct), 0) FROM purchase_orders"
    ).fetchone()[0]
    m['escalated'] = conn.execute(
        "SELECT COUNT(*) FROM requests WHERE status = 'escalated'"
    ).fetchone()[0]
    conn.close()
    return m


def get_existing_suppliers_by_category(category):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM suppliers
        WHERE type = 'existing' AND (category = ? OR category = 'multi')
        ORDER BY rating DESC LIMIT 1
    """, (category,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_supplier(supplier_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── writes ─────────────────────────────────────────────────────────────────────

def insert_request(data):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO requests
            (id, buyer_name, buyer_department, business_unit, category, subcategory,
             description, quantity, unit, max_budget, required_by, priority,
             risk_tier, status, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data['id'], data['buyer_name'], data.get('buyer_department'),
        data.get('business_unit'), data['category'], data.get('subcategory'),
        data['description'], data.get('quantity'), data.get('unit'),
        data.get('max_budget'), data.get('required_by'), data.get('priority', 'standard'),
        data.get('risk_tier', 'low'), data.get('status', 'intake'),
        data['created_at'], data['updated_at'],
    ))
    conn.commit()
    conn.close()


def update_request_status(request_id, status):
    conn = get_connection()
    conn.execute(
        "UPDATE requests SET status = ?, updated_at = ? WHERE id = ?",
        (status, datetime.utcnow().isoformat(), request_id)
    )
    conn.commit()
    conn.close()


def insert_supplier(data):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO suppliers
            (id, name, type, category, contact_email, location,
             accreditations, rating, source, description)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        data['id'], data['name'], data['type'], data.get('category'),
        data.get('contact_email'), data.get('location'),
        data.get('accreditations'), data.get('rating'),
        data.get('source'), data.get('description'),
    ))
    conn.commit()
    conn.close()


def insert_negotiation(data):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO negotiations
            (id, request_id, supplier_id, strategy, initial_price, centrica_target,
             payment_terms, delivery_days, status, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data['id'], data['request_id'], data['supplier_id'],
        data.get('strategy'), data.get('initial_price'),
        data.get('centrica_target'), data.get('payment_terms', 'Net 30'),
        data.get('delivery_days', 14), data.get('status', 'rfq_sent'),
        data['created_at'], data['updated_at'],
    ))
    conn.commit()
    conn.close()


def update_negotiation(negotiation_id, updates):
    updates['updated_at'] = datetime.utcnow().isoformat()
    conn = get_connection()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn.execute(
        f"UPDATE negotiations SET {set_clause} WHERE id = ?",
        list(updates.values()) + [negotiation_id]
    )
    conn.commit()
    conn.close()


def insert_message(data):
    conn = get_connection()
    conn.execute("""
        INSERT INTO messages
            (request_id, negotiation_id, sender, content, message_type, timestamp)
        VALUES (?,?,?,?,?,?)
    """, (
        data.get('request_id'), data.get('negotiation_id'),
        data['sender'], data['content'],
        data.get('message_type', 'chat'), data['timestamp'],
    ))
    conn.commit()
    conn.close()


def insert_po(data):
    conn = get_connection()
    conn.execute("""
        INSERT OR IGNORE INTO purchase_orders
            (id, request_id, supplier_id, negotiation_id, po_number,
             total_value, payment_terms, delivery_date,
             savings_vs_budget, savings_pct, issued_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data['id'], data['request_id'], data['supplier_id'],
        data['negotiation_id'], data['po_number'], data['total_value'],
        data.get('payment_terms', 'Net 30'), data.get('delivery_date'),
        data['savings_vs_budget'], data['savings_pct'], data['issued_at'],
    ))
    conn.commit()
    conn.close()


def db_has_demo_data():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    conn.close()
    return count > 0
