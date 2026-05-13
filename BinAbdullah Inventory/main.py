import customtkinter as ctk
from tkinter import ttk, messagebox, Menu
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import Database
from datetime import datetime
import csv
import os
from PIL import Image, ImageTk, ImageDraw
from io import BytesIO
import sys


def resource_path(*path_parts):
    """Get absolute path to resource, works for dev and PyInstaller onefile bundles."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base, *path_parts)


def user_db_path(filename='brand_data.db'):
    """Return a writable path for the application's database.
    Prefer %APPDATA%\Bin Abdullah IM on Windows, fallback to executable directory.
    """
    appdata = os.getenv('APPDATA')
    if appdata:
        appdir = os.path.join(appdata, 'Bin Abdullah IM')
        try:
            os.makedirs(appdir, exist_ok=True)
        except Exception:
            pass
        return os.path.join(appdir, filename)
    # fallback to exe dir or source dir
    base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base, filename)

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

class ClothingBrandApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Database Connection (store DB in a writable user location)
        db_file = user_db_path('brand_data.db')
        self.db = Database(db_name=db_file)

        # Window Setup
        self.title("Clothing Brand Manager - Ultimate Edition")
        self.geometry("1100x700")

        # Grid Layout (Sidebar + Main Area)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_pages()
        
        # Start at Dashboard
        self.show_frame("Dashboard")

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="BRAND MANAGER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation Buttons
        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=lambda: self.show_frame("Dashboard"))
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_products = ctk.CTkButton(self.sidebar_frame, text="Products & Inventory", command=lambda: self.show_frame("Products"))
        self.btn_products.grid(row=2, column=0, padx=20, pady=10)

        self.btn_sales = ctk.CTkButton(self.sidebar_frame, text="New Sale", command=lambda: self.show_frame("Sales"))
        self.btn_sales.grid(row=3, column=0, padx=20, pady=10)

        self.btn_expenses = ctk.CTkButton(self.sidebar_frame, text="Expenses", command=lambda: self.show_frame("Expenses"))
        self.btn_expenses.grid(row=4, column=0, padx=20, pady=10)
        
        self.btn_report = ctk.CTkButton(self.sidebar_frame, text="Business Report", command=lambda: self.show_frame("BusinessReport"))
        self.btn_report.grid(row=5, column=0, padx=20, pady=10)
        
        # Clear cache (delete all data) button
        self.btn_clear = ctk.CTkButton(self.sidebar_frame, text="Clear Cache", fg_color="#B22222", hover_color="#8B0000", command=self._confirm_clear_cache)
        self.btn_clear.grid(row=7, column=0, padx=20, pady=10)

    def create_pages(self):
        # Create a dictionary to hold frames
        self.frames = {}

        # Initialize all frames
        for F in (DashboardPage, ProductsPage, SalesPage, ExpensesPage, BusinessReportPage):
            page_name = F.__name__.replace("Page", "")
            frame = F(parent=self, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=1, sticky="nsew")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        # Refresh data when opening a page
        if hasattr(frame, "update_data"):
            frame.update_data()

    def _confirm_clear_cache(self):
        """Ask user for confirmation and clear all DB data if confirmed."""
        answer = messagebox.askyesno("Clear All Data", "This will PERMANENTLY delete ALL products, sales, expenses, and categories.\n\nAre you sure you want to continue?")
        if not answer:
            return

        ok = False
        try:
            ok = self.db.clear_all_data()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear data: {e}")
            return

        if ok:
            # Refresh all pages that implement update_data
            for f in self.frames.values():
                try:
                    if hasattr(f, 'update_data'):
                        f.update_data()
                except Exception:
                    pass
            messagebox.showinfo("Cleared", "All data cleared successfully.")
        else:
            messagebox.showerror("Failed", "Failed to clear database tables. See console for details.")

# --- PAGE 1: DASHBOARD ---
class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Title
        label = ctk.CTkLabel(self, text="Business Overview", font=("Arial", 24, "bold"))
        label.pack(pady=20, padx=20, anchor="w")

        # KPI Cards Frame
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=20)

        # 3 Cards
        self.card_sales = self.create_kpi_card("Total Sales", "$0", "green")
        self.card_profit = self.create_kpi_card("Net Profit", "$0", "blue")
        self.card_expense = self.create_kpi_card("Total Expenses", "$0", "red")

        # Graph Area
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def create_kpi_card(self, title, value, color_theme):
        colors = {"green": "#2CC985", "blue": "#3B8ED0", "red": "#E04F5F"}
        frame = ctk.CTkFrame(self.kpi_frame, width=250, height=100)
        frame.pack(side="left", padx=10, expand=True, fill="x")
        
        lbl_title = ctk.CTkLabel(frame, text=title, font=("Arial", 14))
        lbl_title.pack(pady=(10,0))
        
        lbl_val = ctk.CTkLabel(frame, text=value, font=("Arial", 28, "bold"), text_color=colors[color_theme])
        lbl_val.pack(pady=(0,10))
        return lbl_val

    def update_data(self):
        # Refresh numbers from DB
        sales = self.controller.db.get_total_sales()
        expenses = self.controller.db.get_total_expenses()
        profit = self.controller.db.get_total_profit() # Gross profit stored in sales

        # Update Labels
        self.card_sales.configure(text=f"${sales:,.2f}")
        self.card_profit.configure(text=f"${profit:,.2f}")
        self.card_expense.configure(text=f"${expenses:,.2f}")

        # Refresh Graph
        self.plot_graph()

    def plot_graph(self):
        # Clear old graph
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        # Get Data
        data = self.controller.db.get_daily_sales_data()
        dates = [x[0] for x in data]
        amounts = [x[1] for x in data]

        # Create Matplotlib Figure
        fig = plt.Figure(figsize=(5, 4), dpi=100, facecolor="#2b2b2b")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#2b2b2b")
        ax.plot(dates, amounts, marker='o', color='#3B8ED0', linewidth=2)
        ax.set_title("Sales Over Time", color="white", fontsize=30)
        ax.tick_params(axis='x', colors='white', labelsize=10)
        ax.tick_params(axis='y', colors='white', labelsize=10)
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

# --- PAGE 2: PRODUCTS ---
class ProductsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Layout
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Inputs
        ctk.CTkLabel(self.input_frame, text="Add New Product", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.entry_name = ctk.CTkEntry(self.input_frame, placeholder_text="Product Name")
        self.entry_name.pack(pady=5, padx=10)
        
        # Category field with embedded icons (+ and ▼ inside the field)
        cat_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        cat_frame.pack(pady=5, padx=10, fill="x")
        
        self.entry_cat = ctk.CTkEntry(cat_frame, placeholder_text="Category")
        self.entry_cat.pack(side="left", fill="x", expand=True)
        
        # Load embedded icons inside the category field (SVG or fallback)
        self._load_category_icons(cat_frame)

        self.entry_cost = ctk.CTkEntry(self.input_frame, placeholder_text="Cost Price")
        self.entry_cost.pack(pady=5, padx=10)
        
        self.entry_price = ctk.CTkEntry(self.input_frame, placeholder_text="Selling Price")
        self.entry_price.pack(pady=5, padx=10)
        
        self.entry_stock = ctk.CTkEntry(self.input_frame, placeholder_text="Stock Qty")
        self.entry_stock.pack(pady=5, padx=10)

        ctk.CTkButton(self.input_frame, text="Save Product", command=self.add_product).pack(pady=20, padx=10)

        # Table (Treeview)
        style = ttk.Style()
        style.theme_use("default")
        # Increase font size and row height for better readability
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=36, font=("Arial", 28))
        style.configure("Treeview.Heading", font=("Arial", 36, "bold"), foreground="black")
        style.map('Treeview', background=[('selected', '#1f538d')])

        # Add search entry above the tree (like Expenses page)
        self.product_search = ctk.CTkEntry(self.table_frame, width=360, placeholder_text="Search Products")
        self.product_search.pack(pady=(8,6), padx=10, anchor='ne')
        self.product_search.bind("<KeyRelease>", lambda e: self.filter_products())

        self.tree = ttk.Treeview(self.table_frame, columns=("ID", "Name", "Category", "Cost", "Price", "Stock"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Cost", text="Cost")
        self.tree.heading("Price", text="Price")
        self.tree.heading("Stock", text="Stock")
        # Increase column widths to match larger font and improve readability
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Name", width=220)
        self.tree.column("Category", width=140)
        self.tree.column("Cost", width=90)
        self.tree.column("Price", width=90)
        self.tree.column("Stock", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True)

    def add_product(self):
        try:
            name = self.entry_name.get()
            cat = self.entry_cat.get()
            cost = float(self.entry_cost.get())
            price = float(self.entry_price.get())
            stock = int(self.entry_stock.get())
            
            self.controller.db.add_product(name, cat, cost, price, stock)
            messagebox.showinfo("Success", "Product Added!")
            self.clear_inputs()
            self.update_data()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for price/stock")

    def clear_inputs(self):
        self.entry_name.delete(0, 'end')
        self.entry_cost.delete(0, 'end')
        self.entry_price.delete(0, 'end')
        self.entry_stock.delete(0, 'end')
        self.entry_cat.delete(0, 'end')

    def add_new_category(self):
        """Add a new category to the database from the entry field."""
        cat_name = self.entry_cat.get().strip()
        if not cat_name:
            messagebox.showwarning("Input Error", "Please enter a category name")
            return
        
        if self.controller.db.add_category(cat_name):
            messagebox.showinfo("Success", f"Category '{cat_name}' added!")
            self.entry_cat.delete(0, 'end')
        else:
            messagebox.showerror("Error", f"Category '{cat_name}' already exists or failed to add")

    def show_category_dropdown(self):
        """Show a dropdown menu with all saved categories."""
        categories = self.controller.db.get_all_categories()
        if not categories:
            messagebox.showinfo("No Categories", "No categories found. Add one first using the '+' button.")
            return
        
        # Create a Tkinter menu
        menu = Menu(self.input_frame, tearoff=False)
        for cat in categories:
            menu.add_command(label=cat, command=lambda c=cat: self._select_category(c))
        
        # Show menu at the dropdown icon position if available
        try:
            if hasattr(self, 'cat_drop_label'):
                x = self.cat_drop_label.winfo_rootx()
                y = self.cat_drop_label.winfo_rooty() + self.cat_drop_label.winfo_height()
                menu.post(x, y)
            else:
                menu.post(self.input_frame.winfo_rootx(), self.input_frame.winfo_rooty())
        except Exception:
            menu.post(self.input_frame.winfo_rootx(), self.input_frame.winfo_rooty())

    def _select_category(self, selected):
        """Callback when a category is selected from dropdown."""
        self.entry_cat.delete(0, 'end')
        self.entry_cat.insert(0, selected)

    def _load_category_icons(self, cat_frame):
        """Load SVG icons (or draw fallbacks) and place them visually inside the category entry area."""
        # try to rasterize SVGs using cairosvg, fallback to drawing
        add_path = resource_path('assets', 'add_icon.svg')
        drop_path = resource_path('assets', 'drop_down_icon.svg')

        def load_svg(path, fallback_draw):
            try:
                import cairosvg
                png_bytes = cairosvg.svg2png(url=path)
                img = Image.open(BytesIO(png_bytes)).convert('RGBA')
            except Exception:
                # fallback: draw a simple icon
                img = Image.new('RGBA', (20, 20), (0,0,0,0))
                draw = ImageDraw.Draw(img)
                fallback_draw(draw)
            return img

        add_img = load_svg(add_path, lambda d: (d.line((10,2,10,18), fill='white', width=2), d.line((2,10,18,10), fill='white', width=2)))
        drop_img = load_svg(drop_path, lambda d: d.polygon([(6,8),(14,12),(6,16)], fill='white'))

        # Resize to fit nicely
        add_img = add_img.resize((20,20), Image.LANCZOS)
        drop_img = drop_img.resize((20,20), Image.LANCZOS)

        # Use CTkImage for crisp scaling on high-DPI displays
        try:
            self._add_icon_ctk = ctk.CTkImage(light_image=add_img, size=(20,20))
            self._drop_icon_ctk = ctk.CTkImage(light_image=drop_img, size=(20,20))
        except Exception:
            # fallback to PIL PhotoImage
            self._add_icon_photo = ImageTk.PhotoImage(add_img)
            self._drop_icon_photo = ImageTk.PhotoImage(drop_img)

        # Create labels with image and place them inside the cat_frame using absolute positioning
        # Position: right side of the entry field
        # Add icon
        try:
            # Prefer CTkImage when available
            img_arg = getattr(self, '_add_icon_ctk', getattr(self, '_add_icon_photo', None))
            img_arg2 = getattr(self, '_drop_icon_ctk', getattr(self, '_drop_icon_photo', None))
            self.cat_add_label = ctk.CTkLabel(cat_frame, image=img_arg, text='')
            self.cat_add_label.place(relx=1.0, x=-44, rely=0.5, anchor='e')
            self.cat_add_label.bind('<Button-1>', lambda e: self.add_new_category())

            # Dropdown icon
            self.cat_drop_label = ctk.CTkLabel(cat_frame, image=img_arg2, text='')
            self.cat_drop_label.place(relx=1.0, x=-16, rely=0.5, anchor='e')
            self.cat_drop_label.bind('<Button-1>', lambda e: self.show_category_dropdown())
        except Exception:
            # If CTkLabel binding doesn't work, use tkinter Label
            import tkinter as tk
            # Ensure PIL PhotoImage exists for tk fallback
            img_p1 = getattr(self, '_add_icon_photo', None)
            img_p2 = getattr(self, '_drop_icon_photo', None)
            if img_p1 is None:
                img_p1 = ImageTk.PhotoImage(add_img)
                self._add_icon_photo = img_p1
            if img_p2 is None:
                img_p2 = ImageTk.PhotoImage(drop_img)
                self._drop_icon_photo = img_p2
            self.cat_add_label = tk.Label(cat_frame, image=img_p1, bd=0)
            self.cat_add_label.image = img_p1
            self.cat_add_label.place(relx=1.0, x=-44, rely=0.5, anchor='e')
            self.cat_add_label.bind('<Button-1>', lambda e: self.add_new_category())

            self.cat_drop_label = tk.Label(cat_frame, image=img_p2, bd=0)
            self.cat_drop_label.image = img_p2
            self.cat_drop_label.place(relx=1.0, x=-16, rely=0.5, anchor='e')
            self.cat_drop_label.bind('<Button-1>', lambda e: self.show_category_dropdown())

    def update_data(self):
        # Clear Table
        # Load New Data into cache and apply filter
        products = self.controller.db.get_all_products()
        # store as tuples that match columns
        self._products_cache = products
        self.filter_products()

    def filter_products(self):
        q = self.product_search.get().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in getattr(self, '_products_cache', []):
            # p = (id, name, category, cost_price, selling_price, stock)
            row_text = ' '.join([str(p[1]), str(p[2])]).lower()
            if not q or q in row_text:
                self.tree.insert("", "end", values=p)

# --- PAGE 3: SALES ---
class SalesPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # Layout: top label, left POS controls, right sales history
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 8))
        ctk.CTkLabel(header, text="Point of Sale", font=("Arial", 24, "bold")).pack(side="left")

        body = ctk.CTkFrame(self)
        body.pack(fill="both", expand=True, padx=20, pady=10)

        # Left: POS controls
        pos_frame = ctk.CTkFrame(body)
        pos_frame.pack(side="left", fill="y", padx=(0,10))

        ctk.CTkLabel(pos_frame, text="Select Product", font=("Arial", 14, "bold")).pack(pady=(6,4))
        self.product_map = {}  # Maps "Name" -> ID, Price, Cost, Stock
        self.product_var = ctk.StringVar(value="Select Product")
        self.product_menu = ctk.CTkOptionMenu(pos_frame, variable=self.product_var)
        self.product_menu.pack(pady=6)

        ctk.CTkLabel(pos_frame, text="Quantity", font=("Arial", 14)).pack(pady=(8,4))
        self.entry_qty = ctk.CTkEntry(pos_frame, placeholder_text="Quantity")
        self.entry_qty.pack(pady=4)

        ctk.CTkButton(pos_frame, text="Confirm Sale", command=self.make_sale, fg_color="green", width=140).pack(pady=12)

        # Right: Sales history
        history_frame = ctk.CTkFrame(body)
        history_frame.pack(side="right", fill="both", expand=True)

        # Treeview style for sales
        style = ttk.Style()
        style.theme_use("default")
        # Larger readable table in Sales history
        style.configure("Treeview", rowheight=36, font=("Arial", 16))
        style.configure("Treeview.Heading", font=("Arial", 16, "bold"), foreground="black")

        self.sales_tree = ttk.Treeview(history_frame, columns=("Product", "Qty", "Total", "Profit", "Date"), show="headings")
        self.sales_tree.heading("Product", text="Product")
        self.sales_tree.heading("Qty", text="Quantity")
        self.sales_tree.heading("Total", text="Total")
        self.sales_tree.heading("Profit", text="Profit")
        self.sales_tree.heading("Date", text="Date / Time")

        self.sales_tree.column("Product", width=260)
        self.sales_tree.column("Qty", width=80)
        self.sales_tree.column("Total", width=110)
        self.sales_tree.column("Profit", width=110)
        self.sales_tree.column("Date", width=200)

        self.sales_tree.pack(fill="both", expand=True)

        # cache for sales entries (optional)
        self._sales_cache = []

    def update_data(self):
        # Refresh product dropdown
        products = self.controller.db.get_all_products()
        self.product_map = {}
        names = []
        for p in products:
            # p = (id, name, cat, cost, price, stock)
            if p[5] > 0:  # Only show in stock items
                name = f"{p[1]} (${p[4]})"
                names.append(name)
                self.product_map[name] = {"id": p[0], "name": p[1], "cost": p[3], "price": p[4], "stock": p[5]}

        if names:
            self.product_menu.configure(values=names)
            self.product_var.set(names[0])
        else:
            self.product_menu.configure(values=["No Stock Available"])

        # Refresh sales history table
        for i in self.sales_tree.get_children():
            self.sales_tree.delete(i)
        sales = self.controller.db.get_all_sales()
        self._sales_cache = []
        for s in sales:
            # s = (id, product_id, product_name, quantity, total_amount, profit, date)
            sid, pid, pname, qty, total, profit, date_val = s
            try:
                dt = datetime.fromisoformat(date_val) if isinstance(date_val, str) else date_val
            except Exception:
                dt = date_val
            date_str = dt.strftime('%d %b %Y %H:%M') if hasattr(dt, 'strftime') else str(date_val)
            row = (pname, qty, f"{total:,.2f}", f"{profit:,.2f}", date_str)
            self._sales_cache.append(row)
            self.sales_tree.insert("", "end", values=row)

    def make_sale(self):
        selected_text = self.product_var.get()
        if selected_text not in self.product_map:
            return

        try:
            qty = int(self.entry_qty.get())
            prod_data = self.product_map[selected_text]

            if qty > prod_data["stock"]:
                messagebox.showerror("Error", "Not enough stock!")
                return

            # Calc Financials
            total_sale = prod_data["price"] * qty
            total_profit = (prod_data["price"] - prod_data["cost"]) * qty
            new_stock = prod_data["stock"] - qty

            # DB Operations
            self.controller.db.add_sale(prod_data["id"], prod_data["name"], qty, total_sale, total_profit)
            self.controller.db.update_stock(prod_data["id"], new_stock)

            messagebox.showinfo("Success", f"Sold! Profit: ${total_profit}")
            self.entry_qty.delete(0, 'end')
            self.update_data() # Refresh dropdown stock

        except ValueError:
            messagebox.showerror("Error", "Invalid Quantity")

# --- PAGE 4: EXPENSES ---
class ExpensesPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Top bar with title, search, filter and add button
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        lbl = ctk.CTkLabel(top_frame, text="Expenses", font=("Arial", 28, "bold"))
        lbl.pack(side="left")

        right_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        right_frame.pack(side="right")

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(right_frame, width=360, placeholder_text="Search")
        self.search_entry.pack(side="left", padx=(0,10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_table())

        # Table + Inline form layout: left = input form, right = table
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(side="right", fill="both", expand=True, padx=20, pady=10)

        style = ttk.Style()
        style.theme_use("default")
        # Configure readable fonts and row height for Expenses
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=38, font=("Arial", 22))
        style.configure("Treeview.Heading", font=("Arial", 24, "bold"), foreground="black")
        style.map('Treeview', background=[('selected', '#1f538d')])

        # Add the tree to the right table frame
        self.tree = ttk.Treeview(self.table_frame, columns=("Date", "Name", "Category", "Amount", "Notes"), show="headings")
        self.tree.heading("Date", text="DATE")
        self.tree.heading("Name", text="NAME")
        self.tree.heading("Category", text="CATEGORY")
        self.tree.heading("Amount", text="AMOUNT")
        self.tree.heading("Notes", text="NOTES")

        self.tree.column("Date", width=220)
        self.tree.column("Name", width=300)
        self.tree.column("Category", width=180)
        self.tree.column("Amount", width=120)
        self.tree.column("Notes", width=300)

        self.tree.pack(fill="both", expand=True)

        # Inputs on the left (inline add form)
        ctk.CTkLabel(self.input_frame, text="Add New Expense", font=("Arial", 16, "bold")).pack(pady=10)

        ctk.CTkLabel(self.input_frame, text="Date", anchor="w").pack(pady=(6,0), padx=8, fill='x')
        self.entry_date_exp = ctk.CTkEntry(self.input_frame)
        self.entry_date_exp.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.entry_date_exp.pack(pady=4, padx=8, fill='x')

        ctk.CTkLabel(self.input_frame, text="Name", anchor="w").pack(pady=(6,0), padx=8, fill='x')
        self.entry_title_exp = ctk.CTkEntry(self.input_frame, placeholder_text="Expense Title (e.g., Rent)")
        self.entry_title_exp.pack(pady=4, padx=8, fill='x')

        ctk.CTkLabel(self.input_frame, text="Category", anchor="w").pack(pady=(6,0), padx=8, fill='x')
        self.entry_cat_exp = ctk.CTkEntry(self.input_frame, placeholder_text="Category")
        self.entry_cat_exp.pack(pady=4, padx=8, fill='x')

        ctk.CTkLabel(self.input_frame, text="Amount", anchor="w").pack(pady=(6,0), padx=8, fill='x')
        self.entry_amount_exp = ctk.CTkEntry(self.input_frame, placeholder_text="Amount ($)")
        self.entry_amount_exp.pack(pady=4, padx=8, fill='x')

        ctk.CTkLabel(self.input_frame, text="Notes", anchor="w").pack(pady=(6,0), padx=8, fill='x')
        try:
            self.entry_notes_exp = ctk.CTkTextbox(self.input_frame, height=120)
            self.entry_notes_exp.pack(pady=4, padx=8, fill='both', expand=False)
        except Exception:
            import tkinter as tk
            self.entry_notes_exp = tk.Text(self.input_frame, height=6)
            self.entry_notes_exp.pack(pady=4, padx=8, fill='both', expand=False)

        ctk.CTkButton(self.input_frame, text="Record Expense", command=self.save_expense, fg_color="red").pack(pady=12, padx=8)

        # Keep a copy of the full dataset for filtering
        self._expenses_cache = []

    def update_data(self):
        # Fetch expenses from DB and populate table
        for i in self.tree.get_children():
            self.tree.delete(i)

        expenses = self.controller.db.get_all_expenses()
        # Normalize date and insert
        self._expenses_cache = []
        for row in expenses:
            # row = (id, date, title, category, amount, notes)
            eid, date_val, title, category, amount, notes = row
            # Format date nicely
            try:
                dt = datetime.fromisoformat(date_val) if isinstance(date_val, str) else date_val
            except Exception:
                dt = date_val
            date_str = dt.strftime('%d %B %Y') if hasattr(dt, 'strftime') else str(date_val)
            notes = notes or ""
            item = (date_str, title, category, f"{amount:,.2f}", notes)
            self._expenses_cache.append(item)
            self.tree.insert("", "end", values=item)

    def filter_table(self):
        q = self.search_entry.get().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for item in self._expenses_cache:
            if not q or q in " ".join([str(x).lower() for x in item]):
                self.tree.insert("", "end", values=item)

    def open_add_modal(self):
        # Old modal removed; inline form now used
        return

    def save_expense(self, modal=None):
        try:
            amt = float(self.entry_amount_exp.get())
            title = self.entry_title_exp.get()
            category = self.entry_cat_exp.get()
            # Get notes
            try:
                notes = self.entry_notes_exp.get("1.0", "end").strip()
            except Exception:
                notes = self.entry_notes_exp.get().strip()
            # Parse date (YYYY-MM-DD preferred)
            date_text = self.entry_date_exp.get().strip()
            try:
                parsed = datetime.fromisoformat(date_text)
            except Exception:
                parsed = datetime.now()

            self.controller.db.add_expense(title, category, amt, date=parsed, notes=notes)
            messagebox.showinfo("Saved", "Expense Recorded")
            self.clear_expense_inputs()
            self.update_data()
        except ValueError:
            messagebox.showerror("Error", "Invalid Amount")

    def clear_expense_inputs(self):
        try:
            self.entry_title_exp.delete(0, 'end')
            self.entry_cat_exp.delete(0, 'end')
            self.entry_amount_exp.delete(0, 'end')
            try:
                self.entry_notes_exp.delete('1.0', 'end')
            except Exception:
                pass
            self.entry_date_exp.delete(0, 'end')
            self.entry_date_exp.insert(0, datetime.now().strftime('%Y-%m-%d'))
        except Exception:
            pass
        

class BusinessReportPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20,10))
        ctk.CTkLabel(header, text="Business Report", font=("Arial", 24, "bold")).pack(side="left")

        # Form area
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=20, pady=10)

        # Report Type
        ctk.CTkLabel(form, text="Report Type", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        self.report_type = ctk.CTkEntry(form, placeholder_text="e.g., Weekly Sales")
        self.report_type.grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        # Date range
        ctk.CTkLabel(form, text="From", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        ctk.CTkLabel(form, text="To", font=("Arial", 12, "bold")).grid(row=1, column=2, sticky="w", pady=6)

        # Try to use tkcalendar.DateEntry if available (use larger font for readability)
        try:
            from tkcalendar import DateEntry
            # Increase font and width to make calendar and entry larger
            self.from_date = DateEntry(form, date_pattern='y-mm-dd', width=20, font=('Arial', 24))
            self.to_date = DateEntry(form, date_pattern='y-mm-dd', width=20, font=('Arial', 24))
            # Bind selection event to auto-generate report
            self.from_date.bind('<<DateEntrySelected>>', lambda e: self.generate_report())
            self.to_date.bind('<<DateEntrySelected>>', lambda e: self.generate_report())
        except Exception:
            # Fallback: use larger CTkEntry widgets and generate on focus out / Enter
            self.from_date = ctk.CTkEntry(form, placeholder_text='YYYY-MM-DD', font=('Arial', 20), width=160)
            self.to_date = ctk.CTkEntry(form, placeholder_text='YYYY-MM-DD', font=('Arial', 20), width=160)
            self.from_date.bind('<FocusOut>', lambda e: self.generate_report())
            self.to_date.bind('<FocusOut>', lambda e: self.generate_report())
            self.from_date.bind('<Return>', lambda e: self.generate_report())
            self.to_date.bind('<Return>', lambda e: self.generate_report())

        self.from_date.grid(row=1, column=1, sticky="w", padx=8, pady=6)
        self.to_date.grid(row=1, column=3, sticky="w", padx=8, pady=6)

        # Sales / Expenses / Profit fields (read-only)
        ctk.CTkLabel(form, text="Sales", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.sales_var = ctk.StringVar(value="$0.00")
        ctk.CTkLabel(form, textvariable=self.sales_var).grid(row=2, column=1, sticky="w", pady=6)

        ctk.CTkLabel(form, text="Expenses", font=("Arial", 12, "bold")).grid(row=2, column=2, sticky="w", pady=6)
        self.expenses_var = ctk.StringVar(value="$0.00")
        ctk.CTkLabel(form, textvariable=self.expenses_var).grid(row=2, column=3, sticky="w", pady=6)

        ctk.CTkLabel(form, text="Profit", font=("Arial", 12, "bold")).grid(row=3, column=0, sticky="w", pady=6)
        self.profit_var = ctk.StringVar(value="$0.00")
        ctk.CTkLabel(form, textvariable=self.profit_var).grid(row=3, column=1, sticky="w", pady=6)

        # Format selector and actions
        ctk.CTkLabel(form, text="Format", font=("Arial", 12, "bold")).grid(row=3, column=2, sticky="w", pady=6)
        self.format_var = ctk.StringVar(value="csv")
        self.format_menu = ctk.CTkOptionMenu(form, variable=self.format_var, values=["csv", "png", "pdf"])
        self.format_menu.grid(row=3, column=3, sticky="w", pady=6)

        # Buttons (Generate removed; generation is automatic when dates change)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(8,20))
        ctk.CTkButton(btn_frame, text="Export", fg_color="#6B46C1", command=self.export_report).pack(side="left")

        # Make grid expand for entries
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(3, weight=1)

        # Internal storage for last generated report
        self._last_report = None

    def _parse_date_value(self, widget):
        v = None
        try:
            # DateEntry has get_date
            if hasattr(widget, 'get_date'):
                d = widget.get_date()
                v = d.strftime('%Y-%m-%d')
            else:
                v = widget.get().strip()
        except Exception:
            try:
                v = widget.get().strip()
            except Exception:
                v = None
        return v

    def generate_report(self):
        start = self._parse_date_value(self.from_date)
        end = self._parse_date_value(self.to_date)
        if not start or not end:
            # Dates not ready yet — do not show an error when generating automatically.
            # Clear displayed values and return silently.
            self.sales_var.set("$0.00")
            self.expenses_var.set("$0.00")
            self.profit_var.set("$0.00")
            self._last_report = None
            return

        try:
            # Database expects date strings
            sales_sum = self.controller.db.get_sales_sum_between(start, end)
            expenses_sum = self.controller.db.get_expenses_sum_between(start, end)
            profit = sales_sum - expenses_sum

            self.sales_var.set(f"${sales_sum:,.2f}")
            self.expenses_var.set(f"${expenses_sum:,.2f}")
            self.profit_var.set(f"${profit:,.2f}")

            # Store last report data
            self._last_report = {
                'report_type': self.report_type.get(),
                'from': start,
                'to': end,
                'sales': sales_sum,
                'expenses': expenses_sum,
                'profit': profit
            }
            #messagebox.showinfo('Generated', 'Report calculated successfully')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to generate report: {e}')

    def _make_report_image(self, text_lines, out_path):
        # Create a matplotlib figure and render text lines, save as PNG
        fig = plt.figure(figsize=(8,6))
        fig.patch.set_facecolor('#2b2b2b')
        plt.axis('off')
        # white text
        plt.text(0.01, 0.95, 'Business Report', fontsize=20, weight='bold', color='white')
        y = 0.85
        for line in text_lines:
            plt.text(0.01, y, line, fontsize=14, color='white')
            y -= 0.08
        plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)

    def export_report(self):
        if not self._last_report:
            messagebox.showerror('No Report', 'Please generate the report before exporting')
            return

        fmt = self.format_var.get()
        now_tag = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"business_report_{now_tag}"

        # Prepare lines
        rpt = self._last_report
        lines = [f"Report Type: {rpt.get('report_type')}", f"From: {rpt.get('from')}", f"To: {rpt.get('to')}", f"Sales: ${rpt.get('sales'):,.2f}", f"Expenses: ${rpt.get('expenses'):,.2f}", f"Profit: ${rpt.get('profit'):,.2f}"]

        try:
            # Fetch detailed rows
            sales_rows = self.controller.db.get_sales_between(rpt.get('from'), rpt.get('to'))
            expenses_rows = self.controller.db.get_expenses_between(rpt.get('from'), rpt.get('to'))

            if fmt == 'csv':
                out = base_name + '.csv'
                with open(out, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # Summary
                    writer.writerow(['Report Type', 'From', 'To', 'Sales', 'Expenses', 'Profit'])
                    writer.writerow([rpt.get('report_type'), rpt.get('from'), rpt.get('to'), f"{rpt.get('sales'):.2f}", f"{rpt.get('expenses'):.2f}", f"{rpt.get('profit'):.2f}"])
                    writer.writerow([])
                    # Sales details
                    writer.writerow(['Sales Details'])
                    writer.writerow(['Product', 'Quantity', 'Total', 'Profit', 'Date'])
                    for s in sales_rows:
                        # s = (id, product_id, product_name, quantity, total_amount, profit, date)
                        _, _, product_name, quantity, total_amount, profit_val, date_val = s
                        # format date
                        try:
                            dt = datetime.fromisoformat(date_val) if isinstance(date_val, str) else date_val
                            date_str = dt.strftime('%Y-%m-%d %H:%M') if hasattr(dt, 'strftime') else str(date_val)
                        except Exception:
                            date_str = str(date_val)
                        writer.writerow([product_name, quantity, f"{total_amount:.2f}", f"{profit_val:.2f}", date_str])

                    writer.writerow([])
                    # Expenses details
                    writer.writerow(['Expenses Details'])
                    writer.writerow(['Date', 'Name', 'Category', 'Amount', 'Notes'])
                    for ex in expenses_rows:
                        # ex = (id, date, title, category, amount, notes)
                        _, date_val, title, category, amount_val, notes = ex
                        try:
                            dt = datetime.fromisoformat(date_val) if isinstance(date_val, str) else date_val
                            date_str = dt.strftime('%Y-%m-%d %H:%M') if hasattr(dt, 'strftime') else str(date_val)
                        except Exception:
                            date_str = str(date_val)
                        writer.writerow([date_str, title, category, f"{amount_val:.2f}", notes or ""])

                messagebox.showinfo('Exported', f'CSV exported to {os.path.abspath(out)}')

            elif fmt in ('png', 'pdf'):
                # Build lines for image: summary + headings + rows (truncate if too long)
                lines = [f"Report Type: {rpt.get('report_type')}", f"From: {rpt.get('from')}", f"To: {rpt.get('to')}", f"Sales: ${rpt.get('sales'):,.2f}", f"Expenses: ${rpt.get('expenses'):,.2f}", f"Profit: ${rpt.get('profit'):,.2f}", ""]
                lines.append('SALES DETAILS:')
                lines.append('Product | Qty | Total | Profit | Date')
                for s in sales_rows:
                    _, _, product_name, quantity, total_amount, profit_val, date_val = s
                    try:
                        dt = datetime.fromisoformat(date_val) if isinstance(date_val, str) else date_val
                        date_str = dt.strftime('%Y-%m-%d %H:%M') if hasattr(dt, 'strftime') else str(date_val)
                    except Exception:
                        date_str = str(date_val)
                    lines.append(f"{product_name} | {quantity} | {total_amount:.2f} | {profit_val:.2f} | {date_str}")

                lines.append('')
                lines.append('EXPENSES DETAILS:')
                lines.append('Date | Name | Category | Amount | Notes')
                for ex in expenses_rows:
                    _, date_val, title, category, amount_val, notes = ex
                    try:
                        dt = datetime.fromisoformat(date_val) if isinstance(date_val, str) else date_val
                        date_str = dt.strftime('%Y-%m-%d %H:%M') if hasattr(dt, 'strftime') else str(date_val)
                    except Exception:
                        date_str = str(date_val)
                    lines.append(f"{date_str} | {title} | {category} | {amount_val:.2f} | {notes or ''}")

                # Adjust image size by number of lines
                png_out = base_name + '.png'
                # create image with size based on lines count
                height = max(6, int(0.4 * len(lines)))
                fig_height = max(4, height)
                fig = plt.figure(figsize=(8, fig_height))
                fig.patch.set_facecolor('#2b2b2b')
                plt.axis('off')
                y = 0.95
                plt.text(0.01, y, 'Business Report', fontsize=20, weight='bold', color='white')
                y -= 0.05
                for line in lines:
                    plt.text(0.01, y, line, fontsize=10, color='white')
                    y -= 0.03
                    if y < 0.02:
                        break
                plt.savefig(png_out, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
                plt.close(fig)

                if fmt == 'png':
                    messagebox.showinfo('Exported', f'PNG exported to {os.path.abspath(png_out)}')
                else:
                    pdf_out = base_name + '.pdf'
                    img = Image.open(png_out).convert('RGB')
                    img.save(pdf_out, 'PDF', resolution=150.0)
                    messagebox.showinfo('Exported', f'PDF exported to {os.path.abspath(pdf_out)}')
            else:
                messagebox.showerror('Format Error', f'Unknown format: {fmt}')
        except Exception as e:
            messagebox.showerror('Export Error', f'Failed to export: {e}')

if __name__ == "__main__":
    app = ClothingBrandApp()
    app.mainloop()