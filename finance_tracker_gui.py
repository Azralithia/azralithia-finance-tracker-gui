import sys
import json
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from collections import defaultdict
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QStackedWidget, QGraphicsOpacityEffect,
    QCheckBox, QLabel, QLineEdit, QComboBox, QDateEdit, 
    QListWidget, QInputDialog, QDialog, QScrollArea, QGroupBox,
    QFrame, QTableWidget, QTableWidgetItem, QMessageBox, QFormLayout, 
    QDialogButtonBox, QHeaderView
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    pyqtSignal, pyqtProperty, QSettings, QRect, QDate
)
try:
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False


logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "[%(levelname)s] %(asctime)s - Call Line: %(lineno)d - %(message)s",
    "%H:%M:%S"
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Rotating file handler
file_handler = RotatingFileHandler(
    "finance_tracker.log",
    maxBytes=1_000_000,
    backupCount=5
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

conn = sqlite3.connect("transactions.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT,
    date DATETIME NOT NULL,
    note TEXT
)
""")
conn.commit()
# ---------------------------
#           Config
# ---------------------------
BUTTON_WIDTH = 48
BUTTON_HEIGHT = 40
SIDEBAR_COLLAPSED_WIDTH = 60
SIDEBAR_EXPANDED_WIDTH = 300
ANIM_DURATION = 250
TOGGLE_ANIM_DURATION = 200
FADE_DURATION = 200
TOGGLE_WIDTH = 60
TOGGLE_HEIGHT = 28
TOGGLE_MARGIN = 2
TOGGLE_PADDING = 6
DARK_MODE = """
            #SummaryCard {
                border: 1px solid #3a3a3a;
                border-radius: 10px;
                background: #2b2b2b;
            }
            #SummaryCardTitle { 
                font-size: 13px; 
                color: #cfcfcf; 
            }
            #SummaryCardValue { 
                font-size: 24px; 
                font-weight: 600; 
                color: #ffffff; 
            }
            #SummaryGroup { 
                border: 1px solid #3a3a3a; 
                border-radius: 10px; 
            }
            #SummaryLabelSmall { 
            color: #e6e6e6; 
            }
            #SummaryRow { 
                color: #eaeaea;
                font-size: 16px;
                font-weight: 500;
                padding: 4px 0px;
            }
            QWidget { 
                background-color: #2c2c2c; 
                color: white; 
            }
            
            QWidget#SidebarBottom { 
                background-color: #1a1a1a; 
            }     
            
            QWidget#Sidebar { 
                background-color: #1a1a1a; 
                
            }

            #Sidebar QPushButton {
                background-color: transparent;
            }
            #Sidebar QPushButton:hover {
                background-color: rgba(255,255,255,0.08);
            }
            #Sidebar QPushButton:pressed {
                background-color: rgba(255,255,255,0.16);
            }        
            
            /* Sidebar buttons */
            QPushButton { 
                color: white; 
                background-color: #2c2c2c;
                border: none; 
                border-radius: 4px; 
                text-align: left;
                font-size: 14px;
                padding: 6px;
                padding-left: 10px; 
            }
            /* Submenu indentation */
            QPushButton[subitem="true"] {
                padding-left: 30px;
            }
            QPushButton:hover { 
                background-color: #404040; 
            }
            QPushButton:pressed { 
                background-color: #606060;    
            }
            QLabel, QCheckBox { 
                color: white; 
            }
            QLineEdit { 
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
                color: white;
            }
            QTableWidget {
                gridline-color: #555;
                background-color: #2c2c2c;
                alternate-background-color: #3a3a3a;
                color: white;
                selection-background-color: #505050;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: white;
                padding: 4px;
                border: none;
            }
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
                color: white;
            }
            QComboBox QAbstractItemView {
                background-color: #2c2c2c;
                selection-background-color: #404040;
                color: white;
            }
        """

LIGHT_MODE = """
            #SummaryCard {
                border: 1px solid #d0d0d0;
                border-radius: 10px;
                background: #ffffff;
            }
            #SummaryCardTitle { 
                font-size: 13px; 
                color: #333; 
            }
            #SummaryCardValue { 
                font-size: 24px; 
                font-weight: 600; 
                color: #111; 
            }
            #SummaryGroup { 
                border: 1px solid #e0e0e0; 
                border-radius: 10px; 
            }
            #SummaryLabelSmall { 
            color: #222; 
            }
            #SummaryRow { 
                color: #222;
                font-size: 16px;
                font-weight: 500;
                padding: 4px 0px;
            }
            QWidget { 
                background-color: #f0f0f0; 
                color: black; 
            }
            
            QWidget#SidebarBottom { 
                background-color: #e6e6e6; 
            }
            
            QWidget#Sidebar { 
                background-color: #e6e6e6; 
            }

            #Sidebar QPushButton {
                background-color: transparent;
            }
            #Sidebar QPushButton:hover {
                background-color: rgba(0,0,0,0.06);
            }
            #Sidebar QPushButton:pressed {
                background-color: rgba(0,0,0,0.12);
            }

            /* Sidebar buttons */
            QPushButton { 
                color: black;                      
                background-color: #f5f5f5; 
                border: none; 
                border-radius: 4px;
                text-align: left;
                font-size: 14px;
                padding: 6px;
                padding-left: 10px;               
            }
            /* Submenu indentation */
            QPushButton[subitem="true"] {
                padding-left: 30px;
            }
            QPushButton:hover { 
                background-color: #dcdcdc; 
            }
            QPushButton:pressed { 
                background-color: #c0c0c0;    
            }
            QLabel, QCheckBox { 
                color: black; 
            }
            QLineEdit { 
                background-color: white;
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 4px;
                color: black;
            }
            QTableWidget {
                gridline-color: #ccc;
                background-color: white;
                alternate-background-color: #f5f5f5;
                color: black;
                selection-background-color: #d0d0d0;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                color: black;
                padding: 4px;
                border: none;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 4px;
                color: black;
            }
            QComboBox QAbstractItemView {
                background-color: #fff;
                selection-background-color: #dcdcdc;
                color: black;
            }
        """

def map_display_format(display_format: str) -> str:
    if display_format == "(DD-MM-YYYY) | Day-Month-Year":
        return "dd-MM-yyyy"
    if display_format == "(MM-DD-YYYY) | Month-Day-Year":
        return "MM-dd-yyyy"
    if display_format == "(YYYY-DD-MM) | Year-Day-Month":
        return "yyyy-dd-MM"
    return "yyyy-MM-dd" # Default to Year-Month-Day

def graph_format(display_format: str) -> str:
    if display_format == "dd-MM-yyyy":
        return "%d-%m-%Y"
    if display_format == "MM-dd-yyyy":
        return "%m-%d-%Y"
    if display_format == "yyyy-dd-mm":
        return "%Y-%d-%m"
    return "%Y-%m-%d" # Default to Year-Month-Day

def format_date_for_display(date_str: str) -> str:
    s = QSettings("Azralithia", "FinanceTracker").value("date_format", "(YYYY-MM-DD) | Year-Month-Day")
    
    if " | " in s:
        s = s.split(" | ")[0].strip("()") 
    try:
        y, m, d = date_str.split("-")
    except Exception:
        return date_str
    
    if s == "DD-MM-YYYY":
        return f"{d}-{m}-{y}"
    if s == "MM-DD-YYYY":
        return f"{m}-{d}-{y}"
    if s == "YYYY-DD-MM":
        return f"{y}-{d}-{m}"
    return f"{y}-{m}-{d}" # Default to Year-Month-Day

class HistoryPage(QWidget):
    data_changed = pyqtSignal()
    def __init__(self, db_path="transactions.db", parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.page_size = 10
        self.current_page = 0
        self.total_rows = 0
        self._build_ui()
        settings = QSettings("Azralithia", "FinanceTracker")
        save = settings.value("save_filters", False, type=bool)
        if save:
            raw = settings.value("history_filters", None)
            try:
                data = json.loads(raw) if raw else None
            except Exception:
                data = None
            if data:
                self.type_filter.setCurrentText(data.get("type", "All"))
                self._load_category_filter()
                self.category_filter.setCurrentText(data.get("category", "All"))
                
                current_display_format = settings.value("date_format", "(YYYY-MM-DD) | Year-Month-Day")
                display_format = map_display_format(current_display_format)
                self.start_date.setDisplayFormat(display_format)
                self.end_date.setDisplayFormat(display_format)
                self.start_date.setDate(QDate.fromString(data.get("start", QDate.currentDate().addMonths(-1).toString("yyyy-MM-dd")), "yyyy-MM-dd"))
                self.end_date.setDate(QDate.fromString(data.get("end", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
                self.note_search.setText(data.get("note", ""))
        self._load_category_filter()
        self.load_page()

    # ---------- UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)
        # Filters row
        fr = QHBoxLayout()
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All", "Income", "Expense"])
        self.type_filter.currentIndexChanged.connect(self._load_category_filter)
        self.type_filter.currentIndexChanged.connect(self._apply_filters)
        self.category_filter = QComboBox()
        self.category_filter.addItem("All")

        settings = QSettings("Azralithia", "FinanceTracker")
        current_display_format = settings.value("date_format", "(YYYY-MM-DD) | Year-Month-Day")
        display_format = map_display_format(current_display_format)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat(display_format) 
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat(display_format)
        self.end_date.setDate(QDate.currentDate())

        self.note_search = QLineEdit()
        self.note_search.setPlaceholderText("Search notes…")

        self.apply_btn = QPushButton("Apply")
        self.reset_btn = QPushButton("Reset")

        for w in (QLabel("Type:"), self.type_filter,
                  QLabel("Category:"), self.category_filter,
                  QLabel("From:"), self.start_date,
                  QLabel("To:"), self.end_date,
                  self.note_search, self.apply_btn, self.reset_btn):
            fr.addWidget(w)
        fr.addStretch()
        root.addLayout(fr)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Date", "Type", "Category", "Amount", "Note", "Actions"]
        )
        self.table.horizontalHeader().setStretchLastSection(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 100)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.cellClicked.connect(self._handle_cell_click)
        root.addWidget(self.table)

        # Pager
        pr = QHBoxLayout()
        self.prev_btn = QPushButton("⬅️")
        self.next_btn = QPushButton("➡️")
        for b in (self.prev_btn, self.next_btn):
            b.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.setToolTip("Previous 10")
        self.next_btn.setToolTip("Next 10")
        self.page_label = QLabel("Page 1 / 1")

        pr.addStretch()
        pr.addWidget(self.prev_btn)
        pr.addWidget(self.next_btn)
        pr.addWidget(self.page_label)
        root.addLayout(pr)

        # Hooks
        self.apply_btn.clicked.connect(self._apply_filters)
        self.reset_btn.clicked.connect(self._reset_filters)
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn.clicked.connect(self._next_page)
        
    def _handle_cell_click(self, row, column):
        transaction_id_item = self.table.item(row, 0)
        if not transaction_id_item:
            return
        
        transaction_id = int(transaction_id_item.text())
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT date, type, category, amount, note FROM transactions WHERE id=?", (transaction_id,))
        data = cur.fetchone()
        conn.close()
        if not data:
            return 
        date, ttype, category, amount, note = data
        dialog = TransactionEditDialog(transaction_id, self.db_path, self)

        # If the user clicks on data from the table, opens up Editing focus on that data
        if column == 1: 
            dialog.date_edit.setDate(QDate.fromString(date, "yyyy-MM-dd"))
            dialog.date_edit.setFocus()
        elif column == 2: 
            dialog.type_combo.setCurrentText(ttype.title())
            dialog.type_combo.setFocus()
        elif column == 3: 
            dialog.category_edit.setText(category)
            dialog.category_edit.setFocus()
        elif column == 4: 
            dialog.amount_edit.setText(str(amount))
            dialog.amount_edit.setFocus()
        elif column == 5: 
            dialog.note_edit.setText(note)
            dialog.note_edit.setFocus()
        else: 
            pass
        if dialog.exec():
            self.load_page()
            self.data_changed.emit()

    def update_page_size_from_viewport(self):
        row_h = self.table.verticalHeader().defaultSectionSize() or 36
        viewport_h = self.table.viewport().height()
        if viewport_h <= 0:
            return False  
        new_page_size = max(1, viewport_h // row_h)
        if new_page_size != self.page_size:
            self.page_size = int(new_page_size)
            self.current_page = max(0, min(self.current_page, max(0, (self.total_rows - 1) // self.page_size)))
            return True
        return False

    # ---------- Filters & Paging ----------
    def _reset_filters(self):
        self.type_filter.setCurrentIndex(0)
        self.category_filter.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date.setDate(QDate.currentDate())
        self.note_search.clear()
        self.current_page = 0
        self.load_page()

    def _apply_filters(self):
        self.current_page = 0
        self.load_page()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

    def _next_page(self):
        max_page = max(0, (self.total_rows - 1) // self.page_size)
        if self.current_page < max_page:
            self.current_page += 1
            self.load_page()

    def _build_where_and_params(self):
        conds, params = [], []

        t = self.type_filter.currentText()
        if t != "All":
            conds.append("lower(type) = ?")
            params.append(t.lower())

        c = self.category_filter.currentText()
        if c != "All":
            conds.append("lower(category) = ?")
            params.append(c.lower())

        sd = self.start_date.date().toString("yyyy-MM-dd")
        ed = self.end_date.date().toString("yyyy-MM-dd")
        if sd:
            conds.append("date >= ?")
            params.append(sd)
        if ed:
            conds.append("date <= ?")
            params.append(ed)

        q = self.note_search.text().strip()
        if q:
            conds.append("note LIKE ?")
            params.append(f"%{q}%")

        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        return where, params

    def _load_category_filter(self):
        settings = QSettings("Azralithia", "FinanceTracker")
        stored = settings.value("categories", None)
        defaults = {
            "Income": ["Salary", "Gift", "Bonus", "Other"],
            "Expense": ["Food", "Rent", "Utilities", "Transport", "Misc"]
        }
        try:
            cats_map = json.loads(stored) if stored else defaults
        except Exception:
            cats_map = defaults

        t = self.type_filter.currentText()
        items = []
        if t == "All":
            seen = set()
            for lst in cats_map.values():
                for c in lst:
                    if c and c.lower() not in seen:
                        seen.add(c.lower())
                        items.append(c.title())
        else:
            items = [c.title() for c in cats_map.get(t, [])]

        self.category_filter.blockSignals(True)
        current = self.category_filter.currentText()
        self.category_filter.clear()
        self.category_filter.addItem("All")
        for c in items:
            self.category_filter.addItem(c)
        if current and current in [self.category_filter.itemText(i) for i in range(self.category_filter.count())]:
            self.category_filter.setCurrentText(current)
        self.category_filter.blockSignals(False)

    def load_page(self):
        where, params = self._build_where_and_params()

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM transactions {where}", params)
        self.total_rows = cur.fetchone()[0]

        limit = self.page_size
        offset = self.current_page * self.page_size
        cur.execute(
            f"""SELECT id, date, type, category, amount, COALESCE(note,'')
                FROM transactions
                {where}
                ORDER BY date DESC, id DESC
                LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        )
        rows = cur.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        for r, (rid, date, t, cat, amt, note) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(rid)))
            self.table.setItem(r, 1, QTableWidgetItem(format_date_for_display(date)))
            self.table.setItem(r, 2, QTableWidgetItem(t.title()))
            self.table.setItem(r, 3, QTableWidgetItem((cat or "").title()))
            self.table.setItem(r, 4, QTableWidgetItem(f"{amt:.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(note))

            edit_btn = QPushButton(" ✏️")
            delete_btn = QPushButton(" 🗑️")
            for b, tip in ((edit_btn, "Edit"), (delete_btn, "Delete")):
                b.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.setToolTip(tip)

            edit_btn.clicked.connect(lambda _, _rid=rid: self.edit_transaction(_rid))
            delete_btn.clicked.connect(lambda _, _rid=rid: self.delete_transaction(_rid))

            btns = QWidget()
            h = QHBoxLayout(btns)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            h.addWidget(edit_btn)
            h.addWidget(delete_btn)
            self.table.setRowHeight(r, self.table.verticalHeader().defaultSectionSize())
            h.addStretch()
            self.table.setCellWidget(r, 6, btns)
            self.table.setRowHeight(r, self.table.verticalHeader().defaultSectionSize())

        max_page = max(0, (self.total_rows - 1) // self.page_size)
        self.page_label.setText(f"Page {self.current_page + 1} / {max_page + 1 if self.total_rows else 1}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < max_page)

    # ---------- Actions ----------
    def delete_transaction(self, transaction_id: int):
        settings = QSettings("Azralithia", "FinanceTracker")
        confirm_delete = settings.value("confirm_delete", True, type=bool) 
        if confirm_delete: 
            reply = QMessageBox.question(self, 'Confirm Delete', "Are you sure you want to delete this transaction?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) 
            if reply == QMessageBox.StandardButton.No: 
                return 
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
        conn.commit()
        conn.close()
        max_page = max(0, (self.total_rows - 2) // self.page_size)
        self.current_page = min(self.current_page, max_page)
        self.load_page()
        self.data_changed.emit()

    def edit_transaction(self, transaction_id: int):
        dialog = TransactionEditDialog(transaction_id, self.db_path, self)
        if dialog.exec():
            self.load_page()
            self.data_changed.emit()


class TransactionEditDialog(QDialog):
    def __init__(self, transaction_id, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.transaction_id = transaction_id
        self.setWindowTitle("Edit Transaction")
        self.resize(400, 220)
        self.settings = QSettings("Azralithia", "FinanceTracker")

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QFormLayout(self)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        settings = QSettings("Azralithia", "FinanceTracker")
        current_display_format = settings.value("date_format", "(YYYY-MM-DD) | Year-Month-Day")
        display_format = map_display_format(current_display_format)
        self.date_edit.setDisplayFormat(display_format) 

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Income", "Expense"])
        self.type_combo.currentIndexChanged.connect(self._load_categories_for_type)
        
        self.category_combo = QComboBox()
        self.amount_edit = QLineEdit()
        self.note_edit = QLineEdit()

        layout.addRow("Date:", self.date_edit)
        layout.addRow("Type:", self.type_combo)
        layout.addRow("Category:", self.category_combo)
        layout.addRow("Amount:", self.amount_edit)
        layout.addRow("Note:", self.note_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.save_changes)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)
    
    def _load_categories_for_type(self):
        selected_type = self.type_combo.currentText()
        stored = self.settings.value("categories", None)
        defaults = {
            "Income": ["Salary", "Gift", "Bonus", "Other"],
            "Expense": ["Food", "Rent", "Utilities", "Transport", "Misc"]
        }
        try:
            cats_map = json.loads(stored) if stored else defaults
        except Exception:
            cats_map = defaults
        categories = cats_map.get(selected_type, [])
        
        self.category_combo.blockSignals(True) 
        self.category_combo.clear()
        for cat in categories:
            self.category_combo.addItem(cat.title()) 
        self.category_combo.blockSignals(False)

    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT date, type, category, amount, note FROM transactions WHERE id=?", (self.transaction_id,))
        row = cur.fetchone()
        conn.close()

        if row:
            date, ttype, category, amount, note = row
            self.date_edit.setDate(QDate.fromString(date, "yyyy-MM-dd"))
            
            self.type_combo.setCurrentText(ttype.title())
            self._load_categories_for_type()
            
            if category and category.title() in [self.category_combo.itemText(i) for i in range(self.category_combo.count())]:
                self.category_combo.setCurrentText(category.title())
            else:
                if self.category_combo.count() > 0:
                    self.category_combo.setCurrentIndex(0)
                else:
                    self.category_combo.addItem("Other") 
                    self.category_combo.setCurrentText("Other")
            self.amount_edit.setText(str(amount))
            self.note_edit.setText(note or "")

    def save_changes(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        ttype = self.type_combo.currentText().lower()
        category = self.category_combo.currentText().lower()
        try:
            amount = float(self.amount_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Amount must be a number.")
            return
        note = self.note_edit.text()

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "UPDATE transactions SET date=?, type=?, category=?, amount=?, note=? WHERE id=?",
            (date, ttype, category, amount, note, self.transaction_id),
        )
        conn.commit()
        conn.close()
        self.accept()


class SummaryPage(QWidget):
    def __init__(self, db_path="transactions.db", parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self._build_ui()

        self.start_picker.dateChanged.connect(self.refresh_summary)
        self.end_picker.dateChanged.connect(self.refresh_summary)
        self.refresh_summary()

    def set_db_path(self, db_path: str):
        self.db_path = db_path
        self.refresh_summary()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(12)

        settings = QSettings("Azralithia", "FinanceTracker")
        current_display_format = settings.value("date_format", "(YYYY-MM-DD) | Year-Month-Day") 
        display_format = map_display_format(current_display_format)

        self.start_label = QLabel("📅 From:")
        self.start_label.setObjectName("SummaryLabelSmall")
        self.start_picker = QDateEdit()
        self.start_picker.setCalendarPopup(True)
        self.start_picker.setDisplayFormat(display_format)
        self.start_picker.setDate(QDate.currentDate().addMonths(-1))

        self.end_label = QLabel("To:")
        self.end_picker = QDateEdit()
        self.end_picker.setCalendarPopup(True)
        self.end_picker.setDisplayFormat(display_format) 
        self.end_picker.setDate(QDate.currentDate())

        header.addWidget(self.start_label)
        header.addWidget(self.start_picker)
        header.addWidget(self.end_label)
        header.addWidget(self.end_picker)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_summary)

        # Totals
        totals = QHBoxLayout()
        totals.setSpacing(12)

        self.card_income = self._make_metric_card("Income", "0.00")
        self.card_expense = self._make_metric_card("Expense", "0.00")
        self.card_balance = self._make_metric_card("Balance", "0.00")

        totals.addWidget(self.card_income)
        totals.addWidget(self.card_expense)
        totals.addWidget(self.card_balance)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        inner = QWidget()
        inner_layout = QHBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(16)

        self.gb_income = self._make_group_box("Income Breakdown")
        self.gb_expense = self._make_group_box("Expense Breakdown")
        self.gb_income.setObjectName("SummaryCardTitle")
        self.gb_expense.setObjectName("SummaryCardTitle")
        
        inner_layout.addWidget(self.gb_income)
        inner_layout.addWidget(self.gb_expense)
        scroll.setWidget(inner)
    
        # Graph 
        if MATPLOTLIB_AVAILABLE:
            self.graph_fig = Figure(figsize=(4,3), tight_layout=True)
            self.graph_canvas = FigureCanvas(self.graph_fig)
            outer.addWidget(self.graph_canvas)
        else:
            self.graph_placeholder = QLabel("Graph unavailable (matplotlib not installed)")
            outer.addWidget(self.graph_placeholder)
        outer.addLayout(header)
        outer.addLayout(totals)
        outer.addWidget(self._hline())
        outer.addWidget(scroll)
    
    def _make_metric_card(self, title: str, value: str) -> QGroupBox:
        box = QGroupBox()
        box.setObjectName("SummaryCard")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(16, 12, 16, 16)
        lay.setSpacing(6)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("SummaryCardTitle")

        lbl_value = QLabel(value)
        lbl_value.setObjectName("SummaryCardValue")

        lay.addWidget(lbl_title)
        lay.addWidget(lbl_value)
        lay.addStretch()

        box._value_label = lbl_value
        return box

    def _make_group_box(self, title: str) -> QGroupBox:
        gb = QGroupBox(title)
        gb.setObjectName("SummaryGroup")
        v = QVBoxLayout(gb)
        v.setContentsMargins(16, 20, 16, 16)  
        v.setSpacing(8)  

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(6)  

        v.addWidget(inner)
        v.addStretch()

        gb._rows_container = inner
        gb._rows_layout = inner_layout
        return gb

    def _hline(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _plot_balance_over_range(self, start_date, end_date):
        if not MATPLOTLIB_AVAILABLE:
            return
        
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT date,
               SUM(CASE WHEN lower(type)='income' THEN amount WHEN lower(type)='expense' THEN -amount ELSE 0 END) as net
            FROM transactions
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date
        """, (start_date, end_date))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            dates = []
            nets = []
        else:
            rows_map = {r[0]: r[1] for r in rows}
            d0 = datetime.strptime(start_date, "%Y-%m-%d")
            d1 = datetime.strptime(end_date, "%Y-%m-%d")
            raw_dates = []
            nets = []
            running = 0.0
            cur_date = d0
            while cur_date <= d1:
                s = cur_date.strftime("%Y-%m-%d")
                net = float(rows_map.get(s, 0.0))
                running += net
                raw_dates.append(cur_date) 
                nets.append(running)
                cur_date += timedelta(days=1)
            dates = mdates.date2num(raw_dates)
        # plot
        self.graph_fig.clf()
        ax = self.graph_fig.add_subplot(111)
            
        settings = QSettings("Azralithia", "FinanceTracker")
        light_mode = settings.value("light_mode", False, type=bool)
            
        if light_mode:
            ax.set_facecolor("#f0f0f0") 
            self.graph_fig.set_facecolor("#f0f0f0")
            ax.tick_params(axis='x', colors='black')
            ax.tick_params(axis='y', colors='black')
            ax.yaxis.label.set_color('black')
            ax.xaxis.label.set_color('black')
            ax.title.set_color('black')
            ax.spines['bottom'].set_color('black')
            ax.spines['top'].set_color('black')
            ax.spines['right'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.grid(True, color='#ccc') 
            line_color = '#1f77b4' 
        else:
            # Dark mode
            ax.set_facecolor("#2c2c2c") 
            self.graph_fig.set_facecolor("#2c2c2c")
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.yaxis.label.set_color('white')
            ax.xaxis.label.set_color('white')
            ax.title.set_color('white')
            ax.spines['bottom'].set_color('#555') 
            ax.spines['top'].set_color('#555')
            ax.spines['right'].set_color('#555')
            ax.spines['left'].set_color('#555')
            ax.grid(True, color='#4a4a4a') 
            line_color = '#88c0d0' 
            
        if dates.size > 0: 
            ax.plot(dates, nets, color=line_color) 
            ax.set_title("Balance over Time")
            ax.set_xlabel("Date")
            ax.set_ylabel("Balance")
            current_display_format = settings.value("date_format", "(YYYY-MM-DD) | Year-Month-Day")
            display_format = map_display_format(current_display_format) 
            strftime_format = graph_format(display_format)
            ax.xaxis.set_major_formatter(mdates.DateFormatter(strftime_format))
            self.graph_fig.autofmt_xdate()
        else:
            ax.text(0.5, 0.5, "No data for selected range", ha='center', va='center', color='white' if not light_mode else 'black')
        self.graph_canvas.draw_idle()

    # --=-- Data / Queries --=--
    def _get_date_range(self):
        sd = self.start_picker.date().toString("yyyy-MM-dd")
        ed = self.end_picker.date().toString("yyyy-MM-dd")
        return sd, ed

    def _connect(self):
        if not self.db_path:
            raise RuntimeError("SummaryPage: db_path not set. Call set_db_path(path_to_sqlite).")
        return sqlite3.connect(self.db_path)

    def _fetch_totals_and_counts(self, start_date: str, end_date: str):
        totals = {'income': 0.0, 'expense': 0.0, 'balance': 0.0}
        counts_income = defaultdict(lambda: {'total': 0.0, 'count': 0})
        counts_expense = defaultdict(lambda: {'total': 0.0, 'count': 0})

        query_totals = """
            SELECT lower(type) AS type, COALESCE(SUM(amount),0) AS total
            FROM transactions
            WHERE date >= ? AND date <= ?
            GROUP BY lower(type)
        """
        query_counts = """
            SELECT lower(type) AS type, lower(category) AS category,
                COALESCE(SUM(amount),0) AS total, COUNT(*) AS count
            FROM transactions
            WHERE date >= ? AND date <= ?
            GROUP BY lower(type), lower(category)
            ORDER BY total DESC
        """
        ym = (start_date, end_date)
        with self._connect() as conn:
            cur = conn.cursor()
            # Overall totals
            for t, total in cur.execute(query_totals, ym):
                if t.lower() == "income":
                    totals['income'] = float(total or 0)
                elif t.lower() == "expense":
                    totals['expense'] = float(total or 0)
            totals['balance'] = totals['income'] - totals['expense']

            # Detailed counts per category
            for t, cat, total_amt, count in cur.execute(query_counts, ym):
                if (t or "").lower() == "income":
                    counts_income[cat or "Uncategorized"] = {
                        'total': float(total_amt or 0),
                        'count': int(count or 0)
                    }
                elif (t or "").lower() == "expense":
                    counts_expense[cat or "Uncategorized"] = {
                        'total': float(total_amt or 0),
                        'count': int(count or 0)
                    }

        return totals, counts_income, counts_expense

    # ----- Refresh / Render -----
    def refresh_summary(self):
        try:
            sd, ed = self._get_date_range()
            totals, c_in, c_ex = self._fetch_totals_and_counts(sd, ed)

            self.card_income._value_label.setText(f"{totals['income']:.2f}")
            self.card_expense._value_label.setText(f"{totals['expense']:.2f}")
            self.card_balance._value_label.setText(f"{totals['balance']:.2f}")

            self._render_breakdown(self.gb_income, c_in)
            self._render_breakdown(self.gb_expense, c_ex)
            self._plot_balance_over_range(sd, ed)

        except Exception as e:
            # Show a error in the UI instead of crashing
            self.card_income._value_label.setText("—")
            self.card_expense._value_label.setText("—")
            self.card_balance._value_label.setText("—")
            self._render_breakdown(self.gb_income, {"Error": 1})
            self._render_breakdown(self.gb_expense, {str(e): 1})

    def _render_breakdown(self, groupbox: QGroupBox, data: dict):
        lay = groupbox._rows_layout
        while (item := lay.takeAt(0)) is not None:
            w = item.widget()
            if w:
                w.deleteLater()

        if not data:
            lbl = QLabel("No data.")
            lbl.setObjectName("SummaryRow")
            lay.addWidget(lbl)
            return

        for cat, info in data.items():
            total = info['total']
            count = info['count']
            capitalized_cat = cat.title() if cat else "Uncategorized"
            row = QLabel(f"{capitalized_cat} ({count}) — {total:.2f}")
            row.setObjectName("SummaryRow")
            lay.addWidget(row)
    
    def apply_theme(self, mode: str):
        if mode == "dark":
            self.setStyleSheet(DARK_MODE)
        else:
            self.setStyleSheet(LIGHT_MODE)
        self.refresh_summary()


class ToggleSwitch(QCheckBox):
    thumbChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setChecked(False)          
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(TOGGLE_WIDTH, TOGGLE_HEIGHT)

        self._thumb_x = 2
        self._track_dark = True         # Updated by theme: dark=True, light=False
        self._emoji = "🌙"

        # Animation
        self._anim = QPropertyAnimation(self, b"thumb_pos", self)
        self._anim.setDuration(TOGGLE_ANIM_DURATION)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Hook state → animation & emoji
        self.toggled.connect(self._animate_to_state)
        self.toggled.connect(self._update_emoji)

    def get_thumb_pos(self) -> float:
        return float(self._thumb_x)

    def set_thumb_pos(self, x: float):
        self._thumb_x = float(x)
        self.thumbChanged.emit()
        self.update()

    thumb_pos = pyqtProperty(float, fget=get_thumb_pos, fset=set_thumb_pos, notify=thumbChanged)

    #  -=- Helpers -=-
    def _left_pos(self) -> int:
        return TOGGLE_MARGIN

    def _right_pos(self) -> int:
        thumb_d = self.height() - TOGGLE_PADDING
        return self.width() - thumb_d - TOGGLE_MARGIN

    def _animate_to_state(self, checked: bool):
        start = self._thumb_x
        end = self._right_pos() if checked else self._left_pos()
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()

    def _update_emoji(self, checked: bool):
        if self._emoji == "":
            return
        self._emoji = "☀️" if checked else "🌙"
        self.update()

    def resizeEvent(self, e):
        self._thumb_x = self._right_pos() if self.isChecked() else self._left_pos()
        super().resizeEvent(e)

    def mousePressEvent(self, event):
        """Make the whole widget clickable; avoid double-toggle by consuming the event."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QBrush, QFont
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        radius = rect.height() / 2

        # Track color depends on theme + state
        if self.isChecked():
            track_color = QColor("#00c853") if self._track_dark else QColor("#1976d2")
        else:
            track_color = QColor("#555") if self._track_dark else QColor("#bbb")

        # Track
        p.setBrush(QBrush(track_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, radius, radius)

        # Thumb
        thumb_d = rect.height() - TOGGLE_PADDING
        thumb_y = (rect.height() - thumb_d) // 2
        thumb_rect = QRect(int(self._thumb_x), int(thumb_y), int(thumb_d), int(thumb_d))

        p.setBrush(QBrush(QColor("#fff")))
        p.drawEllipse(thumb_rect)

        # Emoji inside the thumb (moves with it)
        p.setFont(QFont("Segoe UI Emoji", 11))
        p.setPen(QColor("#000"))
        p.drawText(thumb_rect, Qt.AlignmentFlag.AlignCenter, self._emoji)

        p.end()


class SidebarButton(QPushButton):
    clicked_action = pyqtSignal(str)

    def __init__(self, icon, text, is_subitem=False, start_collapsed=True):
        super().__init__(f"{icon} {text}")
        self.icon_only = icon
        self.full_text = f"{icon} {'    ' if is_subitem else ''}{text}"
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(BUTTON_HEIGHT)
        self.setProperty("subitem", is_subitem)  # Left padding

        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(FADE_DURATION)

        self.setText(self.icon_only)
        self.opacity_effect.setOpacity(1)

        self.clicked.connect(lambda: self.clicked_action.emit(text))

    def set_collapsed(self, collapsed: bool):
        if collapsed:
            self.setText(self.icon_only)
            self.opacity_anim.stop()
            self.opacity_effect.setOpacity(1.0)
            self.update()
        else:
            self.setText(self.full_text)
            self._fade(0, 1)

    def _fade(self, start, end):
        self.opacity_anim.stop()
        self.opacity_anim.setStartValue(start)
        self.opacity_anim.setEndValue(end)
        self.opacity_anim.start()


class Submenu(QWidget):
    def __init__(self, buttons):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        for btn in buttons:
            self.layout.addWidget(btn)

        self.setMaximumHeight(0)
        self.anim = QPropertyAnimation(self, b"maximumHeight")
        self.anim.setDuration(ANIM_DURATION)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def toggle(self):
        target_height = BUTTON_HEIGHT * self.layout.count() if self.maximumHeight() == 0 else 0
        self.anim.stop()
        self.anim.setStartValue(self.maximumHeight())
        self.anim.setEndValue(target_height)
        self.anim.start()


class Sidebar(QWidget):
    theme_toggled = pyqtSignal(bool)
    action_triggered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMaximumWidth(SIDEBAR_COLLAPSED_WIDTH)

        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(ANIM_DURATION)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.buttons = []

        # Main buttons
        self.add_button("🏠", "Main")
        self.finance_btn = self.add_button("💰", "Finance Tracker")

        # Submenu
        self.sub_buttons = [
            SidebarButton("📝", "Manage Transactions", is_subitem=True),
            SidebarButton("📊", "Show Summary", is_subitem=True),
            SidebarButton("📜", "Transaction Log", is_subitem=True),
            SidebarButton("📤", "Export to CSV", is_subitem=True),
        ]
        self.submenu = Submenu(self.sub_buttons)
        self.layout.addWidget(self.submenu)

        self.add_button("⚙️", "Settings")
        self.layout.addStretch()  # Pushes buttons to the top

        # Exit + Theme switch row
        bottom_container = QWidget()
        bottom_container.setObjectName("SidebarBottom") 
        bottom_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        bottom_layout.setSpacing(10)

        self.exit_btn = SidebarButton("🚪", "Exit")
        self.theme_switch = ToggleSwitch()
        self.theme_switch.toggled.connect(self.toggle_theme)
        self.theme_switch.setVisible(False)  # <-- Hidden at startup
        
        bottom_layout.addWidget(self.exit_btn)
        bottom_layout.addWidget(self.theme_switch)

        self.layout.addWidget(bottom_container) 

        # Toggle submenu
        self.finance_btn.clicked.connect(self.submenu.toggle)

        # Relay signals
        self.exit_btn.clicked_action.connect(self.action_triggered)
        for btn in self.buttons + self.sub_buttons:
            btn.clicked_action.connect(self.action_triggered)

    def add_button(self, icon, text, sub=False):
        btn = SidebarButton(icon, text, is_subitem=sub, start_collapsed=True)
        self.layout.addWidget(btn)
        self.buttons.append(btn)
        return btn

    def animate_sidebar(self, target_width, collapsed):
        self.animation.stop()
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.start()

        for btn in self.buttons + self.sub_buttons + [self.exit_btn]:
            btn.set_collapsed(collapsed)

        self.theme_switch.setVisible(not collapsed)   

    def enterEvent(self, event):
        self.animate_sidebar(SIDEBAR_EXPANDED_WIDTH, collapsed=False)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_sidebar(SIDEBAR_COLLAPSED_WIDTH, collapsed=True)
        super().leaveEvent(event)

    def toggle_theme(self, state):
        self.theme_toggled.emit(bool(state))


class MainPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("🏠 Welcome to Finance Tracker")
        label.setStyleSheet("font-size: 20px;")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("⚙️ Settings")
        label.setStyleSheet("font-size: 24px;")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.settings = QSettings("Azralithia", "FinanceTracker")
        
        # Date format selector
        df_row = QHBoxLayout()
        df_row.addWidget(QLabel("Date format:"))
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems(["(DD-MM-YYYY) | Day-Month-Year", "(MM-DD-YYYY) | Month-Day-Year", "(YYYY-MM-DD) | Year-Month-Day",  "(YYYY-DD-MM) | Year-Day-Month"])
        current_fmt = self.settings.value("date_format", "yyyy-MM-dd")
        self.date_format_combo.setCurrentText(current_fmt)
        df_row.addWidget(self.date_format_combo)
        df_row.addStretch()
        layout.addLayout(df_row)

        # Save filters toggle
        row = QHBoxLayout()
        save_filters_label = QLabel("Save filters on exit") 
        save_filters_label.setStyleSheet("font-size: 16px;") 
        row.addWidget(save_filters_label)
            
        self.save_filters_switch = ToggleSwitch()
        self.save_filters_switch._emoji = "" 
        sf = self.settings.value("save_filters", False, type=bool)
        self.save_filters_switch.setChecked(bool(sf))
            
        row.addWidget(self.save_filters_switch)
        row.addStretch() 
        layout.addLayout(row)
        confirm_delete_row = QHBoxLayout() 
        confirm_delete_label = QLabel("Confirm delete transactions") 
        confirm_delete_label.setStyleSheet("font-size: 16px;") 
        confirm_delete_row.addWidget(confirm_delete_label) 
        self.confirm_delete_switch = ToggleSwitch() 
        self.confirm_delete_switch._emoji = "" 
        cd = self.settings.value("confirm_delete", True, type=bool) # Default to True 
        self.confirm_delete_switch.setChecked(bool(cd)) 
        confirm_delete_row.addWidget(self.confirm_delete_switch) 
        confirm_delete_row.addStretch() 
        layout.addLayout(confirm_delete_row) 
        layout.addStretch()
        

class TransactionsPage(QWidget):
    data_changed = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Azralithia", "FinanceTracker")
        layout = QVBoxLayout(self)

        title = QLabel("📝 Manage Transactions")
        title.setStyleSheet("font-size: 20px; margin-bottom: 10px;")
        layout.addWidget(title)

        # Income/Expense selector
        self.type_row = QHBoxLayout()
        self.income_btn = QPushButton("Income")
        self.expense_btn = QPushButton("Expense")
        for btn in (self.income_btn, self.expense_btn):
            btn.setCheckable(True)
            btn.setFixedHeight(35)
            self.type_row.addWidget(btn)
        layout.addLayout(self.type_row)

        self.income_btn.clicked.connect(lambda: self.set_type("Income"))
        self.expense_btn.clicked.connect(lambda: self.set_type("Expense"))

        # Categories 
        self.categories = {}         
        self.load_categories()       

        # Default type = Expense
        self.current_type = "Expense"
        self.expense_btn.setChecked(True)
        self.update_type_styles()

        # Category dropdown + edit button
        cat_row = QHBoxLayout()
        self.category = QComboBox()
        self.edit_cat_btn = QPushButton(" ✏️")
        self.edit_cat_btn.setFixedWidth(BUTTON_WIDTH)
        cat_row.addWidget(self.category)
        cat_row.addWidget(self.edit_cat_btn)
        layout.addLayout(cat_row)
        self.reload_categories()

        # Form fields
        self.amount = QLineEdit()
        self.amount.setPlaceholderText("Amount")
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())

        settings = QSettings("Azralithia", "FinanceTracker")
        current_display_format = settings.value("date_format", "(YYYY-MM-DD) | Year-Month-Day")
        display_format = map_display_format(current_display_format)
        self.date.setDisplayFormat(display_format)

        self.notes = QLineEdit()
        self.notes.setPlaceholderText("Notes (optional)")

        for widget in (self.amount, self.date, self.notes):
            layout.addWidget(widget)

        self.save_btn = QPushButton("💾 Save Transaction")
        layout.addWidget(self.save_btn)

        self.feedback = QLabel("")
        layout.addWidget(self.feedback)

        # Hookups
        self.edit_cat_btn.clicked.connect(self.edit_categories)
        self.save_btn.clicked.connect(self.save_transaction)  

        # Recent transactions preview
        recent_label = QLabel("Recent transactions")
        recent_label.setStyleSheet("font-weight:600; margin-top:8px;")
        layout.addWidget(recent_label)

        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(6)
        self.recent_table.setHorizontalHeaderLabels(["Date", "Type", "Category", "Amount","Note", "Actions"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header = self.recent_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)   
        self.recent_table.setColumnWidth(5, 100) 
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.recent_table)
    
    def showEvent(self, event):
            self.load_recent_transactions()
            super().showEvent(event)

    def load_recent_transactions(self, limit=10):
        conn = sqlite3.connect("transactions.db")
        cur = conn.cursor()
        cur.execute("SELECT id, date, type, category, amount, COALESCE(note,'') FROM transactions ORDER BY id DESC LIMIT ?", (limit,)) 
        rows = cur.fetchall()
        conn.close()

        self.recent_table.setRowCount(len(rows))
        for r, (rid, date, t, cat, amt, note) in enumerate(rows): 
            self.recent_table.setItem(r, 0, QTableWidgetItem(format_date_for_display(date)))
            self.recent_table.setItem(r, 1, QTableWidgetItem(t.title()))
            self.recent_table.setItem(r, 2, QTableWidgetItem((cat or "").title()))
            self.recent_table.setItem(r, 3, QTableWidgetItem(f"{amt:.2f}"))
            self.recent_table.setItem(r, 4, QTableWidgetItem(note)) 
            edit_btn = QPushButton(" ✏️")
            del_btn = QPushButton(" 🗑️")
            edit_btn.setFixedSize(BUTTON_WIDTH,BUTTON_HEIGHT-10); del_btn.setFixedSize(BUTTON_WIDTH,BUTTON_HEIGHT-10)
            edit_btn.clicked.connect(lambda _, _rid=rid: self._edit_from_preview(_rid))
            del_btn.clicked.connect(lambda _, _rid=rid: self._delete_from_preview(_rid))
            w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0,0,0,0); h.addWidget(edit_btn); h.addWidget(del_btn); h.addStretch()
            self.recent_table.setCellWidget(r, 5, w) 

    def _edit_from_preview(self, rid):
        dlg = TransactionEditDialog(rid, "transactions.db", self)
        if dlg.exec():
            self.load_recent_transactions()
            self.data_changed.emit()

    def _delete_from_preview(self, rid):
        settings = QSettings("Azralithia", "FinanceTracker") 
        confirm_delete = settings.value("confirm_delete", True, type=bool) 
        if confirm_delete: 
            reply = QMessageBox.question(self, 'Confirm Delete', "Are you sure you want to delete this transaction?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) 
            if reply == QMessageBox.StandardButton.No: 
                return 
        conn = sqlite3.connect("transactions.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions WHERE id=?", (rid,))
        conn.commit()
        conn.close()
        self.load_recent_transactions()
        self.data_changed.emit()

    # -=- Helpers -=-
    def set_type(self, t: str):
        self.current_type = t
        self.income_btn.setChecked(t == "Income")
        self.expense_btn.setChecked(t == "Expense")
        self.update_type_styles()
        self.reload_categories()

    def update_type_styles(self):
        self.income_btn.setStyleSheet(
            "border: 2px solid green;" if self.current_type == "Income" else ""
        )
        self.expense_btn.setStyleSheet(
            "border: 2px solid red;" if self.current_type == "Expense" else ""
        )

    def reload_categories(self):
        self.category.clear()
        self.category.addItems(self.categories.get(self.current_type, []))

    def edit_categories(self):
        current = self.categories.get(self.current_type, [])
        dlg = CategoryEditor(current, self)
        if dlg.exec():
            updated = dlg.get_categories()
            cleaned = []
            seen = set()
            for name in (s.strip() for s in updated):
                if name and name not in seen:
                    seen.add(name)
                    cleaned.append(name)
            self.categories[self.current_type] = cleaned or ["Other"]
            self.reload_categories()
            self.save_categories()  

    def load_categories(self):
        stored = self.settings.value("categories", None)
        defaults = {
            "Income": ["Salary", "Gift", "Bonus", "Other"],
            "Expense": ["Food", "Rent", "Utilities", "Transport", "Misc"]
        }
        if not stored:
            self.categories = defaults
            return
        try:
            data = json.loads(stored)
            if not isinstance(data, dict):
                raise ValueError
            for key in ("Income", "Expense"):
                if key not in data or not isinstance(data[key], list) or not data[key]:
                    data[key] = defaults[key]
            self.categories = data
        except Exception:
            self.categories = defaults

    def save_categories(self):
        self.settings.setValue("categories", json.dumps(self.categories))

    def save_transaction(self):
        try:
            amount = float(self.amount.text())
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError as e:
            self.feedback.setText(f"❌ {e}")
            return

        tx = {
            "type": self.current_type.lower(),
            "amount": amount,
            "category": self.category.currentText().lower(),
            "date": self.date.date().toString("yyyy-MM-dd"),
            "note": self.notes.text().strip()
        }
        conn = sqlite3.connect("transactions.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transactions (type, amount, category, date, note)
            VALUES (?, ?, ?, ?, ?)
        """, (tx['type'], tx['amount'], tx['category'], tx['date'], tx['note']))
        conn.commit()
        conn.close()
        logging.getLogger().info(f"Transaction saved: {tx}")
        self.feedback.setText("✅ Transaction saved!")
        self.amount.clear()
        self.notes.clear()
        self.data_changed.emit()
        self.load_recent_transactions()
    
    def apply_theme(self, mode: str):
        if mode == "dark":
            self.setStyleSheet(DARK_MODE)
        else:
            self.setStyleSheet(LIGHT_MODE)
        pass


class CategoryEditor(QDialog):
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Categories")
        layout = QVBoxLayout(self)

        self.list = QListWidget()
        self.list.addItems(categories)
        layout.addWidget(self.list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("➕ Add")
        remove_btn = QPushButton("➖ Remove")
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        layout.addLayout(btn_row)

        save_btn = QPushButton("💾 Save")
        layout.addWidget(save_btn)

        add_btn.clicked.connect(self.add_category)
        remove_btn.clicked.connect(self.remove_category)
        save_btn.clicked.connect(self.accept)

    def add_category(self):
        text, ok = QInputDialog.getText(self, "New Category", "Enter name:")
        if ok:
            text = text.strip()
            if text:
                existing = {self.list.item(i).text() for i in range(self.list.count())}
                if text not in existing:
                    self.list.addItem(text)

    def remove_category(self):
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))

    def get_categories(self):
        return [self.list.item(i).text() for i in range(self.list.count())]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Azralithia Finance Tracker")
        self.setMinimumSize(1200, 700)
        self.setGeometry(200, 200, 900, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        self.sidebar = Sidebar()
        layout.addWidget(self.sidebar)
        layout.setContentsMargins(0, 0, 0, 0)   
        layout.setSpacing(0)

        # Pages
        self.stack = QStackedWidget()
        self.main_page = MainPage()
        self.settings_page = SettingsPage()
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.settings_page)
        layout.addWidget(self.stack)

        # Connect sidebar
        self.sidebar.action_triggered.connect(self.handle_action)
        self.sidebar.theme_toggled.connect(self.toggle_theme)

        self.settings = QSettings("Azralithia", "FinanceTracker")
        light = self.settings.value("light_mode", False, type=bool)

        # Sync toggle state with saved setting
        self.sidebar.theme_switch.setChecked(light)
        self.toggle_theme(light)
        
        self.transactions_page = TransactionsPage()
        self.stack.addWidget(self.transactions_page)
        self.show_summary_tab = SummaryPage(db_path="transactions.db")
        self.stack.addWidget(self.show_summary_tab)
        self.history_page = HistoryPage(db_path="transactions.db")
        self.stack.addWidget(self.history_page)

        self.transactions_page.data_changed.connect(self.on_data_changed)
        self.history_page.data_changed.connect(self.on_data_changed)
        self.transactions_page.data_changed.connect(self.history_page._load_category_filter)
        self.transactions_page.data_changed.connect(self.history_page.load_page)
    
    # Connect setting toggle to QSettings
        self.settings_page.save_filters_switch.toggled.connect(lambda v: self.settings.setValue("save_filters", bool(v)))
        self.settings_page.date_format_combo.currentTextChanged.connect(
            lambda v: (self.settings.setValue("date_format", v), self.on_date_format_changed())
        )
        self.settings_page.confirm_delete_switch.toggled.connect(lambda v: self.settings.setValue("confirm_delete", bool(v)))

    def closeEvent(self, event):
        save = self.settings.value("save_filters", False, type=bool)
        if save and hasattr(self, "history_page"):
            filters = {
                "type": self.history_page.type_filter.currentText(),
                "category": self.history_page.category_filter.currentText(),
                "start": self.history_page.start_date.date().toString("yyyy-MM-dd"),
                "end": self.history_page.end_date.date().toString("yyyy-MM-dd"),
                "note": self.history_page.note_search.text()
            }
            self.settings.setValue("history_filters", json.dumps(filters))
        super().closeEvent(event)

    def on_date_format_changed(self):
        settings = QSettings("Azralithia", "FinanceTracker")
        current_display_format = settings.value("date_format", "(YYYY-MM-DD) | Year-Month-Day")
        display_format = map_display_format(current_display_format)

        if hasattr(self, "history_page"):
            self.history_page.start_date.setDisplayFormat(display_format)
            self.history_page.end_date.setDisplayFormat(display_format)
            self.history_page.load_page()

        if hasattr(self, "transactions_page"):
            self.transactions_page.date.setDisplayFormat(display_format)
            self.transactions_page.load_recent_transactions() 
        
        if hasattr(self, "show_summary_tab"):
            self.show_summary_tab.start_picker.setDisplayFormat(display_format)
            self.show_summary_tab.end_picker.setDisplayFormat(display_format)
            self.show_summary_tab.refresh_summary()

    
    def on_data_changed(self):
        self.show_summary_tab.refresh_summary()
        self.history_page.load_page()  


    def handle_action(self, action_name: str):
        logger.info(f"Action triggered: {action_name}")
        if action_name == "Main":
            self.stack.setCurrentWidget(self.main_page)
        elif action_name == "Settings":
            self.stack.setCurrentWidget(self.settings_page)
        elif action_name == "Exit":
            self.close()
        elif action_name == "Manage Transactions":
            self.stack.setCurrentWidget(self.transactions_page)
        elif action_name == "Show Summary":
            self.stack.setCurrentWidget(self.show_summary_tab)
        elif action_name == "Transaction Log":
            self.stack.setCurrentWidget(self.history_page)

    def toggle_theme(self, light_mode: bool):
        self.settings.setValue("light_mode", bool(light_mode)) 
        theme_mode = "light" if light_mode else "dark"
        
        # Main Stylesheet
        if light_mode:
            self.apply_light_theme()
        else:
            self.apply_dark_theme()
        
        # Propagate theme to pages that support it
        if hasattr(self, 'show_summary_tab'):
            self.show_summary_tab.apply_theme(theme_mode)
        
        if hasattr(self, 'transactions_page'):
            self.transactions_page.apply_theme(theme_mode)

    def apply_dark_theme(self):
        self.setStyleSheet(DARK_MODE)
        self.sidebar.theme_switch._track_dark = True
        self.sidebar.theme_switch.update()

    def apply_light_theme(self):
        self.setStyleSheet(LIGHT_MODE)
        self.sidebar.theme_switch._track_dark = False
        self.sidebar.theme_switch.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  
    window = MainWindow()
    window.show()
    sys.exit(app.exec())