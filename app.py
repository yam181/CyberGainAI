
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

Rules:
- Reply in the same language as the user's latest message.
- Explain IT, cloud computing, networking, Linux, programming,
  and cybersecurity in a clear, beginner-friendly way.
- When useful, give step-by-step instructions and examples.
- Support defensive cybersecurity, system administration,
  troubleshooting, and authorized lab learning.
- Do not assist with stealing credentials, unauthorized access,
  malware deployment, or harming other people's systems.
- Be accurate. If you are uncertain, say so.
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
    """Display chat text safely, including right-to-left languages."""
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


def generate_conversation_title(first_message):
    """
    Create a short topic title using AI, in the same language
    as the user's first message.
    """
    try:
        response = groq.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create a short, descriptive chat title based on "
                        "the user's message. Use 2 to 6 words, in the same "
                        "language as the user. Describe the topic, not the "
                        "whole question. Return only the title, without "
                        "quotation marks or explanation."
                    ),
                },
                {
                    "role": "user",
                    "content": first_message,
                },
            ],
            max_tokens=30,
            temperature=0.2,
        )

        title = (
            response.choices[0].message.content or ""
        ).strip().strip("\"'“”")

        title = " ".join(title.split())

        if not title:
            return first_message[:55]

        return title[:55]

    except Exception:
        # If title generation fails, the conversation still works.
        return first_message[:55]


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
        .insert(
            {
                "id": conversation_id,
                "user_id": user_id,
                "title": "محادثة جديدة",
                "created_at": now,
                "updated_at": now,
            }
        )
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

    supabase.table("chat_history").insert(
        {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
        }
    ).execute()

    # Update the conversation's latest activity.
    supabase.table("conversations").update(
        {
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ).eq(
        "id", conversation_id
    ).eq(
        "user_id", user_id
    ).execute()


def update_conversation_title(title):
    user_id = st.session_state.user["id"]
    conversation_id = st.session_state.conversation_id

    supabase.table("conversations").update(
        {
            "title": title[:55],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq(
        "id", conversation_id
    ).eq(
        "user_id", user_id
    ).execute()


def get_current_conversation():
    conversation_id = st.session_state.conversation_id

    for conversation in st.session_state.conversations:
        if conversation["id"] == conversation_id:
            return conversation

    return None


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

    login_tab, signup_tab = st.tabs(
        ["تسجيل الدخول", "إنشاء حساب"]
    )

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
                result = supabase.auth.sign_in_with_password(
                    {
                        "email": login_email.strip(),
                        "password": login_password,
                    }
                )

                if not result.user:
                    st.error("تعذّر تسجيل الدخول.")
                    st.stop()

                st.session_state.user = {
                    "id": str(result.user.id),
                    "email": result.user.email,
                }

                load_conversations()

                if st.session_state.conversations:
                    latest = st.session_state.conversations[0]
                    open_conversation(latest["id"])
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
                    result = supabase.auth.sign_up(
                        {
                            "email": signup_email.strip(),
                            "password": signup_password,
                        }
                    )

                    if result.session and result.user:
                        st.session_state.user = {
                            "id": str(result.user.id),
                            "email": result.user.email,
                        }

                        load_conversations()

                        if not st.session_state.conversations:
                            create_conversation()
                        else:
                            open_conversation(
                                st.session_state.conversations[0]["id"]
                            )

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

    if st.button(
        "＋ محادثة جديدة",
        use_container_width=True,
    ):
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

    # Check whether this is the first message in the conversation.
    is_first_message = len(st.session_state.messages) == 0

    # Display and store the user's message in session state.
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        display_message(prompt)

    try:
        # Save the user message.
        save_message("user", prompt)

        # Generate a descriptive title only once, from the first question.
        if is_first_message:
            title = generate_conversation_title(prompt)
            update_conversation_title(title)

        # Ask the AI using the conversation history.
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

        # Store the AI response.
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        save_message("assistant", answer)

        # Refresh titles and activity order in the sidebar.
        load_conversations()

        st.rerun()

    except Exception as e:
        st.error(
            f"حدث خطأ أثناء معالجة الرسالة: {type(e).__name__}: {e}"
        )
