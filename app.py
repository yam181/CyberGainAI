
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
    page_title="NEXORA AI",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    [data-testid="stChatInput"] textarea {
        text-align: start;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Connections
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

supabase = get_supabase()
groq = get_groq()

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
You are NEXORA AI, a helpful multilingual AI assistant.
Reply in the same language as the user's latest message.
Support users with IT, cloud computing, networking, Linux,
programming, and defensive cybersecurity.
Explain concepts clearly and adapt to the user's skill level.
Never claim to have performed actions you did not perform.
Provide safe, authorized cybersecurity guidance.
"""

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
# Display messages safely
# -------------------------
def display_message(content):
    safe_content = html.escape(str(content)).replace("\n", "<br>")
    st.markdown(
        f"""
        <div dir="auto"
             style="text-align:start; overflow-wrap:anywhere;">
            {safe_content}
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------
# Conversation helpers
# -------------------------
def load_conversations():
    user_id = st.session_state.user.id

    result = (
        supabase.table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )

    st.session_state.conversations = result.data or []


def create_conversation():
    user_id = st.session_state.user.id

    result = (
        supabase.table("conversations")
        .insert({
            "user_id": user_id,
            "title": "محادثة جديدة"
        })
        .execute()
    )

    if not result.data:
        raise Exception("لم يتم إنشاء المحادثة.")

    conversation = result.data[0]

    st.session_state.conversation_id = conversation["id"]
    st.session_state.messages = []
    st.session_state.history_loaded = True

    load_conversations()


def open_conversation(conversation_id):
    st.session_state.conversation_id = conversation_id

    result = (
        supabase.table("chat_history")
        .select("role, content")
        .eq("user_id", st.session_state.user.id)
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )

    st.session_state.messages = result.data or []
    st.session_state.history_loaded = True


def save_message(role, content):
    supabase.table("chat_history").insert({
        "user_id": st.session_state.user.id,
        "conversation_id": st.session_state.conversation_id,
        "role": role,
        "content": content
    }).execute()


def update_conversation_title(title):
    supabase.table("conversations").update({
        "title": title[:55],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq(
        "id", st.session_state.conversation_id
    ).eq(
        "user_id", st.session_state.user.id
    ).execute()


# -------------------------
# Login / Signup
# -------------------------
if st.session_state.user is None:
    st.title("🛡️ NEXORA AI")
    st.caption("Intelligence. Security. Innovation.")

    login_tab, signup_tab = st.tabs(["تسجيل الدخول", "إنشاء حساب"])

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

        if st.button("دخول", use_container_width=True):
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": login_email,
                    "password": login_password
                })

                st.session_state.user = result.user
                st.session_state.auth_notice = "تم تسجيل الدخول بنجاح."
                st.rerun()

            except Exception as e:
                st.error(f"تعذّر تسجيل الدخول: {e}")

    with signup_tab:
        signup_email = st.text_input(
            "البريد الإلكتروني",
            key="signup_email"
        )
        signup_password = st.text_input(
            "كلمة المرور (6 أحرف على الأقل)",
            type="password",
            key="signup_password"
        )

        if st.button("إنشاء حساب", use_container_width=True):
            if len(signup_password) < 6:
                st.warning("كلمة المرور يجب أن تتكون من 6 أحرف على الأقل.")
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": signup_email,
                        "password": signup_password
                    })

                    if result.session and result.user:
                        st.session_state.user = result.user
                        st.rerun()
                    else:
                        st.success(
                            "تم إنشاء الحساب. افحص بريدك الإلكتروني "
                            "لتأكيد الحساب، ثم سجّل الدخول."
                        )

                except Exception as e:
                    st.error(f"تعذّر إنشاء الحساب: {e}")

    st.stop()


# -------------------------
# Initialize conversations
# -------------------------
if not st.session_state.history_loaded:
    try:
        load_conversations()

        if st.session_state.conversations:
            open_conversation(
                st.session_state.conversations[0]["id"]
            )
        else:
            create_conversation()

    except Exception as e:
        st.error(f"تعذّر تحميل المحادثات: {e}")
        st.stop()


# -------------------------
# Sidebar
# -------------------------
with st.sidebar:
    st.title("🛡️ NEXORA AI")
    st.caption(st.session_state.user.email or "")

    if st.button("＋ محادثة جديدة", use_container_width=True):
        try:
            create_conversation()
            st.rerun()
        except Exception as e:
            st.error(f"تعذّر إنشاء المحادثة: {e}")

    st.divider()
    st.subheader("محادثاتي")

    for conversation in st.session_state.conversations:
        conversation_id = conversation["id"]
        title = conversation.get("title") or "محادثة جديدة"

        if st.button(
            title,
            key=f"conversation_{conversation_id}",
            use_container_width=True,
            type=(
                "primary"
                if conversation_id == st.session_state.conversation_id
                else "secondary"
            )
        ):
            try:
                open_conversation(conversation_id)
                st.rerun()
            except Exception as e:
                st.error(f"تعذّر فتح المحادثة: {e}")

    st.divider()

    if st.button("تسجيل الخروج", use_container_width=True):
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
# Main chat
# -------------------------
st.title("🛡️ NEXORA AI")
st.caption("مساعدك للذكاء الاصطناعي وتقنيات المعلومات")

current_conversation = next(
    (
        c for c in st.session_state.conversations
        if c["id"] == st.session_state.conversation_id
    ),
    None
)

if current_conversation:
    st.caption(f"المحادثة: {current_conversation.get('title', 'محادثة جديدة')}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        display_message(message["content"])


prompt = st.chat_input("اكتب رسالتك إلى NEXORA AI...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        display_message(prompt)

    try:
        save_message("user", prompt)

        # Give the conversation a title based on its first question.
        if (
            current_conversation
            and current_conversation.get("title") == "محادثة جديدة"
        ):
            update_conversation_title(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NEXORA AI يفكر..."):
                response = groq.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ]
                    ]
                )

                answer = response.choices[0].message.content or ""
                display_message(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        save_message("assistant", answer)
        load_conversations()
        st.rerun()

    except Exception as e:
        st.error(
            f"حدث خطأ أثناء معالجة الرسالة: "
            f"{type(e).__name__}: {e}"
        )
