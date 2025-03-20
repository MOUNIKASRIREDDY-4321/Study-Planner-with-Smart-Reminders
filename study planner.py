import tkinter as tk
from tkinter import messagebox
import sqlite3
import datetime
from plyer import notification
import time
import threading

# Create and connect to database in main thread
conn = sqlite3.connect("study_planner.db")
cursor = conn.cursor()

# Create table for tasks with added_on column
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT,
    task TEXT,
    deadline TEXT,
    added_on TEXT DEFAULT CURRENT_DATE,
    completed INTEGER DEFAULT 0
)""")
conn.commit()


def add_task():
    subject = subject_entry.get()
    task = task_entry.get()
    deadline = deadline_entry.get()
    if subject and task and deadline:
        cursor.execute("INSERT INTO tasks (subject, task, deadline, added_on) VALUES (?, ?, ?, CURRENT_DATE)",
                       (subject, task, deadline))
        conn.commit()
        subject_entry.delete(0, tk.END)
        task_entry.delete(0, tk.END)
        deadline_entry.delete(0, tk.END)
        show_tasks()
    else:
        messagebox.showwarning("Input Error", "Please fill all fields")


def show_tasks():
    task_list.delete(0, tk.END)
    cursor.execute("SELECT id, subject, task, deadline, completed FROM tasks ORDER BY deadline ASC")
    tasks = cursor.fetchall()
    for task in tasks:
        status = "✔ Done" if task[4] else "❌ Pending"
        task_list.insert(tk.END, f"{task[0]} | {task[1]} | {task[2]} | Due: {task[3]} | {status}")


def delete_task():
    try:
        selected_task = task_list.get(task_list.curselection())
        task_id = selected_task.split(" | ")[0]
        cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        show_tasks()
    except:
        messagebox.showwarning("Selection Error", "Please select a task to delete")


def mark_as_done():
    try:
        selected_task = task_list.get(task_list.curselection())
        task_id = selected_task.split(" | ")[0]
        cursor.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
        conn.commit()
        show_tasks()
    except:
        messagebox.showwarning("Selection Error", "Please select a task to mark as done")


def send_reminders():
    # Create a new connection inside this function to avoid thread issues
    db_conn = sqlite3.connect("study_planner.db")
    db_cursor = db_conn.cursor()

    db_cursor.execute("SELECT subject, task, deadline FROM tasks WHERE completed=0")
    tasks = db_cursor.fetchall()
    today = datetime.date.today()

    for task in tasks:
        deadline_date = datetime.datetime.strptime(task[2], "%Y-%m-%d").date()
        days_left = (deadline_date - today).days

        if days_left == 1 or (days_left < 1 and deadline_date >= today - datetime.timedelta(days=1)):
            notification.notify(
                title="Study Reminder",
                message=f"⚠ {task[0]}: {task[1]} was due on {task[2]}!",
                timeout=10
            )

    db_conn.close()  # Close connection after checking


def schedule_reminders():
    while True:
        send_reminders()
        time.sleep(86400)  # Wait 24 hours before running again


def start_reminder_thread():
    thread = threading.Thread(target=schedule_reminders, daemon=True)
    thread.start()


# GUI Layout
root = tk.Tk()
root.title("Study Planner with Smart Reminders")
root.geometry("500x500")

tk.Label(root, text="Subject:").pack()
subject_entry = tk.Entry(root)
subject_entry.pack()

tk.Label(root, text="Task:").pack()
task_entry = tk.Entry(root)
task_entry.pack()

tk.Label(root, text="Deadline (YYYY-MM-DD):").pack()
deadline_entry = tk.Entry(root)
deadline_entry.pack()

tk.Button(root, text="Add Task", command=add_task).pack()
tk.Button(root, text="Delete Task", command=delete_task).pack()
tk.Button(root, text="Mark as Done", command=mark_as_done).pack()
tk.Button(root, text="Check Reminders", command=send_reminders).pack()

task_list = tk.Listbox(root, width=70, height=15)
task_list.pack()

show_tasks()  # Load tasks when app starts
start_reminder_thread()  # Start automatic reminders

root.mainloop()
conn.close()