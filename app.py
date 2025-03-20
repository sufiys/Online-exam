import streamlit as st
import sqlite3

# Initialize SQLite Database
conn = sqlite3.connect("assessment.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT NOT NULL
)
""")
conn.commit()

st.title("📝 Online Assessment System")

# Section: Add Exam
st.subheader("Add New Exam")
exam_name = st.text_input("Exam Name")
exam_subject = st.text_input("Subject")

if st.button("Add Exam"):
    cursor.execute("INSERT INTO exams (name, subject) VALUES (?, ?)", (exam_name, exam_subject))
    conn.commit()
    st.success("Exam added successfully!")

# Section: View Exams
st.subheader("Available Exams")
if st.button("Fetch Exams"):
    cursor.execute("SELECT * FROM exams")
    exams = cursor.fetchall()
    for exam in exams:
        st.write(f"📚 {exam[1]} - {exam[2]}")

# Close database connection
conn.close()
