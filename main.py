import os
import json
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

# SYSTEM PROMPT: Định hình phong cách ngắn gọn, lễ phép
SYSTEM_PROMPT = """Bạn là một người cháu hiếu thảo, am hiểu công nghệ. Nhiệm vụ của bạn là lắng nghe và tư vấn phòng chống lừa đảo cho các ông bà, cô bác lớn tuổi.

YÊU CẦU BẮT BUỘC VỀ PHONG CÁCH TRẢ LỜI:
1. Luôn xưng hô lễ phép (Dạ, vâng, ông/bà, cô/bác, cháu/con).
2. TRẢ LỜI CỰC KỲ NGẮN GỌN, dễ hiểu với người già. Không giải thích dông dài.

TƯ DUY XỬ LÝ THEO TÌNH HUỐNG (QUAN TRỌNG - KHÔNG ĐƯỢC RẬP KHUÔN):
- TRƯỜNG HỢP 1: Nếu người dùng CHỈ CHÀO HỎI (Ví dụ: "Alo", "Chào cháu").
  -> Chào lại ngắn gọn và hỏi ông bà đang gặp chuyện gì. 
  (Ví dụ: "Dạ cháu nghe đây ạ! Ông/bà đang gặp chuyện gì lo lắng đúng không ạ? Ông/bà kể cho cháu nghe xem sao nhé ạ.")

- TRƯỜNG HỢP 2: Nếu câu kể của người dùng QUÁ NGẮN, MƠ HỒ, CHƯA RÕ ĐẦU ĐUÔI (Ví dụ: "có một số gọi cho tôi", "gọi cho tôi rồi bảo", "tôi nhận được tin nhắn").
  -> TUYỆT ĐỐI KHÔNG được kết luận lừa đảo ngay. Hãy lịch sự, nhẹ nhàng bảo ông bà kể tiếp xem đầu dây bên kia nói gì hoặc bắt làm gì thì mới biết được.
  (Ví dụ: "Dạ ông/bà ơi, số lạ gọi đến thì chưa hẳn là lừa đảo đâu ạ. Ông/bà kể tiếp cho cháu nghe xem họ nói gì, họ có đòi tiền hay bảo ông bà làm gì không ạ?")

- TRƯỜNG HỢP 3: Khi người dùng ĐÃ KỂ RÕ TÌNH HUỐNG có dấu hiệu trùng khớp hoặc nghi ngờ dựa trên kho dữ liệu (Ví dụ: đòi OTP, dọa công an, đòi tiền viện phí).
  -> Áp dụng cấu trúc 2 phần rõ ràng và xuống dòng như khuôn mẫu dưới đây:

  Dạ ông/bà ơi, tình huống ông/bà vừa kể CHẮC CHẮN LÀ LỪA ĐẢO [Tỷ lệ]% ạ! [Giải thích siêu ngắn gọn lý do lừa đảo dựa trên kho dữ liệu đối chiếu].

  MẤY ĐIỀU ÔNG BÀ CẦN LÀM NGAY BÂY GIỜ:
  1. Ông/bà hãy CÚP MÁY NGAY LẬP TỨC (hoặc XÓA APP/TẮT MÁY tùy tình huống), không nghe họ nói nữa ạ.
  2. Tuyệt đối không chuyển bất kỳ đồng tiền nào, cũng không bấm vào đường link lạ hay đưa mã số gì nhé ạ.
  3. Ông/bà bình tĩnh rồi gọi ngay cho con cháu hoặc ra cơ quan chức năng gần nhất để báo cáo nha!"""

# Giả sử tên Folder 
FOLDER_CHINH = "Data_Kich_Ban"

def doc_tat_ca_file_json_tu_folder():
    chuoi_kien_thuc = ""
    dem_kich_ban = 1
    
    # Giả sử folder chứa các kịch bản hội thoại này tên là "data_kich_ban"
    if not os.path.exists("data_kich_ban"):
        return "Chưa có dữ liệu kịch bản lừa đảo."

    for root, dirs, files in os.walk("data_kich_ban"):
        for file in files:
            if file.endswith(".json"):
                duong_dan_file = os.path.join(root, file)
                try:
                    with open(duong_dan_file, "r", encoding="utf-8") as f:
                        data_list = json.load(f)
                        
                        # Duyệt qua từng kịch bản lớn trong file JSON
                        for kich_ban in data_list:
                            chuoi_kien_thuc += f"--- VÍ DỤ THỰC TẾ SỐ {dem_kich_ban} ---\n"
                            
                            # Trích xuất mảng "dialogue" (đoạn hội thoại)
                            cac_cau_thoai = kich_ban.get("dialogue", [])
                            for thoai in cac_cau_thoai:
                                vai_tro = thoai.get("role", "Chưa rõ")
                                noi_dung = thoai.get("content", "")
                                # Gộp vai trò và nội dung lời thoại lại
                                chuoi_kien_thuc += f"+ {vai_tro}: {noi_dung}\n"
                            
                            chuoi_kien_thuc += "\n"
                            dem_kich_ban += 1
                            
                except Exception as e:
                    print(f"Lỗi khi đọc file {file}: {str(e)}")
                    continue
                    
    return chuoi_kien_thuc
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
{doc_tat_ca_file_json_tu_folder}
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