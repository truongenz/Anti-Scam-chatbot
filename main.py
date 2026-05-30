import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict
from groq import Groq
from dotenv import load_dotenv

# Khởi tạo cấu hình hệ thống lên đầu tiên
load_dotenv()
app = FastAPI()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Định nghĩa dữ liệu đầu vào từ giao diện HTML
class ChatInput(BaseModel):
    messages: List[Dict[str, str]]

# KHO DỮ LIỆU RAG (Được đưa lên làm biến toàn cục để AI truy cập)
KHO_DU_LIEU_LUA_DAO = """
1. KỊCH BẢN GIẢ DANH CÔNG AN/VIỆN KIỂM SÁT:
   - Dấu hiệu: Gọi điện thông báo số tài khoản, số điện thoại của nạn nhân liên quan đến vụ án ma túy, rửa tiền. Yêu cầu chuyển tiền vào "tài khoản an toàn" hoặc tải app lạ.
   - Lời khuyên: Cơ quan công an không bao giờ làm việc qua điện thoại. Tuyệt đối không chuyển tiền.

2. KỊCH BẢN GIẢ DANH NHÂN VIÊN Y TẾ ("CON ĐANG CẤP CỨU"):
   - Dấu hiệu: Gọi điện thông báo con/cháu bị tai nạn nguy kịch, yêu cầu chuyển tiền gấp đóng viện phí.
   - Lời khuyên: Giữ bình tĩnh, tắt máy và gọi ngay cho con/cháu để xác minh.

3. KỊCH BẢN TRÚNG THƯỞNG/QUÀ TẶNG MIỄN PHÍ:
   - Dấu hiệu: Thông báo trúng thưởng lớn, yêu cầu đóng "phí vận chuyển" hoặc "thuế" trước.
   - Lời khuyên: Không gửi tiền, không cung cấp thông tin cá nhân.

4. KỊCH BẢN GIẢ DANH NHÂN VIÊN ĐIỆN LỰC/VIỄN THÔNG:
   - Dấu hiệu: Dọa khóa sim sau 2 tiếng, dọa cắt điện, yêu cầu bấm vào link hoặc cung cấp mã OTP.
   - Lời khuyên: Tắt máy, gọi lên tổng đài chính thức để kiểm tra.
"""

# SYSTEM PROMPT: Định hình phong cách ngắn gọn, lễ phép
SYSTEM_PROMPT = """Bạn là một người cháu hiếu thảo, am hiểu công nghệ. Nhiệm vụ của bạn là tư vấn phòng chống lừa đảo cho các ông bà, cô bác lớn tuổi.

YÊU CẦU BẮT BUỘC VỀ PHONG CÁCH TRẢ LỜI:
1. Luôn xưng hô lễ phép (Dạ, vâng, ông/bà, cô/bác, cháu/con).
2. TRẢ LỜI CỰC KỲ NGẮN GỌN, dùng từ ngữ dễ hiểu với người già. Không giải thích dông dài.
3. CẤU TRÚC PHẢN HỒI LUÔN GỒM 2 PHẦN RÕ RÀNG (BẮT BUỘC XUỐNG DÒNG THEO KHUÔN MẪU):
   - Phần 1: Khẳng định đanh thép tình huống đó CÓ PHẢI LỪA ĐẢO HAY KHÔNG.
   - Phần 2: Danh sách các việc CẦN LÀM NGAY BÂY GIỜ (Dùng các số 1, 2, 3 để chia nhỏ hành động).

HÃY BẮT CHƯỚC CHÍNH XÁC KHUÔN MẪU (FORMAT) SAU ĐÂY:
Dạ ông/bà ơi, tình huống ông/bà vừa kể CHẮC CHẮN LÀ LỪA ĐẢO 100% ạ! Kẻ xấu đang giả danh công an để dọa dẫm và bắt ông/bà chuyển tiền đấy ạ.

MẤY ĐIỀU ÔNG BÀ CẦN LÀM NGAY BÂY GIỜ:
1. Ông/bà hãy CÚP MÁY NGAY LẬP TỨC, không nghe họ nói nữa ạ.
2. Tuyệt đối không chuyển bất kỳ đồng tiền nào, cũng không bấm vào đường link lạ nhé ạ.
3. Ông/bà bình tĩnh rồi gọi ngay cho con cháu hoặc ra công an phường gần nhất để báo cáo nha!"""

@app.get("/", response_class=HTMLResponse)
def get_home():
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="<h3>Vui lòng tạo thư mục 'templates' và đặt file 'index.html' vào trong.</h3>", status_code=404)

# HÀM API CHÍNH: Đã tích hợp RAG + Lịch sử hội thoại
@app.post("/chat")
def chat(data: ChatInput):
    try:
        # Bước 1: Lấy tin nhắn mới nhất mà người dùng vừa nhập
        user_newest_message = data.messages[-1]["content"] if data.messages else ""
        
        # Bước 2: Trộn kho kiến thức RAG vào tin nhắn cuối cùng này để bắt AI đối chiếu
        prompt_rag = f"""--- KHO DỮ LIỆU LỪA ĐẢO ĐỂ ĐỐI CHIẾU ---
{KHO_DU_LIEU_LUA_DAO}
----------------------------------------
Lời kể của ông/bà: {user_newest_message}"""

        # Sao chép lại lịch sử chat cũ từ giao diện gửi lên
        processed_messages = data.messages.copy()
        # Thay thế tin nhắn cuối cùng bằng tin nhắn đã được "nhúng" kho dữ liệu RAG
        if processed_messages:
            processed_messages[-1]["content"] = prompt_rag

        # Bước 3: Tạo payload hoàn chỉnh gửi lên Groq (System Prompt đứng đầu)
        groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        groq_messages.extend(processed_messages)

        # Bước 4: Gọi API sinh câu trả lời
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  
            messages=groq_messages,
            temperature=0.2, # Chỉnh thấp xuống 0.2 để AI trả lời nghiêm túc, bám sát kho dữ liệu lừa đảo
        )
        
        bot_response = completion.choices[0].message.content
        return {
            "status": "success",
            "bot_response": bot_response
        }
        
    except Exception as e:
        print(f"[ERROR]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

# Hàm test tham số phụ (Để bạn giữ lại test ngoài luồng nếu muốn)
def test_parameters(creative_level: bool = True):
    current_temperature = 1.2 if creative_level else 0.1
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Viết một câu slogan ngắn cho quán cà phê lập trình viên."}],
        temperature=current_temperature,
        max_tokens=50
    )
    return response.choices[0].message.content