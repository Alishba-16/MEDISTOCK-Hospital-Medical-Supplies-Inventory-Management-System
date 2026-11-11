"""
================================================================================
MEDISTOCK — HOSPITAL MEDICAL SUPPLIES INVENTORY MANAGEMENT SYSTEM
MODULE 3: Hospital Reports & Analytics Exporter (CSV & PDF 1.4)
================================================================================
Generates all 10 required hospital reports from PROJECT_INSTRUCTIONS.docx:
  1. Complete Inventory Report
  2. Medicine-Wise Stock Report
  3. Batch-Wise Stock Report
  4. Department Requisition Report
  5. Pending Request Report
  6. Completed Request Report
  7. Supplier Report
  8. Expiry Report
  9. Low-Stock Report
 10. FIFO Processing History

Supports one-click export to both UTF-8 CSV and standalone multi-page PDF 1.4.
================================================================================
"""

import csv
import datetime
from typing import Dict, List, Optional, Tuple
import database

REPORT_DEFINITIONS = [
    ("1. Complete Inventory Report", "complete_inventory"),
    ("2. Medicine-Wise Stock Report", "medicine_wise"),
    ("3. Batch-Wise Stock Report", "batch_wise"),
    ("4. Department Requisition Report", "department_requisitions"),
    ("5. Pending Request Report (FIFO Queue)", "pending_requests"),
    ("6. Completed Request Report", "completed_requests"),
    ("7. Supplier Report", "supplier_report"),
    ("8. Expiry & Quarantine Report", "expiry_report"),
    ("9. Low-Stock Alert Report", "low_stock_report"),
    ("10. FIFO Processing History", "fifo_history"),
]

# Format (key, title) for test suite convenience
REPORT_TYPES: List[Tuple[str, str]] = [(key, title) for title, key in REPORT_DEFINITIONS]


def fetch_report_data(report_key: str) -> Dict[str, object]:
    """Queries the SQLite database and returns `{title, columns, rows}` for any of the 10 reports."""
    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        soon_str = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        if report_key == "complete_inventory":
            cursor.execute("""
                SELECT m.id, m.name, m.code, m.category, m.unit, m.min_threshold,
                       COALESCE(SUM(CASE WHEN b.batch_status='Available' AND b.expiry_date >= ? THEN b.remaining_quantity ELSE 0 END), 0) AS avail_qty,
                       COUNT(b.batch_id) AS batch_cnt,
                       ROUND(m.unit_cost * COALESCE(SUM(CASE WHEN b.batch_status='Available' THEN b.remaining_quantity ELSE 0 END), 0), 2) AS stock_val
                FROM medicines m
                LEFT JOIN batches b ON m.id = b.medicine_id
                GROUP BY m.id
                ORDER BY m.id
            """, (today_str,))
            rows = [
                [r["id"], r["name"], r["code"], r["category"], r["unit"], r["min_threshold"], r["avail_qty"], r["batch_cnt"], f"${r['stock_val']:.2f}"]
                for r in cursor.fetchall()
            ]
            return {
                "title": "Complete Hospital Inventory Report",
                "columns": ["Item ID", "Medicine / Supply Name", "Code", "Category", "Unit", "Min Level", "Available Qty", "Batches", "Total Value"],
                "rows": rows,
            }

        if report_key == "medicine_wise":
            cursor.execute("""
                SELECT m.id, m.name, m.category, m.dosage_form, m.storage_req,
                       COALESCE(SUM(CASE WHEN b.batch_status='Available' AND b.expiry_date >= ? THEN b.remaining_quantity ELSE 0 END), 0) AS avail_qty,
                       m.min_threshold
                FROM medicines m
                LEFT JOIN batches b ON m.id = b.medicine_id
                GROUP BY m.id
                ORDER BY m.category, m.name
            """, (today_str,))
            rows = []
            for r in cursor.fetchall():
                status = "HEALTHY" if r["avail_qty"] >= r["min_threshold"] else ("OUT OF STOCK" if r["avail_qty"] == 0 else "LOW STOCK")
                rows.append([r["id"], r["name"], r["category"], r["dosage_form"], r["storage_req"], r["avail_qty"], r["min_threshold"], status])
            return {
                "title": "Medicine-Wise Stock Summary Report",
                "columns": ["Item ID", "Item Name", "Category", "Form", "Storage Condition", "Available Stock", "Min Level", "Status"],
                "rows": rows,
            }

        if report_key == "batch_wise":
            cursor.execute("""
                SELECT batch_id, batch_number, medicine_id, medicine_name, supplier_name,
                       initial_quantity, remaining_quantity, mfg_date, expiry_date, arrival_date, batch_status
                FROM batches
                ORDER BY expiry_date ASC
            """)
            rows = [
                [r["batch_id"], r["batch_number"], r["medicine_id"], r["medicine_name"], r["supplier_name"],
                 r["initial_quantity"], r["remaining_quantity"], r["mfg_date"], r["expiry_date"], r["batch_status"]]
                for r in cursor.fetchall()
            ]
            return {
                "title": "Batch-Wise Stock Report (FEFO Sorted)",
                "columns": ["Batch ID", "Lot #", "Item ID", "Medicine / Supply", "Supplier", "Initial", "Remaining", "Mfg Date", "Expiry Date", "Status"],
                "rows": rows,
            }

        if report_key == "department_requisitions":
            cursor.execute("""
                SELECT request_id, department, requested_by, medicine_name,
                       quantity_requested, quantity_fulfilled, priority, status, request_time
                FROM requisitions
                ORDER BY queue_order ASC
            """)
            rows = [
                [r["request_id"], r["department"], r["requested_by"], r["medicine_name"],
                 r["quantity_requested"], r["quantity_fulfilled"], r["priority"], r["status"], r["request_time"]]
                for r in cursor.fetchall()
            ]
            return {
                "title": "Department Requisition Report (All Departments)",
                "columns": ["Req ID", "Department", "Requested By", "Item Name", "Req Qty", "Issued Qty", "Priority", "Status", "Submitted"],
                "rows": rows,
            }

        if report_key == "pending_requests":
            cursor.execute("""
                SELECT request_id, department, requested_by, medicine_name,
                       quantity_requested, priority, request_time, notes
                FROM requisitions
                WHERE status = 'Pending'
                ORDER BY queue_order ASC
            """)
            rows = [
                [idx + 1, r["request_id"], r["department"], r["requested_by"], r["medicine_name"],
                 r["quantity_requested"], r["priority"], r["request_time"], r["notes"] or "-"]
                for idx, r in enumerate(cursor.fetchall())
            ]
            return {
                "title": "Pending Department Requests Report (Active FIFO Queue Order)",
                "columns": ["Queue Pos", "Req ID", "Department", "Requested By", "Item Name", "Qty Needed", "Priority", "Queued At", "Notes"],
                "rows": rows,
            }

        if report_key == "completed_requests":
            cursor.execute("""
                SELECT request_id, department, requested_by, medicine_name,
                       quantity_requested, quantity_fulfilled, status, request_time, processed_time
                FROM requisitions
                WHERE status IN ('Completed', 'Partially Fulfilled')
                ORDER BY queue_order DESC
            """)
            rows = [
                [r["request_id"], r["department"], r["requested_by"], r["medicine_name"],
                 r["quantity_requested"], r["quantity_fulfilled"], r["status"], r["request_time"], r["processed_time"] or "-"]
                for r in cursor.fetchall()
            ]
            return {
                "title": "Completed & Fulfilled Department Requisitions Report",
                "columns": ["Req ID", "Department", "Officer", "Item Name", "Requested", "Fulfilled", "Status", "Requested At", "Completed At"],
                "rows": rows,
            }

        if report_key == "supplier_report":
            cursor.execute("""
                SELECT s.supplier_id, s.name, s.contact_number, s.email, s.lead_time_days, s.status,
                       COUNT(b.batch_id) AS batches_delivered,
                       COALESCE(SUM(b.initial_quantity), 0) AS total_units_delivered
                FROM suppliers s
                LEFT JOIN batches b ON s.name = b.supplier_name
                GROUP BY s.supplier_id
                ORDER BY s.supplier_id
            """)
            rows = [
                [r["supplier_id"], r["name"], r["contact_number"], r["email"],
                 f"{r['lead_time_days']} days", r["status"], r["batches_delivered"], r["total_units_delivered"]]
                for r in cursor.fetchall()
            ]
            return {
                "title": "Supplier Directory & Delivery Performance Report",
                "columns": ["Supplier ID", "Supplier Name", "Contact", "Email", "Lead Time", "Status", "Batches", "Units Supplied"],
                "rows": rows,
            }

        if report_key == "expiry_report":
            cursor.execute("""
                SELECT batch_id, batch_number, medicine_name, supplier_name,
                       remaining_quantity, expiry_date, batch_status
                FROM batches
                WHERE expiry_date <= ? OR batch_status != 'Available'
                ORDER BY expiry_date ASC
            """, (soon_str,))
            rows = []
            for r in cursor.fetchall():
                alert = "EXPIRED" if r["expiry_date"] < today_str else "EXPIRING SOON (<30d)"
                rows.append([r["batch_id"], r["batch_number"], r["medicine_name"], r["supplier_name"],
                             r["remaining_quantity"], r["expiry_date"], r["batch_status"], alert])
            return {
                "title": "Expiry & Near-Expiry Batch Alert Report",
                "columns": ["Batch ID", "Lot #", "Medicine / Supply", "Supplier", "Remaining Qty", "Expiry Date", "Status", "Alert Level"],
                "rows": rows,
            }

        if report_key == "low_stock_report":
            cursor.execute("""
                SELECT m.id, m.name, m.category, m.unit, m.min_threshold,
                       COALESCE(SUM(CASE WHEN b.batch_status='Available' AND b.expiry_date >= ? THEN b.remaining_quantity ELSE 0 END), 0) AS avail_qty
                FROM medicines m
                LEFT JOIN batches b ON m.id = b.medicine_id
                GROUP BY m.id
                HAVING avail_qty < m.min_threshold
                ORDER BY (m.min_threshold - avail_qty) DESC
            """, (today_str,))
            rows = []
            for r in cursor.fetchall():
                deficit = max(0, r["min_threshold"] - r["avail_qty"])
                suggested_order = max(deficit * 2, r["min_threshold"])
                rows.append([r["id"], r["name"], r["category"], r["unit"], r["avail_qty"], r["min_threshold"], deficit, suggested_order])
            return {
                "title": "Low-Stock & Restocking Suggestions Report",
                "columns": ["Item ID", "Item Name", "Category", "Unit", "Current Stock", "Min Required", "Shortfall", "Suggested Reorder"],
                "rows": rows,
            }

        # Default / 10. FIFO Processing History
        cursor.execute("""
            SELECT tx_id, timestamp, tx_type, reference_id, medicine_name,
                   department_or_supplier, quantity, details, operator
            FROM transactions
            ORDER BY timestamp DESC
        """)
        rows = [
            [r["tx_id"], r["timestamp"], r["tx_type"], r["reference_id"],
             r["medicine_name"], r["department_or_supplier"], r["quantity"], r["details"]]
            for r in cursor.fetchall()
        ]
        return {
            "title": "FIFO Queue & Inventory Processing History Report",
            "columns": ["Tx ID", "Timestamp", "Operation Type", "Ref ID", "Item Name", "Dept / Supplier", "Qty", "Details"],
            "rows": rows,
        }
    finally:
        conn.close()


def generate_report_data(report_key: str) -> Tuple[List[str], List[List[object]]]:
    """Returns `(headers, rows)` tuple for `report_key`."""
    data = fetch_report_data(report_key)
    return list(data["columns"]), list(data["rows"])


def export_to_csv(
    report_or_key: object,
    filepath: str,
    rows: Optional[List[List[object]]] = None,
    title: str = "",
) -> str:
    """Exports report data to a formatted UTF-8 CSV file."""
    if isinstance(report_or_key, str):
        report_data = fetch_report_data(report_or_key)
    elif isinstance(report_or_key, dict):
        report_data = report_or_key
    else:
        report_data = {
            "title": title or "MediStock Report",
            "columns": list(report_or_key),
            "rows": rows or [],
        }

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([f"MEDISTOCK HOSPITAL INVENTORY SYSTEM - {str(report_data['title']).upper()}"])
        writer.writerow([f"Generated At: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([])
        writer.writerow(report_data["columns"])
        for row in report_data["rows"]:
            writer.writerow(row)
    return filepath


def _pdf_escape(text: str) -> str:
    clean = str(text).encode("ascii", "replace").decode("ascii")
    return clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def export_to_pdf(
    report_or_key: object,
    filepath: str,
    rows: Optional[List[List[object]]] = None,
    title: str = "",
) -> str:
    """
    Generates a clean, multi-page landscape PDF 1.4 document using pure Python
    (zero external dependencies required).
    """
    if isinstance(report_or_key, str):
        report_data = fetch_report_data(report_or_key)
    elif isinstance(report_or_key, dict):
        report_data = report_or_key
    else:
        report_data = {
            "title": title or "MediStock Report",
            "columns": list(report_or_key),
            "rows": rows or [],
        }

    doc_title = str(report_data.get("title", "MediStock Report"))
    columns = [str(c) for c in report_data.get("columns", [])]
    data_rows = [[str(cell) for cell in r] for r in report_data.get("rows", [])]
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    col_widths = []
    for idx, col in enumerate(columns):
        max_len = len(col)
        for r in data_rows:
            if idx < len(r):
                max_len = max(max_len, min(26, len(r[idx])))
        col_widths.append(max(max_len + 2, 8))

    def format_table_line(cells: List[str]) -> str:
        parts = []
        for idx, cell in enumerate(cells):
            w = col_widths[idx] if idx < len(col_widths) else 12
            val = cell[: w - 1] if len(cell) >= w else cell
            parts.append(val.ljust(w))
        return " | ".join(parts)[:132]

    header_line = format_table_line(columns)
    sep_line = "-" * len(header_line)

    rows_per_page = 26
    chunks = [data_rows[i: i + rows_per_page] for i in range(0, max(1, len(data_rows)), rows_per_page)]

    objects: List[bytes] = []

    def add_obj(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    font_helv_id = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    font_mono_id = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_ids: List[int] = []
    content_ids: List[int] = []

    for page_num, chunk in enumerate(chunks, start=1):
        stream_lines = [
            "BT",
            "/F1 14 Tf",
            "36 555 Td",
            f"(MEDISTOCK - {_pdf_escape(doc_title.upper())}) Tj",
            "/F2 8.5 Tf",
            "0 -16 Td",
            f"(Generated: {_pdf_escape(now_str)}   |   Queue Architecture: Singly Linked List FIFO   |   Page {page_num} of {len(chunks)}) Tj",
            "0 -14 Td",
            f"({_pdf_escape(sep_line)}) Tj",
            "0 -12 Td",
            f"({_pdf_escape(header_line)}) Tj",
            "0 -12 Td",
            f"({_pdf_escape(sep_line)}) Tj",
        ]
        if not chunk:
            stream_lines.append("0 -14 Td")
            stream_lines.append("(No records found for this report criteria.) Tj")
        else:
            for r in chunk:
                line_str = format_table_line(r)
                stream_lines.append("0 -13 Td")
                stream_lines.append(f"({_pdf_escape(line_str)}) Tj")

        stream_lines.append("0 -14 Td")
        stream_lines.append(f"({_pdf_escape(sep_line)}) Tj")
        stream_lines.append("ET")

        stream_bytes = "\n".join(stream_lines).encode("latin-1", "replace")
        content_id = add_obj(
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"\nendstream"
        )
        content_ids.append(content_id)

    pages_placeholder_id = add_obj(b"")

    for content_id in content_ids:
        page_body = (
            f"<< /Type /Page /Parent {pages_placeholder_id} 0 R "
            f"/MediaBox [0 0 842 595] "
            f"/Resources << /Font << /F1 {font_helv_id} 0 R /F2 {font_mono_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")
        page_ids.append(add_obj(page_body))

    kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[pages_placeholder_id - 1] = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_ids)} >>".encode("ascii")
    catalog_id = add_obj(f"<< /Type /Catalog /Pages {pages_placeholder_id} 0 R >>".encode("ascii"))

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: List[int] = []
    for idx, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{idx} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")

    xref_pos = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for off in offsets:
        output.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )

    with open(filepath, "wb") as f:
        f.write(output)

    return filepath
