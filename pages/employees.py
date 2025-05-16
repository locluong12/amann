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
        "Male": "Nam",
        "Female": "Nữ",
        "Nam": "Nam",
        "Nữ": "Nữ"
    })

    # Create 3 equal-width columns
    col1, col2 = st.columns(2)

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
            color_discrete_sequence=["#2a9d8f"]
        )

        fig_title.update_traces(textposition='outside')
        fig_title.update_layout(
            height=400,
            width=350,
            margin=dict(t=50, b=30),
            title_x=0.5,
            plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white'),
    title=dict(
        font=dict(color='white')
    ) 

        )
        st.plotly_chart(fig_title, use_container_width=True)

    # --- Pie Chart: Gender Ratio ---
    with col2:
        gender_count = employees["gender"].value_counts().reset_index()
        gender_count.columns = ["gender", "count"]

        fig_gender = px.pie(
            gender_count,
            names="gender",
            values="count",
            title="Gender Ratio",
            hole=0.4,
            color_discrete_sequence=["#2a9d8f", "#1f7e6d"]
        )
        fig_gender.update_traces(textinfo='label+percent+value')

        fig_gender.update_layout(
            height=400,
            width=350,
            margin=dict(t=50, b=30),
            title_x=0.5,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            title=dict(
                font=dict(color='white')
            )  
        )
        st.plotly_chart(fig_gender, use_container_width=True)

   
    st.markdown("""
    <style>
    /* Đổi màu chữ tiêu đề tab (tab labels) sang trắng */
    div[role="tablist"] button[role="tab"] {
        color: white !important;
    }

    /* Đổi màu chữ label input sang trắng */
    label, .css-1v0mbdj.e1fqkh3o3 {
        color: white !important;
    }

    /* Đổi màu chữ tiêu đề và text input */
    .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label {
        color: white !important;
    }

    /* Đổi màu chữ tiêu đề và input trong dataframe (nếu cần) */
    div[data-testid="stDataFrameContainer"] {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)


    # Create tabs for Employee List, Add New Employee, and Update Employee Information
    tab1, tab2, tab3 = st.tabs(["Employee List", "Update Information", "Add New Employee"])

    # TAB 1 — Show employee list
    with tab1:
        employees = load_employees()

        with st.expander("🔍 Search & Filter"):
            search_term = st.text_input("Search (Name / Amann ID / ID)", key="search_all", help="Search by name or ID")
            
            col_filter1, col_filter2 = st.columns(2)
            
            with col_filter1:
                employees["active"] = employees["active"].astype(str)

                status_filter = st.selectbox("Status", options=["All", "Active", "Inactive"], key="filter_status")

                if status_filter == "Active":
                    employees = employees[employees["active"] == "1"]
                elif status_filter == "Inactive":
                    employees = employees[employees["active"] == "0"]

                title_filter = st.selectbox(
                    "Position",
                    options=["All"] + sorted(employees["title"].dropna().unique()),
                    key="filter_title"
                )
                
                employees['start_year'] = pd.to_datetime(employees['start_date'], errors='coerce').dt.year
                year_min = int(employees['start_year'].min()) if employees['start_year'].notnull().any() else 2000
                year_max = int(employees['start_year'].max()) if employees['start_year'].notnull().any() else datetime.date.today().year
                selected_years = st.multiselect("Joining Year", list(range(year_min, year_max + 1)))

            with col_filter2:
                unique_provinces = sorted(employees['address'].dropna().unique())
                selected_provinces = st.multiselect("Province/City", unique_provinces)
                
                email_keyword = st.text_input("Email Keyword").lower().strip()

            if search_term.strip():
                search_lower = search_term.strip().lower()
                employees = employees[employees['name'].str.lower().str.contains(search_lower, na=False) |
                                      employees['amann_id'].str.lower().str.contains(search_lower, na=False)]
            
            if status_filter == "Active":
                employees = employees[employees["active"] == "1"]
            elif status_filter == "Inactive":
                employees = employees[employees["active"] == "0"]

            if title_filter != "All":
                employees = employees[employees["title"] == title_filter]

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
        st.markdown("""
        <style>
        /* Đổi màu icon lịch trong st.date_input thành đen */
        [data-baseweb="input"] svg {
            fill: black !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # TAB 3 — Add new employee
    with tab3:
        st.markdown("### ➕ Add New Employee")
        with st.form(key="form_add_emp"):
            amann_id = st.text_input("Amann ID")
            name = st.text_input("Full Name")
            birthday = st.date_input("Birthday")
            start_date = st.date_input("Joining Date")
            address = st.text_input("Address")
            phone_number = st.text_input("Phone Number")
            email = st.text_input("Email")
            gender = st.selectbox("Gender", ["Male", "Female"])
            available_titles = ["Manager", "Employee", "Accountant", "Intern", "Team Leader"]
            available_levels = ["Intern", "Junior", "Senior", "Lead", "Manager"]

            title = st.selectbox("Position", available_titles)
            level = st.selectbox("Level", available_levels)
            active = st.selectbox("Status", ["1", "0"])
            st.markdown("""
        <style>
        div.stDownloadButton > button:first-child {
            background-color: #20c997;
            color: green;
            border: none;
        }
        div.stDownloadButton > button:first-child:hover {
            background-color: #17a2b8;
            color: green;
        }
        </style>
        """, unsafe_allow_html=True)

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
                                    "title": title,
                                    "level": level,
                                    "active": active,
                                    "birthday": birthday,
                                    "start_date": start_date,
                                    "address": address.strip(),
                                    "phone_number": phone_number.strip(),
                                    "email": email.strip(),
                                    "gender": gender
                                })
                                conn.commit()
                                st.success("New employee added successfully!")
                    except Exception as e:
                        st.error(f"Error adding employee: {str(e)}")