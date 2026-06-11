
# ============================================================
# THƯ VIỆN
# ============================================================
import os                       # Tương tác với hệ thống file
import json                     # Đọc/xử lý file JSON
import re                       # Biểu thức chính quy (regex)
import sys                      # Tương tác với hệ thống (sys.path)
from typing import List, Dict, Tuple, Optional    # Type hints
from collections import Counter # Đếm tần suất (dùng trong thống kê)
from fastapi import FastAPI, HTTPException        # Web framework
from fastapi.responses import HTMLResponse        # Trả HTML trang chủ
from fastapi.staticfiles import StaticFiles       # Phục vụ file tĩnh
from pydantic import BaseModel  # Validation dữ liệu đầu vào
from groq import Groq           # Client gọi API Groq
from dotenv import load_dotenv  # Đọc file .env


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 1: DIALECT MAPPING (dialect_map.py)              ║
# ║  Mục đích: Chuẩn hóa từ ngữ địa phương về tiếng Việt   ║
# ║  phổ thông trước khi gửi vào Groq LLM.                ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

# ---------- TỪ ĐIỂN PHƯƠNG NGỮ ----------
# key = từ địa phương, value = từ phổ thông tương ứng
DIALECT_MAP = {
    # ===== MIỀN TRUNG → Phổ thông =====
    # Đại từ / Từ để hỏi
    "mô": "đâu",               # "đi mô" → "đi đâu"
    "răng": "sao",             # "răng rứa" → "sao vậy"
    "rứa": "vậy",              # "răng rứa" → "sao vậy"
    "chi": "gì",               # "làm chi" → "làm gì"
    "tê": "kia",               # "mô tê" → "đâu kia"
    "đâu": "đâu",
    "ni": "này",               # "ni" → "này"
    "nớ": "kia",               # "nớ" → "kia"
    "rú": "núi",
    "ngoe": "vậy",
    "chừ": "giờ",              # "chừ" → "giờ"
    "bây chừ": "bây giờ",     # "bây chừ" → "bây giờ"
    "hè": "nhỉ",
    "hè à": "nhỉ",
    "chừng": "khoảng",

    # Danh từ
    "mạ": "mẹ",               # "mạ" → "mẹ"
    "u": "mẹ",
    "bầm": "mẹ",
    "mệ": "bà",
    "cha": "bố",
    "bọ": "bố",
    "thầy": "bố",
    "tía": "bố",
    "chén": "bát",             # Miền Trung gọi "chén" = bát
    "đọi": "bát",
    "tô": "bát",
    "ly": "cốc",
    "bông": "hoa",             # Miền Trung gọi "bông" = hoa
    "trái": "quả",             # "trái cây" → "quả"

    # Động từ / Tính từ
    "dạn": "dày",
    "nhác": "lười",
    "vô": "vào",               # "vô" → "vào"
    "lộn": "về",               # "lộn" → "về"
    "lẹ": "nhanh",             # "lẹ lên" → "nhanh lên"
    "lẹ lên": "nhanh lên",
    "tốc": "nhanh",

    # Miền Trung đặc trưng
    "trốc": "đầu",             # "trốc" → "đầu"
    "tróc": "đầu",
    "răng rứa": "sao vậy",
    "mô răng rứa": "đâu sao vậy",
    "chi rứa": "gì vậy",
    "mô tê": "đâu kia",
    "ràng": "sao",
    "hắn": "nó",               # "hắn" → "nó"
    "o": "cô",                 # "o" → "cô"
    "tui": "tôi",
    "tau": "tao",
    "mi": "mày",
    "mấy o": "mấy cô",
    "mụ": "bà (xưng hô)",
    "đàng": "đường",
    "mấy chế": "mấy cô",

    # ===== MIỀN NAM → Phổ thông =====
    # Đại từ / Từ để hỏi
    "hông": "không",           # "hông" → "không"
    "hổng": "không",
    "hổng có": "không có",
    "đâu có": "không có",
    "đâu hông": "không đâu",
    "hen": "nhé",              # "hen" → "nhé"
    "nghen": "nhé",
    "nha": "nhé",
    "ná": "nhé",
    "chớ": "chứ",
    "zậy": "vậy",
    "vậy đó": "vậy đó",

    # Danh từ
    "má": "mẹ",
    "ba": "bố",
    "ly": "cốc",
    "cái ly": "cái cốc",
    "muỗng": "thìa",
    "thau": "chậu",
    "thau nhôm": "chậu nhôm",
    "trái": "quả",
    "trái cây": "hoa quả",
    "trái thơm": "quả dứa",
    "thơm": "dứa",
    "bông": "hoa",
    "bông hồng": "hoa hồng",
    "bông mai": "hoa mai",
    "đậu phộng": "lạc",
    "đậu phụng": "lạc",
    "khoai mì": "sắn",
    "bắp": "ngô",
    "trái bắp": "ngô",
    "mè": "vừng",
    "nếp": "gạo nếp",
    "ghe": "thuyền",
    "cái bóp": "cái ví",
    "bóp": "ví",
    "cái nón": "cái mũ",
    "nón": "mũ",
    "cây viết": "bút",
    "viết": "bút",
    "cây bút": "bút",
    "cái cặp": "cặp sách",
    "cặp": "cặp sách",
    "hột gà": "trứng gà",
    "hột vịt": "trứng vịt",
    "hột": "trứng",
    "thịt heo": "thịt lợn",
    "heo": "lợn",

    # Động từ / Tính từ
    "dzô": "vào",              # "dzô" → "vào"
    "vô": "vào",
    "dzìa": "về",
    "dzô đi": "vào đi",
    "bự": "to",                # "bự" → "to"
    "nhỏ": "bé",
    "ổng": "ông ấy",           # "ổng" → "ông ấy"
    "ảnh": "anh ấy",
    "chỉ": "chị ấy",
    "bã": "bà ấy",
    "hổng thấy": "không thấy",
    "hổng biết": "không biết",
    "hổng hiểu": "không hiểu",
    "hổng có gì": "không có gì",
    "hông có": "không có",
    "được hông": "được không",
    "đi hông": "đi không",
    "coi": "xem",
    "coi chừng": "cẩn thận",
    "coi bộ": "có vẻ",
    "nhức đầu": "đau đầu",
    "mắc cỡ": "ngượng",

    # Giao tiếp
    "dạ": "dạ",
    "vâng": "vâng",
    "dza": "dạ",
    "thưa": "thưa",
    "kêu": "gọi",
    "biểu": "bảo",
    "cám ơn": "cảm ơn",

    # Từ lóng / đặc trưng
    "sạo": "giả tạo",
    "xạo": "nói dối",
    "xạo ke": "nói dối",
    "đểu": "xấu tính",
    "dữ": "quá",
    "dữ thần": "quá trời",

    # Từ viết tắt / lóng từ điện thoại
    "otp": "mã OTP",
    "cọc": "tiền cọc",
    "chuyển khoản": "chuyển khoản",
    "ck": "chuyển khoản",
    "stk": "số tài khoản",
    "tk": "tài khoản",
    "qr": "mã QR",
    "qr code": "mã QR",
    "link": "đường dẫn",
}

# ---------- CỤM TỪ ĐẶC TRƯNG VÙNG MIỀN ----------
# Xử lý các cụm từ dài trước để tránh bị ghi đè bởi từ đơn
PHRASE_MAP = {
    # Miền Trung
    "mô răng rứa": "đâu sao vậy",
    "chi rứa": "gì vậy",
    "răng mà nói rứa": "sao mà nói vậy",
    "đi mô đó": "đi đâu đó",
    "về mô": "về đâu",
    "nhà mô": "nhà nào",
    "ai rứa": "ai vậy",
    "làm chi": "làm gì",
    "làm răng": "làm sao",
    "nói chi": "nói gì",
    "đi mô chơi": "đi đâu chơi",

    # Miền Nam
    "tui hổng biết": "tôi không biết",
    "tui hổng có": "tôi không có",
    "ổng nói vậy đó": "ông ấy nói vậy đó",
    "ảnh đi rồi": "anh ấy đi rồi",
    "chỉ nói vậy thôi": "chị ấy nói vậy thôi",
    "hông có gì đâu": "không có gì đâu",
}


def word_boundary_replace(text: str, old: str, new: str) -> str:
    """
    Thay thế từ có word boundary để tránh match substring.
    Ví dụ: "mô" không match vào "cơm", chỉ match "mô" đứng riêng.
    
    --- Args:
    text : str : Văn bản gốc
    old  : str : Từ cần thay thế
    new  : str : Từ thay thế

    --- Returns:
    str : Văn bản đã thay thế
    """
    # pattern: từ phải đứng ở đầu chuỗi hoặc sau ký tự phân cách, và kết thúc bởi ký tự phân cách
    pattern = re.compile(
        r'(^|[\s,.;:!?\"\'()\[\]{}])' + re.escape(old) + r'($|[\s,.;:!?\"\'()\[\]{}])',
        re.IGNORECASE
    )
    # Thay thế nhưng giữ lại ký tự phân cách ở đầu và cuối
    result = pattern.sub(r'\1' + new + r'\2', text)
    return result


def normalize_dialect(text: str) -> str:
    """
    Chuẩn hóa văn bản từ phương ngữ về tiếng Việt phổ thông.
    Áp dụng theo thứ tự: phrase → word (từ dài → ngắn) để tránh ghi đè sai.

    --- Args:
    text : str : Câu nói của người dùng (có thể chứa từ địa phương)

    --- Returns:
    str : Câu đã chuẩn hóa về phổ thông
    """
    normalized = text.strip()  # Bỏ khoảng trắng đầu/cuối

    # Bước 1: Chuẩn hóa khoảng trắng
    normalized = re.sub(r'\s+', ' ', normalized)  # Nén nhiều khoảng trắng thành 1
    normalized = normalized.lower()                # Đưa về chữ thường để dễ so khớp

    # Bước 2: Xử lý cụm từ dài trước (phrase map)
    for phrase in sorted(PHRASE_MAP.keys(), key=len, reverse=True):
        # Sắp xếp từ dài nhất trước để "mô răng rứa" được xử lý trước "mô"
        replacement = PHRASE_MAP[phrase]
        normalized = word_boundary_replace(normalized, phrase, replacement)

    # Bước 3: Xử lý từ đơn (DIALECT_MAP)
    sorted_words = sorted(
        [word for word in DIALECT_MAP if word],  # Lấy danh sách từ cần thay thế
        key=len,
        reverse=True  # Từ dài trước, từ ngắn sau
    )
    for word in sorted_words:
        normalized = word_boundary_replace(normalized, word, DIALECT_MAP[word])

    # Bước 4: Nén khoảng trắng thừa (xuất hiện sau khi thay thế)
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    # Bước 5: Viết hoa chữ cái đầu câu
    if normalized:
        normalized = normalized[0].upper() + normalized[1:]

    return normalized


def detect_region(text: str) -> str:
    """
    Phát hiện vùng miền qua cách nói (heuristic).
    
    --- Args:
    text : str : Câu nói của người dùng

    --- Returns:
    str : "north" | "central" | "south" | "unknown"
    """
    text_lower = text.lower()

    # Đặc trưng miền Trung: "mô", "răng", "rứa", "chi rứa", "mạ ơi", ...
    central_markers = ["mô", "răng", "rứa", "chi rứa", "mạ ơi",
                       "đi mô", "về mô", "làm chi", "o ơi"]
    central_score = sum(1 for m in central_markers if m in text_lower)

    # Đặc trưng miền Nam: "hổng", "hông", "chỉ ơi", "má ơi", "ổng", ...
    south_markers = ["hổng", "hông", "chỉ ơi", "má ơi", "ba ơi",
                     "dzô", "vô đây", "coi chừng", "mắc cỡ", "ổng", "ảnh",
                     "thơm", "bông", "chén", "trái cây"]
    south_score = sum(1 for m in south_markers if m in text_lower)

    # Đặc trưng miền Bắc: "bố ơi", "mẹ ơi", "bát", "cốc", ...
    north_markers = ["bố ơi", "mẹ ơi", "bát", "bố", "mẹ", "cốc",
                     "đâu", "sao", "gì", "thế nào", "quả"]
    north_score = sum(1 for m in north_markers if m in text_lower)

    # Tạo danh sách điểm số và sắp xếp giảm dần
    scores = [
        ("central", central_score),
        ("south", south_score),
        ("north", north_score),
    ]
    scores.sort(key=lambda x: x[1], reverse=True)

    # Trả về vùng miền có điểm cao nhất, hoặc "unknown" nếu không có marker nào
    if scores[0][1] > 0:
        return scores[0][0]
    return "unknown"


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 2: RAG ENGINE (rag_engine.py)                    ║
# ║  Mục đích: Chunk dữ liệu JSON, tính relevance score,   ║
# ║  chỉ lấy top-K chunks liên quan nhất.                  ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

class RAGChunk:
    """
    Một chunk dữ liệu - đại diện cho một kịch bản lừa đảo.
    Chứa hội thoại, file nguồn, loại lừa đảo và các từ khóa.
    """
    def __init__(self, id: int, dialogue: List[Dict], source_file: str, fraud_type: str):
        """
        --- Args:
        id          : int          : ID của chunk
        dialogue    : List[Dict]   : Mảng các đoạn hội thoại [{role, content}, ...]
        source_file : str          : Tên file JSON nguồn
        fraud_type  : str          : Loại lừa đảo (tên thư mục cha)
        """
        self.id = id                        # ID định danh chunk
        self.dialogue = dialogue            # Mảng hội thoại gốc
        self.source_file = source_file      # File nguồn
        self.fraud_type = fraud_type        # Loại lừa đảo
        self.full_text = self._build_full_text()    # Text đầy đủ từ dialogue
        self.keywords = self._extract_keywords()    # Tập từ khóa lừa đảo trong chunk

    def _build_full_text(self) -> str:
        """
        Xây dựng text đầy đủ từ mảng dialogue (dạng [role]: content).
        
        --- Returns:
        str : Toàn bộ hội thoại dạng text
        """
        lines = []
        for turn in self.dialogue:
            role = turn.get("role", "unknown")       # Vai trò người nói
            content = turn.get("content", "")         # Nội dung lời thoại
            lines.append(f"[{role}]: {content}")     # Gộp lại
        return "\n".join(lines)

    def _extract_keywords(self) -> set:
        """
        Trích xuất từ khóa lừa đảo xuất hiện trong dialogue.
        So khớp với danh sách scam_keywords định nghĩa sẵn.

        --- Returns:
        set : Tập các từ khóa lừa đảo tìm được
        """
        text = self.full_text.lower()  # Đưa về chữ thường

        # Danh sách từ khóa lừa đảo phổ biến
        scam_keywords = {
            "chuyển khoản", "chuyển tiền", "cọc", "đặt cọc", "otp",
            "mã otp", "mật khẩu", "pin", "tài khoản", "số tài khoản",
            "stk", "link", "bấm vào", "cài ứng dụng", "ứng dụng",
            "công an", "toà án", "viện kiểm sát", "ngân hàng",
            "bắt giữ", "đe dọa", "khóa tài khoản", "nhận thưởng",
            "trúng thưởng", "quà tặng", "lợi nhuận", "đầu tư",
            "tiền ảo", "cccd", "căn cước", "định danh",
            "tuyển sinh", "tuyển dụng", "từ thiện", "quyên góp",
            "hoàn tiền", "chuyển lại", "phí xác thực", "phí ưu tiên",
            "tài khoản cá nhân", "bảo trì hệ thống", "hệ thống đang lỗi"
        }
        words = set(re.findall(r'\b\w+\b', text))      # Tách từ
        return words & scam_keywords  # Giao giữa từ trong text và từ khóa


class RAGEngine:
    """
    RAG Engine với chunking + relevance scoring.
    Cách hoạt động:
      1. Đọc tất cả file JSON từ Data_Kich_Ban/
      2. Chia mỗi kịch bản thành một chunk riêng
      3. Khi có câu hỏi, tính relevance score cho từng chunk
      4. Chỉ lấy top-K chunks liên quan nhất (tránh nhiễu)
    """
    def __init__(self, data_folder: Optional[str] = None):
        """
        --- Args:
        data_folder : str (optional) : Đường dẫn đến thư mục chứa dữ liệu JSON
        """
        self.chunks: List[RAGChunk] = []           # Danh sách tất cả chunks
        self.data_folder = data_folder or self._find_data_folder()
        self._load_data()  # Tự động load dữ liệu khi khởi tạo

    def _find_data_folder(self) -> str:
        """
        Tự động phát hiện thư mục chứa dữ liệu.
        Thử các tên: Data_Kich_Ban, data_kich_ban, ...
        
        --- Returns:
        str : Đường dẫn thư mục dữ liệu
        """
        possible_names = ["Data_Kich_Ban", "data_kich_ban", "Data_Kich_Ban/"]
        for name in possible_names:
            if os.path.exists(name) and os.path.isdir(name):
                return name

        # Fallback: tìm bất kỳ thư mục nào có chứa "kich_ban" hoặc "data"
        for item in os.listdir("."):
            if os.path.isdir(item) and ("kich_ban" in item.lower() or "data" in item.lower()):
                return item
        return "Data_Kich_Ban"  # Mặc định

    def _load_data(self):
        """
        Đọc tất cả file JSON từ thư mục dữ liệu và tạo chunks.
        Duyệt đệ quy tất cả thư mục con.
        """
        if not os.path.exists(self.data_folder):
            print(f"[RAG Engine] Warning: Folder '{self.data_folder}' not found.")
            return

        file_count = 0    # Đếm số file JSON
        chunk_count = 0   # Đếm số chunk tạo được

        for root, dirs, files in os.walk(self.data_folder):  # Duyệt đệ quy
            for file in files:
                if file.endswith(".json"):     # Chỉ xử lý file JSON
                    filepath = os.path.join(root, file)
                    fraud_type = os.path.basename(root)  # Tên thư mục = loại lừa đảo

                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data_list = json.load(f)  # Load JSON

                        for kich_ban in data_list:
                            kich_ban_id = kich_ban.get("_id", chunk_count + 1)
                            dialogue = kich_ban.get("dialogue", [])

                            if dialogue:  # Chỉ tạo chunk nếu có hội thoại
                                chunk = RAGChunk(
                                    id=kich_ban_id,
                                    dialogue=dialogue,
                                    source_file=file,
                                    fraud_type=fraud_type
                                )
                                self.chunks.append(chunk)
                                chunk_count += 1
                        file_count += 1

                    except Exception as e:
                        print(f"[RAG Engine] Lỗi đọc {file}: {e}")

        print(f"[RAG Engine] Loaded {file_count} files, {chunk_count} chunks")

    def calculate_relevance(self, query: str, chunk: RAGChunk) -> float:
        """
        Tính điểm relevance giữa câu hỏi user và chunk.
        Scoring factors:
          1. Fraud keyword match: Từ khóa lừa đảo trong query
          2. Word overlap: Từ trong query xuất hiện trong chunk

        --- Args:
        query : str      : Câu hỏi của người dùng
        chunk : RAGChunk : Chunk dữ liệu cần so sánh

        --- Returns:
        float : Điểm relevance (0.0 → 1.0)
        """
        if not query or not chunk:
            return 0.0

        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))  # Tách từ trong query

        # Factor 1: Từ khóa lừa đảo trong query (fraud_score)
        fraud_match = 0
        for kw in chunk.keywords:
            if kw in query_lower:      # Từ khóa lừa đảo xuất hiện trong query
                fraud_match += 1

        # Factor 2: Các từ trong query xuất hiện trong chunk (word overlap)
        chunk_text_lower = chunk.full_text.lower()
        query_word_match = sum(
            1 for word in query_words
            if len(word) > 2 and word in chunk_text_lower  # Bỏ từ ngắn (1-2 ký tự)
        )

        # Chuẩn hóa điểm
        query_word_score = query_word_match / max(len(query_words), 1)  # Tỷ lệ match
        fraud_score = fraud_match / max(len(chunk.keywords), 1) * 0.5   # *0.5 để giảm trọng số

        # Tổng hợp: 60% word overlap + 40% fraud keyword
        total_score = query_word_score * 0.6 + fraud_score * 0.4
        return total_score

    def retrieve(self, query: str, top_k: int = 5, min_score: float = 0.05) -> Tuple[List[RAGChunk], str]:
        """
        Retrieve top-K chunks liên quan nhất.

        --- Args:
        query    : str   : Câu hỏi của người dùng
        top_k    : int   : Số chunk muốn lấy (mặc định: 5)
        min_score: float : Ngưỡng relevance tối thiểu (lọc nhiễu)

        --- Returns:
        (relevant_chunks : List[RAGChunk], context_string : str)
        """
        if not self.chunks:
            return [], "Chưa có dữ liệu tra cứu."

        # Tính score cho tất cả chunks
        scored_chunks: List[Tuple[float, RAGChunk]] = []
        for chunk in self.chunks:
            score = self.calculate_relevance(query, chunk)
            if score >= min_score:  # Lọc chunk có điểm dưới ngưỡng
                scored_chunks.append((score, chunk))

        # Sắp xếp giảm dần theo score và lấy top-K
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for _, chunk in scored_chunks[:top_k]]

        # Nếu không có chunk nào đủ điểm
        if not top_chunks:
            return [], "Không tìm thấy kịch bản nào liên quan đến câu hỏi của ông/bà."

        # Xây dựng context string từ các chunks
        context_parts = []
        for i, chunk in enumerate(top_chunks, 1):
            context_parts.append(
                f"[KỊCH BẢN {i} - {chunk.fraud_type}]\n"
                f"{chunk.full_text}\n"
            )
        context_string = "\n---\n".join(context_parts)

        return top_chunks, context_string

    def get_statistics(self) -> Dict:
        """
        Lấy thống kê dữ liệu RAG.

        --- Returns:
        Dict: { "total_chunks": int, "fraud_types": Dict[str, int], "data_folder": str }
        """
        fraud_types = Counter()
        for chunk in self.chunks:
            fraud_types[chunk.fraud_type] += 1  # Đếm số chunk theo từng loại lừa đảo

        return {
            "total_chunks": len(self.chunks),
            "fraud_types": dict(fraud_types),
            "data_folder": self.data_folder,
        }


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 3: HALLUCINATION GUARD (hallucination_guard.py)  ║
# ║  Mục đích: Kiểm tra response của Groq có bị "ảo giác"  ║
# ║  (hallucination) hay không bằng cách so với RAG context.║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

# Những từ "đóng mở" không mang thông tin (cần loại bỏ khi trích claims)
STOP_WORDS = {
    "dạ", "vâng", "ạ", "à", "ơi", "nhé", "nha", "nghen",
    "thì", "là", "và", "của", "có", "được", "sẽ", "đã",
    "đang", "cũng", "rất", "lắm", "quá", "nhỉ", "nhưng",
    "hoặc", "hay", "nếu", "vì", "nên", "mà", "bị", "đây",
    "đó", "kia", "này", "vậy", "thế", "nào", "sao", "gì",
    "cả", "những", "các", "mọi", "mỗi", "một", "như",
}


class HallucinationGuard:
    """
    Layer kiểm tra hallucination sau khi Groq trả response.
    
    Cơ chế:
      1. Trích xuất các "claim" (thông tin khẳng định) từ response.
      2. Tính grounding score = % claims được hỗ trợ bởi context RAG.
      3. Nếu score thấp → response có thể bị hallucination → fallback.
      4. Log các trường hợp hallucination để debug.
    """
    def __init__(self, threshold: float = 0.25):
        """
        --- Args:
        threshold : float : Ngưỡng grounding score tối thiểu (0.0 - 1.0).
                           Thấp = cho phép nhiều (dễ bị hallucination)
                           Cao = an toàn hơn (nhưng dễ false positive)
        """
        self.threshold = threshold   # Ngưỡng phát hiện hallucination
        self.log: List[dict] = []    # Log lịch sử các lần kiểm tra

    def _extract_claims(self, text: str) -> set:
        """
        Trích xuất các "claim" (thông tin khẳng định) từ text.
        Claim = danh từ, số, tên riêng, hành động cụ thể.

        --- Args:
        text : str : Văn bản cần trích xuất

        --- Returns:
        set : Tập các claims
        """
        text_lower = text.lower()

        # Từ có độ dài > 2, không phải stop word
        words = set(re.findall(r'\b\w{3,}\b', text_lower))
        claims = words - STOP_WORDS

        # Thêm số (ví dụ: "2.5 triệu", "500 nghìn", ...)
        numbers = set(re.findall(
            r'\d+(?:[.,]\d+)*(?:\s*(?:triệu|nghìn|đồng|ngàn|trăm|tỷ))?',
            text_lower
        ))

        # Thêm entity: từ viết hoa (tên người, tổ chức)
        entities = set(re.findall(
            r'\b[AÀẢÃÁẠĂẰẮẶẲẴÂẤẦẨẪẬBCDĐEÈÉẺẼẸÊỀẾỂỄỆFGHIÌÍỈĨỊJKLMNÒÓỎÕỌÔỒỐỔỖỘƠỚỜỞỠỢPQRSTUÙÚỦŨỤƯỪỨỬỮỰVWXYÝỲỶỸỴZ][a-zàảãáạăằắặẳẵâấầẩẫậbcdđeèéẻẽẹêềếểễệfghiìíỉĩịjklmnoòóỏõọôồốổỗộơớờởỡợpqrstuùúủũụưừứửữựvwxyýỳỷỹỵz]+',
            text
        ))

        # Hợp tất cả các loại claims
        all_claims = claims | set(numbers) | set(entities)
        return all_claims

    def _calculate_grounding_score(self, context: str, response: str) -> Tuple[float, set, set]:
        """
        Tính grounding score = tỷ lệ claims trong response có xuất hiện trong context.

        --- Args:
        context  : str : Context RAG
        response : str : Response từ Groq

        --- Returns:
        (score : float, supported : set, unsupported : set)
        """
        if not response or not context:
            return 0.0, set(), set()

        response_claims = self._extract_claims(response)   # Lấy claims từ response
        context_lower = context.lower()

        supported = set()     # Claims được hỗ trợ (có trong context)
        unsupported = set()   # Claims không có trong context

        for claim in response_claims:
            if claim in context_lower:
                # Claim xuất hiện trực tiếp trong context
                supported.add(claim)
            else:
                # Kiểm tra fuzzy: claim có thể là một phần của từ trong context
                # Ví dụ: "chuyển" là một phần của "chuyển khoản"
                found = False
                for word in re.findall(r'\b\w+\b', context_lower):
                    if claim in word or word in claim:
                        found = True
                        supported.add(claim)
                        break
                if not found:
                    unsupported.add(claim)

        total = len(response_claims)
        if total == 0:
            return 1.0, set(), set()  # Không có claim = không hallucination

        score = len(supported) / max(total, 1)  # Tỷ lệ claims được hỗ trợ
        return score, supported, unsupported

    def _check_unsafe_patterns(self, response: str) -> bool:
        """
        Kiểm tra các pattern nguy hiểm trong response.
        Ví dụ: "Tôi khuyên bạn nên chuyển tiền" (ngược với nhiệm vụ).

        --- Args:
        response : str : Response từ Groq

        --- Returns:
        bool : True nếu phát hiện pattern nguy hiểm
        """
        response_lower = response.lower()

        # Các pattern nguy hiểm (không bao giờ được phép xuất hiện)
        unsafe_patterns = [
            "chuyển tiền ngay",
            "cung cấp otp",
            "cung cấp mật khẩu",
            "bấm vào link",
            "cài ứng dụng",
        ]

        for pattern in unsafe_patterns:
            if pattern in response_lower:
                # Chỉ đánh dấu nếu đây là lời khuyên (có từ "nên", "hãy", "phải")
                if any(kw in response_lower for kw in ["nên", "hãy", "phải"]):
                    return True
        return False

    def validate(self, context: str, response: str, user_query: str = "") -> Tuple[bool, str, float]:
        """
        Validate response có bị hallucination không.

        --- Args:
        context    : str : Context RAG
        response   : str : Response từ Groq
        user_query : str : Câu hỏi gốc của user (optional, dùng cho logging)

        --- Returns:
        (is_safe : bool, final_response : str, grounding_score : float)
        """
        # Tính grounding score
        score, supported, unsupported = self._calculate_grounding_score(
            context or "", response or ""
        )

        # Kiểm tra unsafe pattern
        has_unsafe = self._check_unsafe_patterns(response)

        # Ghi log
        log_entry = {
            "user_query": user_query,
            "response": response,
            "supported_claims": list(supported)[:10],
            "unsupported_claims": list(unsupported)[:10],
            "grounding_score": score,
            "threshold": self.threshold,
            "has_unsafe_pattern": has_unsafe,
        }
        self.log.append(log_entry)

        # Quyết định: nếu có pattern nguy hiểm → block ngay lập tức
        if has_unsafe:
            return False, "", 0.0

        # Nếu quá nhiều unsupported claims → hallucination
        if score < self.threshold:
            max_unsupported = 2  # Chỉ cho phép tối đa 2 claim không được support
            if len(unsupported) > max_unsupported:
                return False, "", score

        # Response an toàn
        return True, response, score

    def get_hallucination_rate(self) -> float:
        """
        Tính tỷ lệ hallucination từ lịch sử log.

        --- Returns:
        float : Tỷ lệ hallucination (0.0 → 1.0)
        """
        if not self.log:
            return 0.0
        hallucinated = sum(
            1 for entry in self.log
            if entry.get("grounding_score", 1.0) < entry.get("threshold", 0.25)
        )
        return hallucinated / len(self.log)


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 4: FASTAPI SERVER (improved_main.py)             ║
# ║  Mục đích: Định nghĩa các API endpoint, khởi tạo hệ    ║
# ║  thống và pipeline xử lý.                              ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

# ---------- KHỞI TẠO ----------
load_dotenv()   # Đọc file .env để lấy GROQ_API_KEY

# Tạo ứng dụng FastAPI
app = FastAPI(title="Anti-Scam Chatbot - Improved")

# Kiểm tra API key từ biến môi trường
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("[WARNING] GROQ_API_KEY not found in .env file")
    client = None  # Không có API key → không thể gọi Groq
else:
    client = Groq(api_key=GROQ_API_KEY)  # Khởi tạo client Groq

# Đọc System Prompt (đã hợp nhất từ SystemPrompt.txt và SystemPrompt_updated.txt)
SYSTEM_PROMPT_PATH = "SystemPrompt.txt"

with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()  # Nội dung system prompt

# Khởi tạo RAG Engine (đọc tất cả dữ liệu JSON vào bộ nhớ)
print("[INIT] Loading RAG Engine...")
rag_engine = RAGEngine()

# Khởi tạo Hallucination Guard với ngưỡng 0.2
hallucination_guard = HallucinationGuard(threshold=0.2)


# ---------- MODEL DỮ LIỆU ----------
class ChatInput(BaseModel):
    """Model validation cho dữ liệu đầu vào từ client"""
    messages: List[Dict[str, str]]  # Mảng các tin nhắn [{role, content}, ...]


# ---------- API ENDPOINTS ----------
@app.get("/", response_class=HTMLResponse)
def get_home():
    """
    Endpoint trang chủ.
    Phục vụ file index.html từ thư mục templates/.
    """
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html = f.read()
            # Tự động inject phiên bản vào title
            html = html.replace(
                "Trợ Lý Phòng Chống Lừa Đảo",
                "Trợ Lý Phòng Chống Lừa Đảo (v2)"
            )
            return html
    except FileNotFoundError:
        return HTMLResponse(
            content="<h3>Vui lòng tạo thư mục 'templates' và đặt file 'index.html' vào trong.</h3>",
            status_code=404
        )


@app.get("/health")
def health_check():
    """
    Endpoint kiểm tra sức khỏe hệ thống.
    Trả về trạng thái của các thành phần.
    """
    stats = rag_engine.get_statistics()
    return {
        "status": "ok",
        "model_available": client is not None,    # Groq có khả dụng không?
        "rag_stats": {
            "total_chunks": stats["total_chunks"],        # Tổng số chunks
            "fraud_types": stats["fraud_types"],           # Các loại lừa đảo
        },
        "hallucination_rate": hallucination_guard.get_hallucination_rate(),
        "system_prompt": SYSTEM_PROMPT_PATH,
    }


@app.post("/chat")
def chat(data: ChatInput):
    """
    API CHÍNH - Xử lý tin nhắn từ người dùng.
    
    Pipeline xử lý 7 bước:
      1. Nhận message từ user
      2. Dialect normalization (Bắc-Trung-Nam → phổ thông)
      3. RAG retrieval (chunked + relevance scored)
      4. Build prompt với context
      5. Call Groq LLM (llama-3.1-8b-instant)
      6. Hallucination validation
      7. Trả response an toàn
    """
    if not client:
        raise HTTPException(
            status_code=500,
            detail="API key chưa được cấu hình."
        )

    try:
        # === BƯỚC 1: Lấy message mới nhất từ người dùng ===
        if not data.messages:
            raise HTTPException(status_code=400, detail="Không có tin nhắn.")

        user_message = data.messages[-1].get("content", "")  # Message cuối cùng
        if not user_message.strip():
            raise HTTPException(status_code=400, detail="Tin nhắn trống.")

        # === BƯỚC 2: DIALECT NORMALIZATION ===
        # Phát hiện vùng miền (cho mục đích debug/log)
        detected_region = detect_region(user_message)

        # Chuẩn hóa từ địa phương về phổ thông
        normalized_message = normalize_dialect(user_message)

        print(f"[CHAT] Region: {detected_region}")
        print(f"[CHAT] Original: {user_message[:100]}...")
        print(f"[CHAT] Normalized: {normalized_message[:100]}...")

        # === BƯỚC 3: RAG RETRIEVAL ===
        # Chỉ lấy top 3 chunks liên quan nhất (không dump toàn bộ dữ liệu)
        relevant_chunks, context_string = rag_engine.retrieve(
            query=normalized_message,
            top_k=3,
            min_score=0.05
        )

        print(f"[CHAT] RAG retrieved: {len(relevant_chunks)} chunks")

        # === BƯỚC 4: BUILD PROMPT ===
        # Tạo message chứa RAG context để gửi kèm câu hỏi người dùng
        rag_system_message = f"""
--- KHO DỮ LIỆU TRA CỨU ---
{context_string if context_string else "Không có dữ liệu phù hợp."}
-----------------------------

Câu hỏi của người dùng: {normalized_message}

Hướng dẫn:
- Chỉ trả lời dựa trên dữ liệu TRA CỨU ở trên và thông tin người dùng cung cấp.
- Nếu dữ liệu TRA CỨU không liên quan, hãy dựa vào kiến thức của bạn.
- Nếu không đủ thông tin để kết luận, hãy nói chưa đủ căn cứ.
"""
        # Xây dựng message history (giữ nguyên lịch sử chat)
        processed_messages = data.messages.copy()

        # Thay thế message cuối cùng bằng message đã normalize + RAG context
        processed_messages[-1]["content"] = rag_system_message

        # Build payload cho Groq (System Prompt đứng đầu)
        groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        groq_messages.extend(processed_messages)

        # === BƯỚC 5: CALL GROQ LLM ===
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # Model Groq
            messages=groq_messages,          # Messages payload
            temperature=0.1,                 # Nhiệt độ thấp = ít sáng tạo, ít hallucination
            max_tokens=300,                  # Giới hạn độ dài response
            frequency_penalty=0.3,           # Giảm lặp từ
            presence_penalty=0.1,            # Giảm lặp chủ đề
        )

        bot_response = completion.choices[0].message.content  # Response từ Groq

        # === BƯỚC 6: HALLUCINATION VALIDATION ===
        if relevant_chunks:
            # Kiểm tra response có dựa trên context RAG không
            is_safe, validated_response, grounding_score = hallucination_guard.validate(
                context=context_string,
                response=bot_response,
                user_query=normalized_message
            )

            print(f"[CHAT] Grounding score: {grounding_score:.2f}")

            if not is_safe:
                # Hallucination detected - sử dụng fallback response an toàn
                print(f"[HALLUCINATION] Detected! Score: {grounding_score:.2f}")
                print(f"[HALLUCINATION] Original: {bot_response[:100]}...")

                # Fallback responses an toàn (không chứa thông tin sai lệch)
                fallback_responses = [
                    "Dạ ông/bà ơi, cháu đã xem xét câu chuyện của ông/bà. "
                    "Dựa trên thông tin ông/bà cung cấp, cháu thấy có dấu hiệu đáng ngờ. "
                    "Tốt nhất ông/bà nên trao đổi với người thân trước khi làm theo họ nhé ạ.",

                    "Dạ cháu xin lỗi ông/bà, cháu chưa phân tích được tình huống này. "
                    "Ông/bà có thể kể rõ hơn cho cháu được không ạ?",
                ]

                if not relevant_chunks:  # Nếu RAG không có dữ liệu liên quan
                    bot_response = fallback_responses[1]
                else:  # Nếu có dữ liệu nhưng response bị hallucination
                    bot_response = fallback_responses[0]
        else:
            # Không có dữ liệu RAG → giữ nguyên response (system prompt đã guard)
            pass

        # === BƯỚC 7: TRẢ RESPONSE VỀ CLIENT ===
        return {
            "status": "success",
            "bot_response": bot_response,
            "debug": {
                "detected_region": detected_region,
                "normalized_message": normalized_message,
                "chunks_found": len(relevant_chunks),
            }
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions (không bọc lại)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Dạ hệ thống của cháu đang bận, ông/bà thử lại sau nhé ạ!"
        )


# ---------- PHỤC VỤ FILE TĨNH ----------
# Mount thư mục templates để phục vụ CSS/JS (nếu có)
if os.path.exists("templates"):
    app.mount("/static", StaticFiles(directory="templates"), name="static")


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  PHẦN 5: KIỂM TRA (test_improvements.py)               ║
# ║  Mục đích: Chạy kiểm tra toàn bộ module khi gọi        ║
# ║  `python main.py` trực tiếp.                           ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================

def run_tests():
    """
    Hàm kiểm tra toàn bộ hệ thống.
    Chạy khi gọi `python main.py` trực tiếp (không qua uvicorn).
    """
    print("=" * 70)
    print("TESTING ALL MODULES")
    print("=" * 70)

    # ---------- TEST 1: DIALECT MAP ----------
    print("\n" + "=" * 70)
    print("📝 TEST 1: DIALECT MAP")
    print("=" * 70)

    try:
        test_cases = [
            # (input_text, expected_region)
            ("Mô răng rứa?", "central"),
            ("Chi rứa? Đi mô đó?", "central"),
            ("Mạ ơi, nhà mô đây?", "central"),
            ("Má ơi, hổng có gì đâu", "south"),
            ("Ổng nói vậy đó, tui hổng biết", "south"),
            ("Mẹ ơi, bát cơm đây ạ", "north"),
            ("Tôi thấy cái bát này bự quá", "unknown"),
        ]

        for text, expected_region in test_cases:
            region = detect_region(text)
            normalized = normalize_dialect(text)
            status = "✅" if region == expected_region else "⚠"
            print(f"\n{status} Gốc: {text}")
            print(f"   Vùng: {region} (expected: {expected_region})")
            print(f"   Chuẩn: {normalized}")

        print("\n✅ Dialect Map: OK")
    except Exception as e:
        print(f"❌ Dialect Map Error: {e}")

    # ---------- TEST 2: RAG ENGINE ----------
    print("\n" + "=" * 70)
    print("📚 TEST 2: RAG ENGINE")
    print("=" * 70)

    try:
        test_engine = RAGEngine()
        stats = test_engine.get_statistics()

        print(f"\n📊 Thống kê:")
        print(f"   Total chunks: {stats['total_chunks']}")
        for ftype, count in stats['fraud_types'].items():
            print(f"   - {ftype}: {count}")

        test_queries = [
            "Có người yêu cầu tôi chuyển tiền đặt cọc nhà hàng",
            "Họ bảo tôi cung cấp mã OTP",
            "Tôi muốn hỏi về thời tiết hôm nay",  # Không liên quan
        ]

        for q in test_queries:
            chunks, ctx = test_engine.retrieve(q, top_k=2)
            print(f"\n🔍 '{q[:50]}...'")
            print(f"   Relevant chunks: {len(chunks)}")
            if chunks:
                print(f"   Context length: {len(ctx)} chars")

        print("\n✅ RAG Engine: OK")
    except Exception as e:
        print(f"❌ RAG Engine Error: {e}")

    # ---------- TEST 3: HALLUCINATION GUARD ----------
    print("\n" + "=" * 70)
    print("🛡️  TEST 3: HALLUCINATION GUARD")
    print("=" * 70)

    try:
        test_guard = HallucinationGuard(threshold=0.25)

        context = """
        [KỊCH BẢN - Lừa đảo đặt bàn ăn]
        [người gọi]: Em là Minh, chị chuyển tiền cọc 2 triệu rưỡi vào tài khoản cá nhân em nhé.
        [người nhận]: Ừ, để tôi chuyển.
        """

        test_responses = [
            # An toàn: dựa trên context
            "Dạ ông/bà ơi, đây có dấu hiệu lừa đảo. Họ yêu cầu chuyển tiền cọc vào tài khoản cá nhân.",
            # Hallucination: số tiền và chi tiết không có trong context
            "Dạ ông/bà ơi, đây là lừa đảo. Họ yêu cầu chuyển 15 triệu và cung cấp mã OTP từ Vietcombank.",
            # An toàn: không kết luận
            "Dạ ông/bà kể cháu nghe rõ hơn nhé, cháu chưa đủ thông tin để kết luận ạ.",
        ]

        for i, resp in enumerate(test_responses):
            is_safe, final, score = test_guard.validate(context, resp, "test query")
            status = "✅" if is_safe else "❌ HALLUCINATION"
            print(f"\n{status} Response {i+1}: {resp[:60]}...")
            print(f"   Grounding score: {score:.2f}")

        print("\n✅ Hallucination Guard: OK")
    except Exception as e:
        print(f"❌ Hallucination Guard Error: {e}")

    # ---------- KẾT THÚC ----------
    print("\n" + "=" * 70)
    print("🏁 ALL TESTS COMPLETE")
    print("=" * 70)


# ============================================================
# ╔══════════════════════════════════════════════════════════╗
# ║  MAIN ENTRY POINT                                       ║
# ║                                                        ║
# ║  Cách chạy:                                            ║
# ║    python main.py           → Chạy server              ║
# ║    python main.py --test    → Chạy kiểm tra (Phần 5)   ║
# ║    uvicorn main:app --reload → Chạy server             ║
# ╚══════════════════════════════════════════════════════════╝
# ============================================================
if __name__ == "__main__":
    """
    Entry point:
      python main.py           → Chạy FastAPI server
      python main.py --test    → Chạy test (không cần API key, không cần server)
      uvicorn main:app --reload → Chạy FastAPI server
    """
    # Kiểm tra tham số dòng lệnh: nếu có "--test" thì chạy test
    if "--test" in sys.argv:
        run_tests()
        sys.exit(0)

    # Nếu không có "--test" → chạy server
    import uvicorn

    print("=" * 60)
    print("ANTI-SCAM CHATBOT - IMPROVED VERSION")
    print("=" * 60)

    # Hiển thị thông tin hệ thống
    print("\n📊 System Status:")
    stats = rag_engine.get_statistics()
    print(f"   RAG: {stats['total_chunks']} chunks loaded")
    if stats['fraud_types']:
        for ftype, count in stats['fraud_types'].items():
            print(f"     - {ftype}: {count}")
    print(f"   Model: Groq (llama-3.1-8b-instant)")
    print(f"   Hallucination Guard: Active (threshold=0.2)")
    print(f"   Dialect Normalization: Active")
    print(f"\n🚀 Server running at: http://localhost:8000")
    print("=" * 60)

    # Chạy server
    uvicorn.run(app, host="0.0.0.0", port=8000)
