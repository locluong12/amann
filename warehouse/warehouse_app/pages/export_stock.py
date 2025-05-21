import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from database import get_engine
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta
import io
# Hàm lấy dữ liệu lịch sử nhập/xuất kho
def fetch_import_export_history(engine, year=None, quarter=None):
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
            WHERE 1=1
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


def show_export_stock():
    st.markdown("<h1 style='text-align: center;'>Export Stock</h1>", unsafe_allow_html=True)
    engine = get_engine()

    # ====== Load dữ liệu cơ bản ======
    with engine.begin() as conn:
        spare_parts = pd.read_sql('SELECT material_no, description, stock, price FROM spare_parts', conn)
        employees = pd.read_sql('SELECT amann_id, name FROM employees', conn)
        machine_data = pd.read_sql(''' 
            SELECT m.name AS machine_name, mp.mc_pos AS mc_pos_id, mp.mc_pos 
            FROM machine m 
            JOIN machine_pos mp ON m.group_mc_id = mp.mc_id
        ''', conn)

   # Khởi tạo state nếu chưa có
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = datetime.today().year if datetime.today().year >= 2025 else 2025
    if 'selected_quarter' not in st.session_state:
        st.session_state.selected_quarter = 'Q2'

    years = [2023, 2024, 2025]
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']

    st.subheader("Bộ lọc năm và quý")
    cols = st.columns(7)

    # Nút chọn năm
    for i, year in enumerate(years):
        if cols[i].button(f"{year}", key=f"year_{year}"):
            st.session_state.selected_year = year  # Không cần st.rerun()

    # Nút chọn quý
    for j, quarter in enumerate(quarters):
        if cols[3 + j].button(f"{quarter}", key=f"quarter_{quarter}"):
            st.session_state.selected_quarter = quarter  # Không cần st.rerun()

    st.markdown("<div style='margin-top:30px'></div>", unsafe_allow_html=True)  # khoảng cách 30px
    selected_year = st.session_state.selected_year
    selected_quarter = st.session_state.selected_quarter

    # Tính ngày bắt đầu và kết thúc theo quý
    quarter_month_map = {
        'Q1': (1, 3),
        'Q2': (4, 6),
        'Q3': (7, 9),
        'Q4': (10, 12)
    }
    start_month, end_month = quarter_month_map[selected_quarter]
    start_date = datetime(selected_year, start_month, 1)
    end_date = datetime(selected_year, end_month + 1, 1) - timedelta(days=1) if end_month < 12 else datetime(selected_year, 12, 31)

    # ====== Lấy dữ liệu xuất kho và chi phí xuất kho theo khoảng thời gian ======
    def fetch_export_data():
        with engine.begin() as conn:
            export_stats = pd.read_sql(''' 
                SELECT 
                    ie.part_id, 
                    sp.material_no, 
                    sp.description, 
                    SUM(ie.quantity) AS total_quantity
                FROM import_export ie
                JOIN spare_parts sp ON ie.part_id = sp.material_no
                WHERE ie.im_ex_flag = 0
                AND ie.date BETWEEN %s AND %s
                GROUP BY ie.part_id, sp.material_no, sp.description
            ''', conn, params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

            cost_data = pd.read_sql(''' 
                SELECT 
                    DATE(ie.date) AS export_day,
                    ie.part_id,
                    SUM(ie.quantity) AS total_qty,
                    sp.price
                FROM import_export ie
                JOIN spare_parts sp ON ie.part_id = sp.material_no
                WHERE ie.im_ex_flag = 0
                AND ie.date BETWEEN %s AND %s
                GROUP BY export_day, ie.part_id, sp.price
                ORDER BY export_day
            ''', conn, params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))

        return export_stats, cost_data


    export_stats, cost_data = fetch_export_data()

    
    

   # ====== Tính tổng xuất kho và tổng chi phí ======
    total_export_quantity = export_stats['total_quantity'].sum() if not export_stats.empty else 0
    total_export_cost = (cost_data['total_qty'] * cost_data['price']).sum() if not cost_data.empty else 0
    # Hiển thị thông báo dưới bộ lọc
    st.markdown(f"""
    <div style='
        background-color: #3b8c6e;
        padding: 20px;
        font-size: 20px;
        color: #f0fdf4;
        font-weight: bold;
        text-align: center;
        border-radius: 12px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    '>
        Total Export {selected_quarter} năm {selected_year}: 
        <span style='color: #ffffff'>{int(total_export_quantity):,}</span> linh kiện, 
        Total Cost: <span style='color: #ffffff'>{total_export_cost:,.0f}</span>
    </div>
""", unsafe_allow_html=True)
    # ====== Hiển thị 2 ô tổng tiền và tổng xuất kho ngay bên dưới bộ lọc ======
    col_total_1, col_total_2 = st.columns(2)

    box_style_1 = """
        background-color: #38a3a5;
        padding: 20px;
        font-size: 22px;
        color: #f8f7ff;
        font-weight: bold;
        text-align: center;
        border-radius: 12px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    """

    box_style_2 = """
        background-color: #006d77;
        padding: 20px;
        font-size: 22px;
        color: #fff;
        font-weight: bold;
        text-align: center;
        border-radius: 12px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    """

    with col_total_1:
        st.markdown(f"""
            <div style="{box_style_1}">
                Total Value<br>
                <span style="font-size:28px;">{total_export_cost:,.0f}</span>
            </div>
        """, unsafe_allow_html=True)

    with col_total_2:
        st.markdown(f"""
            <div style="{box_style_2}">
                Total Export kho<br>
                <span style="font-size:28px;">{total_export_quantity:,}</span>
            </div>
        """, unsafe_allow_html=True)

    # ====== Tìm kiếm linh kiện ======
    st.markdown('<p style="color:white; margin-bottom:4px;">Tìm linh kiện theo Material_No/Description</p>', unsafe_allow_html=True)
    search = st.text_input("", key="search_input", label_visibility="hidden")

    parts = spare_parts[
        spare_parts['description'].str.contains(search, case=False, na=False) |
        spare_parts['material_no'].str.contains(search, case=False, na=False)
    ] if search else spare_parts

    if not parts.empty:
        part_choice = st.selectbox(
            "", 
            parts.apply(lambda x: f"{x['material_no']} - {x['description']} (Tồn: {x['stock']})", axis=1),
            key="part_choice",
            label_visibility="hidden"
        )
        part_id = part_choice.split(' - ')[0]
    else:
        st.markdown('<p style="color:white;">⚠️ Không có linh kiện phù hợp.</p>', unsafe_allow_html=True)

    # ====== Nhân viên ======
    if not employees.empty:
        st.markdown('<p style="color:white; margin-bottom:4px;">Người thực hiện</p>', unsafe_allow_html=True)
        empl_choice = st.selectbox(
            "",
            employees.apply(lambda x: f"{x['amann_id']} - {x['name']}", axis=1),
            key="empl_choice",
            label_visibility="hidden"
        )
        empl_id = empl_choice.split(' - ')[0]
    else:
        st.markdown('<p style="color:white;">⚠️ Không có dữ liệu nhân viên.</p>', unsafe_allow_html=True)

    # ====== Máy & vị trí ======
    if not machine_data.empty:
        st.markdown('<p style="color:white; margin-bottom:4px;">Chọn máy</p>', unsafe_allow_html=True)
        machine_selected = st.selectbox("", sorted(machine_data['machine_name'].unique()), key="machine_selected", label_visibility="hidden")

        pos_options = machine_data[machine_data['machine_name'] == machine_selected]['mc_pos'].tolist()
        st.markdown('<p style="color:white; margin-bottom:4px;">Chọn vị trí máy</p>', unsafe_allow_html=True)
        pos_selected = st.selectbox("", pos_options, key="pos_selected", label_visibility="hidden")

        mc_pos_row = machine_data[
            (machine_data['machine_name'] == machine_selected) & 
            (machine_data['mc_pos'] == pos_selected)
        ]
        mc_pos_id = mc_pos_row.iloc[0]['mc_pos_id'] if not mc_pos_row.empty else None
    else:
        st.markdown('<p style="color:white;">⚠️ Không có dữ liệu máy.</p>', unsafe_allow_html=True)

    # ====== Thông tin xuất kho ======
    st.markdown('<p style="color:white; margin-bottom:4px;">Số lượng xuất kho</p>', unsafe_allow_html=True)
    quantity = st.number_input("", min_value=1, value=1, key="quantity", label_visibility="hidden")

    is_foc = st.checkbox("Xuất kho miễn phí (FOC)", key="foc_checkbox")

    if not is_foc:
        st.markdown('<p style="color:white; margin-bottom:4px;">✏️ Nhập lý do xuất kho</p>', unsafe_allow_html=True)
        reason = st.text_input("", key="reason_input", label_visibility="hidden")
    else:
        reason = "FOC"

    if st.button("✅ Xác nhận xuất kho"):
        if not reason and not is_foc:
            st.markdown('<p style="color:white;">❌ Bạn phải nhập lý do xuất kho!</p>', unsafe_allow_html=True)
        else:
            with engine.begin() as conn:
                stock = conn.execute(text("SELECT stock FROM spare_parts WHERE material_no = :material_no"),
                                    {"material_no": part_id}).scalar()
                if not is_foc and quantity > stock:
                    st.markdown('<p style="color:white;">❌ Không đủ hàng trong kho!</p>', unsafe_allow_html=True)
                else:
                    now = datetime.now()
                    today_str = now.strftime('%Y-%m-%d')

                    # Kiểm tra xem đã có dòng giống chưa (cùng ngày, part, vị trí, nhân viên, reason)
                    existing_row = conn.execute(text("""
                        SELECT id FROM import_export 
                        WHERE 
                            part_id = :part_id AND 
                            mc_pos_id = :mc_pos_id AND 
                            empl_id = :empl_id AND 
                            reason = :reason AND 
                            DATE(date) = :today AND
                            im_ex_flag = 0
                    """), {
                        "part_id": part_id,
                        "mc_pos_id": mc_pos_id,
                        "empl_id": empl_id,
                        "reason": reason,
                        "today": today_str
                    }).fetchone()

                    if existing_row:
                        # Nếu đã tồn tại -> cập nhật (cộng dồn)
                        conn.execute(text("""
                            UPDATE import_export
                            SET quantity = quantity + :add_quantity
                            WHERE id = :row_id
                        """), {
                            "add_quantity": quantity,
                            "row_id": existing_row[0]
                        })
                    else:
                        # Nếu chưa có -> thêm mới
                        conn.execute(text("""
                            INSERT INTO import_export (date, part_id, quantity, im_ex_flag, empl_id, mc_pos_id, reason)
                            VALUES (:date, :part_id, :quantity, 0, :empl_id, :mc_pos_id, :reason)
                        """), {
                            "date": now,
                            "part_id": part_id,
                            "quantity": quantity,
                            "empl_id": empl_id,
                            "mc_pos_id": mc_pos_id,
                            "reason": reason
                        })

                    # Trừ kho nếu không phải FOC
                    if not is_foc:
                        conn.execute(text("""
                            UPDATE spare_parts
                            SET stock = stock - :quantity
                            WHERE material_no = :part_id
                        """), {
                            "quantity": quantity,
                            "part_id": part_id
                        })

                    st.success("✅ Xuất kho thành công!")
                   



    # --- Phần hiển thị bảng lịch sử nhập/xuất kho luôn có ---
    df_history = fetch_import_export_history(engine, year=selected_year, quarter=selected_quarter)

    if not df_history.empty:
        # Lọc chỉ những dòng xuất kho (im_ex_flag == 0)
        df_export = df_history[df_history['im_ex_flag'] == 0].copy()

        df_export['Type'] = 'Xuất kho'
        df_display = df_export[['date', 'part_id', 'description', 'quantity', 'Type', 'employee_name', 'mc_pos', 'reason']]

       
        df_display.columns = ['date', 'part_id', 'description', 'quantity', 'Type', 'employee_name', 'mc_pos', 'reason']

        st.markdown("### 📋 Lịch sử nhập/xuất kho")
        st.dataframe(df_display)

        # Nút xuất Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_display.to_excel(writer, sheet_name='Import_Export_History', index=False)
        output.seek(0)

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

    st.download_button(
        label="⬇️ Xuất Excel",
        data=output,
        file_name=f"Import_Export_History_{selected_year}_{selected_quarter}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
