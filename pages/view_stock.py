import streamlit as st
import pandas as pd
import io
from database import get_engine
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from st_aggrid.shared import JsCode
import plotly.express as px
import plotly.graph_objects as go

def show_view_stock():
    st.markdown("<h1 style='text-align: center;'>View Stock</h1>", unsafe_allow_html=True)

    # Kết nối cơ sở dữ liệu
    engine = get_engine()
    with engine.begin() as conn:
        df_stock = pd.read_sql(''' 
        SELECT 
            sp.material_no, sp.part_no, sp.description, 
            mt.machine AS machine_type, 
            sp.bin, sp.cost_center, 
            sp.price, sp.stock, sp.safety_stock, 
            sp.safety_stock_check, sp.image_url,
            sp.import_date, sp.export_date,
            DATEDIFF(IFNULL(sp.export_date, CURDATE()), sp.import_date) AS storage_days
        FROM spare_parts sp
        JOIN machine_type mt ON sp.machine_type_id = mt.id
        ''', conn)
        
        # Tính tổng tồn kho và tổng giá trị của tồn kho
        total_stock = int(df_stock['stock'].sum())
        total_value = int((df_stock['stock'] * df_stock['price']).sum())

        col1, col2 = st.columns(2)

        # Hiển thị tổng tồn kho và giá trị tồn kho
        with col1:
            st.markdown(
                f"""
                <div style="border:1px solid #ccc; border-radius:7px; padding:5px; text-align:center; background-color:#008080;">
                    <h4>Total Stock</h4>
                    <p style="font-size:24px; font-weight:bold;">{total_stock}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div style="border:1px solid #ccc; border-radius:7px; padding:5px; text-align:center; background-color:#008080;">
                    <h4>Total Value</h4>
                    <p style="font-size:24px; font-weight:bold;">{total_value:,.0f} đ</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Lọc và tìm kiếm dữ liệu
    machine_types = df_stock['machine_type'].dropna().unique()
    machine_types = ['Tất cả'] + sorted(machine_types.tolist())

    # Thanh tìm kiếm và lọc nằm ở đầu trang
    st.sidebar.header("Lọc Dữ Liệu")
    keyword = st.sidebar.text_input("🔍 Tìm kiếm", placeholder="Nhập mã, mô tả, cost center...")
    min_stock_str = st.sidebar.text_input("🔽 Tồn kho tối thiểu", placeholder="Nhập tồn kho tối thiểu")
    max_stock_str = st.sidebar.text_input("🔼 Tồn kho tối đa", placeholder="Nhập tồn kho tối đa")
    selected_machine = st.sidebar.selectbox("🛠️ Loại máy", machine_types)

    # Kiểm tra và chuyển đổi giá trị tồn kho tối thiểu và tối đa thành số
    try:
        min_stock = int(min_stock_str) if min_stock_str else 0
    except ValueError:
        min_stock = 0
        st.sidebar.warning("⚠️ Tồn kho tối thiểu không hợp lệ, sử dụng giá trị mặc định là 0.")

    try:
        max_stock = int(max_stock_str) if max_stock_str else 100000
    except ValueError:
        max_stock = 100000
        st.sidebar.warning("⚠️ Tồn kho tối đa không hợp lệ, sử dụng giá trị mặc định là 100000.")

    # Lọc dữ liệu
    df_filtered = df_stock.copy()

    if keyword.strip():
        kw = keyword.strip().lower()
        df_filtered = df_filtered[ 
            df_filtered['material_no'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['part_no'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['description'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['bin'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['cost_center'].astype(str).str.lower().str.contains(kw, na=False)
        ]

    df_filtered = df_filtered[
        (df_filtered['stock'] >= min_stock) & (df_filtered['stock'] <= max_stock)
    ]

    if selected_machine != 'Tất cả':
        df_filtered = df_filtered[df_filtered['machine_type'] == selected_machine]

    # Cảnh báo khi tồn kho thấp (<= 5)
    low_stock_items = df_filtered[df_filtered['stock'] <= 5]
    if not low_stock_items.empty:
        st.warning("⚠️ Một số mặt hàng có tồn kho thấp! Vui lòng kiểm tra các sản phẩm dưới đây.")

    # Hiển thị biểu đồ và thông tin tổng quan
    # Biểu đồ thanh: tồn kho theo material_no (giới hạn 10 sản phẩm đầu)
    df_chart = df_filtered.nlargest(10, 'stock')

    col1, col2, col3 = st.columns(3)

    with col1:
        # Biểu đồ thanh: tồn kho theo material_no
        fig_bar = go.Figure(data=[go.Bar(
            x=df_chart['material_no'],
            y=df_chart['stock'],
            marker_color='skyblue'
        )])

        fig_bar.update_layout(
            title=dict(
                text="Top 10 tồn kho cao nhất",  # Tiêu đề
                x=0.5,  # Căn giữa theo trục x
                xanchor='center',  # Căn giữa tiêu đề theo trục x
                yanchor='top',  # Căn tiêu đề ở phía trên
            ),
            xaxis_title=None,
            yaxis_title=None,
            width=400,
            height=400,
            margin=dict(t=30, b=30, l=30, r=30),
            font=dict(size=10),
        )

        st.plotly_chart(fig_bar, use_container_width=False)

    with col2:
        # Biểu đồ tròn: tỷ lệ giá trị tồn kho theo phụ tùng (name)
        df_filtered['total_value'] = df_filtered['stock'] * df_filtered['price']
        fig_pie = px.pie(df_filtered, names='material_no', values='total_value', title='Tỷ lệ Giá Trị Tồn Kho')

        fig_pie.update_layout(
            title=dict(
                text="Tỷ lệ Giá Trị Tồn Kho",  # Tiêu đề
                x=0.5,  # Căn giữa theo trục x
                xanchor='center',  # Căn giữa tiêu đề theo trục x
                yanchor='top',  # Căn tiêu đề ở phía trên
            ),
            width=400,
            height=400,
            margin=dict(t=30, b=30, l=30, r=30),
            font=dict(size=10),
        )

        st.plotly_chart(fig_pie, use_container_width=False)

    with col3:
        # Biểu đồ thanh: số ngày tồn kho theo material_no
        fig_days_in_stock = go.Figure(data=[go.Bar(
            x=df_filtered['material_no'],
            y=df_filtered['storage_days'],
            marker_color='lightcoral'
        )])

        fig_days_in_stock.update_layout(
            title=dict(
                text="Số ngày tồn kho theo Material No",  # Tiêu đề
                x=0.5,  # Căn giữa theo trục x
                xanchor='center',  # Căn giữa tiêu đề theo trục x
                yanchor='top',  # Căn tiêu đề ở phía trên
            ),
            xaxis_title="Material No",
            yaxis_title="Số ngày tồn kho",
            width=400,
            height=400,
            margin=dict(t=30, b=30, l=30, r=30),
            font=dict(size=10),
        )

        st.plotly_chart(fig_days_in_stock, use_container_width=False)
    # Lọc dữ liệu
    df_filtered = df_stock.copy()

    if keyword.strip():
        kw = keyword.strip().lower()
        df_filtered = df_filtered[
            df_filtered['material_no'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['part_no'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['description'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['bin'].astype(str).str.lower().str.contains(kw, na=False) |
            df_filtered['cost_center'].astype(str).str.lower().str.contains(kw, na=False)
        ]

    df_filtered = df_filtered[
        (df_filtered['stock'] >= min_stock) & (df_filtered['stock'] <= max_stock)
    ]

    if selected_machine != 'Tất cả':
        df_filtered = df_filtered[df_filtered['machine_type'] == selected_machine]

    
    # Cấu hình bảng AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_filtered)

    # Ẩn cột image_url và ẩn cột index
    gb.configure_column("image_url", hide=True)
    gb.configure_column("index", hide=True)  # Ẩn cột index

    # Hiển thị số ngày tồn kho như bình thường
    gb.configure_column("storage_days", header_name="Days in Stock", type=["numericColumn"])

    # Cấu hình cột mặc định
    gb.configure_default_column(
        filter=False, sortable=True, editable=False, resizable=True,
        cellStyle=JsCode(""" 
            function(params) { 
                return { 
                    textAlign: 'center', 
                    border: '1px solid black',  // Viền ô
                    padding: '10px'  // Tăng padding ô
                }; 
            }
        """)
    )

    # Cấu hình cột stock để tô màu khi giá trị nhỏ hơn hoặc bằng 5
    gb.configure_column(
        "stock",
        cellStyle=JsCode(""" 
            function(params) {
                let style = {
                    textAlign: 'center',
                    border: '1px solid black',  // Viền vẫn giữ
                    padding: '10px'  // Tăng padding ô
                };
                if (params.value <= 30) {
                    style.backgroundColor = '#ffff99';  // Tô màu đỏ nhạt cho các giá trị <= 5
                    style.fontWeight = 'bold';
                }
                return style;
            }
        """)
    )

    # Cảnh báo nếu có sản phẩm tồn kho trên 60 ngày
    long_stock_items = df_stock[df_stock['storage_days'] > 40]
    if not long_stock_items.empty:
        st.markdown(
            f"<div style='background-color: #ff4d4d; padding: 20px; font-size: 20px; color: white; font-weight: bold; text-align: center; border-radius: 10px;'>⚠️ Cảnh báo! Có {len(long_stock_items)} sản phẩm đã tồn kho trên 40 ngày! Xử lý ngay!</div>", 
            unsafe_allow_html=True)

    # Cấu hình các cột đặc biệt
    gb.configure_selection('single')

    # Cập nhật chiều rộng cột description và các cột có thể chứa văn bản dài
    gb.configure_column("description", width=300, autoHeight=True)  # Đặt chiều rộng lớn hơn cho description

    # Cấu hình bảng và các cài đặt chiều rộng
    gb.configure_grid_options(domLayout='autoHeight', rowHeight=40)  # Tăng chiều cao dòng

    grid_options = gb.build()

    # Hiển thị bảng
    grid_response = AgGrid(
        df_filtered,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        theme="streamlit",
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True
    )

    # Hiển thị chi tiết của hàng đã chọn
    selected_rows = grid_response['selected_rows']

    if selected_rows is not None and len(selected_rows) > 0:
        selected = pd.DataFrame(selected_rows).iloc[0]

        st.markdown("<h3 style='text-align: center;'>📋 Material Details</h3>", unsafe_allow_html=True)

        # Chuyển đổi dữ liệu thành dạng dọc
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
            "Image": f"<img src='{selected['image_url']}' width='300'>" if selected['image_url'] else "No Image"
        }

        # Chuyển đổi thành dataframe dọc
        detail_df = pd.DataFrame(list(detail_data.items()), columns=["Attribute", "Value"])

        # Thêm CSS để căn giữa bảng và tăng kích thước hình ảnh
        st.markdown(""" 
        <style>
        table, th, td {
            border: 1px solid black;
            border-collapse: collapse;
            word-wrap: break-word;
            text-align: center;  /* Căn giữa bảng */
        }
        th, td {
            padding: 12px;
            font-size: 18px;
        }
        th {
            background-color: #f5f5f5;
            color: #333;
            font-weight: bold;
        }
        table tr:hover {
            background-color: #f0f0f0;
        }
        img {
            width: 300px;  /* Tăng kích thước hình ảnh */
            height: auto;
        }
        table {
            margin: 0 auto;  /* Căn giữa bảng */
        }
        </style>
        """, unsafe_allow_html=True)
    
        # Hiển thị bảng theo dạng dọc
        st.markdown(detail_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Nút tải Excel
    if not df_filtered.empty:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Stock')

        st.download_button(
            label="📥 Download Excel",
            data=excel_buffer.getvalue(),
            file_name="stock_view.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ Không tìm thấy kết quả phù hợp.")
