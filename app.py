
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone
import uuid

# =========================
# إعدادات التطبيق
# =========================

st.set_page_config(
    page_title="NEXORA AI",
    page_icon="🤖",
    layout="wide",
)

st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        min-width: 245px !important;
        max-width: 245px !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
        padding-left: 0.7rem;
        padding-right: 0.7rem;
    }

    section[data-testid="stSidebar"] div.stButton > button {
        min-height: 34px;
        padding: 0.25rem 0.45rem;
        font-size: 13px;
        border-radius: 8px;
    }

    .main-title {
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        color: #888;
        font-size: 13px;
        margin-top: 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">NEXORA AI 🤖</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Your intelligent assistant</p>', unsafe_allow_html=True)

# =========================
# الاتصال بالخدمات
# =========================

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"],
)

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
أنت NEXORA AI، مساعد ذكي وودود.
أجب بلغة المستخدم نفسها.
اجعل الإجابات قصيرة وواضحة ومفيدة.
إذا طلب المستخدم شرحاً مفصلاً، يمكنك التوسع.
لا تخترع معلومات عندما لا تعرف الإجابة.
"""

# =========================
# حالة التطبيق
# =========================

defaults = {
    "user": None,
    "conversation_id": None,
    "messages": [],
    "conversations": [],
    "title_error": "",
    "delete_candidate": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================
# أدوات مساعدة
# =========================

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_conversations():
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("user_id", st.session_state.user.id)
        .order("updated_at", desc=True)
        .execute()
    )
    st.session_state.conversations = result.data or []


def create_conversation():
    conversation_id = str(uuid.uuid4())

    supabase.table("conversations").insert({
        "id": conversation_id,
        "user_id": st.session_state.user.id,
        "title": "محادثة جديدة",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }).execute()

    st.session_state.conversation_id = conversation_id
    st.session_state.messages = []
    st.session_state.title_error = ""
    st.session_state.delete_candidate = None

    load_conversations()


def load_messages(conversation_id):
    result = (
        supabase.table("chat_history")
        .select("*")
        .eq("user_id", st.session_state.user.id)
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .execute()
    )

    st.session_state.messages = [
        {"role": row["role"], "content": row["content"]}
        for row in (result.data or [])
    ]

    st.session_state.conversation_id = conversation_id
    st.session_state.title_error = ""
    st.session_state.delete_candidate = None


def save_message(role, content):
    supabase.table("chat_history").insert({
        "user_id": st.session_state.user.id,
        "conversation_id": st.session_state.conversation_id,
        "role": role,
        "content": content,
        "created_at": now_iso(),
    }).execute()


# =========================
# عناوين المحادثات الذكية
# =========================

def generate_conversation_title(messages_text):
    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "اقرأ المحادثة كاملة وحدد موضوعها الأساسي. "
                    "أنشئ عنواناً واضحاً ومحدداً من 3 إلى 6 كلمات "
                    "بلغة المستخدم. أخرج العنوان فقط. "
                    "تجنب العناوين العامة مثل محادثة جديدة."
                ),
            },
            {
                "role": "user",
                "content": "المحادثة:\n" + messages_text,
            },
        ],
        temperature=0.2,
        max_tokens=60,
    )

    title = (
        response.choices[0].message.content or ""
    ).strip().strip("\"'` \n")

    title = " ".join(title.split())

    if not title or title.lower() in {
        "محادثة جديدة",
        "new chat",
        "new conversation",
        "untitled",
    }:
        raise ValueError("AI returned an empty or generic title.")

    return title[:100]


def update_conversation_title(title):
    result = (
        supabase.table("conversations")
        .update({
            "title": title,
            "updated_at": now_iso(),
        })
        .eq("id", st.session_state.conversation_id)
        .eq("user_id", st.session_state.user.id)
        .execute()
    )

    if not result.data:
        raise ValueError("لم يتم حفظ العنوان في قاعدة البيانات.")


def refresh_conversation_title():
    messages = st.session_state.messages
    user_messages = [
        message for message in messages
        if message["role"] == "user"
    ]

    if not user_messages:
        return

    # إرسال آخر الرسائل حتى يفهم الذكاء الاصطناعي موضوع المحادثة
    recent_messages = messages[-12:]

    messages_text = "\n".join(
        ("المستخدم: " if m["role"] == "user" else "المساعد: ")
        + m["content"]
        for m in recent_messages
    )

    try:
        title = generate_conversation_title(messages_text)
        update_conversation_title(title)
        st.session_state.title_error = ""

    except Exception as error:
        st.session_state.title_error = (
            f"تعذّر إنشاء العنوان الذكي: {error}"
        )

        # احتياط: استخدام أول سؤال إذا تعذر إنشاء عنوان
        fallback = user_messages[0]["content"].strip()[:55]
        if fallback:
            try:
                update_conversation_title(fallback)
            except Exception as save_error:
                st.session_state.title_error += (
                    f"\nتعذّر حفظ العنوان البديل: {save_error}"
                )


# =========================
# حذف محادثة واحدة
# =========================

def delete_conversation(conversation_id):
    # تأكد أن المحادثة ملك المستخدم الحالي
    owned = (
        supabase.table("conversations")
        .select("id")
        .eq("id", conversation_id)
        .eq("user_id", st.session_state.user.id)
        .execute()
    )

    if not owned.data:
        raise ValueError("المحادثة غير موجودة أو لا تملك صلاحية حذفها.")

    # حذف الرسائل أولاً لتجنب مشكلة المفتاح الخارجي
    (
        supabase.table("chat_history")
        .delete()
        .eq("conversation_id", conversation_id)
        .eq("user_id", st.session_state.user.id)
        .execute()
    )

    (
        supabase.table("conversations")
        .delete()
        .eq("id", conversation_id)
        .eq("user_id", st.session_state.user.id)
        .execute()
    )

    if st.session_state.conversation_id == conversation_id:
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.session_state.title_error = ""

    st.session_state.delete_candidate = None
    load_conversations()


# =========================
# تسجيل الدخول وإنشاء حساب
# =========================

if st.session_state.user is None:
    st.title("مرحباً بك في NEXORA AI")

    login_tab, signup_tab = st.tabs([
        "تسجيل الدخول",
        "إنشاء حساب",
    ])

    with login_tab:
        email = st.text_input("البريد الإلكتروني", key="login_email")
        password = st.text_input(
            "كلمة المرور",
            type="password",
            key="login_password",
        )

        if st.button("دخول", use_container_width=True):
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })

                st.session_state.user = result.user
                load_conversations()
                st.rerun()

            except Exception:
                st.error(
                    "تعذّر تسجيل الدخول. تحقق من البريد وكلمة المرور "
                    "وتأكيد البريد الإلكتروني."
                )

    with signup_tab:
        new_email = st.text_input(
            "البريد الإلكتروني",
            key="signup_email",
        )
        new_password = st.text_input(
            "كلمة المرور",
            type="password",
            key="signup_password",
        )

        if st.button("إنشاء حساب", use_container_width=True):
            try:
                result = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password,
                })

                if result.user and not result.session:
                    st.success(
                        "تم إنشاء الحساب. افحص بريدك لتأكيد الحساب."
                    )
                elif result.user:
                    st.session_state.user = result.user
                    load_conversations()
                    st.rerun()
                else:
                    st.error("لم يتم إنشاء الحساب.")

            except Exception as error:
                st.error(f"تعذّر إنشاء الحساب: {error}")

    st.stop()


# =========================
# القائمة الجانبية المصغرة
# =========================

with st.sidebar:
    st.markdown("### 🤖 NEXORA")
    st.caption(st.session_state.user.email or "")

    if st.button("＋ محادثة جديدة", use_container_width=True):
        try:
            create_conversation()
            st.rerun()
        except Exception as error:
            st.error(f"تعذّر إنشاء المحادثة: {error}")

    st.divider()
    st.markdown("**محادثاتي**")

    if st.button("↻ تحديث القائمة", use_container_width=True):
        try:
            load_conversations()
            st.rerun()
        except Exception as error:
            st.error(f"تعذّر تحميل المحادثات: {error}")

    for conversation in st.session_state.conversations:
        cid = conversation["id"]
        title = conversation.get("title") or "محادثة جديدة"

        # صف صغير: عنوان المحادثة وزر الحذف
        col_chat, col_delete = st.columns([5, 1], gap="small")

        with col_chat:
            if st.button(
                title[:38],
                key=f"open_{cid}",
                use_container_width=True,
                help=title,
            ):
                try:
                    load_messages(cid)
                    st.rerun()
                except Exception as error:
                    st.error(f"تعذّر فتح المحادثة: {error}")

        with col_delete:
            if st.button(
                "🗑️",
                key=f"delete_{cid}",
                help="حذف هذه المحادثة",
            ):
                st.session_state.delete_candidate = cid
                st.rerun()

    if st.session_state.delete_candidate:
        candidate = st.session_state.delete_candidate
        selected = next(
            (
                c for c in st.session_state.conversations
                if c["id"] == candidate
            ),
            None,
        )

        if selected:
            st.warning(
                f"حذف المحادثة «{selected.get('title', 'محادثة')}»؟"
            )

            confirm_col, cancel_col = st.columns(2)

            with confirm_col:
                if st.button(
                    "حذف",
                    key="confirm_delete",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        delete_conversation(candidate)
                        st.success("تم حذف المحادثة.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"تعذّر الحذف: {error}")

            with cancel_col:
                if st.button(
                    "إلغاء",
                    key="cancel_delete",
                    use_container_width=True,
                ):
                    st.session_state.delete_candidate = None
                    st.rerun()

    st.divider()

    if st.button("تسجيل الخروج", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.user = None
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.session_state.conversations = []
        st.session_state.delete_candidate = None
        st.rerun()


# =========================
# واجهة المحادثة
# =========================

if st.session_state.conversation_id is None:
    st.info("ابدأ محادثة جديدة من القائمة الجانبية.")
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.title_error:
        st.warning(st.session_state.title_error)


# =========================
# إرسال الرسائل والرد
# =========================

prompt = st.chat_input("اكتب رسالتك إلى NEXORA AI...")

if prompt:
    try:
        if st.session_state.conversation_id is None:
            create_conversation()

        user_message = {
            "role": "user",
            "content": prompt,
        }

        st.session_state.messages.append(user_message)
        save_message("user", prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("NEXORA AI يفكر..."):
                response = groq_client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        *[
                            {
                                "role": m["role"],
                                "content": m["content"],
                            }
                            for m in st.session_state.messages[-20:]
                        ],
                    ],
                    temperature=0.5,
                    max_tokens=500,
                )

                answer = (
                    response.choices[0].message.content or ""
                ).strip()

                if not answer:
                    answer = "لم أتمكن من إنشاء إجابة. حاول مرة أخرى."

                st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
        })

        save_message("assistant", answer)

        refresh_conversation_title()
        load_conversations()
        st.rerun()

    except Exception as error:
        st.error(f"حدث خطأ: {error}")
