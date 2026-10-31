
import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import hashlib
import os

# DATABASE
db = sqlite3.connect("habits.db")
db.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT
)""")
db.execute("""CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    name TEXT,
    done INTEGER DEFAULT 0
)""")
db.commit()

user_id = None


def password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


def clear():
    for widget in root.winfo_children():
        widget.destroy()


def register():
    clear()
    tk.Label(root, text="REGISTER",
             font=("Arial", 22, "bold")).pack(pady=15)

    tk.Label(root, text="Username").pack()
    username = tk.Entry(root)
    username.pack()

    tk.Label(root, text="Password").pack()
    password = tk.Entry(root, show="*")
    password.pack()

    def save():
        u, p = username.get().strip(), password.get()
        if not u or not p:
            messagebox.showerror("Error", "Fill in all fields")
            return
        if len(p) < 6:
            messagebox.showerror("Error", "Password needs 6 characters")
            return
        try:
            db.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (u, password_hash(p))
            )
            db.commit()
            messagebox.showinfo("Success", "Account created!")
            login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")

    tk.Button(root, text="Create Account",
              command=save).pack(pady=10)
    tk.Button(root, text="Back to Login",
              command=login).pack()


def login():
    clear()
    tk.Label(root, text="MY DAILY HABITS",
             font=("Arial", 22, "bold"),
             fg="#145b4b").pack(pady=20)

    tk.Label(root, text="Username").pack()
    username = tk.Entry(root)
    username.pack()

    tk.Label(root, text="Password").pack()
    password = tk.Entry(root, show="*")
    password.pack()

    def check():
        global user_id
        row = db.execute(
            "SELECT id FROM users WHERE username=? AND password=?",
            (username.get().strip(), password_hash(password.get()))
        ).fetchone()

        if row:
            user_id = row[0]
            tracker()
        else:
            messagebox.showerror(
                "Login Failed", "Incorrect username or password"
            )

    tk.Button(root, text="LOGIN", command=check,
              width=20, bg="#16866e", fg="white").pack(pady=12)
    tk.Button(root, text="Register New Account",
              command=register).pack()


def tracker():
    clear()
    root.configure(bg="#f1f0ec")

    header = tk.Frame(root, bg="#103d35")
    header.pack(fill="x")

    tk.Label(header, text="My Daily Habits",
             font=("Arial", 22, "bold"),
             bg="#103d35", fg="white").pack(
                 side="left", padx=15, pady=15)

    tk.Button(header, text="Log Out",
              command=login).pack(side="right", padx=10)

    tk.Button(header, text="+ Add Habit",
              command=add_habit).pack(side="right", padx=5)

    tk.Label(root, text="WEEKLY HABIT TRACKER",
             font=("Arial", 15, "bold"),
             bg="#f1f0ec").pack(pady=10)

    global habit_frame
    habit_frame = tk.Frame(root, bg="#f1f0ec")
    habit_frame.pack(fill="both", expand=True, padx=10)

    tk.Label(habit_frame, text="HABIT",
             width=20, relief="ridge").grid(row=0, column=0)

    for i, day in enumerate(
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], 1
    ):
        tk.Label(habit_frame, text=day,
                 width=8, relief="ridge").grid(row=0, column=i)

    tk.Button(root, text="Delete Selected Habit",
              command=delete_habit).pack(pady=5)

    refresh()


def refresh():
    for widget in habit_frame.grid_slaves():
        if int(widget.grid_info()["row"]) > 0:
            widget.destroy()

    habits = db.execute(
        "SELECT id,name,done FROM habits WHERE user_id=?",
        (user_id,)
    ).fetchall()

    for row, (hid, name, done) in enumerate(habits, 1):
        tk.Label(habit_frame, text=name, anchor="w",
                 width=20, relief="ridge").grid(row=row, column=0)

        for day in range(7):
            completed = bool(done & (1 << day))
            tk.Button(
                habit_frame,
                text="✓" if completed else "×",
                width=6,
                bg="#bde5d4" if completed else "#eeeeee",
                command=lambda h=hid, d=day: toggle(h, d)
            ).grid(row=row, column=day + 1)


def toggle(habit_id, day):
    row = db.execute(
        "SELECT done FROM habits WHERE id=? AND user_id=?",
        (habit_id, user_id)
    ).fetchone()

    if row:
        new_value = row[0] ^ (1 << day)
        db.execute("UPDATE habits SET done=? WHERE id=?",
                   (new_value, habit_id))
        db.commit()
        refresh()


def add_habit():
    name = simpledialog.askstring(
        "Add Habit", "Enter your new habit:"
    )
    if name and name.strip():
        db.execute(
            "INSERT INTO habits(user_id,name) VALUES(?,?)",
            (user_id, name.strip())
        )
        db.commit()
        refresh()


def delete_habit():
    selected = simpledialog.askinteger(
        "Delete Habit",
        "Enter the number of the habit shown in the list (starting at 1):"
    )
    habits = db.execute(
        "SELECT id FROM habits WHERE user_id=? ORDER BY id",
        (user_id,)
    ).fetchall()

    if selected is not None and 1 <= selected <= len(habits):
        db.execute("DELETE FROM habits WHERE id=?",
                   (habits[selected - 1][0],))
        db.commit()
        refresh()
    elif selected is not None:
        messagebox.showerror("Error", "Invalid habit number")


root = tk.Tk()
root.title("Daily Routine - Habit Tracker")
root.geometry("950x600")
login()
root.mainloop()

