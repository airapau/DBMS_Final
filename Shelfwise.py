import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QFormLayout, QDialog,
    QHeaderView, QCheckBox, QFrame, QSpacerItem, QSizePolicy, QSpinBox,
    QComboBox, QDoubleSpinBox, QDateEdit, QInputDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QBrush
import datetime
import os

# Color constants
BURGUNDY = "#7D3750"
LIGHT_BURGUNDY = "#9D5975"
LIGHTER_BURGUNDY = "#B37990"
WHITE = "#FFFFFF"
VERY_LIGHT_BURGUNDY = "#D4A5B5"
GRAY = "#E0E0E0"
GREEN = "#4CAF50"
RED = "#F44336"
DARK_TEXT = "#333333"
LOGOUT_COLOR = "#7D3750"  # Dark purple for logout buttons

# Use absolute path to ensure database is saved in a consistent location
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shelfwise.db")

# Initialize DB and tables
# Replace the problematic part in the init_db() function with this code:

def init_db():
    # Ensure the database directory exists
    db_dir = os.path.dirname(DB_NAME)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    # Check if database exists before trying to recreate tables
    db_exists = os.path.exists(DB_NAME)
    
    # Only initialize tables if database doesn't exist
    if not db_exists:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Create the Users table
        c.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName TEXT,
            LastName TEXT,
            Username TEXT UNIQUE NOT NULL,
            Password TEXT NOT NULL,
            Email TEXT,
            DateJoined DATE,
            is_admin INTEGER NOT NULL DEFAULT 0
        )''')
        
        # Create the Collections table
        c.execute('''
        CREATE TABLE IF NOT EXISTS Collections (
            CollectionID INTEGER PRIMARY KEY AUTOINCREMENT,
            CollectionName TEXT UNIQUE NOT NULL,
            Description TEXT
        )''')
        
        # Create the Items table
        c.execute('''
        CREATE TABLE IF NOT EXISTS Items (
            ItemID INTEGER PRIMARY KEY AUTOINCREMENT,
            CollectionID INTEGER,
            ItemName TEXT NOT NULL,
            Description TEXT,
            Price REAL NOT NULL DEFAULT 0.0,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (CollectionID) REFERENCES Collections(CollectionID)
        )''')
        
        # Create the Users_Items table with quantity field
        c.execute('''
        CREATE TABLE IF NOT EXISTS Users_Items (
            UI_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER,
            ItemID INTEGER,
            DateAdded DATE,
            Quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (UserID) REFERENCES Users(UserID),
            FOREIGN KEY (ItemID) REFERENCES Items(ItemID),
            UNIQUE (UserID, ItemID)
        )''')
        
        # Insert admin user if not exists
        today = datetime.date.today().isoformat()
        c.execute("INSERT INTO Users (Username, Password, is_admin, DateJoined) VALUES (?, ?, ?, ?)", 
                ('admin', 'admin', 1, today))
        
        # Insert default collections
        c.execute("INSERT INTO Collections (CollectionName, Description) VALUES (?, ?)", 
                ('Books', 'Book collection'))
        c.execute("INSERT INTO Collections (CollectionName, Description) VALUES (?, ?)", 
                ('Toys', 'Toy collection'))
        
        conn.commit()
        conn.close()
    else:
        # If database exists, check if Quantity column exists in Users_Items
        # But we'll use a try-except to handle the case where it might already exist
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Let's first check if the Users_Items table exists at all
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users_Items'")
        if c.fetchone():
            # Try to add the Quantity column, but catch the error if it already exists
            try:
                c.execute("ALTER TABLE Users_Items ADD COLUMN Quantity INTEGER NOT NULL DEFAULT 1")
                conn.commit()
            except sqlite3.OperationalError as e:
                # If error is about duplicate column, just ignore it
                if "duplicate column name" in str(e):
                    pass
                else:
                    # If it's another type of error, re-raise it
                    raise
            
        conn.close()
    
class AddEditUserDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add User" if user_data is None else "Edit User")
        self.user_data = user_data
        self.setup_ui()
        if user_data:
            self.load_data(user_data)

    def setup_ui(self):
        self.layout = QFormLayout(self)
        self.first_name_edit = QLineEdit()
        self.last_name_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.email_edit = QLineEdit()
        self.date_joined = QDateEdit()
        self.date_joined.setDate(QDate.currentDate())
        self.is_admin_checkbox = QCheckBox("Make Admin")

        self.layout.addRow("First Name:", self.first_name_edit)
        self.layout.addRow("Last Name:", self.last_name_edit)
        self.layout.addRow("Username:", self.username_edit)
        self.layout.addRow("Password:", self.password_edit)
        self.layout.addRow("Email:", self.email_edit)
        self.layout.addRow("Date Joined:", self.date_joined)
        self.layout.addRow("", self.is_admin_checkbox)

        self.buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.save_btn)
        self.buttons_layout.addWidget(self.cancel_btn)
        self.layout.addRow(self.buttons_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def load_data(self, user_data):
        user_id, first_name, last_name, username, password, email, date_joined, is_admin = user_data
        self.first_name_edit.setText(first_name or "")
        self.last_name_edit.setText(last_name or "")
        self.username_edit.setText(username)
        self.password_edit.setText(password)
        self.email_edit.setText(email or "")
        if date_joined:
            self.date_joined.setDate(QDate.fromString(date_joined, "yyyy-MM-dd"))
        self.is_admin_checkbox.setChecked(bool(is_admin))

    def get_data(self):
        first_name = self.first_name_edit.text().strip()
        last_name = self.last_name_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        email = self.email_edit.text().strip()
        date_joined = self.date_joined.date().toString("yyyy-MM-dd")
        is_admin = 1 if self.is_admin_checkbox.isChecked() else 0
        return first_name, last_name, username, password, email, date_joined, is_admin

class AddCollectionDialog(QDialog):
    def __init__(self, parent=None, collection_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add Collection" if collection_data is None else "Edit Collection")
        self.collection_data = collection_data
        self.setup_ui()
        if collection_data:
            self.load_data(collection_data)

    def setup_ui(self):
        self.layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.desc_edit = QLineEdit()
        
        self.layout.addRow("Name:", self.name_edit)
        self.layout.addRow("Description:", self.desc_edit)

        self.buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.save_btn)
        self.buttons_layout.addWidget(self.cancel_btn)
        self.layout.addRow(self.buttons_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def load_data(self, collection_data):
        collection_id, name, desc = collection_data
        self.name_edit.setText(name)
        self.desc_edit.setText(desc if desc else "")

    def get_data(self):
        name = self.name_edit.text().strip()
        desc = self.desc_edit.text().strip()
        return name, desc

class AddItemDialog(QDialog):
    def __init__(self, parent=None, item_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add Item" if item_data is None else "Edit Item")
        self.item_data = item_data
        self.conn = sqlite3.connect(DB_NAME)
        self.setup_ui()
        if item_data:
            self.load_data(item_data)

    def setup_ui(self):
        self.layout = QFormLayout(self)
        
        self.collection_combo = QComboBox()
        self.load_collections()
        
        self.name_edit = QLineEdit()
        self.desc_edit = QLineEdit()
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMinimum(0.0)
        self.price_spin.setMaximum(999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("₱")
        
        self.stock_spin = QSpinBox()
        self.stock_spin.setMinimum(0)
        self.stock_spin.setMaximum(999999)
        
        self.layout.addRow("Collection:", self.collection_combo)
        self.layout.addRow("Name:", self.name_edit)
        self.layout.addRow("Description:", self.desc_edit)
        self.layout.addRow("Price:", self.price_spin)
        self.layout.addRow("Stock Quantity:", self.stock_spin)

        self.buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.save_btn)
        self.buttons_layout.addWidget(self.cancel_btn)
        self.layout.addRow(self.buttons_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def load_collections(self):
        c = self.conn.cursor()
        c.execute("SELECT CollectionID, CollectionName FROM Collections ORDER BY CollectionName")
        collections = c.fetchall()
        for col_id, col_name in collections:
            self.collection_combo.addItem(col_name, col_id)

    def load_data(self, item_data):
        item_id, collection_id, name, desc, price, stock = item_data
        
        # Set collection
        for i in range(self.collection_combo.count()):
            if self.collection_combo.itemData(i) == collection_id:
                self.collection_combo.setCurrentIndex(i)
                break
        
        self.name_edit.setText(name)
        self.desc_edit.setText(desc if desc else "")
        self.price_spin.setValue(price)
        self.stock_spin.setValue(stock)

    def get_data(self):
        collection_id = self.collection_combo.currentData()
        name = self.name_edit.text().strip()
        desc = self.desc_edit.text().strip()
        price = self.price_spin.value()
        stock = self.stock_spin.value()
        return collection_id, name, desc, price, stock
    
    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)

class EditUserItemDialog(QDialog):
    def __init__(self, parent=None, user_item_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit User Item")
        self.user_item_data = user_item_data
        self.setup_ui()
        if user_item_data:
            self.load_data(user_item_data)

    def setup_ui(self):
        self.layout = QFormLayout(self)
        
        # Quantity field
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(999)
        
        self.layout.addRow("Quantity:", self.quantity_spin)

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.buttons_layout.addWidget(self.save_btn)
        self.buttons_layout.addWidget(self.cancel_btn)
        self.layout.addRow(self.buttons_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def load_data(self, user_item_data):
        ui_id, user_id, item_id, date_added, quantity = user_item_data
        self.quantity_spin.setValue(quantity)

    def get_data(self):
        quantity = self.quantity_spin.value()
        return quantity
    
class AdminTab(QWidget):
    def __init__(self, logout_callback):
        super().__init__()
        self.conn = sqlite3.connect(DB_NAME)
        self.logout_callback = logout_callback
        self.setup_ui()
        self.load_users()
        self.load_collections()
        self.load_items()
        self.load_user_items()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Account tab for user management
        self.account_tab = QWidget()
        self.account_layout = QVBoxLayout(self.account_tab)

        # User table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(8)
        self.user_table.setHorizontalHeaderLabels(["ID", "First Name", "Last Name", "Username", "Email", "Date Joined", "Is Admin", "Password"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setSelectionBehavior(self.user_table.SelectRows)
        self.account_layout.addWidget(self.user_table)

        # User buttons
        user_btn_layout = QHBoxLayout()
        self.add_user_btn = QPushButton("Add User")
        self.edit_user_btn = QPushButton("Edit User")
        self.delete_user_btn = QPushButton("Delete User")
        self.logout_btn_users = QPushButton("Logout")
        self.logout_btn_users.setObjectName("logoutButton")
        user_btn_layout.addWidget(self.add_user_btn)
        user_btn_layout.addWidget(self.edit_user_btn)
        user_btn_layout.addWidget(self.delete_user_btn)
        user_btn_layout.addWidget(self.logout_btn_users)
        self.account_layout.addLayout(user_btn_layout)

        self.tabs.addTab(self.account_tab, "Users")
        
        # Collections tab
        self.collections_tab = QWidget()
        self.collections_layout = QVBoxLayout(self.collections_tab)
        
        # Collections table
        self.collections_table = QTableWidget()
        self.collections_table.setColumnCount(3)
        self.collections_table.setHorizontalHeaderLabels(["ID", "Name", "Description"])
        self.collections_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.collections_table.setSelectionBehavior(self.collections_table.SelectRows)
        self.collections_layout.addWidget(self.collections_table)
        
        # Collections buttons
        collections_btn_layout = QHBoxLayout()
        self.add_collection_btn = QPushButton("Add Collection")
        self.edit_collection_btn = QPushButton("Edit Collection")
        self.delete_collection_btn = QPushButton("Delete Collection")
        self.logout_btn_collections = QPushButton("Logout")
        self.logout_btn_collections.setObjectName("logoutButton")
        collections_btn_layout.addWidget(self.add_collection_btn)
        collections_btn_layout.addWidget(self.edit_collection_btn)
        collections_btn_layout.addWidget(self.delete_collection_btn)
        collections_btn_layout.addWidget(self.logout_btn_collections)
        self.collections_layout.addLayout(collections_btn_layout)
        
        self.tabs.addTab(self.collections_tab, "Collections")

        # Items tab
        self.items_tab = QWidget()
        self.items_layout = QVBoxLayout(self.items_tab)

        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["ID", "Collection", "Name", "Description", "Price", "Stock"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setSelectionBehavior(self.items_table.SelectRows)
        self.items_layout.addWidget(self.items_table)

        # Items buttons
        items_btn_layout = QHBoxLayout()
        self.add_item_btn = QPushButton("Add Item")
        self.edit_item_btn = QPushButton("Edit Item")
        self.delete_item_btn = QPushButton("Delete Item")
        self.logout_btn_items = QPushButton("Logout")
        self.logout_btn_items.setObjectName("logoutButton")
        items_btn_layout.addWidget(self.add_item_btn)
        items_btn_layout.addWidget(self.edit_item_btn)
        items_btn_layout.addWidget(self.delete_item_btn)
        items_btn_layout.addWidget(self.logout_btn_items)
        self.items_layout.addLayout(items_btn_layout)

        self.tabs.addTab(self.items_tab, "Items")
        
        # User Items tab (modified)
        self.user_items_tab = QWidget()
        self.user_items_layout = QVBoxLayout(self.user_items_tab)
        
        # User selection for filtering
        user_filter_layout = QHBoxLayout()
        user_filter_label = QLabel("Select User:")
        self.user_filter_combo = QComboBox()
        self.user_filter_combo.addItem("All Users", None)
        user_filter_layout.addWidget(user_filter_label)
        user_filter_layout.addWidget(self.user_filter_combo)
        user_filter_layout.addStretch()
        self.user_items_layout.addLayout(user_filter_layout)

        # User Items table
        self.user_items_table = QTableWidget()
        self.user_items_table.setColumnCount(7)  # Added column for quantity
        self.user_items_table.setHorizontalHeaderLabels(["ID", "User", "Item Name", "Collection", "Date Added", "Item Price", "Quantity"])
        self.user_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_items_layout.addWidget(self.user_items_table)
        
        # User Items buttons
        user_items_btn_layout = QHBoxLayout()
        self.edit_user_item_btn = QPushButton("Edit Item Quantity")
        self.logout_btn_user_items = QPushButton("Logout")
        self.logout_btn_user_items.setObjectName("logoutButton")
        user_items_btn_layout.addWidget(self.edit_user_item_btn)
        user_items_btn_layout.addWidget(self.logout_btn_user_items)
        self.user_items_layout.addLayout(user_items_btn_layout)
        
        self.tabs.addTab(self.user_items_tab, "User Items")

        # Connect buttons
        self.add_user_btn.clicked.connect(self.add_user)
        self.edit_user_btn.clicked.connect(self.edit_user)
        self.delete_user_btn.clicked.connect(self.delete_user)
        
        self.add_collection_btn.clicked.connect(self.add_collection)
        self.edit_collection_btn.clicked.connect(self.edit_collection)
        self.delete_collection_btn.clicked.connect(self.delete_collection)

        self.add_item_btn.clicked.connect(self.add_item)
        self.edit_item_btn.clicked.connect(self.edit_item)
        self.delete_item_btn.clicked.connect(self.delete_item)
        
        self.edit_user_item_btn.clicked.connect(self.edit_user_item)
        self.user_filter_combo.currentIndexChanged.connect(self.load_user_items)
        
        # Connect all logout buttons
        self.logout_btn_users.clicked.connect(self.logout_callback)
        self.logout_btn_collections.clicked.connect(self.logout_callback)
        self.logout_btn_items.clicked.connect(self.logout_callback)
        self.logout_btn_user_items.clicked.connect(self.logout_callback)

    def load_users(self):
        c = self.conn.cursor()
        try:
            c.execute("SELECT UserID, FirstName, LastName, Username, Email, DateJoined, is_admin, Password FROM Users WHERE Username <> 'admin'")
            rows = c.fetchall()
            self.user_table.setRowCount(len(rows))
            
            # Clear and repopulate user filter combo
            self.user_filter_combo.clear()
            self.user_filter_combo.addItem("All Users", None)
            
            for i, row in enumerate(rows):
                user_id, first_name, last_name, username, email, date_joined, is_admin, password = row
                self.user_table.setItem(i, 0, QTableWidgetItem(str(user_id)))
                self.user_table.setItem(i, 1, QTableWidgetItem(first_name or ""))
                self.user_table.setItem(i, 2, QTableWidgetItem(last_name or ""))
                self.user_table.setItem(i, 3, QTableWidgetItem(username))
                self.user_table.setItem(i, 4, QTableWidgetItem(email or ""))
                self.user_table.setItem(i, 5, QTableWidgetItem(date_joined or ""))
                self.user_table.setItem(i, 6, QTableWidgetItem("Yes" if is_admin else "No"))
                self.user_table.setItem(i, 7, QTableWidgetItem(password))
                
                # Add to user filter combo
                display_name = f"{username} ({first_name} {last_name})".strip()
                if display_name.endswith("()"):
                    display_name = display_name[:-3]
                self.user_filter_combo.addItem(display_name, user_id)
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load users: {str(e)}")
    
    def load_collections(self):
        c = self.conn.cursor()
        try:
            c.execute("SELECT CollectionID, CollectionName, Description FROM Collections")
            rows = c.fetchall()
            self.collections_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                col_id, name, desc = row
                self.collections_table.setItem(i, 0, QTableWidgetItem(str(col_id)))
                self.collections_table.setItem(i, 1, QTableWidgetItem(name))
                self.collections_table.setItem(i, 2, QTableWidgetItem(desc if desc else ""))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load collections: {str(e)}")

    def load_items(self):
        c = self.conn.cursor()
        try:
            c.execute("""SELECT Items.ItemID, Collections.CollectionName, Items.ItemName, Items.Description, 
                        Items.Price, Items.stock_quantity 
                        FROM Items 
                        JOIN Collections ON Items.CollectionID = Collections.CollectionID""")
            rows = c.fetchall()
            self.items_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                id_, collection, name, desc, price, stock = row
                self.items_table.setItem(i, 0, QTableWidgetItem(str(id_)))
                self.items_table.setItem(i, 1, QTableWidgetItem(collection))
                self.items_table.setItem(i, 2, QTableWidgetItem(name))
                self.items_table.setItem(i, 3, QTableWidgetItem(desc if desc else ""))
                self.items_table.setItem(i, 4, QTableWidgetItem(f"${price:.2f}"))
                self.items_table.setItem(i, 5, QTableWidgetItem(str(stock)))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load items: {str(e)}")
    
    def load_user_items(self):
        c = self.conn.cursor()
        selected_user_id = self.user_filter_combo.currentData()
        
        try:
            if selected_user_id is None:
                # Show all user items
                c.execute("""
                    SELECT ui.UI_ID, u.Username, i.ItemName, c.CollectionName, ui.DateAdded, i.Price, ui.Quantity
                    FROM Users_Items ui
                    JOIN Users u ON ui.UserID = u.UserID
                    JOIN Items i ON ui.ItemID = i.ItemID
                    JOIN Collections c ON i.CollectionID = c.CollectionID
                    ORDER BY u.Username, i.ItemName
                """)
            else:
                # Show items for specific user
                c.execute("""
                    SELECT ui.UI_ID, u.Username, i.ItemName, c.CollectionName, ui.DateAdded, i.Price, ui.Quantity
                    FROM Users_Items ui
                    JOIN Users u ON ui.UserID = u.UserID
                    JOIN Items i ON ui.ItemID = i.ItemID
                    JOIN Collections c ON i.CollectionID = c.CollectionID
                    WHERE ui.UserID = ?
                    ORDER BY i.ItemName
                """, (selected_user_id,))
            
            rows = c.fetchall()
            self.user_items_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                ui_id, username, item_name, collection_name, date_added, price, quantity = row
                self.user_items_table.setItem(i, 0, QTableWidgetItem(str(ui_id)))
                self.user_items_table.setItem(i, 1, QTableWidgetItem(username))
                self.user_items_table.setItem(i, 2, QTableWidgetItem(item_name))
                self.user_items_table.setItem(i, 3, QTableWidgetItem(collection_name))
                self.user_items_table.setItem(i, 4, QTableWidgetItem(date_added or ""))
                self.user_items_table.setItem(i, 5, QTableWidgetItem(f"${price:.2f}"))
                self.user_items_table.setItem(i, 6, QTableWidgetItem(str(quantity)))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load user items: {str(e)}")

    def add_user(self):
        dlg = AddEditUserDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            first_name, last_name, username, password, email, date_joined, is_admin = dlg.get_data()
            if not username or not password:
                QMessageBox.warning(self, "Error", "Username and password cannot be empty.")
                return
            try:
                c = self.conn.cursor()
                c.execute("""INSERT INTO Users 
                          (FirstName, LastName, Username, Password, Email, DateJoined, is_admin) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)""",
                          (first_name, last_name, username, password, email, date_joined, is_admin))
                
                self.conn.commit()
                self.load_users()
                QMessageBox.information(self, "Success", "User added successfully!")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Error", "Username already exists.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add user: {str(e)}")

    def edit_user(self):
        selected_rows = self.user_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Select a user first.")
            return
        row = selected_rows[0].row()
        user_id = int(self.user_table.item(row, 0).text())
        
        try:
            c = self.conn.cursor()
            c.execute("SELECT UserID, FirstName, LastName, Username, Password, Email, DateJoined, is_admin FROM Users WHERE UserID=?", (user_id,))
            user_data = c.fetchone()
            
            dlg = AddEditUserDialog(self, user_data)
            if dlg.exec_() == QDialog.Accepted:
                first_name, last_name, username, password, email, date_joined, is_admin = dlg.get_data()
                if not username or not password:
                    QMessageBox.warning(self, "Error", "Username and password cannot be empty.")
                    return
                try:
                    c = self.conn.cursor()
                    c.execute("""UPDATE Users SET 
                            FirstName=?, LastName=?, Username=?, Password=?, 
                            Email=?, DateJoined=?, is_admin=? WHERE UserID=?""",
                            (first_name, last_name, username, password, email, date_joined, is_admin, user_id))
                    self.conn.commit()
                    self.load_users()
                    QMessageBox.information(self, "Success", "User updated successfully!")
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "Error", "Username already exists.")
                except sqlite3.Error as e:
                    QMessageBox.critical(self, "Database Error", f"Failed to update user: {str(e)}")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load user data: {str(e)}")

    def delete_user(self):
        selected_rows = self.user_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Select a user first.")
            return
        row = selected_rows[0].row()
        user_id = int(self.user_table.item(row, 0).text())
        confirm = QMessageBox.question(self, "Confirm Delete",
                                       f"Delete user id {user_id}?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                c = self.conn.cursor()
                
                # Delete user's items
                c.execute("DELETE FROM Users_Items WHERE UserID=?", (user_id,))
                
                # Finally delete the user
                c.execute("DELETE FROM Users WHERE UserID=?", (user_id,))
                
                self.conn.commit()
                self.load_users()
                self.load_user_items()
                QMessageBox.information(self, "Success", "User deleted successfully!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete user: {str(e)}")
    
    def add_collection(self):
        dlg = AddCollectionDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            name, desc = dlg.get_data()
            if not name:
                QMessageBox.warning(self, "Error", "Collection name cannot be empty.")
                return
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO Collections (CollectionName, Description) VALUES (?, ?)", 
                          (name, desc))
                self.conn.commit()
                self.load_collections()
                QMessageBox.information(self, "Success", "Collection added successfully!")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Error", "Collection name already exists.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add collection: {str(e)}")
    
    def edit_collection(self):
        selected_rows = self.collections_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Select a collection first.")
            return
        row = selected_rows[0].row()
        collection_id = int(self.collections_table.item(row, 0).text())
        name = self.collections_table.item(row, 1).text()
        desc = self.collections_table.item(row, 2).text()
        
        dlg = AddCollectionDialog(self, (collection_id, name, desc))
        if dlg.exec_() == QDialog.Accepted:
            new_name, new_desc = dlg.get_data()
            if not new_name:
                QMessageBox.warning(self, "Error", "Collection name cannot be empty.")
                return
            try:
                c = self.conn.cursor()
                c.execute("UPDATE Collections SET CollectionName=?, Description=? WHERE CollectionID=?",
                          (new_name, new_desc, collection_id))
                self.conn.commit()
                self.load_collections()
                self.load_items()
                QMessageBox.information(self, "Success", "Collection updated successfully!")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Error", "Collection name already exists.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to update collection: {str(e)}")
    
    def delete_collection(self):
        selected_rows = self.collections_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Select a collection first.")
            return
        row = selected_rows[0].row()
        collection_id = int(self.collections_table.item(row, 0).text())
        
        try:
            # Check if collection has items
            c = self.conn.cursor()
            c.execute("SELECT COUNT(*) FROM Items WHERE CollectionID=?", (collection_id,))
            item_count = c.fetchone()[0]
            
            if item_count > 0:
                QMessageBox.warning(self, "Error", 
                                f"This collection has {item_count} items. Delete all items first.")
                return
                
            confirm = QMessageBox.question(self, "Confirm Delete",
                                        f"Delete collection id {collection_id}?",
                                        QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                c = self.conn.cursor()
                c.execute("DELETE FROM Collections WHERE CollectionID=?", (collection_id,))
                self.conn.commit()
                self.load_collections()
                QMessageBox.information(self, "Success", "Collection deleted successfully!")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete collection: {str(e)}")

    def add_item(self):
        dlg = AddItemDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            collection_id, name, desc, price, stock = dlg.get_data()
            if not name:
                QMessageBox.warning(self, "Error", "Name cannot be empty.")
                return
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO Items (CollectionID, ItemName, Description, Price, stock_quantity) VALUES (?, ?, ?, ?, ?)", 
                        (collection_id, name, desc, price, stock))
                self.conn.commit()
                self.load_items()
                QMessageBox.information(self, "Success", "Item added successfully!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add item: {str(e)}")

    def edit_item(self):
        selected_rows = self.items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Select an item first.")
            return
        row = selected_rows[0].row()
        item_id = int(self.items_table.item(row, 0).text())
        
        try:
            c = self.conn.cursor()
            c.execute("SELECT ItemID, CollectionID, ItemName, Description, Price, stock_quantity FROM Items WHERE ItemID=?", (item_id,))
            item_data = c.fetchone()
            
            dlg = AddItemDialog(self, item_data)
            if dlg.exec_() == QDialog.Accepted:
                collection_id, name, desc, price, stock = dlg.get_data()
                if not name:
                    QMessageBox.warning(self, "Error", "Name cannot be empty.")
                    return
                c = self.conn.cursor()
                c.execute("UPDATE Items SET CollectionID=?, ItemName=?, Description=?, Price=?, stock_quantity=? WHERE ItemID=?",
                        (collection_id, name, desc, price, stock, item_id))
                self.conn.commit()
                self.load_items()
                self.load_user_items()
                QMessageBox.information(self, "Success", "Item updated successfully!")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update item: {str(e)}")

    def delete_item(self):
        selected_rows = self.items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Select an item first.")
            return
        row = selected_rows[0].row()
        item_id = int(self.items_table.item(row, 0).text())
        confirm = QMessageBox.question(self, "Confirm Delete",
                                      f"Delete item id {item_id}?",
                                      QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                c = self.conn.cursor()
                c.execute("DELETE FROM Users_Items WHERE ItemID=?", (item_id,))
                c.execute("DELETE FROM Items WHERE ItemID=?", (item_id,))
                self.conn.commit()
                self.load_items()
                self.load_user_items()
                QMessageBox.information(self, "Success", "Item deleted successfully!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete item: {str(e)}")
                
    def edit_user_item(self):
        selected_rows = self.user_items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Select a user item first.")
            return
        row = selected_rows[0].row()
        ui_id = int(self.user_items_table.item(row, 0).text())
        
        try:
            c = self.conn.cursor()
            c.execute("SELECT UI_ID, UserID, ItemID, DateAdded, Quantity FROM Users_Items WHERE UI_ID=?", (ui_id,))
            user_item_data = c.fetchone()
            
            dlg = EditUserItemDialog(self, user_item_data)
            if dlg.exec_() == QDialog.Accepted:
                quantity = dlg.get_data()
                c = self.conn.cursor()
                c.execute("UPDATE Users_Items SET Quantity=? WHERE UI_ID=?", (quantity, ui_id))
                self.conn.commit()
                self.load_user_items()
                QMessageBox.information(self, "Success", "User item quantity updated successfully!")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update user item: {str(e)}")
    
    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)
            
class UserTab(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.conn = sqlite3.connect(DB_NAME)
        self.setup_ui()
        self.load_collections()
        self.load_items()
        self.load_my_items()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tabs for different sections
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Shop tab
        self.shop_tab = QWidget()
        self.setup_shop_tab()
        self.tabs.addTab(self.shop_tab, "Shop")
        
        # My Items tab
        self.my_items_tab = QWidget()
        self.setup_my_items_tab()
        self.tabs.addTab(self.my_items_tab, "My Items")
        
        # Logout button
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setObjectName("logoutButton")
        layout.addWidget(self.logout_btn)

    def setup_shop_tab(self):
        layout = QVBoxLayout(self.shop_tab)
        
        # Collection filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Collection:")
        self.collection_filter = QComboBox()
        self.collection_filter.addItem("All Collections", None)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.collection_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        label = QLabel("Browse Items")
        label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(label)

        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["ID", "Collection", "Name", "Price", "Stock", "Actions"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setSelectionBehavior(self.items_table.SelectRows)
        layout.addWidget(self.items_table)

        # Connect signals
        self.collection_filter.currentIndexChanged.connect(self.load_items)
    
    def setup_my_items_tab(self):
        layout = QVBoxLayout(self.my_items_tab)
        
        label = QLabel("My Items")
        label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(label)
        
        self.my_items_table = QTableWidget()
        self.my_items_table.setColumnCount(6)  # Added quantity column
        self.my_items_table.setHorizontalHeaderLabels(["ID", "Item Name", "Collection", "Price", "Date Added", "Quantity"])
        self.my_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.my_items_table)

    def load_collections(self):
        c = self.conn.cursor()
        try:
            c.execute("SELECT CollectionID, CollectionName FROM Collections ORDER BY CollectionName")
            collections = c.fetchall()
            
            # Clear and repopulate collection filter
            self.collection_filter.clear()
            self.collection_filter.addItem("All Collections", None)
            for col_id, col_name in collections:
                self.collection_filter.addItem(col_name, col_id)
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load collections: {str(e)}")

    def load_items(self):
        c = self.conn.cursor()
        collection_id = self.collection_filter.currentData()
        
        try:
            if collection_id is None:
                query = """SELECT Items.ItemID, Collections.CollectionName, Items.ItemName, Items.Price, Items.stock_quantity 
                          FROM Items 
                          JOIN Collections ON Items.CollectionID = Collections.CollectionID
                          WHERE Items.stock_quantity > 0"""
                c.execute(query)
            else:
                query = """SELECT Items.ItemID, Collections.CollectionName, Items.ItemName, Items.Price, Items.stock_quantity 
                          FROM Items 
                          JOIN Collections ON Items.CollectionID = Collections.CollectionID
                          WHERE Items.CollectionID = ? AND Items.stock_quantity > 0"""
                c.execute(query, (collection_id,))
            
            rows = c.fetchall()
            self.items_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                id_, collection, name, price, stock = row
                self.items_table.setItem(i, 0, QTableWidgetItem(str(id_)))
                self.items_table.setItem(i, 1, QTableWidgetItem(collection))
                self.items_table.setItem(i, 2, QTableWidgetItem(name))
                self.items_table.setItem(i, 3, QTableWidgetItem(f"${price:.2f}"))
                self.items_table.setItem(i, 4, QTableWidgetItem(str(stock)))
                
                # Add actions container 
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                add_to_myitems_btn = QPushButton("Add to My Items")
                add_to_myitems_btn.clicked.connect(lambda checked, item_id=id_: self.add_to_my_items(item_id))
                actions_layout.addWidget(add_to_myitems_btn)
                
                self.items_table.setCellWidget(i, 5, actions_widget)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load items: {str(e)}")
    
    def load_my_items(self):
        c = self.conn.cursor()
        try:
            # Get user's items
            c.execute("""
                SELECT ui.UI_ID, i.ItemName, c.CollectionName, i.Price, ui.DateAdded, ui.Quantity
                FROM Users_Items ui
                JOIN Items i ON ui.ItemID = i.ItemID
                JOIN Collections c ON i.CollectionID = c.CollectionID
                WHERE ui.UserID = ?
            """, (self.user_id,))
            
            rows = c.fetchall()
            self.my_items_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                ui_id, item_name, collection_name, price, date_added, quantity = row
                self.my_items_table.setItem(i, 0, QTableWidgetItem(str(ui_id)))
                self.my_items_table.setItem(i, 1, QTableWidgetItem(item_name))
                self.my_items_table.setItem(i, 2, QTableWidgetItem(collection_name))
                self.my_items_table.setItem(i, 3, QTableWidgetItem(f"${price:.2f}"))
                self.my_items_table.setItem(i, 4, QTableWidgetItem(date_added or ""))
                self.my_items_table.setItem(i, 5, QTableWidgetItem(str(quantity)))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load my items: {str(e)}")

    def add_to_my_items(self, item_id):
        c = self.conn.cursor()
        try:
            # Check if item already added
            c.execute("SELECT UI_ID, Quantity FROM Users_Items WHERE UserID=? AND ItemID=?", 
                      (self.user_id, item_id))
            
            existing = c.fetchone()
            
            # Get the item details for display
            c.execute("SELECT ItemName, stock_quantity FROM Items WHERE ItemID=?", (item_id,))
            item_name, max_stock = c.fetchone()
            
            if existing:
                ui_id, current_quantity = existing
                # Ask if user wants to update quantity
                confirm = QMessageBox.question(
                    self, 
                    "Update Quantity", 
                    f"You already have {current_quantity} of this item. Do you want to update the quantity?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm == QMessageBox.Yes:
                    # Ask for new quantity
                    quantity, ok = QInputDialog.getInt(
                        self, "Enter Quantity", 
                        f"How many {item_name} do you want? (Max: {max_stock})",
                        value=current_quantity, min=1, max=max_stock
                    )
                    if ok:
                        c.execute("UPDATE Users_Items SET Quantity=? WHERE UI_ID=?", (quantity, ui_id))
                        self.conn.commit()
                        self.load_my_items()
                        QMessageBox.information(self, "Success", f"Updated to {quantity} items!")
            else:
                # Ask for quantity
                quantity, ok = QInputDialog.getInt(
                    self, "Enter Quantity", 
                    f"How many {item_name} do you want? (Max: {max_stock})",
                    value=1, min=1, max=max_stock
                )
                
                if ok:
                    # Add to my items with quantity
                    today = datetime.date.today().isoformat()
                    c.execute("INSERT INTO Users_Items (UserID, ItemID, DateAdded, Quantity) VALUES (?, ?, ?, ?)",
                            (self.user_id, item_id, today, quantity))
                    
                    self.conn.commit()
                    self.load_my_items()
                    QMessageBox.information(self, "Success", f"Added {quantity} items to your collection!")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add to items: {str(e)}")
            
    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)
    
class LoginPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.conn = sqlite3.connect(DB_NAME)
        self.setup_ui()

    def setup_ui(self):
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Center container for content
        center_container = QWidget()
        center_container.setMaximumWidth(600)
        center_container.setMinimumWidth(500)
        
        layout = QVBoxLayout(center_container)
        layout.setSpacing(30)

        # Icon representation
        icon_widget = QWidget()
        icon_widget.setFixedHeight(120)
        icon_layout = QVBoxLayout(icon_widget)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        # Stylized icon using text representation
        icon_label = QLabel("📚")
        icon_label.setStyleSheet("font-size: 72px;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        layout.addWidget(icon_widget)

        # Title
        title = QLabel("Welcome to Shelfwise !")
        title.setFont(QFont("Arial", 36, QFont.Bold))
        title.setStyleSheet(f"""
            font-size: 36px; 
            font-weight: bold; 
            color: {WHITE};
            margin-top: 20px;
            margin-bottom: 50px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Select Role label
        role_label = QLabel("Select Role:")
        role_label.setStyleSheet(f"""
            font-size: 24px; 
            color: {WHITE};
            margin-bottom: 20px;
        """)
        role_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(role_label)

        # Buttons container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(40)
        buttons_layout.setAlignment(Qt.AlignCenter)

        # Admin button
        self.admin_btn = QPushButton("ADMIN")
        self.admin_btn.setFixedSize(200, 60)
        self.admin_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LIGHT_BURGUNDY};
                color: {WHITE};
                font-size: 20px;
                font-weight: bold;
                border-radius: 30px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BURGUNDY};
            }}
        """)
        
        # Collector button (using USER functionality)
        self.collector_btn = QPushButton("COLLECTOR")
        self.collector_btn.setFixedSize(200, 60)
        self.collector_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LIGHT_BURGUNDY};
                color: {WHITE};
                font-size: 20px;
                font-weight: bold;
                border-radius: 30px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BURGUNDY};
            }}
        """)

        buttons_layout.addWidget(self.admin_btn)
        buttons_layout.addWidget(self.collector_btn)
        layout.addWidget(buttons_container)

        main_layout.addWidget(center_container)

        # Connect buttons to show appropriate dialogs
        self.admin_btn.clicked.connect(self.show_admin_login)
        self.collector_btn.clicked.connect(self.show_user_login)

    def show_admin_login(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Admin Login")
        dialog.setFixedSize(400, 200)
        
        layout = QFormLayout(dialog)
        
        username_edit = QLineEdit()
        username_edit.setText("admin")
        username_edit.setReadOnly(True)
        
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Username:", username_edit)
        layout.addRow("Password:", password_edit)
        
        buttons_layout = QHBoxLayout()
        login_btn = QPushButton("Login")
        cancel_btn = QPushButton("Cancel")
        
        buttons_layout.addWidget(login_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addRow(buttons_layout)
        
        # Apply styling to dialog
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {VERY_LIGHT_BURGUNDY};
            }}
            QLineEdit {{
                background-color: {WHITE};
                border: 1px solid {LIGHT_BURGUNDY};
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {BURGUNDY};
                color: {WHITE};
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BURGUNDY};
            }}
        """)
        
        def do_admin_login():
            password = password_edit.text().strip()
            if password == "admin":
                dialog.accept()
                self.parent.login_success(admin=True)
            else:
                QMessageBox.warning(dialog, "Error", "Invalid admin password.")
        
        login_btn.clicked.connect(do_admin_login)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def show_user_login(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Collector Login / Signup")
        dialog.setFixedSize(450, 350)
        
        layout = QVBoxLayout(dialog)
        
        # Tabs for login/signup
        tabs = QTabWidget()
        
        # Login tab
        login_tab = QWidget()
        login_layout = QFormLayout(login_tab)
        
        login_username = QLineEdit()
        login_password = QLineEdit()
        login_password.setEchoMode(QLineEdit.Password)
        
        login_layout.addRow("Username:", login_username)
        login_layout.addRow("Password:", login_password)
        
        login_btn = QPushButton("Login")
        login_layout.addRow("", login_btn)
        
        tabs.addTab(login_tab, "Login")
        
        # Signup tab
        signup_tab = QWidget()
        signup_layout = QFormLayout(signup_tab)
        
        signup_first_name = QLineEdit()
        signup_last_name = QLineEdit()
        signup_username = QLineEdit()
        signup_password = QLineEdit()
        signup_password.setEchoMode(QLineEdit.Password)
        signup_email = QLineEdit()
        
        signup_layout.addRow("First Name:", signup_first_name)
        signup_layout.addRow("Last Name:", signup_last_name)
        signup_layout.addRow("Username:", signup_username)
        signup_layout.addRow("Password:", signup_password)
        signup_layout.addRow("Email:", signup_email)
        
        signup_btn = QPushButton("Signup")
        signup_layout.addRow("", signup_btn)
        
        tabs.addTab(signup_tab, "Signup")
        
        layout.addWidget(tabs)
        
        # Close button
        close_btn = QPushButton("Close")
        layout.addWidget(close_btn)
        
        # Apply styling to dialog
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {VERY_LIGHT_BURGUNDY};
            }}
            QLineEdit {{
                background-color: {WHITE};
                border: 1px solid {LIGHT_BURGUNDY};
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {BURGUNDY};
                color: {WHITE};
                border-radius: 3px;
                padding: 5px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BURGUNDY};
            }}
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            QTabBar::tab {{
                background: {LIGHTER_BURGUNDY};
                color: {WHITE};
                padding: 8px 16px;
                margin: 2px;
            }}
            QTabBar::tab:selected {{
                background: {BURGUNDY};
                font-weight: bold;
            }}
        """)
        
        def do_user_login():
            username = login_username.text().strip()
            password = login_password.text().strip()
            if not username or not password:
                QMessageBox.warning(dialog, "Error", "Please enter username and password.")
                return
            try:
                c = self.conn.cursor()
                c.execute("SELECT UserID FROM Users WHERE Username=? AND Password=? AND is_admin=0", (username, password))
                row = c.fetchone()
                if row:
                    user_id = row[0]
                    dialog.accept()
                    self.parent.login_success(user_id=user_id)
                else:
                    QMessageBox.warning(dialog, "Error", "Invalid user credentials.")
            except sqlite3.Error as e:
                QMessageBox.critical(dialog, "Database Error", f"Login failed: {str(e)}")
        
        def do_user_signup():
            first_name = signup_first_name.text().strip()
            last_name = signup_last_name.text().strip()
            username = signup_username.text().strip()
            password = signup_password.text().strip()
            email = signup_email.text().strip()
            
            if not username or not password:
                QMessageBox.warning(dialog, "Error", "Username and password cannot be empty.")
                return
                
            today = datetime.date.today().isoformat()
            
            try:
                c = self.conn.cursor()
                c.execute("""INSERT INTO Users 
                           (FirstName, LastName, Username, Password, Email, DateJoined, is_admin) 
                           VALUES (?, ?, ?, ?, ?, ?, 0)""", 
                          (first_name, last_name, username, password, email, today))
                
                self.conn.commit()
                QMessageBox.information(dialog, "Success", "User registered successfully! You may now login.")
                signup_first_name.clear()
                signup_last_name.clear()
                signup_username.clear()
                signup_password.clear()
                signup_email.clear()
                tabs.setCurrentWidget(login_tab)
            except sqlite3.IntegrityError:
                QMessageBox.warning(dialog, "Error", "Username already exists.")
            except sqlite3.Error as e:
                QMessageBox.critical(dialog, "Database Error", f"Registration failed: {str(e)}")
        
        login_btn.clicked.connect(do_user_login)
        signup_btn.clicked.connect(do_user_signup)
        close_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()
        
    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shelfwise")
        self.resize(1000, 800)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = LoginPage(self)
        self.stack.addWidget(self.login_page)

        self.admin_tab = AdminTab(logout_callback=self.logout)
        self.stack.addWidget(self.admin_tab)

        self.user_tab = None  # created dynamically for logged in user

    def apply_styles(self):
        # Apply the burgundy gradient background and updated styles using the color constants
        style = f"""
            QMainWindow {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {BURGUNDY}, stop: 0.5 {BURGUNDY}, stop: 1 {BURGUNDY});
            }}
            LoginPage {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {LIGHT_BURGUNDY}, stop: 0.5 {LIGHT_BURGUNDY}, stop: 1 {LIGHT_BURGUNDY});
            }}
            QWidget {{
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: {DARK_TEXT};
            }}
            AdminTab, UserTab {{
                background-color: {VERY_LIGHT_BURGUNDY};
            }}
            QPushButton {{
                background-color: {BURGUNDY};
                color: {WHITE};
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BURGUNDY};
            }}
            QPushButton#logoutButton {{
                background-color: {LOGOUT_COLOR};
                color: {WHITE};
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton#logoutButton:hover {{
                background-color:({LOGOUT_COLOR}, 10%);
            }}
            QLineEdit {{
                background-color: {WHITE};
                border: 1px solid {LIGHT_BURGUNDY};
                border-radius: 3px;
                padding: 5px;
                color: {DARK_TEXT};
            }}
            QTableWidget {{
                background-color: {WHITE};
                gridline-color: {LIGHTER_BURGUNDY};
                color: {DARK_TEXT};
            }}
            QHeaderView::section {{
                background-color: {LIGHT_BURGUNDY};
                color: {WHITE};
                padding: 4px;
                border: 1px solid {BURGUNDY};
            }}
            QTabWidget::pane {{
                border: 1px solid {LIGHT_BURGUNDY};
                background: {VERY_LIGHT_BURGUNDY};
            }}
            QTabBar::tab {{
                background: {LIGHTER_BURGUNDY};
                border: 1px solid {LIGHT_BURGUNDY};
                border-bottom-color: {VERY_LIGHT_BURGUNDY};
                padding: 5px;
                color: {WHITE};
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background: {BURGUNDY};
                border-bottom-color: {BURGUNDY};
                font-weight: bold;
            }}
            QDialog {{
                background-color: {VERY_LIGHT_BURGUNDY};
            }}
            QSpinBox, QDoubleSpinBox, QDateEdit {{
                background-color: {WHITE};
                border: 1px solid {LIGHT_BURGUNDY};
                border-radius: 3px;
                padding: 2px;
                color: {DARK_TEXT};
            }}
            QComboBox {{
                background-color: {WHITE};
                border: 1px solid {LIGHT_BURGUNDY};
                border-radius: 3px;
                padding: 3px;
                color: {DARK_TEXT};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {BURGUNDY};
                margin-right: 5px;
            }}
        """
        self.setStyleSheet(style)

    def login_success(self, admin=False, user_id=None):
        if admin:
            self.admin_tab.load_users()
            self.admin_tab.load_collections()
            self.admin_tab.load_items()
            self.admin_tab.load_user_items()
            self.stack.setCurrentWidget(self.admin_tab)
        else:
            if self.user_tab:
                # Remove old user tab to update for new user
                self.stack.removeWidget(self.user_tab)
                self.user_tab.deleteLater()
            self.user_tab = UserTab(user_id)
            self.stack.addWidget(self.user_tab)
            self.stack.setCurrentWidget(self.user_tab)
            # Connect the logout button
            self.user_tab.logout_btn.clicked.connect(self.logout)

    def logout(self):
        # Return to login page
        self.stack.setCurrentWidget(self.login_page)
        
# Main function
def main():
    # Create application directory if it doesn't exist
    app_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
        
    # Ensure the database is initialized
    init_db()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()