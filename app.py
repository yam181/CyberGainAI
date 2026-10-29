
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone
import html
import uuid

# =========================
# PAGE SETTINGS
# =========================
st.set_page_config(
    page_title="NEXORA AI",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    [data-testid="stChatMessage"] {
        border-radius: 14px;
    }
    [data-testid="stChatInput"] textarea {
        text-align: start;
    }
    section[data-testid="stSidebar"] {
        min-width: 260px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# CONFIGURATION
# =========================
MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
You are NEXORA AI, a helpful multilingual AI assistant.

- Reply in the same language as the user's latest message.
- Explain IT, cloud, networking, Linux, programming,
  and defensive cybersecurity clearly.
- Give beginner-friendly, step-by-step instructions when useful.
- Help with authorized labs and troubleshooting.
- Do not help with stealing credentials, unauthorized access,
  malware deployment, or harming other people's systems.
- Be accurate and admit uncertainty.
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
# HELPER FUNCTIONS
# =========================
def display_message(content):
    safe_content = html.escape(str(content)).replace("\n", "<br>")

    st.markdown(
        f"""
        <div dir="auto"
             style="text-align:start; overflow-wrap:anywhere;
                    line-height:1.7;">
            {safe_content}
        </div>
        """,
        unsafe_allow_html=True,
    )


def generate_conversation_title(messages_text):
    """Generate a short title describing the conversation topic."""
    try:
        response = groq.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create a short, descriptive title for this "
                        "conversation based on its current topic. "
                        "Use 2 to 6 words, in the same language as "
                        "the conversation. Summarize the topic, "
                        "not just the first question. Return only "
                        "the title, without quotation marks."
                    ),
                },
                {
                    "role": "user",
                    "content": messages_text,
                },
            ],
            max_tokens=30,
            temperature=0.2,
        )

        title = (
            response.choices[0].message.content or ""
        ).strip().strip("\"'“”")

        title = " ".join(title.split())

        return title[:55] if title else "محادثة جديدة"

    except Exception:
        return "محادثة جديدة"


def load_conversations():
    user_id = st.session_state.user["id"]

    response = (
        supabase.table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )

    st.session_state.conversations = response.data or []


def create_conversation():
    user_id = st.session_state.user["id"]
    conversation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    response = (
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

    if not response.data:
        raise Exception("Could not create a conversation.")

    st.session_state.conversation_id = conversation_id
    st.session_state.messages = []

    load_conversations()


def open_conversation(conversation_id):
    user_id = st.session_state.user["id"]

    response = (
        supabase.table("chat_history")
        .select("role, content")
        .eq("user_id", user_id)
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )

    st.session_state.conversation_id = conversation_id
    st.session_state.messages = response.data or []


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
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq(
        "id", conversation_id
    ).eq(
        "user_id", user_id
    ).execute()


def update_conversation_title(title):
    user_id = st.session_state.user["id"]
    conversation_id = st.session_state.conversation_id

    supabase.table("conversations").update({
        "title": title[:55],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq(
        "id", conversation_id
    ).eq(
        "user_id", user_id
    ).execute()


def refresh_conversation_title():
    """Recalculate the title from the latest conversation messages."""
    messages = st.session_state.messages

    # Use recent messages so the title follows the current topic.
    recent_messages = messages[-10:]

    messages_text = "\n".join(
        f'{message["role"]}: {message["content"]}'
        for message in recent_messages
        if message.get("content")
    )

    if not messages_text.strip():
        return

    title = generate_conversation_title(messages_text)
    update_conversation_title(title)


# =========================
# SESSION STATE
# =========================
defaults = {
    "user": None,
    "messages": [],
    "conversations": [],
    "conversation_id": None,
    "auth_notice": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================
# LOGIN / SIGNUP
# =========================
if not st.session_state.user:
    st.title("🛡️ NEXORA AI")
    st.caption("Your AI assistant for learning and problem-solving.")

    if st.session_state.auth_notice:
        st.info(st.session_state.auth_notice)
        st.session_state.auth_notice = ""

    login_tab, signup_tab = st.tabs([
        "تسجيل الدخول",
        "إنشاء حساب",
    ])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("البريد الإلكتروني")
            login_password = st.text_input(
                "كلمة المرور",
                type="password",
            )
            login_submit = st.form_submit_button(
                "تسجيل الدخول",
                use_container_width=True,
            )

        if login_submit:
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": login_email.strip(),
                    "password": login_password,
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
            signup_email = st.text_input(
                "البريد الإلكتروني",
                key="signup_email",
            )
            signup_password = st.text_input(
                "كلمة المرور",
                type="password",
                key="signup_password",
            )
            signup_submit = st.form_submit_button(
                "إنشاء حساب",
                use_container_width=True,
            )

        if signup_submit:
            if len(signup_password) < 6:
                st.warning(
                    "استخدم كلمة مرور من 6 أحرف على الأقل."
                )
            else:
                try:
                    result = supabase.auth.sign_up({
                        "email": signup_email.strip(),
                        "password": signup_password,
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
                            "تم إنشاء الحساب. افحص بريدك الإلكتروني "
                            "لتأكيد الحساب، ثم سجّل الدخول."
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
            ),
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
        st.rerun()


# =========================
# MAIN CHAT
# =========================
st.title("🛡️ NEXORA AI")
st.caption("اسأل، تعلّم، وطوّر مهاراتك.")

if not st.session_state.conversation_id:
    try:
        create_conversation()
    except Exception as e:
        st.error(f"تعذّر بدء المحادثة: {e}")
        st.stop()


# Display previous messages.
for message in st.session_state.messages:
    role = message.get("role", "assistant")

    if role not in ("user", "assistant"):
        continue

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
        # Save the user's message.
        save_message("user", prompt)

        # Generate the AI response.
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
                )

                answer = (
                    response.choices[0].message.content or ""
                ).strip()

                display_message(answer)

        # Save the assistant's response.
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
        })

        save_message("assistant", answer)

        # IMPORTANT: update the title after every exchange.
        refresh_conversation_title()

        # Refresh sidebar titles and conversation order.
        load_conversations()

        st.rerun()

    except Exception as e:
        st.error(
            f"حدث خطأ أثناء معالجة الرسالة: {type(e).__name__}: {e}"
        )
