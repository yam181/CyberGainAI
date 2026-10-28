
import streamlit as st
from groq import Groq
from supabase import create_client

st.set_page_config(
    page_title="CyberGain AI",
    page_icon="🛡️",
    layout="centered"
)

st.markdown("""
<style>
html, body, [data-testid="stApp"] {
    direction: rtl;
    text-align: right;
}
.stMarkdown, .stText, label, p {
    text-align: right;
}
[data-testid="stChatMessage"] {
    direction: rtl;
}
[data-testid="stChatInput"] textarea {
    direction: rtl;
    text-align: right;
}
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """
أنت CyberGain AI، مساعد متخصص في IT وCloud والشبكات
وLinux وWindows Server والأمن السيبراني الدفاعي.
أجب بالعربية البسيطة وباختصار، واستخدم كلمات سهلة للمبتدئين.
ركز على الحماية والاستخدام المصرح به.
"""

st.title("CyberGain AI")
st.caption("مساعدك في IT وCloud والشبكات")

try:
    if "supabase" not in st.session_state:
        st.session_state.supabase = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
    db = st.session_state.supabase
except Exception:
    st.error("تعذّر الاتصال بقاعدة البيانات. تحقق من إعدادات Secrets.")
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.user:
    st.subheader("حسابك الشخصي")

    action = st.radio(
        "اختر العملية",
        ["تسجيل الدخول", "إنشاء حساب"],
        horizontal=True
    )

    email = st.text_input("البريد الإلكتروني")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("متابعة", use_container_width=True):
        if not email or not password:
            st.warning("أدخل البريد الإلكتروني وكلمة المرور.")
        else:
            try:
                if action == "إنشاء حساب":
                    result = db.auth.sign_up({
                        "email": email,
                        "password": password
                    })

                    if result.session is None:
                        st.info(
                            "افتح رسالة التأكيد في بريدك الإلكتروني، "
                            "ثم ارجع وسجّل الدخول."
                        )
                    else:
                        st.session_state.user = result.user
                        st.session_state.messages = []
                        st.rerun()
                else:
                    result = db.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })

                    st.session_state.user = result.user

                    history = (
                        db.table("chat_history")
                        .select("role, content")
                        .eq("user_id", result.user.id)
                        .order("created_at")
                        .execute()
                    )

                    st.session_state.messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in history.data
                    ]
                    st.rerun()

            except Exception as e:
                st.error(f"خطأ: {type(e).__name__}: {e}")

    st.stop()

user = st.session_state.user

with st.sidebar:
    st.write(f"الحساب: {user.email}")

    if st.button("تسجيل الخروج"):
        try:
            db.auth.sign_out()
        finally:
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()

    if st.button("محادثة جديدة"):
        st.session_state.messages = []
        st.rerun()

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"], avatar=None):
        st.markdown(message["content"])

question = st.chat_input("اكتب سؤالك هنا...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user", avatar=None):
        st.markdown(question)

    try:
        db.table("chat_history").insert({
            "user_id": user.id,
            "role": "user",
            "content": question
        }).execute()

        with st.chat_message("assistant", avatar=None):
            with st.spinner("يفكر..."):
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])

                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT}
                    ] + st.session_state.messages,
                    max_tokens=300,
                    temperature=0.2
                )

                answer = (
                    response.choices[0].message.content
                    or "ما وصلني جواب. جرّب مرة ثانية."
                )
                st.markdown(answer)

        db.table("chat_history").insert({
            "user_id": user.id,
            "role": "assistant",
            "content": answer
        }).execute()

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except Exception as e:
        st.error(f"حدث خطأ: {type(e).__name__}: {e}")
