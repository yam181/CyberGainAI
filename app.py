
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone
import uuid
import re

# -------------------------
# Page configuration
# -------------------------
st.set_page_config(
    page_title="NEXORA AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.3rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }
    [data-testid="stSidebar"] {
        min-width: 255px;
        max-width: 255px;
    }
    .nexora-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .nexora-subtitle {
        color: #8b949e;
        font-size: 0.9rem;
        margin-top: 0;
    }
    div[data-testid="stButton"] button {
        border-radius: 10px;
    }
    .stChatMessage {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Secrets and clients
# -------------------------
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    groq = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("تعذّر الاتصال بالإعدادات. افحص Secrets في Streamlit Cloud.")
    st.stop()

MODEL = "openai/gpt-oss-120b"

# -------------------------
# Session state
# -------------------------
defaults = {
    "user": None,
    "access_token": None,
    "conversation_id": None,
    "messages": [],
    "auth_mode": "login",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def set_access_token(token):
    """Apply the signed-in user's JWT to database requests."""
    st.session_state.access_token = token
    supabase.postgrest.auth(token)


def restore_auth():
    token = st.session_state.access_token
    if token:
        set_access_token(token)


def current_user_id():
    user = st.session_state.user
    return str(user.id) if user else None


def db_error_message(error):
    message = str(error)
    if "row-level security" in message.lower() or "42501" in message:
        return (
            "رفضت صلاحيات Supabase العملية. تأكد أن تسجيل الدخول ناجح "
            "وأن سياسات RLS تسمح للمستخدم بعملياته على الجدول."
        )
    return message


def make_title(messages):
    """Create a short title from the conversation context."""
    try:
        context = "\n".join(
            f"{m['role']}: {m['content'][:500]}"
            for m in messages[-8:]
        )

        result = groq.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create a concise title for this conversation. "
                        "Use the same language as the user. "
                        "Return only the title, 3 to 7 words maximum."
                    ),
                },
                {"role": "user", "content": context},
            ],
            max_tokens=40,
            temperature=0.2,
        )
        title = (result.choices[0].message.content or "").strip()
        title = title.strip('"\'` ')
        return title[:80] if title else "محادثة جديدة"
    except Exception:
        for message in messages:
            if message["role"] == "user":
                return message["content"][:45] or "محادثة جديدة"
        return "محادثة جديدة"


# -------------------------
# Authentication
# -------------------------
def sign_out():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.conversation_id = None
    st.session_state.messages = []
    st.rerun()


def load_conversations():
    restore_auth()
    return (
        supabase.table("conversations")
        .select("id,user_id,title,created_at,updated_at")
        .eq("user_id", current_user_id())
        .order("updated_at", desc=True)
        .execute()
        .data
    )


def create_conversation():
    restore_auth()
    now = datetime.now(timezone.utc).isoformat()
    conversation_id = str(uuid.uuid4())

    result = supabase.table("conversations").insert({
        "id": conversation_id,
        "user_id": current_user_id(),
        "title": "محادثة جديدة",
        "created_at": now,
        "updated_at": now,
    }).execute()

    st.session_state.conversation_id = str(result.data[0]["id"])
    st.session_state.messages = []
    return st.session_state.conversation_id


def load_messages(conversation_id):
    restore_auth()
    result = (
        supabase.table("chat_history")
        .select("role,content,created_at")
        .eq("user_id", current_user_id())
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )
    return [
        {"role": row["role"], "content": row["content"]}
        for row in result.data
        if row.get("role") in ("user", "assistant")
    ]


def save_message(conversation_id, role, content):
    restore_auth()
    supabase.table("chat_history").insert({
        "user_id": current_user_id(),
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def update_conversation_title(conversation_id, title):
    restore_auth()
    supabase.table("conversations").update({
        "title": title,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", conversation_id).eq(
        "user_id", current_user_id()
    ).execute()


def touch_conversation(conversation_id):
    restore_auth()
    supabase.table("conversations").update({
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", conversation_id).eq(
        "user_id", current_user_id()
    ).execute()


def delete_conversation(conversation_id):
    restore_auth()

    # Delete messages first because chat_history references conversations.
    supabase.table("chat_history").delete().eq(
        "user_id", current_user_id()
    ).eq("conversation_id", conversation_id).execute()

    supabase.table("conversations").delete().eq(
        "user_id", current_user_id()
    ).eq("id", conversation_id).execute()

    if str(st.session_state.conversation_id) == str(conversation_id):
        st.session_state.conversation_id = None
        st.session_state.messages = []


# -------------------------
# Login screen
# -------------------------
if not st.session_state.user:
    st.markdown('<p class="nexora-title">🤖 NEXORA AI</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="nexora-subtitle">Your intelligent AI assistant</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    left, center, right = st.columns([1, 1.5, 1])

    with center:
        st.subheader("مرحبًا بك 👋")

        mode = st.radio(
            "اختَر العملية",
            ["تسجيل الدخول", "إنشاء حساب"],
            horizontal=True,
        )

        with st.form("auth_form"):
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور", type="password")
            submitted = st.form_submit_button(
                "دخول" if mode == "تسجيل الدخول" else "إنشاء حساب",
                use_container_width=True,
            )

        if submitted:
            if not email.strip() or not password:
                st.warning("أدخل البريد الإلكتروني وكلمة المرور.")
            else:
                try:
                    if mode == "تسجيل الدخول":
                        result = supabase.auth.sign_in_with_password({
                            "email": email.strip(),
                            "password": password,
                        })

                        if not result.user or not result.session:
                            st.error("لم يكتمل تسجيل الدخول.")
                        else:
                            st.session_state.user = result.user
                            set_access_token(result.session.access_token)
                            st.session_state.conversation_id = None
                            st.session_state.messages = []
                            st.rerun()

                    else:
                        result = supabase.auth.sign_up({
                            "email": email.strip(),
                            "password": password,
                        })

                        if result.session and result.user:
                            st.session_state.user = result.user
                            set_access_token(result.session.access_token)
                            st.success("تم إنشاء الحساب!")
                            st.rerun()
                        else:
                            st.success(
                                "تم إرسال طلب التسجيل. افحص بريدك الإلكتروني "
                                "لتأكيد الحساب، ثم سجّل الدخول."
                            )

                except Exception as e:
                    st.error(db_error_message(e))

    st.stop()


# -------------------------
# Restore authenticated JWT
# -------------------------
restore_auth()

# -------------------------
# Sidebar
# -------------------------
with st.sidebar:
    st.markdown("## 🤖 NEXORA AI")
    st.caption("مساعدك الذكي")
    st.divider()

    user_email = getattr(st.session_state.user, "email", None)
    if user_email:
        st.caption(user_email)

    if st.button("＋ محادثة جديدة", use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    if st.button("تسجيل الخروج", use_container_width=True):
        sign_out()

    st.divider()
    st.markdown("### محادثاتي")

    try:
        conversations = load_conversations()
    except Exception as e:
        st.error("تعذّر تحميل المحادثات.")
        st.caption(db_error_message(e))
        conversations = []

    for conversation in conversations:
        cid = str(conversation["id"])
        title = conversation.get("title") or "محادثة جديدة"

        # Two compact columns: title and visible trash button.
        title_col, trash_col = st.columns([5, 1], gap="small")

        with title_col:
            label = title[:27] + ("…" if len(title) > 27 else "")
            if st.button(
                label,
                key=f"open_{cid}",
                use_container_width=True,
                type=(
                    "primary"
                    if str(st.session_state.conversation_id) == cid
                    else "secondary"
                ),
            ):
                try:
                    st.session_state.conversation_id = cid
                    st.session_state.messages = load_messages(cid)
                    st.rerun()
                except Exception as e:
                    st.error("تعذّر فتح المحادثة.")
                    st.caption(db_error_message(e))

        with trash_col:
            if st.button("🗑️", key=f"delete_{cid}", help="حذف المحادثة"):
                st.session_state[f"confirm_delete_{cid}"] = True

        if st.session_state.get(f"confirm_delete_{cid}", False):
            st.warning(f"هل تريد حذف «{title}»؟")
            yes_col, no_col = st.columns(2)

            with yes_col:
                if st.button("نعم، احذف", key=f"yes_delete_{cid}"):
                    try:
                        delete_conversation(cid)
                        st.session_state.pop(f"confirm_delete_{cid}", None)
                        st.rerun()
                    except Exception as e:
                        st.error("تعذّر حذف المحادثة.")
                        st.caption(db_error_message(e))

            with no_col:
                if st.button("إلغاء", key=f"no_delete_{cid}"):
                    st.session_state.pop(f"confirm_delete_{cid}", None)
                    st.rerun()


# -------------------------
# Main chat
# -------------------------
st.markdown('<p class="nexora-title">NEXORA AI</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="nexora-subtitle">اسألني أي شيء، وسأساعدك خطوة بخطوة.</p>',
    unsafe_allow_html=True,
)
st.divider()

# Start a conversation only when the user sends the first message.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("اكتب رسالتك هنا...")

if prompt and prompt.strip():
    prompt = prompt.strip()

    try:
        if not st.session_state.conversation_id:
            create_conversation()

        conversation_id = str(st.session_state.conversation_id)

        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)

        with st.chat_message("user"):
            st.markdown(prompt)

        save_message(conversation_id, "user", prompt)

        # Keep the context concise.
        context = st.session_state.messages[-12:]

        with st.chat_message("assistant"):
            with st.spinner("NEXORA يفكّر..."):
                response = groq.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are NEXORA AI, a helpful assistant. "
                                "Answer clearly and briefly by default. "
                                "Use the user's language. "
                                "For technical topics, explain step by step "
                                "when needed. Never claim to perform actions "
                                "you have not performed."
                            ),
                        },
                        *context,
                    ],
                    temperature=0.5,
                    max_tokens=700,
                )

                answer = (
                    response.choices[0].message.content or
                    "عذرًا، لم أتمكن من إنشاء رد."
                ).strip()

                st.markdown(answer)

        assistant_message = {"role": "assistant", "content": answer}
        st.session_state.messages.append(assistant_message)

        save_message(conversation_id, "assistant", answer)
        touch_conversation(conversation_id)

        # Generate a title from the first exchange.
        if len(st.session_state.messages) <= 2:
            title = make_title(st.session_state.messages)
            update_conversation_title(conversation_id, title)

        st.rerun()

    except Exception as e:
        st.error("حدث خطأ أثناء حفظ الرسالة أو إنشاء الرد.")
        st.caption(db_error_message(e))
