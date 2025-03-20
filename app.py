import streamlit as st
import sqlite3
import time
from hashlib import sha256

# --------------------------
# Database Setup & Functions
# --------------------------
def init_db():
    conn = sqlite3.connect("exam_system.db", check_same_thread=False)
    c = conn.cursor()
    # Create users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('admin', 'student'))
        )
    """)
    # Create exams table (include exam duration in seconds)
    c.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            questions TEXT,
            duration INTEGER
        )
    """)
    # Create results table to store student exam submissions
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            exam_id INTEGER,
            answers TEXT,
            submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(exam_id) REFERENCES exams(id)
        )
    """)
    conn.commit()
    return conn

# Use a single connection for the session
conn = init_db()

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def register_user(username, password, role):
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  (username, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username = ? AND password = ?", 
              (username, hash_password(password)))
    user = c.fetchone()
    return user[0] if user else None

def add_exam(name, questions, duration):
    c = conn.cursor()
    c.execute("INSERT INTO exams (name, questions, duration) VALUES (?, ?, ?)", 
              (name, questions, duration))
    conn.commit()

def get_exams():
    c = conn.cursor()
    c.execute("SELECT * FROM exams")
    return c.fetchall()

def add_result(username, exam_id, answers):
    c = conn.cursor()
    c.execute("INSERT INTO results (username, exam_id, answers) VALUES (?, ?, ?)",
              (username, exam_id, answers))
    conn.commit()

def get_results():
    c = conn.cursor()
    c.execute("SELECT * FROM results")
    return c.fetchall()

# --------------------------
# Streamlit UI
# --------------------------
st.title("Online Assessment System")

# Sidebar Navigation
menu = ["Login", "Register", "Admin Dashboard", "Student Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

# Session State Initialization
if "username" not in st.session_state:
    st.session_state["username"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "current_exam" not in st.session_state:
    st.session_state["current_exam"] = None
if "exam_start_time" not in st.session_state:
    st.session_state["exam_start_time"] = None

# --------------------------
# Registration
# --------------------------
if choice == "Register":
    st.subheader("Create an Account")
    username = st.text_input("Username", key="reg_username")
    password = st.text_input("Password", type="password", key="reg_password")
    role = st.selectbox("Role", ["admin", "student"])
    if st.button("Register"):
        if register_user(username, password, role):
            st.success("Account created! Please login.")
        else:
            st.error("Username already exists.")

# --------------------------
# Login
# --------------------------
elif choice == "Login":
    st.subheader("Login to your Account")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        role = login_user(username, password)
        if role:
            st.session_state["username"] = username
            st.session_state["role"] = role
            st.success(f"Logged in as {role}")
        else:
            st.error("Invalid username or password")

# --------------------------
# Admin Dashboard
# --------------------------
elif choice == "Admin Dashboard":
    if st.session_state.get("role") != "admin":
        st.error("Admin access required. Please login as admin.")
    else:
        st.subheader("Admin Dashboard")
        st.write("### Create a New Exam")
        exam_name = st.text_input("Exam Name", key="exam_name")
        questions = st.text_area("Questions (Format: Q1?;Q2?;Q3?)", key="exam_questions")
        duration = st.number_input("Exam Duration (in seconds)", min_value=10, value=60, step=10, key="exam_duration")
        if st.button("Create Exam"):
            add_exam(exam_name, questions, duration)
            st.success("Exam Created!")
        
        st.write("### Existing Exams")
        exams = get_exams()
        for exam in exams:
            st.write(f"**{exam[1]}** - Duration: {exam[3]} seconds")
            st.write(f"Questions: {exam[2]}")
        
        st.write("### Exam Submissions")
        results = get_results()
        if results:
            for res in results:
                st.write(f"User: {res[1]}, Exam ID: {res[2]}, Answers: {res[3]}, Submitted on: {res[4]}")
        else:
            st.info("No submissions yet.")

# --------------------------
# Student Dashboard
# --------------------------
elif choice == "Student Dashboard":
    if st.session_state.get("role") != "student":
        st.error("Student access required. Please login as student.")
    else:
        st.subheader("Student Dashboard")
        st.write("### Available Exams:")
        exams = get_exams()
        for exam in exams:
            if st.button(f"Take {exam[1]}", key=f"take_{exam[0]}"):
                st.session_state["current_exam"] = exam
                st.session_state["exam_start_time"] = time.time()
        
        # If an exam is selected
        if st.session_state.get("current_exam"):
            exam = st.session_state["current_exam"]
            exam_id, exam_name, questions_str, duration = exam
            st.write(f"## Exam: {exam_name}")
            
            # Timer Logic
            elapsed = int(time.time() - st.session_state["exam_start_time"])
            remaining = duration - elapsed
            if remaining <= 0:
                st.error("Time is up!")
            else:
                st.info(f"Time Remaining: {remaining} seconds")
            
            # Display questions
            questions = questions_str.split(";")
            answers = []
            st.write("### Answer the following questions:")
            for i, q in enumerate(questions, start=1):
                ans = st.text_input(f"Q{i}: {q}", key=f"q{i}")
                answers.append(ans)
            
            if st.button("Submit Exam"):
                if remaining <= 0:
                    st.error("Cannot submit, time is up!")
                else:
                    # For demo purposes, we simply store answers as a semicolon-separated string.
                    answers_str = ";".join(answers)
                    add_result(st.session_state["username"], exam_id, answers_str)
                    st.success("Exam Submitted!")
                    # Clear current exam data
                    st.session_state["current_exam"] = None
                    st.session_state["exam_start_time"] = None

            # Auto-refresh the page every second for the timer (if time remains)  
            if remaining > 0:
                st.experimental_rerun()
