"""
================================================================================
MEDISTOCK — HOSPITAL MEDICAL SUPPLIES INVENTORY MANAGEMENT SYSTEM
MODULE 2: SQLite3 Relational Database & Persistence Layer
================================================================================
Provides relational schema initialization, WAL concurrency settings (preventing
`sqlite3.OperationalError: database is locked`), and hospital seed data across
all 6 required inventory categories and 6 hospital departments.
================================================================================
"""

import datetime
import os
import sqlite3
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medistock_hospital.db")

HOSPITAL_DEPARTMENTS = [
    "Emergency",
    "General Ward",
    "ICU",
    "Operation Theatre",
    "Pediatric Ward",
    "Pharmacy",
]
DEPARTMENTS = HOSPITAL_DEPARTMENTS

INVENTORY_CATEGORIES = [
    "Medicines",
    "Surgical supplies",
    "Emergency supplies",
    "Medical equipment",
    "Protective equipment",
    "IV supplies",
]
CATEGORIES = INVENTORY_CATEGORIES


def get_connection() -> sqlite3.Connection:
    """
    Opens a SQLite3 connection with a 30-second timeout and WAL journal mode
    so concurrent UI reads/writes never raise `database is locked`.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA synchronous=NORMAL")
    except sqlite3.Error:
        pass
    return conn


def init_database() -> None:
    """Initializes all 7 relational tables and seeds initial hospital data if empty."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. Medicine & Medical Supplies Catalog Table (Product records — separate from Batches)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            category TEXT NOT NULL,
            dosage_form TEXT NOT NULL,
            unit TEXT NOT NULL,
            min_threshold INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            storage_req TEXT NOT NULL,
            description TEXT
        )
        """)

        # 2. Suppliers Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            lead_time_days INTEGER DEFAULT 2,
            status TEXT DEFAULT 'Active'
        )
        """)

        # 3. Stock Batches Table (One Medicine ID can have multiple Batch records)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            batch_id TEXT PRIMARY KEY,
            batch_number TEXT NOT NULL,
            medicine_id TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            supplier_name TEXT NOT NULL,
            initial_quantity INTEGER NOT NULL,
            remaining_quantity INTEGER NOT NULL,
            mfg_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            arrival_date TEXT NOT NULL,
            batch_status TEXT NOT NULL,
            storage_bin TEXT,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        )
        """)

        # 4. Incoming Stock Queue Persistence Table (Core DSA Queue #1)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS incoming_queue_items (
            queue_order INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE NOT NULL,
            batch_number TEXT NOT NULL,
            medicine_id TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            category TEXT NOT NULL,
            supplier_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            mfg_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            arrival_time TEXT NOT NULL,
            condition_note TEXT DEFAULT 'Good / Sealed'
        )
        """)

        # 5. Department Requisitions Table (Core DSA Queue #2 + History)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS requisitions (
            queue_order INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            medicine_id TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            quantity_requested INTEGER NOT NULL,
            quantity_fulfilled INTEGER DEFAULT 0,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            request_time TEXT NOT NULL,
            processed_time TEXT,
            notes TEXT
        )
        """)

        # 6. Quarantine & Damaged/Recalled/Expired Stock Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quarantine (
            quarantine_id TEXT PRIMARY KEY,
            batch_id TEXT NOT NULL,
            medicine_id TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            supplier_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reason TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            logged_at TEXT NOT NULL,
            action_status TEXT NOT NULL
        )
        """)

        # 7. FIFO & Inventory Transactions Audit Log
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            tx_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            tx_type TEXT NOT NULL,
            reference_id TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            department_or_supplier TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            details TEXT NOT NULL,
            operator TEXT NOT NULL
        )
        """)

        conn.commit()

        cursor.execute("SELECT COUNT(*) as cnt FROM medicines")
        if cursor.fetchone()["cnt"] == 0:
            _seed_initial_data(conn)
    finally:
        conn.close()


# Alias for backward compatibility
init_db = init_database


def _seed_initial_data(conn: sqlite3.Connection) -> None:
    """Seeds realistic hospital inventory data across all 6 categories and 6 departments."""
    cursor = conn.cursor()
    today = datetime.date.today()

    def fmt_date(delta_days: int) -> str:
        return (today + datetime.timedelta(days=delta_days)).strftime("%Y-%m-%d")

    # 1. Seed Catalog (12 items covering all 6 required categories)
    medicines_seed = [
        ("MED-101", "Amoxicillin + Clavulanate 625mg", "AMC-625", "Medicines", "Tablet", "Tablets", 150, 1.45, "Cool & Dry (<25°C)", "Broad-spectrum beta-lactam antibiotic"),
        ("MED-102", "Paracetamol IV Infusion 1g/100mL", "PCM-1000", "Medicines", "Infusion", "Vials", 120, 3.80, "Room Temp (15-25°C)", "Antipyretic and analgesic IV solution"),
        ("MED-103", "Sterile Latex Surgical Gloves (Size 7.5)", "GLV-75S", "Surgical supplies", "Sterile Pair", "Pairs", 300, 0.95, "Dry Sterile Cabinet", "Powder-free sterile surgical gloves"),
        ("MED-104", "Disposable Luer-Lock Syringes 10mL", "SYR-10ML", "Surgical supplies", "Syringe", "Pieces", 400, 0.35, "Standard Store", "Sterile single-use hypodermic syringes"),
        ("MED-105", "Epinephrine Auto-Injector 1mg/mL", "EPI-1MG", "Emergency supplies", "Ampoule", "Ampoules", 80, 11.50, "Light-Protected (2-8°C)", "Emergency anaphylaxis and cardiac resuscitation"),
        ("MED-106", "Trauma & First-Aid Hemostatic Kit", "TRM-KIT1", "Emergency supplies", "Kit", "Kits", 50, 28.00, "Emergency Bay", "Comprehensive emergency bleeding control kit"),
        ("MED-107", "Digital Infrared Clinical Thermometer", "THM-IR2", "Medical equipment", "Device", "Units", 40, 34.00, "Equipment Rack", "Non-contact hospital grade thermometer"),
        ("MED-108", "Multiparameter Patient Vital Monitor", "MON-VP5", "Medical equipment", "Monitor", "Units", 15, 420.00, "Biomed Store", "ECG, SpO2, NIBP bedside monitor"),
        ("MED-109", "N95 Particulate Respirator Masks", "MSK-N95", "Protective equipment", "Mask", "Masks", 500, 1.15, "PPE Bay", "NIOSH-approved healthcare respirator mask"),
        ("MED-110", "Level-3 Fluid Resistant Isolation Gowns", "GWN-L3", "Protective equipment", "Gown", "Gowns", 250, 4.20, "PPE Bay", "Sterile barrier protection gown"),
        ("MED-111", "Normal Saline 0.9% NaCl IV Fluid 500mL", "NS-500ML", "IV supplies", "IV Bag", "Bags", 350, 1.90, "IV Fluid Rack", "Isotonic crystalloid intravenous fluid"),
        ("MED-112", "IV Infusion Giving Set with Burette", "IVS-BUR", "IV supplies", "IV Set", "Sets", 200, 2.40, "Sterile Supply", "Precision pediatric and ICU IV administration set"),
    ]
    cursor.executemany(
        "INSERT INTO medicines VALUES (?,?,?,?,?,?,?,?,?,?)",
        medicines_seed,
    )

    # 2. Seed Suppliers
    suppliers_seed = [
        ("SUP-01", "Apex Pharma & Surgical Co.", "+1-800-555-0191", "orders@apexpharma.med", "410 Medical Park Blvd, Suite 200", 2, "Active"),
        ("SUP-02", "BioCare Hospital Logistics", "+1-800-555-0244", "supply@biocarelogistics.org", "88 LifeScience Way, Sector 4", 1, "Active"),
        ("SUP-03", "MedEquip Global Instruments", "+1-800-555-0377", "dispatch@medequipglobal.com", "1900 Innovation Drive", 3, "Active"),
        ("SUP-04", "SterileGuard PPE & IV Systems", "+1-800-555-0412", "clinical@sterileguard.io", "72 Healthcare Industrial Zone", 2, "Active"),
        ("SUP-05", "NovaMed Emergency Therapeutics", "+1-800-555-0588", "urgent@novamed-rx.com", "505 ColdChain Avenue", 1, "Active"),
    ]
    cursor.executemany(
        "INSERT INTO suppliers VALUES (?,?,?,?,?,?,?)",
        suppliers_seed,
    )

    # 3. Seed Stock Batches (Multiple batches per product, including normal, expiring-soon, and expired)
    batches_seed = [
        ("B-1001", "LOT-AMC-24A", "MED-101", "Amoxicillin + Clavulanate 625mg", "Apex Pharma & Surgical Co.", 300, 220, fmt_date(-180), fmt_date(120), fmt_date(-60), "Available", "Rack A-01"),
        ("B-1002", "LOT-AMC-24B", "MED-101", "Amoxicillin + Clavulanate 625mg", "Apex Pharma & Surgical Co.", 200, 180, fmt_date(-90), fmt_date(240), fmt_date(-20), "Available", "Rack A-02"),
        ("B-1003", "LOT-PCM-88", "MED-102", "Paracetamol IV Infusion 1g/100mL", "BioCare Hospital Logistics", 200, 95, fmt_date(-200), fmt_date(18), fmt_date(-45), "Available", "Rack B-04"),
        ("B-1004", "LOT-GLV-01", "MED-103", "Sterile Latex Surgical Gloves (Size 7.5)", "SterileGuard PPE & IV Systems", 500, 410, fmt_date(-120), fmt_date(310), fmt_date(-30), "Available", "Cabinet S-1"),
        ("B-1005", "LOT-SYR-19", "MED-104", "Disposable Luer-Lock Syringes 10mL", "Apex Pharma & Surgical Co.", 600, 480, fmt_date(-150), fmt_date(400), fmt_date(-25), "Available", "Cabinet S-2"),
        ("B-1006", "LOT-EPI-09", "MED-105", "Epinephrine Auto-Injector 1mg/mL", "NovaMed Emergency Therapeutics", 100, 45, fmt_date(-300), fmt_date(14), fmt_date(-90), "Available", "ColdBay C-1"),
        ("B-1007", "LOT-TRM-04", "MED-106", "Trauma & First-Aid Hemostatic Kit", "NovaMed Emergency Therapeutics", 60, 32, fmt_date(-100), fmt_date(190), fmt_date(-15), "Available", "Bay E-2"),
        ("B-1008", "LOT-THM-12", "MED-107", "Digital Infrared Clinical Thermometer", "MedEquip Global Instruments", 50, 28, fmt_date(-210), fmt_date(600), fmt_date(-40), "Available", "Equip E-1"),
        ("B-1009", "LOT-MON-02", "MED-108", "Multiparameter Patient Vital Monitor", "MedEquip Global Instruments", 20, 9, fmt_date(-180), fmt_date(900), fmt_date(-50), "Available", "Biomed M-1"),
        ("B-1010", "LOT-N95-77", "MED-109", "N95 Particulate Respirator Masks", "SterileGuard PPE & IV Systems", 600, 520, fmt_date(-80), fmt_date(365), fmt_date(-12), "Available", "PPE-01"),
        ("B-1011", "LOT-GWN-33", "MED-110", "Level-3 Fluid Resistant Isolation Gowns", "SterileGuard PPE & IV Systems", 300, 270, fmt_date(-70), fmt_date(290), fmt_date(-10), "Available", "PPE-02"),
        ("B-1012", "LOT-NS-501", "MED-111", "Normal Saline 0.9% NaCl IV Fluid 500mL", "BioCare Hospital Logistics", 450, 390, fmt_date(-110), fmt_date(210), fmt_date(-18), "Available", "IV-Rack-1"),
        ("B-1013", "LOT-IVS-14", "MED-112", "IV Infusion Giving Set with Burette", "BioCare Hospital Logistics", 250, 215, fmt_date(-95), fmt_date(260), fmt_date(-14), "Available", "IV-Rack-2"),
        ("B-1014", "LOT-PCM-OLD", "MED-102", "Paracetamol IV Infusion 1g/100mL", "BioCare Hospital Logistics", 80, 40, fmt_date(-420), fmt_date(-5), fmt_date(-200), "Expired", "Quarantine-Bay"),
    ]
    cursor.executemany(
        "INSERT INTO batches VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        batches_seed,
    )

    # 4. Seed Incoming Stock Queue (Core DSA Queue #1: B001 -> B002 -> B003 -> B004)
    incoming_seed = [
        ("B001", "LOT-GLV-NEW1", "MED-103", "Sterile Latex Surgical Gloves (Size 7.5)", "Surgical supplies", "SterileGuard PPE & IV Systems", 250, fmt_date(-20), fmt_date(340), "08:15 AM", "Good / Sealed"),
        ("B002", "LOT-EPI-NEW2", "MED-105", "Epinephrine Auto-Injector 1mg/mL", "Emergency supplies", "NovaMed Emergency Therapeutics", 75, fmt_date(-15), fmt_date(180), "08:42 AM", "Cold-Chain Verified"),
        ("B003", "LOT-NS-NEW3", "MED-111", "Normal Saline 0.9% NaCl IV Fluid 500mL", "IV supplies", "BioCare Hospital Logistics", 300, fmt_date(-10), fmt_date(365), "09:10 AM", "Good / Sealed"),
        ("B004", "LOT-AMC-EXP", "MED-101", "Amoxicillin + Clavulanate 625mg", "Medicines", "Apex Pharma & Surgical Co.", 90, fmt_date(-380), fmt_date(-10), "09:35 AM", "Expired Seal Alert"),
    ]
    for row in incoming_seed:
        cursor.execute(
            """
            INSERT INTO incoming_queue_items
            (batch_id, batch_number, medicine_id, medicine_name, category, supplier_name,
             quantity, mfg_date, expiry_date, arrival_time, condition_note)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            row,
        )

    # 5. Seed Department Requisitions (Core DSA Queue #2: R001 -> R002 -> R003 -> R004 + Processed across all 6 departments)
    requisitions_seed = [
        ("R001", "Emergency", "Dr. Sarah Jenkins", "MED-103", "Sterile Latex Surgical Gloves (Size 7.5)", 60, 0, "Urgent", "Pending", "08:30 AM", None, "Trauma bay restock"),
        ("R002", "ICU", "Dr. Omar Farooq", "MED-109", "N95 Particulate Respirator Masks", 80, 0, "High", "Pending", "08:50 AM", None, "ICU isolation unit"),
        ("R003", "General Ward", "Nurse Clara Mensah", "MED-111", "Normal Saline 0.9% NaCl IV Fluid 500mL", 70, 0, "Normal", "Pending", "09:05 AM", None, "Daily ward IV rounds"),
        ("R004", "Operation Theatre", "Dr. Viktor Petrov", "MED-104", "Disposable Luer-Lock Syringes 10mL", 100, 0, "Urgent", "Pending", "09:20 AM", None, "OT Schedule Block A"),
        ("R005", "Pediatric Ward", "Dr. Amina Tariq", "MED-112", "IV Infusion Giving Set with Burette", 45, 0, "High", "Pending", "09:40 AM", None, "Pediatric infusion pumps"),
        ("R006", "Pharmacy", "Chief Pharm. H. Raza", "MED-101", "Amoxicillin + Clavulanate 625mg", 90, 90, "Normal", "Completed", "Yesterday 02:15 PM", "Yesterday 02:40 PM", "Dispensary counter refill"),
        ("R007", "Emergency", "Dr. Sarah Jenkins", "MED-105", "Epinephrine Auto-Injector 1mg/mL", 25, 25, "Urgent", "Completed", "Yesterday 04:00 PM", "Yesterday 04:12 PM", "Crash cart replenishment"),
    ]
    for row in requisitions_seed:
        cursor.execute(
            """
            INSERT INTO requisitions
            (request_id, department, requested_by, medicine_id, medicine_name,
             quantity_requested, quantity_fulfilled, priority, status, request_time, processed_time, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            row,
        )

    # 6. Seed Quarantine Table
    quarantine_seed = [
        ("QRN-01", "B-1014", "MED-102", "Paracetamol IV Infusion 1g/100mL", "BioCare Hospital Logistics", 40, "Expired Batch Detected", fmt_date(-5), fmt_date(-1), "Quarantined - Awaiting Disposal"),
        ("QRN-02", "B-0992", "MED-111", "Normal Saline 0.9% NaCl IV Fluid 500mL", "BioCare Hospital Logistics", 25, "Damaged Outer Carton in Transit", fmt_date(180), fmt_date(-3), "Quarantined - Return to Supplier"),
    ]
    cursor.executemany(
        "INSERT INTO quarantine VALUES (?,?,?,?,?,?,?,?,?,?)",
        quarantine_seed,
    )

    # 7. Seed Transactions Audit Log
    tx_seed = [
        ("TX-9001", fmt_date(-2) + " 10:15", "BATCH_APPROVE", "B-1010", "N95 Particulate Respirator Masks", "SterileGuard PPE & IV Systems", 520, "Dequeued & Approved into PPE-01", "Inventory Manager"),
        ("TX-9002", fmt_date(-1) + " 14:40", "REQ_ISSUE", "R006", "Amoxicillin + Clavulanate 625mg", "Pharmacy", 90, "FEFO Issued from Batch B-1001", "Inventory Manager"),
        ("TX-9003", fmt_date(-1) + " 16:12", "REQ_ISSUE", "R007", "Epinephrine Auto-Injector 1mg/mL", "Emergency", 25, "FEFO Issued from Batch B-1006", "Inventory Manager"),
        ("TX-9004", fmt_date(-1) + " 17:05", "QUARANTINE", "B-1014", "Paracetamol IV Infusion 1g/100mL", "BioCare Hospital Logistics", 40, "Moved to Quarantine (Expired)", "Quality Officer"),
    ]
    cursor.executemany(
        "INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?)",
        tx_seed,
    )

    conn.commit()


def log_transaction(
    tx_type: str,
    reference_id: str,
    medicine_name: str,
    dept_or_supplier: str,
    quantity: int,
    details: str,
    operator: str = "Inventory Manager",
    conn: Optional[sqlite3.Connection] = None,
) -> str:
    """
    Safely records an audit transaction in SQLite.
    Accepts an optional existing `conn` or opens/closes its own WAL connection.
    """
    owns_conn = conn is None
    active_conn = conn if conn is not None else get_connection()
    try:
        cursor = active_conn.cursor()
        tx_id = f"TX-{int(datetime.datetime.now().timestamp() * 100) % 1000000:06d}"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?)",
            (tx_id, now_str, tx_type, reference_id, medicine_name, dept_or_supplier, int(quantity), details, operator),
        )
        if owns_conn:
            active_conn.commit()
        return tx_id
    finally:
        if owns_conn:
            active_conn.close()
