
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone

# -------------------------
# Page settings
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
# Connect to services
# -------------------------
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


@st.cache_resource
def get_groq():
    return Groq(
        api_key=st.secrets["GROQ_API_KEY"]
    )


try:
    supabase = get_supabase()
    groq = get_groq()
except Exception as e:
    st.error("فشل الاتصال بالخدمات.")
    st.code(f"{type(e).__name__}: {e}")
    st.stop()


# -------------------------
# AI instructions
# -------------------------
SYSTEM_PROMPT = """
You are CyberGain AI, an assistant specializing in:
IT, Cloud Computing, Networking, Linux, Windows Server,
and defensive cybersecurity.

Always answer in the same language as the user's latest message.
Support Arabic, English, Hebrew, and other languages.
If the user changes language, change your response language too.

Be clear, concise, and beginner-friendly.
Provide step-by-step instructions when useful.
Focus on legal, authorized, defensive cybersecurity.
"""


# -------------------------
# Session state
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False


# -------------------------
# Login and signup
# -------------------------
if st.session_state.user is None:
    st.title("🛡️ CyberGain AI")
    st.caption("Your AI assistant for IT, Cloud & Cybersecurity")

    login_tab, signup_tab = st.tabs([
        "تسجيل الدخول | Login",
        "إنشاء حساب | Sign up"
    ])

    with login_tab:
        email = st.text_input(
            "البريد الإلكتروني",
            key="login_email"
        )

        password = st.text_input(
            "كلمة المرور",
            type="password",
            key="login_password"
        )

        if st.button("دخول | Login", use_container_width=True):
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password
                })

                if result.user and result.session:
                    st.session_state.user = result.user
                    st.session_state.messages = []
                    st.session_state.history_loaded = False
                    st.rerun()
                else:
                    st.error("لم ينجح تسجيل الدخول.")

            except Exception as e:
                st.error("خطأ أثناء تسجيل الدخول:")
                st.code(f"{type(e).__name__}: {e}")

    with signup_tab:
        new_email = st.text_input(
            "البريد الإلكتروني الجديد",
            key="signup_email"
        )

        new_password = st.text_input(
            "كلمة المرور الجديدة (8 أحرف أو أكثر)",
            type="password",
            key="signup_password"
        )

        if st.button(
            "إنشاء حساب | Sign up",
            use_container_width=True
        ):
            if len(new_password) < 8:
                st.warning(
                    "كلمة المرور يجب أن تكون 8 أحرف على الأقل."
                )
            elif not new_email.strip():
                st.warning("اكتب البريد الإلكتروني.")
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": new_email.strip(),
                        "password": new_password
                    })

                    if result.user and result.session:
                        st.session_state.user = result.user
                        st.session_state.messages = []
                        st.session_state.history_loaded = False
                        st.rerun()
                    else:
                        st.success(
                            "افحص بريدك الإلكتروني لتأكيد الحساب، "
                            "ثم سجّل الدخول."
                        )

                except Exception as e:
                    st.error("خطأ أثناء إنشاء الحساب:")
                    st.code(f"{type(e).__name__}: {e}")

    st.stop()


# -------------------------
# Load saved messages
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
            {
                "role": row["role"],
                "content": row["content"]
            }
            for row in result.data
            if row["role"] in ("user", "assistant")
        ]

        st.session_state.history_loaded = True

    except Exception as e:
        st.error("خطأ أثناء تحميل المحادثات:")
        st.code(f"{type(e).__name__}: {e}")
        st.stop()


# -------------------------
# Chat interface
# -------------------------
st.title("🛡️ CyberGain AI")
st.caption("IT • Cloud • Networking • Linux • Cybersecurity")

with st.sidebar:
    st.subheader("الحساب | Account")
    st.write(st.session_state.user.email)

    if st.button(
        "محادثة جديدة | New chat",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.rerun()

    if st.button(
        "تسجيل الخروج | Logout",
        use_container_width=True
    ):
        try:
            supabase.auth.sign_out()
        except Exception as e:
            st.warning(f"تعذّر تسجيل الخروج من الخدمة: {e}")

        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.history_loaded = False
        st.rerun()


# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -------------------------
# Ask AI
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
                    model="openai/gpt-oss-120b",
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },
                        *st.session_state.messages[-20:]
                    ],
                    max_tokens=2048
                )

                answer = response.choices[0].message.content

                if not answer:
                    raise RuntimeError(
                        "The AI returned an empty answer."
                    )

                st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except Exception as e:
        st.error("فشل الحصول على إجابة من Groq:")
        st.code(f"{type(e).__name__}: {e}")
        st.stop()


    # -------------------------
    # Save messages to Supabase
    # -------------------------
    try:
        supabase.table("chat_history").insert([
            {
                "user_id": user_id,
                "role": "user",
                "content": prompt,
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()
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

    except Exception as e:
        st.error(
            "وصلتك الإجابة، لكن فشل حفظ المحادثة في Supabase:"
        )
        st.code(f"{type(e).__name__}: {e}")

