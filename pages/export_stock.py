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

        
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df


def show_export_stock():
    st.markdown("<h1 style='text-align: center;'>Xuất kho</h1>", unsafe_allow_html=True)
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
        st.session_state.selected_year = datetime.today().year
    if 'selected_month' not in st.session_state:
        st.session_state.selected_month = datetime.today().month

    # Danh sách năm và tháng
    years = list(range(2020, 2031))
    months = list(range(1, 13))  # dùng số nguyên thay vì string


    # Bộ lọc năm và tháng
    # CSS căn giữa và đổi màu chữ trắng cho selectbox
    
    st.markdown(
        """
        <style>
        /* Màu trắng và căn giữa nhãn tiêu đề (label) */
        .stSelectbox label {
            color: white !important;
            text-align: center !important;
            display: block;
            width: 100%;
        }

        /* Màu trắng và căn giữa chữ trong selectbox đã chọn */
        div[data-baseweb="select"] > div {
            color: white !important;
            text-align: center !important;
        }

        /* Màu trắng placeholder khi chưa chọn */
        .css-1jqq78o-placeholder {
            color: white !important;
            text-align: center !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Layout chia 2 cột
    col1, col2 = st.columns(2)

    with col1:
        selected_year = st.selectbox("Chọn năm", years, index=years.index(st.session_state.selected_year))
        st.session_state.selected_year = selected_year

    with col2:
        selected_month = st.selectbox("Chọn tháng", months, index=st.session_state.selected_month - 1)
        st.session_state.selected_month = selected_month
    # Tính ngày bắt đầu và kết thúc của tháng được chọn
    start_date = datetime(selected_year, st.session_state.selected_month, 1)
    # Lấy ngày cuối cùng của tháng (chuyển sang tháng kế tiếp rồi trừ 1 ngày)
    if st.session_state.selected_month == 12:
        end_date = datetime(selected_year, 12, 31)
    else:
        end_date = datetime(selected_year, st.session_state.selected_month + 1, 1) - timedelta(days=1)

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
    # Tổng chi phí đã là USD, không cần quy đổi
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
        Tổng xuất kho tháng <span style='color: #ffffff;'>{int(selected_month):02d}</span> năm 
        <span style='color: #ffffff;'>{selected_year}</span>: 
        <span style='color: #ffffff'>{int(total_export_quantity):,}</span> cái, 
        Tổng chi phí: <span style='color: #ffffff'>${total_export_cost:,.0f}</span> USD
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
                Tổng chi phí<br>
                <span style="font-size:28px;">${total_export_cost:,.0f} USD</span>
            </div>
        """, unsafe_allow_html=True)
    with col_total_2:
        st.markdown(f"""
            <div style="{box_style_2}">
                Tổng xuất kho<br>
                <span style="font-size:28px;">{int(total_export_quantity):,}</span>
            </div>
        """, unsafe_allow_html=True)


    # ====== Tìm kiếm linh kiện ======
    query = "SELECT material_no, description, stock, bin FROM spare_parts"
    spare_parts = pd.read_sql_query(text(query), engine)

    st.markdown('<p style="color:white; margin-bottom:4px;">🔍 Tìm linh kiện theo Mã / Mô tả / Vị trí (BIN)</p>', unsafe_allow_html=True)
    search = st.text_input("", key="search_input", label_visibility="hidden")

    # Lọc linh kiện theo Material_No, Description hoặc Bin
    parts = spare_parts[
        spare_parts['description'].str.contains(search, case=False, na=False) |
        spare_parts['material_no'].str.contains(search, case=False, na=False) |
        spare_parts['bin'].astype(str).str.contains(search, case=False, na=False)
    ] if search else spare_parts

    if not parts.empty:
        # Hiển thị danh sách linh kiện để chọn
        part_choice = st.selectbox(
            "", 
            parts.apply(lambda x: f"{x['material_no']} - {x['description']} (Tồn: {x['stock']})", axis=1),
            key="part_choice",
            label_visibility="hidden"
        )
        part_id = part_choice.split(' - ')[0]  # Lấy mã vật liệu được chọn

        # ====== Hiển thị vị trí BIN của linh kiện đã chọn ======
        bin_location = spare_parts.loc[spare_parts['material_no'] == part_id, 'bin'].values
        if bin_location.size > 0:
            bin_value = bin_location[0]
            st.markdown("<p style='color:white; font-weight:bold;'>Vị trí lưu (BIN):</p>", unsafe_allow_html=True)
            bin_input = st.text_input("", value=bin_value, key="bin_input", label_visibility="hidden")

        else:
            st.text_input("Vị trí lưu (BIN):", value="", key="bin_input", label_visibility="visible")
            st.markdown("<p style='color:white;'>⚠️ Không có thông tin vị trí BIN cho linh kiện này.</p>", unsafe_allow_html=True)


    # ====== Chọn nhân viên ======
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


    if not machine_data.empty:
        # Bước 1: chọn mã vật liệu
        def load_machine_data(engine):
            query = """
            SELECT 
                sp.material_no,
                mt.id AS machine_type_id,
                mt.machine AS group_mc_name,
                m.id AS machine_id,
                m.name AS machine_name,
                mp.mc_pos,
                mp.id AS mc_pos_id
            FROM spare_parts sp
            JOIN machine_type mt ON sp.machine_type_id = mt.id
            JOIN group_mc g ON g.id = mt.id            -- giả sử group_mc.id = machine_type.id để nối tiếp
            JOIN machine m ON m.group_mc_id = g.id
            LEFT JOIN machine_pos mp ON mp.mc_id = m.id
            ORDER BY m.name
            """
            df = pd.read_sql_query(text(query), engine)
            return df


        machine_data = load_machine_data(engine)

    # Giả sử machine_data có cột 'machine_name' và 'mc_pos' như bạn mô tả
    # ====== Định nghĩa hàm load_machines bên ngoài ======
    def load_machines(engine, selected_group, selected_pos, search_name):
        query = """
        SELECT m.name AS machine_name, g.mc_name AS group_mc_name,
            mp.mc_pos AS machine_pos, mp.id AS mc_pos_id
        FROM machine m
        JOIN group_mc g ON m.group_mc_id = g.id
        LEFT JOIN machine_pos mp ON m.group_mc_id = mp.mc_id
        WHERE (:group_name = 'Tất cả' OR g.mc_name = :group_name)
        AND (:pos = 'Tất cả' OR mp.mc_pos = :pos)
        AND (:search_name = '' OR m.name LIKE :search_name)
        ORDER BY m.name DESC
        LIMIT 1000
        """
        df = pd.read_sql_query(text(query), engine, params={
            "group_name": selected_group,
            "pos": selected_pos,
            "search_name": f"%{search_name}%"
        })
        return df



    # ====== Phần UI và logic chọn máy, vị trí ======

    mc_pos_id = None  # Đặt mặc định

    if not machine_data.empty and part_id is not None:
        # Lọc máy theo linh kiện
        filtered_data = machine_data[machine_data['material_no'] == part_id].copy()
        filtered_data['machine_name'] = filtered_data['machine_name'].astype(str).str.strip()

        machine_names = sorted(filtered_data['machine_name'].unique())
        st.markdown('<p style="color:white; margin-bottom:4px;">Chọn tên máy (theo linh kiện)</p>', unsafe_allow_html=True)
        machine_selected = st.selectbox("", machine_names, key="machine_selected_filtered", label_visibility="hidden")

        # Lấy vị trí máy theo máy được chọn
        pos_df = load_machines(engine, selected_group='Tất cả', selected_pos='Tất cả', search_name=machine_selected)

    elif not machine_data.empty:
        machine_names = sorted(machine_data['machine_name'].astype(str).str.strip().unique())
        st.markdown('<p style="color:white; margin-bottom:4px;">Chọn máy</p>', unsafe_allow_html=True)
        machine_selected = st.selectbox("", machine_names, key="machine_selected_all", label_visibility="hidden")

        pos_df = load_machines(engine, selected_group='Tất cả', selected_pos='Tất cả', search_name=machine_selected)

    else:
        st.markdown('<p style="color:white;">⚠️ Không có dữ liệu máy.</p>', unsafe_allow_html=True)
        pos_df = pd.DataFrame()
        machine_selected = None

    # ====== Chọn vị trí nếu có dữ liệu vị trí và máy được chọn ======

    if not pos_df.empty and machine_selected:
        # Chuẩn hóa dữ liệu để so sánh không phân biệt hoa thường và khoảng trắng
        pos_df['machine_name_clean'] = pos_df['machine_name'].astype(str).str.strip().str.lower()
        pos_df['machine_pos_clean'] = pos_df['machine_pos'].astype(str).str.strip().str.lower()
        machine_selected_clean = machine_selected.strip().lower()

        pos_options = pos_df[pos_df['machine_name_clean'] == machine_selected_clean]['machine_pos'].unique()
        pos_options = sorted(pos_options)

        if pos_options:
            st.markdown('<p style="color:white; margin-bottom:4px;">Chọn vị trí máy</p>', unsafe_allow_html=True)
            pos_selected = st.selectbox("", pos_options, key="pos_selected", label_visibility="hidden")

            pos_selected_clean = pos_selected.strip().lower()

            mc_pos_row = pos_df[
                (pos_df['machine_name_clean'] == machine_selected_clean) &
                (pos_df['machine_pos_clean'] == pos_selected_clean)
            ]

            if not mc_pos_row.empty:
                # Chuyển mc_pos_id sang string để thống nhất kiểu dữ liệu (tránh lỗi so sánh)
                mc_pos_id = str(mc_pos_row.iloc[0]['mc_pos_id'])
                
            else:
                st.warning("❌ Không tìm thấy ID vị trí máy tương ứng.")
                mc_pos_id = None
        else:
            st.warning("❌ Không có vị trí máy phù hợp để chọn.")
            mc_pos_id = None
    else:
        mc_pos_id = None


    # ====== Giao diện xuất kho (luôn hiện nếu có part_id) ======

    if part_id:
        st.markdown('<hr style="border-top: 1px solid white;"/>', unsafe_allow_html=True)
        st.markdown('<p style="color:white; margin-bottom:4px;">Số lượng xuất kho</p>', unsafe_allow_html=True)
        quantity = st.number_input("", min_value=1, value=1, key="quantity", label_visibility="hidden")

        st.markdown('<span style="color:white; font-weight:bold;">Xuất kho miễn phí (FOC)</span>', unsafe_allow_html=True)
        is_foc = st.checkbox("", key="foc_checkbox")

        if not is_foc:
            st.markdown('<p style="color:white; margin-bottom:4px;">✏️ Nhập lý do xuất kho</p>', unsafe_allow_html=True)
            reason = st.text_input("", key="reason_input", label_visibility="hidden")
        else:
            reason = "FOC"

        if st.button("✅ Xác nhận xuất kho"):
            if not reason and not is_foc:
                st.markdown('<p style="color:white;">❌ Bạn phải nhập lý do xuất kho!</p>', unsafe_allow_html=True)
            elif mc_pos_id is None:
                st.markdown('<p style="color:white;">❌ Vui lòng chọn đúng vị trí máy!</p>', unsafe_allow_html=True)
            else:
                try:
                    mc_pos_id_int = int(mc_pos_id)
                except Exception:
                    st.markdown('<p style="color:white;">❌ Vị trí máy không hợp lệ!</p>', unsafe_allow_html=True)
                    return

                with engine.begin() as conn:
                    # Lấy đúng giá trị mc_pos (khóa chính thật sự) từ machine_pos theo id
                    mc_pos_value = conn.execute(
                        text("SELECT mc_pos FROM machine_pos WHERE id = :id"),
                        {"id": mc_pos_id_int}
                    ).scalar()

                    if mc_pos_value is None:
                        st.markdown(f'<p style="color:white;">❌ Vị trí máy với ID {mc_pos_id_int} không tồn tại!</p>', unsafe_allow_html=True)
                        return

                    stock = conn.execute(
                        text("SELECT stock FROM spare_parts WHERE material_no = :material_no"),
                        {"material_no": part_id}
                    ).scalar()

                    if stock is None:
                        st.markdown('<p style="color:white;">❌ Không tìm thấy phụ tùng trong kho!</p>', unsafe_allow_html=True)
                        return

                    elif not is_foc and quantity > stock:
                        st.markdown(f'<p style="color:white;">❌ Không đủ hàng trong kho! Tồn kho hiện tại: {stock}</p>', unsafe_allow_html=True)
                        return

                    now = datetime.now()
                    today_str = now.strftime('%Y-%m-%d')

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
                        "mc_pos_id": mc_pos_value,    # Dùng giá trị đúng
                        "empl_id": empl_id,
                        "reason": reason,
                        "today": today_str
                    }).fetchone()

                    if existing_row:
                        conn.execute(text("""
                            UPDATE import_export
                            SET quantity = quantity + :add_quantity
                            WHERE id = :row_id
                        """), {
                            "add_quantity": quantity,
                            "row_id": existing_row[0]
                        })
                    else:
                        conn.execute(text("""
                            INSERT INTO import_export (date, part_id, quantity, im_ex_flag, empl_id, mc_pos_id, reason)
                            VALUES (:date, :part_id, :quantity, 0, :empl_id, :mc_pos_id, :reason)
                        """), {
                            "date": now,
                            "part_id": part_id,
                            "quantity": quantity,
                            "empl_id": empl_id,
                            "mc_pos_id": mc_pos_value,  # Dùng giá trị đúng
                            "reason": reason
                        })

                    if not is_foc:
                        # Giảm tồn kho khi không phải FOC
                        conn.execute(text("""
                            UPDATE spare_parts
                            SET stock = stock - :quantity
                            WHERE material_no = :part_id
                        """), {
                            "quantity": quantity,
                            "part_id": part_id
                        })

                    # Cập nhật export_date dù có FOC hay không
                    conn.execute(text("""
                        UPDATE spare_parts
                        SET export_date = :export_date
                        WHERE material_no = :part_id
                    """), {
                        "export_date": now,
                        "part_id": part_id
                    })




                    st.success("✅ Xuất kho thành công!")




    # ====== Lịch sử xuất kho ======
    df_history = fetch_import_export_history(engine, year=selected_year, quarter=selected_month)

    if not df_history.empty:
        # Lọc bản ghi xuất kho (im_ex_flag == 0)
        df_export = df_history[df_history['im_ex_flag'] == 0].copy()
        df_export['Type'] = 'Xuất kho'

        # Đọc bảng spare_parts lấy cột material_no và bin
        query_spare_parts = "SELECT material_no, bin FROM spare_parts"
        df_spare_parts = pd.read_sql_query(query_spare_parts, engine)

        # Merge df_export với df_spare_parts theo 'part_id' = 'material_no'
        df_export = df_export.merge(df_spare_parts, left_on='part_id', right_on='material_no', how='left')
        

        st.markdown('<span style="color:white; font-weight:bold;">Tìm kiếm theo Mã phụ tùng / Mô tả</span>', unsafe_allow_html=True)
        search_keyword_export = st.text_input("", key="search", placeholder="Nhập Mã phụ tùng hoặc Mô tả")

        # Nếu có từ khóa tìm kiếm, lọc dữ liệu theo part_id hoặc description
        if search_keyword_export.strip() != "":
            mask_export = (
                df_export['part_id'].str.contains(search_keyword_export, case=False, na=False) |
                df_export['description'].str.contains(search_keyword_export, case=False, na=False)
            )
            df_export = df_export[mask_export]


        # Chuẩn bị dataframe để hiển thị
        # Trước khi merge, làm sạch cột machine_name:
        machine_data['machine_name'] = machine_data['machine_name'].astype(str).str.strip()

        # Thực hiện merge để thêm cột machine_name vào df_export theo key part_id <-> material_no
        df_export = df_export.merge(machine_data[['material_no', 'machine_name']], 
                                    left_on='part_id', right_on='material_no', how='left')

        # Giờ df_export có thêm cột 'machine_name'
        # Bạn có thể tạo df_display như mong muốn:
        df_display = df_export[['date', 'part_id', 'description', 'quantity', 'Type', 'bin', 'employee_name', 'machine_name','mc_pos']].copy()
        df_display.columns = ['Ngày', 'Mã phụ tùng', 'Mô tả', 'Số lượng', 'Loại', 'Vị trí lưu (BIN)', 'Nhân viên','Tên máy', 'Vị trí máy']

        st.markdown(" Lịch sử xuất kho")
        st.dataframe(df_display)

        # Tạo file Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_display.to_excel(writer, sheet_name='Export_History', index=False)
        output.seek(0)

        # Style cho nút tải Excel
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
            label="⬇️ Tải Excel",
            data=output,
            file_name=f"Export_History_{selected_year}_{selected_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Không có dữ liệu xuất kho trong tháng đã chọn.")
