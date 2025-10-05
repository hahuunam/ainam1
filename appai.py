import streamlit as st
import openai
import os
from PyPDF2 import PdfReader
import docx

# ------------------- Cấu hình -------------------
st.set_page_config(page_title="AI Hỗ trợ Ngữ Văn", page_icon="📚", layout="wide")
st.title("📚 AI Hỗ trợ Dạy & Học Ngữ Văn")

openai.api_key = os.getenv("OPENAI_API_KEY")

# ------------------- Hàm tiện ích -------------------
def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def read_docx(file):
    doc = docx.Document(file)
    text = "\n".join([p.text for p in doc.paragraphs])
    return text

# ------------------- Quản lý quyền Admin -------------------
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

st.sidebar.title("🔐 Quản lý")
admin_tab = st.sidebar.radio("Chọn chế độ:", ["Người dùng", "Admin"])

if admin_tab == "Admin":
    password = st.sidebar.text_input("Nhập mật khẩu admin:", type="password")
    if st.sidebar.button("Đăng nhập"):
        if password == "12345":  # 🔒 đổi mật khẩu tùy ý
            st.session_state.is_admin = True
            st.sidebar.success("✅ Đăng nhập thành công!")
        else:
            st.sidebar.error("❌ Sai mật khẩu!")

if admin_tab == "Người dùng":
    st.session_state.is_admin = False

# ------------------- Bộ nhớ tài liệu -------------------
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {}

# ------------------- Giao diện -------------------
col1, col2 = st.columns([1.2, 1])

# --------- CỘT PHẢI: Quản lý tài liệu (chỉ hiển thị cho Admin) ---------
with col2:
    if st.session_state.is_admin:
        st.subheader("📂 Tài liệu (PDF, DOCX, TXT)")

        uploaded_file = st.file_uploader("Tải lên tài liệu mới", type=["pdf", "docx", "txt"])
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                text = read_pdf(uploaded_file)
            elif uploaded_file.type in [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"
            ]:
                text = read_docx(uploaded_file)
            else:
                text = uploaded_file.read().decode("utf-8", errors="ignore")

            st.session_state.uploaded_docs[uploaded_file.name] = text
            st.success(f"✅ Đã tải lên: {uploaded_file.name}")

        if st.session_state.uploaded_docs:
            st.subheader("📘 Danh sách tài liệu")
            doc_name = st.selectbox("Chọn tài liệu để xem:", list(st.session_state.uploaded_docs.keys()))
            st.text_area("📖 Nội dung", value=st.session_state.uploaded_docs[doc_name][:4000], height=300)
        else:
            st.info("📭 Chưa có tài liệu nào được tải lên.")
    else:
        st.info("👤 Bạn đang ở chế độ người dùng. Chỉ Admin mới xem và tải tài liệu.")

# --------- CỘT TRÁI: Hỏi đáp dựa trên tài liệu ---------
with col1:
    st.subheader("📝 Đặt câu hỏi (AI chỉ trả lời nếu có trong tài liệu)")
    question = st.text_area("Nhập câu hỏi:", height=100)

    api_key_input = st.text_input("🔑 Nhập OpenAI API Key (nếu chưa set trong môi trường)", type="password")
    if api_key_input:
        openai.api_key = api_key_input

    if st.button("💡 Hỏi AI"):
        if not question.strip():
            st.warning("❗ Vui lòng nhập câu hỏi trước.")
        elif not st.session_state.uploaded_docs:
            st.warning("📭 Hiện chưa có tài liệu nào. Hãy để admin tải lên trước.")
        else:
            with st.spinner("🤖 AI đang đọc tài liệu và trả lời..."):
                context = "\n\n".join([v for v in st.session_state.uploaded_docs.values()])
                context = context[:6000]

                prompt = f"""
                Bạn là trợ lý AI chỉ được phép trả lời dựa trên thông tin có trong tài liệu dưới đây.
                Nếu câu hỏi không liên quan hoặc không có trong tài liệu, hãy trả lời chính xác: 
                "Câu hỏi không có trong tài liệu."

                --- TÀI LIỆU ---
                {context}
                -----------------

                Câu hỏi: {question}
                """

                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Bạn là trợ lý AI đọc hiểu tài liệu Ngữ văn Việt Nam."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=800
                )
                answer = response.choices[0].message.content.strip()
                st.session_state.answer = answer

    st.subheader("📖 Câu trả lời từ AI")
    st.text_area("Kết quả:", value=st.session_state.get("answer", ""), height=300)
