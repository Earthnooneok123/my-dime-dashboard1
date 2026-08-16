import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from google import genai
import json

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="Investment Dashboard (Gemini Powered)",
    page_icon="📈",
    layout="wide"
)

if 'df' not in st.session_state:
    default_data = {
        'Asset': ['SP50001', 'NDX01', 'VOO', 'QQQI', 'QQQM', 'SCB', 'ICHI', 'MANU'],
        'Category': ['กองทุน 💰', 'กองทุน 💰', 'กองทุน 💰', 'กองทุน 💰', 'กองทุน 💰', 'ปันผล 🌀', 'ปันผล 🌀', 'ซิ่งจัด 😈'],
        'Value_THB': [7852.00, 6257.25, 5837.97, 5539.17, 5581.56, 4696.50, 1480.00, 313.79],
        'Profit_THB': [365.42, 247.86, 211.17, -11.10, 72.92, 355.57, 190.00, 65.31]
    }
    st.session_state.df = pd.DataFrame(default_data)

st.title("🚀 INVESTMENT DASHBOARD (GEMINI VISION - FREE)")
st.caption("AI วิเคราะห์รูปสลิป/หน้าจอ Dime! หลายรูปพร้อมกันด้วย Google Gemini (ใช้งานฟรี)")
st.divider()

# 2. แถบด้านข้าง (Sidebar)
with st.sidebar:
    st.header("⚙️ จัดการพอร์ตด้วย Gemini AI")
    
    api_key_from_secrets = st.secrets.get("GEMINI_API_KEY", "")
    
    if api_key_from_secrets:
        st.success("🔑 เชื่อมต่อ Gemini API Key แล้ว")
        user_key = api_key_from_secrets
    else:
        user_key = st.text_input("🔑 กรอก Gemini API Key:", type="password", help="วาง API Key ที่ได้จาก Google AI Studio")

    st.divider()
    
    st.subheader("📸 อัปโหลดรูปภาพหลายรูปพร้อมกัน")
    uploaded_files = st.file_uploader("เลือกรูปภาพสลิป/หน้าจอพอร์ต Dime!", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    st.divider()
    
    if uploaded_files:
        st.write(f"พบ {len(uploaded_files)} รูปภาพ...")
        
        def analyze_images_with_gemini(files, api_key):
            try:
                client = genai.Client(api_key=api_key.strip())
                
                images = [Image.open(file) for file in files]
                
                prompt = """
                วิเคราะห์รูปภาพสลิปหรือหน้าจอพอร์ต Dime! ทั้งหมดนี้ และดึงข้อมูลมูลค่ากับกำไร/ขาดทุนของสินทรัพย์แต่ละตัวออกมาเป็น JSON:
                1. Asset: ชื่อสินทรัพย์ (เช่น SP50001, NDX01, VOO, QQQI, QQQM, SCB, ICHI, MANU)
                2. Value_THB: มูลค่าปัจจุบัน (เป็นตัวเลข THB เท่านั้น)
                3. Profit_THB: กำไร/ขาดทุน (เป็นตัวเลข THB ถ้าขาดทุนให้ติดลบ)

                ส่งคืนผลลัพธ์เป็นโครงสร้าง JSON array แบบนี้เท่านั้น ห้ามมีข้อความอื่นปน:
                [
                  {"Asset": "SCB", "Value_THB": 4681.00, "Profit_THB": 340.07},
                  {"Asset": "ICHI", "Value_THB": 1470.00, "Profit_THB": 180.00}
                ]
                """
                
                contents = [prompt] + images
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=contents,
                )
                
                text = response.text
                json_start = text.find('[')
                json_end = text.rfind(']') + 1
                json_string = text[json_start:json_end]
                return json.loads(json_string)
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์ด้วย Gemini: {e}")
                return None

        if st.button("🧠 ให้ Gemini วิเคราะห์รูปภาพและอัปเดตพอร์ต"):
            if not user_key:
                st.warning("⚠️ กรุณากรอก Gemini API Key ด้านบนก่อนครับ")
            else:
                with st.spinner("กำลังให้ Gemini วิเคราะห์รูปภาพทั้งหมด (ฟรี)..."):
                    analysis_results = analyze_images_with_gemini(uploaded_files, user_key)
                    if analysis_results:
                        df_current = st.session_state.df
                        for result in analysis_results:
                            asset_name = result.get('Asset', '')
                            matched_rows = df_current[df_current['Asset'].str.upper() == asset_name.upper()]
                            if not matched_rows.empty:
                                row_index = matched_rows.index[0]
                                df_current.loc[row_index, 'Value_THB'] = float(result['Value_THB'])
                                df_current.loc[row_index, 'Profit_THB'] = float(result['Profit_THB'])
                        
                        st.session_state.df = df_current
                        st.success("อัปเดตตัวเลขตามรูปภาพเรียบร้อยแล้ว!")

    st.divider()
    
    st.subheader("✏️ แก้ไขยอดเงินเอง")
    edited_df = st.data_editor(
        st.session_state.df,
        column_config={
            "Value_THB": st.column_config.NumberColumn("มูลค่า (บาท)", format="฿%.2f"),
            "Profit_THB": st.column_config.NumberColumn("กำไร/ขาดทุน (บาท)", format="฿%.2f")
        },
        num_rows="dynamic"
    )
    st.session_state.df = edited_df

# 3. ส่วนแสดงผลหลัก
df = st.session_state.df.copy()
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
    col_img = st.columns(min(len(uploaded_files), 3))
    for i, file in enumerate(uploaded_files):
        with col_img[i % 3]:
            image = Image.open(file)
            st.image(image, caption=f"รูปที่ {i+1}")
    st.divider()

# 4. กราฟ
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 สัดส่วนพอร์ต (Donut Chart)")
    fig_pie = px.pie(df, values='Value_THB', names='Asset', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_traces(textinfo='percent+label')
    fig_pie.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_pie)

with c2:
    st.subheader("📈 ผลตอบแทน % รายสินทรัพย์")
    df['Color'] = df['Profit_Pct'].apply(lambda x: '#10B981' if x >= 0 else '#EF4444')
    fig_bar = px.bar(df, x='Asset', y='Profit_Pct', text_auto='.2f', color='Color', color_discrete_map="identity")
    fig_bar.update_layout(template="plotly_dark", yaxis_title="กำไร (%)", xaxis_title="")
    st.plotly_chart(fig_bar)
