import psycopg2
import streamlit as st
import pandas as pd

# Function to connect to the PostgreSQL database
# IMPORTANT: Replace these with your actual database credentials.
@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="PMS",
            user="postgres",
            password="Bangalore100%"
        )
        return conn
    except psycopg2.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

# --- CRUD Operations for Employees ---
def get_employee_by_id(employee_id):
    conn = get_db_connection()
    if conn is None: return None
    with conn.cursor() as cur:
        cur.execute("SELECT employee_id, name, manager_id FROM employees WHERE employee_id = %s", (employee_id,))
        employee = cur.fetchone()
    conn.close()
    return employee

def get_all_employees():
    conn = get_db_connection()
    if conn is None: return []
    with conn.cursor() as cur:
        cur.execute("SELECT employee_id, name FROM employees")
        employees = cur.fetchall()
    conn.close()
    return employees

def get_employees_by_manager(manager_id):
    conn = get_db_connection()
    if conn is None: return []
    with conn.cursor() as cur:
        cur.execute("SELECT employee_id, name FROM employees WHERE manager_id = %s", (manager_id,))
        employees = cur.fetchall()
    conn.close()
    return employees

# --- CRUD Operations for Goals ---
def create_goal(description, due_date, employee_id, manager_id):
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO goals (description, due_date, status, employee_id, manager_id) VALUES (%s, %s, 'Draft', %s, %s)", (description, due_date, employee_id, manager_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        st.error(f"Error creating goal: {e}")
        return False
    finally:
        conn.close()

def get_goals_for_employee(employee_id):
    conn = get_db_connection()
    if conn is None: return []
    with conn.cursor() as cur:
        cur.execute("SELECT goal_id, description, due_date, status FROM goals WHERE employee_id = %s", (employee_id,))
        goals = cur.fetchall()
    conn.close()
    return goals

def update_goal_status(goal_id, new_status):
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE goals SET status = %s WHERE goal_id = %s", (new_status, goal_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        st.error(f"Error updating goal status: {e}")
        return False
    finally:
        conn.close()

# --- CRUD Operations for Tasks ---
def create_task(description, goal_id, employee_id):
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO tasks (description, goal_id, employee_id) VALUES (%s, %s, %s)", (description, goal_id, employee_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        st.error(f"Error logging task: {e}")
        return False
    finally:
        conn.close()

def get_tasks_for_goal(goal_id):
    conn = get_db_connection()
    if conn is None: return []
    with conn.cursor() as cur:
        cur.execute("SELECT task_id, description, is_approved FROM tasks WHERE goal_id = %s", (goal_id,))
        tasks = cur.fetchall()
    conn.close()
    return tasks

def approve_task(task_id):
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE tasks SET is_approved = TRUE WHERE task_id = %s", (task_id,))
        conn.commit()
        return True
    except psycopg2.Error as e:
        st.error(f"Error approving task: {e}")
        return False
    finally:
        conn.close()

# --- CRUD Operations for Feedback ---
def create_feedback(feedback_text, goal_id, manager_id):
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO feedback (feedback_text, goal_id, manager_id) VALUES (%s, %s, %s)", (feedback_text, goal_id, manager_id))
        conn.commit()
        return True
    except psycopg2.Error as e:
        st.error(f"Error providing feedback: {e}")
        return False
    finally:
        conn.close()

def get_feedback_for_goal(goal_id):
    conn = get_db_connection()
    if conn is None: return []
    with conn.cursor() as cur:
        cur.execute("SELECT feedback_text, manager_id FROM feedback WHERE goal_id = %s", (goal_id,))
        feedback = cur.fetchall()
    conn.close()
    return feedback

# --- Reporting and Business Insights ---
def get_performance_history(employee_id):
    conn = get_db_connection()
    if conn is None: return None
    with conn.cursor() as cur:
        # Get all goals and feedback for the employee
        cur.execute("""
            SELECT g.description, g.due_date, g.status, f.feedback_text
            FROM goals g
            LEFT JOIN feedback f ON g.goal_id = f.goal_id
            WHERE g.employee_id = %s
            ORDER BY g.due_date DESC
        """, (employee_id,))
        history = cur.fetchall()
    conn.close()
    return history

def get_completed_goals_count(employee_id=None):
    conn = get_db_connection()
    if conn is None: return 0
    with conn.cursor() as cur:
        if employee_id:
            cur.execute("SELECT COUNT(*) FROM goals WHERE status = 'Completed' AND employee_id = %s", (employee_id,))
        else:
            cur.execute("SELECT COUNT(*) FROM goals WHERE status = 'Completed'")
        count = cur.fetchone()[0]
    conn.close()
    return count

def get_avg_tasks_per_goal(employee_id=None):
    conn = get_db_connection()
    if conn is None: return 0
    with conn.cursor() as cur:
        if employee_id:
            cur.execute("""
                SELECT AVG(task_count)
                FROM (
                    SELECT goal_id, COUNT(task_id) AS task_count
                    FROM tasks
                    WHERE employee_id = %s
                    GROUP BY goal_id
                ) AS goal_task_counts
            """, (employee_id,))
        else:
            cur.execute("""
                SELECT AVG(task_count)
                FROM (
                    SELECT goal_id, COUNT(task_id) AS task_count
                    FROM tasks
                    GROUP BY goal_id
                ) AS goal_task_counts
            """)
        avg = cur.fetchone()[0]
    conn.close()
    return avg if avg else 0

def get_min_max_due_date_difference():
    conn = get_db_connection()
    if conn is None: return (None, None)
    with conn.cursor() as cur:
        # Calculate the number of days between the goal's creation and its due date
        # Assuming there is a created_at column. If not, this needs to be adjusted.
        # The schema provided does not have a created_at column, so this query needs to be adapted.
        # Let's return some placeholder values to prevent an error.
        return (None, None)

def get_total_tasks():
    conn = get_db_connection()
    if conn is None: return 0
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tasks")
        count = cur.fetchone()[0]
    conn.close()
    return count
