# MediStock — Hospital Medical Supplies Inventory Management System

A complete Python Desktop GUI application built from scratch according to `PROJECT_INSTRUCTIONS.docx`. Every module is cleanly separated (no mixed code or mixed layouts):

---

## 📁 Project Architecture (Clean & Modular)

1. **`queue_dsa.py`** — **Manual Singly Linked List Queue (`Node` & `Queue`)**
   - Built from scratch using explicit `front` and `rear` pointers (never uses `collections.deque` or SQL `ORDER BY` as a substitute for the Queue).
   - Implements all **9 required methods**:
     - `enqueue(item)` — $O(1)$ insertion at `rear`
     - `dequeue()` — $O(1)$ removal from `front` (resets `rear = None` when removing the last element)
     - `peek()` — $O(1)$ front element inspection
     - `is_empty()` — $O(1)$ empty check
     - `size()` — $O(1)$ element count
     - `display()` — $O(n)$ traversal from `front` to `rear`
     - `search(id)` — $O(n)$ lookup without altering queue order
     - `delete(id)` — $O(n)$ node removal preserving FIFO order (handles front, middle, rear, and single-element edge cases)
     - `update(id, data)` — $O(n)$ in-place node update preserving order

2. **`database.py`** — **Lock-Free SQLite3 Relational Persistence (`WAL` Mode)**
   - Uses `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=30000`, and `timeout=30.0` so concurrent GUI operations never trigger `sqlite3.OperationalError: database is locked`.
   - Keeps **Product Catalog records (`medicines`) strictly separate from Batch records (`batches`)** (one medicine can have multiple batches).
   - Seeds all **6 required categories** (`Medicines`, `Surgical supplies`, `Emergency supplies`, `Medical equipment`, `Protective equipment`, `IV supplies`) and all **6 hospital departments** (`Emergency`, `General Ward`, `ICU`, `Operation Theatre`, `Pediatric Ward`, `Pharmacy`).

3. **`reports_exporter.py`** — **10 Hospital Reports & Analytics (CSV & PDF 1.4)**
   - Generates and exports all **10 required reports** to both UTF-8 CSV and standalone multi-page PDF 1.4.

4. **`main.py`** — **9-Module Desktop GUI with Pure Un-Mixed Inspiration Layouts**
   - **Pure Inspiration Layouts** (switchable in top header without mixing styles together):
     - **💜 Inspo 1: Lavender 3D Clay** (Faithful to `image1.png`)
     - **🌿 Inspo 2: Pharmacy Mint** (Faithful to `image2.png`)
     - **🌸 Inspo 3: Pastel Peach & Lavender** (Faithful to `image3.png`)
   - **9 Dedicated Hospital Modules** in the left navigation sidebar.

---

## 🚀 How to Run the Project

### Windows (PowerShell / Command Prompt)
```powershell
py main.py
```
*(Or double-click `run_desktop.bat`)*

### Linux / macOS
```bash
python3 main.py
```

### Run the Automated Unit Tests
```powershell
py test_medistock.py
```
