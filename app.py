import json
import extra_streamlit_components as stx
from cryptography.fernet import Fernet
import streamlit as st
from groq import Groq
from supabase import create_client
from datetime import datetime, timezone, timedelta
import uuid
import re
import base64
import io
import requests

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
    "guest_mode": False,
    "guest_message_count": 0,
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
    "work_mode": "normal",
    "pending_prompt": None,
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
def get_css():
    return """
    <style>
    :root {
        --nx-bg: #090812;
        --nx-panel: #100d1a;
        --nx-panel-soft: #171224;
        --nx-purple: #8155d9;
        --nx-purple-light: #b49aff;
        --nx-text: #f2effa;
        --nx-muted: #aaa2ba;
        --nx-border: rgba(174, 143, 232, .16);
    }

    html, body, [class*="css"] {
        font-family: Inter, "Segoe UI", Arial, sans-serif;
    }

    .stApp {
        background-color: #070817 !important;
        background-image:
            linear-gradient(
                180deg,
                rgba(5, 6, 18, .22) 0%,
                rgba(5, 6, 18, .34) 58%,
                rgba(5, 6, 18, .48) 100%
            ),
            url("https://raw.githubusercontent.com/yam181/nexora-ai/main/nexora_glass_background.png") !important;
        background-size: cover !important;
        background-position: center center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        color: var(--nx-text) !important;
    }

    [data-testid="stMain"] {
        background: transparent !important;
    }

    .block-container {
        max-width: 1120px !important;
        padding-top: 2.2rem !important;
        padding-bottom: 7rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* Sidebar: quiet, clean, and fixed-width */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #100d1b 0%, #0d0b15 100%) !important;
        border-right: 1px solid var(--nx-border) !important;
        min-width: 260px !important;
        width: 260px !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
        padding: 1.35rem 1rem !important;
    }

    [data-testid="stSidebar"] button[kind="header"] {
        display: none !important;
    }

    [data-testid="stToolbar"],
    [data-testid="stToolbarActions"],
    [data-testid="stStatusWidget"],
    .stDeployButton,
    .viewerBadge_container__1QSob,
    [data-testid="stDecoration"],
    footer,
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }

    a[href*="streamlit.io/cloud"],
    a[href*="streamlit.app"],
    a[href*="share.streamlit.com"] {
        display: none !important;
    }

    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        pointer-events: auto !important;
    }

    /* Profile shortcut */
    .st-key-nx_profile_button {
        position: fixed !important;
        top: 12px !important;
        right: 14px !important;
        z-index: 999999 !important;
        width: 48px !important;
        height: 48px !important;
        padding: 2px !important;
        background: transparent !important;
    }

    .st-key-nx_profile_button button {
        width: 42px !important;
        height: 42px !important;
        min-height: 42px !important;
        padding: 0 !important;
        background: #1a1428 !important;
        border: 1px solid rgba(180, 154, 255, .5) !important;
        border-radius: 50% !important;
        color: #d8caff !important;
        font-size: 20px !important;
        box-shadow: 0 0 22px rgba(129, 85, 217, .13) !important;
    }

    /* Chat messages: hide only user avatars; keep the NEXORA assistant logo */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageAvatar"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div:first-child {
        display: none !important;
    }

    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 38px !important;
        min-width: 38px !important;
        height: 38px !important;
        border-radius: 50% !important;
        overflow: hidden !important;
        border: 1px solid rgba(183, 148, 255, .58) !important;
        background: linear-gradient(145deg, #25183c, #110d20) !important;
        box-shadow: 0 0 17px rgba(137, 91, 225, .22) !important;
    }

    [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        border-radius: 50% !important;
    }

    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        padding: 13px 0 !important;
        margin: 8px 0 !important;
    }

    [data-testid="stChatMessage"] > div:last-child {
        width: 100% !important;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: rgba(116, 78, 178, .12) !important;
        border: 1px solid rgba(150, 112, 220, .13) !important;
        border-radius: 18px !important;
        padding: 13px 18px !important;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatar"] img) {
        background: rgba(22, 18, 31, .52) !important;
        border: 1px solid rgba(174, 143, 232, .10) !important;
        border-radius: 18px !important;
        padding: 15px 18px !important;
    }

    /* Brand */
    .nexora-title {
        font-size: 21px !important;
        font-weight: 750 !important;
        letter-spacing: .7px !important;
        color: #d7c5ff !important;
        margin: 2px 0 3px 2px !important;
        text-shadow: 0 0 20px rgba(129, 85, 217, .24);
    }

    .nexora-subtitle {
        color: #9386ad !important;
        font-size: 12px !important;
        margin: 0 0 23px 3px !important;
    }

    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 57vh;
        text-align: center;
        padding: 1.5rem 1rem 2rem;
    }

    .welcome-logo {
        font-size: 17px;
        font-weight: 750;
        letter-spacing: 3px;
        color: #bda4ff;
        margin-bottom: 22px;
        text-shadow: 0 0 26px rgba(129, 85, 217, .55);
    }

    .welcome-text {
        font-size: clamp(25px, 3vw, 34px);
        font-weight: 600;
        letter-spacing: -.6px;
        color: #f4efff;
        margin-bottom: 10px;
    }

    .welcome-sub {
        font-size: 15px;
        color: #a99cbe;
    }

    /* =====================================
       NEXORA Ultra Premium Purple Composer
       ===================================== */
    [data-testid="stChatInput"] {
        background: linear-gradient(135deg, rgba(28, 20, 46, .98), rgba(18, 14, 31, .98)) !important;
        border: 1px solid rgba(169, 130, 255, .38) !important;
        border-radius: 20px !important;
        padding: 3px 8px !important;
        box-shadow:
            0 14px 42px rgba(0, 0, 0, .34),
            0 0 26px rgba(126, 79, 214, .16),
            inset 0 1px 0 rgba(255, 255, 255, .045) !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
        transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(194, 166, 255, .82) !important;
        box-shadow:
            0 0 0 1px rgba(157, 112, 255, .24),
            0 16px 46px rgba(0, 0, 0, .38),
            0 0 30px rgba(137, 87, 231, .24),
            inset 0 1px 0 rgba(255, 255, 255, .06) !important;
    }

    [data-testid="stChatInput"] textarea {
        color: #f6f1ff !important;
        caret-color: #c4a7ff !important;
        font-size: 14px !important;
        line-height: 1.4 !important;
        min-height: 26px !important;
        padding: 5px 7px !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* Remove the browser/Streamlit orange focus ring from the composer */
    [data-testid="stChatInput"]:focus,
    [data-testid="stChatInput"]:focus-within,
    [data-testid="stChatInput"] [data-baseweb="textarea"],
    [data-testid="stChatInput"] [data-baseweb="textarea"]:focus-within,
    [data-testid="stChatInput"] textarea:focus,
    [data-testid="stChatInput"] textarea:focus-visible {
        outline: none !important;
    }

    [data-testid="stChatInput"] [data-baseweb="textarea"],
    [data-testid="stChatInput"] [data-baseweb="textarea"]:focus-within,
    [data-testid="stChatInput"] textarea:focus,
    [data-testid="stChatInput"] textarea:focus-visible {
        box-shadow: none !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #a99bbf !important;
        opacity: 1 !important;
    }

    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #9a6af0 0%, #7042c4 55%, #59339f 100%) !important;
        border: 1px solid rgba(211, 188, 255, .48) !important;
        border-radius: 12px !important;
        min-width: 36px !important;
        min-height: 36px !important;
        width: 36px !important;
        height: 36px !important;
        color: #ffffff !important;
        box-shadow:
            0 5px 16px rgba(100, 57, 174, .32),
            inset 0 1px 0 rgba(255, 255, 255, .18) !important;
        transition: transform .18s ease, box-shadow .18s ease, filter .18s ease !important;
    }

    [data-testid="stChatInput"] button:hover {
        filter: brightness(1.12) !important;
        transform: translateY(-1px) !important;
        box-shadow:
            0 7px 20px rgba(119, 72, 202, .42),
            0 0 16px rgba(164, 119, 255, .2) !important;
    }

    [data-testid="stChatInput"] button:active {
        transform: translateY(0) scale(.97) !important;
    }

    [data-testid="stChatInput"] [data-testid="stFileUploader"] button,
    [data-testid="stChatInput"] button[aria-label*="Attach"],
    [data-testid="stChatInput"] button[aria-label*="attach"] {
        color: #d9c7ff !important;
    }

    /* Buttons */
    .stButton > button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stDownloadButton"] button,
    button[kind="primary"],
    button[kind="secondary"] {
        border-radius: 11px !important;
        transition: background .18s ease, border-color .18s ease, transform .18s ease !important;
    }

    .stButton > button,
    [data-testid="stFormSubmitButton"] button,
    button[kind="primary"] {
        background: linear-gradient(135deg, #7650bd, #593995) !important;
        border: 1px solid rgba(190, 163, 255, .38) !important;
        color: #fff !important;
    }

    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] button:hover,
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #8962d0, #6844aa) !important;
        border-color: rgba(210, 190, 255, .7) !important;
        transform: translateY(-1px);
    }

    [data-testid="stSidebar"] .stButton > button {
        min-height: 39px !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
        color: #d6cfe3 !important;
        text-align: left !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(130, 95, 190, .13) !important;
        border-color: rgba(174, 143, 232, .12) !important;
    }

    [data-testid="stSidebar"] input {
        background: #171222 !important;
        color: #f4efff !important;
        border: 1px solid rgba(174, 143, 232, .18) !important;
        border-radius: 11px !important;
    }

    [data-testid="stSidebar"] input:focus {
        border-color: #9a78df !important;
        box-shadow: 0 0 0 1px rgba(154, 120, 223, .25) !important;
    }

    .date-group {
        font-size: 11px !important;
        color: #8f83a5 !important;
        font-weight: 700 !important;
        letter-spacing: .5px !important;
        margin: 20px 0 8px 7px !important;
        text-transform: uppercase;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(174, 143, 232, .12) !important;
    }

    [data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 5px;
    }

    [data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: #493763;
        border-radius: 10px;
    }

    /* Form controls */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stSelectbox"] [role="combobox"],
    [data-testid="stMultiSelect"] [role="combobox"],
    [data-testid="stForm"] {
        background-color: #171222 !important;
        color: #f1ebfb !important;
        border-color: rgba(174, 143, 232, .25) !important;
        border-radius: 11px !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stNumberInput"] input:focus,
    [data-testid="stDateInput"] input:focus {
        border-color: #a78bfa !important;
        box-shadow: 0 0 0 1px rgba(129, 85, 217, .25) !important;
    }

    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        color: var(--nx-text) !important;
    }

    [data-testid="stAlert"] {
        border-color: rgba(129, 85, 217, .45) !important;
        border-radius: 12px !important;
    }

    h1, h2, h3 {
        color: #e1d4ff !important;
        letter-spacing: -.3px;
    }

    @media (max-width: 768px) {
        [data-testid="stChatInput"] {
            border-radius: 17px !important;
            padding: 2px 6px !important;
            box-shadow:
                0 10px 30px rgba(0, 0, 0, .34),
                0 0 20px rgba(126, 79, 214, .14) !important;
        }

        [data-testid="stChatInput"] textarea {
            font-size: 13px !important;
            line-height: 1.35 !important;
            min-height: 24px !important;
            padding: 4px 6px !important;
        }

        [data-testid="stChatInput"] button {
            min-width: 33px !important;
            min-height: 33px !important;
            width: 33px !important;
            height: 33px !important;
        }

        .block-container {
            padding: 1.2rem .8rem 6rem !important;
        }

        .welcome-container {
            min-height: 48vh;
        }

        .welcome-text {
            font-size: 24px !important;
        }

        [data-testid="stSidebar"] {
            border-right: none !important;
            min-width: 260px !important;
        }

        .st-key-nx_profile_button {
            top: 7px !important;
            right: 8px !important;
        }
    }
    

    /* FINAL GLASS OVERRIDES: top header, bottom composer tray, and sidebar search */
    [data-testid="stHeader"],
    header[data-testid="stHeader"] {
        background: rgba(8, 7, 20, .12) !important;
        background-color: rgba(8, 7, 20, .12) !important;
        border: 0 !important;
        box-shadow: none !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
    }

    [data-testid="stHeader"]::before,
    [data-testid="stHeader"]::after {
        background: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div {
        background: transparent !important;
        background-color: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
    }

    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"] {
        background: linear-gradient(180deg,
            rgba(8, 7, 20, 0) 0%,
            rgba(12, 9, 25, .08) 100%) !important;
        border: 0 !important;
        box-shadow: none !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
    }

    [data-testid="stChatInput"] {
        background: linear-gradient(135deg,
            rgba(42, 28, 67, .78),
            rgba(20, 15, 39, .78)) !important;
        border: 1px solid rgba(177, 143, 255, .48) !important;
        box-shadow: 0 12px 38px rgba(0, 0, 0, .24),
                    0 0 24px rgba(126, 79, 214, .18),
                    inset 0 1px 0 rgba(255, 255, 255, .07) !important;
    }

    [data-testid="stChatInput"] [data-baseweb="textarea"],
    [data-testid="stChatInput"] [data-baseweb="textarea"] > div,
    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        background-color: transparent !important;
    }

    [data-testid="stSidebar"] .st-key-sidebar_search,
    [data-testid="stSidebar"] .st-key-sidebar_search > div,
    [data-testid="stSidebar"] .st-key-sidebar_search [data-baseweb="input"],
    [data-testid="stSidebar"] .st-key-sidebar_search [data-baseweb="input"] > div {
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stSidebar"] .st-key-sidebar_search input {
        background: rgba(31, 22, 52, .76) !important;
        background-color: rgba(31, 22, 52, .76) !important;
        color: #f4efff !important;
        border: 1px solid rgba(174, 143, 255, .42) !important;
        border-radius: 12px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.06),
                    0 0 18px rgba(129,85,217,.10) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
    }

    /* FINAL COMPOSER INNER SURFACE FIX: keep the typing area transparent */
    [data-testid="stChatInput"] [data-baseweb="textarea"],
    [data-testid="stChatInput"] [data-baseweb="textarea"] > div,
    [data-testid="stChatInput"] [data-baseweb="textarea"] > div > div,
    [data-testid="stChatInput"] [data-baseweb="textarea"] textarea,
    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        background-color: transparent !important;
        color: #f6f1ff !important;
        border-color: transparent !important;
        box-shadow: none !important;
        -webkit-box-shadow: none !important;
    }

    [data-testid="stChatInput"] [data-baseweb="textarea"]:focus-within,
    [data-testid="stChatInput"] [data-baseweb="textarea"] > div:focus-within,
    [data-testid="stChatInput"] textarea:focus {
        background: transparent !important;
        background-color: transparent !important;
        outline: none !important;
    }

    /* Fix the actual gray BaseWeb surface identified in DevTools */
    [data-testid="stChatInput"] .st-emotion-cache-1bdk92a {
        background: linear-gradient(
            135deg,
            rgba(42, 28, 67, .78),
            rgba(20, 15, 39, .78)
        ) !important;
        background-color: rgba(31, 22, 52, .78) !important;
        border: 1px solid rgba(177, 143, 255, .34) !important;
        box-shadow: none !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #b8a9d2 !important;
        opacity: 1 !important;
    }

    /* NEXORA chat image card */
    [class*="st-key-nx_image_card_"] {
        width: fit-content !important;
        max-width: min(100%, 460px) !important;
        margin-top: 10px !important;
        margin-bottom: 8px !important;
        padding: 7px !important;
        border: 1px solid rgba(177, 143, 255, .22) !important;
        border-radius: 17px !important;
        background: rgba(18, 14, 31, .58) !important;
        box-shadow: 0 8px 26px rgba(0, 0, 0, .20) !important;
    }

    [class*="st-key-nx_image_card_"] img {
        display: block !important;
        width: 100% !important;
        max-width: 420px !important;
        height: auto !important;
        border-radius: 12px !important;
        cursor: zoom-in !important;
    }

    [class*="st-key-nx_image_card_"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 7px !important;
        margin-top: 6px !important;
    }

    [class*="st-key-nx_image_card_"] [data-testid="stButton"],
    [class*="st-key-nx_image_card_"] [data-testid="stDownloadButton"] {
        width: fit-content !important;
        margin: 0 !important;
    }

    [class*="st-key-nx_image_card_"] [data-testid="stButton"] button,
    [class*="st-key-nx_image_card_"] [data-testid="stDownloadButton"] button {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 36px !important;
        min-width: 36px !important;
        max-width: 36px !important;
        height: 34px !important;
        min-height: 34px !important;
        padding: 0 !important;
        border-radius: 10px !important;
        background: rgba(112, 66, 196, .22) !important;
        border: 1px solid rgba(177, 143, 255, .32) !important;
        color: #e8ddff !important;
        font-size: 16px !important;
        box-shadow: none !important;
    }

    [class*="st-key-nx_image_card_"] [data-testid="stButton"] button:hover,
    [class*="st-key-nx_image_card_"] [data-testid="stDownloadButton"] button:hover {
        background: rgba(129, 85, 217, .42) !important;
        border-color: rgba(194, 166, 255, .72) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
    }

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
MODEL = "qwen/qwen3.8-27b"

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


def _jwt_expiry(token):
    """Return JWT exp timestamp, or 0 when the token cannot be decoded."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return 0
        payload_part = parts[1]
        payload_part += "=" * (-len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_part.encode()))
        return int(payload.get("exp", 0))
    except Exception:
        return 0


def _store_auth_session(session, user=None, persist=True):
    """Keep Streamlit state, Supabase PostgREST auth, and cookie in sync."""
    if not session:
        raise Exception("لم تُرجع Supabase جلسة دخول صالحة.")

    st.session_state.access_token = session.access_token
    st.session_state.refresh_token = session.refresh_token

    if user:
        st.session_state.user = user

    supabase.postgrest.auth(session.access_token)

    if persist:
        save_session_cookie()


def _clear_auth_session():
    for key in ("user", "access_token", "refresh_token"):
        st.session_state[key] = None

    try:
        cookie_manager.delete(
            COOKIE_NAME,
            key="nexora_auth_expired",
            path="/",
        )
    except Exception:
        pass


def apply_token():
    """Refresh the access token before it expires and apply it to PostgREST."""
    access = st.session_state.get("access_token")
    refresh = st.session_state.get("refresh_token")

    if not refresh:
        if not access:
            return
        expiry = _jwt_expiry(access)
        if not expiry or expiry <= int(datetime.now(timezone.utc).timestamp()):
            _clear_auth_session()
            raise Exception("انتهت جلسة الدخول. سجّل الدخول مرة أخرى.")
        supabase.postgrest.auth(access)
        return

    now_ts = int(datetime.now(timezone.utc).timestamp())
    expiry = _jwt_expiry(access) if access else 0

    # Refresh if the token is expired, cannot be decoded, or has 5 minutes left.
    if not access or not expiry or expiry <= now_ts + 300:
        try:
            result = supabase.auth.refresh_session(refresh)
            if not result or not result.session:
                raise Exception("لم يتمكن Supabase من تجديد جلسة الدخول.")
            _store_auth_session(result.session, result.user)
            access = result.session.access_token
        except Exception as error:
            _clear_auth_session()
            raise Exception(
                "انتهت جلسة الدخول وتعذّر تجديدها. سجّل الخروج ثم ادخل مرة أخرى."
            ) from error

    supabase.postgrest.auth(access)


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

        old_access = tokens.get("access_token")
        refresh = tokens.get("refresh_token")
        if not refresh:
            raise Exception("لا يوجد Refresh Token في ملف الجلسة.")

        expiry = _jwt_expiry(old_access) if old_access else 0
        now_ts = int(datetime.now(timezone.utc).timestamp())

        # Do not try to restore an expired access token first.
        if not old_access or not expiry or expiry <= now_ts + 300:
            result = supabase.auth.refresh_session(refresh)
        else:
            try:
                result = supabase.auth.set_session(old_access, refresh)
            except Exception:
                # If the stored access token has expired, try the refresh token.
                result = supabase.auth.refresh_session(refresh)

        if not result or not result.session:
            raise Exception("تعذّرت استعادة جلسة Supabase.")

        _store_auth_session(result.session, result.user)

        if not st.session_state.user:
            user_result = supabase.auth.get_user()
            if user_result and user_result.user:
                st.session_state.user = user_result.user

    except Exception:
        _clear_auth_session()


def get_user_id():
    user = st.session_state.user
    return str(user.id) if user else None


def get_user_email():
    return getattr(st.session_state.user, "email", "") or ""
    

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

# محاولة استعادة الجلسة من الكوكيز
restore_session_cookie()

# استعادة الجلسة الحالية إذا كانت موجودة
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
if not st.session_state.user and not st.session_state.guest_mode:
    st.markdown(
        """
        <div class="welcome-container">
            <div class="welcome-logo">NEXORA AI</div>
            <div class="welcome-sub">مساعدك الذكي</div>
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
                        st.rerun()
                    else:
                        st.success(t("check_email"))
                except Exception:
                    st.error(t("error_signup"))

    st.divider()
    guest_label = "👤 الدخول كزائر — 10 رسائل" if st.session_state.language == "ar" else "👤 Continue as Guest — 10 messages"
    if st.button(guest_label, use_container_width=True):
        st.session_state.guest_mode = True
        st.session_state.guest_message_count = 0
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()

    st.stop()


if not st.session_state.guest_mode:
    try:
        apply_token()
    except Exception:
        st.warning("انتهت جلسة الدخول. سجّل الدخول مرة أخرى للمتابعة.")
        st.stop()

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
                {"role": "user", "content": question},
            ],
            max_tokens=40,
            temperature=0.2,
        )
        title = (result.choices[0].message.content or "").strip()
        title = re.sub(r"\s+", " ", title).strip("\"'`“” ")
        return title[:80] if title else question[:45]
    except Exception:
        return question[:45]



def _extract_document_text(file):
    """Extract text from common document formats using optional parsers."""
    name = file.name.lower()
    raw = file.getvalue()
    max_bytes = 15 * 1024 * 1024
    if len(raw) > max_bytes:
        return "[تجاوز الملف حد القراءة البالغ 15 MB]"

    if name.endswith((".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css", ".yaml", ".yml", ".xml", ".log")):
        return raw.decode("utf-8", errors="replace")[:18000]

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join((page.extract_text() or "") for page in reader.pages[:40])[:18000]
        except ImportError:
            return "[لقراءة PDF ثبّت pypdf في requirements.txt]"
        except Exception as exc:
            return f"[تعذرت قراءة PDF: {type(exc).__name__}]"

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(raw))
            return "\n".join(p.text for p in doc.paragraphs)[:18000]
        except ImportError:
            return "[لقراءة DOCX ثبّت python-docx في requirements.txt]"
        except Exception as exc:
            return f"[تعذرت قراءة DOCX: {type(exc).__name__}]"

    if name.endswith(".xlsx"):
        try:
            from openpyxl import load_workbook
            wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            chunks = []
            for ws in wb.worksheets[:8]:
                chunks.append(f"[Sheet: {ws.title}]")
                for row in ws.iter_rows(min_row=1, max_row=150, values_only=True):
                    vals = [str(v) if v is not None else "" for v in row[:20]]
                    if any(vals):
                        chunks.append(" | ".join(vals))
            wb.close()
            return "\n".join(chunks)[:18000]
        except ImportError:
            return "[لقراءة XLSX ثبّت openpyxl في requirements.txt]"
        except Exception as exc:
            return f"[تعذرت قراءة XLSX: {type(exc).__name__}]"

    if name.endswith(".pptx"):
        try:
            from pptx import Presentation
            prs = Presentation(io.BytesIO(raw))
            chunks = []
            for index, slide in enumerate(prs.slides[:40], 1):
                chunks.append(f"[Slide {index}]")
                for shape in slide.shapes:
                    if getattr(shape, "has_text_frame", False):
                        chunks.append(shape.text)
            return "\n".join(chunks)[:18000]
        except ImportError:
            return "[لقراءة PPTX ثبّت python-pptx في requirements.txt]"
        except Exception as exc:
            return f"[تعذرت قراءة PPTX: {type(exc).__name__}]"

    return "[نوع الملف غير مدعوم لاستخراج النص؛ يمكن إرفاقه للمراجعة اليدوية إن كان مدعوماً]"


def process_uploaded_files(files):
    parts = []
    image_contents = []

    for file in files:
        name = file.name
        mime = file.type or ""

        if mime.startswith("image/"):
            if len(image_contents) >= 3:
                parts.append("[تم تجاهل الصورة: الحد الأقصى 3 صور]")
                continue
            if file.size > 20 * 1024 * 1024:
                parts.append(f"[الصورة {name} أكبر من 20 MB]")
                continue
            try:
                image_data = base64.b64encode(file.getvalue()).decode("utf-8")
                image_contents.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{image_data}"},
                })
                parts.append(f"[صورة مرفقة: {name}]")
            except Exception:
                parts.append(f"[تعذرت قراءة الصورة: {name}]")
        else:
            extracted = _extract_document_text(file)
            parts.append(f"[محتوى الملف: {name}]\n{extracted}")

    return "\n\n".join(parts), image_contents



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


if not st.session_state.guest_mode:
    # =====================================
    # زر الملف الشخصي
    # =====================================
    with st.container(key="nx_profile_button"):
        if st.button("👤", key="nx_profile_open", help=t("profile")):
            st.session_state.show_profile = True
            st.session_state.show_settings = False
            st.rerun()


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
                        background:#211638;border:3px solid #7546C8;
                        display:flex;align-items:center;justify-content:center;
                        font-size:60px;color:#C4B5FD;">
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
        st.markdown(
            f'<div class="nexora-title">{t("app_title")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="nexora-subtitle">{t("subtitle")}</div>',
            unsafe_allow_html=True,
        )

        if st.button(t("new_chat"), use_container_width=True, type="primary"):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.session_state.show_settings = False
            st.rerun()

        search_query = st.text_input(
            "🔎",
            placeholder=t("search_placeholder"),
            label_visibility="collapsed",
            key="sidebar_search",
        )
    
        try:
            conversations = list_conversations()
        except Exception as error:
            st.error("حدث خطأ أثناء تحميل المحادثات:")
            st.exception(error)
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
                    title = conv.get("title") or t("new_chat")
                    active = str(st.session_state.conversation_id) == cid

                    col1, col2 = st.columns([6, 1], gap="small")

                    with col1:
                        label = title[:24] + ("…" if len(title) > 24 else "")
                        if st.button(
                            label,
                            key=f"open_{cid}",
                            use_container_width=True,
                            type="primary" if active else "tertiary",
                        ):
                            try:
                                st.session_state.conversation_id = cid
                                st.session_state.messages = load_messages(cid)
                                st.rerun()
                            except Exception as error:
                                show_error(error)

                    with col2:
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
        st.caption("👤 " + (st.session_state.profile_name or get_user_email()))

        if st.button("⚙️ " + t("settings_prefs"), use_container_width=True):
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


else:
    with st.sidebar:
        st.markdown('<div class="nexora-title">NEXORA AI</div>', unsafe_allow_html=True)
        st.caption("👤 " + ("وضع الزائر" if st.session_state.language == "ar" else "Guest mode"))
        st.caption(
            f"{'الرسائل المتبقية:' if st.session_state.language == 'ar' else 'Messages remaining:'} "
            f"{max(0, 10 - st.session_state.guest_message_count)} / 10"
        )
        if st.button("🚪 تسجيل الدخول / إنشاء حساب" if st.session_state.language == "ar" else "🚪 Login / Sign up", use_container_width=True):
            st.session_state.guest_mode = False
            st.session_state.guest_message_count = 0
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.rerun()


# =====================================
# شعار NEXORA المصغّر لرسائل المساعد
# =====================================
@st.cache_resource
def get_nexora_avatar():
    """Create the NEXORA purple orbital N mark in memory (no extra asset file)."""
    try:
        from PIL import Image, ImageDraw

        avatar = Image.new("RGBA", (96, 96), (12, 8, 24, 255))
        draw = ImageDraw.Draw(avatar)
        draw.ellipse((3, 3, 93, 93), fill=(27, 18, 45, 255),
                     outline=(160, 119, 239, 255), width=4)
        draw.arc((12, 12, 84, 84), start=205, end=335,
                 fill=(221, 202, 255, 255), width=3)
        draw.line([(29, 68), (29, 28), (67, 68), (67, 28)],
                  fill=(205, 180, 255, 255), width=8, joint="curve")
        draw.ellipse((70, 18, 79, 27), fill=(235, 218, 255, 255))
        return avatar
    except Exception:
        # Safe fallback if Pillow is unavailable in the deployment.
        return "✦"


# =====================================
# توليد الصور وتعديلها (للمستخدمين المسجلين فقط)
# =====================================
def image_request_type(prompt_text, uploaded_files):
    """Return generate/edit only for explicit image creation/edit requests."""
    text = (prompt_text or "").lower()

    edit_terms = (
        "عدّل", "عدل", "تعديل", "غيّر", "غير", "تغيير", "احذف", "حذف",
        "أضف", "اضف", "إضافة", "اضافة", "إزالة", "ازالة", "استبدل",
        "بدّل", "بدل", "حوّلها", "حولها", "حوّل الصورة", "حول الصورة",
        "خليها", "اجعل الخلفية", "غيّر الخلفية", "edit this", "edit the image",
        "modify this", "change the image", "remove from the image",
        "add to the image", "replace the", "retouch", "make the background",
        "turn it into", "make it", "cartoonize",
    )
    generate_terms = (
        "أنشئ صورة", "انشئ صورة", "ولد صورة", "ولّد صورة", "توليد صورة",
        "اصنع صورة", "اعمل صورة", "اعمل صوره", "اعمل صوره احترافيه",
        "اعمل صورة احترافية", "ارسم", "ارسم صورة", "صمم صورة", "صمّم صورة",
        "اريد صورة", "أريد صورة", "بدي صورة", "صورة احترافية", "صوره احترافيه",
        "generate an image", "generate image",
        "create an image", "make an image", "draw an image", "create a picture",
    )

    image_files = [file for file in (uploaded_files or []) if (file.type or "").startswith("image/")]
    if image_files and any(term in text for term in edit_terms):
        return "edit"
    if not image_files and any(term in text for term in generate_terms):
        return "generate"
    return None


def create_or_edit_image(prompt_text, uploaded_files=None):
    """Generate or edit an image through Cloudflare Workers AI FLUX.2 Klein 4B."""
    account_id = st.secrets.get("CLOUDFLARE_ACCOUNT_ID")
    api_token = st.secrets.get("CLOUDFLARE_API_TOKEN")

    if not account_id or not api_token:
        raise Exception(
            "بيانات Cloudflare غير مكتملة. افحص CLOUDFLARE_ACCOUNT_ID وCLOUDFLARE_API_TOKEN في Streamlit Secrets."
        )

    model_id = "@cf/black-forest-labs/flux-2-klein-4b"
    endpoint = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{account_id}/ai/run/{model_id}"
    )

    multipart_fields = {
        "prompt": (None, prompt_text or "Create a high-quality image."),
        "width": (None, "1024"),
        "height": (None, "1024"),
    }
    image_files = [
        file for file in (uploaded_files or [])
        if (getattr(file, "type", "") or "").startswith("image/")
    ]

    if len(image_files) > 4:
        raise Exception("يمكن تعديل الصورة باستخدام 4 صور مرجعية كحد أقصى.")

    if image_files:
        try:
            from PIL import Image
        except Exception as exc:
            raise Exception("مكتبة Pillow غير متوفرة لمعالجة الصورة المرفوعة.") from exc

        for index, source_file in enumerate(image_files):
            allowed_types = {"image/png", "image/jpeg", "image/webp"}
            if source_file.type not in allowed_types:
                raise Exception("تعديل الصور يدعم حاليًا PNG وJPG وWEBP فقط.")
            if source_file.size > 20 * 1024 * 1024:
                raise Exception("حجم كل صورة يجب ألا يتجاوز 20 MB.")

            try:
                image = Image.open(io.BytesIO(source_file.getvalue())).convert("RGB")
                image.thumbnail((512, 512))
                image_buffer = io.BytesIO()
                image.save(image_buffer, format="PNG", optimize=True)
                image_buffer.seek(0)
            except Exception as exc:
                raise Exception(f"تعذّرت قراءة الصورة المرفوعة: {source_file.name}") from exc

            multipart_fields[f"input_image_{index}"] = (
                f"reference_{index}.png",
                image_buffer.getvalue(),
                "image/png",
            )

    try:
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_token}"},
            files=multipart_fields,
            timeout=180,
        )
    except requests.RequestException as exc:
        raise Exception(f"تعذّر الاتصال بخدمة Cloudflare Workers AI: {exc}") from exc

    if not response.ok:
        try:
            error_data = response.json()
            details = error_data.get("errors") or error_data.get("messages") or error_data
            details_text = str(details)[:1200]
        except Exception:
            details_text = response.text[:1200]
        raise Exception(
            f"Cloudflare رفض طلب الصورة (HTTP {response.status_code}): {details_text}"
        )

    try:
        result_data = response.json()
    except ValueError:
        raise Exception("أرجعت Cloudflare استجابة غير مفهومة بدل بيانات الصورة.")

    result = result_data.get("result", result_data)
    encoded_image = result.get("image") if isinstance(result, dict) else None

    if not encoded_image:
        raise Exception(
            "لم تُرجع Cloudflare الصورة المتوقعة. تحقق من استجابة Workers AI وإعدادات النموذج."
        )

    try:
        image_bytes = base64.b64decode(encoded_image, validate=True)
    except Exception as exc:
        raise Exception("تعذّر فك ترميز الصورة التي أرجعتها Cloudflare.") from exc

    if not image_bytes:
        raise Exception("أرجعت Cloudflare ملف صورة فارغًا.")

    return image_bytes


def render_chat_image(image_bytes, key_suffix):
    """Render a compact image card with icon-only feedback and download controls."""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    feedback_key = f"nx_image_feedback_{key_suffix}"

    with st.container(key=f"nx_image_card_{key_suffix}"):
        st.markdown(
            f"""
            <a href="data:image/png;base64,{encoded}" target="_blank"
               rel="noopener noreferrer" title="Open full-size image"
               style="display:block;width:fit-content;max-width:100%;">
                <img src="data:image/png;base64,{encoded}"
                     alt="NEXORA generated image"
                     style="display:block;width:100%;max-width:420px;height:auto;
                            border-radius:12px;object-fit:contain;">
            </a>
            """,
            unsafe_allow_html=True,
        )

        like_col, dislike_col, spacer_col, download_col = st.columns(
            [1, 1, 7, 1], gap="small"
        )
        is_ar = st.session_state.language == "ar"

        with like_col:
            if st.button(
                "👍", key=f"nx_image_like_{key_suffix}",
                help="أعجبني" if is_ar else "Like this image",
            ):
                st.session_state[feedback_key] = "like"

        with dislike_col:
            if st.button(
                "👎", key=f"nx_image_dislike_{key_suffix}",
                help="لم يعجبني" if is_ar else "Dislike this image",
            ):
                st.session_state[feedback_key] = "dislike"

        with download_col:
            st.download_button(
                "⬇", data=image_bytes,
                file_name="nexora_image.png",
                mime="image/png",
                key=f"nx_image_download_{key_suffix}",
                help="حفظ الصورة" if is_ar else "Download image",
            )


# =====================================
# أدوات NEXORA: الوكلاء والبحث وتشغيل Python
# =====================================
WORK_MODES = {
    "normal": {
        "ar": "عادي", "en": "Normal",
        "instruction": "Answer naturally and helpfully. Keep the answer clear and appropriately concise."
    },
    "technical": {
        "ar": "تقني", "en": "Technical",
        "instruction": "Use precise technical language, explain assumptions, and provide practical step-by-step guidance and code when useful."
    },
    "research": {
        "ar": "بحث", "en": "Research",
        "instruction": "Prioritize evidence, source quality, dates, links, uncertainty, and structured findings. Never fabricate citations."
    },
    "creative": {
        "ar": "إبداعي", "en": "Creative",
        "instruction": "Explore original ideas and useful alternatives while staying practical and clear."
    },
}

QUICK_PROMPTS = [
    ("💡", "اقترح أفكارًا لمشروعي", "Suggest ideas for my project"),
    ("💻", "اشرح لي موضوعًا تقنيًا خطوة بخطوة", "Explain a technical topic step by step"),
    ("🔍", "ابحث عن معلومات موثوقة حول موضوع", "Research a topic using reliable sources"),
    ("🧠", "حلّل ملفًا واشرح أهم ما فيه", "Analyze a file and explain its key points"),
]


def _groq_text(messages, max_tokens=None, temperature=None):
    response = groq.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=st.session_state.temperature if temperature is None else temperature,
        max_tokens=st.session_state.max_tokens if max_tokens is None else max_tokens,
    )
    return (response.choices[0].message.content or "").strip()


def _looks_like_web_research(prompt, mode):
    p = prompt.casefold()
    terms = ["ابحث", "مصادر", "آخر الأخبار", "اليوم", "مقارنة حديثة", "معلومات حديثة", "research", "search the web", "latest", "current news", "sources", "look up"]
    return mode == "research" or any(term in p for term in terms)


def _web_research(prompt):
    """Optional Tavily search. Requires TAVILY_API_KEY in Streamlit Secrets."""
    try:
        api_key = st.secrets.get("TAVILY_API_KEY", "")
    except Exception:
        api_key = ""
    if not api_key:
        return "", "لم يتم إجراء بحث ويب خارجي: أضف TAVILY_API_KEY إلى Streamlit Secrets لتفعيل البحث الحقيقي."
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": prompt, "search_depth": "basic", "max_results": 5, "include_answer": False},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("results", [])
        formatted = []
        for item in items[:5]:
            title = item.get("title", "Source")
            url = item.get("url", "")
            content = item.get("content", "")[:1200]
            formatted.append(f"- {title}\n  URL: {url}\n  Summary: {content}")
        return "\n\n".join(formatted), ("تم العثور على مصادر ويب." if formatted else "لم يُرجع البحث مصادر.")
    except Exception as exc:
        return "", f"تعذر إكمال بحث الويب: {type(exc).__name__}."


def _extract_python_code(prompt):
    matches = re.findall(r"```(?:python|py)?\s*\n(.*?)```", prompt, flags=re.IGNORECASE | re.DOTALL)
    return matches[-1].strip() if matches else ""


def _wants_python_execution(prompt):
    p = prompt.casefold()
    triggers = ["شغّل الكود", "شغل الكود", "نفّذ الكود", "نفذ الكود", "نفذ بايثون", "شغّل python", "run this python", "execute this python", "run the code", "execute the code"]
    return bool(_extract_python_code(prompt)) and any(x in p for x in triggers)


def _execute_python_sandbox(code):
    """Execute code remotely in the Piston sandbox; user code is not eval'ed by this app."""
    if len(code) > 12000:
        return "تم رفض التنفيذ: الكود أطول من الحد المسموح (12,000 حرف)."
    try:
        response = requests.post(
            "https://emkc.org/api/v2/piston/execute",
            json={"language": "python", "version": "3.10.0", "files": [{"name": "main.py", "content": code}], "stdin": "", "args": [], "compile_timeout": 10000, "run_timeout": 5000, "compile_memory_limit": -1, "run_memory_limit": 50000000},
            timeout=18,
        )
        response.raise_for_status()
        data = response.json()
        run = data.get("run", {})
        output = (run.get("stdout", "") or "").strip()
        errors = (run.get("stderr", "") or "").strip()
        status = run.get("code")
        result = f"Exit code: {status}\nOutput:\n{output or '(no output)'}"
        if errors:
            result += f"\nErrors:\n{errors}"
        return result[:7000]
    except Exception as exc:
        return f"تعذر تشغيل Python في بيئة Piston المعزولة: {type(exc).__name__}. يمكنك المحاولة لاحقًا."


def run_multi_agent(prompt, history, image_contents=None):
    """Three sequential model roles: researcher, writer, and reviewer."""
    mode = st.session_state.get("work_mode", "normal")
    mode_instruction = WORK_MODES.get(mode, WORK_MODES["normal"])["instruction"]
    web_context, web_status = ("", "لم يُطلب بحث ويب.")
    if _looks_like_web_research(prompt, mode):
        web_context, web_status = _web_research(prompt)

    python_result = ""
    if _wants_python_execution(prompt):
        python_result = _execute_python_sandbox(_extract_python_code(prompt))

    status_lines = []
    with st.status("NEXORA AI — مراحل معالجة الطلب", expanded=False) as status:
        status.update(label="1/3 — الباحث: جمع السياق والمعلومات", state="running")
        researcher_prompt = (
            "You are the Researcher agent in NEXORA's three-stage workflow. "
            "Identify the user's actual question, extract relevant facts from the conversation, "
            "analyze attached content, and distinguish verified facts from unknowns. "
            "Use ONLY the web results supplied below as external research; do not invent sources. "
            "Return concise findings, uncertainties, and useful source URLs.\n\n"
            f"User request:\n{prompt}\n\nConversation context:\n{history}\n\n"
            f"Web results:\n{web_context or web_status}\n\nPython sandbox result:\n{python_result or 'Not requested.'}"
        )
        research = _groq_text([
            {"role": "system", "content": SYSTEM_PROMPT + "\nYou are the Researcher agent."},
            {"role": "user", "content": researcher_prompt},
        ], max_tokens=min(1100, st.session_state.max_tokens + 200), temperature=0.2)

        status.update(label="2/3 — الكاتب: إعداد الإجابة", state="running")
        writer = _groq_text([
            {"role": "system", "content": SYSTEM_PROMPT + "\nYou are the Writer agent. " + mode_instruction},
            {"role": "user", "content": f"User request:\n{prompt}\n\nResearcher findings:\n{research}\n\nWrite the best direct answer in the user's language. Include source URLs when supplied."},
        ], temperature=st.session_state.temperature)

        status.update(label="3/3 — المراجع: تدقيق الإجابة", state="running")
        reviewed = _groq_text([
            {"role": "system", "content": SYSTEM_PROMPT + "\nYou are the Reviewer agent. Check factual consistency, unsupported claims, clarity, safety, and whether the answer actually addresses the request. Do not reveal private chain-of-thought. Return only the corrected final answer."},
            {"role": "user", "content": f"Original request:\n{prompt}\n\nDraft answer:\n{writer}\n\nResearch notes for verification:\n{research}\n\nImprove and return the final answer only."},
        ], temperature=0.15)
        status.update(label="اكتملت المراحل الثلاث", state="complete")

    if web_status and web_status not in ("لم يُطلب بحث ويب.", "تم العثور على مصادر ويب."):
        reviewed += "\n\n---\n" + web_status
    if python_result:
        reviewed += (
            "\n\n**نتيجة تشغيل Python (بيئة Piston خارج التطبيق):**\n"
            "تنبيه: أُرسل الكود إلى خدمة تنفيذ خارجية معزولة؛ لا تضع كلمات مرور أو مفاتيح API أو بيانات خاصة داخل الكود.\n"
            "```text\n" + python_result + "\n```"
        )
    return reviewed or writer or research


# =====================================
# المحتوى الرئيسي
# =====================================

if st.session_state.guest_mode and st.session_state.guest_message_count >= 10:
    st.warning(
        "وصلت إلى الحد الأقصى وهو 10 رسائل. أنشئ حسابًا أو سجّل الدخول لمتابعة المحادثة."
        if st.session_state.language == "ar"
        else "You have reached the 10-message limit. Create an account or log in to continue."
    )
    if st.button("إنشاء حساب / تسجيل الدخول" if st.session_state.language == "ar" else "Create account / Log in", type="primary"):
        st.session_state.guest_mode = False
        st.session_state.guest_message_count = 0
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()

# وضع العمل
mode_label = "وضع العمل" if st.session_state.language == "ar" else "Work mode"
mode_options = list(WORK_MODES.keys())
mode_names = [WORK_MODES[key]["ar" if st.session_state.language == "ar" else "en"] for key in mode_options]
selected_mode = st.selectbox(
    mode_label,
    options=mode_options,
    format_func=lambda value: WORK_MODES[value]["ar" if st.session_state.language == "ar" else "en"],
    index=mode_options.index(st.session_state.get("work_mode", "normal")),
    key="nx_work_mode_select",
)
st.session_state.work_mode = selected_mode

if not st.session_state.messages:
    st.caption("اقتراحات سريعة" if st.session_state.language == "ar" else "Quick suggestions")
    quick_cols = st.columns(2)
    for idx, (emoji, ar_text, en_text) in enumerate(QUICK_PROMPTS):
        with quick_cols[idx % 2]:
            if st.button(f"{emoji} {ar_text if st.session_state.language == 'ar' else en_text}", key=f"nx_quick_{idx}", use_container_width=True):
                st.session_state.pending_prompt = ar_text if st.session_state.language == "ar" else en_text
                st.rerun()

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
    for message_index, message in enumerate(st.session_state.messages):
        with st.chat_message(
            message["role"],
            avatar=get_nexora_avatar() if message["role"] == "assistant" else None,
        ):
            st.markdown(message["content"])
            if message.get("image_b64"):
                image_data = base64.b64decode(message["image_b64"])
                render_chat_image(image_data, f"history_{message_index}")


# =====================================
# خانة الكتابة والمرفقات
# =====================================
chat_prompt = st.chat_input(
    t("chat_placeholder"),
    accept_file=False if st.session_state.guest_mode else "multiple",
    disabled=(
        st.session_state.guest_mode
        and st.session_state.guest_message_count >= 10
    ),
)
prompt = chat_prompt if chat_prompt is not None else st.session_state.pop("pending_prompt", None)

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
    image_contents = []

    if files:
        extra, image_contents = process_uploaded_files(files)

        if extra:
            final_prompt = (
                f"{user_text}\n\n---\n{extra}" if user_text else extra
            )

    try:
        is_guest = st.session_state.guest_mode

        # Enforce the guest limit before sending anything to an AI provider.
        if is_guest and st.session_state.guest_message_count >= 10:
            st.warning(
                "انتهت رسائل الزائر العشر. سجّل الدخول للمتابعة."
                if st.session_state.language == "ar"
                else "The 10 guest messages have been used. Log in to continue."
            )
            st.stop()

        request_type = image_request_type(user_text, files)

        # Image creation/editing is restricted to authenticated accounts.
        if is_guest and request_type in ("generate", "edit"):
            st.warning(
                "توليد الصور وتعديلها متاحان للمستخدمين المسجّلين فقط. سجّل الدخول لاستخدام هذه الميزة."
                if st.session_state.language == "ar"
                else "Image generation and editing are available to registered users only. Please log in."
            )
            st.stop()

        if not is_guest and not st.session_state.conversation_id:
            create_conversation()

        cid = str(st.session_state.conversation_id) if not is_guest else None
        first_message = len(st.session_state.messages) == 0

        st.session_state.messages.append({
            "role": "user",
            "content": final_prompt,
        })

        if not is_guest:
            save_message(cid, "user", final_prompt)

        with st.chat_message("user", avatar=None):
            st.markdown(final_prompt)

        generated_image_b64 = None
        with st.chat_message("assistant", avatar=get_nexora_avatar()):
            with st.spinner(t("thinking")):
                if request_type in ("generate", "edit"):
                    edit_images = [file for file in files if (file.type or "").startswith("image/")]
                    image_bytes = create_or_edit_image(user_text, edit_images if request_type == "edit" else None)
                    generated_image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                    answer = (
                        "تم إنشاء الصورة بنجاح." if request_type == "generate"
                        else "تم تعديل الصورة بنجاح."
                    ) if st.session_state.language == "ar" else (
                        "Image generated successfully." if request_type == "generate"
                        else "Image edited successfully."
                    )
                    st.markdown(answer)
                    render_chat_image(image_bytes, "generated")
                else:
                    user_content = [
                        {
                            "type": "text",
                            "text": final_prompt or "حلّل الصورة المرفقة واشرح ما يظهر فيها.",
                        }
                    ] + image_contents

                    # Preserve recent context; image payloads are passed to the researcher as multimodal input.
                    history_text = "\n\n".join(
                        f"{item['role']}: {item['content']}"
                        for item in st.session_state.messages[-12:-1]
                    )
                    agent_prompt = final_prompt or "حلّل الصورة المرفقة واشرح ما يظهر فيها."
                    if image_contents:
                        # Vision analysis is handled directly by the model with the supplied image payload.
                        vision_response = groq.chat.completions.create(
                            model=MODEL,
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT + "\nAnalyze the attached image accurately."},
                                {"role": "user", "content": user_content},
                            ],
                            temperature=st.session_state.temperature,
                            max_tokens=st.session_state.max_tokens,
                        )
                        image_analysis = (vision_response.choices[0].message.content or "").strip()
                        agent_prompt += "\n\nImage analysis supplied to the agents:\n" + image_analysis
                    answer = run_multi_agent(agent_prompt, history_text)
                    st.markdown(answer)

        assistant_message = {
            "role": "assistant",
            "content": answer,
        }
        if generated_image_b64:
            assistant_message["image_b64"] = generated_image_b64
        st.session_state.messages.append(assistant_message)

        if is_guest:
            st.session_state.guest_message_count += 1
        else:
            # Keep database chat_history text-only; image bytes remain in this session.
            save_message(cid, "assistant", answer)

            if first_message:
                update_title(cid, generate_title(final_prompt))

            update_activity(cid)

        st.rerun()

    except Exception as error:
        st.error("حدث خطأ أثناء إرسال الرسالة أو حفظها.")
        show_error(error)
