import streamlit as st
import pandas as pd
import io
from database import get_engine
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from st_aggrid.shared import JsCode
import matplotlib.pyplot as plt

def show_view_stock():
    st.markdown("<h1 style='text-align: center;'>Xem Tồn Kho</h1>", unsafe_allow_html=True)

    # Kết nối cơ sở dữ liệu và truy vấn dữ liệu tồn kho
    engine = get_engine()
    with engine.begin() as conn:
        df_stock = pd.read_sql(''' 
        SELECT 
            sp.part_no, sp.material_no, sp.description, 
            mt.machine AS machine_type, 
            sp.bin, sp.cost_center, 
            sp.price, sp.stock, sp.safety_stock, 
            sp.safety_stock_check, sp.image_url, 
            sp.import_date, sp.export_date
        FROM spare_parts sp
        JOIN machine_type mt ON sp.machine_type_id = mt.id
        ''', conn)

    # Lấy danh sách loại máy để lọc dữ liệu
    machine_types = df_stock['machine_type'].dropna().unique()
    machine_types = ['Tất cả'] + sorted(machine_types.tolist())

    # Các bộ lọc theo cột
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        keyword = st.text_input("🔍 Tìm kiếm", placeholder="Nhập mã, mô tả, cost center...")
    with col2:
        min_stock_str = st.text_input("🔽 Tồn kho tối thiểu", placeholder="Nhập tồn kho tối thiểu")
    with col3:
        max_stock_str = st.text_input("🔼 Tồn kho tối đa", placeholder="Nhập tồn kho tối đa")
    with col4:
        selected_machine = st.selectbox("🛠️ Loại máy", machine_types)

    # Xử lý các giá trị tồn kho tối thiểu và tối đa
    try:
        min_stock = int(min_stock_str) if min_stock_str else 0
    except ValueError:
        min_stock = 0
        st.warning("⚠️ Tồn kho tối thiểu không hợp lệ, sử dụng giá trị mặc định là 0.")

    try:
        max_stock = int(max_stock_str) if max_stock_str else 100000
    except ValueError:
        max_stock = 100000
        st.warning("⚠️ Tồn kho tối đa không hợp lệ, sử dụng giá trị mặc định là 100000.")

    # Lọc dữ liệu theo các tiêu chí
    df_filtered = df_stock.copy()

    # Lọc theo từ khóa
    if keyword.strip():
        kw = keyword.strip().lower()
        df_filtered = df_filtered[
            df_filtered['material_no'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['part_no'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['description'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['bin'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['cost_center'].astype(str).str.lower().str.contains(kw, na=False)
        ]

    # Lọc theo tồn kho
    df_filtered = df_filtered[
        (df_filtered['stock'] >= min_stock) & (df_filtered['stock'] <= max_stock)
    ]

    # Lọc theo loại máy
    if selected_machine != 'Tất cả':
        df_filtered = df_filtered[df_filtered['machine_type'] == selected_machine]

    # Cấu hình AgGrid để hiển thị bảng
    # Cấu hình AgGrid để hiển thị bảng (mở rộng và tối ưu)
    gb = GridOptionsBuilder.from_dataframe(df_filtered)

    # Cấu hình mặc định cho cột
    gb.configure_default_column(
        filter=False, sortable=True, editable=False, resizable=True,
        cellStyle=JsCode("""function(params) { 
            return { 
                textAlign: 'center', 
                border: '1px solid #ccc', 
                padding: '8px',
                lineHeight: '24px'
            }; 
        }""")
    )

    # Định dạng cho cột tồn kho
    gb.configure_column(
        "stock",
        type=["numericColumn"],
        valueFormatter=JsCode("function(params) { return params.value.toLocaleString(); }"),
        cellStyle=JsCode("""function(params) {
            let style = {
                textAlign: 'center',
                border: '1px solid #ccc',
                padding: '8px',
                lineHeight: '24px'
            };
            if (params.value <= 10) {
                style.backgroundColor = '#ffdddd';
                style.fontWeight = 'bold';
            }
            return style;
        }""")
    )

    # Định dạng cho tồn kho an toàn
    gb.configure_column(
        "safety_stock",
        type=["numericColumn"],
        valueFormatter=JsCode("function(params) { return params.value.toLocaleString(); }")
    )

    # Ẩn cột ảnh
    gb.configure_column("image_url", hide=True)

    # Cho phép chọn 1 dòng
    gb.configure_selection('single', use_checkbox=True)

    # Tự động fit cột khi render
    gb.configure_grid_options(
        domLayout='normal',
        suppressHorizontalScroll=False,
        suppressColumnVirtualisation=True,
        rowHeight=38,
        onFirstDataRendered=JsCode(
            "function(params) { params.api.sizeColumnsToFit(); }"
        )
    )

    grid_options = gb.build()

    # Hiển thị bảng
    grid_response = AgGrid(
        df_filtered,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        theme="streamlit",
        fit_columns_on_grid_load=False,  # Cho phép rộng theo nội dung
        height=600,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True
    )


    # Hiển thị chi tiết của vật liệu đã chọn
    selected_rows = grid_response['selected_rows']
    if selected_rows is not None and len(selected_rows) > 0:
        selected = pd.DataFrame(selected_rows).iloc[0]
        st.markdown("<h3 style='text-align: center;'>📋 Chi Tiết Vật Liệu</h3>", unsafe_allow_html=True)

        detail_data = {
            "Material No": selected['material_no'],
            "Part No": selected['part_no'],
            "Description": selected['description'],
            "Machine Type": selected['machine_type'],
            "Location (bin)": selected['bin'],
            "Cost Center": selected['cost_center'],
            "Stock": selected['stock'],
            "Safety Stock": selected['safety_stock'],
            "Safety Stock Check": "✅ Yes" if selected['safety_stock_check'] else "❌ No",
            "Price": selected['price'],
            "Import Date": selected['import_date'],
            "Export Date": selected['export_date'],
            "Image": f"<img src='{selected['image_url']}' width='300'>" if selected['image_url'] else "No Image"
        }

        detail_df = pd.DataFrame(list(detail_data.items()), columns=["Attribute", "Value"])
        st.markdown(detail_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.warning("⚠️ Bạn chưa chọn vật liệu.")

   

       

    # Cung cấp tính năng tải xuống dữ liệu đã lọc dưới dạng Excel
    if not df_filtered.empty:  # Kiểm tra nếu DataFrame không rỗng
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Stock')

        st.download_button(
            label="📥 Tải Xuống Excel",
            data=excel_buffer.getvalue(),
            file_name="stock_view.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ Không tìm thấy kết quả phù hợp.")
