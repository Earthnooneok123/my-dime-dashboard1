import json
from PIL import Image
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Investment Dashboard", layout="wide")

if "df" not in st.session_state:
  st.session_state.df = pd.DataFrame({
      "Asset": ["SP50001", "NDX01", "VOO", "SCB"],
      "Value_THB": [7852.00, 6257.25, 5837.97, 4696.50],
      "Profit_THB": [365.42, 247.86, 211.17, 355.57],
  })

st.title("🚀 INVESTMENT DASHBOARD")

with st.sidebar:
  st.header("⚙️ จัดการพอร์ต")
  user_key = st.text_input("🔑 กรอก Gemini API Key:", type="password")
  uploaded_files = st.file_uploader(
      "เลือกรูปภาพ", type=["jpg", "jpeg", "png"], accept_multiple_files=True
  )

  if uploaded_files and st.button("วิเคราะห์รูปภาพ"):
    if not user_key:
      st.warning("กรุณากรอก API Key")
    else:
      try:
        genai.configure(api_key=user_key.strip())
        # ดึงโมเดลอัตโนมัติจากบัญชีจริง ไม่ระบุชื่อแบบ Hardcode
        available_models = [
            m.name
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        model = genai.GenerativeModel(available_models[0])

        images = [Image.open(f) for f in uploaded_files]
        prompt = (
            "Extract Asset, Value_THB, Profit_THB as JSON array."
            ' Example: [{"Asset": "SCB", "Value_THB": 1000, "Profit_THB": 50}]'
        )
        res = model.generate_content([prompt] + images)

        text = res.text
        data = json.loads(text[text.find("[") : text.rfind("]") + 1])

        df_curr = st.session_state.df
        for r in data:
          m = df_curr[df_curr["Asset"].str.upper() == r["Asset"].upper()]
          if not m.empty:
            df_curr.loc[m.index[0], "Value_THB"] = float(r["Value_THB"])
            df_curr.loc[m.index[0], "Profit_THB"] = float(r["Profit_THB"])
        st.session_state.df = df_curr
        st.success("อัปเดตเรียบร้อย!")
      except Exception as e:
        st.error(f"Error: {e}")

df = st.session_state.df
st.dataframe(df)
st.plotly_chart(
    px.pie(df, values="Value_THB", names="Asset", title="สัดส่วนพอร์ต")
)
