import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_engine

# Hàm load các loại máy từ cơ sở dữ liệu
def load_machine_types():
    engine = get_engine()
    return pd.read_sql("SELECT id, machine FROM machine_type", engine)

# Hàm load dữ liệu spare parts từ cơ sở dữ liệu
def load_spare_parts():
    engine = get_engine()
    return pd.read_sql("SELECT * FROM spare_parts", engine)

def manage_spare_parts():
    st.title("Quản lý linh kiện")

    # Kiểm tra và cập nhật dữ liệu spare_parts nếu cần
    if "reload_parts_data" not in st.session_state:
        st.session_state.reload_parts_data = True

    if "parts_data" not in st.session_state or st.session_state.reload_parts_data:
        st.session_state.parts_data = load_spare_parts()
        st.session_state.reload_parts_data = False

    parts = st.session_state.parts_data
    machine_types = load_machine_types()
    machine_type_dict = {f"{row['id']} - {row['machine']}": row['id'] for _, row in machine_types.iterrows()}

    # Tạo các tab cho chức năng tìm kiếm, thêm mới và cập nhật
    tab1, tab3 = st.tabs(["Tìm kiếm", "Cập nhật"])

    # ------------ TÌM KIẾM + XOÁ ------------
    with tab1:
        st.subheader("Tìm kiếm linh kiện")
        keyword = st.text_input("Tìm theo Material No hoặc Description:", key="search_keyword")

        # Lọc chính xác theo từ khóa
        if keyword:
            filtered_parts = parts[
                (parts['material_no'].str.contains(f"^{keyword}$", case=False, na=False)) |
                (parts['description'].str.contains(f"^{keyword}$", case=False, na=False))
            ]
        else:
            filtered_parts = parts

        if filtered_parts.empty:
            st.warning("Không tìm thấy linh kiện.")
        else:
            # Chọn cột cần hiển thị
            display_cols = ['id', 'material_no', 'description', 'part_no', 'bin', 'machine_type_id', 'cost_center', 'price', 'stock']
            st.dataframe(filtered_parts[display_cols].reset_index(drop=True), use_container_width=True)

    # ------------ CẬP NHẬT ------------ 
    with tab3:
        st.subheader("Cập nhật vật liệu")
        
        # Kiểm tra xem cột 'id' có tồn tại trong DataFrame hay không
        if 'id' not in parts.columns:
            st.error("Cột 'id' không tồn tại trong dữ liệu.")
            return

        selected_part = st.selectbox(
            "Chọn vật liệu",
            parts.apply(lambda x: f"{x['id']} - {x['material_no']} ({x['description']})", axis=1),
            key="edit_part_selector"
        )
        
        # Lấy selected_id từ chọn lựa vật liệu
        selected_id = int(selected_part.split(" - ")[0])
        selected_data = parts[parts['id'] == selected_id].iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            material_no = st.text_input("Material No", selected_data['material_no'], key="edit_material_no")
            description = st.text_input("Description", selected_data['description'], key="edit_description")
            part_no = st.text_input("Part No", selected_data['part_no'] or "", key="edit_part_no")
            bin_val = st.text_input("Bin", selected_data['bin'] or "", key="edit_bin")
            machine_type_selection = st.selectbox("Machine Type", list(machine_type_dict.keys()),
                                                  index=list(machine_type_dict.values()).index(selected_data['machine_type_id']),
                                                  key="edit_machine_type")
            machine_type_id = machine_type_dict[machine_type_selection]
        with col2:
            cost_center = st.text_input("Cost Center", selected_data['cost_center'] or "", key="edit_cost_center")
            price = st.number_input("Price", min_value=0.0, value=selected_data['price'] or 0.0, key="edit_price")
            stock = st.number_input("Stock", min_value=0, value=selected_data['stock'] or 0, key="edit_stock")
            safety_stock = st.number_input("Safety Stock", min_value=0, value=selected_data['safety_stock'] or 0, key="edit_safety_stock")
            safety_stock_check = st.radio("Kiểm tra tồn kho an toàn", ["Yes", "No"],
                                          index=0 if selected_data['safety_stock_check'] == "Yes" else 1,
                                          key="edit_safety_check")

        if st.button("Lưu cập nhật", key="btn_update_part"):
            try:
                with get_engine().begin() as conn:
                    conn.execute(text("""
                        UPDATE spare_parts
                        SET material_no = :material_no,
                            description = :description,
                            part_no = :part_no,
                            machine_type_id = :machine_type_id,
                            bin = :bin,
                            cost_center = :cost_center,
                            price = :price,
                            stock = :stock,
                            safety_stock = :safety_stock,
                            safety_stock_check = :safety_stock_check
                        WHERE id = :id
                    """), {
                        "material_no": material_no,
                        "description": description,
                        "part_no": part_no,
                        "machine_type_id": machine_type_id,
                        "bin": bin_val,
                        "cost_center": cost_center,
                        "price": price,
                        "stock": stock,
                        "safety_stock": safety_stock,
                        "safety_stock_check": safety_stock_check,
                        "id": selected_id
                    })
                st.success("✅ Cập nhật thành công.")
                # Cập nhật lại danh sách sau khi cập nhật
                st.session_state.reload_parts_data = True  # 👈 Cập nhật lại parts_data
            except Exception as e:
                st.error(f"Đã có lỗi khi cập nhật: {e}")

