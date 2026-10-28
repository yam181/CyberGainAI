
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone

# -------------------------
# إعداد الصفحة
# -------------------------
st.set_page_config(
    page_title="CyberGain AI",
    page_icon="🛡️",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    max-width: 950px;
    margin: auto;
}
[data-testid="stChatMessage"] {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# الاتصال بالخدمات
# -------------------------
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

@st.cache_resource
def get_groq():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

try:
    supabase = get_supabase()
    groq = get_groq()
except Exception as e:
    st.error("تعذّر الاتصال بالخدمات. افحص إعدادات Secrets.")
    st.stop()

# -------------------------
# تعليمات الذكاء الاصطناعي
# -------------------------
SYSTEM_PROMPT = """
You are CyberGain AI, an assistant specializing in IT,
Cloud Computing, networking, Linux, Windows Server,
and defensive cybersecurity.

LANGUAGE RULE:
Always answer in the same language as the user's latest message.
Support Arabic, English, Hebrew, and other languages.
If the user changes language, change your response language too.
Do not force Arabic when the user asks in another language.

Keep answers clear, helpful, and beginner-friendly.
Give step-by-step instructions when appropriate.
Focus on legal, authorized, defensive cybersecurity.
"""

# -------------------------
# حالة المستخدم
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False

# -------------------------
# تسجيل الدخول وإنشاء حساب
# -------------------------
if st.session_state.user is None:
    st.title("🛡️ CyberGain AI")
    st.caption("Your AI assistant for IT, Cloud & Cybersecurity")

    login_tab, signup_tab = st.tabs(
        ["تسجيل الدخول | Login", "إنشاء حساب | Sign up"]
    )

    with login_tab:
        login_email = st.text_input(
            "البريد الإلكتروني",
            key="login_email"
        )
        login_password = st.text_input(
            "كلمة المرور",
            type="password",
            key="login_password"
        )

        if st.button("دخول | Login", use_container_width=True):
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": login_email.strip(),
                    "password": login_password
                })

                if result.user and result.session:
                    st.session_state.user = result.user
                    st.session_state.messages = []
                    st.session_state.history_loaded = False
                    st.rerun()
                else:
                    st.error("تعذّر تسجيل الدخول. حاول مرة أخرى.")

            except Exception:
                st.error(
                    "فشل تسجيل الدخول. افحص البريد وكلمة المرور، "
                    "وتأكد من تأكيد البريد الإلكتروني."
                )

    with signup_tab:
        signup_email = st.text_input(
            "البريد الإلكتروني الجديد",
            key="signup_email"
        )
        signup_password = st.text_input(
            "كلمة المرور الجديدة (8 أحرف أو أكثر)",
            type="password",
            key="signup_password"
        )

        if st.button("إنشاء حساب | Sign up", use_container_width=True):
            if len(signup_password) < 8:
                st.warning("استخدم كلمة مرور من 8 أحرف على الأقل.")
            elif not signup_email.strip():
                st.warning("اكتب بريدك الإلكتروني.")
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": signup_email.strip(),
                        "password": signup_password
                    })

                    if result.session and result.user:
                        st.session_state.user = result.user
                        st.session_state.messages = []
                        st.session_state.history_loaded = False
                        st.rerun()
                    else:
                        st.success(
                            "تم طلب إنشاء الحساب. افحص بريدك الإلكتروني "
                            "لتأكيد الحساب، ثم سجّل الدخول."
                        )

                except Exception:
                    st.error(
                        "تعذّر إنشاء الحساب. قد يكون البريد مستخدمًا "
                        "أو كلمة المرور غير مقبولة."
                    )

    st.stop()

# -------------------------
# تحميل محادثات المستخدم
# -------------------------
user_id = str(st.session_state.user.id)

if not st.session_state.history_loaded:
    try:
        result = (
            supabase.table("chat_history")
            .select("role, content, created_at")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )

        st.session_state.messages = [
            {"role": row["role"], "content": row["content"]}
            for row in result.data
            if row["role"] in ("user", "assistant")
        ]
        st.session_state.history_loaded = True

    except Exception:
        st.error(
            "تعذّر تحميل المحادثات. افحص صلاحيات Supabase وRLS."
        )
        st.stop()

# -------------------------
# واجهة المحادثة
# -------------------------
st.title("🛡️ CyberGain AI")
st.caption("IT • Cloud • Networking • Linux • Cybersecurity")

with st.sidebar:
    st.subheader("الحساب | Account")
    st.write(st.session_state.user.email)

    if st.button("محادثة جديدة | New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("تسجيل الخروج | Logout", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.history_loaded = False
        st.rerun()

# عرض الرسائل الحالية
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------------
# إرسال السؤال والحصول على الإجابة
# -------------------------
prompt = st.chat_input("اكتب سؤالك بأي لغة...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            with st.spinner("CyberGain AI is thinking..."):
                response = groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        *st.session_state.messages[-20:]
                    ],
                    temperature=0.5,
                    max_tokens=2048
                )

                answer = response.choices[0].message.content
                st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        # حفظ السؤال والإجابة في Supabase
        now = datetime.now(timezone.utc).isoformat()

        supabase.table("chat_history").insert([
            {
                "user_id": user_id,
                "role": "user",
                "content": prompt,
                "created_at": now
            },
            {
                "user_id": user_id,
                "role": "assistant",
                "content": answer,
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }
        ]).execute()

    except Exception:
        st.error(
            "حدث خطأ أثناء الحصول على الإجابة أو حفظ المحادثة. "
            "افحص إعدادات Groq وSupabase."
        )
