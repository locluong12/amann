import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from database import get_engine
from io import BytesIO

def show_export_stock():
    st.markdown("<h1 style='text-align: center;'>Export Stock</h1>", unsafe_allow_html=True)
    engine = get_engine()

    with engine.begin() as conn:
        spare_parts = pd.read_sql('SELECT material_no, description, stock FROM spare_parts', conn)
        employees = pd.read_sql('SELECT amann_id, name FROM employees', conn)
        machine_data = pd.read_sql(''' 
            SELECT m.id AS mc_id, m.name AS machine_name,
                   mp.mc_pos_id, mp.mc_pos
            FROM machine m
            JOIN machine_pos mp ON m.id = mp.mc_id
        ''', conn)

    # ====== Chọn linh kiện ======
    search = st.text_input("Tìm linh kiện theo Material_No/Description")
    parts = spare_parts[
        spare_parts['description'].str.contains(search, case=False, na=False) |
        spare_parts['material_no'].str.contains(search, case=False, na=False)
    ] if search else spare_parts

    part_choice = st.selectbox("Chọn linh kiện để xuất", parts.apply(
        lambda x: f"{x['material_no']} - {x['description']} (Tồn: {x['stock']})", axis=1
    ))
    part_id = part_choice.split(' - ')[0]  # 'material_no' is being used as the unique identifier

    # ====== Chọn người thực hiện ======
    empl_choice = st.selectbox("Người thực hiện xuất kho", employees.apply(lambda x: f"{x['amann_id']} - {x['name']}", axis=1))
    empl_id = empl_choice.split(' - ')[0]  # Use 'amann_id' as employee identifier

    # ====== Chọn máy và vị trí ======
    machine_selected = st.selectbox("Chọn máy", sorted(machine_data['machine_name'].unique()))
    pos_options = machine_data[machine_data['machine_name'] == machine_selected]['mc_pos'].tolist()
    pos_selected = st.selectbox("Chọn vị trí máy", pos_options)

    mc_pos_row = machine_data[
        (machine_data['machine_name'] == machine_selected) & 
        (machine_data['mc_pos'] == pos_selected)
    ]
    mc_pos_id = int(mc_pos_row.iloc[0]['mc_pos_id']) if not mc_pos_row.empty else None

    # ====== Nhập số lượng ======
    quantity = st.number_input("Số lượng xuất kho", min_value=1, value=1)

    # ====== Nhập lý do ======
    is_foc = st.checkbox("Xuất kho miễn phí (FOC)")
    reason = "FOC" if is_foc else st.text_input("Nhập lý do xuất kho", "")

    if st.button("Xác nhận xuất kho"):
        if not reason:
            st.error("❌ Bạn phải nhập lý do xuất kho!")
        else:
            with engine.begin() as conn:
                stock = conn.execute(text("SELECT stock FROM spare_parts WHERE material_no = :material_no"), {"material_no": part_id}).scalar()
                if not is_foc and quantity > stock:
                    st.error("❌ Không đủ hàng trong kho!")
                else:
                    conn.execute(text(""" 
                        INSERT INTO import_export (part_id, quantity, mc_pos_id, empl_id, date, reason, im_ex_flag)
                        VALUES (:part_id, :quantity, :mc_pos_id, :empl_id, :date, :reason, 0)
                    """), {
                        "part_id": part_id,
                        "quantity": quantity,
                        "mc_pos_id": mc_pos_id,
                        "empl_id": empl_id,
                        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "reason": reason
                    })

                    if not is_foc:
                        conn.execute(text("UPDATE spare_parts SET stock = stock - :q WHERE material_no = :material_no"),
                                     {"q": quantity, "material_no": part_id})
                    
                    st.success("✅ Đã xuất kho thành công!")

    st.markdown("---")

    # === BỘ LỌC LỊCH SỬ ===
    with engine.begin() as conn:
        export_history = pd.read_sql(""" 
            SELECT 
                ie.date, ie.quantity, ie.reason,
                sp.material_no, sp.description,
                e.name AS employee,
                mp.mc_pos, m.name AS machine,
                g.mc_name AS group_name,
                d.mc_of_dept AS dept
            FROM import_export ie
            LEFT JOIN spare_parts sp ON ie.part_id = sp.material_no
            LEFT JOIN employees e ON ie.empl_id = e.amann_id
            LEFT JOIN machine_pos mp ON ie.mc_pos_id = mp.mc_pos_id
            LEFT JOIN machine m ON mp.mc_id = m.id
            LEFT JOIN group_mc g ON m.group_mc_id = g.id
            LEFT JOIN dept d ON m.dept_id = d.id
            WHERE ie.im_ex_flag = 0
        """, conn)

    if export_history.empty:
        st.info("Không có lịch sử xuất kho.")
        return

    # ====== Bộ lọc theo tháng và năm (gộp chung) ======
    st.markdown("Bộ lọc")

    # Sử dụng st.columns để tạo 4 bộ lọc nằm ngang
    col1, col2, col3, col4 = st.columns(4)

    # Bộ lọc tháng/năm
    with col1:
        month_year_filter = st.selectbox(
            "Chọn tháng và năm",
            options=[f"{i:02d}/{year}" for year in range(2020, datetime.now().year + 1) for i in range(1, 13)]
        )

    # Bộ lọc Material/Description
    with col2:
        material_search = st.text_input("Tìm theo Material_No hoặc Description")

    # Bộ lọc Machine
    with col3:
        machine_filter = st.selectbox("Chọn máy", ["Tất cả"] + list(export_history['machine'].unique()))

    # Bộ lọc FOC
    with col4:
        foc_filter = st.selectbox("Lọc theo FOC", ["Tất cả", "FOC", "Không FOC"])

    # Chuyển đổi cột date sang datetime nếu chưa
    export_history['date'] = pd.to_datetime(export_history['date'])

    # Lọc theo tháng và năm
    selected_month, selected_year = month_year_filter.split("/")
    selected_month = int(selected_month)
    selected_year = int(selected_year)

    # Lọc dữ liệu theo tháng và năm
    filtered_df = export_history[
        (export_history['date'].dt.month == selected_month) & 
        (export_history['date'].dt.year == selected_year)
    ]

    # Lọc theo Material/Description
    if material_search:
        filtered_df = filtered_df[
            filtered_df['material_no'].str.contains(material_search, case=False, na=False) |
            filtered_df['description'].str.contains(material_search, case=False, na=False)
        ]

    # Lọc theo Machine
    if machine_filter != "Tất cả":
        filtered_df = filtered_df[filtered_df['machine'] == machine_filter]

    # Lọc theo FOC
    if foc_filter != "Tất cả":
        if foc_filter == "FOC":
            filtered_df = filtered_df[filtered_df['reason'] == "FOC"]
        else:
            filtered_df = filtered_df[filtered_df['reason'] != "FOC"]
    
    # Đổi thứ tự các cột theo yêu cầu
    filtered_df = filtered_df[[ 
        'material_no', 'description', 'employee', 
        'group_name', 'machine', 'mc_pos',
        'quantity', 'reason', 'date'
    ]]

    # Hiển thị lịch sử xuất kho đã lọc
    st.dataframe(filtered_df, use_container_width=True)

    # ====== Tạo và Tải file Excel ======
    def convert_df(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Export History')
        output.seek(0)
        return output

    excel_file = convert_df(filtered_df)

    st.download_button(
        label="📥 Tải xuống Excel",
        data=excel_file,
        file_name="export_stock_history.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
