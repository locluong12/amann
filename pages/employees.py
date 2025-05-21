import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_engine

def load_employees():
    engine = get_engine()
    with engine.begin() as conn:
        return pd.read_sql("SELECT amann_id, name, title, level, active, address, phone_number, shift_start, shift_end, department, status FROM employees", conn)

def show_employees():
    st.title("Quản lý nhân viên")

    tab1, tab2 = st.tabs(["Danh sách & Thêm nhân viên", "Cập nhật thông tin"])

    # TAB 1
    with tab1:
        employees = load_employees()

        with st.expander("🔍 Tìm kiếm & Lọc"):
            search_term = st.text_input("Tìm kiếm (Tên / Amann ID)", key="search_all")
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                status_filter = st.selectbox("Trạng thái", options=["Tất cả", "Active", "Inactive"], key="filter_status")
            with col_filter2:
                title_filter = st.selectbox(
                    "Chức vụ",
                    options=["Tất cả"] + sorted(employees["title"].dropna().unique()),
                    key="filter_title"
                )

        # Tìm kiếm
        if search_term.strip():
            search_lower = search_term.strip().lower()
            employees = employees[
                employees['name'].str.lower().str.contains(search_lower, na=False) |
                employees['amann_id'].str.lower().str.contains(search_lower, na=False)
            ]

        # Lọc trạng thái
        if status_filter == "Active":
            employees = employees[employees["active"] == "1"]
        elif status_filter == "Inactive":
            employees = employees[employees["active"] == "0"]

        # Lọc chức vụ
        if title_filter != "Tất cả":
            employees = employees[employees["title"] == title_filter]

        st.subheader("Quản lý nhân viên")
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 📋 Danh sách nhân viên")
            st.dataframe(employees.drop(columns=["active"]), use_container_width=True)  # Ẩn cột active

        with col2:
            st.markdown("### ➕ Thêm nhân viên mới")
            with st.form(key="form_add_emp"):
                amann_id = st.text_input("Amann ID")
                name = st.text_input("Họ và tên")
                available_titles = ["Quản lý", "Nhân viên", "Kế toán", "Thực tập", "Trưởng nhóm", "Technician"]
                available_levels = ["Intern", "Junior", "Senior", "Lead", "Manager"]

                title = st.selectbox("Chức danh", available_titles)
                level = st.selectbox("Cấp độ", available_levels)
                address = st.text_input("Địa chỉ")
                phone_number = st.text_input("Số điện thoại")
                shift_start = st.time_input("Giờ bắt đầu ca")
                shift_end = st.time_input("Giờ kết thúc ca")
                department = st.text_input("Phòng ban")
                status = st.selectbox("Trạng thái nhân viên", ["Đang làm", "Nghỉ việc", "Tạm nghỉ"])

                submit_add = st.form_submit_button("Thêm")
                if submit_add:
                    if not amann_id.strip() or not name.strip():
                        st.error("Phải nhập đầy đủ Amann ID và Họ tên!")
                    else:
                        try:
                            engine = get_engine()
                            with engine.connect() as conn:
                                existing = conn.execute(
                                    text("SELECT COUNT(*) FROM employees WHERE amann_id = :amann_id"),
                                    {"amann_id": amann_id.strip()}
                                ).scalar()

                                if existing > 0:
                                    st.error("Amann ID đã tồn tại trong hệ thống!")
                                else:
                                    conn.execute(text("""
                                        INSERT INTO employees (amann_id, name, title, level, active, address, phone_number, shift_start, shift_end, department, status)
                                        VALUES (:amann_id, :name, :title, :level, :active, :address, :phone_number, :shift_start, :shift_end, :department, :status)
                                    """), {
                                        "amann_id": amann_id.strip(),
                                        "name": name.strip(),
                                        "title": title.strip(),
                                        "level": level.strip(),
                                        "active": "1",  # luôn mặc định là active
                                        "address": address.strip(),
                                        "phone_number": phone_number.strip(),
                                        "shift_start": shift_start,
                                        "shift_end": shift_end,
                                        "department": department.strip(),
                                        "status": status.strip()
                                    })
                                    conn.commit()
                                    st.success(f"Đã thêm nhân viên '{name.strip()}' thành công!")
                                    st.cache_data.clear()
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi thêm nhân viên: {str(e)}")

    # TAB 2
    with tab2:
        employees = load_employees()
        st.subheader("Cập nhật thông tin nhân viên")

        if employees.empty:
            st.warning("Không có nhân viên để cập nhật.")
            return

        employee_choice = st.selectbox(
            "Chọn nhân viên",
            employees.apply(lambda x: f"{x['amann_id']} - {x['name']}", axis=1)
        )
        selected_amann_id = employee_choice.split(' - ')[0]
        selected_employee = employees[employees['amann_id'] == selected_amann_id].iloc[0]

        amann_id_edit = st.text_input("Amann ID", selected_employee['amann_id'] or "")
        name_edit = st.text_input("Họ và tên", selected_employee['name'] or "")

        available_titles = ["Quản lý", "Nhân viên", "Kế toán", "Thực tập", "Trưởng nhóm"]
        available_levels = ["Intern", "Junior", "Senior", "Lead", "Manager"]

        title_value = (selected_employee['title'] or "").strip()
        if title_value not in available_titles:
            available_titles.append(title_value)

        level_value = (selected_employee['level'] or "").strip()
        if level_value not in available_levels:
            available_levels.append(level_value)

        title_edit = st.selectbox("Chức vụ", available_titles, index=available_titles.index(title_value))
        level_edit = st.selectbox("Cấp độ", available_levels, index=available_levels.index(level_value))

        if st.button("Lưu cập nhật"):
            try:
                engine = get_engine()
                with engine.begin() as conn:
                    conn.execute(text("""
                        UPDATE employees
                        SET amann_id = :amann_id,
                            name = :name,
                            title = :title,
                            level = :level
                        WHERE amann_id = :original_amann_id
                    """), {
                        "amann_id": amann_id_edit.strip(),
                        "name": name_edit.strip(),
                        "title": title_edit.strip(),
                        "level": level_edit.strip(),
                        "original_amann_id": selected_employee['amann_id']
                    })
                st.success("Cập nhật thành công!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi cập nhật: {str(e)}")
