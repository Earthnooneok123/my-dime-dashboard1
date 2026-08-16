import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="My Interactive Investment Dashboard",
    page_icon="📈",
    layout="wide"
)

# 2. ตัวแปรเก็บข้อมูลพอร์ตเริ่มต้น (Session State เพื่อให้แก้ไขบนหน้าเว็บได้เรียลไทม์)
if 'df' not in st.session_state:
    default_data = {
        'Asset': ['SP50001', 'NDX01', 'VOO', 'QQQI', 'QQQM', 'SCB', 'ICHI', 'MANU'],
        'Category': ['กองทุน 💰', 'กองทุน 💰', 'กองทุน 💰', 'กองทุน 💰', 'กองทุน 💰', 'ปันผล 🌀', 'ปันผล 🌀', 'ซิ่งจัด 😈'],
        'Value_THB': [7852.00, 6257.25, 5837.97, 5539.17, 5581.56, 4696.50, 1480.00, 313.79],
        'Profit_THB': [365.42, 247.86, 211.17, -11.10, 72.92, 355.57, 190.00, 65.31]
    }
    st.session_state.df = pd.DataFrame(default_data)

st.title("🚀 MY LIVE INVESTMENT DASHBOARD")
st.caption("อัปเดตข้อมูล อัปโหลดรูปสลิป/หน้าจอ และปรับแต่งพอร์ตได้เรียลไทม์")
st.divider()

# 3. แถบด้านข้าง (Sidebar): อัปโหลดรูปภาพ & ปรับข้อมูลเรียลไทม์
with st.sidebar:
    st.header("⚙️ เมนูจัดการพอร์ต (Control Panel)")
    
    st.subheader("📸 อัปโหลดรูปภาพหน้าจอ/สลิป")
    uploaded_file = st.file_uploader("เลือกรูปภาพจากมือถือ/คอม", type=["jpg", "jpeg", "png"])
    
    st.divider()
    
    st.subheader("✏️ แก้ไขยอดเงินในพอร์ต")
    st.info("พิมพ์เปลี่ยนตัวเลขด้านล่างนี้ กราฟจะเปลี่ยนตามทันที!")
    
    edited_df = st.data_editor(
        st.session_state.df,
        column_config={
            "Value_THB": st.column_config.NumberColumn("มูลค่า (บาท)", format="฿%.2f"),
            "Profit_THB": st.column_config.NumberColumn("กำไร/ขาดทุน (บาท)", format="฿%.2f")
        },
        num_rows="dynamic",
        use_container_width=True
    )
    st.session_state.df = edited_df

# 4. คำนวณตัวเลข & แสดงผลบน Dashboardหลัก
df = st.session_state.df
df['Profit_Pct'] = (df['Profit_THB'] / (df['Value_THB'] - df['Profit_THB'])) * 100

total_value = df['Value_THB'].sum()
total_profit = df['Profit_THB'].sum()
total_cost = total_value - total_profit
total_return = (total_profit / total_cost) * 100 if total_cost != 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("มูลค่าพอร์ตรวม", f"฿{total_value:,.2f}")
col2.metric("เงินต้นรวม", f"฿{total_cost:,.2f}")
col3.metric("กำไร/ขาดทุนรวม", f"฿{total_profit:,.2f}", f"{total_return:.2f}%")
col4.metric("บรรยากาศพอร์ต", "🟢 เขียวขจี" if total_profit > 0 else "🔴 แดงเดือด")

st.divider()

if uploaded_file is not None:
    st.subheader("🖼️ รูปภาพหน้าจอพอร์ตที่อัปโหลดล่าสุด")
    image = Image.open(uploaded_file)
    st.image(image, caption="รูปภาพอัปโหลดสภาวะพอร์ต / คำสั่งซื้อ", use_container_width=True)
    st.divider()

# 5. กราฟวิเคราะห์พอร์ต
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 สัดส่วนพอร์ต (Donut Chart)")
    fig_pie = px.pie(
        df, values='Value_THB', names='Asset',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_pie.update_traces(textinfo='percent+label')
    fig_pie.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    st.subheader("📈 ผลตอบแทน % รายสินทรัพย์ (Bar Chart)")
    df['Color'] = df['Profit_Pct'].apply(lambda x: '#10B981' if x >= 0 else '#EF4444')
    fig_bar = px.bar(
        df, x='Asset', y='Profit_Pct',
        text_auto='.2f',
        color='Color',
        color_discrete_map="identity"
    )
    fig_bar.update_layout(template="plotly_dark", yaxis_title="กำไร (%)", xaxis_title="")
    st.plotly_chart(fig_bar, use_container_width=True)
