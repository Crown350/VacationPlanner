import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database

# --- Configuration & Constants ---
APP_TITLE = "Vacation Planner System"
WINDOW_SIZE = "1200x800"

THEME = {
    "primary": "#2c3e50",
    "secondary": "#34495e",
    "accent": "#3498db",
    "success": "#27ae60",
    "danger": "#e74c3c",
    "bg": "#ecf0f1",
    "card_bg": "#ffffff",
    "text_dark": "#2c3e50",
    "text_light": "#ecf0f1"
}

FONTS = {
    "h1": ("Segoe UI", 24, "bold"),
    "h2": ("Segoe UI", 20, "bold"),
    "h3": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 11),
    "small": ("Segoe UI", 9)
}

# --- Utility Functions ---
def calculate_business_days(start_date: datetime.date, end_date: datetime.date) -> int:
    """Calculates number of business days (Mon-Fri) between two dates inclusive."""
    days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 0-4 are Mon-Fri
            days += 1
        current += timedelta(days=1)
    return days

def format_date_display(date_str: str) -> str:
    """Converts YYYY-MM-DD to DD.MM.YYYY for display."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return str(date_str)

# --- UI Components ---
class AppStyle:
    @staticmethod
    def configure():
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame Styles
        style.configure("Main.TFrame", background=THEME["bg"])
        style.configure("Sidebar.TFrame", background=THEME["primary"])
        style.configure("Card.TFrame", background=THEME["card_bg"], relief="flat")
        
        # Label Styles
        style.configure("Header.TLabel", background=THEME["bg"], foreground=THEME["text_dark"], font=FONTS["h1"])
        style.configure("SubHeader.TLabel", background=THEME["bg"], foreground=THEME["text_dark"], font=FONTS["h3"])
        style.configure("CardLabel.TLabel", background=THEME["card_bg"], foreground=THEME["text_dark"], font=FONTS["body"])
        style.configure("SidebarLabel.TLabel", background=THEME["primary"], foreground=THEME["text_light"], font=FONTS["body"])
        
        # Button Styles
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=10)
        style.map("Accent.TButton", background=[('active', '#2980b9'), ('!disabled', THEME["accent"])], foreground=[('!disabled', 'white')])
        
        style.configure("Success.TButton", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=10)
        style.map("Success.TButton", background=[('active', '#219150'), ('!disabled', THEME["success"])], foreground=[('!disabled', 'white')])
        
        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=10)
        style.map("Danger.TButton", background=[('active', '#c0392b'), ('!disabled', THEME["danger"])], foreground=[('!disabled', 'white')])
        
        style.configure("Sidebar.TButton", font=("Segoe UI", 11), anchor="w", padding=(20, 10), borderwidth=0)
        style.map("Sidebar.TButton", background=[('active', THEME["secondary"]), ('!disabled', THEME["primary"])], foreground=[('!disabled', 'white')])

        # Treeview
        style.configure("Treeview", font=FONTS["body"], rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=THEME["secondary"], foreground="white")

class VacationApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=THEME["bg"])
        
        self.current_user = None
        
        AppStyle.configure()
        database.init_db()
        self.show_login_screen()

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- Authentication ---
    def show_login_screen(self):
        self.clear_root()
        self.root.configure(bg=THEME["primary"])
        
        container = ttk.Frame(self.root, style="Card.TFrame", padding=40)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(container, text="Вход в систему", font=FONTS["h2"], background=THEME["card_bg"], foreground=THEME["primary"]).pack(pady=(0, 20))
        
        ttk.Label(container, text="Логин", style="CardLabel.TLabel").pack(anchor="w")
        self.entry_user = ttk.Entry(container, font=FONTS["body"], width=30)
        self.entry_user.pack(pady=(5, 15))
        
        ttk.Label(container, text="Пароль", style="CardLabel.TLabel").pack(anchor="w")
        self.entry_pass = ttk.Entry(container, show="*", font=FONTS["body"], width=30)
        self.entry_pass.pack(pady=(5, 20))
        
        ttk.Button(container, text="Войти", style="Accent.TButton", command=self.attempt_login, width=30).pack()
        self.root.bind('<Return>', lambda e: self.attempt_login())

    def attempt_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # In production, use parameterized queries to prevent SQL Injection
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and user['password_hash'] == database.hash_password(password):
            self.current_user = dict(user)
            self.root.unbind('<Return>')
            conn.close()
            self.init_dashboard()
        else:
            conn.close()
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

    # --- Main Dashboard ---
    def init_dashboard(self):
        self.clear_root()
        self.root.configure(bg=THEME["bg"])
        
        # Sidebar
        sidebar = ttk.Frame(self.root, style="Sidebar.TFrame", width=260)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        ttk.Label(sidebar, text="Vacation\nPlanner", font=("Segoe UI", 26, "bold"), background=THEME["primary"], foreground="white").pack(pady=40, padx=20, anchor="w")
        
        user_info_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        user_info_frame.pack(fill=tk.X, padx=20, pady=(0, 30))
        ttk.Label(user_info_frame, text=self.current_user['full_name'], style="SidebarLabel.TLabel", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        
        role_map = {'employee': 'Сотрудник', 'manager': 'Руководитель', 'hr': 'HR Менеджер'}
        role_display = role_map.get(self.current_user['role'], 'User').upper()
        ttk.Label(user_info_frame, text=role_display, style="SidebarLabel.TLabel", foreground="#95a5a6", font=("Segoe UI", 9)).pack(anchor="w")

        # Navigation
        self.create_nav_button(sidebar, "Главная", self.route_home)
        self.create_nav_button(sidebar, "Выход", self.logout, is_bottom=True)

        # Content Area
        self.content_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        self.route_home()

    def create_nav_button(self, parent, text, command, is_bottom=False):
        btn = ttk.Button(parent, text=text, command=command, style="Sidebar.TButton")
        if is_bottom:
            btn.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        else:
            btn.pack(fill=tk.X, pady=2)

    def route_home(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        role = self.current_user['role']
        if role == 'employee':
            self.render_employee_dashboard()
        elif role == 'manager':
            self.render_manager_dashboard()
        elif role == 'hr':
            self.render_hr_dashboard()

    def logout(self):
        self.current_user = None
        self.show_login_screen()

    # --- Employee View ---
    def render_employee_dashboard(self):
        header_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Мой отпуск", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Button(header_frame, text="+ Новая заявка", style="Accent.TButton", command=self.open_vacation_dialog).pack(side=tk.RIGHT)

        # Info Cards
        cards_frame = ttk.Frame(self.content_frame, style="Main.TFrame")
        cards_frame.pack(fill=tk.X, pady=(0, 30))
        
        self.create_stat_card(cards_frame, "Доступно дней", str(self.current_user['remaining_vacation_days']), THEME["accent"])
        self.create_stat_card(cards_frame, "Всего дней", str(self.current_user['total_vacation_days']), THEME["secondary"])

        # History Table
        ttk.Label(self.content_frame, text="История заявок", style="SubHeader.TLabel").pack(anchor="w", pady=(0, 10))
        
        cols = ("Начало", "Конец", "Статус")
        tree = self.create_treeview(self.content_frame, cols)
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT start_date, end_date, status FROM vacations WHERE user_id=? ORDER BY start_date DESC", (self.current_user['id'],))
        
        status_map = {'approved': 'Одобрено', 'rejected': 'Отклонено', 'pending': 'На рассмотрении'}
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=(
                format_date_display(row['start_date']),
                format_date_display(row['end_date']),
                status_map.get(row['status'], row['status'])
            ), tags=(row['status'],))
        conn.close()

    def create_stat_card(self, parent, title, value, color):
        card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        card.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(card, text=title, font=("Segoe UI", 10), background=THEME["card_bg"], foreground="#7f8c8d").pack(anchor="w")
        ttk.Label(card, text=value, font=("Segoe UI", 28, "bold"), background=THEME["card_bg"], foreground=color).pack(anchor="w")

    def open_vacation_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Заявка на отпуск")
        dialog.geometry("400x350")
        dialog.configure(bg="white")
        
        pad = 20
        ttk.Label(dialog, text="Даты отпуска", font=FONTS["h3"], background="white", foreground=THEME["primary"]).pack(pady=pad)
        
        form = ttk.Frame(dialog, padding=pad, style="Card.TFrame")
        form.pack()
        
        ttk.Label(form, text="С:", style="CardLabel.TLabel").grid(row=0, column=0, padx=10, pady=10)
        start_entry = DateEntry(form, width=12, background=THEME["primary"], borderwidth=2, date_pattern='dd.mm.yyyy')
        start_entry.grid(row=0, column=1, padx=10)
        
        ttk.Label(form, text="По:", style="CardLabel.TLabel").grid(row=1, column=0, padx=10, pady=10)
        end_entry = DateEntry(form, width=12, background=THEME["primary"], borderwidth=2, date_pattern='dd.mm.yyyy')
        end_entry.grid(row=1, column=1, padx=10)

        def submit():
            try:
                start = datetime.strptime(start_entry.get(), "%d.%m.%Y").date()
                end = datetime.strptime(end_entry.get(), "%d.%m.%Y").date()
                
                if end < start:
                    messagebox.showerror("Ошибка", "Дата окончания не может быть раньше начала")
                    return
                
                duration = calculate_business_days(start, end)
                if duration <= 0:
                    messagebox.showerror("Ошибка", "Выбранный период не содержит рабочих дней")
                    return

                if duration > self.current_user['remaining_vacation_days']:
                    messagebox.showerror("Ошибка", f"Недостаточно дней отпуска. Требуется: {duration}, Доступно: {self.current_user['remaining_vacation_days']}")
                    return
                
                conn = database.get_connection()
                conn.execute(
                    "INSERT INTO vacations (user_id, start_date, end_date, status) VALUES (?, ?, ?, 'pending')",
                    (self.current_user['id'], start, end)
                )
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Успех", "Заявка отправлена на согласование")
                dialog.destroy()
                self.route_home()
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать заявку: {e}")

        ttk.Button(dialog, text="Отправить", style="Accent.TButton", command=submit).pack(pady=pad)

    # --- Manager View ---
    def render_manager_dashboard(self):
        ttk.Label(self.content_frame, text="Управление заявками", style="Header.TLabel").pack(anchor="w", pady=(0, 20))
        
        # Action Bar
        actions = ttk.Frame(self.content_frame, style="Main.TFrame")
        actions.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(actions, text="✓ Согласовать", style="Success.TButton", command=lambda: self.process_request('approved')).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(actions, text="✕ Отклонить", style="Danger.TButton", command=lambda: self.process_request('rejected')).pack(side=tk.LEFT)

        cols = ("ID", "Сотрудник", "Начало", "Конец", "Дней")
        self.mgr_tree = self.create_treeview(self.content_frame, cols)
        
        self.refresh_manager_table()

    def refresh_manager_table(self):
        for item in self.mgr_tree.get_children():
            self.mgr_tree.delete(item)
            
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Show pending requests for users in the same department
        query = """
            SELECT v.id, u.full_name, v.start_date, v.end_date
            FROM vacations v
            JOIN users u ON v.user_id = u.id
            WHERE v.status = 'pending' AND u.department_id = ?
        """
        cursor.execute(query, (self.current_user['department_id'],))
        
        for row in cursor.fetchall():
            s_date = datetime.strptime(row['start_date'], "%Y-%m-%d").date()
            e_date = datetime.strptime(row['end_date'], "%Y-%m-%d").date()
            days = calculate_business_days(s_date, e_date)
            
            self.mgr_tree.insert("", tk.END, values=(
                row['id'], row['full_name'],
                format_date_display(row['start_date']),
                format_date_display(row['end_date']),
                days
            ))
        conn.close()

    def process_request(self, decision):
        selection = self.mgr_tree.selection()
        if not selection:
            messagebox.showinfo("Инфо", "Выберите заявку из списка")
            return
            
        vacation_id = self.mgr_tree.item(selection[0])['values'][0]
        days = int(self.mgr_tree.item(selection[0])['values'][4])
        
        conn = database.get_connection()
        try:
            if decision == 'approved':
                # Deduct days
                user_id_query = conn.execute("SELECT user_id FROM vacations WHERE id=?", (vacation_id,))
                uid = user_id_query.fetchone()['user_id']
                conn.execute("UPDATE users SET remaining_vacation_days = remaining_vacation_days - ? WHERE id=?", (days, uid))
            
            conn.execute("UPDATE vacations SET status=? WHERE id=?", (decision, vacation_id))
            conn.commit()
            self.refresh_manager_table()
            
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Ошибка", str(e))
        finally:
            conn.close()

    # --- HR View ---
    def render_hr_dashboard(self):
        tabs = ttk.Notebook(self.content_frame)
        tabs.pack(fill=tk.BOTH, expand=True)
        
        tab_reports = ttk.Frame(tabs, style="Main.TFrame"); tabs.add(tab_reports, text="  Отчеты  ")
        tab_users = ttk.Frame(tabs, style="Main.TFrame"); tabs.add(tab_users, text="  Сотрудники  ")
        tab_stats = ttk.Frame(tabs, style="Main.TFrame"); tabs.add(tab_stats, text="  Аналитика  ")
        
        self.build_hr_reports(tab_reports)
        self.build_hr_users(tab_users)
        self.build_hr_stats(tab_stats)

    def build_hr_reports(self, parent):
        toolbar = ttk.Frame(parent, style="Main.TFrame", padding=(0, 10))
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="Экспорт в Excel", style="Success.TButton", command=self.export_excel).pack(side=tk.RIGHT)
        
        cols = ("Сотрудник", "Отдел", "Начало", "Конец", "Статус")
        tree = self.create_treeview(parent, cols)
        
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.full_name, d.name as dept, v.start_date, v.end_date, v.status
            FROM vacations v
            JOIN users u ON v.user_id = u.id
            JOIN departments d ON u.department_id = d.id
            ORDER BY v.start_date DESC
        """)
        
        status_map = {'approved': 'Одобрено', 'rejected': 'Отклонено', 'pending': 'На рассмотрении'}
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=(
                row['full_name'], row['dept'],
                format_date_display(row['start_date']),
                format_date_display(row['end_date']),
                status_map.get(row['status'], row['status'])
            ), tags=(row['status'],))
        conn.close()

    def build_hr_users(self, parent):
        toolbar = ttk.Frame(parent, style="Main.TFrame", padding=(0, 10))
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="+ Добавить сотрудника", style="Accent.TButton", command=self.add_user_dialog).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Удалить выбранного", style="Danger.TButton", command=lambda: self.delete_user_action(tree)).pack(side=tk.RIGHT)

        cols = ("ID", "ФИО", "Логин", "Роль", "Отдел", "Должность")
        tree = self.create_treeview(parent, cols)
        
        # Load users
        users = database.get_all_users_with_details()
        role_map = {'employee': 'Сотрудник', 'manager': 'Руководитель', 'hr': 'HR'}
        
        for user in users:
            tree.insert("", tk.END, values=(
                user['id'], user['full_name'], user['username'],
                role_map.get(user['role'], user['role']),
                user['dept_name'], user['pos_title']
            ))

    def add_user_dialog(self):
        # Simplification: Only showing stub, full implementation would mirror previous logic but cleaner
        messagebox.showinfo("Info", "Форма добавления сотрудника (Реализовать аналогично заявкам)")

    def delete_user_action(self, tree):
        sel = tree.selection()
        if not sel: return
        
        uid = tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Подтверждение", "Удалить сотрудника и все его данные?"):
            database.delete_user(uid)
            tree.delete(sel[0])

    def build_hr_stats(self, parent):
        conn = database.get_connection()
        query = """
            SELECT d.name, COUNT(v.id) as count
            FROM vacations v
            JOIN users u ON v.user_id = u.id
            JOIN departments d ON u.department_id = d.id
            WHERE v.status = 'approved'
            GROUP BY d.name
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            ttk.Label(parent, text="Нет данных для статистики", style="SubHeader.TLabel").pack(pady=20)
            return

        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        df.plot(kind='bar', x='name', y='count', ax=ax, color=THEME["accent"], legend=False)
        
        ax.set_title("Одобренные отпуска по отделам", fontsize=12)
        ax.set_xlabel("Отдел")
        ax.set_ylabel("Количество")
        plt.subplots_adjust(bottom=0.25)
        plt.xticks(rotation=45, ha='right')
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def export_excel(self):
        try:
            conn = database.get_connection()
            df = pd.read_sql_query("SELECT * FROM vacations", conn)
            conn.close()
            filename = f"report_{datetime.now().strftime('%Y%m%d')}.xlsx"
            df.to_excel(filename, index=False)
            messagebox.showinfo("Успех", f"Отчет сохранен: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")

    def create_treeview(self, parent, columns):
        tree = ttk.Treeview(parent, columns=columns, show="headings", style="Treeview")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        tree.tag_configure('approved', foreground=THEME["success"])
        tree.tag_configure('rejected', foreground=THEME["danger"])
        tree.tag_configure('pending', foreground="#d35400")
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

if __name__ == "__main__":
    root = tk.Tk()
    app = VacationApp(root)
    root.mainloop()
