import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="brand_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Products Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                category TEXT,
                cost_price REAL,
                selling_price REAL,
                stock INTEGER
            )
        """)
        
        # Categories Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)
        
        # Sales Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                product_name TEXT,
                quantity INTEGER,
                total_amount REAL,
                profit REAL,
                date TIMESTAMP
            )
        """)

        # Expenses Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                category TEXT,
                amount REAL,
                date TIMESTAMP,
                notes TEXT
            )
        """)
        # Ensure 'notes' column exists for older DBs
        self.cursor.execute("PRAGMA table_info(expenses)")
        cols = [row[1] for row in self.cursor.fetchall()]
        if 'notes' not in cols:
            try:
                self.cursor.execute("ALTER TABLE expenses ADD COLUMN notes TEXT")
            except Exception:
                pass
        self.conn.commit()

    # --- PRODUCT METHODS ---
    def add_product(self, name, category, cost, price, stock):
        self.cursor.execute("INSERT INTO products (name, category, cost_price, selling_price, stock) VALUES (?, ?, ?, ?, ?)",
                            (name, category, cost, price, stock))
        self.conn.commit()

    def get_all_products(self):
        self.cursor.execute("SELECT * FROM products")
        return self.cursor.fetchall()

    def add_category(self, category_name):
        try:
            self.cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
            self.conn.commit()
            return True
        except Exception:
            return False

    def get_all_categories(self):
        self.cursor.execute("SELECT name FROM categories ORDER BY name ASC")
        return [row[0] for row in self.cursor.fetchall()]

    def update_stock(self, product_id, new_stock):
        self.cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
        self.conn.commit()

    # --- SALES METHODS ---
    def add_sale(self, product_id, product_name, qty, total, profit):
        self.cursor.execute("INSERT INTO sales (product_id, product_name, quantity, total_amount, profit, date) VALUES (?, ?, ?, ?, ?, ?)",
                            (product_id, product_name, qty, total, profit, datetime.now()))
        self.conn.commit()

    def get_total_sales(self):
        self.cursor.execute("SELECT SUM(total_amount) FROM sales")
        result = self.cursor.fetchone()[0]
        return result if result else 0.0

    def get_total_profit(self):
        self.cursor.execute("SELECT SUM(profit) FROM sales")
        result = self.cursor.fetchone()[0]
        return result if result else 0.0
    
    def get_daily_sales_data(self):
        # Returns date and total sales for that date (for graphs)
        self.cursor.execute("SELECT date(date), SUM(total_amount) FROM sales GROUP BY date(date) LIMIT 7")
        return self.cursor.fetchall()

    def get_all_sales(self, limit=0):
        # Returns sales ordered by date desc. If limit>0, limit the rows.
        if limit and isinstance(limit, int) and limit > 0:
            self.cursor.execute("SELECT id, product_id, product_name, quantity, total_amount, profit, date FROM sales ORDER BY date DESC LIMIT ?", (limit,))
        else:
            self.cursor.execute("SELECT id, product_id, product_name, quantity, total_amount, profit, date FROM sales ORDER BY date DESC")
        return self.cursor.fetchall()

    def get_sales_sum_between(self, start_date, end_date):
        # start_date and end_date should be strings in 'YYYY-MM-DD' or date/datetime objects
        self.cursor.execute("SELECT SUM(total_amount) FROM sales WHERE date(date) BETWEEN date(?) AND date(?)", (str(start_date), str(end_date)))
        result = self.cursor.fetchone()[0]
        return result if result else 0.0

    def get_expenses_sum_between(self, start_date, end_date):
        self.cursor.execute("SELECT SUM(amount) FROM expenses WHERE date(date) BETWEEN date(?) AND date(?)", (str(start_date), str(end_date)))
        result = self.cursor.fetchone()[0]
        return result if result else 0.0

    def get_sales_between(self, start_date, end_date):
        """Return detailed sales rows between dates ordered by date desc.
        Each row: (id, product_id, product_name, quantity, total_amount, profit, date)
        """
        self.cursor.execute("SELECT id, product_id, product_name, quantity, total_amount, profit, date FROM sales WHERE date(date) BETWEEN date(?) AND date(?) ORDER BY date DESC", (str(start_date), str(end_date)))
        return self.cursor.fetchall()

    def get_expenses_between(self, start_date, end_date):
        """Return detailed expense rows between dates ordered by date desc.
        Each row: (id, date, title, category, amount, notes)
        """
        self.cursor.execute("SELECT id, date, title, category, amount, notes FROM expenses WHERE date(date) BETWEEN date(?) AND date(?) ORDER BY date DESC", (str(start_date), str(end_date)))
        return self.cursor.fetchall()

    # --- EXPENSE METHODS ---
    def add_expense(self, title, category, amount, date=None, notes=None):
        if date is None:
            date = datetime.now()
        self.cursor.execute("INSERT INTO expenses (title, category, amount, date, notes) VALUES (?, ?, ?, ?, ?)",
                            (title, category, amount, date, notes))
        self.conn.commit()

    def get_all_expenses(self, limit=0):
        # Returns expenses ordered by date desc. If limit>0, limit the rows.
        if limit and isinstance(limit, int) and limit > 0:
            self.cursor.execute("SELECT id, date, title, category, amount, notes FROM expenses ORDER BY date(date) DESC LIMIT ?", (limit,))
        else:
            self.cursor.execute("SELECT id, date, title, category, amount, notes FROM expenses ORDER BY date(date) DESC")
        return self.cursor.fetchall()

    def get_total_expenses(self):
        self.cursor.execute("SELECT SUM(amount) FROM expenses")
        result = self.cursor.fetchone()[0]
        return result if result else 0.0

    def clear_all_data(self):
        """Delete all rows from products, sales, expenses, and categories.
        Resets autoincrement counters where possible and compacts the database.
        """
        try:
            # Delete data from tables
            self.cursor.execute("DELETE FROM products")
            self.cursor.execute("DELETE FROM sales")
            self.cursor.execute("DELETE FROM expenses")
            self.cursor.execute("DELETE FROM categories")
            self.conn.commit()

            # Reset sqlite_sequence entries so AUTOINCREMENT restarts at 1
            try:
                self.cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('products','sales','expenses','categories')")
                self.conn.commit()
            except Exception:
                # Some SQLite setups may not allow direct manipulation; ignore safely
                pass

            # Run VACUUM to reclaim space
            try:
                self.cursor.execute("VACUUM")
            except Exception:
                pass

            return True
        except Exception:
            return False