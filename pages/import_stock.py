import pandas as pd
import streamlit as st
from sqlalchemy import text
from database import get_engine
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------- TẢI DỮ LIỆU TỪ DATABASE ------------------------

def load_machine_types(engine):
    query = "SELECT id, machine FROM machine_type"
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
    query = "SELECT amann_id, name FROM employees"
    return pd.read_sql_query(text(query), engine)

def load_import_stock_data(engine):
    query = """
    SELECT DATE(ie.date) AS import_date, sp.material_no, SUM(ie.quantity) AS total_quantity_imported
    FROM import_export ie
    JOIN spare_parts sp ON ie.part_id = sp.material_no
    WHERE ie.im_ex_flag = 1
    GROUP BY DATE(ie.date), sp.material_no
    """
    return pd.read_sql_query(text(query), engine)

# ---------------------- GIAO DIỆN TRANG VẬT LIỆU ------------------------
def fetch_import_history(engine, year=None, quarter=None):
    with engine.connect() as conn:
        query = """
            SELECT 
                ie.date, 
                sp.material_no as part_id, 
                sp.description, 
                ie.quantity, 
                ie.im_ex_flag,
                e.name as employee_name, 
                mp.mc_pos, 
                ie.reason
            FROM import_export ie
            JOIN spare_parts sp ON ie.part_id = sp.material_no
            LEFT JOIN employees e ON ie.empl_id = e.amann_id
            LEFT JOIN machine_pos mp ON ie.mc_pos_id = mp.mc_pos
            WHERE ie.im_ex_flag = 1  -- chỉ lấy nhập kho
        """
        params = {}

        if year:
            query += " AND YEAR(ie.date) = :year"
            params['year'] = year

        if quarter:
            quarter_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
            quarter_num = quarter_map.get(quarter)
            if quarter_num is None:
                raise ValueError(f"Quarter '{quarter}' không hợp lệ. Phải là Q1, Q2, Q3 hoặc Q4.")
            start_month = (quarter_num - 1) * 3 + 1
            end_month = start_month + 2
            query += " AND MONTH(ie.date) BETWEEN :start_month AND :end_month"
            params['start_month'] = start_month
            params['end_month'] = end_month

        query += " ORDER BY ie.date DESC"

        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df
def show_material_page():
    st.markdown("<h1 style='text-align: center;'>Nhập kho</h1>", unsafe_allow_html=True)
    engine = get_engine()

    spare_parts = load_spare_parts(engine)
    machine_types = load_machine_types(engine)
    employees = load_employees(engine)
    import_stock_data = load_import_stock_data(engine)

    def plot_import_chart(import_stock_data):
        import_stock_data = import_stock_data[import_stock_data['total_quantity_imported'] > 0]
        import_stock_data['import_date'] = pd.to_datetime(import_stock_data['import_date'])
        import_stock_data['year'] = import_stock_data['import_date'].dt.year
        import_stock_data['month'] = import_stock_data['import_date'].dt.month

        years_in_data = sorted(import_stock_data['year'].unique())
        years = sorted(set(years_in_data) | set(range(2020, 2031)))

        months = list(range(1, 13))

        # Khởi tạo session state nếu chưa có
        if "selected_year" not in st.session_state:
            st.session_state.selected_year = years[0]
        if "selected_month" not in st.session_state:
            st.session_state.selected_month = 1

        # CSS style cho nút ô vuông (nếu cần)
        st.markdown("""
        <style>
        .square-button {
            border: 1px solid #999;
            background-color: white;
            padding: 0.5rem 1.2rem;
            margin: 0.2rem;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
            text-align: center;
        }
        .square-button:hover {
            background-color: #eee;
        }
        .selected {
            background-color: #333 !important;
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)

        col_year, col_month = st.columns(2)

        with col_year:
            selected_year = st.selectbox("Năm", years, index=years.index(st.session_state.selected_year))
            st.session_state.selected_year = selected_year

        with col_month:
            month_labels = [f"{m:02d}" for m in months]
            selected_month = st.selectbox("Tháng", month_labels, index=st.session_state.selected_month - 1)
            st.session_state.selected_month = int(selected_month)

        # Lọc dữ liệu theo năm và tháng đã chọn
        filtered_data = import_stock_data[
            (import_stock_data['year'] == st.session_state.selected_year) &
            (import_stock_data['month'] == st.session_state.selected_month)
        ]

        total_stock = filtered_data['total_quantity_imported'].sum()

        st.markdown(f"""
            <div style='
                background-color: #38a3a5;
                padding: 20px;
                font-size: 22px;
                color: #f8f7ff;
                font-weight: bold;
                text-align: center;
                border-radius: 12px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            '>
                Tổng nhập kho tháng {st.session_state.selected_month} năm {st.session_state.selected_year}: 
        <span style='color: #f8f7ff'>{int(total_stock):,} cái</span>
    </div>
""", unsafe_allow_html=True)



    # Gọi hàm hiển thị biểu đồ
    plot_import_chart(import_stock_data)




    
    st.markdown("---")

    col1, col2 = st.columns(2)
    # Chèn CSS để đổi màu chữ thành trắng
    st.markdown("""
        <style>
        /* Đổi màu label thành trắng */
        label, p, span {
            color: white !important;
        }

        /* Có thể tùy chỉnh thêm cho form nếu cần */
        .stTextInput>div>div>input {
            color: black; /* text trong ô input giữ nguyên đen nếu bạn muốn */
            background-color: #f0f2f6;
        }
        </style>
    """, unsafe_allow_html=True)

   # ---------------------- THÊM MỚI VẬT LIỆU ------------------------
    with col1:
        st.subheader("Thêm mới vật liệu")
        with st.expander("Mở form"):
            new_material_no = st.text_input("Mã vật liệu")
            new_description = st.text_input("Mô tả vật liệu")
            
            machine_options = ['Chọn loại máy'] + machine_types['machine'].tolist()
            selected_machine = st.selectbox("Loại máy sử dụng", machine_options, key="machine_select")
            
            machine_type_id = (
                machine_types[machine_types['machine'] == selected_machine]['id'].values[0]
                if selected_machine != 'Chọn loại máy' else None
            )

            new_part_no = st.text_input("Part No")
            new_bin = st.text_input("Vị trí lưu (Bin)")
            new_cost_center = st.text_input("Mã trung tâm chi phí")
            new_price = st.number_input("Đơn giá ($)", min_value=0.0, step=0.01)
            new_stock = st.number_input("Số lượng nhập", min_value=0, step=1)
            new_safety_stock = st.number_input("Tồn kho an toàn", min_value=0, step=1)
            
            safety_check = st.radio("Có kiểm tra tồn kho an toàn không?", ("Có", "Không"))

            selected_employee = st.selectbox(
                "Người thực hiện thao tác", 
                employees.apply(lambda x: f"{x['amann_id']} - {x['name']}", axis=1).tolist(), 
                key="employee_select"
            )

            if st.button("✅ Xác nhận thêm mới"):
                if new_material_no and new_description and machine_type_id:
                    part_no = new_part_no if new_part_no else "Không có"
                    empl_id = selected_employee.split(" - ")[0]
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    with engine.begin() as conn:
                        # Thêm vật liệu mới vào bảng spare_parts
                        conn.execute(text(""" 
                            INSERT INTO spare_parts 
                            (material_no, description, part_no, machine_type_id, bin, cost_center, price, stock, 
                            safety_stock, safety_stock_check, import_date) 
                            VALUES (:material_no, :description, :part_no, :machine_type_id, :bin, :cost_center, 
                                    :price, :stock, :safety_stock, :safety_stock_check, :import_date)
                        """), {
                            "material_no": new_material_no,
                            "description": new_description,
                            "part_no": part_no,
                            "machine_type_id": machine_type_id,
                            "bin": new_bin,
                            "cost_center": new_cost_center,
                            "price": new_price,
                            "stock": new_stock,
                            "safety_stock": new_safety_stock,
                            "safety_stock_check": 1 if safety_check == "Có" else 0,
                            "import_date": current_time
                        })

                        # Nếu có tồn kho ban đầu thì ghi nhận vào lịch sử nhập kho
                        if new_stock > 0:
                            conn.execute(text("""
                                INSERT INTO import_export (part_id, quantity, mc_pos_id, empl_id, date, reason, im_ex_flag)
                                VALUES (:part_id, :quantity, NULL, :empl_id, :date, 'Thêm vật liệu mới', 1)
                            """), {
                                "part_id": new_material_no,
                                "quantity": new_stock,
                                "empl_id": empl_id,
                                "date": current_time
                            })

                    st.success(f"✅ Đã thêm vật liệu **{new_material_no}** và ghi nhận lịch sử nhập kho.")
                    st.rerun()
                else:
                    st.error("⚠️ Vui lòng nhập đầy đủ thông tin và chọn loại máy hợp lệ.")


    # ---------------------- NHẬP KHO VẬT LIỆU CÓ SẴN ------------------------
    with col2:
        st.subheader("Nhập kho linh kiện")
        with st.expander("Form nhập kho"):
            keyword = st.text_input("🔎 Tìm kiếm linh kiện (Material No hoặc Mô tả)")
            filtered = spare_parts[
                spare_parts['material_no'].str.contains(keyword, case=False, na=False) |
                spare_parts['description'].str.contains(keyword, case=False, na=False)
            ] if keyword else spare_parts

            if not filtered.empty:
                part_options = filtered.apply(
                    lambda x: f"{x['part_no']} - {x['material_no']} - {x['description']}", axis=1
                ).tolist()
                selected_part = st.selectbox("Chọn linh kiện để nhập", part_options, key="part_select")
            else:
                st.warning("⚠️ Không tìm thấy linh kiện phù hợp.")
                selected_part = None
            quantity = st.number_input("Số lượng nhập", min_value=1, key="quantity_input")
            input_price = st.number_input("Đơn giá ($)", min_value=0.0, step=0.01, key="input_price_input")


            import_employee = st.selectbox(
                "Người thực hiện thao tác", 
                employees.apply(lambda x: f"{x['amann_id']} - {x['name']}", axis=1).tolist(), 
                key="import_employee_select"
            )
            if st.button("📥 Xác nhận nhập kho"):
                if selected_part and quantity > 0:
                    part_id = selected_part.split(" - ")[1].strip()
                    empl_id = import_employee.split(" - ")[0].strip()
                    current_time = datetime.now()
                    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')

                    with engine.begin() as conn:
                        # Kiểm tra đã có bản ghi nhập kho trong tháng hiện tại cho part_id chưa
                        existing_record = conn.execute(text("""
                            SELECT id, quantity FROM import_export
                            WHERE part_id = :part_id
                            AND EXTRACT(YEAR FROM date) = :year
                            AND EXTRACT(MONTH FROM date) = :month
                            AND im_ex_flag = 1
                            LIMIT 1
                        """), {
                            "part_id": part_id,
                            "year": current_time.year,
                            "month": current_time.month
                        }).fetchone()

                        if existing_record:
                            # Cộng dồn số lượng và cập nhật lại thời gian nhập kho
                            record_id = existing_record.id
                            conn.execute(text("""
                                UPDATE import_export
                                SET quantity = quantity + :quantity,
                                    date = :date
                                WHERE id = :id
                            """), {
                                "quantity": quantity,
                                "date": current_time_str,
                                "id": record_id
                            })
                        else:
                            # Thêm bản ghi mới nếu chưa có
                            conn.execute(text("""
                                INSERT INTO import_export (part_id, quantity, mc_pos_id, empl_id, date, reason, im_ex_flag)
                                VALUES (:part_id, :quantity, NULL, :empl_id, :date, 'Nhập kho', 1)
                            """), {
                                "part_id": part_id,
                                "quantity": quantity,
                                "empl_id": empl_id,
                                "date": current_time_str
                            })

                        # Cập nhật tồn kho spare_parts
                        result = conn.execute(text("""
                            UPDATE spare_parts
                            SET stock = COALESCE(stock, 0) + :quantity,
                                price = :price,
                                import_date = :import_date
                            WHERE material_no = :part_id
                        """), {
                            "quantity": quantity,
                            "price": input_price,
                            "part_id": part_id,
                            "import_date": current_time_str
                        })

                        if result.rowcount == 0:
                            conn.execute(text("""
                                INSERT INTO spare_parts (material_no, stock, price, import_date)
                                VALUES (:part_id, :quantity, :price, :import_date)
                            """), {
                                "part_id": part_id,
                                "quantity": quantity,
                                "price": input_price,
                                "import_date": current_time_str
                            })

                    st.success("✅ Nhập kho thành công và đã cập nhật đơn giá.")
                    st.rerun()
                else:
                    st.error("Vui lòng chọn phụ tùng và nhập số lượng hợp lệ.")




    st.markdown("---")
    st.subheader("Lịch sử nhập kho")

    # Thêm ô nhập liệu tìm kiếm theo material_no hoặc description
    search_keyword = st.text_input("Tìm kiếm theo Mã phụ tùng/Mô tả", "")

    # Lấy dữ liệu nhập kho từ DB
    import_history_df = fetch_import_history(engine)

    # Đảm bảo cột date dạng datetime
    import_history_df['date'] = pd.to_datetime(import_history_df['date'], errors='coerce')
    import_history_df['year'] = import_history_df['date'].dt.year
    import_history_df['month'] = import_history_df['date'].dt.month

    # Lấy bảng spare_parts có material_no và bin
    query_spare_part = "SELECT material_no, bin FROM spare_parts"
    spare_part_df = pd.read_sql(query_spare_part, engine)

    # Chuẩn hóa dữ liệu dạng string, loại bỏ khoảng trắng thừa
    import_history_df['part_id'] = import_history_df['part_id'].astype(str).str.strip()
    spare_part_df['material_no'] = spare_part_df['material_no'].astype(str).str.strip()

    # Merge để lấy thông tin bin
    import_history_df = import_history_df.merge(
        spare_part_df[['material_no', 'bin']],
        left_on='part_id',
        right_on='material_no',
        how='left'
    )

    # Xóa cột thừa và thay thế NaN
    import_history_df.drop(columns=['material_no'], inplace=True)
    import_history_df['bin'] = import_history_df['bin'].fillna('Chưa xác định')

    # Lọc theo tháng và năm người dùng chọn
    filtered_data = import_history_df[
        (import_history_df['year'] == st.session_state.selected_year) &
        (import_history_df['month'] == st.session_state.selected_month)
    ]

    # Nếu có từ khóa tìm kiếm, lọc thêm theo material_no hoặc description
    if search_keyword.strip() != "":
        mask = (
            filtered_data['part_id'].str.contains(search_keyword, case=False, na=False) |
            filtered_data['description'].str.contains(search_keyword, case=False, na=False)
        )
        filtered_data = filtered_data[mask]

    if not filtered_data.empty:
        # Đổi tên cột để hiển thị
        display_df = filtered_data.rename(columns={
            'date': 'Ngày nhập kho',
            'part_id': 'Mã phụ tùng',
            'description': 'Mô tả',
            'quantity': 'Số lượng',
            'Type': 'Loại',
            'bin': 'Vị trí lưu (BIN)',
            'employee_name': 'Nhân viên',
            'reason': 'Lý do'
        }).copy()

        # Định dạng ngày tháng đầy đủ
        display_df['Ngày nhập kho'] = pd.to_datetime(display_df['Ngày nhập kho']).dt.strftime("%Y-%m-%d %H:%M")

        # Chọn cột hiển thị
        columns_to_show = ['Ngày nhập kho', 'Mã phụ tùng', 'Mô tả', 'Số lượng', 'Loại', 'Vị trí lưu (BIN)', 'Nhân viên', 'Lý do']
        columns_to_show = [col for col in columns_to_show if col in display_df.columns]

        # Hiển thị bảng dữ liệu
        st.dataframe(display_df[columns_to_show].sort_values(by='Ngày nhập kho', ascending=False), use_container_width=True)

        # 💅 CSS tùy chỉnh cho nút tải xuống
        st.markdown("""
            <style>
            div.stDownloadButton > button:first-child {
                background-color: #20c997;
                color: white;
                border: none;
            }
            div.stDownloadButton > button:first-child:hover {
                background-color: #17a2b8;
                color: white;
            }
            </style>
            """, unsafe_allow_html=True)

        # ✅ Nút xuất Excel
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            display_df[columns_to_show].to_excel(writer, index=False, sheet_name='Lich_su_nhap_kho')
        output.seek(0)

        st.download_button(
            label="📤 Tải xuống Excel",
            data=output,
            file_name=f"Lich_su_nhap_kho_{st.session_state.selected_month}_{st.session_state.selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("Không có dữ liệu nhập kho trong tháng đã chọn.")
