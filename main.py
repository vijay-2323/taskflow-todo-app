import sqlite3
import tkinter as tk
from tkinter import messagebox
from datetime import date
import customtkinter as ctk


# ==================== CONFIGURATION ====================

APP_NAME = "TaskFlow"
DATABASE_NAME = "tasks.db"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ==================== DATABASE ====================

class TaskDatabase:
    def __init__(self, database_name=DATABASE_NAME):
        self.connection = sqlite3.connect(database_name)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT DEFAULT 'Medium',
                due_date TEXT DEFAULT '',
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()

    def get_tasks(self, search=""):
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT id, title, description, priority,
                   due_date, completed
            FROM tasks
            WHERE title LIKE ?
            ORDER BY completed ASC, id DESC
        """, (f"%{search}%",))

        return cursor.fetchall()

    def add_task(self, title, description, priority, due_date):
        self.connection.execute("""
            INSERT INTO tasks (title, description, priority, due_date)
            VALUES (?, ?, ?, ?)
        """, (title, description, priority, due_date))

        self.connection.commit()

    def update_task_status(self, task_id, completed):
        self.connection.execute("""
            UPDATE tasks SET completed = ?
            WHERE id = ?
        """, (int(completed), task_id))

        self.connection.commit()

    def delete_task(self, task_id):
        self.connection.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )
        self.connection.commit()

    def close(self):
        self.connection.close()


# ==================== MAIN APPLICATION ====================

class TaskFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TaskFlow | Smart To-Do Manager")
        self.geometry("1050x720")
        self.minsize(850, 600)

        self.database = TaskDatabase()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()
        self.refresh_tasks()

    # ==================== SIDEBAR ====================

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="✦ TaskFlow",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(padx=20, pady=(35, 8))

        ctk.CTkLabel(
            self.sidebar,
            text="YOUR PERSONAL WORKSPACE",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(pady=(0, 35))

        ctk.CTkButton(
            self.sidebar,
            text="＋  Add New Task",
            height=42,
            command=self.open_add_task
        ).pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(
            self.sidebar,
            text="↻  Refresh Tasks",
            height=42,
            fg_color="transparent",
            border_width=1,
            command=self.refresh_tasks
        ).pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(
            self.sidebar,
            text="Stay focused.\nGet things done.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(side="bottom", pady=30)

    # ==================== MAIN AREA ====================

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color="transparent"
        )
        self.main_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=28,
            pady=24
        )

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self.main_frame,
            text="Good day! 👋",
            font=ctk.CTkFont(size=30, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        ctk.CTkLabel(
            self.main_frame,
            text=f"Today is {date.today().strftime('%B %d, %Y')}",
            text_color="gray",
            font=ctk.CTkFont(size=14)
        ).grid(row=1, column=0, sticky="w", pady=(0, 20))

        self.stats_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        self.stats_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 20)
        )

        for column in range(3):
            self.stats_frame.grid_columnconfigure(column, weight=1)

        self.total_label = self.create_stat_card(
            0, "TOTAL TASKS", "0", "#2563EB"
        )
        self.pending_label = self.create_stat_card(
            1, "PENDING", "0", "#D97706"
        )
        self.completed_label = self.create_stat_card(
            2, "COMPLETED", "0", "#059669"
        )

        self.task_area = ctk.CTkFrame(
            self.main_frame,
            corner_radius=12
        )
        self.task_area.grid(
            row=3,
            column=0,
            sticky="nsew"
        )

        self.task_area.grid_columnconfigure(0, weight=1)
        self.task_area.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self.task_area,
            text="Your Tasks",
            font=ctk.CTkFont(size=21, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 10))

        self.search_entry = ctk.CTkEntry(
            self.task_area,
            placeholder_text="Search tasks...",
            height=38
        )
        self.search_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 12)
        )
        self.search_entry.bind(
            "<KeyRelease>",
            lambda event: self.refresh_tasks()
        )

        self.task_list = ctk.CTkScrollableFrame(
            self.task_area,
            fg_color="transparent"
        )
        self.task_list.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=12,
            pady=(0, 12)
        )

    # ==================== STATISTICS ====================

    def create_stat_card(self, column, title, value, color):
        card = ctk.CTkFrame(
            self.stats_frame,
            corner_radius=12
        )
        card.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=(0 if column == 0 else 6, 6)
        )

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=14, pady=(15, 5))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=27, weight="bold"),
            text_color=color
        )
        value_label.pack(anchor="w", padx=14, pady=(0, 14))

        return value_label

    # ==================== ADD TASK ====================

    def open_add_task(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create New Task")
        dialog.geometry("430x470")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Create a New Task",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(25, 20))

        title_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="Task title",
            width=340,
            height=40
        )
        title_entry.pack(pady=8)
        title_entry.focus_set()

        description_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="Description (optional)",
            width=340,
            height=40
        )
        description_entry.pack(pady=8)

        priority_menu = ctk.CTkOptionMenu(
            dialog,
            values=["Low", "Medium", "High"],
            width=340
        )
        priority_menu.set("Medium")
        priority_menu.pack(pady=8)

        due_date_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="Due date (YYYY-MM-DD)",
            width=340,
            height=40
        )
        due_date_entry.pack(pady=8)

        def save():
            title = title_entry.get().strip()
            description = description_entry.get().strip()
            priority = priority_menu.get()
            due_date = due_date_entry.get().strip()

            if not title:
                messagebox.showwarning(
                    "Missing title",
                    "Please enter a task title.",
                    parent=dialog
                )
                return

            if due_date:
                try:
                    date.fromisoformat(due_date)
                except ValueError:
                    messagebox.showwarning(
                        "Invalid date",
                        "Use the YYYY-MM-DD date format.",
                        parent=dialog
                    )
                    return

            try:
                self.database.add_task(
                    title, description, priority, due_date
                )
                self.refresh_tasks()
                dialog.destroy()
            except sqlite3.Error as error:
                messagebox.showerror(
                    "Database Error", str(error), parent=dialog
                )

        ctk.CTkButton(
            dialog,
            text="Save Task",
            width=340,
            height=42,
            command=save
        ).pack(pady=20)

    # ==================== TASK LIST ====================

    def refresh_tasks(self):
        for widget in self.task_list.winfo_children():
            widget.destroy()

        search = self.search_entry.get().strip()

        try:
            tasks = self.database.get_tasks(search)
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))
            return

        total = len(tasks)
        completed = sum(task[5] for task in tasks)
        pending = total - completed

        self.total_label.configure(text=str(total))
        self.pending_label.configure(text=str(pending))
        self.completed_label.configure(text=str(completed))

        if not tasks:
            ctk.CTkLabel(
                self.task_list,
                text="No tasks found. Add your first task!",
                text_color="gray",
                font=ctk.CTkFont(size=15)
            ).pack(pady=40)
            return

        for task in tasks:
            self.create_task_card(task)

    def create_task_card(self, task):
        task_id, title, description, priority, due_date, completed = task

        card = ctk.CTkFrame(
            self.task_list,
            corner_radius=10
        )
        card.pack(fill="x", padx=4, pady=6)

        card.grid_columnconfigure(1, weight=1)

        checkbox = ctk.CTkCheckBox(
            card,
            text="",
            width=25,
            command=lambda: self.toggle_task(
                task_id, checkbox.get()
            )
        )
        checkbox.grid(row=0, column=0, rowspan=2, padx=12, pady=12)

        if completed:
            checkbox.select()

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title_label.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=4,
            pady=(12, 2)
        )

        details = f"{priority} Priority"

        if due_date:
            details += f"  •  Due: {due_date}"

        if description:
            details += f"  •  {description}"

        ctk.CTkLabel(
            card,
            text=details,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=4,
            pady=(0, 12)
        )

        if completed:
            title_label.configure(text_color="gray")

        ctk.CTkButton(
            card,
            text="Delete",
            width=65,
            height=30,
            fg_color="#B91C1C",
            hover_color="#991B1B",
            command=lambda: self.delete_task(task_id)
        ).grid(
            row=0,
            column=2,
            rowspan=2,
            padx=12,
            pady=10
        )

    # ==================== TASK ACTIONS ====================

    def toggle_task(self, task_id, completed):
        try:
            self.database.update_task_status(task_id, completed)
            self.refresh_tasks()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def delete_task(self, task_id):
        confirmed = messagebox.askyesno(
            "Delete Task",
            "Are you sure you want to delete this task?"
        )

        if not confirmed:
            return

        try:
            self.database.delete_task(task_id)
            self.refresh_tasks()
        except sqlite3.Error as error:
            messagebox.showerror("Database Error", str(error))

    def on_close(self):
        self.database.close()
        self.destroy()


# ==================== APPLICATION ENTRY POINT ====================

if __name__ == "__main__":
    app = TaskFlowApp()
    app.mainloop()