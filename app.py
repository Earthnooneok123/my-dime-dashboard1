def analyze_images_with_gemini(files, api_key):
    try:
        # ใช้ Client จาก google-genai
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
        
        # เรียกผ่าน Interactions API ตามมาตรฐานใหม่
        response = client.interactions.create(
            model='gemini-2.5-flash',
            input=[prompt] + images
        )
        
        text = response.text
        json_start = text.find('[')
        json_end = text.rfind(']') + 1
        json_string = text[json_start:json_end]
        return json.loads(json_string)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการวิเคราะห์ด้วย Gemini: {e}")
        return None
