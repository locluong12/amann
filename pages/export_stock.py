import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from database import get_engine
import matplotlib.pyplot as plt
import seaborn as sns
def show_export_stock():
    st.markdown("<h1 style='text-align: center;'>📦 Export Stock</h1>", unsafe_allow_html=True)
    engine = get_engine()

    # ====== Load dữ liệu cơ bản ======
    with engine.begin() as conn:
        spare_parts = pd.read_sql('SELECT material_no, description, stock FROM spare_parts', conn)
        employees = pd.read_sql('SELECT amann_id, name FROM employees', conn)
        machine_data = pd.read_sql(''' 
            SELECT m.name AS machine_name, mp.mc_pos AS mc_pos_id, mp.mc_pos 
            FROM machine m 
            JOIN machine_pos mp ON m.group_mc_id = mp.mc_id
        ''', conn)

    # ====== Chọn ngày cần thống kê ======
    selected_date = st.date_input("📅 Chọn ngày để xem thống kê xuất kho", datetime.today())
    today_str = selected_date.strftime('%Y-%m-%d')

    # ====== Hàm lấy dữ liệu xuất kho và chi phí xuất kho ======
    def fetch_export_data():
        # Lấy dữ liệu xuất kho
        with engine.begin() as conn:
            export_stats = pd.read_sql(''' 
                SELECT 
                    ie.date, 
                    ie.part_id, 
                    sp.material_no, 
                    sp.description, 
                    SUM(ie.quantity) AS total_quantity
                FROM import_export ie
                JOIN spare_parts sp ON ie.part_id = sp.material_no
                WHERE DATE(ie.date) = %s
                GROUP BY ie.date, ie.part_id, sp.material_no, sp.description
            ''', conn, params=(today_str,))

        # Lấy chi phí xuất kho
        with engine.begin() as conn:
            cost_data = pd.read_sql(''' 
                SELECT 
                    DATE(ie.date) AS export_day,
                    ie.part_id,
                    SUM(ie.quantity) AS total_qty,
                    sp.price
                FROM import_export ie
                JOIN spare_parts sp ON ie.part_id = sp.material_no
                WHERE ie.im_ex_flag = 0
                GROUP BY export_day, ie.part_id, sp.price
                ORDER BY export_day
            ''', conn)

        return export_stats, cost_data

    # ====== Hàm cập nhật biểu đồ xuất kho ======
    def update_bar_chart(export_stats):
        if not export_stats.empty:
            st.subheader(f"📊 Thống kê xuất kho ngày {today_str}")

            # Kết hợp dữ liệu xuất kho với thông tin kho
            stock_data = export_stats.merge(spare_parts[['material_no', 'stock']], on='material_no', how='left')

            # Lọc những sản phẩm có stock > 0
            stock_data = stock_data[stock_data['stock'] > 0]

            if not stock_data.empty:
                stock_data = stock_data[['material_no', 'total_quantity', 'stock']].sort_values('total_quantity', ascending=False)

                # Vẽ biểu đồ cột với seaborn
                fig, ax = plt.subplots(figsize=(10, 4))
                sns.barplot(
                    x="material_no", 
                    y="total_quantity", 
                    data=stock_data, 
                    ax=ax, 
                    palette='Blues'
                )

                ax.set_title(f"Số lượng xuất kho ngày {today_str}", fontsize=12)
                ax.set_xlabel("Mã vật tư", fontsize=10)
                ax.set_ylabel("Số lượng xuất kho", fontsize=10)
                plt.xticks(rotation=45, fontsize=8)
                plt.yticks(fontsize=8)

                # Thêm thông tin tổng số lượng tồn kho
                total_stock = stock_data['stock'].sum()
                ax.text(
                    0.0, 1.05,
                    f"Total Stock:\n{int(total_stock):,}",
                    transform=ax.transAxes,
                    fontsize=9,
                    fontweight='bold',
                    va='bottom',
                    ha='left',
                    bbox=dict(
                        facecolor='#FFCCCC',
                        alpha=0.8,
                        boxstyle='round,pad=0.5',
                        edgecolor='white',
                        lw=0
                    )
                )

                # Ghi chú giá trị lên các cột
                for p in ax.patches:
                    ax.annotate(f"{p.get_height():.0f}", (p.get_x() + p.get_width() / 2., p.get_height()), 
                                ha='center', va='center', fontsize=8, color='black', xytext=(0, 5), 
                                textcoords='offset points')

                fig.tight_layout()
                st.pyplot(fig)
            else:
                st.warning(f"⚠️ Không có sản phẩm nào có số lượng xuất kho lớn hơn 0 cho ngày {today_str}")
        else:
            st.warning(f"⚠️ Không có dữ liệu xuất kho cho ngày {today_str}")

    # ====== Hàm vẽ biểu đồ chi phí xuất kho ======
    def show_export_cost_chart(cost_data):
        st.subheader("💰 Biểu đồ chi phí xuất kho theo ngày")

        if cost_data.empty:
            st.info("ℹ️ Chưa có dữ liệu xuất kho để tính chi phí.")
            return

        # Tính chi phí theo ngày
        cost_data['export_cost'] = cost_data['total_qty'] * cost_data['price']  # Sử dụng cột price để tính chi phí
        cost_by_day = cost_data.groupby('export_day')['export_cost'].sum().reset_index()

        # Định dạng lại cột ngày tháng
        cost_by_day['export_day'] = pd.to_datetime(cost_by_day['export_day']).dt.strftime('%d-%m-%Y')

        # Vẽ biểu đồ cột
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(data=cost_by_day, x='export_day', y='export_cost', ax=ax, palette='Blues')
        ax.set_title("Chi phí xuất kho theo ngày", fontsize=12)
        ax.set_xlabel("Ngày", fontsize=10)
        ax.set_ylabel("Chi phí (VND)", fontsize=10)
        plt.xticks(rotation=45, fontsize=8)
        plt.yticks(fontsize=8)

        # Thêm ô tổng chi phí vào góc trên bên trái
        total_cost = cost_by_day['export_cost'].sum()
        ax.text(
            0.0, 1.05,
            f"Total Cost: {total_cost:,.0f} VND",
            transform=ax.transAxes,
            fontsize=9,
            fontweight='bold',
            va='bottom',
            ha='left',
            bbox=dict(
                facecolor='#FFCCCC',
                alpha=0.8,
                boxstyle='round,pad=0.5',
                edgecolor='white',
                lw=0
            )
        )

        # Ghi chú giá trị lên các cột
        for p in ax.patches:
            ax.annotate(f"{p.get_height():,.0f}", (p.get_x() + p.get_width() / 2., p.get_height()), 
                        ha='center', va='center', fontsize=8, color='black', xytext=(0, 5), 
                        textcoords='offset points')

        fig.tight_layout()
        st.pyplot(fig)

    # ====== Gọi hàm chính và cập nhật biểu đồ ======
    export_stats, cost_data = fetch_export_data()

    # Hiển thị các biểu đồ
    col1, col2 = st.columns(2)

    with col1:
        update_bar_chart(export_stats)  # Truyền dữ liệu xuất kho vào

    with col2:
        show_export_cost_chart(cost_data)  # Truyền dữ liệu chi phí vào



    # ====== Tìm kiếm linh kiện ======
    search = st.text_input("🔍 Tìm linh kiện theo Material_No/Description")
    parts = spare_parts[
        spare_parts['description'].str.contains(search, case=False, na=False) |
        spare_parts['material_no'].str.contains(search, case=False, na=False)
    ] if search else spare_parts

    if not parts.empty:  # Chỉ hiển thị phần tìm kiếm nếu có linh kiện
        part_choice = st.selectbox("📦 Chọn linh kiện để xuất", parts.apply(
            lambda x: f"{x['material_no']} - {x['description']} (Tồn: {x['stock']})", axis=1))
        part_id = part_choice.split(' - ')[0]
    else:
        st.warning("⚠️ Không có linh kiện phù hợp.")

    # ====== Nhân viên ======
    if not employees.empty:  # Chỉ hiển thị nếu có dữ liệu nhân viên
        empl_choice = st.selectbox("👤 Người thực hiện", employees.apply(
            lambda x: f"{x['amann_id']} - {x['name']}", axis=1))
        empl_id = empl_choice.split(' - ')[0]
    else:
        st.warning("⚠️ Không có dữ liệu nhân viên.")

    # ====== Máy & vị trí ======
    if not machine_data.empty:  # Chỉ hiển thị nếu có dữ liệu máy
        machine_selected = st.selectbox("🖥️ Chọn máy", sorted(machine_data['machine_name'].unique()))
        pos_options = machine_data[machine_data['machine_name'] == machine_selected]['mc_pos'].tolist()
        pos_selected = st.selectbox("📍 Chọn vị trí máy", pos_options)

        mc_pos_row = machine_data[
            (machine_data['machine_name'] == machine_selected) & 
            (machine_data['mc_pos'] == pos_selected)
        ]
        mc_pos_id = mc_pos_row.iloc[0]['mc_pos_id'] if not mc_pos_row.empty else None
    else:
        st.warning("⚠️ Không có dữ liệu máy.")

    # ====== Thông tin xuất kho ======
    quantity = st.number_input("🔢 Số lượng xuất kho", min_value=1, value=1)
    is_foc = st.checkbox("🎁 Xuất kho miễn phí (FOC)")
    reason = "FOC" if is_foc else st.text_input("✏️ Nhập lý do xuất kho", "")

    # ====== Xác nhận xuất kho ======
    if st.button("✅ Xác nhận xuất kho"):
        if not reason and not is_foc:
            st.error("❌ Bạn phải nhập lý do xuất kho!")
        else:
            with engine.begin() as conn:
                # Kiểm tra số lượng tồn kho
                stock = conn.execute(text("SELECT stock FROM spare_parts WHERE material_no = :material_no"),
                                     {"material_no": part_id}).scalar()
                if not is_foc and quantity > stock:
                    st.error("❌ Không đủ hàng trong kho!")
                else:
                    # Ghi vào bảng xuất kho
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

                    # Cập nhật kho
                    if not is_foc:
                        conn.execute(text("""
                            UPDATE spare_parts 
                            SET stock = stock - :q, export_date = :date 
                            WHERE material_no = :material_no
                        """), {"q": quantity, "material_no": part_id, "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                    else:
                        conn.execute(text("""
                            UPDATE spare_parts 
                            SET export_date = :date 
                            WHERE material_no = :material_no
                        """), {"material_no": part_id, "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

            st.success("✅ Đã xuất kho thành công!")

            # Yêu cầu làm mới giao diện và cập nhật lại biểu đồ
            st.rerun()
