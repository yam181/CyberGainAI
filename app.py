import json
import extra_streamlit_components as stx
from cryptography.fernet import Fernet
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone, timedelta
import uuid
import re

# =====================================
# إعداد الصفحة
# =====================================
st.set_page_config(
    page_title="NEXORA AI",
    page_icon="🛡️",
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
    "show_profile": False,
    "profile_image": None,
    "profile_name": "",
    "confirm_delete_account": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
cookie_manager = stx.CookieManager(key="nexora_auth")

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
        "new_chat": "محادثة جديدة",
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
        "delete_account_confirm":
            "هل أنت متأكد من حذف حسابك نهائياً؟ سيتم حذف محادثاتك.",
        "about_text":
            "NEXORA AI هو مساعد ذكي تم تطويره بواسطة Yamin Zoabi.",
        "privacy_text":
            "تُحفظ المحادثات في قاعدة بيانات Supabase وفق إعدادات الوصول الخاصة بها.",
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
        "back": "← العودة إلى المحادثات",
        "profile_name": "الاسم",
        "choose_photo": "اختر صورة شخصية",
        "save_profile": "حفظ الملف الشخصي",
        "profile_saved": "تم حفظ الاسم بنجاح.",
        "profile_error": "تعذّر حفظ الاسم.",
        "photo_note": "الصورة المختارة متاحة في الجلسة الحالية فقط.",
        "remove_photo": "إزالة الصورة",
        "account_info": "معلومات الحساب",
        "account_settings": "إعدادات الحساب",
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
        "logout": "Log Out",
        "new_chat": "New chat",
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
        "delete_account_confirm":
            "Are you sure you want to delete your account and conversations?",
        "about_text":
            "NEXORA AI is a smart assistant developed by Yamin Zoabi.",
        "privacy_text":
            "Conversations are stored in Supabase according to its access policies.",
        "no_conversations": "No conversations yet",
        "error_login": "Login failed. Check your email and password.",
        "error_signup": "Could not create account.",
        "check_email": "Check your email to confirm your account.",
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
        "back": "← Back to chats",
        "profile_name": "Name",
        "choose_photo": "Choose a profile photo",
        "save_profile": "Save Profile",
        "profile_saved": "Name saved successfully.",
        "profile_error": "Could not save the name.",
        "photo_note": "The selected photo is available for this session only.",
        "remove_photo": "Remove photo",
        "account_info": "Account Information",
        "account_settings": "Account Settings",
    },
}


def t(key, **kwargs):
    lang = st.session_state.language
    value = TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)
    return value.format(**kwargs) if kwargs else value


# =====================================
# التصميم
# =====================================
PALETTES = {
    "dark": {
        "APP_BG": (
            "radial-gradient(ellipse at 86% 9%, rgba(35,116,220,.55), transparent 36%),"
            "linear-gradient(112deg, #050a12 0%, #071321 48%, #0a2850 100%)"
        ),
        "SIDEBAR": "#08162b",
        "TEXT": "#f4f7ff",
        "MUTED": "#a9b7ce",
        "BORDER": "rgba(139,174,230,.22)",
        "ROW": "rgba(255,255,255,.04)",
        "ROW_HOVER": "rgba(49,136,244,.18)",
        "ROW_ACTIVE": "rgba(49,136,244,.30)",
        "INPUT_BG": "#142744",
        "USER_MSG": "rgba(49,136,244,.18)",
        "ASSIST_MSG": "rgba(255,255,255,.03)",
        "CHAT_INPUT": "rgba(20,39,70,.96)",
        "LOGO": "#a9eaff",
    },
    "light": {
        "APP_BG": "#f3f6fb",
        "SIDEBAR": "#ffffff",
        "TEXT": "#0f1b2d",
        "MUTED": "#5b6b84",
        "BORDER": "rgba(15,40,80,.16)",
        "ROW": "rgba(15,40,80,.04)",
        "ROW_HOVER": "rgba(49,136,244,.12)",
        "ROW_ACTIVE": "rgba(49,136,244,.22)",
        "INPUT_BG": "#ffffff",
        "USER_MSG": "rgba(49,136,244,.12)",
        "ASSIST_MSG": "#ffffff",
        "CHAT_INPUT": "#ffffff",
        "LOGO": "#1b6fd6",
    },
}

CSS_TEMPLATE = """
<style>
:root {
    --nx-text: __TEXT__;
    --nx-muted: __MUTED__;
    --nx-border: __BORDER__;
    --nx-row: __ROW__;
    --nx-row-hover: __ROW_HOVER__;
    --nx-row-active: __ROW_ACTIVE__;
    --nx-input: __INPUT_BG__;
    --nx-blue: #3188f4;
    --nx-cyan: #22b8d7;
}
html, body, [class*="css"] {
    font-family: Inter, "Segoe UI", Tahoma, Arial, sans-serif;
}
.stApp {
    background: __APP_BG__ !important;
    color: var(--nx-text) !important;
}
[data-testid="stMain"], [data-testid="stAppViewContainer"] {
    background: transparent !important;
}
[data-testid="stMain"] p, [data-testid="stMain"] li,
[data-testid="stMain"] label, [data-testid="stMain"] h1,
[data-testid="stMain"] h2, [data-testid="stMain"] h3,
[data-testid="stMain"] h4 { color: var(--nx-text); }
.block-container {
    max-width: 1100px !important;
    padding: 1.2rem 2rem 6rem !important;
}

/* ---------- إخفاء عناصر Streamlit (GitHub, Deploy, القائمة) ---------- */
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"], [data-testid="stToolbarActions"],
[data-testid="stAppDeployButton"], .stAppDeployButton, .stDeployButton,
[data-testid="stMainMenu"], [data-testid="stStatusWidget"],
[data-testid="stDecoration"], .viewerBadge_container__1QSob,
[data-testid="stHeader"] a[href*="github"],
footer, #MainMenu {
    display: none !important;
    visibility: hidden !important;
}
/* زر فتح/إغلاق الشريط الجانبي يبقى ظاهرًا */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    pointer-events: auto !important;
}

/* ---------- الشريط الجانبي ---------- */
[data-testid="stSidebar"] {
    background: __SIDEBAR__ !important;
    border-right: 1px solid var(--nx-border) !important;
}
[data-testid="stSidebar"] > div:first-child { background: transparent !important; }
[data-testid="stSidebarContent"] {
    overflow-y: auto !important;
    overflow-x: hidden !important;
}
[data-testid="stSidebarUserContent"] { padding: .9rem .8rem 1.2rem !important; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .4rem !important; }
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    gap: .25rem !important;
    align-items: center !important;
    flex-wrap: nowrap !important;
}
[data-testid="stSidebar"] hr {
    border-color: var(--nx-border) !important;
    margin: .6rem 0 !important;
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] label { color: var(--nx-text); }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: var(--nx-muted) !important; }

/* أزرار الشريط الجانبي */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    min-height: 38px !important;
    border-radius: 10px !important;
    color: var(--nx-text) !important;
    background: var(--nx-row) !important;
    border: 1px solid transparent !important;
    box-shadow: none !important;
    justify-content: flex-start !important;
    padding: .4rem .7rem !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--nx-row-hover) !important;
    border-color: var(--nx-border) !important;
}
[data-testid="stSidebar"] .stButton > button:focus,
[data-testid="stSidebar"] .stButton > button:active {
    outline: none !important;
    box-shadow: none !important;
    border-color: var(--nx-blue) !important;
}
[data-testid="stSidebar"] .stButton > button p {
    font-size: 13px !important;
    line-height: 1.35 !important;
    margin: 0 !important;
    text-align: start !important;
    unicode-bidi: plaintext;
}

/* زر محادثة جديدة */
.st-key-nx_new_chat button {
    background: linear-gradient(100deg, #3987fa, #17a9d2) !important;
    color: #fff !important;
    border: 0 !important;
    justify-content: center !important;
    font-weight: 600 !important;
    box-shadow: 0 5px 18px rgba(35,126,231,.25) !important;
}
.st-key-nx_new_chat button p { text-align: center !important; color: #fff !important; }
.st-key-nx_new_chat button:hover { filter: brightness(1.08); }

/* صفوف المحادثات: بدون إطارات، والعنوان يظهر كاملًا (سطرين كحد أقصى) */
[class*="st-key-nx_row_"] button {
    background: transparent !important;
    border: 1px solid transparent !important;
    min-height: 40px !important;
    height: auto !important;
}
[class*="st-key-nx_row_"] button:hover { background: var(--nx-row-hover) !important; }
[class*="st-key-nx_row_active_"] button {
    background: var(--nx-row-active) !important;
}
[class*="st-key-nx_row_"] button p {
    display: -webkit-box !important;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    white-space: normal !important;
    word-break: break-word;
}
/* زر ⋯ */
[class*="st-key-nx_more_"] button {
    background: transparent !important;
    border: 0 !important;
    min-height: 34px !important;
    padding: 0 !important;
    justify-content: center !important;
    color: var(--nx-muted) !important;
}
[class*="st-key-nx_more_"] button:hover { color: var(--nx-text) !important; }

/* عناوين المجموعات الزمنية */
.date-group {
    color: var(--nx-muted) !important;
    font-size: 11.5px !important;
    font-weight: 650 !important;
    letter-spacing: .3px;
    padding: 4px 6px;
    margin: 10px 0 2px !important;
}

/* حقول الإدخال */
[data-testid="stSidebar"] input, [data-testid="stMain"] input,
[data-testid="stMain"] textarea {
    background: var(--nx-input) !important;
    color: var(--nx-text) !important;
    border: 1px solid var(--nx-border) !important;
    border-radius: 10px !important;
}
[data-testid="stSidebar"] input:focus, [data-testid="stMain"] input:focus,
[data-testid="stMain"] textarea:focus {
    border-color: var(--nx-blue) !important;
    box-shadow: 0 0 0 1px rgba(49,136,244,.35) !important;
    outline: none !important;
}
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"] {
    border-color: var(--nx-border) !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="base-input"]:focus-within {
    border-color: var(--nx-blue) !important;
}
[data-testid="stMain"] [data-testid="stSelectbox"] [role="combobox"] {
    background: var(--nx-input) !important;
    color: var(--nx-text) !important;
}

/* ---------- المحتوى الرئيسي ---------- */
.welcome-container {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: 42vh; text-align: center;
    padding: 1rem 1rem 1.4rem;
}
.welcome-logo {
    font-size: 17px; font-weight: 750; letter-spacing: 3px;
    color: __LOGO__; margin-bottom: 20px;
    text-shadow: 0 0 26px rgba(45,177,255,.35);
}
.welcome-text {
    font-size: clamp(24px, 3vw, 34px); font-weight: 600;
    color: var(--nx-text); margin-bottom: 10px;
}
.welcome-sub { font-size: 15px; color: var(--nx-muted); }

/* إزالة صور الروبوت والمستخدم بجانب الرسائل */
[data-testid^="stChatMessageAvatar"],
[data-testid^="chatAvatarIcon"],
[data-testid="stChatMessage"] > div:has([data-testid^="stChatMessageAvatar"]),
[data-testid="stChatMessage"] > div:has([data-testid^="chatAvatarIcon"]) {
    display: none !important;
    width: 0 !important;
    min-width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* شكل الرسائل */
[data-testid="stChatMessage"] {
    background: __ASSIST_MSG__ !important;
    border: 1px solid var(--nx-border) !important;
    border-radius: 16px !important;
    padding: 14px 18px !important;
    margin-bottom: .6rem !important;
    gap: 0 !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: __USER_MSG__ !important;
    border-color: rgba(49,136,244,.35) !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] h1, [data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 {
    color: var(--nx-text) !important;
    unicode-bidi: plaintext;
    text-align: start;
    line-height: 1.7;
}
[data-testid="stChatMessage"] pre, [data-testid="stChatMessage"] code {
    direction: ltr; text-align: left; unicode-bidi: normal;
}

/* مربع الكتابة */
[data-testid="stChatInput"] {
    background: __CHAT_INPUT__ !important;
    border: 1px solid var(--nx-border) !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 36px rgba(0,0,0,.18) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--nx-blue) !important;
    box-shadow: 0 0 0 1px rgba(49,136,244,.4), 0 10px 36px rgba(0,0,0,.2) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--nx-text) !important;
    border: 0 !important;
    box-shadow: none !important;
    unicode-bidi: plaintext;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(100deg, #3987fa, #17a9d2) !important;
    color: #fff !important;
    border-radius: 12px !important;
}

.stButton > button, [data-testid="stFormSubmitButton"] button,
[data-testid="stDownloadButton"] button {
    border-radius: 10px !important;
    transition: all .18s ease !important;
}

@media (max-width: 768px) {
    .block-container { padding: 1rem .7rem 5.5rem !important; }
    [data-testid="stChatMessage"] { padding: 12px 14px !important; }
    .welcome-container { min-height: 36vh; }
    .welcome-text { font-size: 23px !important; }
}
</style>
"""


def get_css():
    palette = PALETTES.get(st.session_state.theme, PALETTES["dark"])
    css = CSS_TEMPLATE
    for name, value in palette.items():
        css = css.replace(f"__{name}__", value)
    return css


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

# =====================================
# تشفير جلسة تسجيل الدخول
# =====================================
try:
    COOKIE_CIPHER = Fernet(
        st.secrets["COOKIE_SECRET"].encode()
    )
except Exception:
    st.error("إعداد COOKIE_SECRET غير صحيح أو غير موجود في Secrets.")
    st.stop()

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
You are NEXORA AI, a helpful AI assistant.

FOUNDER:
The founder of NEXORA AI is Yamin Zoabi.
Always spell the name exactly as "Yamin Zoabi".
When asked who founded or created NEXORA AI, identify Yamin Zoabi.
Do not invent another founder.

GENERAL RULES:
- Reply in the same language as the user whenever possible.
- Be helpful, clear, and concise.
- Explain technical subjects step by step when needed.
- Never invent sources or claim to have personal experiences.
- Prioritize safe, defensive IT and cybersecurity guidance.
"""


# =====================================
# المصادقة والمستخدم
# =====================================
COOKIE_NAME = "nexora_auth"


def apply_token():
    if st.session_state.access_token:
        supabase.postgrest.auth(st.session_state.access_token)


def save_session_cookie():
    access = st.session_state.access_token
    refresh = st.session_state.refresh_token

    if not access or not refresh:
        return

    session_data = json.dumps({
        "access_token": access,
        "refresh_token": refresh,
    })

    encrypted = COOKIE_CIPHER.encrypt(
        session_data.encode()
    ).decode()

    cookie_manager.set(
        COOKIE_NAME,
        encrypted,
        key="nexora_auth_save",
        path="/",
        expires_at=datetime.now() + timedelta(days=30),
        secure=True,
        same_site="lax",
    )


def restore_session_cookie():
    if st.session_state.user:
        return

    encrypted = cookie_manager.get(COOKIE_NAME)

    if not encrypted:
        return

    try:
        session_data = COOKIE_CIPHER.decrypt(
            encrypted.encode()
        ).decode()

        tokens = json.loads(session_data)

        result = supabase.auth.set_session(
            tokens["access_token"],
            tokens["refresh_token"],
        )

        if result and result.session and result.user:
            st.session_state.user = result.user
            st.session_state.access_token = result.session.access_token
            st.session_state.refresh_token = result.session.refresh_token
            apply_token()

    except Exception:
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user = None
        cookie_manager.delete(
            COOKIE_NAME,
            key="nexora_auth_delete",
        )


def get_user_id():
    user = st.session_state.user
    return str(user.id) if user else None


def get_user_email():
    return getattr(st.session_state.user, "email", "") or ""


def default_title():
    return "محادثة جديدة" if st.session_state.language == "ar" else "New Chat"


def show_error(error):
    message = str(error)
    if "42501" in message or "row-level security" in message.lower():
        st.error("رفضت Supabase العملية بسبب صلاحيات RLS.")
    else:
        st.error(message)


def logout():
    try:
        cookie_manager.delete(
            COOKIE_NAME,
            key="nexora_auth_delete",
        )
    except Exception:
        pass

    try:
        apply_token()
        supabase.auth.sign_out()
    except Exception:
        pass

    for key in [
        "user", "access_token", "refresh_token",
        "conversation_id", "messages", "show_settings",
        "show_profile", "profile_image", "profile_name",
    ]:
        st.session_state[key] = [] if key == "messages" else (
            False if key in ("show_settings", "show_profile") else None
        )

    st.rerun()


def delete_account():
    try:
        apply_token()
        uid = get_user_id()

        if uid:
            supabase.table("chat_history").delete().eq(
                "user_id", uid
            ).execute()

            supabase.table("conversations").delete().eq(
                "user_id", uid
            ).execute()

        st.warning(
            "تم حذف سجلات المحادثات. حذف حساب المصادقة نفسه يحتاج "
            "إلى إجراء إداري آمن في Supabase."
        )
        logout()
    except Exception as e:
        show_error(e)


# =====================================
# استعادة الجلسة
# =====================================
restore_session_cookie()

if st.session_state.access_token and not st.session_state.user:
    try:
        if st.session_state.refresh_token:
            supabase.auth.set_session(
                st.session_state.access_token,
                st.session_state.refresh_token,
            )

        result = supabase.auth.get_user()

        if result and result.user:
            st.session_state.user = result.user
            apply_token()

    except Exception:
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user = None


# =====================================
# تسجيل الدخول وإنشاء الحساب
# =====================================
if not st.session_state.user:
    st.markdown(
        f"""
        <div class="welcome-container">
            <div class="welcome-logo">NEXORA AI</div>
            <div class="welcome-sub">{t("subtitle")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    lang_col, theme_col, _ = st.columns([1, 1, 4])

    with lang_col:
        if st.button("🌐 EN" if st.session_state.language == "ar" else "🌐 ع"):
            st.session_state.language = (
                "en" if st.session_state.language == "ar" else "ar"
            )
            st.rerun()

    with theme_col:
        if st.button("🌙" if st.session_state.theme == "light" else "☀️"):
            st.session_state.theme = (
                "light" if st.session_state.theme == "dark" else "dark"
            )
            st.rerun()

    login_tab, signup_tab = st.tabs([t("login"), t("signup")])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input(t("email"))
            password = st.text_input(t("password"), type="password")

            if st.form_submit_button(
                t("login_btn"), use_container_width=True, type="primary"
            ):
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
                        st.session_state.refresh_token = (
                            result.session.refresh_token
                        )
                        st.session_state.conversation_id = None
                        st.session_state.messages = []
                        apply_token()
                        save_session_cookie()
                        st.rerun()
                    else:
                        st.error(t("error_login"))
                except Exception:
                    st.error(t("error_login"))

    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input(t("email"), key="signup_email")
            new_password = st.text_input(
                t("password"), type="password", key="signup_password"
            )

            if st.form_submit_button(
                t("signup_btn"), use_container_width=True, type="primary"
            ):
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
                        st.session_state.refresh_token = (
                            result.session.refresh_token
                        )
                        apply_token()
                        save_session_cookie()
                        st.rerun()
                    else:
                        st.success(t("check_email"))
                except Exception:
                    st.error(t("error_signup"))

    st.stop()


apply_token()

# تحميل اسم الحساب من بيانات Supabase
user_metadata = getattr(st.session_state.user, "user_metadata", None) or {}

if not st.session_state.profile_name:
    st.session_state.profile_name = user_metadata.get(
        "full_name", get_user_email().split("@")[0]
    )


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
        "title": default_title(),
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


def generate_title(question):
    try:
        result = groq.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create a short title of 3 to 6 words in the same "
                        "language as the user's question. Return only the title."
                    ),
                },
                {"role": "user", "content": question[:1000]},
            ],
            # النموذج يستهلك جزءًا من الحد في التفكير، فالقيمة 40 كانت
            # تعيد عنوانًا فارغًا ويسقط الكود على أول 45 حرفًا من السؤال
            max_tokens=200,
            temperature=0.2,
        )
        title = (result.choices[0].message.content or "").strip()
        title = re.sub(r"\s+", " ", title).strip("\"'`“” ")
        return title[:80] if title else question[:45]
    except Exception:
        return question[:45]


def process_uploaded_files(files):
    parts = []

    for file in files:
        name = file.name

        if file.type and file.type.startswith("image/"):
            parts.append(f"[صورة مرفقة: {name}]")
        elif name.lower().endswith(
            (".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css")
        ):
            try:
                content = file.getvalue().decode("utf-8", errors="ignore")
                parts.append(f"[ملف {name}]\n{content[:3000]}")
            except Exception:
                parts.append(f"[ملف {name} - تعذر قراءة المحتوى]")
        else:
            parts.append(f"[ملف مرفق: {name}]")

    return "\n\n".join(parts)


def group_conversations_by_date(conversations):
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    groups = {
        "today": [],
        "yesterday": [],
        "last_7_days": [],
        "older": [],
    }

    for conv in conversations:
        try:
            updated = datetime.fromisoformat(
                conv["updated_at"].replace("Z", "+00:00")
            )
            date = updated.date()

            if date == today:
                groups["today"].append(conv)
            elif date == yesterday:
                groups["yesterday"].append(conv)
            elif date >= week_ago:
                groups["last_7_days"].append(conv)
            else:
                groups["older"].append(conv)
        except Exception:
            groups["older"].append(conv)

    return groups


# =====================================
# صفحة الملف الشخصي
# =====================================
if st.session_state.show_profile:
    st.title("👤 " + t("profile"))
    st.caption("NEXORA AI")
    st.divider()

    if st.button(t("back"), key="profile_back"):
        st.session_state.show_profile = False
        st.rerun()

    left, right = st.columns([1, 2], gap="large")

    with left:
        if st.session_state.profile_image:
            st.image(st.session_state.profile_image, width=180)
        else:
            st.markdown(
                """
                <div style="
                    width:150px;height:150px;border-radius:50%;
                    background:#10294b;border:3px solid #3188f4;
                    display:flex;align-items:center;justify-content:center;
                    font-size:60px;color:#a9d4ff;">
                    👤
                </div>
                """,
                unsafe_allow_html=True,
            )

        uploaded = st.file_uploader(
            t("choose_photo"),
            type=["png", "jpg", "jpeg", "webp"],
            key="profile_photo_upload",
        )

        if uploaded is not None:
            if uploaded.size > 5 * 1024 * 1024:
                st.error("حجم الصورة كبير. الحد الأقصى 5 MB.")
            else:
                st.session_state.profile_image = uploaded.getvalue()
                st.rerun()

        if st.session_state.profile_image:
            if st.button(t("remove_photo"), key="remove_profile_photo"):
                st.session_state.profile_image = None
                st.rerun()

        st.caption(t("photo_note"))

    with right:
        st.subheader(t("account_info"))

        with st.form("profile_form"):
            new_name = st.text_input(
                t("profile_name"),
                value=st.session_state.profile_name,
            )

            st.text_input(
                t("email"),
                value=get_user_email(),
                disabled=True,
            )

            save_profile = st.form_submit_button(
                t("save_profile"),
                type="primary",
                use_container_width=True,
            )

        if save_profile:
            clean_name = new_name.strip()

            if not clean_name:
                st.warning("يرجى إدخال الاسم.")
            else:
                try:
                    result = supabase.auth.update_user({
                        "data": {"full_name": clean_name}
                    })

                    st.session_state.profile_name = clean_name

                    if getattr(result, "user", None):
                        st.session_state.user = result.user

                    st.success(t("profile_saved"))
                except Exception:
                    st.error(t("profile_error"))

    st.divider()
    st.subheader(t("account_settings"))

    if st.button("⚙️ " + t("settings_prefs"), use_container_width=True):
        st.session_state.show_profile = False
        st.session_state.show_settings = True
        st.rerun()

    if st.button("🚪 " + t("logout"), use_container_width=True):
        logout()

    st.stop()


# =====================================
# الشريط الجانبي
# =====================================
with st.sidebar:
    with st.container(key="nx_new_chat"):
        if st.button("＋  " + t("new_chat"), use_container_width=True):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.session_state.show_settings = False
            st.session_state.show_profile = False
            st.rerun()

    search_query = st.text_input(
        "search",
        placeholder="🔎  " + t("search_placeholder"),
        label_visibility="collapsed",
        key="sidebar_search",
    )

    try:
        conversations = list_conversations()
    except Exception as error:
        st.error("حدث خطأ أثناء تحميل المحادثات:")
        show_error(error)
        conversations = []

    if search_query.strip():
        query = search_query.strip().casefold()
        conversations = [
            conv for conv in conversations
            if query in (conv.get("title") or "").casefold()
        ]

    if not conversations:
        st.caption(t("no_conversations"))
    else:
        groups = group_conversations_by_date(conversations)

        def render_group(title_key, items):
            if not items:
                return

            st.markdown(
                f'<div class="date-group">{t(title_key)}</div>',
                unsafe_allow_html=True,
            )

            for conv in items:
                cid = str(conv["id"])
                title = conv.get("title") or default_title()
                active = str(st.session_state.conversation_id) == cid
                row_class = "active" if active else "idle"

                col1, col2 = st.columns([8, 1], gap="small")

                with col1:
                    with st.container(key=f"nx_row_{row_class}_{cid}"):
                        if st.button(
                            title[:60],
                            key=f"open_{cid}",
                            use_container_width=True,
                        ):
                            try:
                                st.session_state.conversation_id = cid
                                st.session_state.messages = load_messages(cid)
                                st.session_state.show_settings = False
                                st.rerun()
                            except Exception as error:
                                show_error(error)

                with col2:
                    with st.container(key=f"nx_more_{cid}"):
                        if st.button("⋯", key=f"menu_{cid}"):
                            key = f"show_menu_{cid}"
                            st.session_state[key] = not st.session_state.get(key, False)

                if st.session_state.get(f"show_menu_{cid}", False):
                    st.caption(t("delete_confirm", title=title))
                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button(t("yes"), key=f"yes_{cid}"):
                            try:
                                delete_conversation(cid)
                                st.session_state.pop(f"show_menu_{cid}", None)
                                st.rerun()
                            except Exception as error:
                                show_error(error)

                    with c2:
                        if st.button(t("cancel"), key=f"no_{cid}"):
                            st.session_state.pop(f"show_menu_{cid}", None)
                            st.rerun()

        render_group("today", groups["today"])
        render_group("yesterday", groups["yesterday"])
        render_group("last_7_days", groups["last_7_days"])
        render_group("older", groups["older"])

    st.divider()

    if st.button(
        "👤  " + (st.session_state.profile_name or get_user_email()),
        key="nx_profile_open",
        use_container_width=True,
        help=t("profile"),
    ):
        st.session_state.show_profile = True
        st.session_state.show_settings = False
        st.rerun()

    if st.button(
        "⚙️  " + t("settings_prefs"),
        key="nx_settings_open",
        use_container_width=True,
    ):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()


# =====================================
# الإعدادات
# =====================================
if st.session_state.show_settings:
    st.title("⚙️ " + t("settings"))

    if st.button(t("close")):
        st.session_state.show_settings = False
        st.rerun()

    st.subheader(t("language"))

    lang1, lang2 = st.columns(2)

    with lang1:
        if st.button(t("arabic"), use_container_width=True):
            st.session_state.language = "ar"
            st.rerun()

    with lang2:
        if st.button(t("english"), use_container_width=True):
            st.session_state.language = "en"
            st.rerun()

    st.divider()
    st.subheader(t("theme"))

    theme1, theme2 = st.columns(2)

    with theme1:
        if st.button("🌙 " + t("dark"), use_container_width=True):
            st.session_state.theme = "dark"
            st.rerun()

    with theme2:
        if st.button("☀️ " + t("light"), use_container_width=True):
            st.session_state.theme = "light"
            st.rerun()

    st.divider()

    with st.expander(t("chat_settings"), expanded=True):
        temp = st.slider(
            t("temperature"), 0.0, 1.0,
            float(st.session_state.temperature), 0.1,
        )
        tokens = st.slider(
            t("max_tokens"), 200, 2000,
            int(st.session_state.max_tokens), 50,
        )

        if st.button(t("save_settings")):
            st.session_state.temperature = temp
            st.session_state.max_tokens = tokens
            st.success("✓")

    with st.expander(t("about")):
        st.markdown(t("about_text"))
        st.caption("Founder: Yamin Zoabi")

    with st.expander(t("privacy")):
        st.markdown(t("privacy_text"))

    st.divider()

    if st.button(t("delete_account"), type="primary"):
        st.session_state.confirm_delete_account = True

    if st.session_state.confirm_delete_account:
        st.warning(t("delete_account_confirm"))

        yes_col, no_col = st.columns(2)

        with yes_col:
            if st.button(t("yes"), key="confirm_delete_yes"):
                delete_account()

        with no_col:
            if st.button(t("cancel"), key="confirm_delete_no"):
                st.session_state.confirm_delete_account = False
                st.rerun()

    if st.button(t("logout"), use_container_width=True):
        logout()

    st.stop()


# =====================================
# المحتوى الرئيسي
# =====================================
if not st.session_state.messages:
    st.markdown(
        f"""
        <div class="welcome-container">
            <div class="welcome-logo">NEXORA AI</div>
            <div class="welcome-text">{t("welcome_title")}</div>
            <div class="welcome-sub">{t("welcome_subtitle")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=None):
            st.markdown(message["content"])


# =====================================
# خانة الكتابة والمرفقات
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
            final_prompt = (
                f"{user_text}\n\n---\n{extra}" if user_text else extra
            )

    try:
        if not st.session_state.conversation_id:
            create_conversation()

        cid = str(st.session_state.conversation_id)
        first_message = len(st.session_state.messages) == 0

        st.session_state.messages.append({
            "role": "user",
            "content": final_prompt,
        })
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

                answer = (
                    result.choices[0].message.content
                    or "عذرًا، لم أتمكن من إنشاء رد."
                ).strip()

                st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
        })
        save_message(cid, "assistant", answer)

        if first_message:
            update_title(cid, generate_title(final_prompt))

        update_activity(cid)
        st.rerun()

    except Exception as error:
        st.error("حدث خطأ أثناء إرسال الرسالة أو حفظها.")
        show_error(error)
