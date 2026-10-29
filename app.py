
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

st.markdown("""
<style>
.stApp {
    background-color: #0b0f14;
}
[data-testid="stSidebar"] {
    background-color: #10161e;
}
.block-container {
    padding-top: 1.5rem;
}
div[data-testid="stButton"] button {
    border-radius: 9px;
    min-height: 40px;
    white-space: normal;
}
.nexora-title {
    font-size: 30px;
    font-weight: 800;
    color: #65efa4;
}
.nexora-subtitle {
    color: #9aa8b6;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# =====================================
# 2. الاتصال بالخدمات
# =====================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    groq = Groq(api_key=GROQ_API_KEY)

except Exception:
    st.error("تأكد من إعداد SUPABASE_URL وSUPABASE_KEY وGROQ_API_KEY في Secrets.")
    st.stop()

MODEL = "openai/gpt-oss-120b"

# =====================================
# 3. بيانات الجلسة
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


def user_id():
    user = st.session_state.user
    return str(user.id) if user else None


def error_text(error):
    message = str(error)
    if "42501" in message or "row-level security" in message.lower():
        return "Supabase رفض العملية بسبب صلاحيات قاعدة البيانات. افحص سياسات RLS."
    return message


# =====================================
# 4. تسجيل الدخول وإنشاء الحساب
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
    st.markdown('<div class="nexora-title">🤖 NEXORA AI</div>',
                unsafe_allow_html=True)
    st.markdown("مساعدك الذكي", unsafe_allow_html=True)
    st.divider()

    login_tab, signup_tab = st.tabs(["تسجيل الدخول", "إنشاء حساب"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور", type="password")
            login_button = st.form_submit_button("دخول", use_container_width=True)

        if login_button:
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password,
                })

                if not result.user or not result.session:
                    st.error("لم يكتمل تسجيل الدخول.")
                else:
                    st.session_state.user = result.user
                    st.session_state.access_token = result.session.access_token
                    apply_token()
                    st.session_state.conversation_id = None
                    st.session_state.messages = []
                    st.rerun()

            except Exception:
                st.error("تعذّر تسجيل الدخول. افحص البريد وكلمة المرور.")

    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input("البريد الإلكتروني", key="signup_email")
            new_password = st.text_input(
                "كلمة المرور", type="password", key="signup_password"
            )
            signup_button = st.form_submit_button(
                "إنشاء حساب", use_container_width=True
            )

        if signup_button:
            try:
                result = supabase.auth.sign_up({
                    "email": new_email.strip(),
                    "password": new_password,
                })

                if result.user and result.session:
                    st.session_state.user = result.user
                    st.session_state.access_token = result.session.access_token
                    apply_token()
                    st.success("تم إنشاء الحساب.")
                    st.rerun()
                else:
                    st.success("افحص بريدك لتأكيد الحساب، ثم سجّل الدخول.")

            except Exception:
                st.error("تعذّر إنشاء الحساب. افحص البيانات.")

    st.stop()


apply_token()

# =====================================
# 5. إدارة المحادثات
# =====================================
def get_conversations():
    apply_token()
    result = (
        supabase.table("conversations")
        .select("id,user_id,title,created_at,updated_at")
        .eq("user_id", user_id())
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
        "user_id": user_id(),
        "title": "محادثة جديدة",
        "created_at": now,
        "updated_at": now,
    }).execute()

    if not result.data:
        raise Exception("لم يتم إنشاء المحادثة.")

    st.session_state.conversation_id = str(result.data[0]["id"])
    st.session_state.messages = []
    return st.session_state.conversation_id


def get_messages(cid):
    apply_token()
    result = (
        supabase.table("chat_history")
        .select("role,content,created_at")
        .eq("user_id", user_id())
        .eq("conversation_id", cid)
        .order("created_at")
        .execute()
    )
    return [
        {"role": item["role"], "content": item["content"]}
        for item in (result.data or [])
        if item.get("role") in ["user", "assistant"]
    ]


def save_message(cid, role, content):
    apply_token()
    supabase.table("chat_history").insert({
        "user_id": user_id(),
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
    }).eq("id", cid).eq("user_id", user_id()).execute()


def update_activity(cid):
    apply_token()
    supabase.table("conversations").update({
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", cid).eq("user_id", user_id()).execute()


def delete_conversation(cid):
    apply_token()

    # حذف الرسائل التابعة أولًا
    supabase.table("chat_history").delete().eq(
        "user_id", user_id()
    ).eq("conversation_id", cid).execute()

    # ثم حذف المحادثة نفسها
    supabase.table("conversations").delete().eq(
        "user_id", user_id()
    ).eq("id", cid).execute()

    if str(st.session_state.conversation_id) == str(cid):
        st.session_state.conversation_id = None
        st.session_state.messages = []


# =====================================
# 6. إنشاء اسم للمحادثة
# =====================================
def make_title(first_question):
    question = first_question.strip()

    try:
        result = groq.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "اكتب عنوانًا قصيرًا يلخص سؤال المستخدم. "
                        "من 3 إلى 6 كلمات، بنفس لغة السؤال. "
                        "أخرج العنوان فقط دون شرح."
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

    # عنوان احتياطي إذا تعذّر توليد العنوان
    return question[:45] + ("…" if len(question) > 45 else "")


# =====================================
# 7. القائمة الجانبية
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
        conversations = get_conversations()
    except Exception as e:
        st.error("تعذّر تحميل المحادثات.")
        st.caption(error_text(e))
        conversations = []

    for conv in conversations:
        cid = str(conv["id"])
        title = conv.get("title") or "محادثة جديدة"

        # مساحة أكبر لزر الحذف حتى تظهر الكلمة بوضوح
        title_col, delete_col = st.columns([3.5, 1.7], gap="small")

        with title_col:
            label = title[:25] + ("…" if len(title) > 25 else "")
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
                    st.session_state.messages = get_messages(cid)
                    st.rerun()
                except Exception as e:
                    st.error("تعذّر فتح المحادثة.")
                    st.caption(error_text(e))

        with delete_col:
            # كلمة حذف ستظهر حتى لو لم يظهر الإيموجي
            if st.button("🗑 حذف", key=f"delete_{cid}",
                         use_container_width=True):
                st.session_state[f"confirm_{cid}"] = True

        if st.session_state.get(f"confirm_{cid}", False):
            st.warning(f"حذف المحادثة: {title}؟")
            yes_col, no_col = st.columns(2)

            with yes_col:
                if st.button("نعم، احذف", key=f"yes_{cid}"):
                    try:
                        delete_conversation(cid)
                        st.session_state.pop(f"confirm_{cid}", None)
                        st.rerun()
                    except Exception as e:
                        st.error("تعذّر حذف المحادثة.")
                        st.caption(error_text(e))

            with no_col:
                if st.button("إلغاء", key=f"no_{cid}"):
                    st.session_state.pop(f"confirm_{cid}", None)
                    st.rerun()


# =====================================
# 8. واجهة الدردشة
# =====================================
st.markdown('<div class="nexora-title">NEXORA AI</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="nexora-subtitle">اسألني أي شيء.</div>',
    unsafe_allow_html=True,
)
st.divider()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("اكتب رسالتك هنا...")

if prompt and prompt.strip():
    prompt = prompt.strip()

    try:
        # إنشاء المحادثة عند إرسال أول رسالة
        if not st.session_state.conversation_id:
            create_conversation()

        cid = str(st.session_state.conversation_id)
        is_first_message = len(st.session_state.messages) == 0

        # عرض السؤال وحفظه
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)

        with st.chat_message("user"):
            st.markdown(prompt)

        save_message(cid, "user", prompt)

        # الرد على المستخدم
        with st.chat_message("assistant"):
            with st.spinner("NEXORA يفكّر..."):
                result = groq.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are NEXORA AI. Be helpful and concise "
                                "by default. Reply in the user's language. "
                                "Explain technical subjects step by step when "
                                "needed. Never claim an action was completed "
                                "unless it actually was."
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

        assistant_message = {"role": "assistant", "content": answer}
        st.session_state.messages.append(assistant_message)
        save_message(cid, "assistant", answer)

        # إنشاء عنوان بعد أول سؤال، باستخدام السؤال نفسه
        if is_first_message:
            title = make_title(prompt)
            update_title(cid, title)

        update_activity(cid)
        st.rerun()

    except Exception as e:
        st.error("حدث خطأ أثناء حفظ الرسالة أو إنشاء الرد.")
        st.caption(error_text(e))
