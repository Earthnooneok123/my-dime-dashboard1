import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import google.generativeai as genai
import yfinance as yf
from datetime import datetime

st.set_page_config(
    page_title="Gemini-Powered Investment Dashboard",
    page_icon="📈",
    layout="wide"
)

GOOGLE_API_KEY = "AQ.Ab8RN6KhuiDCupxmizhACXEzoqs7ZSGoHdbua4P0GAMpGVgV6A"

if 'df' not in st.session_state:
    default_data = {
        'Asset': ['SP50001', 'NDX01', 'VOO', 'QQQI', 'QQQM', 'SCB', 'ICHI', 'MANU'],
        'Category': ['กองทุน 💰', 'กองทุน 💰', 'กองทุน 💰', 'กองทุน 💰', 'กองทุน 💰', 'ปันผล 🌀', 'ปันผล 🌀', 'ซิ่งจัด 😈'],
        'Value_THB': [7852.00, 6257.25, 5837.97, 5539.17, 5581.56, 4696.50, 1480.00, 313.79],
        'Profit_THB': [365.42, 247.86, 211.17, -11.10, 72.92, 355.57, 190.00, 65.31]
    }
    st.session_state.df = pd.DataFrame(default_data)

st.title("🚀 GEMINI-POWERED INVESTMENT DASHBOARD")
st.caption("AI วิเคราะห์รูปสลิป/หน้าจอ Dime! หลายรูปพร้อมกัน และอัปเดตตัวเลขแบบเรียลไทม์")
st.divider()

# --- ส่วนแถบข้าง (Sidebar) ---
with st.sidebar:
    st.header("⚙️ จัดการพอร์ตด้วย AI")
    
    st.subheader("📸 อัปโหลดรูปภาพหลายรูปพร้อมกัน")
    # เปลี่ยนเป็น multiple files
    uploaded_files = st.file_uploader("เลือกรูปภาพสลิป/หน้าจอพอร์ต Dime!", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    st.divider()
    
    if uploaded_files:
        st.write(f"พบ {len(uploaded_files)} รูปภาพ...")
        
        # ฟังก์ชันให้ AI วิเคราะห์
        def analyze_images_with_gemini(files):
            images = [Image.open(file) for file in files]
            
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash-latest') # หรือ gemini-pro-vision
            
            prompt = """
            วิเคราะห์รูปภาพสลิปหรือหน้าจอพอร์ต Dime! ทั้งหมดเหล่านี้ (ถ้ามีหลายรูป) และดึงข้อมูลสำคัญตามตารางด้านล่างนี้ออกมาเป็น JSON:
            1. ชื่อสินทรัพย์ (Asset Name เช่น VOO, QQQM, หรือกองทุนไทย)
            2. มูลค่าปัจจุบัน (Current Value เป็น THB เสมอ)
            3. กำไร/ขาดทุนปัจจุบัน (Profit/Loss เป็น THB)

            สรุปผลทั้งหมดเป็น JSON ให้อยู่ในรูปแบบนี้:
            [
              {"Asset": "VOO", "Value_THB": 15000.50, "Profit_THB": 1200.00},
              {"Asset": "SP50001", "Value_THB": 8500.00, "Profit_THB": -200.00}
            ]
            ถ้าหาข้อมูลตัวไหนไม่เจอ ให้ใส่ค่าเป็น 0.00 อย่าเดาตัวเลข
            """
            
            try:
                response = model.generate_content([prompt] + images)
                # ผมจะดึงเฉพาะส่วนที่เป็น JSON ออกมา
                import json
                text = response.text
                json_start = text.find('[')
                json_end = text.rfind(']') + 1
                json_string = text[json_start:json_end]
                return json.loads(json_string)
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์ด้วย AI: {e}")
                return None

        # ปุ่มกดให้ AI เริ่มทำงาน
        if st.button("🧠 ให้ AI วิเคราะห์รูปภาพและอัปเดตพอร์ต"):
            with st.spinner("กำลังให้ AI วิเคราะห์รูปภาพหลายรูปพร้อมกัน..."):
                analysis_results = analyze_images_with_gemini(uploaded_files)
                if analysis_results:
                    # อัปเดตตารางพอร์ต
                    df_current = st.session_state.df
                    for result in analysis_results:
                        asset_name = result.get('Asset', '')
                        if asset_name in df_current['Asset'].values:
                            # อัปเดตเฉพาะตัวที่ AI เจอ
                            row_index = df_current[df_current['Asset'] == asset_name].index[0]
                            df_current.loc[row_index, 'Value_THB'] = result['Value_THB']
                            df_current.loc[row_index, 'Profit_THB'] = result['Profit_THB']
                        else:
                            st.warning(f"สินทรัพย์ชื่อ '{asset_name}' ไม่อยู่ในตารางพอร์ตเริ่มต้น จะข้ามการอัปเดต")
                    
                    st.session_state.df = df_current
                    st.success("อัปเดตตัวเลขตามรูปภาพเรียบร้อยแล้ว!")

    st.divider()
    
    st.subheader("✏️ แก้ไขยอดเงินเอง (ถ้า AI ดึงไม่ครบ)")
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

# --- ส่วนแสดงผลหลัก ---
df = st.session_state.df.copy()
# คำนวณ % Profit
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

if uploaded_files:
    st.subheader(f"🖼️ รูปภาพที่อัปโหลดล่าสุด ({len(uploaded_files)} รูป)")
    col_img = st.columns(min(len(uploaded_files), 4)) # แสดงรูปละคอลัมน์
    for i, file in enumerate(uploaded_files):
        with col_img[i % 4]:
            image = Image.open(file)
           st.image(image, caption=f"รูปที่ {i+1}", use_column_width=True)
    st.divider()

# --- กราฟ ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 สัดส่วนพอร์ต (Donut Chart)")
    fig_pie = px.pie(df, values='Value_THB', names='Asset', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_traces(textinfo='percent+label')
    fig_pie.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    st.subheader("📈 ผลตอบแทน % รายสินทรัพย์")
    # กำหนดสี: บวก=เขียว, ลบ=แดง
    df['Color'] = df['Profit_Pct'].apply(lambda x: '#10B981' if x >= 0 else '#EF4444')
    fig_bar = px.bar(df, x='Asset', y='Profit_Pct', text_auto='.2f', color='Color', color_discrete_map="identity")
    fig_bar.update_layout(template="plotly_dark", yaxis_title="กำไร (%)", xaxis_title="")
    st.plotly_chart(fig_bar, use_container_width=True)
