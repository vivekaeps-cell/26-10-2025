import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import shutil
import datetime
import configparser
import re
import winsound

# Master folder setup
user_home = os.path.expanduser("~")
master_folder = os.path.join(user_home, "Documents", "Master_Client_Desk")
os.makedirs(master_folder, exist_ok=True)

# Config file
config_file = os.path.join(master_folder, "config.ini")
config = configparser.ConfigParser()
if os.path.exists(config_file):
    config.read(config_file)
else:
    config['Paths'] = {
        'scanning_folder': os.path.join(user_home, "Desktop", "Scans"),
        'db_folder': master_folder,
        'backup_folder': os.path.join(master_folder, "Backups")
    }
    config['Lists'] = {
        'wards': "Ward 1,Ward 2,Ward 3,Ward 4,Ward 5,Ward 6,Ward 7,Ward 8,Ward 9,Ward 10,Ward 11,Ward 12,Ward 13,Ward 14,Ward 15,Ward 16,Ward 17,Ward 18,Ward 19,Ward 20",
        'villages': "Village1,Village2"  # Placeholder, user can edit
    }
    config['Preferences'] = {
        'last_cleanup_period': "24 hours",
        'last_sort': "Date Added (Newest First)"
    }
    with open(config_file, 'w') as cf:
        config.write(cf)

# Database setup
db_path = os.path.join(config['Paths']['db_folder'], "clientdesk.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mobile TEXT NOT NULL,
    father_name TEXT,
    ward TEXT,
    village TEXT,
    dues INTEGER DEFAULT 0,
    folder_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

# Sound effects
def play_success_sound():
    winsound.MessageBeep(winsound.MB_OK)

def play_error_sound():
    winsound.Beep(500, 300)

# Capitalize function
def capitalize_entry(event, entry):
    text = entry.get().title()
    entry.delete(0, tk.END)
    entry.insert(0, text)

# Validate mobile
def validate_mobile(event, entry):
    mobile = entry.get()
    if len(mobile) != 10 or not mobile.startswith(('6', '7', '8', '9')) or not mobile.isdigit():
        entry.config(bg='red')
    else:
        entry.config(bg='white')

# Delete word on Ctrl+Backspace
def delete_word(event, entry):
    text = entry.get()
    pos = entry.index(tk.INSERT)
    last_space = text.rfind(' ', 0, pos)
    if last_space == -1:
        entry.delete(0, pos)
    else:
        entry.delete(last_space + 1, pos)

# Main App
class ClientDeskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClientDesk Manager")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')  # Light gray bg for professional look

        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#f0f0f0', foreground='#333')
        style.configure('TButton', background='#007bff', foreground='white', padding=10, font=('Arial', 12))
        style.configure('TEntry', fieldbackground='white', font=('Arial', 12))
        style.configure('Treeview', background='white', fieldbackground='white', foreground='#333', rowheight=25)
        style.configure('Treeview.Heading', background='#007bff', foreground='white', font=('Arial', 12, 'bold'))
        style.map('Treeview', background=[('selected', '#007bff')], foreground=[('selected', 'white')])
        style.configure('Red.Treeview', foreground='red')  # For invalid mobiles

        # Variables
        self.name_var = tk.StringVar()
        self.mobile_var = tk.StringVar()
        self.father_var = tk.StringVar()
        self.ward_var = tk.StringVar()
        self.village_var = tk.StringVar()
        self.dues_var = tk.StringVar(value="0")
        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value=config['Preferences']['last_sort'])
        self.cleanup_var = tk.StringVar(value=config['Preferences']['last_cleanup_period'])
        self.selected_id = None
        self.recent_folders = []  # List of recent folder paths
        self.recent_show_count = 5  # Initial show 5

        # UI Frames
        self.create_ui()

        # Load data
        self.load_customers()

        # Total dues label
        self.update_total_dues()

    def create_ui(self):
        # Top Frame: Search and Sort
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=50, font=('Arial', 12))
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.search_customers)

        ttk.Label(top_frame, text="Sort by:").pack(side=tk.LEFT, padx=5)
        sort_options = [
            "Date Added (Newest First)", "Date Added (Oldest First)",
            "Dues High to Low", "Dues Low to High",
            "Name A-Z", "Name Z-A",
            "Time (Creation Recent)", "Time (Creation Oldest)",
            "Serial (ID Ascending)", "Serial (ID Descending)"
        ]
        ttk.Combobox(top_frame, textvariable=self.sort_var, values=sort_options, width=25, state='readonly').pack(side=tk.LEFT, padx=5)
        self.sort_var.trace('w', self.sort_customers)

        full_view_btn = ttk.Button(top_frame, text="Full View", command=self.open_full_view)
        full_view_btn.pack(side=tk.RIGHT, padx=5)

        # Form Frame: Left
        form_frame = ttk.Frame(self.root, padding=10, width=300)
        form_frame.pack(side=tk.LEFT, fill=tk.Y)

        fields = [
            ("Name:", self.name_var, lambda e: capitalize_entry(e, self.name_entry)),
            ("Mobile:", self.mobile_var, lambda e: validate_mobile(e, self.mobile_entry)),
            ("Father's Name:", self.father_var, lambda e: capitalize_entry(e, self.father_entry)),
            ("Ward:", self.ward_var),
            ("Village:", self.village_var),
            ("Dues (₹):", self.dues_var)
        ]

        for field in fields:
            if len(field) == 3:
                label, var, bind_func = field
            else:
                label, var = field
                bind_func = None
            ttk.Label(form_frame, text=label).pack(anchor=tk.W, pady=2)
            entry = ttk.Entry(form_frame, textvariable=var, width=30)
            entry.pack(pady=5, fill=tk.X)
            if label == "Name:": self.name_entry = entry
            if label == "Mobile:": 
                self.mobile_entry = entry
                entry.bind("<KeyRelease>", bind_func)
                entry.config(validate="key", validatecommand=(self.root.register(lambda s: len(s) <= 10 and s.isdigit()), '%P'))
            if label == "Father's Name:": self.father_entry = entry
            if bind_func and label != "Mobile:": entry.bind("<KeyRelease>", bind_func)
            entry.bind("<Control-BackSpace>", lambda e, ent=entry: delete_word(e, ent))
            if label == "Dues (₹):": entry.config(validate="key", validatecommand=(self.root.register(lambda s: s.isdigit() or s == ""), '%P'))

        # Ward quick entry
        self.ward_entry = [e for e in form_frame.winfo_children() if isinstance(e, ttk.Entry) and e.cget('textvariable') == str(self.ward_var)][0]
        self.ward_entry.bind("<KeyRelease>", self.quick_ward)

        # Village combobox with auto-complete
        village_list = config['Lists']['villages'].split(',')
        self.village_combo = ttk.Combobox(form_frame, textvariable=self.village_var, values=village_list, width=28)
        self.village_combo.pack(pady=5)
        self.village_combo.bind("<KeyRelease>", self.auto_complete_village)

        # Buttons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(pady=10, fill=tk.X)

        self.add_btn = ttk.Button(btn_frame, text="Add Customer", command=self.add_customer, width=15)
        self.add_btn.pack(side=tk.LEFT, padx=5)

        self.update_btn = ttk.Button(btn_frame, text="Update", command=self.update_customer, state=tk.DISABLED, width=15)
        self.update_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Clear", command=self.clear_form).pack(side=tk.LEFT, padx=5)

        # Other buttons below form
        action_frame = ttk.Frame(form_frame)
        action_frame.pack(pady=10, fill=tk.X)

        ttk.Button(action_frame, text="Open Folder", command=self.open_folder).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(action_frame, text="Delete", command=self.delete_customer).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(action_frame, text="WhatsApp", command=self.open_whatsapp).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(action_frame, text="Check Duplicates", command=self.check_duplicates).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(action_frame, text="Export CSV", command=self.export_csv).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(action_frame, text="Backup DB", command=self.backup_db).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(action_frame, text="Import Folders", command=self.import_folders).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(action_frame, text="Settings", command=self.open_settings).grid(row=2, column=1, padx=5, pady=5)

        # Cleanup
        cleanup_frame = ttk.Frame(form_frame)
        cleanup_frame.pack(pady=10, fill=tk.X)

        ttk.Label(cleanup_frame, text="Cleanup Period:").pack(side=tk.LEFT, padx=5)
        periods = ["Immediate", "15 minutes", "30 minutes", "1 hour", "2 hours", "6 hours", "12 hours", "24 hours", "Today", "Yesterday", "2 days ago", "1 week ago"]
        ttk.Combobox(cleanup_frame, textvariable=self.cleanup_var, values=periods, width=15, state='readonly').pack(side=tk.LEFT, padx=5)
        ttk.Button(cleanup_frame, text="Cleanup", command=self.cleanup_folders).pack(side=tk.LEFT, padx=5)

        # Recent Folders Section
        recent_frame = ttk.Frame(form_frame, padding=10)
        recent_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        ttk.Label(recent_frame, text="Recent Folders:", font=('Arial', 12, 'bold')).pack(anchor=tk.W)

        self.recent_listbox = tk.Listbox(recent_frame, height=10, font=('Arial', 11), bg='white', selectmode=tk.SINGLE)
        self.recent_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.recent_listbox.bind("<Double-Button-1>", self.open_recent_folder)

        ttk.Button(recent_frame, text="Show More", command=self.show_more_recent).pack(pady=5)

        # Database Treeview: Center
        tree_frame = ttk.Frame(self.root, padding=10)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("ID", "Name", "Mobile", "Father's Name", "Ward", "Village", "Dues", "Folder Path")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150 if col == "Folder Path" else 100, anchor=tk.CENTER if col in ["ID", "Dues"] else tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.bind("<ButtonRelease-1>", self.select_customer)
        self.tree.bind("<Double-Button-1>", lambda e: self.open_folder())

        # Total Dues Label
        self.total_dues_label = ttk.Label(tree_frame, text="Total Dues: ₹0", font=('Arial', 12, 'bold'), foreground='green')
        self.total_dues_label.pack(pady=10)

    def quick_ward(self, event):
            if event.keysym.isdigit() and 1 <= int(event.keysym) <= 20:
                self.ward_var.set(f"Ward {event.keysym}")

    def auto_complete_village(self, event):
        typed = self.village_var.get().lower()
        if typed:
            suggestions = [v for v in self.village_combo['values'] if v.lower().startswith(typed)]
            if suggestions:
                self.village_combo['values'] = suggestions
                self.village_combo.current(0)
            else:
                self.village_combo['values'] = config['Lists']['villages'].split(',')

    def add_customer(self):
        name = self.name_var.get().strip().title()
        mobile = self.mobile_var.get().strip()
        father = self.father_var.get().strip().title()
        ward = self.ward_var.get().strip()
        village = self.village_var.get().strip()
        try:
            dues = int(self.dues_var.get().strip())
        except ValueError:
            play_error_sound()
            messagebox.showerror("Error", "Dues must be a number!")
            return

        if not name or not mobile:
            play_error_sound()
            messagebox.showerror("Error", "Name and Mobile are required!")
            return

        if len(mobile) != 10 or not mobile.startswith(('6','7','8','9')):
            play_error_sound()
            messagebox.showerror("Error", "Invalid Mobile Number!")
            return

        # Check duplicate
        cursor.execute("SELECT * FROM customers WHERE name=? AND mobile=?", (name, mobile))
        if cursor.fetchone():
            play_error_sound()
            messagebox.showerror("Error", "Customer with same name and mobile exists!")
            return

        # Create folder
        base_folder_name = f"{name}_{mobile}"
        folder_path = os.path.join(os.path.expanduser("~/Desktop"), base_folder_name)
        if os.path.exists(folder_path):
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            folder_path = os.path.join(os.path.expanduser("~/Desktop"), f"{base_folder_name}_{timestamp}")
        os.makedirs(folder_path, exist_ok=True)

        # Move scans
        scanning_folder = config['Paths']['scanning_folder']
        if os.path.exists(scanning_folder):
            for file in os.listdir(scanning_folder):
                shutil.move(os.path.join(scanning_folder, file), folder_path)

        # Insert to DB
        cursor.execute('''
        INSERT INTO customers (name, mobile, father_name, ward, village, dues, folder_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, mobile, father, ward, village, dues, folder_path))
        conn.commit()

        self.load_customers()
        self.clear_form()
        self.update_total_dues()
        self.add_to_recent(folder_path)
        play_success_sound()
        self.show_feedback("Customer added successfully!", 'green')

    def update_customer(self):
        if not self.selected_id:
            return

        name = self.name_var.get().strip().title()
        mobile = self.mobile_var.get().strip()
        father = self.father_var.get().strip().title()
        ward = self.ward_var.get().strip()
        village = self.village_var.get().strip()
        dues = int(self.dues_var.get().strip())

        if len(mobile) != 10 or not mobile.startswith(('6','7','8','9')):
            play_error_sound()
            messagebox.showerror("Error", "Invalid Mobile Number!")
            return

        # Check duplicate excluding self
        cursor.execute("SELECT * FROM customers WHERE name=? AND mobile=? AND id != ?", (name, mobile, self.selected_id))
        if cursor.fetchone():
            play_error_sound()
            messagebox.showerror("Error", "Customer with same name and mobile exists!")
            return

        # Update folder name if changed
        cursor.execute("SELECT folder_path FROM customers WHERE id=?", (self.selected_id,))
        old_path = cursor.fetchone()[0]
        new_base = f"{name}_{mobile}"
        if os.path.basename(old_path).split('_')[0:-1] != name.split(' '):
            new_path = os.path.join(os.path.dirname(old_path), new_base)
            if os.path.exists(new_path):
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                new_path = os.path.join(os.path.dirname(old_path), f"{new_base}_{timestamp}")
            shutil.move(old_path, new_path)
            old_path = new_path

        cursor.execute('''
        UPDATE customers SET name=?, mobile=?, father_name=?, ward=?, village=?, dues=?, folder_path=?
        WHERE id=?
        ''', (name, mobile, father, ward, village, dues, old_path, self.selected_id))
        conn.commit()

        self.load_customers()
        self.clear_form()
        self.update_total_dues()
        play_success_sound()
        self.show_feedback("Customer updated successfully!", 'green')

    def clear_form(self):
        self.name_var.set("")
        self.mobile_var.set("")
        self.father_var.set("")
        self.ward_var.set("")
        self.village_var.set("")
        self.dues_var.set("0")
        self.selected_id = None
        self.update_btn['state'] = tk.DISABLED
        self.name_entry.config(bg='white')
        self.mobile_entry.config(bg='white')

    def load_customers(self, query="", sort="created_at DESC"):
        self.tree.delete(*self.tree.get_children())
        sql = "SELECT * FROM customers"
        if query:
            sql += f" WHERE name LIKE '%{query}%' OR mobile LIKE '%{query}%' OR father_name LIKE '%{query}%' OR ward LIKE '%{query}%' OR village LIKE '%{query}%' OR dues LIKE '%{query}%'"
        sql += f" ORDER BY {sort}"
        cursor.execute(sql)
        for row in cursor.fetchall():
            tag = 'red' if len(row[2]) != 10 or not row[2].startswith(('6','7','8','9')) else ''
            self.tree.insert("", tk.END, values=row, tags=(tag,))
        self.tree.tag_configure('red', foreground='red')

    def search_customers(self, event):
        self.load_customers(self.search_var.get(), self.get_sort_sql())

    def sort_customers(self, *args):
        config['Preferences']['last_sort'] = self.sort_var.get()
        with open(config_file, 'w') as cf:
            config.write(cf)
        self.load_customers(self.search_var.get(), self.get_sort_sql())

    def get_sort_sql(self):
        sort_map = {
            "Date Added (Newest First)": "created_at DESC",
            "Date Added (Oldest First)": "created_at ASC",
            "Dues High to Low": "dues DESC",
            "Dues Low to High": "dues ASC",
            "Name A-Z": "name ASC",
            "Name Z-A": "name DESC",
            "Time (Creation Recent)": "created_at DESC",
            "Time (Creation Oldest)": "created_at ASC",
            "Serial (ID Ascending)": "id ASC",
            "Serial (ID Descending)": "id DESC"
        }
        return sort_map.get(self.sort_var.get(), "created_at DESC")

    def select_customer(self, event):
        selected = self.tree.selection()
        if selected:
            row = self.tree.item(selected[0])['values']
            self.selected_id = row[0]
            self.name_var.set(row[1])
            self.mobile_var.set(row[2])
            self.father_var.set(row[3])
            self.ward_var.set(row[4])
            self.village_var.set(row[5])
            self.dues_var.set(str(row[6]))
            self.update_btn['state'] = tk.NORMAL
            validate_mobile(None, self.mobile_entry)

    def open_folder(self):
        selected = self.tree.selection()
        if selected:
            path = self.tree.item(selected[0])['values'][7]
            if os.path.exists(path):
                os.startfile(path)
            else:
                play_error_sound()
                messagebox.showerror("Error", "Folder not found!")

    def delete_customer(self):
        selected = self.tree.selection()
        if selected:
            row = self.tree.item(selected[0])['values']
            path = row[7]
            if os.path.exists(path):
                if os.listdir(path):
                    os.startfile(path)
                    if not messagebox.askyesno("Confirm Delete", "Folder has files. Delete anyway?"):
                        return
                shutil.rmtree(path)
            cursor.execute("DELETE FROM customers WHERE id=?", (row[0],))
            conn.commit()
            self.load_customers()
            self.clear_form()
            self.update_total_dues()
            play_success_sound()
            self.show_feedback("Customer deleted!", 'green')

    def open_whatsapp(self):
        selected = self.tree.selection()
        if selected:
            mobile = self.tree.item(selected[0])['values'][2]
            os.startfile(f"whatsapp://send?phone=+91{mobile}")

    def check_duplicates(self):
        cursor.execute("SELECT name, mobile, COUNT(*) FROM customers GROUP BY name, mobile HAVING COUNT(*) > 1")
        dups = cursor.fetchall()
        if dups:
            msg = "\n".join([f"{n} - {m} (Count: {c})" for n, m, c in dups])
            if messagebox.askyesno("Duplicates Found", f"Delete duplicates?\n{msg}"):
                for n, m in set([(d[0], d[1]) for d in dups]):
                    cursor.execute("SELECT id FROM customers WHERE name=? AND mobile=? ORDER BY id ASC", (n, m))
                    ids = [r[0] for r in cursor.fetchall()][1:]  # Keep first
                    for id in ids:
                        cursor.execute("DELETE FROM customers WHERE id=?", (id,))
                conn.commit()
                self.load_customers()
                play_success_sound()
                self.show_feedback("Duplicates removed!", 'green')
        else:
            messagebox.showinfo("No Duplicates", "No duplicates found.")

    def export_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", initialdir=master_folder)
        if file:
            cursor.execute("SELECT * FROM customers")
            with open(file, 'w', encoding='utf-8') as f:
                f.write("ID,Name,Mobile,Father's Name,Ward,Village,Dues,Folder Path\n")
                for row in cursor.fetchall():
                    f.write(",".join(map(str, row)) + "\n")
            play_success_sound()
            self.show_feedback("Exported to CSV!", 'green')

    def backup_db(self):
        backup_folder = config['Paths']['backup_folder']
        os.makedirs(backup_folder, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        shutil.copy(db_path, os.path.join(backup_folder, f"clientdesk_{timestamp}.db"))
        play_success_sound()
        self.show_feedback("Database backed up!", 'green')

    def import_folders(self):
        import_dir = filedialog.askdirectory(title="Select Folder to Import")
        if import_dir:
            for item in os.listdir(import_dir):
                if os.path.isdir(os.path.join(import_dir, item)):
                    match = re.match(r"(.+)_(\d{10})(_.*)?$", item)
                    if match:
                        name = match.group(1).replace("_", " ").title()
                        mobile = match.group(2)
                        path = os.path.join(import_dir, item)
                        cursor.execute("SELECT * FROM customers WHERE name=? AND mobile=?", (name, mobile))
                        if not cursor.fetchone():
                            cursor.execute('''
                            INSERT INTO customers (name, mobile, folder_path)
                            VALUES (?, ?, ?)
                            ''', (name, mobile, path))
            conn.commit()
            self.load_customers()
            play_success_sound()
            self.show_feedback("Folders imported!", 'green')

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry("600x400")

        # Paths
        ttk.Label(settings_win, text="Scanning Folder:").pack(pady=5)
        scan_entry = ttk.Entry(settings_win, width=50)
        scan_entry.insert(0, config['Paths']['scanning_folder'])
        scan_entry.pack()
        ttk.Button(settings_win, text="Browse", command=lambda: self.browse_path(scan_entry)).pack()

        ttk.Label(settings_win, text="Database Folder:").pack(pady=5)
        db_entry = ttk.Entry(settings_win, width=50)
        db_entry.insert(0, config['Paths']['db_folder'])
        db_entry.pack()
        ttk.Button(settings_win, text="Browse", command=lambda: self.browse_path(db_entry)).pack()

        ttk.Label(settings_win, text="Backup Folder:").pack(pady=5)
        backup_entry = ttk.Entry(settings_win, width=50)
        backup_entry.insert(0, config['Paths']['backup_folder'])
        backup_entry.pack()
        ttk.Button(settings_win, text="Browse", command=lambda: self.browse_path(backup_entry)).pack()

        # Lists
        ttk.Label(settings_win, text="Wards (comma-separated):").pack(pady=5)
        wards_text = tk.Text(settings_win, height=3, width=50)
        wards_text.insert(tk.END, config['Lists']['wards'])
        wards_text.pack()

        ttk.Label(settings_win, text="Villages (comma-separated):").pack(pady=5)
        villages_text = tk.Text(settings_win, height=5, width=50)
        villages_text.insert(tk.END, config['Lists']['villages'])
        villages_text.pack()

        ttk.Button(settings_win, text="Save", command=lambda: self.save_settings(scan_entry.get(), db_entry.get(), backup_entry.get(), wards_text.get("1.0", tk.END).strip(), villages_text.get("1.0", tk.END).strip(), settings_win)).pack(pady=10)

    def browse_path(self, entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def save_settings(self, scan, db, backup, wards, villages, win):
        config['Paths']['scanning_folder'] = scan
        config['Paths']['db_folder'] = db
        config['Paths']['backup_folder'] = backup
        config['Lists']['wards'] = wards
        config['Lists']['villages'] = villages
        with open(config_file, 'w') as cf:
            config.write(cf)
        # Update village combo
        self.village_combo['values'] = villages.split(',')
        win.destroy()
        play_success_sound()
        self.show_feedback("Settings saved!", 'green')

    def cleanup_folders(self):
        config['Preferences']['last_cleanup_period'] = self.cleanup_var.get()
        with open(config_file, 'w') as cf:
            config.write(cf)

        now = datetime.datetime.now()
        desktop = os.path.expanduser("~/Desktop")
        period = self.cleanup_var.get()

        deltas = {
            "Immediate": datetime.timedelta(seconds=0),
            "15 minutes": datetime.timedelta(minutes=15),
            "30 minutes": datetime.timedelta(minutes=30),
            "1 hour": datetime.timedelta(hours=1),
            "2 hours": datetime.timedelta(hours=2),
            "6 hours": datetime.timedelta(hours=6),
            "12 hours": datetime.timedelta(hours=12),
            "24 hours": datetime.timedelta(hours=24),
            "Today": now - now.replace(hour=0, minute=0, second=0, microsecond=0),
            "Yesterday": datetime.timedelta(days=1),
            "2 days ago": datetime.timedelta(days=2),
            "1 week ago": datetime.timedelta(weeks=1)
        }
        delta = deltas.get(period, datetime.timedelta(0))

        month_folder = now.strftime("%B_%Y")
        target_folder = os.path.join(master_folder, month_folder)
        os.makedirs(target_folder, exist_ok=True)

        moved = 0
        for item in os.listdir(desktop):
            path = os.path.join(desktop, item)
            if os.path.isdir(path) and re.match(r".+_\d{10}(_\d+)?$", item):
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                if period == "Immediate" or (now - mtime) > delta:
                    new_path = os.path.join(target_folder, item)
                    shutil.move(path, new_path)
                    cursor.execute("UPDATE customers SET folder_path=? WHERE folder_path=?", (new_path, path))
                    conn.commit()
                    moved += 1

        self.load_customers()
        play_success_sound()
        self.show_feedback(f"{moved} folders cleaned up!", 'green')

    def update_total_dues(self):
        cursor.execute("SELECT SUM(dues) FROM customers")
        total = cursor.fetchone()[0] or 0
        self.total_dues_label.config(text=f"Total Dues: ₹{total}")

    def show_feedback(self, msg, color):
        feedback = ttk.Label(self.root, text=msg, foreground=color, font=('Arial', 12, 'bold'))
        feedback.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.root.after(3000, feedback.destroy)

    def open_full_view(self):
        full_win = tk.Toplevel(self.root)
        full_win.title("Full Database View")
        full_win.geometry("1400x900")
        full_win.attributes('-topmost', False)

        search_entry = ttk.Entry(full_win, textvariable=self.search_var, width=50)
        search_entry.pack(pady=10)
        search_entry.bind("<KeyRelease>", self.search_customers)

        sort_combo = ttk.Combobox(full_win, textvariable=self.sort_var, values=self.sort_var.get(), width=25, state='readonly')
        sort_combo.pack(pady=10)

        tree = ttk.Treeview(full_win, columns=self.tree['columns'], show='headings', height=30)
        for col in self.tree['columns']:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill=tk.BOTH, expand=True)

        # Load data into full view
        self.load_customers()  # Reload main to sync

    def add_to_recent(self, path):
        self.recent_folders.insert(0, path)
        self.update_recent_listbox()

    def update_recent_listbox(self):
        self.recent_listbox.delete(0, tk.END)
        for i in range(min(self.recent_show_count, len(self.recent_folders))):
            short_path = os.path.basename(self.recent_folders[i])
            self.recent_listbox.insert(tk.END, short_path)

    def show_more_recent(self):
        self.recent_show_count += 5
        self.update_recent_listbox()

    def open_recent_folder(self, event):
        selected = self.recent_listbox.curselection()
        if selected:
            path = self.recent_folders[selected[0]]
            if os.path.exists(path):
                os.startfile(path)

# Run app
if __name__ == "__main__":
    root = tk.Tk()
    app = ClientDeskApp(root)
    root.mainloop()