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
        "upload_photo": "رفع صورة شخصية",
        "no_photo": "لا توجد صورة بعد",
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
        "upload_photo": "Upload profile photo",
        "no_photo": "No photo yet",
        "arabic": "العربية",
        "english": "English",
    },
}

def t(key, **kwargs):
    lang = st.session_state.language
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

# =====================================
# التصميم (بنفسجي + داكن فقط)
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

        /* إزالة البرتقالي من خانة الكتابة */
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

        /* الأزرار */
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

        /* إخفاء عناصر Streamlit */
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
