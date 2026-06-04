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

# Đọc file SystemPromt.txt để lấy nội dung cấu hình hệ thống
with open("SystemPrompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

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
            # --- ĐÁP ỨNG TRỤC 1 & TRỤC 3 TẠI ĐÂY ---
            temperature=0.0,  # Hạ từ 0.2 xuống 0.0: Triệt tiêu hoàn toàn sự "sáng tạo" bậy bạ, AI sẽ cực kỳ nhất quán
             max_tokens=300    # Giới hạn từ để tránh AI bị lặp từ vô hạn (một dạng tấn công làm treo hệ thống)
        )
        
        bot_response = completion.choices[0].message.content
        return {
            "status": "success",
            "bot_response": bot_response
        }
        
    except Exception as e:
        print(f"[ERROR]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

# Hàm test tham số phụ 
def test_parameters(creative_level: bool = True):
    current_temperature = 1.2 if creative_level else 0.1
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Viết một câu slogan ngắn cho quán cà phê lập trình viên."}],
        temperature=current_temperature,
        max_tokens=50
    )
    return response.choices[0].message.content
