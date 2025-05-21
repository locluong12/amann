import streamlit as st
import pandas as pd
import altair as alt
from database import get_engine

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

    st.markdown("<h1 style='text-align: center; color: white;'>Warehouse Dashboard</h1>", unsafe_allow_html=True)

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
        st.markdown(card_style.format("Total Inventory", f"{total_items_in_stock:,}"), unsafe_allow_html=True)
    with col2:
        st.markdown(card_style.format("Total Value", f"${total_value_in_stock:,.0f}"), unsafe_allow_html=True)
    with col3:
        st.markdown(card_style.format("Total Import", f"{total_import:,}"), unsafe_allow_html=True)
    with col4:
        st.markdown(card_style.format("Total Export", f"{total_export:,}"), unsafe_allow_html=True)
    with col5:
        st.markdown(card_style.format("Total Export Value", f"${total_export_value:,.0f}"), unsafe_allow_html=True)

    # --- Phần biểu đồ phía dưới ---

    st.markdown("<h3 style='text-align: center; color: white; margin-top: 40px;'>Stock Overview</h3>", unsafe_allow_html=True)

    stock_overview = df_stock.groupby('description').agg({'stock': 'sum'}).reset_index()
    stock_overview = stock_overview.sort_values('stock', ascending=False)

    chart_stock = alt.Chart(stock_overview).mark_bar(
        color='#008080',
        opacity=0.7,
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6
    ).encode(
        x=alt.X('description:N', sort='-y', title='Phụ tùng'),
        y=alt.Y('stock:Q', title='Tồn kho'),
        tooltip=['description', 'stock']
    ).properties(width=800, height=400)

    text_stock = chart_stock.mark_text(
        align='center',
        baseline='bottom',
        dy=-5,
        color='white',
        fontWeight='bold'
    ).encode(
        text='stock:Q'
    )

    st.altair_chart(chart_stock + text_stock, use_container_width=True)

 


  

   
    st.markdown("<h4 style='text-align: center; color: white;'>So sánh tồn kho và tồn kho an toàn</h4>", unsafe_allow_html=True)

    # Tạo cột status để đổi màu
    df_stock['status'] = df_stock.apply(
        lambda row: 'Under Safety Stock' if row['stock'] < row['safety_stock'] else 'Above Safety Stock',
        axis=1
    )

    # Màu cho cột stock
    bar_stock = alt.Chart(df_stock).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        opacity=0.7
    ).encode(
        x=alt.X('description:N', sort='-y', title='Phụ tùng'),
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

    # Label cho stock với màu tương ứng
    text_stock = alt.Chart(df_stock).mark_text(
        align='center',
        dy=-10,
        fontWeight='bold'
    ).encode(
        x='description:N',
        y='stock:Q',
        text=alt.Text('stock:Q', format='.0f'),
        color=alt.condition(
            alt.datum.stock < alt.datum.safety_stock,
            alt.value('red'),
            alt.value("#015353")
        ),
        detail='description:N'
    )

    # Cột safety_stock màu vàng
    bar_safety = alt.Chart(df_stock).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        opacity=0.5,
        color='yellow'
    ).encode(
        x=alt.X('description:N', sort='-y', title='Phụ tùng'),
        y=alt.Y('safety_stock:Q', title='Số lượng'),
        tooltip=[
            alt.Tooltip('description:N', title='Phụ tùng'),
            alt.Tooltip('safety_stock:Q', title='Tồn kho an toàn'),
        ]
    )

    # Label cho safety_stock (màu vàng)
    text_safety = alt.Chart(df_stock).mark_text(
        align='center',
        dy=-10,
        fontWeight='bold',
        color='gold'  # hoặc 'yellow'
    ).encode(
        x='description:N',
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
        width=400,
        height=400
    )

    st.altair_chart(chart_combined, use_container_width=True)



    # Hai cột song song (chia cột với biểu đồ nhập xuất)
    col1, col2, col3 = st.columns([1,1,1])

    with col1:
        st.markdown("<h3 style='text-align: center; color: white;'>Nhập kho theo ngày</h3>", unsafe_allow_html=True)
        with engine.begin() as conn:
            df_import_history = pd.read_sql("SELECT date, quantity FROM import_export WHERE im_ex_flag = 1", conn)

        df_import_history['date'] = pd.to_datetime(df_import_history['date']).dt.date
        daily_imports = df_import_history.groupby('date')['quantity'].sum().reset_index()
        daily_imports = daily_imports.sort_values('date')
        daily_imports['date'] = daily_imports['date'].apply(lambda x: x.strftime('%d/%m/%Y'))

        chart_imports = alt.Chart(daily_imports).mark_bar(
            color='#008080',
            opacity=0.7,
            cornerRadius=5
        ).encode(
            x=alt.X('date:N', title='Ngày', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantity:Q', title='Số lượng nhập'),
            tooltip=['date:N', 'quantity:Q']
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
        st.markdown("<h3 style='text-align: center; color: white;'>Xuất kho theo ngày</h3>", unsafe_allow_html=True)
        with engine.begin() as conn:
            df_export_history = pd.read_sql("SELECT date, quantity FROM import_export WHERE im_ex_flag = 0", conn)

        df_export_history['date'] = pd.to_datetime(df_export_history['date']).dt.date
        daily_exports = df_export_history.groupby('date')['quantity'].sum().reset_index()
        daily_exports = daily_exports.sort_values('date')
        daily_exports['date'] = daily_exports['date'].apply(lambda x: x.strftime('%d/%m/%Y'))

        chart_exports = alt.Chart(daily_exports).mark_bar(
            color='#008080',
            opacity=0.7,
            cornerRadius=5
        ).encode(
            x=alt.X('date:N', title='Ngày', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('quantity:Q', title='Số lượng xuất'),
            tooltip=['date:N', 'quantity:Q']
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
    with col3:
        st.markdown("<h3 style='text-align: center; color: white;'>Giá trị nhập kho theo ngày</h3>", unsafe_allow_html=True)

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

        df_import_value['date'] = pd.to_datetime(df_import_value['date']).dt.date
        df_import_value['import_value'] = df_import_value['quantity'] * df_import_value['price']

        # Nhóm theo ngày
        daily_import_value = df_import_value.groupby('date')['import_value'].sum().reset_index()
        daily_import_value = daily_import_value.sort_values('date')
        daily_import_value['date'] = daily_import_value['date'].apply(lambda x: x.strftime('%d/%m/%Y'))

        # Vẽ biểu đồ
        chart_value = alt.Chart(daily_import_value).mark_bar(
            color='#008080',
            opacity=0.8,
            cornerRadius=5
        ).encode(
            x=alt.X('date:N', title='Ngày', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('import_value:Q', title='Giá trị nhập kho (VND)'),
            tooltip=[
                alt.Tooltip('date:N', title='Ngày'),
                alt.Tooltip('import_value:Q', title='Giá trị nhập', format=',.0f')
            ]
        ).properties(width=350, height=500)

        text_value = chart_value.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,
            color='white',
            fontWeight='bold'
        ).encode(
            text=alt.Text('import_value:Q', format=',.0f')
        )

        st.altair_chart(chart_value + text_value, use_container_width=True)







    # Chuyển cột import_date sang datetime
    df_stock['import_date'] = pd.to_datetime(df_stock['import_date'])

    # Lấy ngày nhập kho gần nhất
    df_last_inbound = df_stock.groupby('material_no')['import_date'].max().reset_index()
    df_last_inbound.rename(columns={'import_date': 'last_inbound_date'}, inplace=True)

    # Gộp lại với df_stock
    df_stock = df_stock.merge(df_last_inbound, on='material_no', how='left')

    # Tính số ngày lưu kho
    today = pd.Timestamp.today().normalize()
    df_stock['days_in_stock'] = (today - df_stock['last_inbound_date']).dt.days

    # Lọc phụ tùng có tồn kho > 0
    df_stock_filtered = df_stock[df_stock['stock'] > 0]

    # Chia thành 2 cột
    col1, col2 = st.columns(2)

    # ------------------ CỘT 1: Số ngày lưu kho ------------------
    with col1:
        st.markdown("<h3 style='text-align: center; color: white;'>Số ngày lưu kho</h3>", unsafe_allow_html=True)

        chart_lifetime = alt.Chart(df_stock_filtered).mark_bar(
            cornerRadiusTopLeft=6,
            cornerRadiusTopRight=6,
            color='#008080',
            opacity=0.7
        ).encode(
            y=alt.Y('material_no:N', sort='-x', title='Mã phụ tùng'),
            x=alt.X('days_in_stock:Q', title='Số ngày lưu kho'),
            tooltip=[
                alt.Tooltip('material_no:N', title='Mã phụ tùng'),
                alt.Tooltip('days_in_stock:Q', title='Số ngày lưu kho'),
                alt.Tooltip('stock:Q', title='Tồn kho hiện tại')
            ]
        ).properties(
            width=350,
            height=500
        )

        text_lifetime = chart_lifetime.mark_text(
            align='center',
            baseline='bottom',
            dy=-5,
            color='white',
            fontWeight='bold'
        ).encode(
            text=alt.Text('days_in_stock:Q')
        )

        st.altair_chart(chart_lifetime + text_lifetime, use_container_width=True)

    # ------------------ CỘT 2: Giá trị xuất kho theo ngày ------------------
    with col2:
        st.markdown("<h3 style='text-align: center; color: white;'>Giá trị xuất kho theo ngày</h3>", unsafe_allow_html=True)

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

        df_export_value['date'] = pd.to_datetime(df_export_value['date']).dt.date
        df_export_value['export_value'] = df_export_value['quantity'] * df_export_value['price']

        # Nhóm theo ngày
        daily_export_value = df_export_value.groupby('date')['export_value'].sum().reset_index()
        daily_export_value = daily_export_value.sort_values('date')
        daily_export_value['date'] = daily_export_value['date'].apply(lambda x: x.strftime('%d/%m/%Y'))

        # Vẽ biểu đồ
        chart_export = alt.Chart(daily_export_value).mark_bar(
            color='#008080',
            opacity=0.8,
            cornerRadius=5
        ).encode(
            x=alt.X('date:N', title='Ngày', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('export_value:Q', title='Giá trị xuất kho (VND)'),
            tooltip=[
                alt.Tooltip('date:N', title='Ngày'),
                alt.Tooltip('export_value:Q', title='Giá trị xuất', format=',.0f')
            ]
        ).properties(width=350, height=500)

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


       
    st.markdown("<h3 style='text-align: center; color: white; margin-top: 40px;'>Top 10 phụ tùng có giá trị tồn kho cao nhất</h3>", unsafe_allow_html=True)
    df_stock['total_value'] = df_stock['stock'] * df_stock['price']
    top10_value = df_stock.sort_values('total_value', ascending=False).head(10)

    chart_top10 = alt.Chart(top10_value).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        color='#008080',
        opacity=0.7
    ).encode(
        x=alt.X('description:N', sort='-y', title='Tên phụ tùng', axis=alt.Axis(labelAngle=-40)),
        y=alt.Y('total_value:Q', title='Tổng giá trị ($)', axis=alt.Axis(format=",.0f")),
        tooltip=[
            alt.Tooltip('description:N', title='Phụ tùng'),
            alt.Tooltip('stock:Q', title='Tồn kho'),
            alt.Tooltip('price:Q', title='Giá'),
            alt.Tooltip('total_value:Q', title='Tổng giá trị', format=",.0f")
        ]
    ).properties(width=800, height=400)

    text_top10 = chart_top10.mark_text(
        align='center',
        baseline='bottom',
        dy=-5,
        color='white',
        fontWeight='bold'
    ).encode(
        text=alt.Text('total_value:Q', format=',.0f')
    )

    st.altair_chart(chart_top10 + text_top10, use_container_width=True)
    


# Nếu muốn chạy trực tiếp
if __name__ == "__main__":
    show_dashboard()

             
