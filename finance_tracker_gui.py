import sys
import json
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from collections import defaultdict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QStackedWidget, QGraphicsOpacityEffect,
    QCheckBox, QLabel, QLineEdit, QComboBox, QDateEdit, 
    QListWidget, QInputDialog, QDialog, QScrollArea, QGroupBox,
    QFrame
)
from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve,
    pyqtSignal, pyqtProperty, QSettings, QRect, QDate
)

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

class ShowSummaryTab(QWidget):
    def __init__(self, db_path="transactions.db", parent=None):
        super().__init__(parent)
        self.db_path = db_path

        self._build_ui()
        # Default to current month
        self.month_picker.setDate(QDate.currentDate())
        self.refresh_summary()

    def set_db_path(self, db_path: str):
        self.db_path = db_path
        self.refresh_summary()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)

        # Header controls: Month/Year selector + Refresh
        header = QHBoxLayout()
        header.setSpacing(12)

        self.month_label = QLabel("📅 Month:")
        self.month_label.setObjectName("SummaryLabelSmall")

        self.month_picker = QDateEdit()
        self.month_picker.setCalendarPopup(True)
        self.month_picker.setDisplayFormat("MMMM yyyy")
        self.month_picker.setMinimumWidth(180)
        self.month_picker.dateChanged.connect(self.refresh_summary)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_summary)

        header.addWidget(self.month_label)
        header.addWidget(self.month_picker)
        header.addStretch()
        header.addWidget(self.refresh_btn)

        # Totals row
        totals = QHBoxLayout()
        totals.setSpacing(12)

        self.card_income = self._make_metric_card("Income", "0.00")
        self.card_expense = self._make_metric_card("Expense", "0.00")
        self.card_balance = self._make_metric_card("Balance", "0.00")

        totals.addWidget(self.card_income)
        totals.addWidget(self.card_expense)
        totals.addWidget(self.card_balance)

        # Breakdown sections inside a scroll area
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

    # --=-- Data / Queries --=--
    def _get_year_month(self):
        d = self.month_picker.date()
        return d.year(), d.month()

    def _connect(self):
        if not self.db_path:
            raise RuntimeError("ShowSummaryTab: db_path not set. Call set_db_path(path_to_sqlite).")
        return sqlite3.connect(self.db_path)

    def _fetch_totals_and_counts(self, year: int, month: int):
        totals = {'income': 0.0, 'expense': 0.0, 'balance': 0.0}
        counts_income = defaultdict(lambda: {'total': 0.0, 'count': 0})
        counts_expense = defaultdict(lambda: {'total': 0.0, 'count': 0})

        query_totals = """
            SELECT type, COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY type
        """
        query_counts = """
            SELECT type, category, COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
            FROM transactions
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY type, category
            ORDER BY total DESC
        """

        ym = (f"{year:04d}", f"{month:02d}")
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
            y, m = self._get_year_month()
            totals, c_in, c_ex = self._fetch_totals_and_counts(y, m)

            self.card_income._value_label.setText(f"{totals['income']:.2f}")
            self.card_expense._value_label.setText(f"{totals['expense']:.2f}")
            self.card_balance._value_label.setText(f"{totals['balance']:.2f}")

            self._render_breakdown(self.gb_income, c_in)
            self._render_breakdown(self.gb_expense, c_ex)

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

# Light/Dark mode toggle switch
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
        # On a white thumb, black text is always readable
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
        self.setProperty("subitem", is_subitem)  # Used by theme CSS to add left padding

        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(FADE_DURATION)

        if start_collapsed:
            self.setText(self.icon_only)
            self.opacity_effect.setOpacity(0)
        else:
            self.setText(self.full_text)
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

        self.theme_switch.setVisible(not collapsed)   # Show only when expanded

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
        label = QLabel("⚙️ Settings Page")
        label.setStyleSheet("font-size: 20px;")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)


class TransactionsPage(QWidget):
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
        self.edit_cat_btn = QPushButton("✏️")
        self.edit_cat_btn.setFixedWidth(40)
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
            # Basic cleanup: strip blanks, remove duplicates 
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
        self.show_summary_tab = ShowSummaryTab(db_path="transactions.db")
        self.stack.addWidget(self.show_summary_tab)


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

    def toggle_theme(self, light_mode: bool):
        self.settings.setValue("light_mode", bool(light_mode)) 
        theme_mode = "light" if light_mode else "dark"
        
        # Apply main stylesheet
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