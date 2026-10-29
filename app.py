
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone
import uuid
import re

# =====================================
# 1. إعداد التطبيق
# =====================================
st.set_page_config(
    page_title="NEXORA AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================
# 2. التصميم
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

/* رسائل الدردشة افتراضيًا بدون إطار */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0.6rem 0 !important;
}

/* رسالة المستخدم: إطار أخضر شفاف */
[data-testid="stChatMessage"]:has(
    [data-testid="chatAvatarIcon-user"]
) {
    border: 1px solid rgba(101, 239, 164, 0.28) !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
    background: rgba(101, 239, 164, 0.035) !important;
    margin: 8px 0 !important;
}

/* لا نضيف إطارًا حول محتوى الرسائل */
[data-testid="stChatMessage"] > div {
    box-shadow: none !important;
}

/* اسم التطبيق */
.nexora-title {
    font-size: 30px;
    font-weight: 800;
    color: #65efa4;
    margin-bottom: 0;
}

.nexora-subtitle {
    color: #9aa8b6;
    font-size: 14px;
}

/* أزرار أسماء المحادثات والحذف بلا إطار */
div[class*="st-key-open_"] button,
div[class*="st-key-delete_"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #e8edf2 !important;
    padding: 5px 3px !important;
    min-height: 35px !important;
}

div[class*="st-key-open_"] button:hover {
    color: #65efa4 !important;
    background: transparent !important;
}

div[class*="st-key-delete_"] button {
    color: #ff7777 !important;
}

div[class*="st-key-delete_"] button:hover {
    color: #ff4444 !important;
    background: transparent !important;
}

/* حقل كتابة الرسالة */
[data-testid="stChatInput"] {
    border-radius: 14px;
}

h1, h2, h3 {
    color: #65efa4;
}
</style>
""", unsafe_allow_html=True)

# =====================================
# 3. الاتصال بالخدمات
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
# 4. بيانات الجلسة
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
# 5. تسجيل الدخول وإنشاء الحساب
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


if not st.session_state.user:
    st.markdown(
        '<div class="nexora-title">🤖 NEXORA AI</div>',
        unsafe_allow_html=True,
    )
    st.markdown("مساعدك الذكي")

    login_tab, signup_tab = st.tabs(
        ["تسجيل الدخول", "إنشاء حساب"]
    )

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور", type="password")
            submitted = st.form_submit_button(
                "دخول", use_container_width=True
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
                st.error("فشل تسجيل الدخول. افحص البريد وكلمة المرور.")

    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input(
                "البريد الإلكتروني", key="signup_email"
            )
            new_password = st.text_input(
                "كلمة المرور",
                type="password",
                key="signup_password",
            )
            signup = st.form_submit_button(
                "إنشاء حساب", use_container_width=True
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
                    st.success("تم إنشاء الحساب.")
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
# 6. إدارة المحادثات
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
    }).eq("id", cid).eq("user_id", get_user_id()).execute()


def update_activity(cid):
    apply_token()
    supabase.table("conversations").update({
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", cid).eq("user_id", get_user_id()).execute()


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


# =====================================
# 7. توليد عنوان المحادثة
# =====================================
def generate_title(question):
    try:
        result = groq.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Write a short title of 3 to 6 words "
                        "summarizing the user's question. Use the "
                        "same language as the user. Return only the title."
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
# 8. القائمة الجانبية
# =====================================
with st.sidebar:
    st.markdown("## 🤖 NEXORA AI")
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
                        st.session_state.pop(f"confirm_{cid}", None)
                        st.rerun()
                    except Exception as e:
                        show_error(e)

            with no_col:
                if st.button("إلغاء", key=f"no_{cid}"):
                    st.session_state.pop(f"confirm_{cid}", None)
                    st.rerun()


# =====================================
# 9. واجهة المحادثة
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
        is_first_message = len(st.session_state.messages) == 0

        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)

        with st.chat_message("user", avatar=None):
            st.markdown(prompt)

        save_message(cid, "user", prompt)

        with st.chat_message("assistant", avatar=None):
            with st.spinner("NEXORA يفكّر..."):
                result = groq.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are NEXORA AI. Be helpful and concise. "
                                "Reply in the user's language. Explain "
                                "technical subjects step by step when needed."
                            ),
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

        if is_first_message:
            title = generate_title(prompt)
            update_title(cid, title)

        update_activity(cid)
        st.rerun()

    except Exception as e:
        st.error("حدث خطأ أثناء إرسال الرسالة أو حفظها.")
        show_error(e)
