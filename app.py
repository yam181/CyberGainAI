import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone, timedelta
import uuid
import re

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
        "welcome_title": "جاهز عندما تكون مستعدًا",
        "welcome_subtitle": "كيف يمكنني مساعدتك اليوم؟",
        "search_placeholder": "ابحث في محادثاتك...",
        "today": "اليوم",
        "yesterday": "أمس",
        "last_7_days": "آخر 7 أيام",
        "older": "أقدم",
        "settings_prefs": "الإعدادات والتفضيلات",
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
        "welcome_title": "Ready when you are",
        "welcome_subtitle": "How can I help you today?",
        "search_placeholder": "Search your chats...",
        "today": "Today",
        "yesterday": "Yesterday",
        "last_7_days": "Last 7 days",
        "older": "Older",
        "settings_prefs": "Settings & Preferences",
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
    return """
    <style>
    :root {
        --nx-bg: #100D18;
        --nx-purple: #7546C8;
        --nx-text: #EDE6F8;
        --nx-border: #352744;
        --nx-hover: #1F1830;
    }

    /* إخفاء العناصر المزعجة فقط */
   #MainMenu,
footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton {
    display: none !important;
}

    /* ===== زر فتح المحادثات ===== */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 18px !important;
    left: 18px !important;
    z-index: 999999 !important;
    background: #7546C8 !important;
    border: 1px solid #9B78E8 !important;
    border-radius: 12px !important;
    width: 48px !important;
    height: 48px !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}

[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg {
    color: white !important;
    fill: white !important;
    stroke: white !important;
}

    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg {
        fill: #000000 !important;
        color: #000000 !important;
        width: 24px !important;
        height: 24px !important;
    }

    /* باقي التصميم */
    .stApp {
        background: #0B0912 !important;
        color: #EDE6F8 !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 6rem !important;
        max-width: 780px !important;
    }

    [data-testid="stSidebar"] {
        background: #100D18 !important;
        border-right: 1px solid #352744 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: 1.2rem 1rem !important;
    }

    [data-testid="stChatMessageAvatar"],
    [data-testid="chatAvatarIcon-user"],
    [data-testid="chatAvatarIcon-assistant"],
    [data-testid*="chatAvatarIcon"] {
        display: none !important;
    }
    [data-testid="stChatMessage"] > div:first-child {
        display: none !important;
    }

    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 10px 0 !important;
        margin: 6px 0 !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #7546C820 !important;
        border: 1px solid #7546C840 !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 14px 18px !important;
        margin-left: 15% !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: #16121F !important;
        border: 1px solid #352744 !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 14px 18px !important;
        margin-right: 15% !important;
    }

    .nexora-title {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #C4B5FD !important;
        margin: 0 0 4px 0 !important;
    }
    .nexora-subtitle {
        color: #A78BFA !important;
        font-size: 12px !important;
        margin-bottom: 18px !important;
    }

    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 55vh;
        text-align: center;
        padding: 2rem 1rem;
    }
    .welcome-logo {
        font-size: 28px;
        font-weight: 700;
        color: #C4B5FD;
        margin-bottom: 12px;
    }
    .welcome-text {
        font-size: 26px;
        color: #EDE6F8;
        margin-bottom: 8px;
        font-weight: 500;
    }
    .welcome-sub {
        font-size: 15px;
        color: #A78BFA;
        max-width: 380px;
    }

    [data-testid="stSidebar"] .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        min-height: 40px !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #7546C8 !important;
        border: none !important;
        color: white !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"],
    [data-testid="stSidebar"] .stButton > button[kind="tertiary"] {
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #EDE6F8 !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
    [data-testid="stSidebar"] .stButton > button[kind="tertiary"]:hover {
        background: #1F1830 !important;
    }

    [data-testid="stChatInput"] {
        border-radius: 16px !important;
        border: 1px solid #352744 !important;
        background: #16121F !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #7546C8 !important;
        box-shadow: 0 0 0 2px #7546C833 !important;
    }

    .stButton > button[kind="primary"] {
        background: #7546C8 !important;
        border: none !important;
        color: white !important;
        border-radius: 10px !important;
    }

    h1, h2, h3 { color: #C4B5FD !important; }

    .login-card {
        background: #16121F;
        border: 1px solid #352744;
        border-radius: 16px;
        padding: 2rem 1.6rem;
        max-width: 400px;
        margin: 6vh auto 0;
    }

    .date-group {
        font-size: 11px !important;
        color: #A78BFA !important;
        font-weight: 600 !important;
        margin: 14px 0 6px 2px !important;
        text-transform: uppercase;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.7rem !important;
            padding-right: 0.7rem !important;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            margin-left: 4% !important;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            margin-right: 4% !important;
        }
        .welcome-text { font-size: 22px; }
        .welcome-logo { font-size: 24px; }
    }
    </style>
    """

st.markdown(get_css(), unsafe_allow_html=True)

# =====================================
# الاتصال
# =====================================
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
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
GENERAL RULES:
- Be helpful, clear, and concise.
- Reply in the same language as the user whenever possible.
- Explain technical subjects step by step when needed.
- Do not claim to have personal experiences.
"""

def apply_token():
    if st.session_state.access_token:
        supabase.postgrest.auth(st.session_state.access_token)

def get_user_id():
    return str(st.session_state.user.id) if st.session_state.user else None

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
    for key in ["user", "access_token", "refresh_token", "conversation_id", "messages", "show_settings"]:
        st.session_state[key] = None if key != "messages" else []
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
    keywords = ["مخترع", "مؤسس", "من عمل", "من صنع", "من طور", "من أنشأ",
                "founder", "creator", "who made", "who created", "who developed", "who invented", "inventor", "owner"]
    return any(k in text for k in keywords)

# =====================================
# استعادة الجلسة
# =====================================
if st.session_state.access_token and not st.session_state.user:
    try:
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
    st.markdown("""
    <div class="login-card">
        <div style="text-align:center; margin-bottom: 1.4rem;">
            <div style="font-size:28px; font-weight:700; color:#C4B5FD;">NEXORA AI</div>
            <div style="color:#A78BFA; font-size:13px; margin-top:4px;">مساعدك الذكي</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 3])
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
            if st.form_submit_button(t("login_btn"), use_container_width=True, type="primary"):
                try:
                    result = supabase.auth.sign_in_with_password({"email": email.strip(), "password": password})
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
            if st.form_submit_button(t("signup_btn"), use_container_width=True, type="primary"):
                try:
                    result = supabase.auth.sign_up({"email": new_email.strip(), "password": new_password})
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
    result = supabase.table("conversations").select("id,user_id,title,created_at,updated_at").eq("user_id", get_user_id()).order("updated_at", desc=True).execute()
    return result.data or []

def create_conversation():
    apply_token()
    now = datetime.now(timezone.utc).isoformat()
    cid = str(uuid.uuid4())
    result = supabase.table("conversations").insert({
        "id": cid, "user_id": get_user_id(),
        "title": "محادثة جديدة" if st.session_state.language == "ar" else "New Chat",
        "created_at": now, "updated_at": now
    }).execute()
    if not result.data:
        raise Exception("لم يتم إنشاء المحادثة.")
    st.session_state.conversation_id = str(result.data[0]["id"])
    st.session_state.messages = []
    return st.session_state.conversation_id

def load_messages(cid):
    apply_token()
    result = supabase.table("chat_history").select("role,content,created_at").eq("user_id", get_user_id()).eq("conversation_id", cid).order("created_at").execute()
    return [{"role": r["role"], "content": r["content"]} for r in (result.data or []) if r.get("role") in ("user", "assistant")]

def save_message(cid, role, content):
    apply_token()
    supabase.table("chat_history").insert({
        "user_id": get_user_id(), "conversation_id": cid, "role": role, "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }).execute()

def update_title(cid, title):
    apply_token()
    supabase.table("conversations").update({"title": title, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", cid).eq("user_id", get_user_id()).execute()

def update_activity(cid):
    apply_token()
    supabase.table("conversations").update({"updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", cid).eq("user_id", get_user_id()).execute()

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
            messages=[{"role": "system", "content": "Create a short title of 3 to 6 words in the same language as the user's question. Return only the title."},
                      {"role": "user", "content": question}],
            max_tokens=40, temperature=0.2
        )
        title = (result.choices[0].message.content or "").strip().strip("\"'`“” ")
        title = re.sub(r"\s+", " ", title)
        return title[:80] if title else question[:45]
    except Exception:
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

def group_conversations_by_date(conversations):
    now = datetime.now(timezone.utc)
    today = now.date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    groups = {"today": [], "yesterday": [], "last_7_days": [], "older": []}
    for conv in conversations:
        try:
            updated = datetime.fromisoformat(conv["updated_at"].replace("Z", "+00:00"))
            d = updated.date()
            if d == today:
                groups["today"].append(conv)
            elif d == yesterday:
                groups["yesterday"].append(conv)
            elif d >= week_ago:
                groups["last_7_days"].append(conv)
            else:
                groups["older"].append(conv)
        except Exception:
            groups["older"].append(conv)
    return groups

# =====================================
# الشريط الجانبي
# =====================================
with st.sidebar:
    st.markdown(f'<div class="nexora-title">{t("app_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="nexora-subtitle">{t("subtitle")}</div>', unsafe_allow_html=True)

    if st.button(t("new_chat"), use_container_width=True, type="primary"):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    st.markdown("")

    search_query = st.text_input("🔎", placeholder=t("search_placeholder"), label_visibility="collapsed", key="sidebar_search")

    st.markdown("")

    try:
        conversations = list_conversations()
    except Exception as e:
        show_error(e)
        conversations = []

    if search_query.strip():
        q = search_query.strip().casefold()
        conversations = [c for c in conversations if q in (c.get("title") or "").casefold()]

    if not conversations:
        st.caption(t("no_conversations"))
    else:
        groups = group_conversations_by_date(conversations)

        def render_group(title_key, items):
            if not items:
                return
            st.markdown(f'<div class="date-group">{t(title_key)}</div>', unsafe_allow_html=True)
            for conv in items:
                cid = str(conv["id"])
                title = conv.get("title") or ("محادثة جديدة" if st.session_state.language == "ar" else "New Chat")
                is_active = str(st.session_state.conversation_id) == cid
                col1, col2 = st.columns([6, 1], gap="small")
                with col1:
                    label = title[:24] + ("…" if len(title) > 24 else "")
                    if st.button(label, key=f"open_{cid}", use_container_width=True, type="primary" if is_active else "tertiary"):
                        try:
                            st.session_state.conversation_id = cid
                            st.session_state.messages = load_messages(cid)
                            st.rerun()
                        except Exception as e:
                            show_error(e)
                with col2:
                    if st.button("⋯", key=f"menu_{cid}", type="tertiary"):
                        st.session_state[f"show_menu_{cid}"] = not st.session_state.get(f"show_menu_{cid}", False)
                if st.session_state.get(f"show_menu_{cid}", False):
                    st.caption(t("delete_confirm", title=title))
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(t("yes"), key=f"yes_{cid}", type="primary"):
                            try:
                                delete_conversation(cid)
                                st.session_state.pop(f"show_menu_{cid}", None)
                                st.rerun()
                            except Exception as e:
                                show_error(e)
                    with c2:
                        if st.button(t("cancel"), key=f"no_{cid}"):
                            st.session_state.pop(f"show_menu_{cid}", None)
                            st.rerun()

        render_group("today", groups["today"])
        render_group("yesterday", groups["yesterday"])
        render_group("last_7_days", groups["last_7_days"])
        render_group("older", groups["older"])

    st.markdown("---")
    email = getattr(st.session_state.user, "email", None)
    if email:
        st.caption(f"👤 {email}")
    if st.button("⚙️  " + t("settings_prefs"), use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()

# =====================================
# المحتوى الرئيسي
# =====================================
if st.session_state.show_settings:
    main_col, settings_col = st.columns([3.2, 1], gap="medium")
else:
    main_col = st.container()
    settings_col = None

with main_col:
    if not st.session_state.messages:
        st.markdown(f"""
        <div class="welcome-container">
            <div class="welcome-logo">NEXORA AI</div>
            <div class="welcome-text">{t("welcome_title")}</div>
            <div class="welcome-sub">{t("welcome_subtitle")}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=None):
                st.markdown(message["content"])
                if message["role"] == "assistant" and st.session_state.profile_image:
                    if any(k in message["content"].lower() for k in ["yamin zoabi", "25/12/2007", "مؤسس", "مخترع"]):
                        st.image(st.session_state.profile_image, width=260)

if st.session_state.show_settings and settings_col is not None:
    with settings_col:
        st.markdown(f"### {t('settings')}")
        if st.button("✕ " + t("close"), use_container_width=True):
            st.session_state.show_settings = False
            st.rerun()
        st.divider()
        st.markdown(f"**{t('language')}**")
        if st.button(t("arabic"), use_container_width=True, type="primary" if st.session_state.language == "ar" else "secondary"):
            st.session_state.language = "ar"
            st.rerun()
        if st.button(t("english"), use_container_width=True, type="primary" if st.session_state.language == "en" else "secondary"):
            st.session_state.language = "en"
            st.rerun()
        st.divider()
        st.markdown(f"**{t('theme')}**")
        if st.button("🌙 " + t("dark"), use_container_width=True, type="primary" if st.session_state.theme == "dark" else "secondary"):
            st.session_state.theme = "dark"
            st.rerun()
        if st.button("☀️ " + t("light"), use_container_width=True, type="primary" if st.session_state.theme == "light" else "secondary"):
            st.session_state.theme = "light"
            st.rerun()
        st.divider()
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
# خانة الكتابة
# =====================================
prompt = st.chat_input(t("chat_placeholder"), accept_file="multiple")

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
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, *st.session_state.messages[-12:]],
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.max_tokens,
                )
                answer = (result.choices[0].message.content or "عذرًا، لم أتمكن من إنشاء رد.").strip()
                st.markdown(answer)
                if is_founder_question(final_prompt) and st.session_state.profile_image:
                    st.image(st.session_state.profile_image, width=260)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        save_message(cid, "assistant", answer)

        if first_message:
            update_title(cid, generate_title(final_prompt))
        update_activity(cid)
        st.rerun()
    except Exception as e:
        st.error("حدث خطأ أثناء إرسال الرسالة أو حفظها.")
        show_error(e)
