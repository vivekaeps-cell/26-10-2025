import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import shutil
import datetime
import configparser
import re
import winsound
from typing import Optional
import ctypes
import tkinter.font as tkfont

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
        'villages': "Village1,Village2"
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

# Professional sound effects - minimal and only for important actions
def play_success_sound():
    """Subtle success tone."""
    try:
        winsound.Beep(800, 100)
    except:
        pass

def play_error_sound():
    """Error notification sound."""
    try:
        winsound.MessageBeep(winsound.MB_ICONHAND)
    except:
        pass

# Button icons using Unicode symbols
ICONS = {
    'add': '➕',
    'update': '✏️',
    'clear': '🔄',
    'folder': '📁',
    'delete': '🗑️',
    'whatsapp': '💬',
    'check': '🔍',
    'export': '📊',
    'backup': '💾',
    'import': '📥',
    'settings': '⚙️',
    'cleanup': '🧹',
    'view': '👁️'
}

# Capitalize function
def capitalize_entry(event, entry):
    text = entry.get().title()
    entry.delete(0, tk.END)
    entry.insert(0, text)

# Validate mobile
def validate_mobile(event, entry):
    mobile = entry.get()
    if len(mobile) != 10 or not mobile.startswith(('6', '7', '8', '9')) or not mobile.isdigit():
        entry.config(style='Error.TEntry')
    else:
        entry.config(style='TEntry')

# Delete word on Ctrl+Backspace
def delete_word(event, entry):
    text = entry.get()
    pos = entry.index(tk.INSERT)
    last_space = text.rfind(' ', 0, pos)
    if last_space == -1:
        entry.delete(0, pos)
    else:
        entry.delete(last_space + 1, pos)

# Main App with 4K support
class ClientDeskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClientDesk Manager Pro - 4K Edition")

        # Get screen resolution for proper scaling
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Set window size based on screen resolution
        if screen_width >= 3840:  # 4K or higher
            self.root.geometry("2400x1600")
            self.font_size = 16
            self.heading_size = 20
            self.title_size = 24
            self.padding = 20
            self.entry_width = 40
            self.row_height = 40
            self.icon_size = 18
        elif screen_width >= 2560:  # 2K
            self.root.geometry("1800x1200")
            self.font_size = 14
            self.heading_size = 18
            self.title_size = 22
            self.padding = 15
            self.entry_width = 35
            self.row_height = 35
            self.icon_size = 16
        else:  # Full HD and below
            self.root.geometry("1400x900")
            self.font_size = 12
            self.heading_size = 14
            self.title_size = 18
            self.padding = 10
            self.entry_width = 30
            self.row_height = 30
            self.icon_size = 14

        # Center window
        self.root.update_idletasks()
        x = (screen_width - self.root.winfo_width()) // 2
        y = (screen_height - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")

        self.root.configure(bg='#f0f4f8')

        # Create scalable font objects
        self.base_font = tkfont.Font(family='Segoe UI', size=self.font_size)
        self.heading_font = tkfont.Font(family='Segoe UI', size=self.heading_size, weight='bold')
        self.title_font = tkfont.Font(family='Segoe UI', size=self.title_size, weight='bold')
        self.icon_font = tkfont.Font(family='Segoe UI Emoji', size=self.icon_size)

        # Enhanced Style Configuration
        style = ttk.Style()
        style.theme_use('clam')

        # Professional color scheme
        bg_main = '#f0f4f8'
        bg_card = '#ffffff'
        bg_input = '#f7fafc'
        accent_primary = '#2563eb'
        accent_success = '#10b981'
        accent_danger = '#ef4444'
        accent_warning = '#f59e0b'
        text_primary = '#1e293b'
        text_secondary = '#64748b'
        border_color = '#e2e8f0'

        # Frame styles
        style.configure('TFrame', background=bg_main)
        style.configure('Card.TFrame', background=bg_card, relief='flat', borderwidth=1)

        # Label styles
        style.configure('TLabel', background=bg_main, foreground=text_primary, font=self.base_font)
        style.configure('Title.TLabel', font=self.title_font, foreground=accent_primary, background=bg_main)
        style.configure('Heading.TLabel', font=self.heading_font, foreground=text_primary, background=bg_main)
        style.configure('Success.TLabel', foreground=accent_success, font=self.heading_font, background=bg_main)
        style.configure('CardLabel.TLabel', background=bg_card, foreground=text_primary, font=self.base_font)

        # Primary button (for most used actions)
        style.configure('Primary.TButton',
                       background=accent_primary,
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(self.padding*2, self.padding),
                       font=self.heading_font)
        style.map('Primary.TButton',
                 background=[('active', '#1d4ed8'), ('pressed', '#1e40af')])

        # Success button (for add/backup)
        style.configure('Success.TButton',
                       background=accent_success,
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(self.padding, self.padding//2),
                       font=self.base_font)
        style.map('Success.TButton',
                 background=[('active', '#059669'), ('pressed', '#047857')])

        # Danger button (for delete)
        style.configure('Danger.TButton',
                       background=accent_danger,
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(self.padding, self.padding//2),
                       font=self.base_font)
        style.map('Danger.TButton',
                 background=[('active', '#dc2626'), ('pressed', '#b91c1c')])

        # Secondary button (for less used actions)
        style.configure('Secondary.TButton',
                       background='#6366f1',
                       foreground='#ffffff',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(self.padding//2, self.padding//4),
                       font=('Segoe UI', self.font_size-2))
        style.map('Secondary.TButton',
                 background=[('active', '#4f46e5'), ('pressed', '#4338ca')])

        # Entry styles
        style.configure('TEntry',
                       fieldbackground=bg_input,
                       foreground=text_primary,
                       borderwidth=1,
                       relief='solid',
                       padding=self.padding//2,
                       font=self.base_font)
        style.configure('Error.TEntry',
                       fieldbackground='#fee2e2',
                       foreground=text_primary)

        # Combobox styles
        style.configure('TCombobox',
                       fieldbackground=bg_input,
                       background=bg_input,
                       foreground=text_primary,
                       borderwidth=1,
                       arrowsize=self.font_size,
                       padding=self.padding//2,
                       font=self.base_font)

        # Treeview styles
        style.configure('Treeview',
                       background=bg_card,
                       foreground=text_primary,
                       fieldbackground=bg_card,
                       borderwidth=0,
                       font=self.base_font,
                       rowheight=self.row_height)
        style.configure('Treeview.Heading',
                       background=bg_input,
                       foreground=accent_primary,
                       borderwidth=1,
                       relief='flat',
                       font=self.heading_font)
        style.map('Treeview',
                 background=[('selected', accent_primary)],
                 foreground=[('selected', '#ffffff')])
        style.map('Treeview.Heading',
                 background=[('active', border_color)])

        # Scrollbar styles
        style.configure('Vertical.TScrollbar',
                       background=bg_input,
                       troughcolor=bg_main,
                       borderwidth=0,
                       arrowsize=self.font_size)
        style.configure('Horizontal.TScrollbar',
                       background=bg_input,
                       troughcolor=bg_main,
                       borderwidth=0,
                       arrowsize=self.font_size)

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
        self.selected_id: Optional[int] = None
        self.recent_folders = []
        self.recent_show_count = 5

        # UI Frames
        self.create_ui()

        # Load data
        self.load_customers()
        self.update_total_dues()

    def create_ui(self):
        # Main container with padding
        main_container = ttk.Frame(self.root, padding=self.padding)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Title bar
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, self.padding))

        title_label = ttk.Label(title_frame, text="ClientDesk Manager Pro", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)

        # Top Frame: Search, Sort, and Full View
        top_frame = ttk.Frame(main_container, style='Card.TFrame', padding=self.padding)
        top_frame.pack(fill=tk.X, pady=(0, self.padding))

        search_frame = ttk.Frame(top_frame, style='Card.TFrame')
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(search_frame, text=f"{ICONS['check']} Search:", style='CardLabel.TLabel', font=self.icon_font).pack(side=tk.LEFT, padx=(0, self.padding//2))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=self.entry_width+10)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, self.padding))
        search_entry.bind("<KeyRelease>", self.search_customers)

        ttk.Label(search_frame, text="Sort:", style='CardLabel.TLabel').pack(side=tk.LEFT, padx=(self.padding, self.padding//2))
        sort_options = [
            "Date Added (Newest First)", "Date Added (Oldest First)",
            "Dues High to Low", "Dues Low to High",
            "Name A-Z", "Name Z-A",
            "Time (Creation Recent)", "Time (Creation Oldest)",
            "Serial (ID Ascending)", "Serial (ID Descending)"
        ]
        sort_combo = ttk.Combobox(search_frame, textvariable=self.sort_var, values=sort_options, width=25, state='readonly')
        sort_combo.pack(side=tk.LEFT, padx=(0, self.padding))
        self.sort_var.trace('w', self.sort_customers)

        # Full View button (larger and prominent)
        full_view_btn = ttk.Button(top_frame, text=f"{ICONS['view']} Full View", command=self.open_full_view, style='Primary.TButton')
        full_view_btn.pack(side=tk.RIGHT, padx=(self.padding, 0))

        # Content area
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Form Frame: Left side
        form_frame = ttk.Frame(content_frame, style='Card.TFrame', padding=self.padding)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self.padding))

        # Form title
        ttk.Label(form_frame, text="Customer Details", style='Heading.TLabel').pack(anchor=tk.W, pady=(0, self.padding))

        # Form fields with proper spacing
        fields = [
            ("Name:", self.name_var, lambda e: capitalize_entry(e, self.name_entry)),
            ("Mobile:", self.mobile_var, lambda e: validate_mobile(e, self.mobile_entry)),
            ("Father's Name:", self.father_var, lambda e: capitalize_entry(e, self.father_entry)),
        ]

        for label, var, bind_func in fields:
            field_frame = ttk.Frame(form_frame, style='Card.TFrame')
            field_frame.pack(fill=tk.X, pady=(0, self.padding))

            ttk.Label(field_frame, text=label, style='CardLabel.TLabel', font=('Segoe UI', self.font_size, 'bold')).pack(anchor=tk.W, pady=(0, 5))
            entry = ttk.Entry(field_frame, textvariable=var, width=self.entry_width)
            entry.pack(fill=tk.X)

            if label == "Name:":
                self.name_entry = entry
                entry.bind("<KeyRelease>", bind_func)
            elif label == "Mobile:":
                self.mobile_entry = entry
                entry.bind("<KeyRelease>", bind_func)
                entry.config(validate="key", validatecommand=(self.root.register(lambda s: len(s) <= 10 and (s.isdigit() or s == "")), '%P'))
            elif label == "Father's Name:":
                self.father_entry = entry
                entry.bind("<KeyRelease>", bind_func)

            entry.bind("<Control-BackSpace>", lambda e, ent=entry: delete_word(e, ent))

        # Ward field
        ward_frame = ttk.Frame(form_frame, style='Card.TFrame')
        ward_frame.pack(fill=tk.X, pady=(0, self.padding))
        ttk.Label(ward_frame, text="Ward:", style='CardLabel.TLabel', font=('Segoe UI', self.font_size, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        self.ward_entry = ttk.Entry(ward_frame, textvariable=self.ward_var, width=self.entry_width)
        self.ward_entry.pack(fill=tk.X)
        self.ward_entry.bind("<KeyRelease>", self.quick_ward)
        self.ward_entry.bind("<Control-BackSpace>", lambda e: delete_word(e, self.ward_entry))

        # Village field
        village_frame = ttk.Frame(form_frame, style='Card.TFrame')
        village_frame.pack(fill=tk.X, pady=(0, self.padding))
        ttk.Label(village_frame, text="Village:", style='CardLabel.TLabel', font=('Segoe UI', self.font_size, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        village_list = config['Lists']['villages'].split(',')
        self.village_combo = ttk.Combobox(village_frame, textvariable=self.village_var,
                                         values=village_list, width=self.entry_width-2)
        self.village_combo.pack(fill=tk.X)
        self.village_combo.bind("<KeyRelease>", self.auto_complete_village)

        # Dues field
        dues_frame = ttk.Frame(form_frame, style='Card.TFrame')
        dues_frame.pack(fill=tk.X, pady=(0, self.padding))
        ttk.Label(dues_frame, text="Dues (₹):", style='CardLabel.TLabel', font=('Segoe UI', self.font_size, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        dues_entry = ttk.Entry(dues_frame, textvariable=self.dues_var, width=self.entry_width)
        dues_entry.pack(fill=tk.X)
        dues_entry.config(validate="key", validatecommand=(self.root.register(lambda s: s.isdigit() or s == ""), '%P'))

        # PRIMARY ACTION BUTTONS (Most Used - Larger)
        primary_btn_frame = ttk.Frame(form_frame, style='Card.TFrame')
        primary_btn_frame.pack(fill=tk.X, pady=(self.padding, 0))

        ttk.Label(primary_btn_frame, text="Primary Actions", style='CardLabel.TLabel', font=('Segoe UI', self.font_size-1, 'bold')).pack(anchor=tk.W, pady=(0, self.padding//2))

        self.add_btn = ttk.Button(primary_btn_frame, text=f"{ICONS['add']} Add Customer",
                                  command=self.add_customer,
                                  style='Success.TButton')
        self.add_btn.pack(fill=tk.X, pady=(0, self.padding//2))

        self.update_btn = ttk.Button(primary_btn_frame, text=f"{ICONS['update']} Update Customer",
                                     command=self.update_customer,
                                     style='Primary.TButton',
                                     state=tk.DISABLED)
        self.update_btn.pack(fill=tk.X, pady=(0, self.padding//2))

        open_folder_btn = ttk.Button(primary_btn_frame, text=f"{ICONS['folder']} Open Folder",
                                     command=self.open_folder,
                                     style='Primary.TButton')
        open_folder_btn.pack(fill=tk.X, pady=(0, self.padding//2))

        whatsapp_btn = ttk.Button(primary_btn_frame, text=f"{ICONS['whatsapp']} WhatsApp",
                                  command=self.open_whatsapp,
                                  style='Success.TButton')
        whatsapp_btn.pack(fill=tk.X, pady=(0, self.padding//2))

        ttk.Button(primary_btn_frame, text=f"{ICONS['clear']} Clear Form",
                  command=self.clear_form,
                  style='Secondary.TButton').pack(fill=tk.X, pady=(0, self.padding))

        # SECONDARY ACTION BUTTONS (Less Used - Smaller, Organized in Grid)
        secondary_btn_frame = ttk.Frame(form_frame, style='Card.TFrame')
        secondary_btn_frame.pack(fill=tk.X, pady=(self.padding, 0))

        ttk.Label(secondary_btn_frame, text="Additional Actions", style='CardLabel.TLabel', font=('Segoe UI', self.font_size-1, 'bold')).pack(anchor=tk.W, pady=(0, self.padding//2))

        secondary_grid = ttk.Frame(secondary_btn_frame, style='Card.TFrame')
        secondary_grid.pack(fill=tk.X)

        secondary_actions = [
            (f"{ICONS['delete']} Delete", self.delete_customer, 'Danger.TButton'),
            (f"{ICONS['check']} Duplicates", self.check_duplicates, 'Secondary.TButton'),
            (f"{ICONS['export']} Export", self.export_csv, 'Secondary.TButton'),
            (f"{ICONS['backup']} Backup", self.backup_db, 'Success.TButton'),
            (f"{ICONS['import']} Import", self.import_folders, 'Secondary.TButton'),
            (f"{ICONS['settings']} Settings", self.open_settings, 'Secondary.TButton'),
        ]

        for idx, (text, cmd, btn_style) in enumerate(secondary_actions):
            btn = ttk.Button(secondary_grid, text=text, command=cmd, style=btn_style)
            btn.grid(row=idx//2, column=idx%2, padx=3, pady=3, sticky='ew')

        secondary_grid.columnconfigure(0, weight=1)
        secondary_grid.columnconfigure(1, weight=1)

        # Cleanup section
        cleanup_frame = ttk.Frame(form_frame, style='Card.TFrame', padding=self.padding)
        cleanup_frame.pack(fill=tk.X, pady=(self.padding, 0))

        ttk.Label(cleanup_frame, text=f"{ICONS['cleanup']} Cleanup", style='CardLabel.TLabel', font=('Segoe UI', self.font_size, 'bold')).pack(anchor=tk.W, pady=(0, self.padding//2))

        periods = ["Immediate", "15 minutes", "30 minutes", "1 hour", "2 hours",
                  "6 hours", "12 hours", "24 hours", "Today", "Yesterday",
                  "2 days ago", "1 week ago"]
        ttk.Combobox(cleanup_frame, textvariable=self.cleanup_var, values=periods,
                    width=self.entry_width-2, state='readonly').pack(fill=tk.X, pady=(0, self.padding//2))
        ttk.Button(cleanup_frame, text="Run Cleanup",
                  command=self.cleanup_folders,
                  style='Secondary.TButton').pack(fill=tk.X)

        # Recent Folders
        recent_frame = ttk.Frame(form_frame, style='Card.TFrame', padding=self.padding)
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=(self.padding, 0))

        ttk.Label(recent_frame, text=f"{ICONS['folder']} Recent Folders", style='CardLabel.TLabel', font=('Segoe UI', self.font_size, 'bold')).pack(anchor=tk.W, pady=(0, self.padding//2))

        self.recent_listbox = tk.Listbox(recent_frame, font=('Segoe UI', self.font_size-1),
                                        bg='#f7fafc', fg='#1e293b',
                                        selectbackground='#2563eb',
                                        selectforeground='#ffffff',
                                        borderwidth=1,
                                        highlightthickness=0,
                                        relief='solid')
        self.recent_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, self.padding//2))
        self.recent_listbox.bind("<Double-Button-1>", self.open_recent_folder)

        ttk.Button(recent_frame, text="Show More", command=self.show_more_recent, style='Secondary.TButton').pack(fill=tk.X)

        # Database Treeview: Right side
        tree_container = ttk.Frame(content_frame, style='Card.TFrame', padding=self.padding)
        tree_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(tree_container, text="Customer Database", style='Heading.TLabel').pack(anchor=tk.W, pady=(0, self.padding))

        tree_frame = ttk.Frame(tree_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Name", "Mobile", "Father's Name", "Ward", "Village", "Dues", "Folder Path")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                selectmode='browse')

        # Column configuration with proper widths
        col_widths = {
            "ID": 80,
            "Name": 200,
            "Mobile": 150,
            "Father's Name": 200,
            "Ward": 120,
            "Village": 150,
            "Dues": 120,
            "Folder Path": 300
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[col],
                           anchor=tk.CENTER if col in ["ID", "Dues"] else tk.W,
                           minwidth=50)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.bind("<ButtonRelease-1>", self.select_customer)
        self.tree.bind("<Double-Button-1>", lambda e: self.open_folder())

        # Total Dues
        self.total_dues_label = ttk.Label(tree_container, text="Total Dues: ₹0",
                                         style='Success.TLabel')
        self.total_dues_label.pack(pady=(self.padding, 0))

    def quick_ward(self, event):
        if event.keysym.isdigit() and 1 <= int(event.keysym) <= 9:
            self.ward_var.set(f"Ward {event.keysym}")

    def auto_complete_village(self, event):
        typed = self.village_var.get().lower()
        if typed:
            suggestions = [v for v in self.village_combo['values'] if v.lower().startswith(typed)]
            if suggestions:
                self.village_combo['values'] = suggestions
            else:
                self.village_combo['values'] = config['Lists']['villages'].split(',')

    def add_customer(self):
        name = self.name_var.get().strip().title()
        mobile = self.mobile_var.get().strip()
        father = self.father_var.get().strip().title()
        ward = self.ward_var.get().strip()
        village = self.village_var.get().strip()

        try:
            dues = int(self.dues_var.get().strip()) if self.dues_var.get().strip() else 0
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
            messagebox.showerror("Error", "Invalid Mobile Number! Must be 10 digits starting with 6, 7, 8, or 9.")
            return

        cursor.execute("SELECT * FROM customers WHERE name=? AND mobile=?", (name, mobile))
        if cursor.fetchone():
            play_error_sound()
            messagebox.showerror("Error", "Customer with same name and mobile already exists!")
            return

        base_folder_name = f"{name.replace(' ', '_')}_{mobile}"
        folder_path = os.path.join(os.path.expanduser("~/Desktop"), base_folder_name)

        if os.path.exists(folder_path):
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            folder_path = os.path.join(os.path.expanduser("~/Desktop"), f"{base_folder_name}_{timestamp}")

        os.makedirs(folder_path, exist_ok=True)

        scanning_folder = config['Paths']['scanning_folder']
        if os.path.exists(scanning_folder):
            for file in os.listdir(scanning_folder):
                src = os.path.join(scanning_folder, file)
                if os.path.isfile(src):
                    shutil.move(src, folder_path)

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
        self.show_feedback("✓ Customer added successfully!", 'success')

    def update_customer(self):
        if not self.selected_id:
            return

        name = self.name_var.get().strip().title()
        mobile = self.mobile_var.get().strip()
        father = self.father_var.get().strip().title()
        ward = self.ward_var.get().strip()
        village = self.village_var.get().strip()

        try:
            dues = int(self.dues_var.get().strip()) if self.dues_var.get().strip() else 0
        except ValueError:
            play_error_sound()
            messagebox.showerror("Error", "Dues must be a number!")
            return

        if len(mobile) != 10 or not mobile.startswith(('6','7','8','9')):
            play_error_sound()
            messagebox.showerror("Error", "Invalid Mobile Number!")
            return

        cursor.execute("SELECT * FROM customers WHERE name=? AND mobile=? AND id != ?",
                      (name, mobile, self.selected_id))
        if cursor.fetchone():
            play_error_sound()
            messagebox.showerror("Error", "Customer with same name and mobile already exists!")
            return

        cursor.execute("SELECT folder_path FROM customers WHERE id=?", (self.selected_id,))
        result = cursor.fetchone()
        if result:
            old_path = result[0]
            new_base = f"{name.replace(' ', '_')}_{mobile}"
            new_path = os.path.join(os.path.dirname(old_path), new_base)

            if old_path != new_path and os.path.exists(old_path):
                if os.path.exists(new_path):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    new_path = os.path.join(os.path.dirname(old_path), f"{new_base}_{timestamp}")
                try:
                    shutil.move(old_path, new_path)
                    old_path = new_path
                except Exception as e:
                    messagebox.showwarning("Warning", f"Could not rename folder: {str(e)}")

            cursor.execute('''
            UPDATE customers SET name=?, mobile=?, father_name=?, ward=?, village=?, dues=?, folder_path=?
            WHERE id=?
            ''', (name, mobile, father, ward, village, dues, old_path, self.selected_id))
            conn.commit()

            self.load_customers()
            self.clear_form()
            self.update_total_dues()
            play_success_sound()
            self.show_feedback("✓ Customer updated successfully!", 'success')

    def clear_form(self):
        self.name_var.set("")
        self.mobile_var.set("")
        self.father_var.set("")
        self.ward_var.set("")
        self.village_var.set("")
        self.dues_var.set("0")
        self.selected_id = None
        self.update_btn['state'] = tk.DISABLED
        self.mobile_entry.config(style='TEntry')

    def load_customers(self, query="", sort="created_at DESC"):
        for item in self.tree.get_children():
            self.tree.delete(item)

        sql = "SELECT * FROM customers"
        params = []

        if query:
            sql += """ WHERE name LIKE ? OR mobile LIKE ? OR father_name LIKE ?
                      OR ward LIKE ? OR village LIKE ? OR CAST(dues AS TEXT) LIKE ?"""
            params = [f"%{query}%"] * 6

        sql += f" ORDER BY {sort}"

        cursor.execute(sql, params)
        for row in cursor.fetchall():
            mobile = row[2]
            tag = 'error' if len(mobile) != 10 or not mobile.startswith(('6','7','8','9')) else ''
            self.tree.insert("", tk.END, values=row, tags=(tag,))

        self.tree.tag_configure('error', foreground='#ef4444')

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
            self.father_var.set(row[3] if row[3] else "")
            self.ward_var.set(row[4] if row[4] else "")
            self.village_var.set(row[5] if row[5] else "")
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
        if not selected:
            play_error_sound()
            messagebox.showwarning("Warning", "Please select a customer to delete.")
            return

        row = self.tree.item(selected[0])['values']
        path = row[7]

        confirm = messagebox.askyesno("Confirm Delete",
                                      f"Are you sure you want to delete {row[1]}?\n\n"
                                      "This will delete the customer record and their folder.")
        if not confirm:
            return

        if os.path.exists(path):
            if os.listdir(path):
                os.startfile(path)
                if not messagebox.askyesno("Folder Contains Files",
                                          "The folder contains files. Do you still want to delete it?"):
                    return
            try:
                shutil.rmtree(path)
            except Exception as e:
                messagebox.showwarning("Warning", f"Could not delete folder: {str(e)}")

        cursor.execute("DELETE FROM customers WHERE id=?", (row[0],))
        conn.commit()

        self.load_customers()
        self.clear_form()
        self.update_total_dues()
        play_success_sound()
        self.show_feedback("✓ Customer deleted successfully!", 'success')

    def open_whatsapp(self):
        selected = self.tree.selection()
        if selected:
            mobile = self.tree.item(selected[0])['values'][2]
            try:
                os.startfile(f"whatsapp://send?phone=+91{mobile}")
            except:
                play_error_sound()
                messagebox.showerror("Error", "Could not open WhatsApp. Make sure WhatsApp is installed.")

    def check_duplicates(self):
        cursor.execute("""
        SELECT name, mobile, COUNT(*) as count
        FROM customers
        GROUP BY name, mobile
        HAVING count > 1
        """)
        dups = cursor.fetchall()

        if dups:
            msg = "Found duplicate entries:\n\n"
            for name, mobile, count in dups:
                msg += f"{name} - {mobile} (Count: {count})\n"
            msg += "\nDo you want to remove duplicates? (Keeps the oldest entry)"

            if messagebox.askyesno("Duplicates Found", msg):
                for name, mobile in [(d[0], d[1]) for d in dups]:
                    cursor.execute("""
                    SELECT id, folder_path FROM customers
                    WHERE name=? AND mobile=?
                    ORDER BY id ASC
                    """, (name, mobile))
                    records = cursor.fetchall()

                    for record_id, folder_path in records[1:]:
                        if os.path.exists(folder_path):
                            try:
                                shutil.rmtree(folder_path)
                            except:
                                pass
                        cursor.execute("DELETE FROM customers WHERE id=?", (record_id,))

                conn.commit()
                self.load_customers()
                self.update_total_dues()
                play_success_sound()
                self.show_feedback("✓ Duplicates removed!", 'success')
        else:
            messagebox.showinfo("No Duplicates", "No duplicate entries found in the database.")

    def export_csv(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialdir=master_folder,
            initialfile=f"customers_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file:
            try:
                cursor.execute("SELECT * FROM customers ORDER BY id")
                with open(file, 'w', encoding='utf-8') as f:
                    f.write("ID,Name,Mobile,Father's Name,Ward,Village,Dues,Folder Path,Created At\n")
                    for row in cursor.fetchall():
                        f.write(",".join([f'"{str(item)}"' for item in row]) + "\n")

                play_success_sound()
                self.show_feedback("✓ Exported to CSV successfully!", 'success')

                if messagebox.askyesno("Export Complete", "Export completed successfully!\n\nDo you want to open the file?"):
                    os.startfile(file)
            except Exception as e:
                play_error_sound()
                messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def backup_db(self):
        backup_folder = config['Paths']['backup_folder']
        os.makedirs(backup_folder, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_path = os.path.join(backup_folder, f"clientdesk_backup_{timestamp}.db")

        try:
            shutil.copy(db_path, backup_path)
            play_success_sound()
            self.show_feedback("✓ Database backed up successfully!", 'success')

            if messagebox.askyesno("Backup Complete",
                                  f"Backup created successfully!\n\nLocation: {backup_path}\n\n"
                                  "Do you want to open the backup folder?"):
                os.startfile(backup_folder)
        except Exception as e:
            play_error_sound()
            messagebox.showerror("Error", f"Failed to create backup: {str(e)}")

    def import_folders(self):
        import_dir = filedialog.askdirectory(title="Select Folder Containing Customer Folders")
        if not import_dir:
            return

        imported = 0
        skipped = 0

        for item in os.listdir(import_dir):
            item_path = os.path.join(import_dir, item)
            if os.path.isdir(item_path):
                match = re.match(r"(.+)_(\d{10})(_.*)?$", item)
                if match:
                    name = match.group(1).replace("_", " ").title()
                    mobile = match.group(2)

                    cursor.execute("SELECT * FROM customers WHERE name=? AND mobile=?", (name, mobile))
                    if not cursor.fetchone():
                        cursor.execute('''
                        INSERT INTO customers (name, mobile, folder_path)
                        VALUES (?, ?, ?)
                        ''', (name, mobile, item_path))
                        imported += 1
                    else:
                        skipped += 1

        conn.commit()
        self.load_customers()
        self.update_total_dues()
        play_success_sound()

        msg = f"Import complete!\n\nImported: {imported}\nSkipped (duplicates): {skipped}"
        messagebox.showinfo("Import Complete", msg)
        self.show_feedback(f"✓ Imported {imported} customers!", 'success')

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        settings_win.geometry(f"{800}x{700}")
        settings_win.configure(bg='#f0f4f8')

        main_frame = ttk.Frame(settings_win, padding=self.padding)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=f"{ICONS['settings']} Settings", style='Title.TLabel').pack(pady=(0, self.padding))

        # Paths section
        paths_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=self.padding)
        paths_frame.pack(fill=tk.X, pady=(0, self.padding))

        ttk.Label(paths_frame, text="Folder Paths", style='Heading.TLabel').pack(anchor=tk.W, pady=(0, self.padding))

        ttk.Label(paths_frame, text="Scanning Folder:", style='CardLabel.TLabel').pack(anchor=tk.W, pady=(0, 5))
        scan_entry = ttk.Entry(paths_frame, width=60)
        scan_entry.insert(0, config['Paths']['scanning_folder'])
        scan_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(paths_frame, text=f"{ICONS['folder']} Browse",
                  command=lambda: self.browse_path(scan_entry),
                  style='Secondary.TButton').pack(anchor=tk.W, pady=(0, self.padding))

        ttk.Label(paths_frame, text="Database Folder:", style='CardLabel.TLabel').pack(anchor=tk.W, pady=(0, 5))
        db_entry = ttk.Entry(paths_frame, width=60)
        db_entry.insert(0, config['Paths']['db_folder'])
        db_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(paths_frame, text=f"{ICONS['folder']} Browse",
                  command=lambda: self.browse_path(db_entry),
                  style='Secondary.TButton').pack(anchor=tk.W, pady=(0, self.padding))

        ttk.Label(paths_frame, text="Backup Folder:", style='CardLabel.TLabel').pack(anchor=tk.W, pady=(0, 5))
        backup_entry = ttk.Entry(paths_frame, width=60)
        backup_entry.insert(0, config['Paths']['backup_folder'])
        backup_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(paths_frame, text=f"{ICONS['folder']} Browse",
                  command=lambda: self.browse_path(backup_entry),
                  style='Secondary.TButton').pack(anchor=tk.W)

        # Lists section
        lists_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=self.padding)
        lists_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(lists_frame, text="Lists Configuration", style='Heading.TLabel').pack(anchor=tk.W, pady=(0, self.padding))

        ttk.Label(lists_frame, text="Wards (comma-separated):", style='CardLabel.TLabel').pack(anchor=tk.W, pady=(0, 5))
        wards_text = tk.Text(lists_frame, height=4, width=60, font=('Segoe UI', self.font_size),
                            bg='#f7fafc', fg='#1e293b', insertbackground='#1e293b',
                            borderwidth=1, relief='solid')
        wards_text.insert(tk.END, config['Lists']['wards'])
        wards_text.pack(fill=tk.X, pady=(0, self.padding))

        ttk.Label(lists_frame, text="Villages (comma-separated):", style='CardLabel.TLabel').pack(anchor=tk.W, pady=(0, 5))
        villages_text = tk.Text(lists_frame, height=6, width=60, font=('Segoe UI', self.font_size),
                               bg='#f7fafc', fg='#1e293b', insertbackground='#1e293b',
                               borderwidth=1, relief='solid')
        villages_text.insert(tk.END, config['Lists']['villages'])
        villages_text.pack(fill=tk.BOTH, expand=True)

        # Save button
        ttk.Button(main_frame, text="Save Settings",
                  style='Success.TButton',
                  command=lambda: self.save_settings(
                      scan_entry.get(),
                      db_entry.get(),
                      backup_entry.get(),
                      wards_text.get("1.0", tk.END).strip(),
                      villages_text.get("1.0", tk.END).strip(),
                      settings_win
                  )).pack(pady=(self.padding, 0), fill=tk.X)

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

        self.village_combo['values'] = villages.split(',')
        win.destroy()
        play_success_sound()
        self.show_feedback("✓ Settings saved successfully!", 'success')

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
                    try:
                        new_path = os.path.join(target_folder, item)
                        if os.path.exists(new_path):
                            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                            new_path = os.path.join(target_folder, f"{item}_{timestamp}")
                        shutil.move(path, new_path)
                        cursor.execute("UPDATE customers SET folder_path=? WHERE folder_path=?",
                                     (new_path, path))
                        conn.commit()
                        moved += 1
                    except Exception as e:
                        print(f"Error moving {item}: {str(e)}")

        self.load_customers()
        play_success_sound()
        self.show_feedback(f"✓ Cleanup complete! Moved {moved} folders.", 'success')
        messagebox.showinfo("Cleanup Complete", f"Moved {moved} folders to:\n{target_folder}")

    def update_total_dues(self):
        cursor.execute("SELECT SUM(dues) FROM customers")
        total = cursor.fetchone()[0] or 0
        self.total_dues_label.config(text=f"Total Dues: ₹{total:,}")

    def show_feedback(self, msg, msg_type='info'):
        feedback_win = tk.Toplevel(self.root)
        feedback_win.overrideredirect(True)
        feedback_win.attributes('-topmost', True)

        color = '#10b981' if msg_type == 'success' else '#ef4444' if msg_type == 'error' else '#2563eb'

        feedback_frame = tk.Frame(feedback_win, bg=color, padx=self.padding*2, pady=self.padding)
        feedback_frame.pack()

        tk.Label(feedback_frame, text=msg, bg=color, fg='#ffffff',
                font=('Segoe UI', self.heading_size, 'bold')).pack()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        feedback_win.update_idletasks()
        x = (screen_width - feedback_win.winfo_width()) // 2
        y = screen_height - 200
        feedback_win.geometry(f"+{x}+{y}")

        self.root.after(2500, feedback_win.destroy)

    def open_full_view(self):
        full_win = tk.Toplevel(self.root)
        full_win.title("Full Database View")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        full_win.geometry(f"{window_width}x{window_height}")

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        full_win.geometry(f"{window_width}x{window_height}+{x}+{y}")

        full_win.configure(bg='#f0f4f8')

        main_frame = ttk.Frame(full_win, padding=self.padding)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=self.padding)
        header_frame.pack(fill=tk.X, pady=(0, self.padding))

        ttk.Label(header_frame, text=f"{ICONS['view']} Full Database View", style='Title.TLabel').pack(side=tk.LEFT)

        search_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=self.padding)
        search_frame.pack(fill=tk.X, pady=(0, self.padding))

        full_search_var = tk.StringVar()
        ttk.Label(search_frame, text=f"{ICONS['check']} Search:", style='CardLabel.TLabel').pack(side=tk.LEFT, padx=(0, self.padding//2))
        search_entry = ttk.Entry(search_frame, textvariable=full_search_var, width=60)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tree_container = ttk.Frame(main_frame, style='Card.TFrame', padding=self.padding)
        tree_container.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(tree_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("ID", "Name", "Mobile", "Father's Name", "Ward", "Village", "Dues", "Folder Path", "Created At")
        full_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        col_widths = {
            "ID": 80,
            "Name": 200,
            "Mobile": 120,
            "Father's Name": 180,
            "Ward": 100,
            "Village": 150,
            "Dues": 100,
            "Folder Path": 250,
            "Created At": 180
        }

        for col in columns:
            full_tree.heading(col, text=col)
            full_tree.column(col, width=col_widths.get(col, 150),
                           anchor=tk.CENTER if col in ["ID", "Dues"] else tk.W)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=full_tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        full_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=full_tree.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        full_tree.configure(xscrollcommand=hsb.set)

        full_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def load_full_view(query=""):
            for item in full_tree.get_children():
                full_tree.delete(item)

            sql = "SELECT * FROM customers"
            params = []

            if query:
                sql += """ WHERE name LIKE ? OR mobile LIKE ? OR father_name LIKE ?
                          OR ward LIKE ? OR village LIKE ? OR CAST(dues AS TEXT) LIKE ?"""
                params = [f"%{query}%"] * 6

            sql += " ORDER BY created_at DESC"

            cursor.execute(sql, params)
            for row in cursor.fetchall():
                full_tree.insert("", tk.END, values=row)

        def open_selected_folder(event):
            selected = full_tree.selection()
            if selected:
                row = full_tree.item(selected[0])['values']
                folder_path = row[7]
                if os.path.exists(folder_path):
                    os.startfile(folder_path)
                else:
                    play_error_sound()
                    messagebox.showerror("Error", "Folder not found!")

        search_entry.bind("<KeyRelease>", lambda e: load_full_view(full_search_var.get()))
        full_tree.bind("<Double-Button-1>", open_selected_folder)

        load_full_view()

    def add_to_recent(self, path):
        if path in self.recent_folders:
            self.recent_folders.remove(path)
        self.recent_folders.insert(0, path)
        if len(self.recent_folders) > 50:
            self.recent_folders = self.recent_folders[:50]
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
            else:
                play_error_sound()
                messagebox.showerror("Error", "Folder not found!")

# Run app
if __name__ == "__main__":
    # Enable High DPI awareness on Windows so text renders sharply on 4K displays
    try:
        if os.name == 'nt':
            # For Windows 8.1+ per-monitor DPI aware
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

    root = tk.Tk()
    app = ClientDeskApp(root)
    root.mainloop()
