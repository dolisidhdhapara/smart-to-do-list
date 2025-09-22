import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, List, Callable
from task_manager import TaskManager, Task
from api_handler import APIHandler
from exceptions import TaskParsingError, TaskNotFoundError

# Appearance
ctk.set_appearance_mode("system")  
ctk.set_default_color_theme("blue") 

class TaskFrame(ctk.CTkFrame):
    
    def __init__(self, parent, task: Task, on_complete: Callable, on_edit: Callable, on_delete: Callable):
        super().__init__(parent)
        
        self.task = task
        self.on_complete = on_complete
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        self.create_widgets()
    
    def create_widgets(self):
        task_name = self.task.task_name
        if len(task_name) > 50:
            task_name = task_name[:50] + "..."
        
        status_symbol = "✓" if self.task.completed else "○"
        priority_symbol = {"High": "!", "Medium": "-", "Low": "~"}.get(self.task.priority, "-")
        
        display_text = f"{status_symbol} {task_name} [{priority_symbol}]"
        
        self.name_label = ctk.CTkLabel(
            self, 
            text=display_text,
            font=ctk.CTkFont(size=12, weight="bold" if not self.task.completed else "normal"),
            text_color="gray" if self.task.completed else None
        )
        self.name_label.grid(row=0, column=0, sticky="w", padx=8, pady=(5, 1))
        
        info_parts = []
        if self.task.due_date:
            due_text = self.task.due_date
            if self.task.due_time:
                due_text += f" {self.task.due_time}"
            color = "red" if self.task.is_overdue() and not self.task.completed else "gray"
            info_parts.append((f"Due: {due_text}", color))
        
        priority_color = {"High": "red", "Medium": "orange", "Low": "green"}.get(self.task.priority, "gray")
        info_parts.append((f"{self.task.priority}", priority_color))
        
        if info_parts:
            info_text = " | ".join([part[0] for part in info_parts])
            text_color = info_parts[0][1] if len(info_parts) > 1 else priority_color
            
            self.info_label = ctk.CTkLabel(
                self, 
                text=info_text,
                font=ctk.CTkFont(size=10),
                text_color=text_color
            )
            self.info_label.grid(row=1, column=0, sticky="w", padx=8, pady=1)
        
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=0, column=1, sticky="e", padx=8, pady=2)
        
        if not self.task.completed:
            self.complete_btn = ctk.CTkButton(
                buttons_frame,
                text="✓",
                command=self.complete_task,
                width=20,
                height=20,
                fg_color="green",
                hover_color="darkgreen",
                font=ctk.CTkFont(size=10)
            )
            self.complete_btn.pack(side="right", padx=(2, 0))
        
        self.edit_btn = ctk.CTkButton(
            buttons_frame,
            text="✏",
            command=self.edit_task,
            width=20,
            height=20,
            fg_color="orange",
            hover_color="darkorange",
            font=ctk.CTkFont(size=10)
        )
        self.edit_btn.pack(side="right", padx=(2, 2))
        
        self.delete_btn = ctk.CTkButton(
            buttons_frame,
            text="✕",
            command=self.delete_task,
            width=20,
            height=20,
            fg_color="red",
            hover_color="darkred",
            font=ctk.CTkFont(size=10)
        )
        self.delete_btn.pack(side="right", padx=(2, 2))
        
        self.grid_columnconfigure(1, weight=1)
    
    def complete_task(self):
        self.on_complete(self.task.id)
    
    def edit_task(self):
        self.on_edit(self.task.id)
    
    def delete_task(self):
        result = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.task.task_name}'?")
        if result:
            self.on_delete(self.task.id)

class AddTaskDialog(ctk.CTkToplevel):
    
    def __init__(self, parent, task: Optional[Task] = None):
        super().__init__(parent)
        
        self.task = task
        self.result = None
        
        self.title("Edit Task" if task else "Add New Task")
        self.geometry("500x400")
        self.transient(parent)
        
        self.update_idletasks()
        self.after(100, self._setup_grab)
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"500x400+{x}+{y}")
        
        self.create_widgets()
        
        if task:
            self.populate_fields()
    
    def _setup_grab(self):
        try:
            self.grab_set()
        except tk.TclError:
            pass
    
    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.name_label = ctk.CTkLabel(main_frame, text="Task Name:", font=ctk.CTkFont(weight="bold"))
        self.name_label.pack(anchor="w", pady=(10, 5))
        
        self.name_entry = ctk.CTkEntry(main_frame, height=35, placeholder_text="Enter task name or use natural language")
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        self.date_label = ctk.CTkLabel(main_frame, text="Due Date (YYYY-MM-DD):", font=ctk.CTkFont(weight="bold"))
        self.date_label.pack(anchor="w", pady=(0, 5))
        
        self.date_entry = ctk.CTkEntry(main_frame, height=35, placeholder_text="e.g., 2024-12-25 or leave empty")
        self.date_entry.pack(fill="x", pady=(0, 15))
        
        self.time_label = ctk.CTkLabel(main_frame, text="Due Time:", font=ctk.CTkFont(weight="bold"))
        self.time_label.pack(anchor="w", pady=(0, 5))
        
        self.time_entry = ctk.CTkEntry(main_frame, height=35, placeholder_text="e.g., 2:30 PM or 14:30")
        self.time_entry.pack(fill="x", pady=(0, 15))
        
        self.priority_label = ctk.CTkLabel(main_frame, text="Priority:", font=ctk.CTkFont(weight="bold"))
        self.priority_label.pack(anchor="w", pady=(0, 5))
        
        self.priority_var = ctk.StringVar(value="Medium")
        self.priority_menu = ctk.CTkOptionMenu(
            main_frame,
            variable=self.priority_var,
            values=["High", "Medium", "Low"],
            height=35
        )
        self.priority_menu.pack(fill="x", pady=(0, 20))
        
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 10))
        
        self.cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=self.cancel,
            fg_color="gray",
            hover_color="darkgray"
        )
        self.cancel_btn.pack(side="right", padx=(10, 0))
        
        self.save_btn = ctk.CTkButton(
            buttons_frame,
            text="Save Task",
            command=self.save_task,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.save_btn.pack(side="right")
        
        self.parse_btn = ctk.CTkButton(
            buttons_frame,
            text="Parse Natural Language",
            command=self.parse_natural_language,
            fg_color="blue",
            hover_color="darkblue"
        )
        self.parse_btn.pack(side="left")
        
        self.name_entry.focus()
    
    def populate_fields(self):
        if self.task:
            self.name_entry.insert(0, self.task.task_name)
            if self.task.due_date:
                self.date_entry.insert(0, self.task.due_date)
            if self.task.due_time:
                self.time_entry.insert(0, self.task.due_time)
            self.priority_var.set(self.task.priority)
    
    def parse_natural_language(self):
        input_text = self.name_entry.get().strip()
        if not input_text:
            messagebox.showwarning("Warning", "Please enter some text to parse.")
            return
        
        try:
            from nlp_parser import NLPParser
            parser = NLPParser()
            parsed_data = parser.parse_task(input_text)
            
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, parsed_data.get('task_name', input_text))
            
            if parsed_data.get('due_date'):
                self.date_entry.delete(0, "end")
                self.date_entry.insert(0, parsed_data['due_date'])
            
            if parsed_data.get('due_time'):
                self.time_entry.delete(0, "end")
                self.time_entry.insert(0, parsed_data['due_time'])
            
            if parsed_data.get('priority'):
                self.priority_var.set(parsed_data['priority'] or 'Medium')
            
            messagebox.showinfo("Success", "Task details parsed successfully!")
            
        except Exception as e:
            messagebox.showerror("Parse Error", f"Failed to parse natural language: {str(e)}")
    
    def save_task(self):
        task_name = self.name_entry.get().strip()
        if not task_name:
            messagebox.showwarning("Warning", "Task name is required.")
            return
        
        due_date = self.date_entry.get().strip() or None
        due_time = self.time_entry.get().strip() or None
        priority = self.priority_var.get()
        
        self.result = {
            'task_name': task_name,
            'due_date': due_date,
            'due_time': due_time,
            'priority': priority
        }
        
        self.destroy()
    
    def cancel(self):
        self.destroy()

class QuoteDialog(ctk.CTkToplevel):
    
    def __init__(self, parent, quote: str):
        super().__init__(parent)
        
        self.title("Motivational Quote")
        self.geometry("450x200")
        self.transient(parent)
        
        # Center the dialog
        self.update_idletasks()
        # Set up grab after dialog is visible
        self.after(100, self._setup_grab_quote)
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (200 // 2)
        self.geometry(f"450x200+{x}+{y}")
        
        self.create_widgets(quote)
    
    def create_widgets(self, quote: str):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        quote_label = ctk.CTkLabel(
            main_frame,
            text=quote,
            font=ctk.CTkFont(size=14, slant="italic"),
            wraplength=400,
            justify="center"
        )
        quote_label.pack(expand=True, pady=20)
        
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=self.destroy,
            fg_color="blue",
            hover_color="darkblue"
        )
        close_btn.pack(pady=(0, 10))
    
    def _setup_grab_quote(self):
        try:
            self.grab_set()
        except tk.TclError:
            pass

class SmartToDoGUI(ctk.CTk):
    
    def __init__(self):
        super().__init__()
        
        self.title("Smart To-Do List")
        self.geometry("1000x700")
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1000x700+{x}+{y}")
        
        self.task_manager = TaskManager()
        self.api_handler = APIHandler()
        
        self.current_filter = "all"
        
        self.create_widgets()
        self.refresh_tasks()
    
    def create_widgets(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Smart To-Do List",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        add_frame = ctk.CTkFrame(main_frame)
        add_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        add_label = ctk.CTkLabel(add_frame, text="Quick Add Task:", font=ctk.CTkFont(weight="bold"))
        add_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        input_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.task_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="e.g., 'Submit report by Friday 5pm' or 'Call mom tomorrow at 10am'",
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.add_btn = ctk.CTkButton(
            input_frame,
            text="Add Task",
            command=self.add_task_quick,
            height=40,
            width=100,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.add_btn.pack(side="right")
        
        self.task_entry.bind("<Return>", lambda e: self.add_task_quick())
        
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        buttons_left = ctk.CTkFrame(control_frame, fg_color="transparent")
        buttons_left.pack(side="left", fill="x", expand=True, padx=15, pady=15)
        
        self.detailed_add_btn = ctk.CTkButton(
            buttons_left,
            text="Detailed Add",
            command=self.add_task_detailed,
            fg_color="blue",
            hover_color="darkblue"
        )
        self.detailed_add_btn.pack(side="left", padx=(0, 10))
        
        self.refresh_btn = ctk.CTkButton(
            buttons_left,
            text="Refresh",
            command=self.refresh_tasks,
            fg_color="orange",
            hover_color="darkorange"
        )
        self.refresh_btn.pack(side="left", padx=(0, 10))
        
        self.stats_btn = ctk.CTkButton(
            buttons_left,
            text="Statistics",
            command=self.show_statistics,
            fg_color="purple",
            hover_color="#800080"
        )
        self.stats_btn.pack(side="left")
        
        filter_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        filter_frame.pack(side="right", padx=15, pady=15)
        
        filter_label = ctk.CTkLabel(filter_frame, text="Filter:", font=ctk.CTkFont(weight="bold"))
        filter_label.pack(side="left", padx=(0, 10))
        
        filters = [
            ("All", "all"),
            ("Pending", "pending"),
            ("Completed", "completed"),
            ("Overdue", "overdue"),
            ("Today", "today")
        ]
        
        for text, filter_type in filters:
            btn = ctk.CTkButton(
                filter_frame,
                text=text,
                command=lambda f=filter_type: self.set_filter(f),
                width=70,
                height=30,
                fg_color="gray" if filter_type != self.current_filter else "blue"
            )
            btn.pack(side="left", padx=2)
        
        tasks_container = ctk.CTkFrame(main_frame)
        tasks_container.pack(fill="both", expand=True, padx=20)
        
        self.tasks_scroll = ctk.CTkScrollableFrame(tasks_container, height=300)
        self.tasks_scroll.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.pack(pady=(10, 20))
    
    def add_task_quick(self):
        input_text = self.task_entry.get().strip()
        if not input_text:
            messagebox.showwarning("Warning", "Please enter a task.")
            return
        
        try:
            task = self.task_manager.add_task_from_text(input_text)
            self.task_entry.delete(0, "end")
            self.refresh_tasks()
            self.show_motivational_quote()
            self.update_status(f"Task '{task.task_name}' added successfully!")
        except TaskParsingError as e:
            messagebox.showerror("Error", str(e))
    
    def add_task_detailed(self):
        dialog = AddTaskDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            task = self.task_manager.add_task(**dialog.result)
            self.refresh_tasks()
            self.show_motivational_quote()
            self.update_status(f"Task '{task.task_name}' added successfully!")
    
    def complete_task(self, task_id: str):
        try:
            task = self.task_manager.complete_task(task_id)
            self.refresh_tasks()
            self.show_motivational_quote()
            self.update_status(f"Task '{task.task_name}' completed!")
        except TaskNotFoundError as e:
            messagebox.showerror("Error", str(e))
    
    def edit_task(self, task_id: str):
        try:
            task = self.task_manager.get_task(task_id)
            dialog = AddTaskDialog(self, task)
            self.wait_window(dialog)
            
            if dialog.result:
                updated_task = self.task_manager.update_task(task_id, **dialog.result)
                self.refresh_tasks()
                self.update_status(f"Task '{updated_task.task_name}' updated!")
        except TaskNotFoundError as e:
            messagebox.showerror("Error", str(e))
    
    def delete_task(self, task_id: str):
        try:
            task = self.task_manager.get_task(task_id)
            self.task_manager.delete_task(task_id)
            self.refresh_tasks()
            self.update_status(f"Task '{task.task_name}' deleted!")
        except TaskNotFoundError as e:
            messagebox.showerror("Error", str(e))
    
    def set_filter(self, filter_type: str):
        self.current_filter = filter_type
        self.refresh_tasks()
        
        pass
    
    def refresh_tasks(self):
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()
        
        if self.current_filter == "all":
            tasks = self.task_manager.get_all_tasks()
        elif self.current_filter == "pending":
            tasks = self.task_manager.get_pending_tasks()
        elif self.current_filter == "completed":
            tasks = self.task_manager.get_completed_tasks()
        elif self.current_filter == "overdue":
            tasks = self.task_manager.get_overdue_tasks()
        elif self.current_filter == "today":
            tasks = self.task_manager.get_today_tasks()
        else:
            tasks = self.task_manager.get_all_tasks()
        
        def sort_key(task):
            priority_order = {"High": 0, "Medium": 1, "Low": 2}
            overdue_score = 0 if task.is_overdue() and not task.completed else 1
            due_date_score = task.due_date if task.due_date else "9999-99-99"
            priority_score = priority_order.get(task.priority, 1)
            return (overdue_score, due_date_score, priority_score)
        
        tasks.sort(key=sort_key)
        
        if not tasks:
            no_tasks_label = ctk.CTkLabel(
                self.tasks_scroll,
                text=f"No {self.current_filter} tasks found.",
                font=ctk.CTkFont(size=16),
                text_color="gray"
            )
            no_tasks_label.pack(pady=50)
        else:
            for task in tasks:
                task_frame = TaskFrame(
                    self.tasks_scroll,
                    task,
                    self.complete_task,
                    self.edit_task,
                    self.delete_task
                )
                task_frame.pack(fill="x", pady=1, padx=5)
        
        filter_name = self.current_filter.capitalize()
        self.update_status(f"Showing {len(tasks)} {filter_name} task(s)")
    
    def show_motivational_quote(self):
        """Show a motivational quote in a dialog."""
        def show_quote(quote):
            try:
                QuoteDialog(self, quote)
            except:
                pass  
        
        self.api_handler.get_motivational_quote(callback=show_quote)
    
    def show_statistics(self):
        stats = self.task_manager.get_task_stats()
        
        stats_text = f"""Task Statistics
        
Total Tasks: {stats['total']}
Pending Tasks: {stats['pending']}
Completed Tasks: {stats['completed']}
Overdue Tasks: {stats['overdue']}
Due Today: {stats['due_today']}

Completion Rate: {(stats['completed'] / max(stats['total'], 1) * 100):.1f}%"""
        
        messagebox.showinfo("Task Statistics", stats_text)
    
    def update_status(self, message: str):
        self.status_label.configure(text=message)
        self.after(5000, lambda: self.status_label.configure(text="Ready"))

def main():
    try:
        app = SmartToDoGUI()
        app.mainloop()
    except Exception as e:
        print(f"Application error: {e}")

if __name__ == "__main__":
    main()