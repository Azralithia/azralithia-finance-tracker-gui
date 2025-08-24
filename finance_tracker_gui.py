import sys
import logging
import json
from logging.handlers import RotatingFileHandler
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QStackedWidget, QGraphicsOpacityEffect,
    QCheckBox, QLabel, QLineEdit, QComboBox, QDateEdit, 
    QListWidget, QInputDialog, QDialog
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

        title = QLabel("📝 Manage Transactions      ")
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
            "notes": self.notes.text().strip()
        }
        logging.getLogger().info(f"Transaction saved: {tx}")
        self.feedback.setText("✅ Transaction saved!")
        self.amount.clear()
        self.notes.clear()


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

    def toggle_theme(self, light_mode: bool):
        self.settings.setValue("light_mode", bool(light_mode)) 

        if light_mode:
            self.apply_light_theme()
        else:
            self.apply_dark_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
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
        """)
        self.sidebar.theme_switch._track_dark = True
        self.sidebar.theme_switch.update()

    def apply_light_theme(self):
        self.setStyleSheet("""
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
        """)
        self.sidebar.theme_switch._track_dark = False
        self.sidebar.theme_switch.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  
    window = MainWindow()
    window.show()
    sys.exit(app.exec())