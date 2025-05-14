import streamlit as st
import pandas as pd
from sqlalchemy import text
from database import get_engine
import altair as alt

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

    # Tạo các tab cho chức năng tìm kiếm và cập nhật
    tab1, tab3 = st.tabs(["Tìm kiếm", "Cập nhật"])

    # ------------ TÌM KIẾM ------------ 
    with tab1:
        st.subheader("Tìm kiếm linh kiện")
        keyword = st.text_input("Tìm theo Material No hoặc Description:", key="search_keyword")
        
        # Kiểm tra biến đếm nếu chưa có
        if "search_counts" not in st.session_state:
            st.session_state.search_counts = {}

        # Lọc chính xác theo từ khóa
        if keyword:
            filtered_parts = parts[ 
                (parts['material_no'].str.contains(f"^{keyword}$", case=False, na=False)) |
                (parts['description'].str.contains(f"^{keyword}$", case=False, na=False))
            ]
            # Ghi nhận lượt tìm kiếm mới, không xóa dữ liệu cũ
            for mat_no in filtered_parts["material_no"].unique():
                st.session_state.search_counts[mat_no] = st.session_state.search_counts.get(mat_no, 0) + 1
        else:
            filtered_parts = parts

        # Ẩn bảng kết quả tìm kiếm
        display_table = st.checkbox("Hiển thị kết quả tìm kiếm", value=False)

        if display_table:
            if filtered_parts.empty:
                st.warning("Không tìm thấy linh kiện.")
            else:
                # Chọn cột cần hiển thị
                display_cols = ['material_no', 'description', 'part_no', 'bin', 'machine_type_id', 'cost_center', 'price', 'stock', 'safety_stock']
                # Đánh dấu hàng có stock dưới mức an toàn
                def highlight_low_stock(row):
                    # Kiểm tra nếu stock nhỏ hơn safety_stock và đánh dấu toàn bộ dòng
                    if row["stock"] < row.get("safety_stock", 0):  # Ensure safety_stock exists
                        return ['background-color: #FFD700'] * len(row)  # Highlight the entire row with light red
                    else:
                        return [''] * len(row)  # No styling if stock is not below safety stock

                # Áp dụng highlight cho toàn bộ bảng nếu có hàng dưới mức tồn kho an toàn
                styled_df = filtered_parts[display_cols].style.apply(highlight_low_stock, axis=1)
                st.dataframe(styled_df, use_container_width=True)

    # Hiển thị Top 10 tìm kiếm nhiều nhất
    if st.session_state.search_counts:
        st.subheader("Top 10 Material No được tìm kiếm nhiều nhất")
        search_df = pd.DataFrame([{"material_no": k, "count": v} for k, v in st.session_state.search_counts.items()])
        search_df = search_df.sort_values("count", ascending=False).head(10)

        # Tạo biểu đồ bar với nhãn
        chart = alt.Chart(search_df).mark_bar().encode(
            x=alt.X("material_no:N", title="Material No", sort="-y"),
            y=alt.Y("count:Q", title="Số lượt tìm"),
            tooltip=["material_no", "count"]
        ).properties(width=600, height=400)

        # Thêm nhãn hiển thị số lượng tìm kiếm trên mỗi thanh
        text = chart.mark_text(dy=-10, color='black').encode(
            text='count:Q'
        )

        # Kết hợp biểu đồ bar và nhãn
        st.altair_chart(chart + text, use_container_width=True)


    # ------------ CẬP NHẬT ------------ 
    with tab3:
        st.subheader("Cập nhật vật liệu")
        selected_part = st.selectbox(
            "Chọn vật liệu",
            parts.apply(lambda x: f"{x['material_no']} - {x['description']}", axis=1),
            key="edit_part_selector"
        )
        selected_material_no = selected_part.split(" - ")[0]
        selected_data = parts[parts['material_no'] == selected_material_no].iloc[0]

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
            safety_stock = st.number_input("Safety Stock", min_value=0, value=selected_data.get('safety_stock', 0), key="edit_safety_stock")
            safety_stock_check = st.radio("Kiểm tra tồn kho an toàn", ["Yes", "No"],
                                          index=0 if selected_data.get('safety_stock_check', "Yes") == "Yes" else 1,
                                          key="edit_safety_check")
            # Thêm chức năng xuất kho
            quantity_out = st.number_input("Số lượng xuất kho", min_value=0, max_value=int(stock), value=0)

        if st.button("Lưu cập nhật", key="btn_update_part"):
            try:
                # Kiểm tra số lượng xuất kho
                if quantity_out > stock:
                    st.warning("❌ Số lượng xuất kho không thể lớn hơn số lượng tồn kho.")
                    return

                # Cập nhật thông tin vật liệu và trừ số lượng xuất kho
                with get_engine().begin() as conn:
                    # Cập nhật dữ liệu trong cơ sở dữ liệu
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
                        WHERE material_no = :material_no
                    """), {
                        "material_no": material_no,
                        "description": description,
                        "part_no": part_no,
                        "machine_type_id": machine_type_id,
                        "bin": bin_val,
                        "cost_center": cost_center,
                        "price": price,
                        "stock": stock - quantity_out,  # Giảm số lượng tồn kho khi xuất kho
                        "safety_stock": safety_stock,
                        "safety_stock_check": safety_stock_check
                    })

                # Cập nhật lại parts_data sau khi thay đổi
                st.session_state.reload_parts_data = True
                st.success("✅ Cập nhật thành công.")
            
            except Exception as e:
                st.error(f"❌ Cập nhật thất bại: {e}")
                st.session_state.reload_parts_data = True  # Reload data in case of failure

        # Đảm bảo làm mới dữ liệu sau khi cập nhật
        if st.session_state.reload_parts_data:
            st.session_state.parts_data = load_spare_parts()  # Tải lại dữ liệu spare parts từ cơ sở dữ liệu
            st.write(st.session_state.parts_data)  # In ra để kiểm tra dữ liệu đã được tải lại chưa
