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
    st.title("Quản lý nhân viên")
    
    

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

   # --- Biểu đồ Cột: Số lượng nhân viên theo chức vụ ---
    with col1:
        df_title = employees['title'].value_counts().reset_index()
        df_title.columns = ['Chức vụ', 'Số lượng']

        fig_title = px.bar(
            df_title,
            x='Chức vụ', y='Số lượng',
            text='Số lượng',
            labels={'Chức vụ': 'Chức vụ', 'Số lượng': 'Số lượng nhân viên'},
            title="Số lượng nhân viên theo chức vụ",
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

    # --- Biểu đồ Tròn: Tỷ lệ giới tính ---
    with col2:
        gender_count = employees["gender"].value_counts().reset_index()
        gender_count.columns = ["Giới tính", "Số lượng"]

        fig_gender = px.pie(
            gender_count,
            names="Giới tính",
            values="Số lượng",
            title="Tỷ lệ giới tính",
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


    # Tạo các tab: Danh sách nhân viên, Cập nhật thông tin, Thêm nhân viên mới
    tab1, tab2, tab3 = st.tabs(["Danh sách nhân viên", "Cập nhật thông tin", "Thêm nhân viên mới"])

    # TAB 1 — Hiển thị danh sách nhân viên
    with tab1:
        employees = load_employees()

        with st.expander("🔍 Tìm kiếm & Bộ lọc"):
            search_term = st.text_input("Tìm kiếm (Tên / Mã Amann)", key="search_all", help="Tìm theo tên hoặc mã ID")
            
            col_filter1, col_filter2 = st.columns(2)
            
            with col_filter1:
                employees["active"] = employees["active"].astype(str)

                status_filter = st.selectbox("Trạng thái", options=["Tất cả", "Đang làm", "Đã nghỉ"], key="filter_status")

                if status_filter == "Đang làm":
                    employees = employees[employees["active"] == "1"]
                elif status_filter == "Đã nghỉ":
                    employees = employees[employees["active"] == "0"]

                title_filter = st.selectbox(
                    "Chức vụ",
                    options=["Tất cả"] + sorted(employees["title"].dropna().unique()),
                    key="filter_title"
                )
                
                employees['start_year'] = pd.to_datetime(employees['start_date'], errors='coerce').dt.year
                year_min = int(employees['start_year'].min()) if employees['start_year'].notnull().any() else 2000
                year_max = int(employees['start_year'].max()) if employees['start_year'].notnull().any() else datetime.date.today().year
                selected_years = st.multiselect("Năm vào làm", list(range(year_min, year_max + 1)))

            with col_filter2:
                unique_provinces = sorted(employees['address'].dropna().unique())
                selected_provinces = st.multiselect("Tỉnh/Thành phố", unique_provinces)
                
                email_keyword = st.text_input("Từ khóa trong Email").lower().strip()

            if search_term.strip():
                search_lower = search_term.strip().lower()
                employees = employees[employees['name'].str.lower().str.contains(search_lower, na=False) |
                                    employees['amann_id'].str.lower().str.contains(search_lower, na=False)]

            if status_filter == "Đang làm":
                employees = employees[employees["active"] == "1"]
            elif status_filter == "Đã nghỉ":
                employees = employees[employees["active"] == "0"]

            if title_filter != "Tất cả":
                employees = employees[employees["title"] == title_filter]

            st.subheader("Danh sách nhân viên")
            if employees.empty:
                st.warning("Không có nhân viên nào để hiển thị.")
            else:
                st.dataframe(employees)


    # TAB 2 — Cập nhật thông tin nhân viên
    with tab2:
        employees = load_employees()
        st.subheader("Cập nhật thông tin nhân viên")

        if employees.empty:
            st.warning("Không có nhân viên nào để cập nhật.")
        else:
            employee_id = st.selectbox("Chọn nhân viên cần cập nhật", employees['amann_id'])

            emp_info = employees[employees['amann_id'] == employee_id].iloc[0]
            name = st.text_input("Họ và tên", value=emp_info['name'])
            title = st.selectbox("Chức vụ", options=employees["title"].unique(), index=employees['title'].tolist().index(emp_info['title']))
            level = st.selectbox("Cấp bậc", options=employees["level"].unique(), index=employees['level'].tolist().index(emp_info['level']))
            active = st.selectbox("Trạng thái làm việc", options=["Đang làm", "Đã nghỉ"], index=0 if emp_info['active'] == "1" else 1)

            submit_update = st.button("Cập nhật thông tin")
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
                            "active": "1" if active == "Đang làm" else "0",
                            "amann_id": employee_id
                        })
                        conn.commit()
                        st.success(f"✅ Đã cập nhật thông tin nhân viên '{name}' thành công!")
                except Exception as e:
                    st.error(f"❌ Lỗi khi cập nhật: {str(e)}")

        st.markdown("""
        <style>
        /* Đổi màu icon lịch trong st.date_input thành đen */
        [data-baseweb="input"] svg {
            fill: black !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # TAB 3 — Thêm nhân viên mới
    with tab3:
        st.markdown("Thêm nhân viên mới")
        with st.form(key="form_add_emp"):
            amann_id = st.text_input("Mã Amann ID")
            name = st.text_input("Họ và tên")
            birthday = st.date_input("Ngày sinh")
            start_date = st.date_input("Ngày vào làm")
            address = st.text_input("Địa chỉ")
            phone_number = st.text_input("Số điện thoại")
            email = st.text_input("Email")
            gender = st.selectbox("Giới tính", ["Nam", "Nữ"])
            
            available_titles = ["Quản lý", "Nhân viên", "Kế toán", "Thực tập", "Trưởng nhóm"]
            available_levels = ["Thực tập", "Junior", "Senior", "Lead", "Manager"]

            title = st.selectbox("Chức vụ", available_titles)
            level = st.selectbox("Cấp bậc", available_levels)
            active = st.selectbox("Trạng thái làm việc", ["1 - Đang làm", "0 - Đã nghỉ"])

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

            submit_add = st.form_submit_button("Thêm mới")

            if submit_add:
                if not amann_id.strip() or not name.strip():
                    st.error("⚠️ Mã Amann ID và Họ tên là bắt buộc!")
                else:
                    try:
                        engine = get_engine()
                        with engine.connect() as conn:
                            existing = conn.execute(
                                text("SELECT COUNT(*) FROM employees WHERE amann_id = :amann_id"),
                                {"amann_id": amann_id.strip()}
                            ).scalar()

                            if existing > 0:
                                st.error("❌ Mã Amann ID đã tồn tại!")
                            else:
                                conn.execute(text(""" 
                                    INSERT INTO employees (amann_id, name, title, level, active, birthday, start_date, address, phone_number, email, gender)
                                    VALUES (:amann_id, :name, :title, :level, :active, :birthday, :start_date, :address, :phone_number, :email, :gender)
                                """), {
                                    "amann_id": amann_id.strip(),
                                    "name": name.strip(),
                                    "title": title,
                                    "level": level,
                                    "active": active[0],  # chỉ lấy '1' hoặc '0'
                                    "birthday": birthday,
                                    "start_date": start_date,
                                    "address": address.strip(),
                                    "phone_number": phone_number.strip(),
                                    "email": email.strip(),
                                    "gender": gender
                                })
                                conn.commit()
                                st.success("✅ Đã thêm nhân viên mới thành công!")
                    except Exception as e:
                        st.error(f"❌ Lỗi khi thêm nhân viên: {str(e)}")
