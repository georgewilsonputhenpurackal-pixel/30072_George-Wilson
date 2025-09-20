import streamlit as st
import backend as db
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Performance Management System")

# --- Authentication and Role Selection ---
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'is_manager' not in st.session_state:
    st.session_state.is_manager = False

if st.session_state.logged_in_user is None:
    st.sidebar.header("Login")
    all_employees = db.get_all_employees()
    if not all_employees:
        st.error("No employees found. Please populate the `employees` table in your database.")
    else:
        employee_names = [emp[1] for emp in all_employees]
        selected_name = st.sidebar.selectbox("Select your name", employee_names)
        
        selected_employee = [emp for emp in all_employees if emp[1] == selected_name][0]
        st.session_state.logged_in_user = selected_employee[0]
        
        # Check if the user is a manager (simple check: an employee is a manager if another employee reports to them)
        employees_reporting = db.get_employees_by_manager(st.session_state.logged_in_user)
        if employees_reporting:
            st.session_state.is_manager = True
            st.sidebar.success(f"Logged in as Manager: {selected_name}")
        else:
            st.session_state.is_manager = False
            st.sidebar.success(f"Logged in as Employee: {selected_name}")

# --- Main App Interface ---
if st.session_state.logged_in_user is not None:
    tabs = ["Goals & Tasks", "Feedback", "Reporting", "Business Insights"]
    selected_tab = st.sidebar.radio("Navigation", tabs)
    
    # Get user details
    logged_in_user_id = st.session_state.logged_in_user
    user_details = db.get_employee_by_id(logged_in_user_id)
    user_name = user_details[1]

    # Display user info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.write(f"Logged in as: **{user_name}**")
    st.sidebar.write(f"Role: **{'Manager' if st.session_state.is_manager else 'Employee'}**")
    
    # --- GOALS & TASKS TAB ---
    if selected_tab == "Goals & Tasks":
        st.header("Goal and Task Management")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Your Goals")
            my_goals = db.get_goals_for_employee(logged_in_user_id)
            if my_goals:
                df = pd.DataFrame(my_goals, columns=["ID", "Description", "Due Date", "Status"])
                st.dataframe(df)
            else:
                st.info("You have no goals assigned.")
        
        with col2:
            if st.session_state.is_manager:
                st.subheader("Set a New Goal")
                # Manager's functionality: Create Goal
                st.markdown("---")
                employees = db.get_employees_by_manager(logged_in_user_id)
                if employees:
                    employee_names = [emp[1] for emp in employees]
                    selected_employee_name = st.selectbox("Select Employee", employee_names)
                    selected_employee_id = [emp[0] for emp in employees if emp[1] == selected_employee_name][0]

                    goal_desc = st.text_area("Goal Description")
                    due_date = st.date_input("Due Date")
                    
                    if st.button("Set Goal"):
                        if goal_desc and due_date:
                            if db.create_goal(goal_desc, due_date, selected_employee_id, logged_in_user_id):
                                st.success(f"Goal set for {selected_employee_name} successfully!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to set goal.")
                        else:
                            st.warning("Please fill in all fields.")
            else:
                st.subheader("Log a New Task")
                # Employee's functionality: Log Task
                my_goals = db.get_goals_for_employee(logged_in_user_id)
                if my_goals:
                    goal_titles = {goal[0]: goal[1] for goal in my_goals}
                    selected_goal_id = st.selectbox("Select Goal to Log Task for", list(goal_titles.keys()), format_func=lambda x: goal_titles[x])
                    task_desc = st.text_area("Task Description")
                    if st.button("Log Task"):
                        if task_desc and selected_goal_id:
                            if db.create_task(task_desc, selected_goal_id, logged_in_user_id):
                                st.success("Task logged successfully, awaiting manager approval!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to log task.")
                        else:
                            st.warning("Please fill in all fields.")
                else:
                    st.info("You need to have an active goal to log a task.")

        st.markdown("---")
        st.subheader("Progress Tracking")
        if st.session_state.is_manager:
            # Manager's view: track progress and update status
            employees_managed = db.get_employees_by_manager(logged_in_user_id)
            if employees_managed:
                selected_employee_name_track = st.selectbox("Select Employee to View", [emp[1] for emp in employees_managed], key="emp_track_select")
                selected_employee_id_track = [emp[0] for emp in employees_managed if emp[1] == selected_employee_name_track][0]
                
                employee_goals = db.get_goals_for_employee(selected_employee_id_track)
                if employee_goals:
                    st.write(f"**Goals for {selected_employee_name_track}:**")
                    for goal in employee_goals:
                        goal_id, desc, due_date, status = goal
                        st.markdown(f"**Goal ID {goal_id}:** {desc} (Due: {due_date.strftime('%Y-%m-%d')}, Status: {status})")
                        
                        tasks = db.get_tasks_for_goal(goal_id)
                        if tasks:
                            st.markdown("##### Tasks:")
                            task_df = pd.DataFrame(tasks, columns=["ID", "Description", "Approved"])
                            st.dataframe(task_df, use_container_width=True)
                            
                            # Manager can approve tasks
                            st.markdown("###### Approve Tasks")
                            tasks_to_approve = [task for task in tasks if not task[2]]
                            if tasks_to_approve:
                                task_ids_to_approve = [task[0] for task in tasks_to_approve]
                                task_id_to_approve = st.selectbox(f"Select a task to approve for Goal {goal_id}:", task_ids_to_approve, key=f"approve_task_goal_{goal_id}")
                                if st.button("Approve Selected Task", key=f"approve_btn_goal_{goal_id}"):
                                    if db.approve_task(task_id_to_approve):
                                        st.success("Task approved!")
                                        st.experimental_rerun()
                                    else:
                                        st.error("Failed to approve task.")
                            else:
                                st.info("All tasks for this goal are approved.")
                        
                        # Manager can update goal status
                        new_status = st.selectbox("Update Goal Status", ["Draft", "In Progress", "Completed", "Cancelled"], index=["Draft", "In Progress", "Completed", "Cancelled"].index(status), key=f"status_{goal_id}")
                        if st.button("Update Goal Status", key=f"update_status_{goal_id}"):
                            if db.update_goal_status(goal_id, new_status):
                                st.success("Goal status updated successfully!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to update status.")
                        st.markdown("---")
                else:
                    st.info(f"{selected_employee_name_track} has no goals to track.")
            else:
                st.warning("You are not managing any employees.")
        else:
            # Employee's view: track progress
            st.subheader("My Tasks")
            my_goals = db.get_goals_for_employee(logged_in_user_id)
            if my_goals:
                for goal in my_goals:
                    goal_id, desc, due_date, status = goal
                    st.markdown(f"**Goal ID {goal_id}:** {desc} (Due: {due_date.strftime('%Y-%m-%d')}, Status: {status})")
                    tasks = db.get_tasks_for_goal(goal_id)
                    if tasks:
                        task_df = pd.DataFrame(tasks, columns=["ID", "Description", "Approved"])
                        st.dataframe(task_df, use_container_width=True)
                    else:
                        st.info("No tasks logged for this goal yet.")
                    st.markdown("---")
            else:
                st.info("You have no goals to track.")

    # --- FEEDBACK TAB ---
    elif selected_tab == "Feedback":
        st.header("Feedback")
        if st.session_state.is_manager:
            st.subheader("Provide Feedback")
            employees_managed = db.get_employees_by_manager(logged_in_user_id)
            if employees_managed:
                selected_employee_name_fb = st.selectbox("Select Employee", [emp[1] for emp in employees_managed], key="emp_fb_select")
                selected_employee_id_fb = [emp[0] for emp in employees_managed if emp[1] == selected_employee_name_fb][0]

                employee_goals = db.get_goals_for_employee(selected_employee_id_fb)
                if employee_goals:
                    goal_titles = {goal[0]: goal[1] for goal in employee_goals}
                    selected_goal_id_fb = st.selectbox("Select Goal to provide feedback for", list(goal_titles.keys()), format_func=lambda x: goal_titles[x])
                    feedback_text = st.text_area("Your Feedback")
                    if st.button("Submit Feedback"):
                        if feedback_text and selected_goal_id_fb:
                            if db.create_feedback(feedback_text, selected_goal_id_fb, logged_in_user_id):
                                st.success("Feedback submitted successfully!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to submit feedback.")
                        else:
                            st.warning("Please fill in all fields.")
                else:
                    st.info(f"{selected_employee_name_fb} has no goals to provide feedback on.")
            else:
                st.warning("You cannot provide feedback as you are not managing any employees.")
        else:
            st.subheader("Your Feedback")
            my_goals = db.get_goals_for_employee(logged_in_user_id)
            if my_goals:
                for goal in my_goals:
                    goal_id, desc, _, _ = goal
                    st.markdown(f"**Feedback for Goal: {desc}**")
                    feedback_items = db.get_feedback_for_goal(goal_id)
                    if feedback_items:
                        for fb_text, manager_id in feedback_items:
                            manager = db.get_employee_by_id(manager_id)
                            st.markdown(f"**From {manager[1]}:**")
                            st.info(fb_text)
                    else:
                        st.info("No feedback for this goal yet.")
                    st.markdown("---")
            else:
                st.info("You have no goals to receive feedback for.")

    # --- REPORTING TAB ---
    elif selected_tab == "Reporting":
        st.header("Performance History & Reporting")
        
        target_employee_id = logged_in_user_id
        target_employee_name = user_name

        if st.session_state.is_manager:
            employees_managed = db.get_employees_by_manager(logged_in_user_id)
            if employees_managed:
                selected_employee_name_report = st.selectbox("Select Employee to View Report", [emp[1] for emp in employees_managed], key="report_select")
                target_employee_id = [emp[0] for emp in employees_managed if emp[1] == selected_employee_name_report][0]
                target_employee_name = selected_employee_name_report
            else:
                st.warning("You are not managing any employees.")

        st.subheader(f"Performance History for {target_employee_name}")
        performance_history = db.get_performance_history(target_employee_id)
        if performance_history:
            df = pd.DataFrame(performance_history, columns=["Goal", "Due Date", "Status", "Feedback"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No performance history found for this employee.")

    # --- BUSINESS INSIGHTS TAB ---
    elif selected_tab == "Business Insights":
        st.header("Business Insights")
        
        # Select an employee for individual insights
        selected_employee_id = None
        if st.session_state.is_manager:
            employees_managed = db.get_employees_by_manager(logged_in_user_id)
            if employees_managed:
                employee_options = {emp[1]: emp[0] for emp in employees_managed}
                selected_name = st.selectbox("Select Employee for Individual Insights", ["All Employees"] + list(employee_options.keys()))
                if selected_name != "All Employees":
                    selected_employee_id = employee_options[selected_name]

        insights_col1, insights_col2, insights_col3 = st.columns(3)

        # COUNT
        with insights_col1:
            st.metric(label="Total Goals Completed", value=db.get_completed_goals_count(selected_employee_id))
            st.metric(label="Total Tasks Logged", value=db.get_total_tasks())

        # AVG
        with insights_col2:
            st.metric(label="Avg Tasks per Goal", value=f"{db.get_avg_tasks_per_goal(selected_employee_id):.2f}")
        
        # MIN/MAX
        min_max_days = db.get_min_max_due_date_difference()
        if min_max_days and all(min_max_days):
            with insights_col3:
                st.metric(label="Min Days to Complete a Goal", value=f"{min_max_days[0].days} days")
                st.metric(label="Max Days to Complete a Goal", value=f"{min_max_days[1].days} days")
        else:
            with insights_col3:
                st.info("Not enough data to calculate min/max days.")
