"""
================================================================================
MEDISTOCK — HOSPITAL MEDICAL SUPPLIES INVENTORY MANAGEMENT SYSTEM
MAIN DESKTOP APPLICATION (Inspo 1 Lavender 3D Clay GUI + 9 Hospital Modules)
================================================================================
Implements all 9 required hospital modules from PROJECT_INSTRUCTIONS.docx:
  1. Dashboard (Lavender 3D Claymorphism — Inspo 1)
  2. Medicines & Supplies (Catalog CRUD — separate from Batch records)
  3. Stock Batches (Individual Batch CRUD — linked to Medicine ID)
  4. Incoming Queue (Core DSA Module #1 — Manual Singly Linked List Queue)
  5. Requisition Queue (Core DSA Module #2 — Manual Singly Linked List Queue)
  6. FIFO Stock Issuing (FIFO Request Fulfillment + Expiry Validation)
  7. Suppliers (Supplier Directory CRUD + Delivery Tracking)
  8. Expiry & Alerts (Expired, Near-Expiry, Low-Stock & Quarantine)
  9. Reports & Exports (All 10 Hospital Reports with CSV & PDF Export)
================================================================================
"""

import datetime
import os
import random
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Callable, Dict, List, Optional, Tuple

import database
from queue_dsa import LinkedListQueue, Node, Queue
import reports_exporter

FONT_FAMILY = "Segoe UI" if sys.platform.startswith("win") else "Helvetica"
MONO_FAMILY = "Consolas" if sys.platform.startswith("win") else "Courier"


def fnt(size: int, weight: str = "normal") -> Tuple[str, int, str]:
    """
    Uses negative (pixel-locked) font sizes so text height matches tk.Canvas
    pixel coordinates 1:1 on Windows (100%/125%/150% DPI scaling) and Linux.
    """
    px = -max(10, int(round(abs(size) * 1.3333)))
    return (FONT_FAMILY, px, weight)


def mfnt(size: int, weight: str = "normal") -> Tuple[str, int, str]:
    """Pixel-locked monospace font for memory addresses and queue pointers."""
    px = -max(9, int(round(abs(size) * 1.3333)))
    return (MONO_FAMILY, px, weight)


# ==============================================================================
# INSPO 1: LAVENDER 3D CLAYMORPHISM PALETTE
# ==============================================================================
THEME: Dict[str, str] = {
    "outer_bg": "#D9CEF8",
    "sidebar_bg": "#8D75E6",
    "sidebar_hi": "#B29FF5",
    "sidebar_sh": "#6F58C9",
    "sidebar_item_bg": "#7E66D8",
    "sidebar_active_bg": "#FFFFFF",
    "sidebar_active_fg": "#2E1F5E",
    "sidebar_fg": "#FFFFFF",
    "board_bg": "#FAF7F5",
    "card_bg": "#FFFFFF",
    "card_border": "#E6DFF5",
    "card_shadow": "#E5DDF5",
    "text_primary": "#2C1E55",
    "text_secondary": "#6E6290",
    "accent": "#8369E3",
    "accent_hover": "#6D52D1",
    "accent_soft": "#EFEAFD",
    "table_header_bg": "#8369E3",
    "table_header_fg": "#FFFFFF",
    "table_even": "#FFFFFF",
    "table_odd": "#F5F1FD",
    "success": "#269956",
    "warning": "#D97F24",
    "danger": "#DC4758",
}


# ==============================================================================
# CANVAS DRAWING HELPERS (3D Clay Cards, Pills, Character & Plant Illustrations)
# ==============================================================================
def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float = 18,
    fill: str = "#FFFFFF",
    outline: str = "",
    width: int = 1,
    tags: Any = None,
) -> int:
    if x2 <= x1 or y2 <= y1:
        return 0
    r = max(2.0, min(radius, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    pts = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(
        pts,
        smooth=True,
        splinesteps=32,
        fill=fill,
        outline=outline if outline else fill,
        width=width,
        tags=tags,
    )


def draw_clay_card(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float = 20,
    fill: str = "#FFFFFF",
    shadow: str = "#E5DDF5",
    highlight: str = "#FFFFFF",
    border: str = "#E6DFF5",
) -> None:
    """Draws a soft 3D claymorphic card with outer drop-shadow and top specular highlight."""
    draw_rounded_rect(canvas, x1 + 2, y1 + 4, x2 + 2, y2 + 4, radius=radius, fill=shadow, outline=shadow)
    draw_rounded_rect(canvas, x1, y1, x2, y2, radius=radius, fill=fill, outline=border, width=1)
    if highlight and (y2 - y1) > 24:
        draw_rounded_rect(canvas, x1 + 2, y1 + 2, x2 - 2, y1 + 9, radius=max(4, radius - 4), fill=highlight, outline="")


def draw_pill_button(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    text: str,
    bg: str,
    fg: str = "#FFFFFF",
    shadow: str = "",
    font_spec: Optional[Tuple[str, int, str]] = None,
    on_click: Optional[Callable[[], None]] = None,
) -> str:
    tag = f"btn_{int(x1)}_{int(y1)}_{random.randint(1000, 9999)}"
    r = (y2 - y1) / 2.0
    if shadow:
        draw_rounded_rect(canvas, x1 + 1, y1 + 3, x2 + 1, y2 + 3, radius=r, fill=shadow, outline=shadow, tags=(tag,))
    draw_rounded_rect(canvas, x1, y1, x2, y2, radius=r, fill=bg, outline=bg, tags=(tag,))
    canvas.create_text(
        (x1 + x2) / 2.0,
        (y1 + y2) / 2.0,
        text=text,
        fill=fg,
        font=font_spec or fnt(9, "bold"),
        tags=(tag,),
    )
    if on_click is not None:
        canvas.tag_bind(tag, "<Button-1>", lambda _e: on_click())
        canvas.tag_bind(tag, "<Enter>", lambda _e: canvas.config(cursor="hand2"))
        canvas.tag_bind(tag, "<Leave>", lambda _e: canvas.config(cursor=""))
    return tag


def draw_3d_avatar(canvas: tk.Canvas, cx: float, cy: float, scale: float = 1.0, with_headphones: bool = True) -> None:
    """Draws the 3D clay character illustration from Inspo 1."""
    s = scale
    canvas.create_oval(cx - 34 * s, cy - 30 * s, cx + 34 * s, cy + 38 * s, fill="#C3B0EE", outline="")
    canvas.create_oval(cx - 16 * s, cy - 42 * s, cx + 16 * s, cy - 16 * s, fill="#5C3A28", outline="#472B1C", width=1)
    canvas.create_oval(cx - 28 * s, cy - 26 * s, cx + 28 * s, cy + 20 * s, fill="#4E3020", outline="")
    draw_rounded_rect(canvas, cx - 30 * s, cy + 10 * s, cx + 30 * s, cy + 38 * s, radius=14 * s, fill="#9E84F0", outline="#866BE0")
    canvas.create_rectangle(cx - 7 * s, cy + 3 * s, cx + 7 * s, cy + 15 * s, fill="#F5C6A8", outline="")
    canvas.create_oval(cx - 21 * s, cy - 21 * s, cx + 21 * s, cy + 14 * s, fill="#FAD2B8", outline="#F0BE9E", width=1)
    canvas.create_oval(cx - 15 * s, cy - 3 * s, cx - 7 * s, cy + 3 * s, fill="#F5A3A3", outline="")
    canvas.create_oval(cx + 7 * s, cy - 3 * s, cx + 15 * s, cy + 3 * s, fill="#F5A3A3", outline="")
    canvas.create_arc(cx - 13 * s, cy - 10 * s, cx - 4 * s, cy - 2 * s, start=0, extent=180, style=tk.ARC, outline="#3B2418", width=2)
    canvas.create_arc(cx + 4 * s, cy - 10 * s, cx + 13 * s, cy - 2 * s, start=0, extent=180, style=tk.ARC, outline="#3B2418", width=2)
    canvas.create_arc(cx - 7 * s, cy - 2 * s, cx + 7 * s, cy + 6 * s, start=200, extent=140, style=tk.ARC, outline="#8A3E36", width=2)
    canvas.create_arc(cx - 21 * s, cy - 23 * s, cx + 21 * s, cy + 3 * s, start=25, extent=130, fill="#5C3A28", outline="")
    if with_headphones:
        canvas.create_arc(cx - 25 * s, cy - 25 * s, cx + 25 * s, cy + 14 * s, start=15, extent=150, style=tk.ARC, outline="#8E74EB", width=int(max(3, 4 * s)))
        canvas.create_oval(cx - 28 * s, cy - 10 * s, cx - 18 * s, cy + 5 * s, fill="#8368E3", outline="#B5A3F7", width=2)
        canvas.create_oval(cx + 18 * s, cy - 10 * s, cx + 28 * s, cy + 5 * s, fill="#8368E3", outline="#B5A3F7", width=2)


def draw_potted_plant(canvas: tk.Canvas, cx: float, cy: float, scale: float = 1.0) -> None:
    """Draws the 3D clay green leaf plant in a tan pot from Inspo 1."""
    s = scale
    canvas.create_oval(cx - 20 * s, cy - 32 * s, cx - 2 * s, cy - 4 * s, fill="#8BC34A", outline="#7CB342")
    canvas.create_oval(cx + 2 * s, cy - 32 * s, cx + 20 * s, cy - 4 * s, fill="#7CB342", outline="#689F38")
    canvas.create_oval(cx - 10 * s, cy - 40 * s, cx + 10 * s, cy - 6 * s, fill="#9CCC65", outline="#7CB342")
    draw_rounded_rect(canvas, cx - 18 * s, cy - 7 * s, cx + 18 * s, cy + 20 * s, radius=9 * s, fill="#E8C39E", outline="#D7B08A")
    draw_rounded_rect(canvas, cx - 20 * s, cy - 9 * s, cx + 20 * s, cy - 3 * s, radius=4 * s, fill="#F0D0B0", outline="")


# ==============================================================================
# MAIN MEDISTOCK APPLICATION CLASS
# ==============================================================================
class MediStockApp(tk.Tk):
    """
    Main Desktop GUI Window for MediStock.
    Uses pixel-locked fonts and responsive proportional coordinates so the GUI
    looks 100% identical across Windows 10/11 and Linux displays.
    """

    MODULES = [
        ("dashboard", "🏠", "Dashboard"),
        ("catalog", "💊", "Medicines & Supplies"),
        ("batches", "📦", "Stock Batches"),
        ("incoming_queue", "📥", "Incoming Queue"),
        ("requisition_queue", "🏥", "Requisition Queue"),
        ("issuing", "🚚", "FIFO Stock Issuing"),
        ("suppliers", "🤝", "Suppliers"),
        ("alerts", "⚠️", "Expiry & Alerts"),
        ("reports", "📊", "Reports & Exports"),
    ]

    def __init__(self):
        super().__init__()
        # Lock Tk scaling to 96-DPI baseline (1.3333 px/pt) so Windows DPI scaling
        # never distorts font-to-pixel ratios inside Canvas cards or Treeview tables.
        try:
            self.tk.call("tk", "scaling", 1.33333333)
        except Exception:
            pass

        self.title("MediStock — Hospital Medical Supplies Inventory Management System (FIFO Linked List Queue)")

        # Fit comfortably to user's screen work area
        scr_w = self.winfo_screenwidth()
        scr_h = self.winfo_screenheight()
        win_w = min(1400, max(1160, scr_w - 40))
        win_h = min(840, max(700, scr_h - 70))
        pos_x = max(0, (scr_w - win_w) // 2)
        pos_y = max(0, (scr_h - win_h - 40) // 2)
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.minsize(1140, 680)

        # Initialize SQLite database (WAL mode, lock-free)
        database.init_database()

        # Core DSA Queues (Manually Implemented Singly Linked List Queues)
        self.incoming_queue: Queue = LinkedListQueue("IncomingStockQueue")
        self.requisition_queue: Queue = LinkedListQueue("DepartmentRequisitionQueue")
        self.sync_queues_from_db()

        self.active_module: str = "dashboard"
        self.global_search_var = tk.StringVar()

        # Root container
        self.configure(bg=THEME["outer_bg"])
        self.shell_frame = tk.Frame(self, bg=THEME["outer_bg"])
        self.shell_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)

        # Left 3D Lavender Sidebar (260px wide)
        self.sidebar_canvas = tk.Canvas(
            self.shell_frame,
            width=260,
            bg=THEME["outer_bg"],
            highlightthickness=0,
            bd=0,
        )
        self.sidebar_canvas.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        self.sidebar_canvas.bind("<Configure>", lambda _e: self._render_sidebar())

        # Main Cream-White Board
        self.board_frame = tk.Frame(
            self.shell_frame,
            bg=THEME["board_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
        )
        self.board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Top Header Bar + Module Content Frame inside board_frame
        self.topbar_frame = tk.Frame(self.board_frame, bg=THEME["board_bg"], height=56)
        self.topbar_frame.pack(fill=tk.X, padx=22, pady=(12, 6))

        self.content_frame = tk.Frame(self.board_frame, bg=THEME["board_bg"])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=22, pady=(0, 14))

        self._apply_ttk_styles()
        self._build_topbar()
        self.switch_module("dashboard")

    @property
    def theme(self) -> Dict[str, str]:
        return THEME

    # ------------------------------------------------------------------
    # Synchronize Manual Linked List Queues with SQLite Persistence
    # ------------------------------------------------------------------
    def sync_queues_from_db(self) -> None:
        """Populates both manual Singly Linked List Queues from SQLite in FIFO order."""
        conn = database.get_connection()
        try:
            cursor = conn.cursor()

            self.incoming_queue.clear()
            cursor.execute("SELECT * FROM incoming_queue_items ORDER BY queue_order ASC")
            for row in cursor.fetchall():
                self.incoming_queue.enqueue({
                    "id": row["batch_id"],
                    "batch_id": row["batch_id"],
                    "batch_number": row["batch_number"],
                    "medicine_id": row["medicine_id"],
                    "medicine_name": row["medicine_name"],
                    "category": row["category"],
                    "supplier_name": row["supplier_name"],
                    "quantity": int(row["quantity"]),
                    "mfg_date": row["mfg_date"],
                    "expiry_date": row["expiry_date"],
                    "arrival_time": row["arrival_time"],
                    "condition_note": row["condition_note"],
                })

            self.requisition_queue.clear()
            cursor.execute("SELECT * FROM requisitions WHERE status = 'Pending' ORDER BY queue_order ASC")
            for row in cursor.fetchall():
                self.requisition_queue.enqueue({
                    "id": row["request_id"],
                    "request_id": row["request_id"],
                    "department": row["department"],
                    "requested_by": row["requested_by"],
                    "medicine_id": row["medicine_id"],
                    "medicine_name": row["medicine_name"],
                    "quantity_requested": int(row["quantity_requested"]),
                    "priority": row["priority"],
                    "status": row["status"],
                    "request_time": row["request_time"],
                    "notes": row["notes"] or "",
                })
        finally:
            conn.close()

    def _apply_ttk_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        t = THEME
        style.configure(
            "Medi.Treeview",
            background=t["table_even"],
            fieldbackground=t["table_even"],
            foreground=t["text_primary"],
            rowheight=34,
            font=fnt(9),
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Medi.Treeview.Heading",
            background=t["table_header_bg"],
            foreground=t["table_header_fg"],
            font=fnt(9, "bold"),
            relief="flat",
            padding=(4, 7),
        )
        style.map(
            "Medi.Treeview.Heading",
            background=[("active", t["accent_hover"])],
            foreground=[("active", "#FFFFFF")],
        )
        style.map(
            "Medi.Treeview",
            background=[("selected", t["accent"])],
            foreground=[("selected", "#FFFFFF")],
        )

    # ------------------------------------------------------------------
    # Helper: Build a Clean, Auto-Fitting Table with Zero Clipping
    # ------------------------------------------------------------------
    def _create_styled_table(
        self,
        parent: tk.Widget,
        columns_spec: List[Tuple[str, str, int, str]],
        height: int = 14,
    ) -> ttk.Treeview:
        """
        Creates a high-visibility `ttk.Treeview` wrapped with vertical & horizontal
        scrollbars, alternating row colors (`even` / `odd`), and proportional width
        stretching so columns are never cut off on any screen resolution.
        """
        container = tk.Frame(
            parent,
            bg="#FFFFFF",
            highlightbackground=THEME["card_border"],
            highlightthickness=2,
        )
        container.pack(fill=tk.BOTH, expand=True)

        col_ids = [c[0] for c in columns_spec]
        tree = ttk.Treeview(
            container,
            columns=col_ids,
            show="headings",
            style="Medi.Treeview",
            height=height,
            selectmode="browse",
        )

        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        total_base_w = max(1, sum(c[2] for c in columns_spec))
        for cid, heading_text, base_w, anchor in columns_spec:
            tree.heading(cid, text=heading_text, anchor=anchor)
            tree.column(cid, width=base_w, minwidth=max(60, int(base_w * 0.75)), anchor=anchor, stretch=True)

        tree.tag_configure("even", background=THEME["table_even"], foreground=THEME["text_primary"])
        tree.tag_configure("odd", background=THEME["table_odd"], foreground=THEME["text_primary"])
        tree.tag_configure("alert", background="#FDE8EA", foreground="#9C1C2B")
        tree.tag_configure("front", background="#E6F6EC", foreground="#145E32")

        def on_table_resize(event: tk.Event) -> None:
            avail_w = event.width - 6
            if avail_w > 450:
                for cid, _htxt, base_w, _anc in columns_spec:
                    scaled_w = max(62, int(avail_w * (base_w / total_base_w)))
                    tree.column(cid, width=scaled_w)

        tree.bind("<Configure>", on_table_resize)
        return tree

    # ------------------------------------------------------------------
    # Left Sidebar Renderer (High-Contrast, Responsive, Zero Overlap)
    # ------------------------------------------------------------------
    def _render_sidebar(self) -> None:
        c = self.sidebar_canvas
        c.delete("all")
        w = max(250, c.winfo_width())
        h = max(640, c.winfo_height())
        t = THEME

        # Outer 3D rounded lavender sidebar container
        draw_rounded_rect(c, 4, 4, w - 2, h - 2, radius=28, fill=t["sidebar_sh"], outline="")
        draw_rounded_rect(c, 2, 2, w - 5, h - 5, radius=28, fill=t["sidebar_bg"], outline=t["sidebar_hi"], width=2)

        # Top Avatar Ring + "Hi, Pharmacist! 👋"
        c.create_oval(w / 2 - 36, 16, w / 2 + 36, 88, fill="#D8C8FA", outline="#FFFFFF", width=2)
        draw_3d_avatar(c, w / 2, 54, scale=0.72, with_headphones=False)
        c.create_text(w / 2, 105, text="Hi, Pharmacist! 👋", fill="#FFFFFF", font=fnt(11, "bold"))

        # Reserve space at the bottom for the Pink 3D Queue Card
        bottom_card_h = 134
        nav_top = 124
        nav_bottom = h - bottom_card_h - 14
        avail_nav_h = max(300, nav_bottom - nav_top)
        row_h = avail_nav_h / len(self.MODULES)
        pill_h = min(37, max(27, row_h - 6))

        for idx, (mod_key, icon_ch, label) in enumerate(self.MODULES):
            y_center = nav_top + idx * row_h + row_h / 2.0
            y1 = y_center - pill_h / 2.0
            y2 = y_center + pill_h / 2.0
            is_active = self.active_module == mod_key
            tag = f"nav_{mod_key}"

            if is_active:
                draw_rounded_rect(c, 16, y1 + 2, w - 14, y2 + 2, radius=pill_h / 2, fill=t["sidebar_sh"], outline="", tags=(tag,))
                draw_rounded_rect(c, 14, y1, w - 16, y2, radius=pill_h / 2, fill="#FFFFFF", outline="#EFEAFD", width=1, tags=(tag,))
                fg = "#2C1E55"
            else:
                draw_rounded_rect(c, 14, y1 + 1, w - 16, y2 - 1, radius=pill_h / 2, fill=t["sidebar_item_bg"], outline="#9D87EE", width=1, tags=(tag,))
                fg = "#FFFFFF"

            c.create_text(36, y_center, text=icon_ch, fill=fg, font=fnt(11), tags=(tag,))
            c.create_text(58, y_center, text=label, anchor="w", fill=fg, font=fnt(10, "bold"), tags=(tag,))

            c.tag_bind(tag, "<Button-1>", lambda _e, mk=mod_key: self.switch_module(mk))
            c.tag_bind(tag, "<Enter>", lambda _e: c.config(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda _e: c.config(cursor=""))

        # Bottom Pink 3D Clay Card (Inspo 1 Crown Card)
        cy1, cy2 = h - bottom_card_h - 6, h - 14
        draw_rounded_rect(c, 18, cy1 + 3, w - 16, cy2 + 3, radius=20, fill=t["sidebar_sh"], outline="")
        draw_rounded_rect(c, 16, cy1, w - 18, cy2, radius=20, fill="#F7C6CE", outline="#FBE0E5", width=2)

        pts_crown = [
            w / 2 - 18, cy1 + 33,
            w / 2 - 22, cy1 + 13,
            w / 2 - 8, cy1 + 23,
            w / 2, cy1 + 11,
            w / 2 + 8, cy1 + 23,
            w / 2 + 22, cy1 + 13,
            w / 2 + 18, cy1 + 33,
        ]
        c.create_polygon(pts_crown, fill="#FFC947", outline="#E5AC27", width=2)
        c.create_text(w / 2, cy1 + 50, text="FIFO Queue Live", fill="#422036", font=fnt(10, "bold"))
        c.create_text(
            w / 2,
            cy1 + 69,
            text=f"{self.incoming_queue.size()} Batches • {self.requisition_queue.size()} Reqs",
            fill="#6E425C",
            font=fnt(8, "bold"),
        )
        draw_pill_button(
            c,
            30,
            cy2 - 37,
            w - 32,
            cy2 - 9,
            text="Open FIFO Queue",
            bg="#E8889E",
            fg="#FFFFFF",
            shadow="#CF6E84",
            font_spec=fnt(9, "bold"),
            on_click=lambda: self.switch_module("incoming_queue"),
        )

    # ------------------------------------------------------------------
    # Top Header Bar (3-Column Grid for Exact Centerline Alignment)
    # ------------------------------------------------------------------
    def _build_topbar(self) -> None:
        for child in self.topbar_frame.winfo_children():
            child.destroy()
        t = THEME

        self.topbar_frame.grid_columnconfigure(0, weight=1, uniform="top_edges")
        self.topbar_frame.grid_columnconfigure(1, weight=2)
        self.topbar_frame.grid_columnconfigure(2, weight=1, uniform="top_edges")

        mod_titles = dict((k, lbl) for k, _ic, lbl in self.MODULES)
        current_title = mod_titles.get(self.active_module, "Dashboard")

        # Column 0: Left Module Title
        lbl_title = tk.Label(
            self.topbar_frame,
            text=current_title,
            bg=t["board_bg"],
            fg=t["text_primary"],
            font=fnt(18, "bold"),
            anchor="w",
        )
        lbl_title.grid(row=0, column=0, sticky="w")

        # Column 1: Centered Pill Search Bar
        search_canvas = tk.Canvas(self.topbar_frame, width=380, height=40, bg=t["board_bg"], highlightthickness=0, bd=0)
        search_canvas.grid(row=0, column=1)
        draw_rounded_rect(search_canvas, 3, 4, 377, 38, radius=17, fill=t["card_shadow"], outline="")
        draw_rounded_rect(search_canvas, 1, 2, 375, 35, radius=17, fill="#FFFFFF", outline=t["card_border"])
        search_canvas.create_text(22, 18, text="🔍", fill=t["text_secondary"], font=fnt(10))
        search_entry = tk.Entry(
            search_canvas,
            textvariable=self.global_search_var,
            bd=0,
            bg="#FFFFFF",
            fg=t["text_primary"],
            insertbackground=t["text_primary"],
            font=fnt(9),
            width=34,
        )
        search_canvas.create_window(198, 18, window=search_entry)
        search_entry.bind("<Return>", lambda _e: self._on_global_search())

        # Column 2: Right Notification Bell & Profile Avatar Circle
        badge_canvas = tk.Canvas(self.topbar_frame, width=96, height=42, bg=t["board_bg"], highlightthickness=0)
        badge_canvas.grid(row=0, column=2, sticky="e")
        badge_canvas.create_oval(6, 5, 40, 39, fill="#FFFFFF", outline=t["card_border"], width=2)
        badge_canvas.create_text(23, 22, text="🔔", fill=t["accent"], font=fnt(11))
        badge_canvas.create_oval(28, 3, 43, 18, fill="#F2789F", outline="#FFFFFF")
        badge_canvas.create_text(35, 10, text=str(self.requisition_queue.size()), fill="#FFFFFF", font=fnt(7, "bold"))

        badge_canvas.create_oval(52, 5, 86, 39, fill=t["accent"], outline="#B29FF5", width=2)
        badge_canvas.create_text(69, 22, text="👤", fill="#FFFFFF", font=fnt(11))
        badge_canvas.bind("<Button-1>", lambda _e: self.switch_module("alerts"))

    def _on_global_search(self) -> None:
        q = self.global_search_var.get().strip()
        if not q:
            return
        self.switch_module("catalog")

    # ------------------------------------------------------------------
    # Module Router
    # ------------------------------------------------------------------
    def switch_module(self, module_key: str) -> None:
        self.active_module = module_key
        self._render_sidebar()
        self._build_topbar()

        for child in self.content_frame.winfo_children():
            child.destroy()

        builders: Dict[str, Callable[[], None]] = {
            "dashboard": self._build_dashboard_module,
            "catalog": self._build_catalog_module,
            "batches": self._build_batches_module,
            "incoming_queue": self._build_incoming_queue_module,
            "requisition_queue": self._build_requisition_queue_module,
            "issuing": self._build_issuing_module,
            "suppliers": self._build_suppliers_module,
            "alerts": self._build_alerts_module,
            "reports": self._build_reports_module,
        }
        builders.get(module_key, self._build_dashboard_module)()

    # ------------------------------------------------------------------
    # Gather Live Hospital Metrics for Dashboard
    # ------------------------------------------------------------------
    def _fetch_dashboard_stats(self) -> Dict[str, Any]:
        conn = database.get_connection()
        try:
            cur = conn.cursor()
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            soon_str = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")

            total_catalog = cur.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
            total_medicines = cur.execute("SELECT COUNT(*) FROM medicines WHERE category='Medicines'").fetchone()[0]
            total_supplies = total_catalog - total_medicines

            avail_stock = cur.execute(
                "SELECT COALESCE(SUM(remaining_quantity), 0) FROM batches WHERE batch_status='Available' AND expiry_date >= ?",
                (today_str,),
            ).fetchone()[0]

            pending_reqs = self.requisition_queue.size()
            incoming_q_size = self.incoming_queue.size()
            processed_reqs = cur.execute(
                "SELECT COUNT(*) FROM requisitions WHERE status IN ('Completed', 'Partially Fulfilled')"
            ).fetchone()[0]

            expiring_soon = cur.execute(
                "SELECT COUNT(*) FROM batches WHERE expiry_date <= ? OR batch_status != 'Available'",
                (soon_str,),
            ).fetchone()[0]

            low_stock_rows = cur.execute("""
                SELECT m.id, COALESCE(SUM(CASE WHEN b.batch_status='Available' AND b.expiry_date >= ? THEN b.remaining_quantity ELSE 0 END), 0) AS qty, m.min_threshold
                FROM medicines m
                LEFT JOIN batches b ON m.id = b.medicine_id
                GROUP BY m.id
                HAVING qty < m.min_threshold
            """, (today_str,)).fetchall()
            low_stock_count = len(low_stock_rows)

            cat_rows = cur.execute("""
                SELECT m.category, COALESCE(SUM(CASE WHEN b.batch_status='Available' THEN b.remaining_quantity ELSE 0 END), 0) AS qty
                FROM medicines m
                LEFT JOIN batches b ON m.id = b.medicine_id
                GROUP BY m.category
                ORDER BY qty DESC
            """).fetchall()

            recent_tx = cur.execute(
                "SELECT tx_id, timestamp, tx_type, reference_id, medicine_name, department_or_supplier, quantity, details FROM transactions ORDER BY timestamp DESC LIMIT 5"
            ).fetchall()

            return {
                "total_catalog": total_catalog,
                "total_medicines": total_medicines,
                "total_supplies": total_supplies,
                "avail_stock": avail_stock,
                "pending_reqs": pending_reqs,
                "incoming_q_size": incoming_q_size,
                "processed_reqs": processed_reqs,
                "expiring_soon": expiring_soon,
                "low_stock_count": low_stock_count,
                "categories": [(r["category"], int(r["qty"])) for r in cat_rows],
                "recent_tx": [dict(r) for r in recent_tx],
            }
        finally:
            conn.close()

    # ==========================================================================
    # MODULE 1: DASHBOARD (Pure Inspo 1 Layout with Responsive Card Sizing)
    # ==========================================================================
    def _build_dashboard_module(self) -> None:
        stats = self._fetch_dashboard_stats()
        canvas = tk.Canvas(self.content_frame, bg=THEME["board_bg"], highlightthickness=0, bd=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        def on_resize(_event: Any = None) -> None:
            canvas.delete("all")
            w = max(840, canvas.winfo_width())
            h = max(580, canvas.winfo_height())
            self._draw_inspo1_dashboard(canvas, w, h, stats)

        canvas.bind("<Configure>", on_resize)

    def _draw_inspo1_dashboard(self, c: tk.Canvas, w: int, h: int, stats: Dict[str, Any]) -> None:
        v_gap = 12
        footer_h = 36
        usable_h = h - footer_h - v_gap * 4 - 6

        hero_h = max(124, int(usable_h * 0.23))
        kpi_h = max(116, int(usable_h * 0.21))
        mid_h = max(160, int(usable_h * 0.30))
        bot_h = max(140, usable_h - hero_h - kpi_h - mid_h)

        hy1 = 2
        hy2 = hy1 + hero_h

        ky1 = hy2 + v_gap
        ky2 = ky1 + kpi_h

        my1 = ky2 + v_gap
        my2 = my1 + mid_h

        by1 = my2 + v_gap
        by2 = by1 + bot_h

        fy1 = by2 + v_gap
        fy2 = h - 4

        # ------------------------------------------------------------------
        # ROW 1: Lavender 3D Hero Banner ("Good Morning, Pharmacist! ☀️")
        # ------------------------------------------------------------------
        draw_rounded_rect(c, 6, hy1 + 4, w - 4, hy2 + 4, radius=24, fill="#C3B2EE", outline="")
        draw_rounded_rect(c, 2, hy1, w - 8, hy2, radius=24, fill="#D6C8F7", outline="#E7DDFC", width=2)

        hero_cy = (hy1 + hy2) / 2.0
        draw_3d_avatar(c, 106, hero_cy + 4, scale=1.06, with_headphones=True)
        c.create_text(170, hy1 + 30, text="✚", fill="#E57FA2", font=fnt(13, "bold"))
        c.create_text(182, hy1 + 62, text="💊", fill="#E57FA2", font=fnt(11))

        text_x = 220
        c.create_text(
            text_x,
            hy1 + int(hero_h * 0.23),
            text="Good Morning, Pharmacist! ☀️",
            anchor="w",
            fill="#2C1E55",
            font=fnt(16, "bold"),
        )
        c.create_text(
            text_x,
            hy1 + int(hero_h * 0.47),
            text=f"Hospital FIFO Queues Active  •  {stats['total_medicines']} Medicines & {stats['total_supplies']} Supplies  •  {stats['low_stock_count']} Low-Stock Alerts",
            anchor="w",
            fill="#56477E",
            font=fnt(10),
        )

        btn_y1 = hy2 - 43
        btn_y2 = hy2 - 11
        draw_pill_button(
            c,
            text_x,
            btn_y1,
            text_x + 195,
            btn_y2,
            text="▶  Process FIFO Queue",
            bg="#8369E3",
            fg="#FFFFFF",
            shadow="#694FD0",
            font_spec=fnt(9, "bold"),
            on_click=lambda: self.switch_module("requisition_queue"),
        )
        draw_pill_button(
            c,
            text_x + 210,
            btn_y1,
            text_x + 395,
            btn_y2,
            text="🚚  FIFO Stock Issue",
            bg="#FAF7F5",
            fg="#2C1E55",
            shadow="#B7A5E8",
            font_spec=fnt(9, "bold"),
            on_click=lambda: self.switch_module("issuing"),
        )

        draw_potted_plant(c, w - 82, hy2 - 28, scale=1.10)

        # ------------------------------------------------------------------
        # ROW 2: 4 Pastel 3D Clay KPI Cards (Lavender, Peach, Butter, Ice-Blue)
        # ------------------------------------------------------------------
        gap = 14
        card_w = (w - 10 - gap * 3) / 4.0
        kpi_defs = [
            ("#EFEAFD", "#DFD5FA", "#8F75EA", "💊", "Total Catalog Items", f"{stats['total_catalog']} Items", f"+{stats['total_medicines']} Meds / {stats['total_supplies']} Supplies"),
            ("#FCE8E6", "#F7D3CF", "#F27D72", "📦", "Available Stock", f"{stats['avail_stock']:,} Units", f"+{stats['processed_reqs']} Requests Fulfilled"),
            ("#FFF4DE", "#F7E4BE", "#F5B841", "🏥", "Pending Dept Reqs", f"{stats['pending_reqs']} in Queue", f"+{stats['incoming_q_size']} Incoming Batches"),
            ("#E6EEF8", "#CFE0F2", "#69A6E8", "⚠️", "Low Stock / Expiring", f"{stats['low_stock_count']} / {stats['expiring_soon']}", "FIFO & Quarantine Active"),
        ]
        for idx, (bg_col, sh_col, ic_bg, ic_txt, title, big_val, sub_txt) in enumerate(kpi_defs):
            x1 = 2 + idx * (card_w + gap)
            x2 = x1 + card_w
            draw_clay_card(c, x1, ky1, x2, ky2, radius=20, fill=bg_col, shadow=sh_col, highlight="#FFFFFF", border=sh_col)
            draw_rounded_rect(c, x1 + 16, ky1 + 11, x1 + 48, ky1 + 41, radius=10, fill=ic_bg, outline="")
            c.create_text(x1 + 32, ky1 + 26, text=ic_txt, fill="#FFFFFF", font=fnt(11))
            c.create_text(x1 + 16, ky1 + int(kpi_h * 0.47), text=title, anchor="w", fill="#5E527A", font=fnt(9, "bold"))
            c.create_text(x1 + 16, ky1 + int(kpi_h * 0.69), text=big_val, anchor="w", fill="#2C1E55", font=fnt(15, "bold"))
            c.create_text(x1 + 16, ky2 - 14, text=sub_txt, anchor="w", fill="#269956" if idx < 3 else "#5C5278", font=fnt(8, "bold"))

        # ------------------------------------------------------------------
        # ROW 3: Left "Inventory & FIFO Queue Overview" + Right "Top Categories"
        # ------------------------------------------------------------------
        left_w = int(w * 0.52)
        draw_clay_card(c, 2, my1, left_w - 6, my2, radius=20, fill="#FFFFFF", shadow="#E5DDF5", border="#E6DFF5")
        c.create_text(22, my1 + 22, text="Inventory & FIFO Queue Overview", anchor="w", fill="#2C1E55", font=fnt(11, "bold"))
        draw_rounded_rect(c, left_w - 104, my1 + 10, left_w - 20, my1 + 32, radius=11, fill="#F5F2FA", outline="#E6E0F2")
        c.create_text(left_w - 62, my1 + 21, text="This Week ▾", fill="#5E527A", font=fnt(8, "bold"))

        chart_top, chart_bot = my1 + 46, my2 - 26
        for step_idx, lbl in enumerate(["600", "400", "200", "0"]):
            yy = chart_top + step_idx * ((chart_bot - chart_top) / 3.0)
            c.create_text(28, yy, text=lbl, fill="#8D82A8", font=fnt(8))
            c.create_line(46, yy, left_w - 24, yy, fill="#F3EFFA", dash=(3, 3))

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        bar_vals = [0.62, 0.80, 0.65, 0.92, 0.60, 0.76, 0.68]
        bar_colors = [
            ("#A38DF2", "#BBA9F8"),
            ("#F5A6B8", "#F9C2CE"),
            ("#FA9F5C", "#FCBC8B"),
            ("#FCD062", "#FDE092"),
            ("#A5D67E", "#C1E5A3"),
            ("#7BB8EE", "#A4CFF5"),
            ("#A68FF0", "#C2B1F7"),
        ]
        avail_bw = (left_w - 84) / 7.0
        for i, (day, ratio, (col_main, col_hi)) in enumerate(zip(days, bar_vals, bar_colors)):
            bx_center = 64 + i * avail_bw + avail_bw / 2.0
            bw_half = min(14, avail_bw * 0.28)
            bh = max(12, (chart_bot - chart_top) * ratio)
            by_top = chart_bot - bh
            draw_rounded_rect(c, bx_center - bw_half + 2, by_top + 2, bx_center + bw_half + 2, chart_bot + 2, radius=bw_half, fill="#EAE4F4", outline="")
            draw_rounded_rect(c, bx_center - bw_half, by_top, bx_center + bw_half, chart_bot, radius=bw_half, fill=col_main, outline="")
            draw_rounded_rect(c, bx_center - bw_half + 3, by_top + 3, bx_center - 1, chart_bot - 5, radius=3, fill=col_hi, outline="")
            c.create_text(bx_center, chart_bot + 13, text=day, fill="#6E638A", font=fnt(8, "bold"))

        # Right Card: "Top Categories" 3D Donut + Full Untruncated Category Names
        rx1 = left_w + 8
        draw_clay_card(c, rx1, my1, w - 8, my2, radius=20, fill="#FFFFFF", shadow="#E5DDF5", border="#E6DFF5")
        c.create_text(rx1 + 22, my1 + 22, text="Top Categories", anchor="w", fill="#2C1E55", font=fnt(11, "bold"))

        dr = min(48, int((my2 - my1 - 52) / 2.0))
        dcx = rx1 + 26 + dr
        dcy = (my1 + 36 + my2) / 2.0
        c.create_oval(dcx - dr + 2, dcy - dr + 3, dcx + dr + 2, dcy + dr + 3, fill="#EAE3F5", outline="")
        cats = stats["categories"][:5] or [("Medicines", 45), ("Surgical supplies", 25), ("IV supplies", 15), ("Protective equipment", 10), ("Emergency supplies", 5)]
        total_cat_qty = max(1, sum(q for _, q in cats))
        donut_cols = ["#9C86F2", "#F594A9", "#FCD168", "#A3D67C", "#78B7EE"]
        start_deg = 90.0
        for idx, (_cat_name, qty) in enumerate(cats):
            extent = max(8.0, (qty / total_cat_qty) * 360.0)
            col = donut_cols[idx % len(donut_cols)]
            c.create_arc(dcx - dr, dcy - dr, dcx + dr, dcy + dr, start=start_deg, extent=-extent, fill=col, outline="#FFFFFF", width=2)
            start_deg -= extent
        inner_r = int(dr * 0.54)
        c.create_oval(dcx - inner_r, dcy - inner_r, dcx + inner_r, dcy + inner_r, fill="#FFFFFF", outline="#EFEAF8")

        leg_x = dcx + dr + 24
        leg_top = my1 + 46
        leg_step = max(21, int((my2 - leg_top - 12) / max(1, len(cats[:5]))))
        for idx, (cat_name, qty) in enumerate(cats[:5]):
            ly = leg_top + idx * leg_step
            pct = int(round((qty / total_cat_qty) * 100))
            col = donut_cols[idx % len(donut_cols)]
            c.create_oval(leg_x, ly - 5, leg_x + 10, ly + 5, fill=col, outline="")
            c.create_text(leg_x + 16, ly, text=cat_name, anchor="w", fill="#3D315E", font=fnt(9))
            c.create_text(w - 24, ly, text=f"{pct}%", anchor="e", fill="#2C1E55", font=fnt(9, "bold"))

        # ------------------------------------------------------------------
        # ROW 4: Left "Recently Processed (FIFO)" + Right "Active FIFO Queue"
        # ------------------------------------------------------------------
        draw_clay_card(c, 2, by1, left_w - 6, by2, radius=20, fill="#FFFFFF", shadow="#E5DDF5", border="#E6DFF5")
        c.create_text(22, by1 + 20, text="Recently Processed (FIFO)", anchor="w", fill="#2C1E55", font=fnt(11, "bold"))
        draw_pill_button(
            c,
            left_w - 84,
            by1 + 9,
            left_w - 20,
            by1 + 31,
            text="See All",
            bg="#F5F2FA",
            fg="#5E527A",
            font_spec=fnt(8, "bold"),
            on_click=lambda: self.switch_module("reports"),
        )

        tx_list = stats["recent_tx"][:3]
        thumb_cols = ["#D8C8FA", "#FAD2C8", "#FDE6B8"]
        avail_list_h = max(86, by2 - by1 - 40)
        row_span = avail_list_h / 3.0
        for idx, tx in enumerate(tx_list):
            ry = by1 + 36 + idx * row_span
            box_s = min(26, int(row_span - 6))
            draw_rounded_rect(c, 22, ry, 22 + box_s, ry + box_s, radius=7, fill=thumb_cols[idx % 3], outline="")
            c.create_text(22 + box_s / 2, ry + box_s / 2, text="💊" if idx == 0 else ("🚚" if idx == 1 else "📥"), font=fnt(9))
            c.create_text(22 + box_s + 10, ry + box_s * 0.28, text=tx["medicine_name"], anchor="w", fill="#2C1E55", font=fnt(9, "bold"))
            c.create_text(
                22 + box_s + 10,
                ry + box_s * 0.76,
                text=f"{tx['reference_id']} • {tx['department_or_supplier']} ({tx['quantity']} units)",
                anchor="w",
                fill="#7D709E",
                font=fnt(8),
            )
            c.create_oval(left_w - 46, ry + 2, left_w - 22, ry + 26, fill="#F5F2FA", outline="#E4DDF2")
            c.create_text(left_w - 34, ry + 14, text="▶", fill="#8369E3", font=fnt(8, "bold"))

        # Right Bottom Card: "Active FIFO Queue Status"
        draw_clay_card(c, rx1, by1, w - 8, by2, radius=20, fill="#FFFFFF", shadow="#E5DDF5", border="#E6DFF5")
        c.create_text(rx1 + 22, by1 + 20, text="Active FIFO Queue Status", anchor="w", fill="#2C1E55", font=fnt(11, "bold"))
        draw_pill_button(
            c,
            w - 82,
            by1 + 9,
            w - 20,
            by1 + 31,
            text="See All",
            bg="#F5F2FA",
            fg="#5E527A",
            font_spec=fnt(8, "bold"),
            on_click=lambda: self.switch_module("incoming_queue"),
        )

        in_y1, in_y2 = by1 + 36, by2 - 12
        draw_rounded_rect(c, rx1 + 16, in_y1, w - 22, in_y2, radius=16, fill="#8A72E6", outline="#A893F5")
        front_req = self.requisition_queue.peek()
        front_batch = self.incoming_queue.peek()
        front_lbl = f"FRONT REQ: {front_req['request_id']} — {front_req['department']} ({front_req['quantity_requested']}u)" if front_req else "All Dept Requisitions Completed"
        batch_lbl = f"FRONT BATCH: {front_batch['batch_id']} — {front_batch['medicine_name']}" if front_batch else "Incoming Queue Empty"

        inner_h = in_y2 - in_y1
        c.create_text(rx1 + 32, in_y1 + int(inner_h * 0.24), text="SINGLY LINKED LIST (FRONT → REAR)", anchor="w", fill="#E5DCFC", font=fnt(8, "bold"))
        c.create_text(rx1 + 32, in_y1 + int(inner_h * 0.52), text=front_lbl, anchor="w", fill="#FFFFFF", font=fnt(10, "bold"))
        c.create_text(rx1 + 32, in_y1 + int(inner_h * 0.78), text=batch_lbl, anchor="w", fill="#EFEAFD", font=fnt(9))

        play_r = 15
        px_c, py_c = w - 46, (in_y1 + in_y2) / 2.0
        c.create_oval(px_c - play_r, py_c - play_r, px_c + play_r, py_c + play_r, fill="#FFFFFF", outline="")
        c.create_text(px_c + 1, py_c, text="▶", fill="#8369E3", font=fnt(9, "bold"))

        # ------------------------------------------------------------------
        # Bottom Full-Width Purple Banner
        # ------------------------------------------------------------------
        draw_rounded_rect(c, 2, fy1, w - 8, fy2, radius=16, fill="#9C87EE", outline="#B8A6F8")
        fy_mid = (fy1 + fy2) / 2.0
        c.create_text(30, fy_mid, text="⭐", font=fnt(13))
        c.create_text(
            56,
            fy_mid,
            text="Generate All 10 Hospital Inventory, Batch & FIFO Queue Reports (CSV / PDF Export)  ✨",
            anchor="w",
            fill="#FFFFFF",
            font=fnt(9, "bold"),
        )
        draw_pill_button(
            c,
            w - 138,
            fy1 + 5,
            w - 20,
            fy2 - 5,
            text="Explore Now",
            bg="#7E66DF",
            fg="#FFFFFF",
            font_spec=fnt(8, "bold"),
            on_click=lambda: self.switch_module("reports"),
        )

    # ==========================================================================
    # SHARED UI HELPERS FOR MODULES 2–9
    # ==========================================================================
    def _create_action_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        bg: Optional[str] = None,
        fg: str = "#FFFFFF",
    ) -> tk.Button:
        btn_bg = bg or THEME["accent"]
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=btn_bg,
            fg=fg,
            activebackground=THEME["accent_hover"],
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            font=fnt(9, "bold"),
        )

    def _draw_linked_list_queue_canvas(
        self,
        canvas: tk.Canvas,
        queue_obj: Queue,
        is_incoming: bool = True,
    ) -> None:
        """
        Renders the manual Singly Linked List Queue (`FRONT -> Node -> REAR -> NULL`)
        with dynamic node card sizing so every node and text line fits 100% inside the card.
        """
        canvas.delete("all")
        w = max(840, canvas.winfo_width())
        h = max(195, canvas.winfo_height())
        t = THEME

        draw_clay_card(canvas, 2, 2, w - 4, h - 4, radius=18, fill="#FFFFFF", shadow=t["card_shadow"], border=t["card_border"])

        nodes = queue_obj.display_nodes()
        front_addr = queue_obj.front.memory_address if queue_obj.front else "NULL"
        rear_addr = queue_obj.rear.memory_address if queue_obj.rear else "NULL"

        canvas.create_text(
            18,
            18,
            text=f"Singly Linked List Queue  •  size() = {queue_obj.size()}  •  is_empty() = {queue_obj.is_empty()}  •  front = {front_addr}  •  rear = {rear_addr}",
            anchor="w",
            fill=t["text_primary"],
            font=fnt(9, "bold"),
        )
        last_op_short = queue_obj.last_operation[:56]
        draw_rounded_rect(canvas, w - 385, 7, w - 16, 29, radius=10, fill="#F4F0FC", outline="#E2D9F7")
        canvas.create_text(
            w - 200,
            18,
            text=f"Last Op: {last_op_short}",
            fill=t["accent"],
            font=mfnt(8, "bold"),
        )

        if not nodes:
            canvas.create_text(
                w / 2,
                h / 2 + 12,
                text="Queue is Empty  [ front = NULL , rear = NULL ]  — Click 'Enqueue' to insert a Node at REAR in O(1)",
                fill=t["text_secondary"],
                font=fnt(11, "bold"),
            )
            return

        visible_nodes = nodes[:6]
        n_count = len(visible_nodes)
        start_x = 18
        null_box_w = 52
        arrow_gap = 24
        avail_for_cards = w - start_x - 20 - null_box_w - (n_count * arrow_gap)
        card_w = max(125, min(185, int(avail_for_cards / max(1, n_count))))
        max_chars = max(14, int((card_w - 18) / 6.3))

        ny1, ny2 = 54, h - 16

        for idx, ninfo in enumerate(visible_nodes):
            x1 = start_x + idx * (card_w + arrow_gap)
            x2 = x1 + card_w
            data = ninfo["data"]
            is_front = ninfo["is_front"]
            is_rear = ninfo["is_rear"]

            node_bg = "#EFEAFD" if is_front else ("#FCE8E6" if is_rear else "#F7F5FC")
            node_border = t["accent"] if is_front else ("#E87A6D" if is_rear else "#D8D0EC")

            if is_front and is_rear:
                draw_rounded_rect(canvas, x1 + 10, ny1 - 18, x2 - 10, ny1 - 2, radius=7, fill=t["accent"], outline="")
                canvas.create_text((x1 + x2) / 2, ny1 - 10, text="FRONT & REAR", fill="#FFFFFF", font=fnt(7, "bold"))
            elif is_front:
                draw_rounded_rect(canvas, x1 + 14, ny1 - 18, x2 - 14, ny1 - 2, radius=7, fill="#269956", outline="")
                canvas.create_text((x1 + x2) / 2, ny1 - 10, text="FRONT (Dequeue)", fill="#FFFFFF", font=fnt(7, "bold"))
            elif is_rear:
                draw_rounded_rect(canvas, x1 + 16, ny1 - 18, x2 - 16, ny1 - 2, radius=7, fill="#D96552", outline="")
                canvas.create_text((x1 + x2) / 2, ny1 - 10, text="REAR (Enqueue)", fill="#FFFFFF", font=fnt(7, "bold"))

            draw_rounded_rect(canvas, x1, ny1, x2, ny2, radius=13, fill=node_bg, outline=node_border, width=2)
            canvas.create_text(x1 + 9, ny1 + 14, text=f"#{ninfo['position']} {ninfo['id']}", anchor="w", fill=t["text_primary"], font=fnt(9, "bold"))
            canvas.create_text(x2 - 8, ny1 + 14, text=ninfo["memory_address"], anchor="e", fill=t["text_secondary"], font=mfnt(7))

            if is_incoming:
                line1 = str(data.get("medicine_name", ""))[:max_chars]
                line2 = f"Qty:{data.get('quantity', 0)} | Exp:{data.get('expiry_date', '')}"[: max_chars + 2]
            else:
                line1 = f"{data.get('department', '')} ({data.get('priority', '')})"[:max_chars]
                line2 = f"{str(data.get('medicine_name', ''))[: max_chars - 5]} x{data.get('quantity_requested', 0)}"

            canvas.create_text(x1 + 9, ny1 + 36, text=line1, anchor="w", fill=t["text_primary"], font=fnt(8, "bold"))
            canvas.create_text(x1 + 9, ny1 + 54, text=line2, anchor="w", fill=t["text_secondary"], font=fnt(8))

            draw_rounded_rect(canvas, x1 + 7, ny2 - 24, x2 - 7, ny2 - 6, radius=6, fill="#FFFFFF", outline="#E2DCF0")
            canvas.create_text(
                (x1 + x2) / 2,
                ny2 - 15,
                text=f"next → {ninfo['next_address']}",
                fill=t["accent"],
                font=mfnt(7, "bold"),
            )

            ax1 = x2 + 3
            ax2 = x2 + arrow_gap - 3
            ay = (ny1 + ny2) / 2
            canvas.create_line(ax1, ay, ax2, ay, fill=t["accent"], width=2, arrow=tk.LAST)

        null_x = start_x + n_count * (card_w + arrow_gap)
        ay = (ny1 + ny2) / 2
        draw_rounded_rect(canvas, null_x, ay - 15, null_x + 48, ay + 15, radius=8, fill="#F3EFFA", outline="#D8D0EC", width=1)
        canvas.create_text(null_x + 24, ay, text="NULL", fill=t["text_secondary"], font=mfnt(8, "bold"))

    # ==========================================================================
    # MODULE 2: MEDICINES & SUPPLIES MANAGEMENT (Catalog CRUD)
    # ==========================================================================
    def _build_catalog_module(self) -> None:
        t = THEME
        bar = tk.Frame(self.content_frame, bg=t["board_bg"])
        bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(bar, text="Category:", bg=t["board_bg"], fg=t["text_primary"], font=fnt(9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        cat_var = tk.StringVar(value="All Categories")
        cat_cb = ttk.Combobox(bar, textvariable=cat_var, values=["All Categories"] + database.CATEGORIES, state="readonly", width=20)
        cat_cb.pack(side=tk.LEFT, padx=(0, 12))

        search_var = tk.StringVar(value=self.global_search_var.get())
        tk.Label(bar, text="Search ID/Name:", bg=t["board_bg"], fg=t["text_primary"], font=fnt(9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        tk.Entry(bar, textvariable=search_var, width=22, font=fnt(9)).pack(side=tk.LEFT, padx=(0, 10))

        columns_spec = [
            ("id", "Item ID", 80, "center"),
            ("name", "Medicine / Medical Supply Name", 240, "w"),
            ("code", "Code", 80, "center"),
            ("category", "Category", 145, "w"),
            ("dosage_form", "Form", 85, "center"),
            ("unit", "Unit", 75, "center"),
            ("avail_stock", "Avail Stock", 110, "center"),
            ("min_threshold", "Min Level", 90, "center"),
            ("unit_cost", "Unit Cost", 85, "center"),
            ("storage_req", "Storage Condition", 160, "w"),
        ]
        tree = self._create_styled_table(self.content_frame, columns_spec)

        def refresh_table(*_args: Any) -> None:
            for item in tree.get_children():
                tree.delete(item)
            conn = database.get_connection()
            try:
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                rows = conn.execute("""
                    SELECT m.*,
                           COALESCE(SUM(CASE WHEN b.batch_status='Available' AND b.expiry_date >= ? THEN b.remaining_quantity ELSE 0 END), 0) AS avail_qty
                    FROM medicines m
                    LEFT JOIN batches b ON m.id = b.medicine_id
                    GROUP BY m.id
                    ORDER BY m.id
                """, (today_str,)).fetchall()
                sel_cat = cat_var.get()
                q = search_var.get().strip().lower()
                row_idx = 0
                for r in rows:
                    if sel_cat != "All Categories" and r["category"] != sel_cat:
                        continue
                    if q and q not in r["id"].lower() and q not in r["name"].lower() and q not in r["code"].lower():
                        continue
                    tag = "alert" if r["avail_qty"] < r["min_threshold"] else ("even" if row_idx % 2 == 0 else "odd")
                    tree.insert(
                        "",
                        tk.END,
                        iid=r["id"],
                        tags=(tag,),
                        values=(
                            r["id"],
                            r["name"],
                            r["code"],
                            r["category"],
                            r["dosage_form"],
                            r["unit"],
                            r["avail_qty"],
                            r["min_threshold"],
                            f"${r['unit_cost']:.2f}",
                            r["storage_req"],
                        ),
                    )
                    row_idx += 1
            finally:
                conn.close()

        cat_cb.bind("<<ComboboxSelected>>", refresh_table)
        search_var.trace_add("write", refresh_table)

        def open_editor(existing_id: Optional[str] = None) -> None:
            win = tk.Toplevel(self)
            win.title("Update Catalog Item" if existing_id else "Add New Medicine / Medical Supply")
            win.geometry("540x560")
            win.configure(bg="#FFFFFF")
            win.transient(self)
            win.grab_set()

            existing_row = None
            if existing_id:
                conn = database.get_connection()
                try:
                    existing_row = conn.execute("SELECT * FROM medicines WHERE id = ?", (existing_id,)).fetchone()
                finally:
                    conn.close()

            fields = [
                ("id", "Item ID (e.g. MED-115):", existing_row["id"] if existing_row else f"MED-{113 + len(tree.get_children())}"),
                ("name", "Item Name:", existing_row["name"] if existing_row else ""),
                ("code", "Catalog Code:", existing_row["code"] if existing_row else "SUP-001"),
                ("category", "Category:", existing_row["category"] if existing_row else database.CATEGORIES[0]),
                ("dosage_form", "Dosage / Form:", existing_row["dosage_form"] if existing_row else "Unit"),
                ("unit", "Measurement Unit:", existing_row["unit"] if existing_row else "Units"),
                ("min_threshold", "Minimum Stock Level:", str(existing_row["min_threshold"]) if existing_row else "100"),
                ("unit_cost", "Unit Cost ($):", str(existing_row["unit_cost"]) if existing_row else "2.50"),
                ("storage_req", "Storage Requirement:", existing_row["storage_req"] if existing_row else "Room Temp (15-25°C)"),
                ("description", "Description:", existing_row["description"] if existing_row else ""),
            ]
            vars_map: Dict[str, tk.StringVar] = {}
            form = tk.Frame(win, bg="#FFFFFF", padx=24, pady=18)
            form.pack(fill=tk.BOTH, expand=True)

            for r_idx, (fkey, flbl, fdefault) in enumerate(fields):
                tk.Label(form, text=flbl, bg="#FFFFFF", fg=t["text_primary"], font=fnt(9, "bold")).grid(row=r_idx, column=0, sticky="w", pady=6)
                sv = tk.StringVar(value=fdefault)
                vars_map[fkey] = sv
                if fkey == "category":
                    w_inp = ttk.Combobox(form, textvariable=sv, values=database.CATEGORIES, state="readonly", width=28)
                else:
                    w_inp = tk.Entry(form, textvariable=sv, width=31, font=fnt(9), state="readonly" if (fkey == "id" and existing_id) else "normal")
                w_inp.grid(row=r_idx, column=1, sticky="w", pady=6, padx=(12, 0))

            def save_item() -> None:
                cid = vars_map["id"].get().strip()
                cname = vars_map["name"].get().strip()
                if not cid or not cname:
                    messagebox.showwarning("Validation", "Item ID and Name are required.", parent=win)
                    return
                try:
                    min_t = int(vars_map["min_threshold"].get().strip())
                    ucost = float(vars_map["unit_cost"].get().strip())
                except ValueError:
                    messagebox.showwarning("Validation", "Minimum stock level must be an integer and Unit Cost a number.", parent=win)
                    return

                conn = database.get_connection()
                try:
                    if existing_id:
                        conn.execute("""
                            UPDATE medicines
                            SET name=?, code=?, category=?, dosage_form=?, unit=?,
                                min_threshold=?, unit_cost=?, storage_req=?, description=?
                            WHERE id=?
                        """, (
                            cname,
                            vars_map["code"].get().strip(),
                            vars_map["category"].get().strip(),
                            vars_map["dosage_form"].get().strip(),
                            vars_map["unit"].get().strip(),
                            min_t,
                            ucost,
                            vars_map["storage_req"].get().strip(),
                            vars_map["description"].get().strip(),
                            cid,
                        ))
                    else:
                        conn.execute(
                            "INSERT INTO medicines VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (
                                cid,
                                cname,
                                vars_map["code"].get().strip(),
                                vars_map["category"].get().strip(),
                                vars_map["dosage_form"].get().strip(),
                                vars_map["unit"].get().strip(),
                                min_t,
                                ucost,
                                vars_map["storage_req"].get().strip(),
                                vars_map["description"].get().strip(),
                            ),
                        )
                    conn.commit()
                except Exception as exc:
                    messagebox.showerror("Database Error", str(exc), parent=win)
                    return
                finally:
                    conn.close()

                database.log_transaction(
                    "CATALOG_UPDATE" if existing_id else "CATALOG_ADD",
                    cid,
                    cname,
                    vars_map["category"].get(),
                    min_t,
                    f"{'Updated' if existing_id else 'Added'} catalog item {cid}",
                )
                win.destroy()
                refresh_table()

            self._create_action_button(win, "💾 Save Catalog Item", save_item).pack(pady=(0, 18))

        def edit_selected() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select Item", "Click on a row in the table first, then click 'Update Selected'.")
                return
            open_editor(sel[0])

        def delete_selected() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select Item", "Click on a row in the table first, then click 'Delete Selected'.")
                return
            cid = sel[0]
            conn = database.get_connection()
            try:
                active_batches = conn.execute(
                    "SELECT COUNT(*) FROM batches WHERE medicine_id=? AND remaining_quantity > 0",
                    (cid,),
                ).fetchone()[0]
                if active_batches > 0:
                    messagebox.showwarning(
                        "Cannot Delete Active Item",
                        f"Item {cid} has {active_batches} active stock batch(es). Deplete or remove batches first.",
                    )
                    return
                if not messagebox.askyesno("Confirm Delete", f"Delete catalog item {cid}?"):
                    return
                conn.execute("DELETE FROM medicines WHERE id=?", (cid,))
                conn.commit()
            finally:
                conn.close()
            database.log_transaction("CATALOG_DELETE", cid, cid, "Catalog", 0, f"Deleted catalog record {cid}")
            refresh_table()

        self._create_action_button(bar, "➕ Add Item", lambda: open_editor(None)).pack(side=tk.RIGHT, padx=4)
        self._create_action_button(bar, "✏️ Update Selected", edit_selected, bg="#5C7CFA").pack(side=tk.RIGHT, padx=4)
        self._create_action_button(bar, "🗑️ Delete Selected", delete_selected, bg=t["danger"]).pack(side=tk.RIGHT, padx=4)

        refresh_table()

    # ==========================================================================
    # MODULE 3: STOCK BATCH MANAGEMENT
    # ==========================================================================
    def _build_batches_module(self) -> None:
        t = THEME
        bar = tk.Frame(self.content_frame, bg=t["board_bg"])
        bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            bar,
            text="Product Catalog records are kept separate from Stock Batches (1 Medicine → Multiple Batches, sorted by Expiry Date).",
            bg=t["board_bg"],
            fg=t["text_secondary"],
            font=fnt(9, "bold"),
        ).pack(side=tk.LEFT)

        columns_spec = [
            ("batch_id", "Batch ID", 82, "center"),
            ("batch_number", "Lot #", 105, "center"),
            ("medicine_id", "Med ID", 78, "center"),
            ("medicine_name", "Medicine / Supply Name", 220, "w"),
            ("supplier_name", "Supplier", 170, "w"),
            ("initial_quantity", "Init Qty", 88, "center"),
            ("remaining_quantity", "Rem Qty", 88, "center"),
            ("mfg_date", "Mfg Date", 98, "center"),
            ("expiry_date", "Expiry Date", 102, "center"),
            ("arrival_date", "Arrived On", 98, "center"),
            ("batch_status", "Status", 90, "center"),
        ]
        tree = self._create_styled_table(self.content_frame, columns_spec)

        def refresh_batches() -> None:
            for item in tree.get_children():
                tree.delete(item)
            conn = database.get_connection()
            try:
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                rows = conn.execute("SELECT * FROM batches ORDER BY expiry_date ASC").fetchall()
                for idx, r in enumerate(rows):
                    is_exp = r["expiry_date"] < today_str or r["batch_status"] != "Available"
                    tag = "alert" if is_exp else ("even" if idx % 2 == 0 else "odd")
                    tree.insert(
                        "",
                        tk.END,
                        iid=r["batch_id"],
                        tags=(tag,),
                        values=(
                            r["batch_id"],
                            r["batch_number"],
                            r["medicine_id"],
                            r["medicine_name"],
                            r["supplier_name"],
                            r["initial_quantity"],
                            r["remaining_quantity"],
                            r["mfg_date"],
                            r["expiry_date"],
                            r["arrival_date"],
                            r["batch_status"],
                        ),
                    )
            finally:
                conn.close()

        def add_batch_dialog() -> None:
            win = tk.Toplevel(self)
            win.title("Register Direct Stock Batch")
            win.geometry("520x480")
            win.configure(bg="#FFFFFF")
            win.transient(self)
            win.grab_set()

            conn = database.get_connection()
            try:
                meds = [(r["id"], r["name"]) for r in conn.execute("SELECT id, name FROM medicines ORDER BY id").fetchall()]
                sups = [r["name"] for r in conn.execute("SELECT name FROM suppliers ORDER BY name").fetchall()]
            finally:
                conn.close()

            med_choices = [f"{mid} | {mname}" for mid, mname in meds]
            today = datetime.date.today()

            form = tk.Frame(win, bg="#FFFFFF", padx=24, pady=18)
            form.pack(fill=tk.BOTH, expand=True)

            b_id_var = tk.StringVar(value=f"B-{1015 + len(tree.get_children())}")
            lot_var = tk.StringVar(value=f"LOT-{today.strftime('%y%m')}-{len(tree.get_children()) + 1:02d}")
            med_var = tk.StringVar(value=med_choices[0] if med_choices else "")
            sup_var = tk.StringVar(value=sups[0] if sups else "")
            qty_var = tk.StringVar(value="200")
            mfg_var = tk.StringVar(value=(today - datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
            exp_var = tk.StringVar(value=(today + datetime.timedelta(days=365)).strftime("%Y-%m-%d"))

            rows_spec = [
                ("Batch ID:", tk.Entry(form, textvariable=b_id_var, width=30)),
                ("Lot Number:", tk.Entry(form, textvariable=lot_var, width=30)),
                ("Medicine / Item:", ttk.Combobox(form, textvariable=med_var, values=med_choices, state="readonly", width=28)),
                ("Supplier:", ttk.Combobox(form, textvariable=sup_var, values=sups, state="readonly", width=28)),
                ("Quantity Received:", tk.Entry(form, textvariable=qty_var, width=30)),
                ("Mfg Date (YYYY-MM-DD):", tk.Entry(form, textvariable=mfg_var, width=30)),
                ("Expiry Date (YYYY-MM-DD):", tk.Entry(form, textvariable=exp_var, width=30)),
            ]
            for idx, (lbl, widget) in enumerate(rows_spec):
                tk.Label(form, text=lbl, bg="#FFFFFF", fg=t["text_primary"], font=fnt(9, "bold")).grid(row=idx, column=0, sticky="w", pady=6)
                widget.grid(row=idx, column=1, sticky="w", pady=6, padx=(12, 0))

            def save_batch() -> None:
                try:
                    qty = int(qty_var.get().strip())
                except ValueError:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be an integer.", parent=win)
                    return
                med_id, med_name = med_var.get().split(" | ", 1)
                bid = b_id_var.get().strip()
                conn = database.get_connection()
                try:
                    conn.execute(
                        "INSERT INTO batches VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            bid,
                            lot_var.get().strip(),
                            med_id,
                            med_name,
                            sup_var.get().strip(),
                            qty,
                            qty,
                            mfg_var.get().strip(),
                            exp_var.get().strip(),
                            today.strftime("%Y-%m-%d"),
                            "Available",
                            "Main-Store",
                        ),
                    )
                    conn.commit()
                except Exception as exc:
                    messagebox.showerror("Error", str(exc), parent=win)
                    return
                finally:
                    conn.close()

                database.log_transaction("BATCH_ADD", bid, med_name, sup_var.get(), qty, f"Added batch {bid}")
                win.destroy()
                refresh_batches()

            self._create_action_button(win, "💾 Save Batch Record", save_batch).pack(pady=14)

        self._create_action_button(bar, "➕ Register Batch", add_batch_dialog).pack(side=tk.RIGHT, padx=4)
        refresh_batches()

    # ==========================================================================
    # MODULE 4: INCOMING STOCK QUEUE (Core DSA Module #1 — Linked List Queue)
    # ==========================================================================
    def _build_incoming_queue_module(self) -> None:
        t = THEME
        viz_canvas = tk.Canvas(self.content_frame, height=200, bg=t["board_bg"], highlightthickness=0)
        viz_canvas.pack(fill=tk.X, pady=(0, 8))

        ctrl = tk.Frame(self.content_frame, bg=t["board_bg"])
        ctrl.pack(fill=tk.X, pady=(0, 8))

        columns_spec = [
            ("pos", "Queue Pos", 102, "center"),
            ("batch_id", "Batch ID", 80, "center"),
            ("batch_number", "Lot #", 112, "center"),
            ("medicine_name", "Medicine / Supply Name", 230, "w"),
            ("category", "Category", 135, "w"),
            ("supplier_name", "Supplier", 175, "w"),
            ("quantity", "Qty", 65, "center"),
            ("expiry_date", "Expiry Date", 102, "center"),
            ("arrival_time", "Arrived", 85, "center"),
            ("condition_note", "Condition / Safety", 155, "w"),
        ]
        tree = self._create_styled_table(self.content_frame, columns_spec, height=10)

        def refresh_ui(nodes_override: Optional[List[Dict[str, Any]]] = None) -> None:
            self._draw_linked_list_queue_canvas(viz_canvas, self.incoming_queue, is_incoming=True)
            for item in tree.get_children():
                tree.delete(item)
            nodes = nodes_override if nodes_override is not None else self.incoming_queue.display_nodes()
            for idx, n in enumerate(nodes):
                d = n["data"]
                pos_lbl = f"#{n['position']} (FRONT)" if n["is_front"] else (f"#{n['position']} (REAR)" if n["is_rear"] else f"#{n['position']}")
                tag = "front" if n["is_front"] else ("alert" if "Expired" in d["condition_note"] or "Damaged" in d["condition_note"] else ("even" if idx % 2 == 0 else "odd"))
                tree.insert(
                    "",
                    tk.END,
                    iid=d["batch_id"],
                    tags=(tag,),
                    values=(
                        pos_lbl,
                        d["batch_id"],
                        d["batch_number"],
                        d["medicine_name"],
                        d["category"],
                        d["supplier_name"],
                        d["quantity"],
                        d["expiry_date"],
                        d["arrival_time"],
                        d["condition_note"],
                    ),
                )
            self._render_sidebar()

        viz_canvas.bind("<Configure>", lambda _e: self._draw_linked_list_queue_canvas(viz_canvas, self.incoming_queue, is_incoming=True))

        def do_enqueue() -> None:
            win = tk.Toplevel(self)
            win.title("Enqueue(batch) — Receive Incoming Supplier Delivery at REAR")
            win.geometry("520x470")
            win.configure(bg="#FFFFFF")
            win.transient(self)
            win.grab_set()

            conn = database.get_connection()
            try:
                meds = [(r["id"], r["name"], r["category"]) for r in conn.execute("SELECT id, name, category FROM medicines ORDER BY id").fetchall()]
                sups = [r["name"] for r in conn.execute("SELECT name FROM suppliers ORDER BY name").fetchall()]
            finally:
                conn.close()

            med_opts = [f"{m[0]} | {m[1]} ({m[2]})" for m in meds]
            today = datetime.date.today()

            b_id_v = tk.StringVar(value=f"B{self.incoming_queue.size() + 5:03d}")
            lot_v = tk.StringVar(value=f"LOT-NEW-{self.incoming_queue.size() + 5:02d}")
            med_v = tk.StringVar(value=med_opts[0] if med_opts else "")
            sup_v = tk.StringVar(value=sups[0] if sups else "")
            qty_v = tk.StringVar(value="180")
            exp_v = tk.StringVar(value=(today + datetime.timedelta(days=300)).strftime("%Y-%m-%d"))
            cond_v = tk.StringVar(value="Good / Sealed")

            f = tk.Frame(win, bg="#FFFFFF", padx=24, pady=18)
            f.pack(fill=tk.BOTH, expand=True)
            for idx, (lbl, w_inp) in enumerate([
                ("Batch ID:", tk.Entry(f, textvariable=b_id_v, width=30)),
                ("Lot Number:", tk.Entry(f, textvariable=lot_v, width=30)),
                ("Medicine / Item:", ttk.Combobox(f, textvariable=med_v, values=med_opts, state="readonly", width=28)),
                ("Supplier:", ttk.Combobox(f, textvariable=sup_v, values=sups, state="readonly", width=28)),
                ("Quantity Delivered:", tk.Entry(f, textvariable=qty_v, width=30)),
                ("Expiry Date (YYYY-MM-DD):", tk.Entry(f, textvariable=exp_v, width=30)),
                ("Condition:", ttk.Combobox(f, textvariable=cond_v, values=["Good / Sealed", "Cold-Chain Verified", "Damaged Outer Carton", "Expired Seal Alert", "Recalled Lot"], width=28)),
            ]):
                tk.Label(f, text=lbl, bg="#FFFFFF", fg=t["text_primary"], font=fnt(9, "bold")).grid(row=idx, column=0, sticky="w", pady=6)
                w_inp.grid(row=idx, column=1, sticky="w", pady=6, padx=(12, 0))

            def confirm_enqueue() -> None:
                try:
                    qty = int(qty_v.get().strip())
                except ValueError:
                    messagebox.showwarning("Invalid Qty", "Quantity must be an integer.", parent=win)
                    return
                raw_med = med_v.get()
                med_id = raw_med.split(" | ")[0]
                med_name = raw_med.split(" | ")[1].rsplit(" (", 1)[0]
                cat = raw_med.rsplit("(", 1)[1].rstrip(")")
                bid = b_id_v.get().strip()
                mfg_str = (today - datetime.timedelta(days=15)).strftime("%Y-%m-%d")
                arr_str = datetime.datetime.now().strftime("%I:%M %p")

                item_payload = {
                    "id": bid,
                    "batch_id": bid,
                    "batch_number": lot_v.get().strip(),
                    "medicine_id": med_id,
                    "medicine_name": med_name,
                    "category": cat,
                    "supplier_name": sup_v.get().strip(),
                    "quantity": qty,
                    "mfg_date": mfg_str,
                    "expiry_date": exp_v.get().strip(),
                    "arrival_time": arr_str,
                    "condition_note": cond_v.get().strip(),
                }
                self.incoming_queue.enqueue(item_payload)

                conn = database.get_connection()
                try:
                    conn.execute("""
                        INSERT INTO incoming_queue_items
                        (batch_id, batch_number, medicine_id, medicine_name, category, supplier_name,
                         quantity, mfg_date, expiry_date, arrival_time, condition_note)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        bid, item_payload["batch_number"], med_id, med_name, cat,
                        item_payload["supplier_name"], qty, mfg_str, item_payload["expiry_date"],
                        arr_str, item_payload["condition_note"],
                    ))
                    conn.commit()
                finally:
                    conn.close()

                database.log_transaction("QUEUE_ENQUEUE", bid, med_name, item_payload["supplier_name"], qty, f"Enqueued incoming batch {bid} at REAR")
                win.destroy()
                refresh_ui()

            self._create_action_button(win, "📥 Enqueue at REAR [O(1)]", confirm_enqueue).pack(pady=12)

        def do_dequeue_and_inspect() -> None:
            front_item = self.incoming_queue.peek()
            if not front_item:
                messagebox.showinfo("Queue Empty", "Incoming Stock Queue is empty (front = NULL).")
                return

            popped = self.incoming_queue.dequeue()
            bid = popped["batch_id"]
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            is_unsafe = (
                popped["expiry_date"] < today_str
                or "Damaged" in popped["condition_note"]
                or "Expired" in popped["condition_note"]
                or "Recalled" in popped["condition_note"]
            )

            conn = database.get_connection()
            try:
                conn.execute("DELETE FROM incoming_queue_items WHERE batch_id=?", (bid,))
                if is_unsafe:
                    qid = f"QRN-{int(datetime.datetime.now().timestamp()) % 10000:04d}"
                    conn.execute(
                        "INSERT INTO quarantine VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            qid, bid, popped["medicine_id"], popped["medicine_name"],
                            popped["supplier_name"], popped["quantity"],
                            f"Rejected at Queue Inspection: {popped['condition_note']} (Exp: {popped['expiry_date']})",
                            popped["expiry_date"], today_str, "Quarantined - Blocked from Stock",
                        ),
                    )
                    msg = f"Batch {bid} DEQUEUED from FRONT and QUARANTINED due to safety/expiry check ({popped['condition_note']})."
                    tx_type = "QUEUE_QUARANTINE"
                else:
                    conn.execute(
                        "INSERT OR REPLACE INTO batches VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            bid, popped["batch_number"], popped["medicine_id"], popped["medicine_name"],
                            popped["supplier_name"], popped["quantity"], popped["quantity"],
                            popped["mfg_date"], popped["expiry_date"], today_str, "Available", "Main-Store",
                        ),
                    )
                    msg = f"Batch {bid} ({popped['medicine_name']}) DEQUEUED from FRONT, inspected & approved into Available Inventory!"
                    tx_type = "QUEUE_DEQUEUE_APPROVE"
                conn.commit()
            finally:
                conn.close()

            database.log_transaction(tx_type, bid, popped["medicine_name"], popped["supplier_name"], popped["quantity"], msg)
            refresh_ui()
            messagebox.showinfo("Dequeue() Complete [O(1)]", msg)

        def do_peek() -> None:
            top = self.incoming_queue.peek()
            refresh_ui()
            if not top:
                messagebox.showinfo("Peek() [O(1)]", "Queue is empty (front = NULL).")
            else:
                messagebox.showinfo(
                    "Peek() Front Node [O(1)]",
                    f"FRONT Batch ID: {top['batch_id']}\nMedicine: {top['medicine_name']}\nSupplier: {top['supplier_name']}\nQuantity: {top['quantity']}\nExpiry: {top['expiry_date']}\nCondition: {top['condition_note']}",
                )

        def do_search() -> None:
            q = simpledialog.askstring("SearchQueue() [O(n)]", "Enter Batch ID, Medicine Name, or Supplier to search without altering queue order:", parent=self)
            if q is None:
                return
            self.incoming_queue.search(q)
            matches = self.incoming_queue.search_all(q)
            refresh_ui(matches)

        def do_update() -> None:
            sel = tree.selection()
            target_id = sel[0] if sel else (self.incoming_queue.peek()["batch_id"] if self.incoming_queue.peek() else None)
            if not target_id:
                messagebox.showinfo("Update Node", "Select a batch in the queue to update.")
                return
            new_qty_str = simpledialog.askstring("update(id, data) [O(n)]", f"Enter updated quantity for {target_id} (preserves queue order):", parent=self)
            if not new_qty_str:
                return
            try:
                new_qty = int(new_qty_str)
            except ValueError:
                messagebox.showwarning("Invalid", "Quantity must be an integer.")
                return
            self.incoming_queue.update(target_id, {"quantity": new_qty})
            conn = database.get_connection()
            try:
                conn.execute("UPDATE incoming_queue_items SET quantity=? WHERE batch_id=?", (new_qty, target_id))
                conn.commit()
            finally:
                conn.close()
            refresh_ui()

        def do_delete() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("delete(id) [O(n)]", "Click a batch row in the table first, then click 'Delete(id)'.")
                return
            target_id = sel[0]
            removed = self.incoming_queue.delete(target_id)
            if removed:
                conn = database.get_connection()
                try:
                    conn.execute("DELETE FROM incoming_queue_items WHERE batch_id=?", (target_id,))
                    conn.commit()
                finally:
                    conn.close()
                database.log_transaction("QUEUE_DELETE", target_id, removed["medicine_name"], removed["supplier_name"], removed["quantity"], f"Deleted node {target_id} from Incoming Queue")
                refresh_ui()

        self._create_action_button(ctrl, "📥 Enqueue(batch)", do_enqueue).pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "✅ Dequeue() & Inspect", do_dequeue_and_inspect, bg=t["success"]).pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "👁️ Peek()", do_peek, bg="#5C7CFA").pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "🔍 Search(id)", do_search, bg="#7950F2").pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "✏️ Update(id)", do_update, bg=t["warning"]).pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "🗑️ Delete(id)", do_delete, bg=t["danger"]).pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "🔄 Display All", lambda: refresh_ui(None), bg="#495057").pack(side=tk.LEFT, padx=3)

        refresh_ui()

    # ==========================================================================
    # MODULE 5: DEPARTMENT REQUISITION MANAGEMENT (Core DSA Module #2 — Queue)
    # ==========================================================================
    def _build_requisition_queue_module(self) -> None:
        t = THEME
        viz_canvas = tk.Canvas(self.content_frame, height=200, bg=t["board_bg"], highlightthickness=0)
        viz_canvas.pack(fill=tk.X, pady=(0, 8))

        ctrl = tk.Frame(self.content_frame, bg=t["board_bg"])
        ctrl.pack(fill=tk.X, pady=(0, 8))

        columns_spec = [
            ("pos", "Queue Pos", 102, "center"),
            ("request_id", "Req ID", 78, "center"),
            ("department", "Department", 145, "w"),
            ("requested_by", "Requested By", 145, "w"),
            ("medicine_name", "Requested Item", 235, "w"),
            ("quantity_requested", "Qty", 65, "center"),
            ("priority", "Priority", 80, "center"),
            ("status", "Status", 85, "center"),
            ("request_time", "Submitted", 90, "center"),
            ("notes", "Clinical Notes", 165, "w"),
        ]
        tree = self._create_styled_table(self.content_frame, columns_spec, height=10)

        def refresh_req_ui(nodes_override: Optional[List[Dict[str, Any]]] = None) -> None:
            self._draw_linked_list_queue_canvas(viz_canvas, self.requisition_queue, is_incoming=False)
            for item in tree.get_children():
                tree.delete(item)
            nodes = nodes_override if nodes_override is not None else self.requisition_queue.display_nodes()
            for idx, n in enumerate(nodes):
                d = n["data"]
                pos_lbl = f"#{n['position']} (FRONT)" if n["is_front"] else (f"#{n['position']} (REAR)" if n["is_rear"] else f"#{n['position']}")
                tag = "front" if n["is_front"] else ("even" if idx % 2 == 0 else "odd")
                tree.insert(
                    "",
                    tk.END,
                    iid=d["request_id"],
                    tags=(tag,),
                    values=(
                        pos_lbl,
                        d["request_id"],
                        d["department"],
                        d["requested_by"],
                        d["medicine_name"],
                        d["quantity_requested"],
                        d["priority"],
                        d["status"],
                        d["request_time"],
                        d.get("notes", ""),
                    ),
                )
            self._render_sidebar()

        viz_canvas.bind("<Configure>", lambda _e: self._draw_linked_list_queue_canvas(viz_canvas, self.requisition_queue, is_incoming=False))

        def do_enqueue_req() -> None:
            win = tk.Toplevel(self)
            win.title("Enqueue(request) — New Hospital Department Requisition")
            win.geometry("520x470")
            win.configure(bg="#FFFFFF")
            win.transient(self)
            win.grab_set()

            conn = database.get_connection()
            try:
                meds = [(r["id"], r["name"]) for r in conn.execute("SELECT id, name FROM medicines ORDER BY id").fetchall()]
                total_reqs = conn.execute("SELECT COUNT(*) FROM requisitions").fetchone()[0]
            finally:
                conn.close()

            med_opts = [f"{m[0]} | {m[1]}" for m in meds]
            rid_v = tk.StringVar(value=f"R{total_reqs + 1:03d}")
            dept_v = tk.StringVar(value=database.DEPARTMENTS[0])
            doc_v = tk.StringVar(value="Dr. Hannah Abbott")
            med_v = tk.StringVar(value=med_opts[0] if med_opts else "")
            qty_v = tk.StringVar(value="50")
            prio_v = tk.StringVar(value="Urgent")
            note_v = tk.StringVar(value="Ward replenishment")

            f = tk.Frame(win, bg="#FFFFFF", padx=24, pady=18)
            f.pack(fill=tk.BOTH, expand=True)
            for idx, (lbl, w_inp) in enumerate([
                ("Request ID:", tk.Entry(f, textvariable=rid_v, width=30)),
                ("Department:", ttk.Combobox(f, textvariable=dept_v, values=database.DEPARTMENTS, state="readonly", width=28)),
                ("Requested By:", tk.Entry(f, textvariable=doc_v, width=30)),
                ("Requested Item:", ttk.Combobox(f, textvariable=med_v, values=med_opts, state="readonly", width=28)),
                ("Quantity Requested:", tk.Entry(f, textvariable=qty_v, width=30)),
                ("Priority:", ttk.Combobox(f, textvariable=prio_v, values=["Urgent", "High", "Normal"], state="readonly", width=28)),
                ("Clinical Notes:", tk.Entry(f, textvariable=note_v, width=30)),
            ]):
                tk.Label(f, text=lbl, bg="#FFFFFF", fg=t["text_primary"], font=fnt(9, "bold")).grid(row=idx, column=0, sticky="w", pady=6)
                w_inp.grid(row=idx, column=1, sticky="w", pady=6, padx=(12, 0))

            def confirm_req() -> None:
                try:
                    qty = int(qty_v.get().strip())
                except ValueError:
                    messagebox.showwarning("Invalid", "Quantity must be an integer.", parent=win)
                    return
                rid = rid_v.get().strip()
                med_id, med_name = med_v.get().split(" | ", 1)
                now_t = datetime.datetime.now().strftime("%I:%M %p")
                payload = {
                    "id": rid,
                    "request_id": rid,
                    "department": dept_v.get(),
                    "requested_by": doc_v.get().strip(),
                    "medicine_id": med_id,
                    "medicine_name": med_name,
                    "quantity_requested": qty,
                    "priority": prio_v.get(),
                    "status": "Pending",
                    "request_time": now_t,
                    "notes": note_v.get().strip(),
                }
                self.requisition_queue.enqueue(payload)
                conn = database.get_connection()
                try:
                    conn.execute("""
                        INSERT INTO requisitions
                        (request_id, department, requested_by, medicine_id, medicine_name,
                         quantity_requested, quantity_fulfilled, priority, status, request_time, processed_time, notes)
                        VALUES (?,?,?,?,?,?,0,?,?,?,NULL,?)
                    """, (rid, payload["department"], payload["requested_by"], med_id, med_name, qty, payload["priority"], "Pending", now_t, payload["notes"]))
                    conn.commit()
                finally:
                    conn.close()
                database.log_transaction("REQ_ENQUEUE", rid, med_name, payload["department"], qty, f"Enqueued department request {rid} at REAR")
                win.destroy()
                refresh_req_ui()

            self._create_action_button(win, "🏥 Enqueue Request at REAR [O(1)]", confirm_req).pack(pady=12)

        def do_peek_req() -> None:
            top = self.requisition_queue.peek()
            refresh_req_ui()
            if not top:
                messagebox.showinfo("Peek() [O(1)]", "Requisition Queue is empty.")
            else:
                messagebox.showinfo(
                    "Peek() Front Request [O(1)]",
                    f"FRONT Request: {top['request_id']}\nDepartment: {top['department']}\nItem: {top['medicine_name']}\nQuantity: {top['quantity_requested']}\nPriority: {top['priority']}",
                )

        def do_search_req() -> None:
            q = simpledialog.askstring("Search(id) [O(n)]", "Enter Request ID, Department, or Medicine to search:", parent=self)
            if q is None:
                return
            self.requisition_queue.search(q)
            refresh_req_ui(self.requisition_queue.search_all(q))

        def do_update_req() -> None:
            sel = tree.selection()
            target_id = sel[0] if sel else (self.requisition_queue.peek()["request_id"] if self.requisition_queue.peek() else None)
            if not target_id:
                messagebox.showinfo("Update Request", "Select a pending request in the queue.")
                return
            new_q_str = simpledialog.askstring("update(id, data) [O(n)]", f"Enter new quantity for request {target_id}:", parent=self)
            if not new_q_str:
                return
            try:
                nq = int(new_q_str)
            except ValueError:
                return
            self.requisition_queue.update(target_id, {"quantity_requested": nq})
            conn = database.get_connection()
            try:
                conn.execute("UPDATE requisitions SET quantity_requested=? WHERE request_id=?", (nq, target_id))
                conn.commit()
            finally:
                conn.close()
            refresh_req_ui()

        def do_cancel_req() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Cancel Request", "Click a request row in the table first, then click 'Cancel / Delete(id)'.")
                return
            rid = sel[0]
            removed = self.requisition_queue.delete(rid)
            if removed:
                conn = database.get_connection()
                try:
                    conn.execute("DELETE FROM requisitions WHERE request_id=?", (rid,))
                    conn.commit()
                finally:
                    conn.close()
                database.log_transaction("REQ_CANCEL", rid, removed["medicine_name"], removed["department"], removed["quantity_requested"], f"Cancelled request {rid} via delete(id)")
                refresh_req_ui()

        self._create_action_button(ctrl, "➕ Enqueue Request", do_enqueue_req).pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "🚚 Dequeue & Issue Stock", lambda: self.switch_module("issuing"), bg=t["success"]).pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "👁️ Peek()", do_peek_req, bg="#5C7CFA").pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "🔍 Search(id)", do_search_req, bg="#7950F2").pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "✏️ Update(id)", do_update_req, bg=t["warning"]).pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "🗑️ Cancel / Delete(id)", do_cancel_req, bg=t["danger"]).pack(side=tk.LEFT, padx=3)
        self._create_action_button(ctrl, "🔄 Display All", lambda: refresh_req_ui(None), bg="#495057").pack(side=tk.LEFT, padx=3)

        refresh_req_ui()

    # ==========================================================================
    # MODULE 6: FIFO STOCK ISSUING & DISTRIBUTION
    # ==========================================================================
    def _build_issuing_module(self) -> None:
        t = THEME
        top_card = tk.Frame(
            self.content_frame,
            bg="#FFFFFF",
            highlightbackground=t["card_border"],
            highlightthickness=2,
            padx=22,
            pady=16,
        )
        top_card.pack(fill=tk.X, pady=(0, 12))

        front_req = self.requisition_queue.peek()
        if not front_req:
            tk.Label(
                top_card,
                text="✅ All Pending Department Requisitions Have Been Processed (FIFO Queue is Empty)!",
                bg="#FFFFFF",
                fg=t["success"],
                font=fnt(12, "bold"),
            ).pack(anchor="w")
        else:
            tk.Label(
                top_card,
                text=f"NEXT FRONT REQUEST IN FIFO QUEUE:  {front_req['request_id']}  •  Department: {front_req['department']}  •  Officer: {front_req['requested_by']}",
                bg="#FFFFFF",
                fg=t["accent"],
                font=fnt(11, "bold"),
            ).pack(anchor="w")
            tk.Label(
                top_card,
                text=f"Requested Item: {front_req['medicine_name']} ({front_req['medicine_id']})   |   Quantity Needed: {front_req['quantity_requested']} units   |   Priority: {front_req['priority']}",
                bg="#FFFFFF",
                fg=t["text_primary"],
                font=fnt(10),
            ).pack(anchor="w", pady=(4, 10))

            def execute_fifo_issue() -> None:
                req = self.requisition_queue.peek()
                if not req:
                    return
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                needed = int(req["quantity_requested"])
                med_id = req["medicine_id"]

                conn = database.get_connection()
                allocated_total = 0
                used_batches: List[str] = []
                try:
                    cur = conn.cursor()
                    eligible = cur.execute("""
                        SELECT batch_id, remaining_quantity, expiry_date
                        FROM batches
                        WHERE medicine_id=? AND batch_status='Available' AND remaining_quantity > 0 AND expiry_date >= ?
                        ORDER BY expiry_date ASC
                    """, (med_id, today_str)).fetchall()

                    if not eligible:
                        messagebox.showwarning(
                            "Insufficient Eligible Stock",
                            f"No non-expired available batches found for {req['medicine_name']}.",
                        )
                        return

                    for b in eligible:
                        if allocated_total >= needed:
                            break
                        take = min(needed - allocated_total, int(b["remaining_quantity"]))
                        new_rem = int(b["remaining_quantity"]) - take
                        new_status = "Depleted" if new_rem == 0 else "Available"
                        cur.execute(
                            "UPDATE batches SET remaining_quantity=?, batch_status=? WHERE batch_id=?",
                            (new_rem, new_status, b["batch_id"]),
                        )
                        allocated_total += take
                        used_batches.append(f"{b['batch_id']} ({take}u, exp {b['expiry_date']})")

                    self.requisition_queue.dequeue()

                    final_status = "Completed" if allocated_total >= needed else "Partially Fulfilled"
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    cur.execute("""
                        UPDATE requisitions
                        SET quantity_fulfilled=?, status=?, processed_time=?
                        WHERE request_id=?
                    """, (allocated_total, final_status, now_str, req["request_id"]))
                    conn.commit()
                finally:
                    conn.close()

                summary_str = f"{final_status}: Issued {allocated_total}/{needed} units from {', '.join(used_batches)}"
                database.log_transaction("REQ_ISSUE", req["request_id"], req["medicine_name"], req["department"], allocated_total, summary_str)
                messagebox.showinfo("Stock Issued & Request Dequeued", summary_str)
                self.switch_module("issuing")

            self._create_action_button(
                top_card,
                "🚚 Dequeue Front Request & Issue Eligible Stock",
                execute_fifo_issue,
                bg=t["success"],
            ).pack(anchor="w")

        columns_spec = [
            ("request_id", "Req ID", 90, "center"),
            ("department", "Hospital Department", 160, "w"),
            ("medicine_name", "Medicine / Supply Issued", 260, "w"),
            ("quantity_requested", "Requested Qty", 115, "center"),
            ("quantity_fulfilled", "Issued Qty", 115, "center"),
            ("status", "Fulfillment Status", 145, "center"),
            ("processed_time", "Processed Timestamp", 170, "center"),
        ]
        tree = self._create_styled_table(self.content_frame, columns_spec, height=11)

        conn = database.get_connection()
        try:
            for idx, r in enumerate(conn.execute("SELECT * FROM requisitions ORDER BY queue_order DESC").fetchall()):
                tag = "front" if r["status"] == "Completed" else ("even" if idx % 2 == 0 else "odd")
                tree.insert(
                    "",
                    tk.END,
                    tags=(tag,),
                    values=(
                        r["request_id"],
                        r["department"],
                        r["medicine_name"],
                        r["quantity_requested"],
                        r["quantity_fulfilled"],
                        r["status"],
                        r["processed_time"] or "Waiting in FIFO Queue",
                    ),
                )
        finally:
            conn.close()

    # ==========================================================================
    # MODULE 7: SUPPLIER MANAGEMENT
    # ==========================================================================
    def _build_suppliers_module(self) -> None:
        t = THEME
        bar = tk.Frame(self.content_frame, bg=t["board_bg"])
        bar.pack(fill=tk.X, pady=(0, 10))
        tk.Label(bar, text="Hospital Approved Suppliers & Delivery Performance", bg=t["board_bg"], fg=t["text_primary"], font=fnt(11, "bold")).pack(side=tk.LEFT)

        columns_spec = [
            ("supplier_id", "Supplier ID", 100, "center"),
            ("name", "Supplier Name", 220, "w"),
            ("contact_number", "Contact Number", 135, "center"),
            ("email", "Email Address", 195, "w"),
            ("address", "Location / Address", 225, "w"),
            ("lead_time_days", "Lead Time", 95, "center"),
            ("batches_count", "Batches", 95, "center"),
            ("status", "Status", 90, "center"),
        ]
        tree = self._create_styled_table(self.content_frame, columns_spec)

        def refresh_suppliers() -> None:
            for item in tree.get_children():
                tree.delete(item)
            conn = database.get_connection()
            try:
                rows = conn.execute("""
                    SELECT s.*, COUNT(b.batch_id) AS b_cnt
                    FROM suppliers s
                    LEFT JOIN batches b ON s.name = b.supplier_name
                    GROUP BY s.supplier_id
                    ORDER BY s.supplier_id
                """).fetchall()
                for idx, r in enumerate(rows):
                    tree.insert(
                        "",
                        tk.END,
                        iid=r["supplier_id"],
                        tags=("even" if idx % 2 == 0 else "odd",),
                        values=(
                            r["supplier_id"],
                            r["name"],
                            r["contact_number"],
                            r["email"],
                            r["address"],
                            f"{r['lead_time_days']} days",
                            r["b_cnt"],
                            r["status"],
                        ),
                    )
            finally:
                conn.close()

        def open_supplier_dialog(edit_id: Optional[str] = None) -> None:
            win = tk.Toplevel(self)
            win.title("Update Supplier" if edit_id else "Add New Supplier")
            win.geometry("500x410")
            win.configure(bg="#FFFFFF")
            win.transient(self)
            win.grab_set()

            existing = None
            if edit_id:
                conn = database.get_connection()
                try:
                    existing = conn.execute("SELECT * FROM suppliers WHERE supplier_id=?", (edit_id,)).fetchone()
                finally:
                    conn.close()

            sid_v = tk.StringVar(value=existing["supplier_id"] if existing else f"SUP-0{len(tree.get_children()) + 1}")
            name_v = tk.StringVar(value=existing["name"] if existing else "")
            phone_v = tk.StringVar(value=existing["contact_number"] if existing else "+1-800-555-0199")
            mail_v = tk.StringVar(value=existing["email"] if existing else "contact@supplier.med")
            addr_v = tk.StringVar(value=existing["address"] if existing else "100 Healthcare Way")
            lead_v = tk.StringVar(value=str(existing["lead_time_days"]) if existing else "2")

            f = tk.Frame(win, bg="#FFFFFF", padx=24, pady=18)
            f.pack(fill=tk.BOTH, expand=True)
            for idx, (lbl, sv) in enumerate([
                ("Supplier ID:", sid_v),
                ("Supplier Name:", name_v),
                ("Contact Number:", phone_v),
                ("Email:", mail_v),
                ("Address:", addr_v),
                ("Lead Time (Days):", lead_v),
            ]):
                tk.Label(f, text=lbl, bg="#FFFFFF", fg=t["text_primary"], font=fnt(9, "bold")).grid(row=idx, column=0, sticky="w", pady=6)
                tk.Entry(f, textvariable=sv, width=30, state="readonly" if (idx == 0 and edit_id) else "normal").grid(row=idx, column=1, sticky="w", pady=6, padx=(12, 0))

            def save_sup() -> None:
                sid = sid_v.get().strip()
                sname = name_v.get().strip()
                if not sid or not sname:
                    messagebox.showwarning("Required", "Supplier ID and Name are required.", parent=win)
                    return
                conn = database.get_connection()
                try:
                    if edit_id:
                        conn.execute(
                            "UPDATE suppliers SET name=?, contact_number=?, email=?, address=?, lead_time_days=? WHERE supplier_id=?",
                            (sname, phone_v.get().strip(), mail_v.get().strip(), addr_v.get().strip(), int(lead_v.get() or 2), sid),
                        )
                    else:
                        conn.execute(
                            "INSERT INTO suppliers VALUES (?,?,?,?,?,?,?)",
                            (sid, sname, phone_v.get().strip(), mail_v.get().strip(), addr_v.get().strip(), int(lead_v.get() or 2), "Active"),
                        )
                    conn.commit()
                finally:
                    conn.close()
                database.log_transaction("SUPPLIER_SAVE", sid, sname, sname, 0, f"Saved supplier {sid}")
                win.destroy()
                refresh_suppliers()

            self._create_action_button(win, "💾 Save Supplier", save_sup).pack(pady=12)

        def edit_sup() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select Supplier", "Click a supplier row in the table first, then click 'Update Selected'.")
                return
            open_supplier_dialog(sel[0])

        def delete_sup() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Select Supplier", "Click a supplier row in the table first, then click 'Delete Selected'.")
                return
            sid = sel[0]
            if not messagebox.askyesno("Confirm Delete", f"Delete supplier {sid}?"):
                return
            conn = database.get_connection()
            try:
                conn.execute("DELETE FROM suppliers WHERE supplier_id=?", (sid,))
                conn.commit()
            finally:
                conn.close()
            refresh_suppliers()

        self._create_action_button(bar, "➕ Add Supplier", lambda: open_supplier_dialog(None)).pack(side=tk.RIGHT, padx=4)
        self._create_action_button(bar, "✏️ Update Selected", edit_sup, bg="#5C7CFA").pack(side=tk.RIGHT, padx=4)
        self._create_action_button(bar, "🗑️ Delete Selected", delete_sup, bg=t["danger"]).pack(side=tk.RIGHT, padx=4)
        refresh_suppliers()

    # ==========================================================================
    # MODULE 8: EXPIRY & LOW STOCK ALERTS (+ QUARANTINE TRACKING)
    # ==========================================================================
    def _build_alerts_module(self) -> None:
        t = THEME
        top_pane = tk.Frame(self.content_frame, bg=t["board_bg"])
        top_pane.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        bot_pane = tk.Frame(self.content_frame, bg=t["board_bg"])
        bot_pane.pack(fill=tk.BOTH, expand=True)

        hdr1 = tk.Frame(top_pane, bg=t["board_bg"])
        hdr1.pack(fill=tk.X, pady=(0, 6))
        tk.Label(hdr1, text="⚠️ Expired, Near-Expiry (<30 Days) & Quarantined Batches", bg=t["board_bg"], fg=t["danger"], font=fnt(11, "bold")).pack(side=tk.LEFT)

        exp_spec = [
            ("bid", "Batch ID", 85, "center"),
            ("lot", "Lot #", 110, "center"),
            ("med", "Medicine / Supply Name", 240, "w"),
            ("sup", "Supplier", 190, "w"),
            ("qty", "Rem Qty", 100, "center"),
            ("exp", "Expiry Date", 105, "center"),
            ("status", "Current Status", 115, "center"),
            ("alert", "Safety Classification", 165, "center"),
        ]
        exp_tree = self._create_styled_table(top_pane, exp_spec, height=6)

        hdr2 = tk.Frame(bot_pane, bg=t["board_bg"])
        hdr2.pack(fill=tk.X, pady=(4, 6))
        tk.Label(hdr2, text="📉 Low-Stock Catalog Items & Automated Restocking Suggestions", bg=t["board_bg"], fg=t["text_primary"], font=fnt(11, "bold")).pack(side=tk.LEFT)

        low_spec = [
            ("id", "Item ID", 95, "center"),
            ("name", "Medicine / Supply Name", 250, "w"),
            ("cat", "Category", 155, "w"),
            ("avail", "Available Stock", 120, "center"),
            ("min", "Min Threshold", 120, "center"),
            ("deficit", "Shortfall", 105, "center"),
            ("reorder", "Suggested Restock Order", 170, "center"),
        ]
        low_tree = self._create_styled_table(bot_pane, low_spec, height=6)

        def refresh_alerts() -> None:
            for item in exp_tree.get_children():
                exp_tree.delete(item)
            for item in low_tree.get_children():
                low_tree.delete(item)
            for idx, row in enumerate(reports_exporter.fetch_report_data("expiry_report")["rows"]):
                tag = "alert" if row[7] == "EXPIRED" else ("even" if idx % 2 == 0 else "odd")
                exp_tree.insert("", tk.END, iid=row[0], tags=(tag,), values=row)
            for idx, row in enumerate(reports_exporter.fetch_report_data("low_stock_report")["rows"]):
                low_tree.insert("", tk.END, tags=("even" if idx % 2 == 0 else "odd",), values=(row[0], row[1], row[2], row[4], row[5], row[6], f"Order {row[7]} {row[3]}"))

        def quarantine_selected_batch() -> None:
            sel = exp_tree.selection()
            if not sel:
                messagebox.showinfo("Select Batch", "Click an expired or damaged batch row in the top table first, then click 'Quarantine Selected Batch'.")
                return
            bid = sel[0]
            conn = database.get_connection()
            try:
                b = conn.execute("SELECT * FROM batches WHERE batch_id=?", (bid,)).fetchone()
                if not b:
                    return
                conn.execute("UPDATE batches SET batch_status='Quarantined' WHERE batch_id=?", (bid,))
                qid = f"QRN-{int(datetime.datetime.now().timestamp()) % 10000:04d}"
                conn.execute(
                    "INSERT INTO quarantine VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (
                        qid, bid, b["medicine_id"], b["medicine_name"], b["supplier_name"],
                        b["remaining_quantity"], "Quarantined via Expiry & Alert Module",
                        b["expiry_date"], datetime.date.today().strftime("%Y-%m-%d"), "Quarantined",
                    ),
                )
                conn.commit()
            finally:
                conn.close()
            database.log_transaction("QUARANTINE", bid, b["medicine_name"], b["supplier_name"], b["remaining_quantity"], f"Quarantined batch {bid}")
            refresh_alerts()
            messagebox.showinfo("Quarantined", f"Batch {bid} has been moved to Quarantine and blocked from dispensing.")

        self._create_action_button(hdr1, "🛡️ Quarantine Selected Batch", quarantine_selected_batch, bg=t["danger"]).pack(side=tk.RIGHT)
        refresh_alerts()

    # ==========================================================================
    # MODULE 9: REPORTS & ANALYTICS (All 10 Reports + CSV & PDF Export)
    # ==========================================================================
    def _build_reports_module(self) -> None:
        t = THEME
        bar = tk.Frame(self.content_frame, bg=t["board_bg"])
        bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(bar, text="Select Hospital Report:", bg=t["board_bg"], fg=t["text_primary"], font=fnt(10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        titles = [title for title, _key in reports_exporter.REPORT_DEFINITIONS]
        key_by_title = dict(reports_exporter.REPORT_DEFINITIONS)
        rep_var = tk.StringVar(value=titles[0])
        rep_cb = ttk.Combobox(bar, textvariable=rep_var, values=titles, state="readonly", width=40)
        rep_cb.pack(side=tk.LEFT, padx=(0, 14))

        table_holder = tk.Frame(self.content_frame, bg=t["board_bg"])
        table_holder.pack(fill=tk.BOTH, expand=True)

        def load_selected_report(*_args: Any) -> Dict[str, Any]:
            for child in table_holder.winfo_children():
                child.destroy()
            rkey = key_by_title.get(rep_var.get(), "complete_inventory")
            data = reports_exporter.fetch_report_data(rkey)
            col_names = list(data["columns"])
            spec: List[Tuple[str, str, int, str]] = []
            for idx, cname in enumerate(col_names):
                clow = cname.lower()
                if any(w_word in clow for w_word in ("name", "supply", "details")):
                    w_col, anc = 235, "w"
                elif any(w_word in clow for w_word in ("category", "supplier", "condition", "department", "notes")):
                    w_col, anc = 165, "w"
                else:
                    w_col, anc = 95, "center"
                spec.append((f"c{idx}", cname, w_col, anc))
            tree = self._create_styled_table(table_holder, spec, height=15)
            for idx, row in enumerate(data["rows"]):
                tree.insert("", tk.END, tags=("even" if idx % 2 == 0 else "odd",), values=row)
            return data

        rep_cb.bind("<<ComboboxSelected>>", load_selected_report)

        def export_csv_click() -> None:
            rkey = key_by_title.get(rep_var.get(), "complete_inventory")
            default_name = f"MediStock_{rkey}_{datetime.date.today().strftime('%Y%m%d')}.csv"
            path = filedialog.asksaveasfilename(
                parent=self,
                title="Export Report to CSV",
                initialfile=default_name,
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv")],
            )
            if path:
                reports_exporter.export_to_csv(rkey, path)
                messagebox.showinfo("CSV Export Complete", f"Saved CSV report to:\n{path}")

        def export_pdf_click() -> None:
            rkey = key_by_title.get(rep_var.get(), "complete_inventory")
            default_name = f"MediStock_{rkey}_{datetime.date.today().strftime('%Y%m%d')}.pdf"
            path = filedialog.asksaveasfilename(
                parent=self,
                title="Export Report to PDF",
                initialfile=default_name,
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
            )
            if path:
                reports_exporter.export_to_pdf(rkey, path)
                messagebox.showinfo("PDF Export Complete", f"Saved PDF report to:\n{path}")

        self._create_action_button(bar, "📄 Export PDF", export_pdf_click, bg=t["danger"]).pack(side=tk.RIGHT, padx=4)
        self._create_action_button(bar, "📊 Export CSV", export_csv_click, bg=t["success"]).pack(side=tk.RIGHT, padx=4)

        load_selected_report()


if __name__ == "__main__":
    app = MediStockApp()
    app.mainloop()
