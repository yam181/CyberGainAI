
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone
import html
import uuid

st.set_page_config(
    page_title="NEXORA AI",
    page_icon="🛡️",
    layout="wide",
)

st.markdown("""
<style>
.block-container {
    max-width: 1250px;
    padding-top: 2rem;
}
[data-testid="stChatInput"] textarea {
    text-align: start;
}
section[data-testid="stSidebar"] {
    min-width: 260px;
}
</style>
""", unsafe_allow_html=True)

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
You are NEXORA AI, a helpful multilingual AI assistant.
- Reply in the same language as the user.
- Keep answers short and direct, usually 2-5 sentences.
- Avoid long introductions and unnecessary details.
- Use simple words and examples.
- Help with IT, cloud, networking, Linux, programming,
  and defensive cybersecurity.
- Do not help with unauthorized access or harming systems.
"""


# =========================
# CONNECTIONS
# =========================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


@st.cache_resource
def get_groq():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


try:
    supabase = get_supabase()
    groq = get_groq()
except Exception as e:
    st.error(f"Connection error: {type(e).__name__}: {e}")
    st.stop()


# =========================
# DISPLAY
# =========================
def display_message(content):
    safe = html.escape(str(content)).replace("\n", "<br>")

    st.markdown(
        f'<div dir="auto" style="text-align:start;'
        f'overflow-wrap:anywhere;line-height:1.7">{safe}</div>',
        unsafe_allow_html=True,
    )


# =========================
# CONVERSATION TITLES
# =========================
def generate_conversation_title(messages_text):
    response = groq.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Create a short, descriptive title for this "
                    "conversation. Use 2-5 words in the same language "
                    "as the user. Describe the main topic. Return only "
                    "the title, without quotes or explanation."
                ),
            },
            {
                "role": "user",
                "content": messages_text,
            },
        ],
        max_tokens=40,
        temperature=0.2,
    )

    title = (response.choices[0].message.content or "").strip()
    title = title.strip("\"'“”")
    title = " ".join(title.split())

    if not title or title.lower() in (
        "new conversation",
        "محادثة جديدة",
        "محادثة",
    ):
        raise ValueError("AI returned an empty or generic title.")

    return title[:55]


def update_conversation_title(title):
    conversation_id = st.session_state.conversation_id
    user_id = st.session_state.user["id"]

    result = (
        supabase.table("conversations")
        .update({
            "title": title[:55],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("id", conversation_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        raise Exception("Supabase did not update the conversation title.")


def refresh_conversation_title():
    messages = st.session_state.messages[-10:]

    if not messages:
        return

    conversation_text = "\n".join(
        f'{message["role"]}: {message["content"]}'
        for message in messages
        if message.get("content")
    )

    try:
        title = generate_conversation_title(conversation_text)
        update_conversation_title(title)
        st.session_state.title_error = ""
    except Exception as e:
        # Keep a meaningful fallback title if title generation fails.
        first_user_message = next(
            (
                message["content"]
                for message in st.session_state.messages
                if message.get("role") == "user"
                and message.get("content")
            ),
            "محادثة جديدة",
        )

        fallback_title = " ".join(first_user_message.split())[:55]

        try:
            update_conversation_title(fallback_title)
        except Exception as db_error:
            st.session_state.title_error = (
                f"تعذّر حفظ العنوان: {type(db_error).__name__}: "
                f"{db_error}"
            )
            return

        st.session_state.title_error = (
            f"تعذّر توليد عنوان ذكي؛ استُخدم أول سؤال بدلًا منه. "
            f"السبب: {type(e).__name__}: {e}"
        )


# =========================
# DATABASE
# =========================
def load_conversations():
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("user_id", st.session_state.user["id"])
        .order("updated_at", desc=True)
        .execute()
    )

    st.session_state.conversations = result.data or []


def create_conversation():
    user_id = st.session_state.user["id"]
    conversation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("conversations")
        .insert({
            "id": conversation_id,
            "user_id": user_id,
            "title": "محادثة جديدة",
            "created_at": now,
            "updated_at": now,
        })
        .execute()
    )

    if not result.data:
        raise Exception("Could not create conversation.")

    st.session_state.conversation_id = conversation_id
    st.session_state.messages = []
    st.session_state.title_error = ""

    load_conversations()


def open_conversation(conversation_id):
    result = (
        supabase.table("chat_history")
        .select("role, content")
        .eq("user_id", st.session_state.user["id"])
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )

    st.session_state.conversation_id = conversation_id
    st.session_state.messages = result.data or []
    st.session_state.title_error = ""


def save_message(role, content):
    user_id = st.session_state.user["id"]
    conversation_id = st.session_state.conversation_id

    if not conversation_id:
        raise Exception("No active conversation.")

    supabase.table("chat_history").insert({
        "user_id": user_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
    }).execute()

    supabase.table("conversations").update({
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq(
        "id", conversation_id
    ).eq(
        "user_id", user_id
    ).execute()


# =========================
# SESSION STATE
# =========================
defaults = {
    "user": None,
    "messages": [],
    "conversations": [],
    "conversation_id": None,
    "title_error": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================
# LOGIN / SIGNUP
# =========================
if not st.session_state.user:
    st.title("🛡️ NEXORA AI")

    login_tab, signup_tab = st.tabs([
        "تسجيل الدخول",
        "إنشاء حساب",
    ])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input(
                "كلمة المرور",
                type="password",
            )
            login = st.form_submit_button(
                "تسجيل الدخول",
                use_container_width=True,
            )

        if login:
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password,
                })

                if not result.user:
                    st.error("تعذّر تسجيل الدخول.")
                    st.stop()

                st.session_state.user = {
                    "id": str(result.user.id),
                    "email": result.user.email,
                }

                load_conversations()

                if st.session_state.conversations:
                    open_conversation(
                        st.session_state.conversations[0]["id"]
                    )
                else:
                    create_conversation()

                st.rerun()

            except Exception as e:
                st.error(
                    f"فشل تسجيل الدخول: {type(e).__name__}: {e}"
                )

    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input("البريد الإلكتروني")
            new_password = st.text_input(
                "كلمة المرور",
                type="password",
            )
            signup = st.form_submit_button(
                "إنشاء حساب",
                use_container_width=True,
            )

        if signup:
            if len(new_password) < 6:
                st.warning(
                    "كلمة المرور يجب أن تكون 6 أحرف على الأقل."
                )
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": new_email.strip(),
                        "password": new_password,
                    })

                    if result.session and result.user:
                        st.session_state.user = {
                            "id": str(result.user.id),
                            "email": result.user.email,
                        }

                        load_conversations()

                        if st.session_state.conversations:
                            open_conversation(
                                st.session_state.conversations[0]["id"]
                            )
                        else:
                            create_conversation()

                        st.rerun()
                    else:
                        st.success(
                            "افحص بريدك لتأكيد الحساب، ثم سجّل الدخول."
                        )

                except Exception as e:
                    st.error(
                        f"فشل إنشاء الحساب: {type(e).__name__}: {e}"
                    )

    st.stop()


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.title("🛡️ NEXORA AI")
    st.caption(st.session_state.user["email"])

    if st.button("＋ محادثة جديدة", use_container_width=True):
        try:
            create_conversation()
            st.rerun()
        except Exception as e:
            st.error(f"تعذّر إنشاء المحادثة: {e}")

    st.divider()
    st.subheader("محادثاتي")

    try:
        load_conversations()
    except Exception as e:
        st.error(f"تعذّر تحميل المحادثات: {e}")

    if not st.session_state.conversations:
        st.caption("لا توجد محادثات بعد.")

    for conversation in st.session_state.conversations:
        cid = conversation["id"]
        title = conversation.get("title") or "محادثة جديدة"

        if st.button(
            title,
            key=f"chat_{cid}",
            use_container_width=True,
            type=(
                "primary"
                if cid == st.session_state.conversation_id
                else "secondary"
            ),
        ):
            try:
                open_conversation(cid)
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
        st.rerun()


# =========================
# MAIN CHAT
# =========================
st.title("🛡️ NEXORA AI")
st.caption("اسأل، تعلّم، وطوّر مهاراتك.")

if st.session_state.title_error:
    st.warning(st.session_state.title_error)

if not st.session_state.conversation_id:
    try:
        create_conversation()
    except Exception as e:
        st.error(f"تعذّر بدء المحادثة: {e}")
        st.stop()

for message in st.session_state.messages:
    role = message.get("role", "assistant")

    if role in ("user", "assistant"):
        with st.chat_message(role):
            display_message(message.get("content", ""))


# =========================
# SEND MESSAGE
# =========================
prompt = st.chat_input("اكتب رسالتك إلى NEXORA AI...")

if prompt and prompt.strip():
    prompt = prompt.strip()

    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    with st.chat_message("user"):
        display_message(prompt)

    try:
        save_message("user", prompt)

        with st.chat_message("assistant"):
            with st.spinner("NEXORA AI يفكر..."):
                response = groq.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        *[
                            {
                                "role": message["role"],
                                "content": message["content"],
                            }
                            for message in st.session_state.messages
                        ],
                    ],
                    max_tokens=500,
                    temperature=0.5,
                )

                answer = (
                    response.choices[0].message.content or ""
                ).strip()

                display_message(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
        })

        save_message("assistant", answer)

        # Update the title and reload the sidebar.
        refresh_conversation_title()
        load_conversations()

        st.rerun()

    except Exception as e:
        st.error(
            f"حدث خطأ: {type(e).__name__}: {e}"
        )
