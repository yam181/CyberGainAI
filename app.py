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
# حالة الجلسة
# =====================================
defaults = {
    "user": None,
    "access_token": None,
    "refresh_token": None,
    "conversation_id": None,
    "messages": [],
    "language": "ar",
    "theme": "dark",
    "temperature": 0.5,
    "max_tokens": 700,
    "show_settings": False,
    "profile_image": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =====================================
# الترجمة
# =====================================
TRANSLATIONS = {
    "ar": {
        "app_title": "NEXORA AI",
        "subtitle": "مساعدك الذكي",
        "login": "تسجيل الدخول",
        "signup": "إنشاء حساب",
        "email": "البريد الإلكتروني",
        "password": "كلمة المرور",
        "login_btn": "دخول",
        "signup_btn": "إنشاء حساب",
        "logout": "تسجيل الخروج",
        "new_chat": "＋ محادثة جديدة",
        "my_chats": "محادثاتي",
        "delete_confirm": "حذف «{title}»؟",
        "yes": "نعم",
        "cancel": "إلغاء",
        "chat_placeholder": "اكتب رسالتك هنا...",
        "thinking": "NEXORA يفكّر...",
        "settings": "الإعدادات",
        "profile": "الملف الشخصي",
        "delete_account": "حذف الحساب",
        "about": "حول التطبيق",
        "privacy": "الخصوصية",
        "chat_settings": "إعدادات المحادثة",
        "language": "اللغة",
        "theme": "الوضع",
        "dark": "داكن",
        "light": "فاتح",
        "temperature": "درجة الإبداع",
        "max_tokens": "أقصى طول للرد",
        "save_settings": "حفظ الإعدادات",
        "delete_account_confirm": "هل أنت متأكد من حذف حسابك نهائياً؟ سيتم حذف جميع محادثاتك.",
        "about_text": "NEXORA AI هو مساعد ذكي تم تطويره بواسطة Yamin Zoabi. يوفر محادثات ذكية مع حفظ السجل بشكل آمن.",
        "privacy_text": "نحن نحترم خصوصيتك. يتم تخزين المحادثات بشكل آمن في قاعدة بيانات محمية، ولا يتم مشاركة بياناتك مع أي طرف ثالث.",
        "no_conversations": "لا توجد محادثات بعد",
        "error_login": "فشل تسجيل الدخول. افحص البريد وكلمة المرور.",
        "error_signup": "تعذّر إنشاء الحساب.",
        "check_email": "افحص بريدك لتأكيد الحساب، ثم سجّل الدخول.",
        "secrets_error": "افحص إعدادات Secrets في Streamlit Cloud.",
        "close": "إغلاق",
        "arabic": "العربية",
        "english": "English",
    },
    "en": {
        "app_title": "NEXORA AI",
        "subtitle": "Your AI assistant",
        "login": "Login",
        "signup": "Sign Up",
        "email": "Email",
        "password": "Password",
        "login_btn": "Login",
        "signup_btn": "Create Account",
        "logout": "Logout",
        "new_chat": "＋ New Chat",
        "my_chats": "My Chats",
        "delete_confirm": "Delete «{title}»?",
        "yes": "Yes",
        "cancel": "Cancel",
        "chat_placeholder": "Type your message...",
        "thinking": "NEXORA is thinking...",
        "settings": "Settings",
        "profile": "Profile",
        "delete_account": "Delete Account",
        "about": "About",
        "privacy": "Privacy",
        "chat_settings": "Chat Settings",
        "language": "Language",
        "theme": "Theme",
        "dark": "Dark",
        "light": "Light",
        "temperature": "Creativity",
        "max_tokens": "Max response length",
        "save_settings": "Save Settings",
        "delete_account_confirm": "Are you sure you want to permanently delete your account? All conversations will be deleted.",
        "about_text": "NEXORA AI is a smart assistant developed by Yamin Zoabi. It provides intelligent conversations with secure history storage.",
        "privacy_text": "We respect your privacy. Conversations are stored securely in a protected database and your data is never shared with third parties.",
        "no_conversations": "No conversations yet",
        "error_login": "Login failed. Check email and password.",
        "error_signup": "Could not create account.",
        "check_email": "Check your email to confirm the account, then log in.",
        "secrets_error": "Check Secrets settings in Streamlit Cloud.",
        "close": "Close",
        "arabic": "العربية",
        "english": "English",
    },
}

def t(key, **kwargs):
    lang = st.session_state.language
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

# =====================================
# التصميم
# =====================================
def get_css():
    if st.session_state.theme == "dark":
        return """
        <style>
        .stApp { background: #0b0f14; color: #e8edf2; }
        .block-container { padding-top: 1.2rem; max-width: 1100px; }
        [data-testid="stSidebar"] { background: #10161e; border-right: none !important; }

        [data-testid="stChatMessageAvatar"],
        [data-testid="chatAvatarIcon-user"],
        [data-testid="chatAvatarIcon-assistant"],
        [data-testid*="chatAvatarIcon"] { display: none !important; }

        [data-testid="stChatMessage"] > div:first-child { display: none !important; }

        [data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 8px 0 !important;
            margin: 8px 0 !important;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background: rgba(157, 78, 221, 0.08) !important;
            border: 1px solid rgba(157, 78, 221, 0.25) !important;
            border-radius: 14px !important;
            padding: 12px 16px !important;
        }

        .nexora-title {
            display: block !important;
            font-size: 24px !important;
            font-weight: 700 !important;
            color: #9D4EDD !important;
            line-height: 2 !important;
            height: auto !important;
            min-height: 48px !important;
            padding: 8px 0 !important;
            margin: 0 !important;
            overflow: visible !important;
            white-space: normal !important;
        }
        .nexora-subtitle { color: #9aa8b6; font-size: 14px; }

        div[class*="st-key-open_"] button,
        div[class*="st-key-delete_"] button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #e8edf2 !important;
            padding: 5px 3px !important;
        }
        div[class*="st-key-open_"] button:hover { color: #c77dff !important; }
        div[class*="st-key-delete_"] button { color: #ff7777 !important; }
        div[class*="st-key-delete_"] button:hover { color: #ff4444 !important; }

        [data-testid="stChatInput"] {
            border-radius: 14px !important;
            border: 1px solid #3a2a4f !important;
        }
        [data-testid="stChatInput"] > div {
            border-color: #3a2a4f !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: #9D4EDD !important;
            box-shadow: 0 0 0 1px #9D4EDD !important;
        }
        [data-testid="stChatInput"] textarea {
            color: #e8edf2 !important;
        }

        .stButton > button {
            border-radius: 10px !important;
        }
        .stButton > button[kind="primary"] {
            background-color: #9D4EDD !important;
            border-color: #9D4EDD !important;
            color: white !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #7b2cbf !important;
            border-color: #7b2cbf !important;
        }
        .stButton > button[kind="secondary"] {
            border-color: #3a2a4f !important;
            color: #e8edf2 !important;
        }

        h1, h2, h3 { color: #9D4EDD; }

        /* جعل لوحة الإعدادات أصغر على الموبايل */
        @media (max-width: 768px) {
            .block-container { padding: 0.5rem !important; }
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        [data-testid="stStatusWidget"] {display: none !important;}
        .stDeployButton {display: none !important;}
        </style>
        """
    else:
        return """
        <style>
        .stApp { background: #f7f9fc; color: #1a1a1a; }
        .block-container { padding-top: 1.2rem; max-width: 1100px; }
        [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e0e0e0 !important; }

        [data-testid="stChatMessageAvatar"],
        [data-testid="chatAvatarIcon-user"],
        [data-testid="chatAvatarIcon-assistant"],
        [data-testid*="chatAvatarIcon"] { display: none !important; }

        [data-testid="stChatMessage"] > div:first-child { display: none !important; }

        [data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 8px 0 !important;
            margin: 8px 0 !important;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background: rgba(123, 44, 191, 0.06) !important;
            border: 1px solid rgba(123, 44, 191, 0.15) !important;
            border-radius: 14px !important;
            padding: 12px 16px !important;
        }

        .nexora-title {
            display: block !important;
            font-size: 24px !important;
            font-weight: 700 !important;
            color: #7B2CBF !important;
            line-height: 2 !important;
            height: auto !important;
            min-height: 48px !important;
            padding: 8px 0 !important;
            margin: 0 !important;
            overflow: visible !important;
            white-space: normal !important;
        }
        .nexora-subtitle { color: #555; font-size: 14px; }

        div[class*="st-key-open_"] button,
        div[class*="st-key-delete_"] button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #1a1a1a !important;
            padding: 5px 3px !important;
        }
        div[class*="st-key-open_"] button:hover { color: #7B2CBF !important; }
        div[class*="st-key-delete_"] button { color: #c62828 !important; }
        div[class*="st-key-delete_"] button:hover { color: #b71c1c !important; }

        [data-testid="stChatInput"] {
            border-radius: 14px !important;
            border: 1px solid #d0c4e0 !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: #7B2CBF !important;
            box-shadow: 0 0 0 1px #7B2CBF !important;
        }

        .stButton > button[kind="primary"] {
            background-color: #7B2CBF !important;
            border-color: #7B2CBF !important;
            color: white !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #5a189a !important;
            border-color: #5a189a !important;
        }

        h1, h2, h3 { color: #7B2CBF; }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        [data-testid="stStatusWidget"] {display: none !important;}
        .stDeployButton {display: none !important;}
        </style>
        """

st.markdown(get_css(), unsafe_allow_html=True)

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
    st.error(t("secrets_error"))
    st.stop()

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
You are NEXORA AI, a helpful AI assistant.

IMPORTANT FOUNDER IDENTITY RULES:
- The founder and creator of NEXORA AI is Yamin Zoabi.
- The name must ALWAYS be written exactly as "Yamin Zoabi" in English.
- Birth date of the founder is 25/12/2007.
- Whenever anyone asks who founded, created, developed, invented, or owns NEXORA AI,
  clearly identify the founder as Yamin Zoabi and mention his birth date 25/12/2007.
- This rule applies regardless of the language used in the question.
- Reply in the user's language, but keep the founder's name in English as "Yamin Zoabi".
- Do not invent another founder or change the spelling of the name.
- If asked who made NEXORA AI, say that it was created by Yamin Zoabi (born 25/12/2007).

GENERAL RULES:
- Be helpful, clear, and concise.
- Reply in the same language as the user whenever possible.
- Explain technical subjects step by step when needed.
- Do not claim to have personal experiences.
"""

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

def logout():
    try:
        apply_token()
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.conversation_id = None
    st.session_state.messages = []
    st.session_state.show_settings = False
    st.rerun()

def delete_account():
    try:
        apply_token()
        uid = get_user_id()
        if uid:
            supabase.table("chat_history").delete().eq("user_id", uid).execute()
            supabase.table("conversations").delete().eq("user_id", uid).execute()
        logout()
    except Exception as e:
        show_error(e)

def is_founder_question(text):
    text = text.lower()
    keywords = [
        "مخترع", "مؤسس", "من عمل", "من صنع", "من طور", "من أنشأ",
        "founder", "creator", "who made", "who created", "who developed",
        "who invented", "inventor", "owner"
    ]
    return any(k in text for k in keywords)

# =====================================
# محاولة استعادة الجلسة (تسجيل دخول محفوظ)
# =====================================
if st.session_state.access_token and not st.session_state.user:
    try:
        # محاولة استعادة الجلسة
        if st.session_state.refresh_token:
            supabase.auth.set_session(st.session_state.access_token, st.session_state.refresh_token)
        user = supabase.auth.get_user()
        if user and user.user:
            st.session_state.user = user.user
            apply_token()
    except Exception:
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user = None

# =====================================
# تسجيل الدخول
# =====================================
if not st.session_state.user:
    st.markdown(f'<div class="nexora-title">{t("app_title")}</div>', unsafe_allow_html=True)
    st.caption(t("subtitle"))

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🌐 " + ("EN" if st.session_state.language == "ar" else "ع"), use_container_width=True):
            st.session_state.language = "en" if st.session_state.language == "ar" else "ar"
            st.rerun()
    with col2:
        if st.button("🌙" if st.session_state.theme == "light" else "☀️", use_container_width=True):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()

    login_tab, signup_tab = st.tabs([t("login"), t("signup")])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input(t("email"))
            password = st.text_input(t("password"), type="password")
            submitted = st.form_submit_button(t("login_btn"), use_container_width=True)

        if submitted:
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password,
                })
                if result.user and result.session:
                    st.session_state.user = result.user
                    st.session_state.access_token = result.session.access_token
                    st.session_state.refresh_token = result.session.refresh_token
                    apply_token()
                    st.session_state.conversation_id = None
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error(t("error_login"))
            except Exception:
                st.error(t("error_login"))

    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input(t("email"), key="signup_email")
            new_password = st.text_input(t("password"), type="password", key="signup_password")
            signup = st.form_submit_button(t("signup_btn"), use_container_width=True)

        if signup:
            try:
                result = supabase.auth.sign_up({
                    "email": new_email.strip(),
                    "password": new_password,
                })
                if result.user and result.session:
                    st.session_state.user = result.user
                    st.session_state.access_token = result.session.access_token
                    st.session_state.refresh_token = result.session.refresh_token
                    apply_token()
                    st.rerun()
                else:
                    st.success(t("check_email"))
            except Exception:
                st.error(t("error_signup"))

    st.stop()

apply_token()

# =====================================
# دوال المحادثات
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
        "title": "محادثة جديدة" if st.session_state.language == "ar" else "New Chat",
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
    supabase.table("chat_history").delete().eq("user_id", get_user_id()).eq("conversation_id", cid).execute()
    supabase.table("conversations").delete().eq("id", cid).eq("user_id", get_user_id()).execute()
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

def process_uploaded_files(files):
    parts = []
    for f in files:
        name = f.name
        if f.type and f.type.startswith("image/"):
            parts.append(f"[صورة مرفقة: {name}]")
        elif name.lower().endswith((".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css")):
            try:
                content = f.getvalue().decode("utf-8", errors="ignore")
                parts.append(f"[ملف {name}]\n{content[:3000]}")
            except Exception:
                parts.append(f"[ملف {name} - تعذر قراءة المحتوى]")
        else:
            parts.append(f"[ملف مرفق: {name}]")
    return "\n\n".join(parts)

# =====================================
# القائمة الجانبية
# =====================================
with st.sidebar:
    st.markdown(f"## {t('app_title')}")
    st.caption(t("subtitle"))

    email = getattr(st.session_state.user, "email", None)
    if email:
        st.caption(email)

    if st.button(t("new_chat"), use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown(f"### {t('my_chats')}")

    try:
        conversations = list_conversations()
    except Exception as e:
        show_error(e)
        conversations = []

    if not conversations:
        st.caption(t("no_conversations"))

    for conv in conversations:
        cid = str(conv["id"])
        title = conv.get("title") or ("محادثة جديدة" if st.session_state.language == "ar" else "New Chat")

        name_col, trash_col = st.columns([5, 1], gap="small")

        with name_col:
            label = title[:27] + ("…" if len(title) > 27 else "")
            if st.button(label, key=f"open_{cid}", use_container_width=True, type="tertiary"):
                try:
                    st.session_state.conversation_id = cid
                    st.session_state.messages = load_messages(cid)
                    st.rerun()
                except Exception as e:
                    show_error(e)

        with trash_col:
            if st.button("🗑️", key=f"delete_{cid}", help="حذف", type="tertiary"):
                st.session_state[f"confirm_{cid}"] = True

        if st.session_state.get(f"confirm_{cid}", False):
            st.caption(t("delete_confirm", title=title))
            yes_col, no_col = st.columns(2)
            with yes_col:
                if st.button(t("yes"), key=f"yes_{cid}"):
                    try:
                        delete_conversation(cid)
                        st.session_state.pop(f"confirm_{cid}", None)
                        st.rerun()
                    except Exception as e:
                        show_error(e)
            with no_col:
                if st.button(t("cancel"), key=f"no_{cid}"):
                    st.session_state.pop(f"confirm_{cid}", None)
                    st.rerun()

# =====================================
# شريط العنوان
# =====================================
top_col1, top_col2 = st.columns([8, 1.5])

with top_col1:
    st.markdown(f'<div class="nexora-title">{t("app_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="nexora-subtitle">{t("subtitle")}</div>', unsafe_allow_html=True)

with top_col2:
    if st.button("⚙️ " + t("settings"), use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()

st.divider()

# =====================================
# المحتوى + لوحة الإعدادات (صغيرة على اليمين)
# =====================================
if st.session_state.show_settings:
    main_col, settings_col = st.columns([4, 1], gap="small")   # أصغر من قبل
else:
    main_col = st.container()
    settings_col = None

with main_col:
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=None):
            st.markdown(message["content"])
            if message["role"] == "assistant" and st.session_state.profile_image:
                if any(k in message["content"].lower() for k in ["yamin zoabi", "25/12/2007", "مؤسس", "مخترع"]):
                    st.image(st.session_state.profile_image, width=280)

# لوحة الإعدادات (صغيرة)
if st.session_state.show_settings and settings_col is not None:
    with settings_col:
        st.markdown(f"### {t('settings')}")

        if st.button("✕ " + t("close"), use_container_width=True):
            st.session_state.show_settings = False
            st.rerun()

        st.divider()

        # اللغة
        st.markdown(f"**{t('language')}**")
        if st.button(t("arabic"), use_container_width=True, type="primary" if st.session_state.language == "ar" else "secondary"):
            st.session_state.language = "ar"
            st.rerun()
        if st.button(t("english"), use_container_width=True, type="primary" if st.session_state.language == "en" else "secondary"):
            st.session_state.language = "en"
            st.rerun()

        st.divider()

        # الوضع
        st.markdown(f"**{t('theme')}**")
        if st.button("🌙 " + t("dark"), use_container_width=True, type="primary" if st.session_state.theme == "dark" else "secondary"):
            st.session_state.theme = "dark"
            st.rerun()
        if st.button("☀️ " + t("light"), use_container_width=True, type="primary" if st.session_state.theme == "light" else "secondary"):
            st.session_state.theme = "light"
            st.rerun()

        st.divider()

        # الملف الشخصي (بدون رفع صور)
        st.markdown(f"**{t('profile')}**")
        st.caption(email)

        st.divider()

        with st.expander(t("chat_settings"), expanded=False):
            temp = st.slider(t("temperature"), 0.0, 1.0, st.session_state.temperature, 0.1)
            tokens = st.slider(t("max_tokens"), 200, 2000, st.session_state.max_tokens, 50)
            if st.button(t("save_settings")):
                st.session_state.temperature = temp
                st.session_state.max_tokens = tokens
                st.success("✓")

        with st.expander(t("about"), expanded=False):
            st.markdown(t("about_text"))
            st.caption("Founder: Yamin Zoabi | Born: 25/12/2007")

        with st.expander(t("privacy"), expanded=False):
            st.markdown(t("privacy_text"))

        st.divider()

        if st.button(t("delete_account"), type="primary", use_container_width=True):
            st.session_state["confirm_delete_account"] = True

        if st.session_state.get("confirm_delete_account", False):
            st.warning(t("delete_account_confirm"))
            c1, c2 = st.columns(2)
            with c1:
                if st.button(t("yes"), key="confirm_del_yes"):
                    delete_account()
            with c2:
                if st.button(t("cancel"), key="confirm_del_no"):
                    st.session_state["confirm_delete_account"] = False
                    st.rerun()

        st.divider()

        if st.button(t("logout"), use_container_width=True):
            logout()

# =====================================
# خانة الكتابة في الأسفل
# =====================================
prompt = st.chat_input(
    t("chat_placeholder"),
    accept_file="multiple",
)

if prompt:
    if hasattr(prompt, "text"):
        user_text = prompt.text.strip() if prompt.text else ""
        files = prompt.files if prompt.files else []
    else:
        user_text = str(prompt).strip()
        files = []

    if not user_text and not files:
        st.stop()

    final_prompt = user_text
    if files:
        extra = process_uploaded_files(files)
        if extra:
            final_prompt = f"{user_text}\n\n---\n{extra}" if user_text else extra

    try:
        if not st.session_state.conversation_id:
            create_conversation()

        cid = str(st.session_state.conversation_id)
        first_message = len(st.session_state.messages) == 0

        st.session_state.messages.append({"role": "user", "content": final_prompt})
        save_message(cid, "user", final_prompt)

        with st.chat_message("user", avatar=None):
            st.markdown(final_prompt)

        with st.chat_message("assistant", avatar=None):
            with st.spinner(t("thinking")):
                result = groq.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *st.session_state.messages[-12:],
                    ],
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.max_tokens,
                )
                answer = (result.choices[0].message.content or "عذرًا، لم أتمكن من إنشاء رد.").strip()
                st.markdown(answer)

                if is_founder_question(final_prompt) and st.session_state.profile_image:
                    st.image(st.session_state.profile_image, width=280)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        save_message(cid, "assistant", answer)

        if first_message:
            update_title(cid, generate_title(final_prompt))

        update_activity(cid)
        st.rerun()

    except Exception as e:
        st.error("حدث خطأ أثناء إرسال الرسالة أو حفظها.")
        show_error(e)
