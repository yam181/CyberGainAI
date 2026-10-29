import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone
import uuid
import re

# =====================================
# إعداد التطبيق
# =====================================
st.set_page_config(
    page_title="NEXORA AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================
# التصميم
# =====================================
st.markdown("""
<style>
.stApp {
    background: #0b0f14;
    color: #e8edf2;
}

.block-container {
    padding-top: 1.4rem;
    max-width: 1100px;
}

[data-testid="stSidebar"] {
    background: #10161e;
    border-right: none !important;
}

/* إخفاء صور وأيقونات الرسائل */
[data-testid="stChatMessageAvatar"],
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"],
[data-testid*="chatAvatarIcon"] {
    display: none !important;
}

/* إخفاء مساحة الأفاتار */
[data-testid="stChatMessage"] > div:first-child {
    display: none !important;
}

/* الرسائل بلا إطار افتراضيًا */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 8px 0 !important;
    margin: 8px 0 !important;
}

/* إطار رمادي شفاف لرسالة المستخدم */
[data-testid="stChatMessage"]:has(
    [data-testid="chatAvatarIcon-user"]
) {
    background: rgba(160, 160, 160, 0.08) !important;
    border: 1px solid rgba(180, 180, 180, 0.25) !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
}

/* عنوان التطبيق */
.nexora-title {
    font-size: 24px;
    font-weight: 700;
    color: #9D4EDD;
    margin-bottom: 0;
    letter-spacing: 1px;
}

.nexora-subtitle {
    color: #9aa8b6;
    font-size: 14px;
}

/* أزرار المحادثات */
div[class*="st-key-open_"] button,
div[class*="st-key-delete_"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #e8edf2 !important;
    padding: 5px 3px !important;
}

div[class*="st-key-open_"] button:hover {
    color: #65efa4 !important;
}

div[class*="st-key-delete_"] button {
    color: #ff7777 !important;
}

div[class*="st-key-delete_"] button:hover {
    color: #ff4444 !important;
}

[data-testid="stChatInput"] {
    border-radius: 14px;
}

h1, h2, h3 {
    color: #9D4EDD;
}
</style>
""", unsafe_allow_html=True)

# =====================================
# الاتصال بالخدمات
# =====================================
try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )
    groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("افحص إعدادات Secrets في Streamlit Cloud.")
    st.stop()

MODEL = "openai/gpt-oss-120b"

# =====================================
# هوية NEXORA AI والمؤسس
# =====================================
SYSTEM_PROMPT = """
You are NEXORA AI, a helpful AI assistant.

IMPORTANT FOUNDER IDENTITY RULES:
- The founder and creator of NEXORA AI is Yamin Zoabi.
- The name must ALWAYS be written exactly as "Yamin Zoabi" in English.
- Whenever anyone asks who founded, created, developed, or owns NEXORA AI,
  clearly identify the founder as Yamin Zoabi.
- This rule applies regardless of the language used in the question.
- Reply in the user's language, but keep the founder's name in English
  as "Yamin Zoabi".
- Do not invent another founder or change the spelling of the name.
- If asked who made NEXORA AI, say that it was created by Yamin Zoabi.

GENERAL RULES:
- Be helpful, clear, and concise.
- Reply in the same language as the user whenever possible.
- Explain technical subjects step by step when needed.
- Do not claim to have personal experiences.
"""

# =====================================
# حالة الجلسة
# =====================================
defaults = {
    "user": None,
    "access_token": None,
    "conversation_id": None,
    "messages": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def apply_token():
    token = st.session_state.access_token
    if token:
        supabase.postgrest.auth(token)


def get_user_id():
    user = st.session_state.user
    return str(user.id) if user else None


def show_error(error):
    message = str(error)
    if "42501" in message or "row-level security" in message.lower():
        st.error("رفضت Supabase العملية بسبب صلاحيات RLS.")
    else:
        st.error(message)


# =====================================
# تسجيل الخروج
# =====================================
def logout():
    try:
        apply_token()
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.conversation_id = None
    st.session_state.messages = []
    st.rerun()


# =====================================
# تسجيل الدخول وإنشاء حساب
# =====================================
if not st.session_state.user:
    st.markdown(
        '<div class="nexora-title">NEXORA AI</div>',
        unsafe_allow_html=True,
    )
    st.caption("مساعدك الذكي")

    login_tab, signup_tab = st.tabs(
        ["تسجيل الدخول", "إنشاء حساب"]
    )

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input(
                "كلمة المرور",
                type="password",
            )
            submitted = st.form_submit_button(
                "دخول",
                use_container_width=True,
            )

        if submitted:
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password,
                })

                if result.user and result.session:
                    st.session_state.user = result.user
                    st.session_state.access_token = (
                        result.session.access_token
                    )
                    apply_token()
                    st.session_state.conversation_id = None
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error("لم يكتمل تسجيل الدخول.")
            except Exception:
                st.error(
                    "فشل تسجيل الدخول. افحص البريد وكلمة المرور."
                )

    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input(
                "البريد الإلكتروني",
                key="signup_email",
            )
            new_password = st.text_input(
                "كلمة المرور",
                type="password",
                key="signup_password",
            )
            signup = st.form_submit_button(
                "إنشاء حساب",
                use_container_width=True,
            )

        if signup:
            try:
                result = supabase.auth.sign_up({
                    "email": new_email.strip(),
                    "password": new_password,
                })

                if result.user and result.session:
                    st.session_state.user = result.user
                    st.session_state.access_token = (
                        result.session.access_token
                    )
                    apply_token()
                    st.rerun()
                else:
                    st.success(
                        "افحص بريدك لتأكيد الحساب، ثم سجّل الدخول."
                    )
            except Exception:
                st.error("تعذّر إنشاء الحساب.")

    st.stop()

apply_token()

# =====================================
# المحادثات
# =====================================
def list_conversations():
    apply_token()
    result = (
        supabase.table("conversations")
        .select("id,user_id,title,created_at,updated_at")
        .eq("user_id", get_user_id())
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data or []


def create_conversation():
    apply_token()
    now = datetime.now(timezone.utc).isoformat()
    cid = str(uuid.uuid4())

    result = supabase.table("conversations").insert({
        "id": cid,
        "user_id": get_user_id(),
        "title": "محادثة جديدة",
        "created_at": now,
        "updated_at": now,
    }).execute()

    if not result.data:
        raise Exception("لم يتم إنشاء المحادثة.")

    st.session_state.conversation_id = str(result.data[0]["id"])
    st.session_state.messages = []
    return st.session_state.conversation_id


def load_messages(cid):
    apply_token()
    result = (
        supabase.table("chat_history")
        .select("role,content,created_at")
        .eq("user_id", get_user_id())
        .eq("conversation_id", cid)
        .order("created_at")
        .execute()
    )

    return [
        {"role": row["role"], "content": row["content"]}
        for row in (result.data or [])
        if row.get("role") in ("user", "assistant")
    ]


def save_message(cid, role, content):
    apply_token()
    supabase.table("chat_history").insert({
        "user_id": get_user_id(),
        "conversation_id": cid,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def update_title(cid, title):
    apply_token()
    supabase.table("conversations").update({
        "title": title,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", cid).eq(
        "user_id", get_user_id()
    ).execute()


def update_activity(cid):
    apply_token()
    supabase.table("conversations").update({
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", cid).eq(
        "user_id", get_user_id()
    ).execute()


def delete_conversation(cid):
    apply_token()

    supabase.table("chat_history").delete().eq(
        "user_id", get_user_id()
    ).eq("conversation_id", cid).execute()

    supabase.table("conversations").delete().eq(
        "id", cid
    ).eq("user_id", get_user_id()).execute()

    if str(st.session_state.conversation_id) == str(cid):
        st.session_state.conversation_id = None
        st.session_state.messages = []


def generate_title(question):
    try:
        result = groq.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create a short title of 3 to 6 words "
                        "in the same language as the user's question. "
                        "Return only the title."
                    ),
                },
                {"role": "user", "content": question},
            ],
            max_tokens=40,
            temperature=0.2,
        )

        title = (result.choices[0].message.content or "").strip()
        title = title.strip("\"'`“” ")
        title = re.sub(r"\s+", " ", title)

        if title:
            return title[:80]
    except Exception:
        pass

    return question[:45] + ("…" if len(question) > 45 else "")


# =====================================
# القائمة الجانبية
# =====================================
with st.sidebar:
    st.markdown("## NEXORA AI")
    st.caption("Your AI assistant")

    email = getattr(st.session_state.user, "email", None)
    if email:
        st.caption(email)

    if st.button("＋ محادثة جديدة", use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    if st.button("تسجيل الخروج", use_container_width=True):
        logout()

    st.divider()
    st.markdown("### محادثاتي")

    try:
        conversations = list_conversations()
    except Exception as e:
        show_error(e)
        conversations = []

    for conv in conversations:
        cid = str(conv["id"])
        title = conv.get("title") or "محادثة جديدة"

        name_col, trash_col = st.columns([5, 1], gap="small")

        with name_col:
            label = title[:27] + ("…" if len(title) > 27 else "")
            if st.button(
                label,
                key=f"open_{cid}",
                use_container_width=True,
                type="tertiary",
            ):
                try:
                    st.session_state.conversation_id = cid
                    st.session_state.messages = load_messages(cid)
                    st.rerun()
                except Exception as e:
                    show_error(e)

        with trash_col:
            if st.button(
                "🗑️",
                key=f"delete_{cid}",
                help="حذف المحادثة",
                type="tertiary",
            ):
                st.session_state[f"confirm_{cid}"] = True

        if st.session_state.get(f"confirm_{cid}", False):
            st.caption(f"حذف «{title}»؟")
            yes_col, no_col = st.columns(2)

            with yes_col:
                if st.button("نعم", key=f"yes_{cid}"):
                    try:
                        delete_conversation(cid)
                        st.session_state.pop(
                            f"confirm_{cid}", None
                        )
                        st.rerun()
                    except Exception as e:
                        show_error(e)

            with no_col:
                if st.button("إلغاء", key=f"no_{cid}"):
                    st.session_state.pop(
                        f"confirm_{cid}", None
                    )
                    st.rerun()


# =====================================
# واجهة المحادثة
# =====================================
st.markdown(
    '<div class="nexora-title">NEXORA AI</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="nexora-subtitle">مساعدك الذكي</div>',
    unsafe_allow_html=True,
)
st.divider()

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=None):
        st.markdown(message["content"])

prompt = st.chat_input("اكتب رسالتك هنا...")

if prompt and prompt.strip():
    prompt = prompt.strip()

    try:
        if not st.session_state.conversation_id:
            create_conversation()

        cid = str(st.session_state.conversation_id)
        first_message = len(st.session_state.messages) == 0

        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
        })

        save_message(cid, "user", prompt)

        with st.chat_message("user", avatar=None):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=None):
            with st.spinner("NEXORA يفكّر..."):
                result = groq.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        *st.session_state.messages[-12:],
                    ],
                    temperature=0.5,
                    max_tokens=700,
                )

                answer = (
                    result.choices[0].message.content or
                    "عذرًا، لم أتمكن من إنشاء رد."
                ).strip()

                st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
        })

        save_message(cid, "assistant", answer)

        if first_message:
            update_title(cid, generate_title(prompt))

        update_activity(cid)
        st.rerun()

    except Exception as e:
        st.error("حدث خطأ أثناء إرسال الرسالة أو حفظها.")
        show_error(e)
