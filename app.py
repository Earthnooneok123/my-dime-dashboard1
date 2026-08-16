import json
import re
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from PIL import Image
import streamlit as st

# ตั้งค่าหน้าตา App
st.set_page_config(
    page_title="Investment Dashboard (Gemini Powered)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS เพื่อความสวยงาม
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: bold; }
    .stButton>button { width: 100%; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)

# 1. ข้อมูลเริ่มต้นสินทรัพย์ทั้ง 8 ตัวครบถ้วน
INITIAL_DATA = [
    {
        "Asset": "SP50001",
        "Category": "กองทุน 💰",
        "Value_THB": 7852.00,
        "Profit_THB": 365.42,
    },
    {
        "Asset": "NDX01",
        "Category": "กองทุน 💰",
        "Value_THB": 6257.25,
        "Profit_THB": 247.86,
    },
    {
        "Asset": "VOO",
        "Category": "กองทุน 💰",
        "Value_THB": 5837.97,
        "Profit_THB": 211.17,
    },
    {
        "Asset": "QQQI",
        "Category": "กองทุน 💰",
        "Value_THB": 5539.17,
        "Profit_THB": -11.10,
    },
    {
        "Asset": "QQQM",
        "Category": "กองทุน 💰",
        "Value_THB": 5581.56,
        "Profit_THB": 72.92,
    },
    {
        "Asset": "SCB",
        "Category": "ปันผล 🌀",
        "Value_THB": 4696.50,
        "Profit_THB": 355.57,
    },
    {
        "Asset": "ICHI",
        "Category": "ปันผล 🌀",
        "Value_THB": 1480.00,
        "Profit_THB": 190.00,
    },
    {
        "Asset": "MANU",
        "Category": "ซิ่งจัด 😈",
        "Value_THB": 313.79,
        "Profit_THB": 65.31,
    },
]

# Initialize Session State
if "df" not in st.session_state:
  st.session_state.df = pd.DataFrame(INITIAL_DATA)

# ---------------- Sidebar ----------------
with st.sidebar:
  st.title("⚙️ จัดการพอร์ตด้วย Gemini AI")

  api_key_from_secrets = st.secrets.get("GEMINI_API_KEY", "")

  if api_key_from_secrets:
    st.success("🔑 เชื่อมต่อ Gemini API Key แล้ว")
    user_key = api_key_from_secrets
  else:
    user_key = st.text_input(
        "🔑 กรอก Gemini API Key:",
        type="password",
        help="วาง API Key ที่ได้จาก Google AI Studio",
    )

  st.divider()
  st.subheader("📸 อัปโหลดรูปภาพหลายรูปพร้อมกัน")
  uploaded_files = st.file_uploader(
      "เลือกรูปภาพสลิป/หน้าจอพอร์ต Dime!",
      type=["png", "jpg", "jpeg"],
      accept_multiple_files=True,
  )

  if uploaded_files:
    st.info(f"พบ {len(uploaded_files)} รูปภาพ...")

    if st.button("🧠 ให้ Gemini วิเคราะห์รูปภาพและอัปเดตพอร์ต"):
      if not user_key:
        st.warning("⚠️ กรุณากรอก Gemini API Key ด้านบนก่อนครับ")
      else:
        with st.spinner("กำลังให้ Gemini วิเคราะห์รูปภาพทั้งหมด..."):
          try:
            genai.configure(api_key=user_key.strip())

            # ค้นหาโมเดลที่ใช้งานได้อัตโนมัติจาก API Key
            models = [
                m.name
                for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]

            selected_model_name = None
            for target in [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro-vision",
            ]:
              matched = [m for m in models if target in m]
              if matched:
                selected_model_name = matched[0]
                break

            if not selected_model_name:
              selected_model_name = models[0] if models else "gemini-1.5-flash"

            model = genai.GenerativeModel(selected_model_name)
            images = [Image.open(file) for file in uploaded_files]

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

            response = model.generate_content([prompt] + images)
            response_text = response.text

            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
              analysis_results = json.loads(json_match.group(0))
              df_current = st.session_state.df.copy()

              for result in analysis_results:
                asset_name = str(result.get("Asset", "")).strip()
                matched_rows = df_current[
                    df_current["Asset"].str.upper() == asset_name.upper()
                ]

                if not matched_rows.empty:
                  row_index = matched_rows.index[0]
                  df_current.loc[row_index, "Value_THB"] = float(
                      result["Value_THB"]
                  )
                  df_current.loc[row_index, "Profit_THB"] = float(
                      result["Profit_THB"]
                  )
                else:
                  new_row = {
                      "Asset": asset_name,
                      "Category": "อื่นๆ 📦",
                      "Value_THB": float(result["Value_THB"]),
                      "Profit_THB": float(result["Profit_THB"]),
                  }
                  df_current = pd.concat(
                      [df_current, pd.DataFrame([new_row])], ignore_index=True
                  )

              st.session_state.df = df_current
              st.success("อัปเดตตัวเลขตามรูปภาพเรียบร้อยแล้ว!")
              st.rerun()
            else:
              st.error("ไม่สามารถแกะข้อมูล JSON จากรูปภาพได้ ลองใหม่อีกครั้ง")

          except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์ด้วย Gemini: {e}")

  st.divider()

  st.subheader("✏️ แก้ไขยอดเงินเอง")
  edited_df = st.data_editor(
      st.session_state.df,
      column_config={
          "Asset": st.column_config.TextColumn("สินทรัพย์"),
          "Category": st.column_config.TextColumn("หมวดหมู่"),
          "Value_THB": st.column_config.NumberColumn(
              "มูลค่า (บาท)", format="฿%.2f"
          ),
          "Profit_THB": st.column_config.NumberColumn(
              "กำไร/ขาดทุน (บาท)", format="฿%.2f"
          ),
      },
      num_rows="dynamic",
  )
  st.session_state.df = edited_df

# ---------------- Main Dashboard ----------------
st.title("🚀 INVESTMENT DASHBOARD (GEMINI VISION - FREE)")
st.caption(
    "AI วิเคราะห์รูปสลิป/หน้าจอ Dime! หลายรูปพร้อมกันด้วย Google Gemini"
    " (ใช้งานฟรี)"
)
st.divider()

df = st.session_state.df.copy()
df["Profit_Pct"] = (
    df["Profit_THB"] / (df["Value_THB"] - df["Profit_THB"])
) * 100

total_value = df["Value_THB"].sum()
total_profit = df["Profit_THB"].sum()
total_cost = total_value - total_profit
total_return = (total_profit / total_cost) * 100 if total_cost != 0 else 0

# Summary Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("มูลค่าพอร์ตรวม", f"฿{total_value:,.2f}")
col2.metric("เงินต้นรวม", f"฿{total_cost:,.2f}")
col3.metric("กำไร/ขาดทุนรวม", f"฿{total_profit:,.2f}", f"{total_return:.2f}%")
col4.metric("บรรยากาศพอร์ต", "🟢 เขียวขจี" if total_profit > 0 else "🔴 แดงเดือด")

st.divider()

# Charts
c1, c2 = st.columns(2)

with c1:
  st.subheader("📊 สัดส่วนพอร์ต (Donut Chart)")
  fig_pie = px.pie(
      df,
      values="Value_THB",
      names="Asset",
      hole=0.4,
      color_discrete_sequence=px.colors.qualitative.Pastel,
  )
  fig_pie.update_traces(textinfo="percent+label")
  fig_pie.update_layout(showlegend=False)
  st.plotly_chart(fig_pie, use_container_width=True)

with c2:
  st.subheader("📈 ผลตอบแทน % รายสินทรัพย์")
  df["Color"] = df["Profit_Pct"].apply(
      lambda x: "#10B981" if x >= 0 else "#EF4444"
  )
  fig_bar = px.bar(
      df,
      x="Asset",
      y="Profit_Pct",
      text_auto=".2f",
      color="Color",
      color_discrete_map="identity",
  )
  fig_bar.update_layout(yaxis_title="กำไร (%)", xaxis_title="")
  st.plotly_chart(fig_bar, use_container_width=True)
