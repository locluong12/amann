import io
import pandas as pd
import streamlit as st
from sqlalchemy import text
from database import get_engine
from datetime import datetime
from io import BytesIO

def load_machine_types(engine):
    query = "SELECT mc_pos_id, mc_pos FROM machine_pos"
    return pd.read_sql_query(text(query), engine)

def load_spare_parts(engine):
    query = """
        SELECT sp.material_no, sp.description, mt.machine, sp.part_no, sp.bin, sp.cost_center,
               sp.price, sp.stock, sp.safety_stock, sp.safety_stock_check
        FROM spare_parts sp
        JOIN machine_type mt ON sp.machine_type_id = mt.id
    """
    return pd.read_sql_query(text(query), engine)

def load_employees(engine):
    return pd.read_sql('SELECT amann_id, name FROM employees', engine)

def show_material_page():
    st.markdown("<h1 style='text-align: center;'>Import Stock</h1>", unsafe_allow_html=True)
    engine = get_engine()

    machine_types = load_machine_types(engine)
    spare_parts = load_spare_parts(engine)
    employees = load_employees(engine)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Thêm mới vật liệu")
        with st.expander("Form nhập liệu mới"):
            new_material_no = st.text_input("Material No", key="add_material_no")
            new_description = st.text_input("Description", key="add_description")
            machine_options = ['Chọn loại máy'] + machine_types['mc_pos'].tolist()
            selected_machine = st.selectbox("Loại máy", machine_options, key="add_machine_pos")

            # Xử lý mc_pos_id: nếu không có loại máy thì mc_pos_id = None
            if selected_machine != 'Chọn loại máy':
                filtered_machine = machine_types[machine_types['mc_pos'] == selected_machine]
                if not filtered_machine.empty:
                    new_machine_pos_id = filtered_machine['mc_pos_id'].values[0]
                else:
                    new_machine_pos_id = None
            else:
                new_machine_pos_id = None

            new_part_no = st.text_input("Part No", key="add_part_no")
            new_bin = st.text_input("Bin", key="add_bin")
            new_cost_center = st.text_input("Cost Center", key="add_cost_center")
            new_price = st.number_input("Price", min_value=0.0, step=0.01, key="add_price")
            new_stock = st.number_input("Stock", min_value=0, step=1, key="add_stock")
            new_safety_stock = st.number_input("Safety Stock", min_value=0, step=1, key="add_safety_stock")
            safety_stock_check = st.radio("Kiểm tra tồn kho an toàn?", ("Yes", "No"), key="add_safety_check")
            selected_employee = st.selectbox(
                "Người thực hiện (ghi lịch sử)",
                employees.apply(lambda x: f"{x['amann_id']} - {x['name']}", axis=1).tolist(),
                key="add_employee"
            )

            if st.button("✅ Xác nhận thêm vật liệu mới", key="confirm_add_material"):
                if new_material_no and new_description and new_machine_pos_id:
                    if not new_part_no:
                        new_part_no = "N/A"

                    empl_id = int(selected_employee.split(" - ")[0])
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    with engine.begin() as conn:
                        conn.execute(text(""" 
                            INSERT INTO spare_parts 
                            (material_no, description, part_no, machine_type_id, bin, cost_center, price, stock, safety_stock, safety_stock_check) 
                            VALUES (:material_no, :description, :part_no, :machine_pos_id, :bin, :cost_center, :price, :stock, :safety_stock, :safety_stock_check)
                        """), {
                            "material_no": new_material_no,
                            "description": new_description,
                            "part_no": new_part_no,
                            "machine_pos_id": new_machine_pos_id,
                            "bin": new_bin,
                            "cost_center": new_cost_center,
                            "price": new_price,
                            "stock": new_stock,
                            "safety_stock": new_safety_stock,
                            "safety_stock_check": safety_stock_check
                        })

                        result = conn.execute(text("SELECT LAST_INSERT_ID()"))
                        new_part_id = result.scalar()

                        if new_stock > 0:
                            conn.execute(text(""" 
                                INSERT INTO import_export (part_id, quantity, mc_pos_id, empl_id, date, reason, im_ex_flag) 
                                VALUES (:part_id, :quantity, :mc_pos_id, :empl_id, :date, :reason, 1)
                            """), {
                                "part_id": new_part_id,
                                "quantity": new_stock,
                                "mc_pos_id": new_machine_pos_id,  # Giữ lại mc_pos_id
                                "empl_id": empl_id,
                                "date": current_time,
                                "reason": "Nhập kho"
                            })

                    st.success(f"✅ Đã thêm vật liệu {new_material_no} và cập nhật nhập kho!")
                else:
                    st.error("⚠️ Vui lòng nhập đầy đủ thông tin và chọn loại máy hợp lệ!")

    with col2:
        st.markdown("### Nhập kho linh kiện")
        with st.expander("Nhập kho linh kiện mới"):
            search_keyword = st.text_input("Tìm kiếm theo Material No hoặc Description", key="search_existing")

            if search_keyword:
                filtered_parts = spare_parts[
                    spare_parts['material_no'].str.contains(search_keyword, case=False, na=False) |
                    spare_parts['description'].str.contains(search_keyword, case=False, na=False)
                ]
            else:
                filtered_parts = spare_parts

            if not filtered_parts.empty:
                part_display = filtered_parts.apply(lambda x: f"{x['material_no']} - {x['description']}", axis=1).tolist()
                part_choice = st.selectbox("Chọn linh kiện", part_display, key="select_existing_part")
            else:
                st.warning("🔎 Không tìm thấy linh kiện phù hợp.")
                part_choice = None

            quantity = st.number_input("Số lượng nhập", min_value=1, value=1, key="import_quantity")
            employee_choice = st.selectbox("Người thực hiện", employees.apply(lambda x: f"{x['amann_id']} - {x['name']}", axis=1).tolist(), key="import_employee")

            if st.button("📥 Xác nhận nhập kho", key="confirm_import"):
                if part_choice:
                    selected_row = filtered_parts[
                        filtered_parts.apply(lambda x: f"{x['material_no']} - {x['description']}", axis=1) == part_choice
                    ].iloc[0]

                    part_id = selected_row['material_no']

                    filtered_mc_pos = machine_types[machine_types['mc_pos'] == selected_row['machine']]
                    if not filtered_mc_pos.empty:
                        mc_pos_id = filtered_mc_pos['mc_pos_id'].values[0]
                    else:
                        st.error(f"⚠️ Không tìm thấy loại máy tương ứng với '{selected_row['machine']}'")
                        return

                    empl_id_str = employee_choice.split(" - ")[0]

                    if empl_id_str.startswith('A'):  # xử lý chuỗi như A001
                        empl_id = empl_id_str
                    elif empl_id_str.isdigit():
                        empl_id = int(empl_id_str)
                    else:
                        st.error(f"⚠️ Mã nhân viên '{empl_id_str}' không hợp lệ.")
                        empl_id = None

                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    if empl_id:
                        with engine.begin() as conn:
                            conn.execute(text(""" 
                                INSERT INTO import_export (part_id, quantity, mc_pos_id, empl_id, date, reason, im_ex_flag) 
                                VALUES (:part_id, :quantity, :mc_pos_id, :empl_id, :date, :reason, 1) 
                            """), {
                                "part_id": part_id,
                                "quantity": quantity,
                                "mc_pos_id": mc_pos_id,
                                "empl_id": empl_id,
                                "date": current_time,
                                "reason": "Nhập kho"
                            })

                            conn.execute(text(""" 
                                UPDATE spare_parts SET stock = stock + :quantity WHERE material_no = :part_id 
                            """), {
                                "quantity": quantity,
                                "part_id": part_id
                            })

                        st.success("✅ Đã nhập kho thành công!")
                else:
                    st.warning("🔎 Không tìm thấy linh kiện.")


                
    st.markdown("---")

