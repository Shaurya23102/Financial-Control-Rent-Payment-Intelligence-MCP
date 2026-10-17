from fastmcp import FastMCP
import os
import sqlite3
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "property_management.db")

mcp = FastMCP("PropertyManager")

# ──────────────────────────────────────────────────────────────────────
# DATABASE INITIALIZATION
# ──────────────────────────────────────────────────────────────────────

def init_db():
    """Create all required tables if they don't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                total_floors INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                room_number TEXT NOT NULL,
                floor INTEGER DEFAULT 1,
                room_type TEXT DEFAULT 'single',
                monthly_rent REAL NOT NULL,
                status TEXT DEFAULT 'vacant',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (building_id) REFERENCES buildings(id),
                UNIQUE(building_id, room_number)
            );

            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT DEFAULT '',
                emergency_contact TEXT DEFAULT '',
                id_type TEXT DEFAULT '',
                id_number TEXT DEFAULT '',
                id_verified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tenant_room_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                move_in_date TEXT NOT NULL,
                move_out_date TEXT DEFAULT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                payment_month TEXT NOT NULL,
                payment_mode TEXT DEFAULT 'cash',
                late_fee REAL DEFAULT 0,
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            );

            CREATE TABLE IF NOT EXISTS maintenance_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                escalation_level INTEGER DEFAULT 0,
                escalated_at TEXT DEFAULT NULL,
                resolved_at TEXT DEFAULT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            );

            CREATE TABLE IF NOT EXISTS lease_agreements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                monthly_rent REAL NOT NULL,
                security_deposit REAL DEFAULT 0,
                late_fee_per_day REAL DEFAULT 50,
                grace_period_days INTEGER DEFAULT 5,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            );
        """)

init_db()


def seed_dummy_data():
    """Populate the database with realistic dummy data if tables are empty.
    This runs on every cold start so the demo always has data to showcase."""
    with sqlite3.connect(DB_PATH) as conn:
        # Check if data already exists
        count = conn.execute("SELECT COUNT(*) FROM buildings").fetchone()[0]
        if count > 0:
            return  # Already seeded, skip

        # ── BUILDINGS ──
        conn.executemany("INSERT INTO buildings (name, address, total_floors) VALUES (?, ?, ?)", [
            ("Sunrise Apartments", "42 MG Road, Koramangala, Bangalore - 560034", 3),
            ("Green Valley Residency", "18 Nehru Nagar, Indiranagar, Bangalore - 560038", 2),
        ])

        # ── ROOMS ──
        # Sunrise Apartments (building_id=1): 6 rooms across 3 floors
        conn.executemany("""
            INSERT INTO rooms (building_id, room_number, floor, room_type, monthly_rent, status) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (1, "101", 1, "single",  8000,  "occupied"),
            (1, "102", 1, "single",  8000,  "occupied"),
            (1, "103", 1, "double",  12000, "vacant"),
            (1, "201", 2, "double",  12000, "occupied"),
            (1, "202", 2, "studio",  15000, "occupied"),
            (1, "301", 3, "suite",   20000, "maintenance"),
        ])
        # Green Valley Residency (building_id=2): 4 rooms across 2 floors
        conn.executemany("""
            INSERT INTO rooms (building_id, room_number, floor, room_type, monthly_rent, status) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (2, "G1",  1, "single",  7500,  "occupied"),
            (2, "G2",  1, "double",  11000, "occupied"),
            (2, "G3",  2, "single",  7500,  "vacant"),
            (2, "G4",  2, "studio",  14000, "vacant"),
        ])

        # ── TENANTS ──
        conn.executemany("""
            INSERT INTO tenants (name, phone, email, emergency_contact, id_type, id_number, id_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            ("Rahul Sharma",   "9876543210", "rahul.sharma@gmail.com",   "9876500000", "aadhaar",         "4832-7712-5619", 1),
            ("Priya Patel",    "9123456780", "priya.patel@yahoo.com",    "9123400000", "pan",             "ABCPP1234K",     1),
            ("Amit Kumar",     "9988776655", "amit.k@outlook.com",       "9988770000", "driving_license", "KA-0120267890",  1),
            ("Sneha Reddy",    "8877665544", "sneha.reddy@gmail.com",    "8877660000", "aadhaar",         "6721-8834-9012", 1),
            ("Vikram Singh",   "7766554433", "vikram.s@gmail.com",       "7766550000", "",                "",               0),
            ("Deepa Menon",    "6655443322", "deepa.m@hotmail.com",      "",           "",                "",               0),
        ])

        # ── TENANT-ROOM ASSIGNMENTS (6 active) ──
        conn.executemany("""
            INSERT INTO tenant_room_assignments (tenant_id, room_id, move_in_date, is_active)
            VALUES (?, ?, ?, 1)
        """, [
            (1, 1, "2026-03-01"),   # Rahul  → Sunrise 101
            (2, 2, "2026-01-15"),   # Priya  → Sunrise 102
            (3, 4, "2026-06-01"),   # Amit   → Sunrise 201
            (4, 5, "2026-04-10"),   # Sneha  → Sunrise 202
            (5, 7, "2026-07-01"),   # Vikram → Green Valley G1
            (6, 8, "2026-08-01"),   # Deepa  → Green Valley G2
        ])

        # ── LEASE AGREEMENTS ──
        conn.executemany("""
            INSERT INTO lease_agreements (tenant_id, room_id, start_date, end_date, monthly_rent,
                security_deposit, late_fee_per_day, grace_period_days, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, [
            (1, 1, "2026-03-01", "2027-03-01",  8000, 16000, 50, 5),   # Rahul — standard lease
            (2, 2, "2026-01-15", "2026-11-01",  8000, 16000, 50, 5),   # Priya — expiring in ~15 days!
            (3, 4, "2026-06-01", "2027-06-01", 12000, 24000, 75, 5),   # Amit  — higher late fee
            (4, 5, "2026-04-10", "2027-04-10", 15000, 30000, 100, 7),  # Sneha — 7 day grace
            (5, 7, "2026-07-01", "2027-07-01",  7500, 15000, 50, 5),   # Vikram
            (6, 8, "2026-08-01", "2027-08-01", 11000, 22000, 50, 5),   # Deepa
        ])

        # ── PAYMENTS (Jul, Aug, Sep, Oct 2026) ──
        # Rahul — always pays on time, fully paid all months
        conn.executemany("""
            INSERT INTO payments (tenant_id, room_id, amount, payment_date, payment_month, payment_mode, late_fee, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (1, 1, 8000, "2026-07-02", "2026-07", "upi",           0, ""),
            (1, 1, 8000, "2026-08-01", "2026-08", "upi",           0, ""),
            (1, 1, 8000, "2026-09-03", "2026-09", "upi",           0, ""),
            (1, 1, 8000, "2026-10-02", "2026-10", "upi",           0, "Paid on time as always"),
        ])

        # Priya — pays but always late, has late fees
        conn.executemany("""
            INSERT INTO payments (tenant_id, room_id, amount, payment_date, payment_month, payment_mode, late_fee, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (2, 2, 8000, "2026-07-12", "2026-07", "cash",         300, "Paid 7 days late"),
            (2, 2, 8000, "2026-08-15", "2026-08", "cash",         500, "Paid 10 days late"),
            (2, 2, 8000, "2026-09-10", "2026-09", "bank_transfer", 200, "Paid 5 days late"),
            # October — NOT PAID YET (will show in pending dues)
        ])

        # Amit — regular payer, mix of modes
        conn.executemany("""
            INSERT INTO payments (tenant_id, room_id, amount, payment_date, payment_month, payment_mode, late_fee, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (3, 4, 12000, "2026-07-03", "2026-07", "bank_transfer", 0, ""),
            (3, 4, 12000, "2026-08-05", "2026-08", "upi",           0, ""),
            (3, 4, 12000, "2026-09-02", "2026-09", "bank_transfer", 0, ""),
            (3, 4, 12000, "2026-10-04", "2026-10", "upi",           0, ""),
        ])

        # Sneha — paid partial for October
        conn.executemany("""
            INSERT INTO payments (tenant_id, room_id, amount, payment_date, payment_month, payment_mode, late_fee, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (4, 5, 15000, "2026-07-05", "2026-07", "cheque", 0, ""),
            (4, 5, 15000, "2026-08-04", "2026-08", "cheque", 0, ""),
            (4, 5, 15000, "2026-09-06", "2026-09", "upi",    0, "Switched to UPI"),
            (4, 5, 7000,  "2026-10-08", "2026-10", "upi",    0, "Partial payment — will pay rest by 20th"),
        ])

        # Vikram — NOT PAID for October at all (defaulter)
        conn.executemany("""
            INSERT INTO payments (tenant_id, room_id, amount, payment_date, payment_month, payment_mode, late_fee, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (5, 7, 7500, "2026-07-05", "2026-07", "cash", 0, ""),
            (5, 7, 7500, "2026-08-03", "2026-08", "cash", 0, ""),
            (5, 7, 7500, "2026-09-08", "2026-09", "cash", 150, "3 days late"),
            # October — NOT PAID (defaulter, ID also not verified)
        ])

        # Deepa — paid normally
        conn.executemany("""
            INSERT INTO payments (tenant_id, room_id, amount, payment_date, payment_month, payment_mode, late_fee, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (6, 8, 11000, "2026-08-02", "2026-08", "upi", 0, "First month"),
            (6, 8, 11000, "2026-09-01", "2026-09", "upi", 0, ""),
            (6, 8, 11000, "2026-10-03", "2026-10", "upi", 0, ""),
        ])

        # ── MAINTENANCE REQUESTS ──
        conn.executemany("""
            INSERT INTO maintenance_requests (tenant_id, room_id, category, description, priority, status, 
                escalation_level, escalated_at, resolved_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            # Rahul — plumbing issue, escalated twice, still open
            (1, 1, "plumbing", "Bathroom tap leaking continuously, water wastage is high. Reported 2 weeks ago but not fixed.",
             "urgent", "open", 2, "2026-10-10", None, "2026-10-03"),
            # Priya — electrical issue, open, medium priority
            (2, 2, "electrical", "Bedroom light switch sparking occasionally when turned on.",
             "high", "open", 1, "2026-10-14", None, "2026-10-12"),
            # Amit — furniture request, resolved
            (3, 4, "furniture", "Wardrobe door hinge broken, door hanging loose.",
             "medium", "resolved", 0, None, "2026-09-22", "2026-09-18"),
            # Sneha — pest control, open
            (4, 5, "pest_control", "Cockroach infestation in kitchen area. Need fumigation.",
             "medium", "open", 0, None, None, "2026-10-15"),
        ])

        conn.commit()


seed_dummy_data()


# ──────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────────────────

def dict_factory(cursor, row):
    """Convert sqlite3 rows to dictionaries."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_conn():
    """Get a database connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    return conn


# ══════════════════════════════════════════════════════════════════════
# 1. UNIT TRACKING TOOLS
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def add_building(name: str, address: str, total_floors: int = 1) -> str:
    """Add a new building/property to the system.
    
    Args:
        name: Name of the building (e.g., 'Sunrise Apartments')
        address: Full address of the building
        total_floors: Number of floors in the building
    """
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO buildings (name, address, total_floors) VALUES (?, ?, ?)",
                (name, address, total_floors)
            )
            return json.dumps({"status": "success", "message": f"Building '{name}' added successfully."})
    except sqlite3.IntegrityError:
        return json.dumps({"status": "error", "message": f"Building '{name}' already exists."})


@mcp.tool()
def add_room(building_name: str, room_number: str, floor: int, room_type: str, monthly_rent: float) -> str:
    """Add a new room/unit to an existing building.
    
    Args:
        building_name: Name of the building this room belongs to
        room_number: Room identifier (e.g., '101', 'A-12')
        floor: Floor number where the room is located
        room_type: Type of room — 'single', 'double', 'studio', 'suite'
        monthly_rent: Monthly rent amount for this room
    """
    with get_conn() as conn:
        building = conn.execute("SELECT id FROM buildings WHERE name = ?", (building_name,)).fetchone()
        if not building:
            return json.dumps({"status": "error", "message": f"Building '{building_name}' not found."})
        try:
            conn.execute(
                "INSERT INTO rooms (building_id, room_number, floor, room_type, monthly_rent) VALUES (?, ?, ?, ?, ?)",
                (building["id"], room_number, floor, room_type, monthly_rent)
            )
            return json.dumps({"status": "success", "message": f"Room '{room_number}' added to '{building_name}'."})
        except sqlite3.IntegrityError:
            return json.dumps({"status": "error", "message": f"Room '{room_number}' already exists in '{building_name}'."})


@mcp.tool()
def list_vacant_rooms(building_name: str = "") -> str:
    """List all vacant rooms, optionally filtered by building name.
    
    Args:
        building_name: Optional — filter by building name. Leave empty for all buildings.
    """
    with get_conn() as conn:
        if building_name:
            rooms = conn.execute("""
                SELECT r.room_number, r.floor, r.room_type, r.monthly_rent, b.name as building
                FROM rooms r JOIN buildings b ON r.building_id = b.id
                WHERE r.status = 'vacant' AND b.name = ?
                ORDER BY b.name, r.floor, r.room_number
            """, (building_name,)).fetchall()
        else:
            rooms = conn.execute("""
                SELECT r.room_number, r.floor, r.room_type, r.monthly_rent, b.name as building
                FROM rooms r JOIN buildings b ON r.building_id = b.id
                WHERE r.status = 'vacant'
                ORDER BY b.name, r.floor, r.room_number
            """).fetchall()
        return json.dumps({"vacant_rooms": rooms, "count": len(rooms)})


@mcp.tool()
def update_room_status(building_name: str, room_number: str, status: str) -> str:
    """Update the occupancy status of a room.
    
    Args:
        building_name: Name of the building
        room_number: Room identifier
        status: New status — 'vacant', 'occupied', 'maintenance', 'reserved'
    """
    valid_statuses = ['vacant', 'occupied', 'maintenance', 'reserved']
    if status not in valid_statuses:
        return json.dumps({"status": "error", "message": f"Invalid status. Choose from: {valid_statuses}"})
    
    with get_conn() as conn:
        result = conn.execute("""
            UPDATE rooms SET status = ?
            WHERE room_number = ? AND building_id = (SELECT id FROM buildings WHERE name = ?)
        """, (status, room_number, building_name))
        if result.rowcount == 0:
            return json.dumps({"status": "error", "message": "Room not found."})
        return json.dumps({"status": "success", "message": f"Room '{room_number}' status updated to '{status}'."})


# ══════════════════════════════════════════════════════════════════════
# 2. TENANT PROFILE TOOLS
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def add_tenant(name: str, phone: str, email: str = "", emergency_contact: str = "") -> str:
    """Add a new tenant profile to the system.
    
    Args:
        name: Full name of the tenant
        phone: Primary phone number
        email: Email address (optional)
        emergency_contact: Emergency contact number (optional)
    """
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO tenants (name, phone, email, emergency_contact) VALUES (?, ?, ?, ?)",
            (name, phone, email, emergency_contact)
        )
        return json.dumps({
            "status": "success",
            "tenant_id": cursor.lastrowid,
            "message": f"Tenant '{name}' added successfully."
        })


@mcp.tool()
def assign_tenant_to_room(tenant_name: str, building_name: str, room_number: str, move_in_date: str,
                           lease_end_date: str, security_deposit: float = 0, late_fee_per_day: float = 50,
                           grace_period_days: int = 5) -> str:
    """Assign a tenant to a specific room and create a lease agreement.
    
    Args:
        tenant_name: Name of the tenant
        building_name: Name of the building
        room_number: Room number to assign
        move_in_date: Move-in date (YYYY-MM-DD)
        lease_end_date: Lease end date (YYYY-MM-DD)
        security_deposit: Security deposit amount
        late_fee_per_day: Late fee charged per day after grace period
        grace_period_days: Number of days after due date before late fees kick in
    """
    with get_conn() as conn:
        tenant = conn.execute("SELECT id FROM tenants WHERE name = ?", (tenant_name,)).fetchone()
        if not tenant:
            return json.dumps({"status": "error", "message": f"Tenant '{tenant_name}' not found."})

        room = conn.execute("""
            SELECT r.id, r.monthly_rent, r.status FROM rooms r
            JOIN buildings b ON r.building_id = b.id
            WHERE r.room_number = ? AND b.name = ?
        """, (room_number, building_name)).fetchone()
        if not room:
            return json.dumps({"status": "error", "message": "Room not found."})
        if room["status"] != "vacant":
            return json.dumps({"status": "error", "message": f"Room is currently '{room['status']}', not vacant."})

        # Create assignment
        conn.execute(
            "INSERT INTO tenant_room_assignments (tenant_id, room_id, move_in_date) VALUES (?, ?, ?)",
            (tenant["id"], room["id"], move_in_date)
        )
        # Create lease
        conn.execute("""
            INSERT INTO lease_agreements (tenant_id, room_id, start_date, end_date, monthly_rent,
                security_deposit, late_fee_per_day, grace_period_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tenant["id"], room["id"], move_in_date, lease_end_date, room["monthly_rent"],
              security_deposit, late_fee_per_day, grace_period_days))
        # Mark room occupied
        conn.execute("UPDATE rooms SET status = 'occupied' WHERE id = ?", (room["id"],))
        return json.dumps({
            "status": "success",
            "message": f"'{tenant_name}' assigned to Room '{room_number}' in '{building_name}'. Lease created until {lease_end_date}."
        })


@mcp.tool()
def get_tenant_history(tenant_name: str) -> str:
    """Get full history of a tenant — room assignments, payments, and maintenance requests.
    
    Args:
        tenant_name: Name of the tenant to look up
    """
    with get_conn() as conn:
        tenant = conn.execute("SELECT * FROM tenants WHERE name = ?", (tenant_name,)).fetchone()
        if not tenant:
            return json.dumps({"status": "error", "message": f"Tenant '{tenant_name}' not found."})

        assignments = conn.execute("""
            SELECT r.room_number, b.name as building, tra.move_in_date, tra.move_out_date, tra.is_active
            FROM tenant_room_assignments tra
            JOIN rooms r ON tra.room_id = r.id
            JOIN buildings b ON r.building_id = b.id
            WHERE tra.tenant_id = ?
            ORDER BY tra.move_in_date DESC
        """, (tenant["id"],)).fetchall()

        payments = conn.execute("""
            SELECT p.amount, p.payment_date, p.payment_month, p.payment_mode, p.late_fee, p.note,
                   r.room_number, b.name as building
            FROM payments p
            JOIN rooms r ON p.room_id = r.id
            JOIN buildings b ON r.building_id = b.id
            WHERE p.tenant_id = ?
            ORDER BY p.payment_date DESC LIMIT 20
        """, (tenant["id"],)).fetchall()

        maintenance = conn.execute("""
            SELECT m.category, m.description, m.priority, m.status, m.escalation_level, m.created_at
            FROM maintenance_requests m WHERE m.tenant_id = ?
            ORDER BY m.created_at DESC LIMIT 10
        """, (tenant["id"],)).fetchall()

        return json.dumps({
            "tenant": tenant,
            "room_assignments": assignments,
            "recent_payments": payments,
            "recent_maintenance": maintenance
        })


@mcp.tool()
def record_id_verification(tenant_name: str, id_type: str, id_number: str) -> str:
    """Record and verify a tenant's government ID.
    
    Args:
        tenant_name: Name of the tenant
        id_type: Type of ID — 'aadhaar', 'pan', 'passport', 'voter_id', 'driving_license'
        id_number: ID document number
    """
    valid_id_types = ['aadhaar', 'pan', 'passport', 'voter_id', 'driving_license']
    if id_type not in valid_id_types:
        return json.dumps({"status": "error", "message": f"Invalid ID type. Choose from: {valid_id_types}"})

    with get_conn() as conn:
        result = conn.execute(
            "UPDATE tenants SET id_type = ?, id_number = ?, id_verified = 1 WHERE name = ?",
            (id_type, id_number, tenant_name)
        )
        if result.rowcount == 0:
            return json.dumps({"status": "error", "message": f"Tenant '{tenant_name}' not found."})
        return json.dumps({"status": "success", "message": f"ID verified for '{tenant_name}' ({id_type}: {id_number})."})


# ══════════════════════════════════════════════════════════════════════
# 3. RENT & PAYMENT TOOLS
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def record_payment(tenant_name: str, building_name: str, room_number: str,
                   amount: float, payment_date: str, payment_month: str,
                   payment_mode: str = "cash", note: str = "") -> str:
    """Record a rent payment from a tenant.
    
    Args:
        tenant_name: Name of the tenant making the payment
        building_name: Building name
        room_number: Room number
        amount: Amount paid
        payment_date: Date of payment (YYYY-MM-DD)
        payment_month: Which month this payment is for (YYYY-MM)
        payment_mode: Payment method — 'cash', 'upi', 'bank_transfer', 'cheque'
        note: Any additional notes
    """
    with get_conn() as conn:
        tenant = conn.execute("SELECT id FROM tenants WHERE name = ?", (tenant_name,)).fetchone()
        if not tenant:
            return json.dumps({"status": "error", "message": f"Tenant '{tenant_name}' not found."})

        room = conn.execute("""
            SELECT r.id FROM rooms r JOIN buildings b ON r.building_id = b.id
            WHERE r.room_number = ? AND b.name = ?
        """, (room_number, building_name)).fetchone()
        if not room:
            return json.dumps({"status": "error", "message": "Room not found."})

        # Calculate late fee automatically
        late_fee = _calculate_late_fee(conn, tenant["id"], room["id"], payment_date, payment_month)

        conn.execute("""
            INSERT INTO payments (tenant_id, room_id, amount, payment_date, payment_month, payment_mode, late_fee, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tenant["id"], room["id"], amount, payment_date, payment_month, payment_mode, late_fee, note))

        result: dict = {"status": "success", "message": f"Payment of ₹{amount} recorded for '{tenant_name}'."}
        if late_fee > 0:
            result["late_fee_applied"] = late_fee
            result["message"] += f" Late fee of ₹{late_fee} was applied."
        return json.dumps(result)


def _calculate_late_fee(conn, tenant_id: int, room_id: int, payment_date: str, payment_month: str) -> float:
    """Internal helper to calculate late fee based on lease terms."""
    lease = conn.execute("""
        SELECT late_fee_per_day, grace_period_days FROM lease_agreements
        WHERE tenant_id = ? AND room_id = ? AND is_active = 1
    """, (tenant_id, room_id)).fetchone()

    if not lease:
        return 0

    # Due date is the 1st of the payment month + grace period
    try:
        due_date = datetime.strptime(payment_month + "-01", "%Y-%m-%d")
        grace_end = due_date + timedelta(days=lease["grace_period_days"])
        pay_date = datetime.strptime(payment_date, "%Y-%m-%d")

        if pay_date > grace_end:
            days_late = (pay_date - grace_end).days
            return round(days_late * lease["late_fee_per_day"], 2)
    except (ValueError, TypeError):
        pass
    return 0


@mcp.tool()
def get_pending_dues(building_name: str = "", month: str = "") -> str:
    """Get all pending/unpaid rent dues. Highlights overdue tenants.
    
    Args:
        building_name: Optional — filter by building name
        month: Month to check (YYYY-MM). Defaults to current month.
    """
    if not month:
        month = datetime.now().strftime("%Y-%m")

    with get_conn() as conn:
        query = """
            SELECT t.name as tenant_name, t.phone, r.room_number, b.name as building,
                   r.monthly_rent, la.grace_period_days, la.late_fee_per_day
            FROM tenant_room_assignments tra
            JOIN tenants t ON tra.tenant_id = t.id
            JOIN rooms r ON tra.room_id = r.id
            JOIN buildings b ON r.building_id = b.id
            LEFT JOIN lease_agreements la ON la.tenant_id = t.id AND la.room_id = r.id AND la.is_active = 1
            WHERE tra.is_active = 1
        """
        params = []
        if building_name:
            query += " AND b.name = ?"
            params.append(building_name)

        active_tenants = conn.execute(query, params).fetchall()
        pending = []

        for tenant_info in active_tenants:
            # Check if payment exists for this month
            payment = conn.execute("""
                SELECT SUM(amount) as total_paid FROM payments p
                JOIN tenants t ON p.tenant_id = t.id
                WHERE t.name = ? AND p.payment_month = ?
            """, (tenant_info["tenant_name"], month)).fetchone()

            total_paid = payment["total_paid"] or 0
            rent = tenant_info["monthly_rent"] or 0
            remaining = rent - total_paid

            if remaining > 0:
                # Calculate current late fee
                today = datetime.now().strftime("%Y-%m-%d")
                grace_days = tenant_info["grace_period_days"] or 5
                fee_per_day = tenant_info["late_fee_per_day"] or 50
                due_date = datetime.strptime(month + "-01", "%Y-%m-%d")
                grace_end = due_date + timedelta(days=grace_days)
                days_late = max(0, (datetime.now() - grace_end).days)
                current_late_fee = round(days_late * fee_per_day, 2) if days_late > 0 else 0

                pending.append({
                    "tenant": tenant_info["tenant_name"],
                    "phone": tenant_info["phone"],
                    "building": tenant_info["building"],
                    "room": tenant_info["room_number"],
                    "monthly_rent": rent,
                    "paid": total_paid,
                    "remaining": remaining,
                    "days_overdue": days_late,
                    "accumulated_late_fee": current_late_fee
                })

        return json.dumps({"month": month, "pending_dues": pending, "total_defaulters": len(pending)})


@mcp.tool()
def get_payment_history(tenant_name: str = "", building_name: str = "", limit: int = 50) -> str:
    """Get payment history with filters.
    
    Args:
        tenant_name: Optional — filter by tenant name
        building_name: Optional — filter by building name
        limit: Maximum number of records to return (default 50)
    """
    with get_conn() as conn:
        query = """
            SELECT t.name as tenant, r.room_number as room, b.name as building,
                   p.amount, p.payment_date, p.payment_month, p.payment_mode, p.late_fee, p.note
            FROM payments p
            JOIN tenants t ON p.tenant_id = t.id
            JOIN rooms r ON p.room_id = r.id
            JOIN buildings b ON r.building_id = b.id
            WHERE 1=1
        """
        params = []
        if tenant_name:
            query += " AND t.name = ?"
            params.append(tenant_name)
        if building_name:
            query += " AND b.name = ?"
            params.append(building_name)
        query += " ORDER BY p.payment_date DESC LIMIT ?"
        params.append(limit)

        payments = conn.execute(query, params).fetchall()
        total_collected = sum(p["amount"] for p in payments)
        total_late_fees = sum(p["late_fee"] for p in payments)
        return json.dumps({
            "payments": payments,
            "total_records": len(payments),
            "total_collected": total_collected,
            "total_late_fees_collected": total_late_fees
        })


# ══════════════════════════════════════════════════════════════════════
# 4. LATE FEE, PENALTY & ESCALATION TOOLS
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def calculate_late_fee(tenant_name: str, payment_month: str) -> str:
    """Calculate the current late fee for a tenant for a given month.
    
    Args:
        tenant_name: Name of the tenant
        payment_month: The month to check (YYYY-MM)
    """
    with get_conn() as conn:
        tenant = conn.execute("SELECT id FROM tenants WHERE name = ?", (tenant_name,)).fetchone()
        if not tenant:
            return json.dumps({"status": "error", "message": f"Tenant '{tenant_name}' not found."})

        lease = conn.execute("""
            SELECT la.*, r.room_number, b.name as building FROM lease_agreements la
            JOIN rooms r ON la.room_id = r.id
            JOIN buildings b ON r.building_id = b.id
            WHERE la.tenant_id = ? AND la.is_active = 1
        """, (tenant["id"],)).fetchone()

        if not lease:
            return json.dumps({"status": "error", "message": "No active lease found."})

        # Check payments already made
        paid = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) as total FROM payments
            WHERE tenant_id = ? AND room_id = ? AND payment_month = ?
        """, (tenant["id"], lease["room_id"], payment_month)).fetchone()

        remaining = lease["monthly_rent"] - paid["total"]
        if remaining <= 0:
            return json.dumps({"status": "paid", "message": "Rent is fully paid for this month.", "late_fee": 0})

        due_date = datetime.strptime(payment_month + "-01", "%Y-%m-%d")
        grace_end = due_date + timedelta(days=lease["grace_period_days"])
        days_late = max(0, (datetime.now() - grace_end).days)
        late_fee = round(days_late * lease["late_fee_per_day"], 2) if days_late > 0 else 0

        # Determine escalation level
        if days_late > 30:
            escalation = "CRITICAL — Consider eviction notice"
        elif days_late > 15:
            escalation = "HIGH — Send formal demand letter"
        elif days_late > 7:
            escalation = "MEDIUM — Personal follow-up call needed"
        elif days_late > 0:
            escalation = "LOW — Send payment reminder"
        else:
            escalation = "NONE — Within grace period"

        return json.dumps({
            "tenant": tenant_name,
            "building": lease["building"],
            "room": lease["room_number"],
            "monthly_rent": lease["monthly_rent"],
            "paid": paid["total"],
            "remaining_rent": remaining,
            "days_overdue": days_late,
            "late_fee": late_fee,
            "total_due": round(remaining + late_fee, 2),
            "escalation_level": escalation
        })


@mcp.tool()
def get_overdue_escalation_report(month: str = "") -> str:
    """Generate an escalation report for all overdue tenants — sorted by severity.
    
    Args:
        month: Month to check (YYYY-MM). Defaults to current month.
    """
    if not month:
        month = datetime.now().strftime("%Y-%m")

    with get_conn() as conn:
        active_leases = conn.execute("""
            SELECT la.tenant_id, la.room_id, la.monthly_rent, la.grace_period_days, la.late_fee_per_day,
                   t.name as tenant_name, t.phone, r.room_number, b.name as building
            FROM lease_agreements la
            JOIN tenants t ON la.tenant_id = t.id
            JOIN rooms r ON la.room_id = r.id
            JOIN buildings b ON r.building_id = b.id
            WHERE la.is_active = 1
        """).fetchall()

        escalations = []
        for lease in active_leases:
            paid = conn.execute("""
                SELECT COALESCE(SUM(amount), 0) as total FROM payments
                WHERE tenant_id = ? AND room_id = ? AND payment_month = ?
            """, (lease["tenant_id"], lease["room_id"], month)).fetchone()

            remaining = lease["monthly_rent"] - paid["total"]
            if remaining <= 0:
                continue

            due_date = datetime.strptime(month + "-01", "%Y-%m-%d")
            grace_end = due_date + timedelta(days=lease["grace_period_days"])
            days_late = max(0, (datetime.now() - grace_end).days)

            if days_late <= 0:
                continue

            late_fee = round(days_late * lease["late_fee_per_day"], 2)

            if days_late > 30:
                level = "CRITICAL"
                action = "Issue eviction notice / legal action"
            elif days_late > 15:
                level = "HIGH"
                action = "Send formal demand letter via registered post"
            elif days_late > 7:
                level = "MEDIUM"
                action = "Make personal follow-up call"
            else:
                level = "LOW"
                action = "Send SMS/WhatsApp payment reminder"

            escalations.append({
                "tenant": lease["tenant_name"],
                "phone": lease["phone"],
                "building": lease["building"],
                "room": lease["room_number"],
                "days_overdue": days_late,
                "remaining_rent": remaining,
                "late_fee": late_fee,
                "total_due": round(remaining + late_fee, 2),
                "escalation_level": level,
                "recommended_action": action
            })

        # Sort by days overdue (most critical first)
        escalations.sort(key=lambda x: x["days_overdue"], reverse=True)

        return json.dumps({
            "month": month,
            "overdue_tenants": escalations,
            "total_overdue": len(escalations),
            "total_outstanding": round(sum(e["total_due"] for e in escalations), 2)
        })


# ══════════════════════════════════════════════════════════════════════
# 5. MAINTENANCE REQUEST TOOLS
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def raise_maintenance_request(tenant_name: str, building_name: str, room_number: str,
                               category: str, description: str, priority: str = "medium") -> str:
    """Raise a maintenance/repair request as a tenant.
    
    Args:
        tenant_name: Name of the tenant raising the request
        building_name: Building name
        room_number: Room number
        category: Category — 'plumbing', 'electrical', 'furniture', 'appliance', 'pest_control', 'structural', 'other'
        description: Detailed description of the issue
        priority: Priority level — 'low', 'medium', 'high', 'urgent'
    """
    valid_categories = ['plumbing', 'electrical', 'furniture', 'appliance', 'pest_control', 'structural', 'other']
    valid_priorities = ['low', 'medium', 'high', 'urgent']

    if category not in valid_categories:
        return json.dumps({"status": "error", "message": f"Invalid category. Choose from: {valid_categories}"})
    if priority not in valid_priorities:
        return json.dumps({"status": "error", "message": f"Invalid priority. Choose from: {valid_priorities}"})

    with get_conn() as conn:
        tenant = conn.execute("SELECT id FROM tenants WHERE name = ?", (tenant_name,)).fetchone()
        if not tenant:
            return json.dumps({"status": "error", "message": f"Tenant '{tenant_name}' not found."})

        room = conn.execute("""
            SELECT r.id FROM rooms r JOIN buildings b ON r.building_id = b.id
            WHERE r.room_number = ? AND b.name = ?
        """, (room_number, building_name)).fetchone()
        if not room:
            return json.dumps({"status": "error", "message": "Room not found."})

        cursor = conn.execute("""
            INSERT INTO maintenance_requests (tenant_id, room_id, category, description, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (tenant["id"], room["id"], category, description, priority))

        return json.dumps({
            "status": "success",
            "request_id": cursor.lastrowid,
            "message": f"Maintenance request #{cursor.lastrowid} created — {category} ({priority} priority)."
        })


@mcp.tool()
def escalate_maintenance_request(request_id: int, reason: str = "") -> str:
    """Escalate an unresolved maintenance request to a higher priority level.
    
    Args:
        request_id: The maintenance request ID to escalate
        reason: Reason for escalation
    """
    with get_conn() as conn:
        request = conn.execute("SELECT * FROM maintenance_requests WHERE id = ?", (request_id,)).fetchone()
        if not request:
            return json.dumps({"status": "error", "message": f"Request #{request_id} not found."})
        if request["status"] == "resolved":
            return json.dumps({"status": "error", "message": "Cannot escalate a resolved request."})

        new_level = request["escalation_level"] + 1
        priority_map = {0: "medium", 1: "high", 2: "urgent"}
        new_priority = priority_map.get(new_level, "urgent")

        conn.execute("""
            UPDATE maintenance_requests
            SET escalation_level = ?, priority = ?, escalated_at = datetime('now')
            WHERE id = ?
        """, (new_level, new_priority, request_id))

        escalation_labels = {1: "Escalated to property manager", 2: "Escalated to owner/vendor", 3: "Critical — needs immediate external contractor"}
        label = escalation_labels.get(new_level, f"Escalation level {new_level}")

        return json.dumps({
            "status": "success",
            "request_id": request_id,
            "new_priority": new_priority,
            "escalation_level": new_level,
            "escalation_action": label,
            "message": f"Request #{request_id} escalated. {label}."
        })


@mcp.tool()
def resolve_maintenance_request(request_id: int, resolution_note: str = "") -> str:
    """Mark a maintenance request as resolved.
    
    Args:
        request_id: The maintenance request ID to resolve
        resolution_note: Note about how the issue was resolved
    """
    with get_conn() as conn:
        result = conn.execute("""
            UPDATE maintenance_requests SET status = 'resolved', resolved_at = datetime('now')
            WHERE id = ? AND status != 'resolved'
        """, (request_id,))
        if result.rowcount == 0:
            return json.dumps({"status": "error", "message": "Request not found or already resolved."})
        return json.dumps({"status": "success", "message": f"Request #{request_id} marked as resolved."})


@mcp.tool()
def get_open_maintenance_requests(building_name: str = "", priority: str = "") -> str:
    """List all open/unresolved maintenance requests.
    
    Args:
        building_name: Optional — filter by building
        priority: Optional — filter by priority ('low', 'medium', 'high', 'urgent')
    """
    with get_conn() as conn:
        query = """
            SELECT m.id, t.name as tenant, r.room_number as room, b.name as building,
                   m.category, m.description, m.priority, m.status, m.escalation_level,
                   m.created_at, m.escalated_at
            FROM maintenance_requests m
            JOIN tenants t ON m.tenant_id = t.id
            JOIN rooms r ON m.room_id = r.id
            JOIN buildings b ON r.building_id = b.id
            WHERE m.status != 'resolved'
        """
        params = []
        if building_name:
            query += " AND b.name = ?"
            params.append(building_name)
        if priority:
            query += " AND m.priority = ?"
            params.append(priority)
        query += " ORDER BY CASE m.priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, m.created_at ASC"

        requests = conn.execute(query, params).fetchall()
        return json.dumps({"open_requests": requests, "total": len(requests)})


# ══════════════════════════════════════════════════════════════════════
# 6. BUSINESS DASHBOARD / ANALYTICS TOOLS
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def occupancy_rate(building_name: str = "") -> str:
    """Calculate occupancy rate — overall or per building.
    
    Args:
        building_name: Optional — specific building to check. Leave empty for overall rate.
    """
    with get_conn() as conn:
        if building_name:
            stats = conn.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN r.status = 'occupied' THEN 1 ELSE 0 END) as occupied,
                       SUM(CASE WHEN r.status = 'vacant' THEN 1 ELSE 0 END) as vacant,
                       SUM(CASE WHEN r.status = 'maintenance' THEN 1 ELSE 0 END) as under_maintenance
                FROM rooms r JOIN buildings b ON r.building_id = b.id
                WHERE b.name = ?
            """, (building_name,)).fetchone()
        else:
            stats = conn.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) as occupied,
                       SUM(CASE WHEN status = 'vacant' THEN 1 ELSE 0 END) as vacant,
                       SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as under_maintenance
                FROM rooms
            """).fetchone()

        total = stats["total"] or 0
        occupied = stats["occupied"] or 0
        rate = round((occupied / total * 100), 2) if total > 0 else 0

        return json.dumps({
            "building": building_name or "ALL",
            "total_rooms": total,
            "occupied": occupied,
            "vacant": stats["vacant"] or 0,
            "under_maintenance": stats["under_maintenance"] or 0,
            "occupancy_rate_percent": rate
        })


@mcp.tool()
def revenue_trend(months: int = 6) -> str:
    """Get monthly revenue trend for the last N months.
    
    Args:
        months: Number of past months to include (default 6)
    """
    with get_conn() as conn:
        revenue = conn.execute("""
            SELECT payment_month, SUM(amount) as total_revenue, SUM(late_fee) as total_late_fees,
                   COUNT(DISTINCT tenant_id) as paying_tenants
            FROM payments
            GROUP BY payment_month
            ORDER BY payment_month DESC
            LIMIT ?
        """, (months,)).fetchall()

        return json.dumps({
            "revenue_trend": revenue,
            "months_covered": len(revenue),
            "total_revenue": round(sum(r["total_revenue"] for r in revenue), 2) if revenue else 0
        })


@mcp.tool()
def collection_efficiency(month: str = "") -> str:
    """Calculate rent collection efficiency for a given month.
    
    Collection Efficiency = (Total Collected / Total Expected) × 100
    
    Args:
        month: Month to check (YYYY-MM). Defaults to current month.
    """
    if not month:
        month = datetime.now().strftime("%Y-%m")

    with get_conn() as conn:
        # Total expected from active leases
        expected = conn.execute("""
            SELECT COALESCE(SUM(monthly_rent), 0) as total
            FROM lease_agreements WHERE is_active = 1
        """).fetchone()

        # Total collected for the month
        collected = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) as total, COALESCE(SUM(late_fee), 0) as late_fees
            FROM payments WHERE payment_month = ?
        """, (month,)).fetchone()

        expected_total = expected["total"] or 0
        collected_total = collected["total"] or 0
        efficiency = round((collected_total / expected_total * 100), 2) if expected_total > 0 else 0

        return json.dumps({
            "month": month,
            "expected_revenue": expected_total,
            "collected_revenue": collected_total,
            "late_fees_collected": collected["late_fees"],
            "collection_efficiency_percent": efficiency,
            "shortfall": round(expected_total - collected_total, 2)
        })


# ══════════════════════════════════════════════════════════════════════
# 7. LEASE MANAGEMENT TOOLS
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def get_expiring_leases(days: int = 30) -> str:
    """Get leases expiring within the next N days — proactive renewal alert.
    
    Args:
        days: Number of days to look ahead (default 30)
    """
    with get_conn() as conn:
        cutoff = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        leases = conn.execute("""
            SELECT t.name as tenant, t.phone, r.room_number as room, b.name as building,
                   la.start_date, la.end_date, la.monthly_rent,
                   CAST(julianday(la.end_date) - julianday(?) AS INTEGER) as days_remaining
            FROM lease_agreements la
            JOIN tenants t ON la.tenant_id = t.id
            JOIN rooms r ON la.room_id = r.id
            JOIN buildings b ON r.building_id = b.id
            WHERE la.is_active = 1 AND la.end_date <= ? AND la.end_date >= ?
            ORDER BY la.end_date ASC
        """, (today, cutoff, today)).fetchall()

        return json.dumps({
            "expiring_within_days": days,
            "leases": leases,
            "total": len(leases)
        })


# ══════════════════════════════════════════════════════════════════════
# 8. UTILITY — LIST ALL TOOLS
# ══════════════════════════════════════════════════════════════════════

@mcp.tool()
def list_all_tools() -> str:
    """List all available tools in this MCP server with their descriptions."""
    tools = [
        {"category": "🏢 Unit Tracking", "tools": [
            {"name": "add_building", "description": "Add a new building/property"},
            {"name": "add_room", "description": "Add a room/unit to a building"},
            {"name": "list_vacant_rooms", "description": "List all vacant rooms"},
            {"name": "update_room_status", "description": "Update room occupancy status"},
        ]},
        {"category": "👤 Tenant Profiles", "tools": [
            {"name": "add_tenant", "description": "Register a new tenant"},
            {"name": "assign_tenant_to_room", "description": "Assign tenant to room with lease"},
            {"name": "get_tenant_history", "description": "Full tenant history — rooms, payments, maintenance"},
            {"name": "record_id_verification", "description": "Verify tenant's government ID"},
        ]},
        {"category": "💰 Rent & Payments", "tools": [
            {"name": "record_payment", "description": "Record a rent payment (auto-calculates late fee)"},
            {"name": "get_pending_dues", "description": "View all unpaid/pending rent dues"},
            {"name": "get_payment_history", "description": "Full payment audit trail"},
        ]},
        {"category": "⚠️ Late Fees & Escalation", "tools": [
            {"name": "calculate_late_fee", "description": "Calculate current late fee for a tenant"},
            {"name": "get_overdue_escalation_report", "description": "Severity-sorted overdue tenant report"},
        ]},
        {"category": "🔧 Maintenance", "tools": [
            {"name": "raise_maintenance_request", "description": "Raise a repair/maintenance request"},
            {"name": "escalate_maintenance_request", "description": "Escalate unresolved request to higher level"},
            {"name": "resolve_maintenance_request", "description": "Mark a request as resolved"},
            {"name": "get_open_maintenance_requests", "description": "List all open maintenance requests"},
        ]},
        {"category": "📊 Business Dashboard", "tools": [
            {"name": "occupancy_rate", "description": "Occupancy rate — overall or per building"},
            {"name": "revenue_trend", "description": "Monthly revenue trend"},
            {"name": "collection_efficiency", "description": "Rent collection efficiency percentage"},
        ]},
        {"category": "📋 Lease Management", "tools": [
            {"name": "get_expiring_leases", "description": "Proactive lease renewal alerts"},
        ]},
        {"category": "🛠️ Utility", "tools": [
            {"name": "list_all_tools", "description": "List all available MCP tools"},
        ]},
    ]
    return json.dumps({"mcp_server": "PropertyManager", "total_tools": 20, "tools_by_category": tools})
