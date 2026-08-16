import json
import re
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from PIL import Image
import streamlit as st

# ตั้งค่าหน้าตา App
st.set_page_config(
    page_title="Personal Investment Dashboard",
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

# 1. ข้อมูลเริ่มต้น (Default Portfolio Data)
INITIAL_DATA = [
    {
        "Asset": "SP50001",
        "Type": "US Equity",
        "Value_THB": 7852.00,
        "Cost_THB": 7486.58,
        "Profit_THB": 365.42,
        "Return_Pct": 4.88,
    },
    {
        "Asset": "NDX01",
        "Type": "US Tech",
        "Value_THB": 6257.25,
        "Cost_THB": 6009.39,
        "Profit_THB": 247.86,
        "Return_Pct": 4.12,
    },
    {
        "Asset": "VOO",
        "Type": "US Equity",
        "Value_THB": 5837.97,
        "Cost_THB": 5626.80,
        "Profit_THB": 211.17,
        "Return_Pct": 3.75,
    },
    {
        "Asset": "SCB",
        "Type": "Thai Equity",
        "Value_THB": 4696.50,
        "Cost_THB": 4340.93,
        "Profit_THB": 355.57,
        "Return_Pct": 8.19,
    },
]

# Initialize Session State
if "portfolio_df" not in st.session_state:
  st.session_state.portfolio_df = pd.DataFrame(INITIAL_DATA)


# Helper Function: คำนวณเปอร์เซ็นต์กำไร/ขาดทุน
def recalculate_df(df):
  df["Cost_THB"] = df["Value_THB"] - df["Profit_THB"]
  df["Return_Pct"] = (df["Profit_THB"] / df["Cost_THB"].replace(0, 1)) * 100
  return df


# ---------------- Sidebar ----------------
with st.sidebar:
  st.title("⚙️ ตั้งค่า & อัปเดต")

  api_key = st.text_input(
      "🔑 กรอก Gemini API Key:",
      type="password",
      help="รับ API Key ได้ฟรีจาก Google AI Studio",
  )

  st.divider()
  st.subheader("📸 อัปเดตพอร์ตด้วยรูปภาพ")
  uploaded_files = st.file_uploader(
      "อัปโหลดแคปหน้าจอพอร์ต (รองรับหลายรูป):",
      type=["png", "jpg", "jpeg"],
      accept_multiple_files=True,
  )

  if uploaded_files:
    st.info(f"พบ {len(uploaded_files)} รูปภาพ...")

    if st.button("🧠 ให้ Gemini วิเคราะห์รูปภาพและอัปเดตพอร์ต"):
      if not api_key:
        st.error("กรุณากรอก Gemini API Key ในช่องด้านบนก่อนครับ")
      else:
        with st.spinner("กำลังวิเคราะห์รูปภาพด้วย AI..."):
          try:
            genai.configure(api_key=api_key.strip())

            # ค้นหาโมเดล Gemini ที่รองรับอัตโนมัติ เพื่อป้องกันปัญหา 404
            models = [
                m.name
                for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]

            # เลือกโมเดลที่เหมาะสมที่สุด
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

            # โหลดรูปภาพทั้งหมด
            images = [Image.open(file) for file in uploaded_files]

            prompt = """
                        คุณคือผู้ช่วยวิเคราะห์พอร์ตการลงทุน โปรดสกัดข้อมูลสินทรัพย์จากภาพถ่ายหน้าจอพอร์ตการลงทุนนี้
                        ส่งคืนผลลัพธ์เป็น JSON Array เท่านั้น โดยไม่ต้องมีคำอธิบายเพิ่มเติม รูปแบบดังนี้:
                        [
                          {
                            "Asset": "ชื่อสินทรัพย์ หรือ ตัวย่อหุ้น/กองทุน",
                            "Value_THB": มูลค่ารวมปัจจุบันเป็นตัวเลข float,
                            "Profit_THB": กำไรหรือขาดทุนรวมเป็นตัวเลข float (ถ้าขาดทุนให้ติดลบ)
                          }
                        ]
                        """

            response = model.generate_content([prompt] + images)
            response_text = response.text

            # แกะข้อมูล JSON จาก Text Response
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
              extracted_data = json.loads(json_match.group(0))

              # อัปเดตเข้า Session State
              curr_df = st.session_state.portfolio_df.copy()

              for item in extracted_data:
                asset_name = str(item.get("Asset", "")).strip()
                val = float(item.get("Value_THB", 0))
                profit = float(item.get("Profit_THB", 0))

                # Match ชื่อ Asset
                match_idx = curr_df[
                    curr_df["Asset"].str.upper() == asset_name.upper()
                ].index

                if not match_idx.empty:
                  curr_df.loc[match_idx[0], "Value_THB"] = val
                  curr_df.loc[match_idx[0], "Profit_THB"] = profit
                else:
                  # เพิ่มรายการใหม่หากไม่เคยมีในตาราง
                  new_row = {
                      "Asset": asset_name,
                      "Type": "Other",
                      "Value_THB": val,
                      "Cost_THB": val - profit,
                      "Profit_THB": profit,
                      "Return_Pct": 0,
                  }
                  curr_df = pd.concat(
                      [curr_df, pd.DataFrame([new_row])], ignore_index=True
                  )

              st.session_state.portfolio_df = recalculate_df(curr_df)
              st.success("✨ อัปเดตข้อมูลพอร์ตจากรูปภาพเรียบร้อยแล้ว!")
              st.rerun()
            else:
              st.error(
                  "ไม่สามารถแปลงข้อมูลจากรูปภาพเป็นรูปแบบ JSON ได้"
                  " กรุณาลองใหม่อีกครั้ง"
              )

          except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์ด้วย Gemini: {e}")

  st.divider()
  if st.button("🔄 รีเซ็ตข้อมูลกลับค่าเริ่มต้น"):
    st.session_state.portfolio_df = pd.DataFrame(INITIAL_DATA)
    st.rerun()

# ---------------- Main Dashboard ----------------
st.title("📈 Personal Investment Dashboard")
st.caption("แดชบอร์ดสรุปภาพรวมพอร์ตการลงทุนและการเติบโต")

df = st.session_state.portfolio_df

# คำนวณสรุปผลภาพรวม
total_value = df["Value_THB"].sum()
total_profit = df["Profit_THB"].sum()
total_cost = total_value - total_profit
total_return_pct = (
    (total_profit / total_cost * 100) if total_cost > 0 else 0.0
)

# 1. Key Metrics Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(label="มูลค่าพอร์ตรวม (บาท)", value=f"฿{total_value:,.2f}")
with col2:
  st.metric(label="ต้นทุนรวม (บาท)", value=f"฿{total_cost:,.2f}")
with col3:
  st.metric(
      label="กำไร/ขาดทุน รวม (บาท)",
      value=f"฿{total_profit:,.2f}",
      delta=f"{total_profit:,.2f} บาท",
  )
with col4:
  st.metric(
      label="ผลตอบแทนรวม (%)",
      value=f"{total_return_pct:.2f}%",
      delta=f"{total_return_pct:.2f}%",
  )

st.divider()

# 2. Charts Section
c1, c2 = st.columns(2)

with c1:
  st.subheader("📊 สัดส่วนสินทรัพย์ (Asset Allocation)")
  fig_pie = px.pie(
      df,
      values="Value_THB",
      names="Asset",
      hole=0.4,
      color_discrete_sequence=px.colors.qualitative.Pastel,
  )
  fig_pie.update_traces(textposition="inside", textinfo="percent+label")
  fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
  st.plotly_chart(fig_pie, use_container_width=True)

with c2:
  st.subheader("💵 กำไร/ขาดทุน รายสินทรัพย์ (THB)")
  df_sorted = df.sort_values(by="Profit_THB", ascending=True)
  fig_bar = px.bar(
      df_sorted,
      x="Profit_THB",
      y="Asset",
      orientation="h",
      color="Profit_THB",
      color_continuous_scale=["#ef553b", "#00cc96"],
      text_auto=".2f",
  )
  fig_bar.update_layout(
      margin=dict(t=20, b=20, l=20, r=20), coloraxis_showscale=False
  )
  st.plotly_chart(fig_bar, use_container_width=True)

# 3. Editable Data Table
st.subheader("📋 รายละเอียดพอร์ตการลงทุน (แก้ไขข้อมูลได้)")
st.caption(
    "💡 คุณสามารถดับเบิลคลิกที่ช่องตัวเลขในตารางเพื่อแก้ไขมูลค่าพอร์ตได้โดยตรง"
)

edited_df = st.data_editor(
    df,
    column_config={
        "Asset": st.column_config.TextColumn("สินทรัพย์/หุ้น", disabled=False),
        "Type": st.column_config.TextColumn("ประเภท"),
        "Value_THB": st.column_config.NumberColumn(
            "มูลค่าปัจจุบัน (บาท)", format="฿%.2f"
        ),
        "Cost_THB": st.column_config.NumberColumn(
            "ต้นทุน (บาท)", format="฿%.2f"
        ),
        "Profit_THB": st.column_config.NumberColumn(
            "กำไร/ขาดทุน (บาท)", format="฿%.2f"
        ),
        "Return_Pct": st.column_config.NumberColumn(
            "ผลตอบแทน (%)", format="%.2f%%"
        ),
    },
    use_container_width=True,
    num_rows="dynamic",
)

# ถ้ารายการในตารางมีการแก้ไข ให้คำนวณและอัปเดต Session State ใหม่
if not edited_df.equals(df):
  updated_df = recalculate_df(edited_df)
  st.session_state.portfolio_df = updated_df
  st.rerun()
