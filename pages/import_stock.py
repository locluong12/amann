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
    st.markdown("<h1 style='text-align: center;'>Import Stock</h1>", unsafe_allow_html=True)
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

        def get_quarter(month):
            if 1 <= month <= 3:
                return "Q1"
            elif 4 <= month <= 6:
                return "Q2"
            elif 7 <= month <= 9:
                return "Q3"
            else:
                return "Q4"

        import_stock_data['quarter'] = import_stock_data['month'].apply(get_quarter)

        # Lấy danh sách năm và quý
        years = sorted(import_stock_data['year'].unique())
        quarters = ["Q1", "Q2", "Q3", "Q4"]

        # Khởi tạo session state
        if "selected_year" not in st.session_state:
            st.session_state.selected_year = years[0]
        if "selected_quarter" not in st.session_state:
            st.session_state.selected_quarter = "Q1"

        # CSS style cho nút ô vuông
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
        }
        .square-button:hover {
            background-color: #eee;
        }
        .selected {
            background-color: #333;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        years = sorted(import_stock_data['year'].unique())
        quarters = ["Q1", "Q2", "Q3", "Q4"]

        # Tạo 2 cột ngang: Năm | Quý
        col_year, col_quarter = st.columns([2, 2])

        with col_year:
            st.markdown("<h4 style='text-align: center;'>Chọn năm</h4>", unsafe_allow_html=True)

            year_cols = st.columns(len(years))
            for i, year in enumerate(years):
                is_selected = st.session_state.selected_year == year
                btn_label = f"**{year}**" if is_selected else str(year)
                with year_cols[i]:
                    if st.button(btn_label, key=f"year_{year}"):
                        st.session_state.selected_year = year

        with col_quarter:
            st.markdown("<h4 style='text-align: center;'>Chọn quý</h4>", unsafe_allow_html=True)

            quarter_cols = st.columns(len(quarters))
            for i, quarter in enumerate(quarters):
                is_selected = st.session_state.selected_quarter == quarter
                btn_label = f"**{quarter}**" if is_selected else quarter
                with quarter_cols[i]:
                    if st.button(btn_label, key=f"quarter_{quarter}"):
                        st.session_state.selected_quarter = quarter


        # Lọc dữ liệu
        selected_year = st.session_state.selected_year
        selected_quarter = st.session_state.selected_quarter


        filtered_data = import_stock_data[
            (import_stock_data['year'] == selected_year) &
            (import_stock_data['quarter'] == selected_quarter)
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
                Total Stock {selected_quarter} năm {selected_year}: 
                <span style='color: #f8f7ff'>{int(total_stock):,}</span>
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
        with st.expander("Form thêm mới"):
            new_material_no = st.text_input("Material No")
            new_description = st.text_input("Description")
            machine_options = ['Chọn loại máy'] + machine_types['machine'].tolist()
            selected_machine = st.selectbox("Loại máy", machine_options, key="machine_select")
            machine_type_id = (
                machine_types[machine_types['machine'] == selected_machine]['id'].values[0]
                if selected_machine != 'Chọn loại máy' else None
            )

            new_part_no = st.text_input("Part No")
            new_bin = st.text_input("Bin")
            new_cost_center = st.text_input("Cost Center")
            new_price = st.number_input("Price", min_value=0.0, step=0.01)
            new_stock = st.number_input("Stock", min_value=0, step=1)
            new_safety_stock = st.number_input("Safety Stock", min_value=0, step=1)
            safety_check = st.radio("Kiểm tra tồn kho an toàn?", ("Yes", "No"))
            selected_employee = st.selectbox(
                "Người thực hiện", 
                employees.apply(lambda x: f"{x['amann_id']} - {x['name']}", axis=1).tolist(), 
                key="employee_select"
            )

            if st.button("✅ Xác nhận thêm vật liệu mới"):
                if new_material_no and new_description and machine_type_id:
                    part_no = new_part_no if new_part_no else "N/A"
                    empl_id = selected_employee.split(" - ")[0]
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    with engine.begin() as conn:
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
                            "safety_stock_check": 1 if safety_check == "Yes" else 0,
                            "import_date": current_time
                        })

                        # Ghi nhận lịch sử nhập kho ban đầu
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

                    st.success(f"✅ Đã thêm vật liệu {new_material_no} và cập nhật lịch sử nhập kho.")
                    st.rerun()
                else:
                    st.error("⚠️ Vui lòng nhập đầy đủ thông tin và chọn loại máy hợp lệ.")

    # ---------------------- NHẬP KHO VẬT LIỆU CÓ SẴN ------------------------
    with col2:
        st.subheader("Nhập kho linh kiện")
        with st.expander("Form nhập kho"):
            keyword = st.text_input("Tìm kiếm linh kiện (Material No hoặc Description)")
            filtered = spare_parts[
                spare_parts['material_no'].str.contains(keyword, case=False, na=False) |
                spare_parts['description'].str.contains(keyword, case=False, na=False)
            ] if keyword else spare_parts

            if not filtered.empty:
                part_options = filtered.apply(lambda x: f"{x['part_no']} - {x['material_no']} - {x['description']}", axis=1).tolist()
                selected_part = st.selectbox("Chọn linh kiện", part_options, key="part_select")
            else:
                st.warning("Không tìm thấy linh kiện phù hợp.")
                selected_part = None

            quantity = st.number_input("Số lượng nhập", min_value=1)
            import_employee = st.selectbox(
                "Người thực hiện", 
                employees.apply(lambda x: f"{x['amann_id']} - {x['name']}", axis=1).tolist(), 
                key="import_employee_select"
            )

            if st.button("📥 Xác nhận nhập kho"):
                if selected_part:
                    part_id = selected_part.split(" - ")[1]  # material_no
                    empl_id = import_employee.split(" - ")[0]
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    with engine.begin() as conn:
                        conn.execute(text(""" 
                            INSERT INTO import_export (part_id, quantity, mc_pos_id, empl_id, date, reason, im_ex_flag)
                            VALUES (:part_id, :quantity, NULL, :empl_id, :date, 'Nhập kho', 1)
                        """), {
                            "part_id": part_id,
                            "quantity": quantity,
                            "empl_id": empl_id,
                            "date": current_time
                        })

                        conn.execute(text(""" 
                            UPDATE spare_parts 
                            SET stock = stock + :quantity, import_date = :import_date 
                            WHERE material_no = :part_id
                        """), {
                            "quantity": quantity,
                            "part_id": part_id,
                            "import_date": current_time
                        })

                    st.success("✅ Nhập kho thành công.")
                    st.rerun()
                

         
