import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_engine  # Ensure you have a database.py with get_engine()
import datetime
import plotly.express as px

# Load employee data from the database
def load_employees():
    engine = get_engine()
    with engine.begin() as conn:
        return pd.read_sql("SELECT amann_id, name, title, level, active, birthday, start_date, address, phone_number, email, gender FROM employees", conn)

def show_employees():
    st.title("Employee Management")

    # 🔁 Load data before use
    employees = load_employees()

    # Chuẩn hóa giá trị giới tính
    employees["gender"] = employees["gender"].replace({
        "Male": "Nam",  # Hoặc "Male" thành "Nam"
        "Female": "Nữ",  # Hoặc "Female" thành "Nữ"
        "Nam": "Nam",    # Nếu đã có "Nam"
        "Nữ": "Nữ"       # Nếu đã có "Nữ"
    })

    # Create 3 equal-width columns
    col1, col2, col3 = st.columns(3)

    # --- Bar Chart: Employee Count by Position ---
    with col1:
        df_title = employees['title'].value_counts().reset_index()
        df_title.columns = ['Position', 'Count']

        fig_title = px.bar(
            df_title,
            x='Position', y='Count',
            text='Count',
            labels={'Position': 'Position', 'Count': 'Number of Employees'},
            title="Employee Count by Position",
            color_discrete_sequence=px.colors.sequential.RdBu
        )

        fig_title.update_traces(textposition='outside')
        fig_title.update_layout(
            height=400,
            width=350,  # Set width explicitly
            margin=dict(t=50, b=30),
            title_x=0.5
        )
        st.plotly_chart(fig_title, use_container_width=True)

    # --- Pie Chart: Gender Ratio ---
    with col2:
        # Biểu đồ Gender, đảm bảo dữ liệu đã được chuẩn hóa
        gender_count = employees["gender"].value_counts().reset_index()
        gender_count.columns = ["gender", "count"]

        fig_gender = px.pie(
            gender_count,
            names="gender",
            values="count",
            title="Gender Ratio",
            hole=0.4,
            color_discrete_sequence=["#9c0f23", "#d3363e"]
        )
        fig_gender.update_traces(textinfo='label+percent+value')

        fig_gender.update_layout(
            height=400,
            width=350,  # Set width explicitly
            margin=dict(t=50, b=30),
            title_x=0.5
        )
        st.plotly_chart(fig_gender, use_container_width=True)

    # --- Line Chart: New Employees per Month ---
    with col3:
        employees['month'] = pd.to_datetime(employees['start_date'], errors='coerce').dt.to_period('M')
        monthly_counts = employees['month'].value_counts().sort_index().reset_index()
        monthly_counts.columns = ['Month', 'New Employees']
        monthly_counts['Month'] = monthly_counts['Month'].astype(str)

        fig_month = px.line(
            monthly_counts,
            x='Month', y='New Employees',
            markers=True,
            text='New Employees',
            title="New Employees per Month",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig_month.update_traces(textposition='top center')
        fig_month.update_layout(
            height=400,
            width=350,  # Set width explicitly
            margin=dict(t=50, b=30),
            title_x=0.5
        )
        st.plotly_chart(fig_month, use_container_width=True)


    # Create tabs for Employee List, Add New Employee, and Update Employee Information
    tab1, tab2, tab3 = st.tabs(["Employee List", "Update Information", "Add New Employee"])

    # TAB 1 — Show employee list
    with tab1:
        employees = load_employees()

        with st.expander("🔍 Search & Filter"):
            search_term = st.text_input("Search (Name / Amann ID / ID)", key="search_all", help="Search by name or ID")
            
            # Create 2 columns for filters
            col_filter1, col_filter2 = st.columns(2)
            
            with col_filter1:
                
                # Ép kiểu cột 'active' sang string để so sánh đúng
                employees["active"] = employees["active"].astype(str)

                # Status filter
                status_filter = st.selectbox("Status", options=["All", "Active", "Inactive"], key="filter_status")

                if status_filter == "Active":
                    employees = employees[employees["active"] == "1"]
                elif status_filter == "Inactive":
                    employees = employees[employees["active"] == "0"]


                
                # Title filter
                title_filter = st.selectbox(
                    "Position",
                    options=["All"] + sorted(employees["title"].dropna().unique()),
                    key="filter_title"
                )
                
                # Year of joining filter
                employees['start_year'] = pd.to_datetime(employees['start_date'], errors='coerce').dt.year
                year_min = int(employees['start_year'].min()) if employees['start_year'].notnull().any() else 2000
                year_max = int(employees['start_year'].max()) if employees['start_year'].notnull().any() else datetime.date.today().year
                selected_years = st.multiselect("Joining Year", list(range(year_min, year_max + 1)))

            with col_filter2:
                # Province filter
                unique_provinces = sorted(employees['address'].dropna().unique())
                selected_provinces = st.multiselect("Province/City", unique_provinces)
                
                # Email keyword filter
                email_keyword = st.text_input("Email Keyword").lower().strip()

            # Search by name and ID
            if search_term.strip():
                search_lower = search_term.strip().lower()
                employees = employees[employees['name'].str.lower().str.contains(search_lower, na=False) |
                                    employees['amann_id'].str.lower().str.contains(search_lower, na=False)]
            
            # Status filter
            if status_filter == "Active":
                employees = employees[employees["active"] == "1"]
            elif status_filter == "Inactive":
                employees = employees[employees["active"] == "0"]

            # Position filter
            if title_filter != "All":
                employees = employees[employees["title"] == title_filter]

            # Display results after filtering
            st.subheader("Employee List")
            if employees.empty:
                st.warning("No employees to display.")
            else:
                st.dataframe(employees)

    # TAB 2 — Update employee information
    with tab2:
        employees = load_employees()
        st.subheader("Update Employee Information")

        if employees.empty:
            st.warning("No employees to update.")
        else:
            employee_id = st.selectbox("Select Employee to Update", employees['amann_id'])

            emp_info = employees[employees['amann_id'] == employee_id].iloc[0]
            name = st.text_input("Name", value=emp_info['name'])
            title = st.selectbox("Position", options=employees["title"].unique(), index=employees['title'].tolist().index(emp_info['title']))
            level = st.selectbox("Level", options=employees["level"].unique(), index=employees['level'].tolist().index(emp_info['level']))
            active = st.selectbox("Status", options=["Active", "Inactive"], index=0 if emp_info['active'] == "1" else 1)

            submit_update = st.button("Update Information")
            if submit_update:
                try:
                    engine = get_engine()
                    with engine.connect() as conn:
                        conn.execute(text(""" 
                            UPDATE employees
                            SET name = :name, title = :title, level = :level, active = :active
                            WHERE amann_id = :amann_id
                        """), {
                            "name": name,
                            "title": title,
                            "level": level,
                            "active": "1" if active == "Active" else "0",
                            "amann_id": employee_id
                        })
                        conn.commit()
                        st.success(f"Employee '{name}' information updated successfully!")
                except Exception as e:
                    st.error(f"Update error: {str(e)}")

    # TAB 3 — Add new employee
    with tab3:
        st.markdown("### ➕ Add New Employee")
        with st.form(key="form_add_emp"):
            amann_id = st.text_input("Amann ID")
            name = st.text_input("Full Name")
            birthday = st.date_input("Birthday", value=None, min_value=datetime.date(1880, 1, 1))
            start_date = st.date_input("Joining Date", value=None)
            address = st.text_input("Address")
            phone_number = st.text_input("Phone Number")
            email = st.text_input("Email")
            gender = st.selectbox("Gender", ["Male", "Female"])
            available_titles = ["Manager", "Employee", "Accountant", "Intern", "Team Leader"]
            available_levels = ["Intern", "Junior", "Senior", "Lead", "Manager"]

            title = st.selectbox("Position", available_titles)
            level = st.selectbox("Level", available_levels)
            active = st.selectbox("Status", ["1", "0"])

            submit_add = st.form_submit_button("Add")
            if submit_add:
                if not amann_id.strip() or not name.strip():
                    st.error("Amann ID and Full Name are required!")
                else:
                    try:
                        engine = get_engine()
                        with engine.connect() as conn:
                            existing = conn.execute(
                                text("SELECT COUNT(*) FROM employees WHERE amann_id = :amann_id"),
                                {"amann_id": amann_id.strip()}
                            ).scalar()

                            if existing > 0:
                                st.error("Amann ID already exists!")
                            else:
                                conn.execute(text(""" 
                                    INSERT INTO employees (amann_id, name, title, level, active, birthday, start_date, address, phone_number, email, gender)
                                    VALUES (:amann_id, :name, :title, :level, :active, :birthday, :start_date, :address, :phone_number, :email, :gender)
                                """), {
                                    "amann_id": amann_id.strip(),
                                    "name": name.strip(),
                                    "title": title.strip(),
                                    "level": level.strip(),
                                    "active": active,
                                    "birthday": birthday,
                                    "start_date": start_date,
                                    "address": address,
                                    "phone_number": phone_number,
                                    "email": email,
                                    "gender": gender
                                })

                                conn.commit()
                                st.success(f"Employee '{name.strip()}' added successfully!")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Add employee error: {str(e)}")
