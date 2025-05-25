import streamlit as st
import pandas as pd
import altair as alt
from database import get_engine
import datetime
datetime.datetime.now()


# Cấu hình Altair theme trong suốt, chữ trắng
def transparent_theme():
    return {
        'config': {
            'background': 'transparent',
            'title': {'color': 'white'},
            'axis': {
                'labelColor': 'white',
                'titleColor': 'white',
                'gridColor': '#444',
                'domainColor': 'white',
                'tickColor': 'white'
            },
            'legend': {
                'labelColor': 'white',
                'titleColor': 'white'
            }
        }
    }

alt.themes.register('transparent', transparent_theme)
alt.themes.enable('transparent')

def show_dashboard():
    st.markdown(
        """
        <style>
            body {
                background-color: transparent;
                color: white;
            }
            .block-container {
                background-color: transparent !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<h1 style='text-align: center; color: white;'>Tổng quan kho phụ tùng</h1>", unsafe_allow_html=True)

    engine = get_engine()
    with engine.begin() as conn:
        # Lấy dữ liệu tồn kho
        df_stock = pd.read_sql("""
            SELECT material_no, description, stock, price, safety_stock,import_date
            FROM spare_parts
        """, conn)

        # Tổng số lượng nhập kho
        total_import = pd.read_sql("""
            SELECT SUM(quantity) AS total_import 
            FROM import_export 
            WHERE im_ex_flag = 1
        """, conn).iloc[0]['total_import']

        # Tổng số lượng xuất kho
        total_export = pd.read_sql("""
            SELECT SUM(quantity) AS total_export 
            FROM import_export 
            WHERE im_ex_flag = 0
        """, conn).iloc[0]['total_export']

        # Tổng giá trị xuất kho
        total_export_value_result = pd.read_sql("""
            SELECT 
                SUM(ie.quantity * sp.price) AS total_export_value
            FROM import_export ie
            JOIN spare_parts sp ON ie.part_id = sp.material_no
            WHERE ie.im_ex_flag = 0
        """, conn)

        total_export_value = total_export_value_result['total_export_value'].iloc[0]

    # Chuyển đổi các giá trị None về 0 nếu có
    total_items_in_stock = int(df_stock['stock'].sum())
    total_import = int(total_import) if total_import is not None else 0
    total_export = int(total_export) if total_export is not None else 0
    total_value_in_stock = float((df_stock['stock'] * df_stock['price']).sum())
    total_export_value = float(total_export_value) if total_export_value is not None else 0

    # Hiển thị các chỉ số trong giao diện (ở đầu trang)
    col1, col2, col3, col4, col5 = st.columns(5)

    card_style = """
        <div style="border: 1px solid #00bfa5; border-radius: 10px; padding: 15px; text-align: center;
                    background-color: rgba(0,0,0,0.3); color: white;">
            <div style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">{}</div>
            <div style="font-size: 24px; color: #00bfa5;">{}</div>
        </div>
    """

    with col1:
        st.markdown(card_style.format("Tổng số lượng tồn", f"{total_items_in_stock:,} cái"), unsafe_allow_html=True)
    with col2:
        st.markdown(card_style.format("Tổng giá trị tồn", f"${total_value_in_stock:,.0f}"), unsafe_allow_html=True)
    with col3:
        st.markdown(card_style.format("Tổng số lượng nhập", f"{total_import:,} cái"), unsafe_allow_html=True)
    with col4:
        st.markdown(card_style.format("Tổng số lượng xuất", f"{total_export:,} cái"), unsafe_allow_html=True)
    with col5:
        st.markdown(card_style.format("Tổng giá trị xuất", f"${total_export_value:,.0f}"), unsafe_allow_html=True)


    # --- Phần biểu đồ phía dưới ---
    # Sắp xếp dữ liệu giảm dần theo tồn kho
    df_stock_sorted = df_stock.sort_values(by='stock', ascending=False)

    # Tạo cột status để đổi màu
    df_stock_sorted['status'] = df_stock_sorted.apply(
        lambda row: 'Under Safety Stock' if row['stock'] < row['safety_stock'] else 'Above Safety Stock',
        axis=1
    )

    st.markdown("<h4 style='text-align: center; color: white;'>Tồn kho hiện tại</h4>", unsafe_allow_html=True)

    bar_stock = alt.Chart(df_stock_sorted).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        opacity=0.7
    ).encode(
        x=alt.X('description:N', sort=df_stock_sorted['description'].tolist(), title='Phụ tùng'),
        y=alt.Y('stock:Q', title='Số lượng'),
        color=alt.condition(
            alt.datum.stock < alt.datum.safety_stock,
            alt.value('red'),      # Dưới tồn kho an toàn
            alt.value("#05CECE")   # Trên tồn kho an toàn
        ),
        tooltip=[
            alt.Tooltip('description:N', title='Phụ tùng'),
            alt.Tooltip('stock:Q', title='Tồn kho'),
        ]
    )

    text_stock = alt.Chart(df_stock_sorted).mark_text(
        align='center',
        dy=-10,
        fontWeight='bold'
    ).encode(
        x=alt.X('description:N', sort=df_stock_sorted['description'].tolist()),
        y='stock:Q',
        text=alt.Text('stock:Q', format='.0f'),
        color=alt.condition(
            alt.datum.stock < alt.datum.safety_stock,
            alt.value('red'),
            alt.value("#015353")
        ),
        detail='description:N'
    )

    bar_safety = alt.Chart(df_stock_sorted).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        opacity=0.5,
        color='yellow'
    ).encode(
        x=alt.X('description:N', sort=df_stock_sorted['description'].tolist(), title='Phụ tùng'),
        y=alt.Y('safety_stock:Q', title='Số lượng'),
        tooltip=[
            alt.Tooltip('description:N', title='Phụ tùng'),
            alt.Tooltip('safety_stock:Q', title='Tồn kho an toàn'),
        ]
    )

    text_safety = alt.Chart(df_stock_sorted).mark_text(
        align='center',
        dy=-10,
        fontWeight='bold',
        color='gold'
    ).encode(
        x=alt.X('description:N', sort=df_stock_sorted['description'].tolist()),
        y='safety_stock:Q',
        text=alt.Text('safety_stock:Q', format='.0f'),
        detail='description:N'
    )

    # Gộp biểu đồ
    chart_combined = alt.layer(
        bar_safety, text_safety,
        bar_stock, text_stock
    ).resolve_scale(
        y='shared'
    ).properties(
        width=800,
        height=400
    )

    st.altair_chart(chart_combined, use_container_width=True)




    # Hai cột song song (chia cột với biểu đồ nhập xuất)
    col1, col2, col3 = st.columns([1,1,1])
# Lấy dữ liệu nhập xuất kho 1 lần duy nhất
    with engine.begin() as conn:
        df_import_history = pd.read_sql("SELECT date, quantity FROM import_export WHERE im_ex_flag = 1", conn)
        df_export_history = pd.read_sql("SELECT date, quantity FROM import_export WHERE im_ex_flag = 0", conn)

    # Chuyển cột date về datetime
    df_import_history['date'] = pd.to_datetime(df_import_history['date'])
    df_export_history['date'] = pd.to_datetime(df_export_history['date'])

    # Tạo cột month theo định dạng 'YYYY-MM'
    df_import_history['month'] = df_import_history['date'].dt.to_period('M').astype(str)
    df_export_history['month'] = df_export_history['date'].dt.to_period('M').astype(str)

    # Tạo danh sách tháng duy nhất (theo cả 2 bảng)
    start_date = min(df_import_history['date'].min(), df_export_history['date'].min())
    end_date = max(df_import_history['date'].max(), df_export_history['date'].max())
    all_months = pd.period_range(start=start_date, end=end_date, freq='M').astype(str).tolist()
    all_months_dates = [datetime.datetime.strptime(m, "%Y-%m").date() for m in all_months]

    # Slider chọn khoảng tháng dùng chung
    start_month_date, end_month_date = st.slider(
        "Chọn khoảng thời gian (tháng)",
        min_value=all_months_dates[0],
        max_value=all_months_dates[-1],
        value=(all_months_dates[0], all_months_dates[-1]),
        format="YYYY-MM"
    )

    start_month = start_month_date.strftime("%Y-%m")
    end_month = end_month_date.strftime("%Y-%m")

    # Lọc dữ liệu theo khoảng tháng đã chọn
    df_import_filtered = df_import_history[(df_import_history['month'] >= start_month) & (df_import_history['month'] <= end_month)]
    df_export_filtered = df_export_history[(df_export_history['month'] >= start_month) & (df_export_history['month'] <= end_month)]

    # Tổng hợp số lượng theo tháng
    monthly_imports = df_import_filtered.groupby('month')['quantity'].sum().reset_index()
    monthly_exports = df_export_filtered.groupby('month')['quantity'].sum().reset_index()

    # Vẽ biểu đồ nhập kho và xuất kho theo tháng
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h3 style='text-align: center; color: white;'>Nhập kho theo tháng</h3>", unsafe_allow_html=True)

        chart_imports = alt.Chart(monthly_imports).mark_bar(
            color='#008080',
            opacity=0.7,
            cornerRadius=5
        ).encode(
            x=alt.X('month:N', title='Tháng', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantity:Q', title='Số lượng nhập (cái)'),
            tooltip=['month:N', 'quantity:Q']
        ).properties(width=350, height=500)

        text_imports = chart_imports.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,
            color='white',
            fontWeight='bold'
        ).encode(
            text='quantity:Q'
        )

        st.altair_chart(chart_imports + text_imports, use_container_width=True)

    with col2:
        st.markdown("<h3 style='text-align: center; color: white;'>Xuất kho theo tháng</h3>", unsafe_allow_html=True)

        chart_exports = alt.Chart(monthly_exports).mark_bar(
            color='#008080',
            opacity=0.7,
            cornerRadius=5
        ).encode(
            x=alt.X('month:N', title='Tháng', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantity:Q', title='Số lượng xuất(cái)'),
            tooltip=['month:N', 'quantity:Q']
        ).properties(width=350, height=500)

        text_exports = chart_exports.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,
            color='white',
            fontWeight='bold'
        ).encode(
            text='quantity:Q'
        )

        st.altair_chart(chart_exports + text_exports, use_container_width=True)
        # =================== TẠO CỘT VÀ XỬ LÝ DỮ LIỆU ===================
    # Chuyển đổi cột ngày
    df_stock['import_date'] = pd.to_datetime(df_stock['import_date'])
    df_stock['month'] = df_stock['import_date'].dt.strftime('%Y-%m')

    # Lọc dữ liệu theo khoảng tháng được chọn
    df_stock = df_stock[(df_stock['month'] >= start_month) & (df_stock['month'] <= end_month)]

    # Tính ngày nhập gần nhất
    df_last_inbound = df_stock.groupby('material_no')['import_date'].max().reset_index()
    df_last_inbound.rename(columns={'import_date': 'last_inbound_date'}, inplace=True)
    df_stock = df_stock.merge(df_last_inbound, on='material_no', how='left')

    # Lọc phụ tùng còn tồn kho
    df_stock_filtered = df_stock[df_stock['stock'] > 0]

    # =================== TẠO GIAO DIỆN 2 CỘT ===================
    col1, col2 = st.columns(2)

    # ------------------ CỘT 1: Nhập kho theo tháng ------------------
    with col1:
        st.markdown("<h3 style='text-align: center; color: white;'>Giá trị nhập kho theo tháng</h3>", unsafe_allow_html=True)

        with engine.begin() as conn:
            df_import_value = pd.read_sql("""
                SELECT 
                    ie.date, 
                    ie.quantity, 
                    sp.price
                FROM import_export ie
                JOIN spare_parts sp ON ie.part_id = sp.material_no
                WHERE ie.im_ex_flag = 1
            """, conn)

        df_import_value['date'] = pd.to_datetime(df_import_value['date'])
        df_import_value['month'] = df_import_value['date'].dt.strftime('%Y-%m')
        df_import_value['import_value'] = df_import_value['quantity'] * df_import_value['price']

        df_import_value = df_import_value[
            (df_import_value['month'] >= start_month) & (df_import_value['month'] <= end_month)
        ]

        monthly_import_value = df_import_value.groupby('month')['import_value'].sum().reset_index()

        chart_import = alt.Chart(monthly_import_value).mark_bar(
            color='#008080',
            opacity=0.8,
            cornerRadius=5
        ).encode(
            x=alt.X('month:N', title='Tháng'),
            y=alt.Y('import_value:Q', title='Giá trị nhập kho ($)'),
            tooltip=[
                alt.Tooltip('month:N', title='Tháng'),
                alt.Tooltip('import_value:Q', title='Giá trị nhập', format=',.0f')
            ]
        ).properties(width=350, height=400)

        text_import = chart_import.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,
            color='white',
            fontWeight='bold'
        ).encode(
            text=alt.Text('import_value:Q', format=',.0f')
        )

        st.altair_chart(chart_import + text_import, use_container_width=True)

    # ------------------ CỘT 2: Xuất kho theo tháng ------------------
    with col2:
        st.markdown("<h3 style='text-align: center; color: white;'>Giá trị xuất kho theo tháng</h3>", unsafe_allow_html=True)

        with engine.begin() as conn:
            df_export_value = pd.read_sql("""
                SELECT 
                    ie.date, 
                    ie.quantity, 
                    sp.price
                FROM import_export ie
                JOIN spare_parts sp ON ie.part_id = sp.material_no
                WHERE ie.im_ex_flag = 0
            """, conn)

        df_export_value['date'] = pd.to_datetime(df_export_value['date'])
        df_export_value['month'] = df_export_value['date'].dt.strftime('%Y-%m')
        df_export_value['export_value'] = df_export_value['quantity'] * df_export_value['price']

        df_export_value = df_export_value[
            (df_export_value['month'] >= start_month) & (df_export_value['month'] <= end_month)
        ]

        monthly_export_value = df_export_value.groupby('month')['export_value'].sum().reset_index()

        chart_export = alt.Chart(monthly_export_value).mark_bar(
            color='#008080',
            opacity=0.8,
            cornerRadius=5
        ).encode(
            x=alt.X('month:N', title='Tháng'),
            y=alt.Y('export_value:Q', title='Giá trị xuất kho ($)'),
            tooltip=[
                alt.Tooltip('month:N', title='Tháng'),
                alt.Tooltip('export_value:Q', title='Giá trị xuất', format=',.0f')
            ]
        ).properties(width=350, height=400)

        text_export = chart_export.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,
            color='white',
            fontWeight='bold'
        ).encode(
            text=alt.Text('export_value:Q', format=',.0f')
        )

        st.altair_chart(chart_export + text_export, use_container_width=True)
    
        
# Nếu muốn chạy trực tiếp
if __name__ == "__main__":
    show_dashboard()

             
