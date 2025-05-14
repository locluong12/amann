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

def show_material_page():
    st.markdown("<h1 style='text-align: center;'>Import Stock</h1>", unsafe_allow_html=True)
    engine = get_engine()

    spare_parts = load_spare_parts(engine)
    machine_types = load_machine_types(engine)
    employees = load_employees(engine)
    import_stock_data = load_import_stock_data(engine)

    def plot_import_chart(import_stock_data):
        import_stock_data = import_stock_data[import_stock_data['total_quantity_imported'] > 0]

        selected_date = st.date_input("📅 Chọn ngày để xem thống kê nhập kho", datetime.today())

        # Đảm bảo định dạng ngày đúng
        import_stock_data['import_date'] = pd.to_datetime(import_stock_data['import_date'])
        
        # Lọc theo ngày (không so sánh giờ phút)
        filtered_data = import_stock_data[import_stock_data['import_date'].dt.date == selected_date]

        total_stock = filtered_data['total_quantity_imported'].sum() if not filtered_data.empty else 0

        fig, ax = plt.subplots(figsize=(10, 4))

        if not filtered_data.empty:
            sns.barplot(
                x="material_no",
                y="total_quantity_imported",
                data=filtered_data,
                ax=ax,
                palette='Reds'
            )
            ax.set_title(f"Số lượng nhập kho ngày {selected_date.strftime('%Y-%m-%d')}", fontsize=12)
            ax.set_xlabel("Material No", fontsize=10)
            ax.set_ylabel("Số lượng nhập", fontsize=10)
            plt.xticks(rotation=45, fontsize=8)
            plt.yticks(fontsize=8)

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

            for p in ax.patches:
                ax.annotate(f"{p.get_height():.0f}", (p.get_x() + p.get_width() / 2., p.get_height()), 
                            ha='center', va='center', fontsize=8, color='black', xytext=(0, 5), 
                            textcoords='offset points')

            fig.tight_layout()
            st.pyplot(fig)
        else:
            st.warning(f"⚠️ Không có dữ liệu nhập kho vào ngày {selected_date.strftime('%Y-%m-%d')}.")



    # Gọi hàm
    plot_import_chart(import_stock_data)
    st.markdown("---")

    col1, col2 = st.columns(2)

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
