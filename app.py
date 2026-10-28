
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone
import html
import uuid

# -------------------------
# Page settings
# -------------------------
st.set_page_config(
    page_title="CyberGain AI",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
.stApp { max-width: 1250px; margin: auto; }
[data-testid="stChatMessage"] { border-radius: 12px; }
[data-testid="stChatInput"] textarea {
    text-align: start !important;
}
</style>
""", unsafe_allow_html=True)


# -------------------------
# Services
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
    st.error("فشل الاتصال بالخدمات.")
    st.code(f"{type(e).__name__}: {e}")
    st.stop()


SYSTEM_PROMPT = """
You are CyberGain AI, an assistant specializing in IT,
Cloud Computing, networking, Linux, Windows Server,
and defensive cybersecurity.

Always respond in the same language as the user's latest message.
Support Arabic, English, Hebrew, and other languages.
Be clear, friendly, and beginner-friendly.
Give step-by-step instructions when helpful.
Focus on legal and authorized cybersecurity.
"""


def display_message(content):
    safe = html.escape(content).replace("\n", "<br>")
    st.markdown(
        f'<div dir="auto" style="text-align:start;'
        f'overflow-wrap:anywhere">{safe}</div>',
        unsafe_allow_html=True
    )


# -------------------------
# Session state
# -------------------------
defaults = {
    "user": None,
    "messages": [],
    "conversations": [],
    "conversation_id": None,
    "history_loaded": False,
    "auth_notice": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------------
# Authentication
# -------------------------
if st.session_state.user is None:
    st.title("🛡️ CyberGain AI")
    st.caption("مساعدك الذكي في IT وCloud والأمن السيبراني")

    login_tab, signup_tab = st.tabs([
        "تسجيل الدخول | Login",
        "إنشاء حساب | Sign up"
    ])

    with login_tab:
        email = st.text_input("البريد الإلكتروني", key="login_email")
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
                    st.session_state.conversations = []
                    st.session_state.conversation_id = None
                    st.session_state.history_loaded = False
                    st.rerun()
                else:
                    st.error("تعذّر تسجيل الدخول.")

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

        if st.button("إنشاء حساب | Sign up", use_container_width=True):
            if not new_email.strip():
                st.warning("اكتب بريدك الإلكتروني.")
            elif len(new_password) < 8:
                st.warning("كلمة المرور يجب أن تكون 8 أحرف على الأقل.")
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": new_email.strip(),
                        "password": new_password
                    })

                    if result.user and result.session:
                        st.session_state.user = result.user
                        st.session_state.messages = []
                        st.session_state.conversations = []
                        st.session_state.conversation_id = None
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


user_id = str(st.session_state.user.id)


# -------------------------
# Conversation helpers
# -------------------------
def load_conversations():
    result = (
        supabase.table("conversations")
        .select("id, title, created_at, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data or []


def create_conversation():
    result = supabase.table("conversations").insert({
        "user_id": user_id,
        "title": "محادثة جديدة"
    }).execute()

    if not result.data:
        raise RuntimeError("لم يتم إنشاء المحادثة.")

    conversation = result.data[0]
    st.session_state.conversation_id = str(conversation["id"])
    st.session_state.messages = []
    st.session_state.conversations = load_conversations()


def open_conversation(conversation_id):
    result = (
        supabase.table("chat_history")
        .select("role, content, created_at")
        .eq("user_id", user_id)
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )

    st.session_state.conversation_id = str(conversation_id)
    st.session_state.messages = [
        {"role": row["role"], "content": row["content"]}
        for row in (result.data or [])
        if row["role"] in ("user", "assistant")
    ]


# -------------------------
# Load conversation list
# -------------------------
if not st.session_state.history_loaded:
    try:
        st.session_state.conversations = load_conversations()

        if st.session_state.conversations:
            first_id = str(st.session_state.conversations[0]["id"])
            open_conversation(first_id)
        else:
            create_conversation()

        st.session_state.history_loaded = True

    except Exception as e:
        st.error("تعذّر تحميل المحادثات من Supabase.")
        st.code(f"{type(e).__name__}: {e}")
        st.stop()


# -------------------------
# Sidebar
# -------------------------
with st.sidebar:
    st.title("🛡️ CyberGain AI")
    st.caption(st.session_state.user.email)

    if st.button("＋ محادثة جديدة", use_container_width=True):
        try:
            create_conversation()
            st.rerun()
        except Exception as e:
            st.error("تعذّر إنشاء محادثة جديدة.")
            st.code(f"{type(e).__name__}: {e}")

    st.divider()
    st.subheader("محادثاتي")

    for conversation in st.session_state.conversations:
        cid = str(conversation["id"])
        title = conversation.get("title") or "محادثة جديدة"
        button_label = ("● " if cid == st.session_state.conversation_id
                        else "") + title

        if st.button(
            button_label,
            key=f"conversation_{cid}",
            use_container_width=True
        ):
            try:
                open_conversation(cid)
                st.rerun()
            except Exception as e:
                st.error("تعذّر فتح المحادثة.")
                st.code(f"{type(e).__name__}: {e}")

    st.divider()

    if st.button("تسجيل الخروج | Logout", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.conversations = []
        st.session_state.conversation_id = None
        st.session_state.history_loaded = False
        st.rerun()


# -------------------------
# Current conversation
# -------------------------
current_conversation = next(
    (
        c for c in st.session_state.conversations
        if str(c["id"]) == str(st.session_state.conversation_id)
    ),
    None
)

current_title = (
    current_conversation.get("title", "محادثة جديدة")
    if current_conversation else "محادثة جديدة"
)

st.title("🛡️ CyberGain AI")
st.caption(current_title)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        display_message(message["content"])


# -------------------------
# Chat input
# -------------------------
prompt = st.chat_input("اكتب سؤالك بأي لغة...")

if prompt:
    conversation_id = st.session_state.conversation_id

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        display_message(prompt)

    try:
        with st.chat_message("assistant"):
            with st.spinner("CyberGain AI يفكر..."):
                response = groq.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *st.session_state.messages[-20:]
                    ],
                    max_tokens=2048
                )

                answer = response.choices[0].message.content

                if not answer:
                    raise RuntimeError("عاد النموذج بإجابة فارغة.")

                display_message(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except Exception as e:
        st.error("حدث خطأ أثناء الحصول على الإجابة.")
        st.code(f"{type(e).__name__}: {e}")
        st.stop()

    # -------------------------
    # Save messages
    # -------------------------
    try:
        now = datetime.now(timezone.utc).isoformat()

        supabase.table("chat_history").insert([
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "role": "user",
                "content": prompt,
                "created_at": now
            },
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": answer,
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }
        ]).execute()

        # Name new conversations after the first question
        if current_title == "محادثة جديدة":
            title = " ".join(prompt.strip().split())[:55]
            if not title:
                title = "محادثة جديدة"

            supabase.table("conversations").update({
                "title": title,
                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }).eq("id", conversation_id).eq(
                "user_id", user_id
            ).execute()

        else:
            supabase.table("conversations").update({
                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }).eq("id", conversation_id).eq(
                "user_id", user_id
            ).execute()

        st.session_state.conversations = load_conversations()
        st.rerun()

    except Exception as e:
        st.error("ظهرت الإجابة، لكن تعذّر حفظ المحادثة.")
        st.code(f"{type(e).__name__}: {e}")
