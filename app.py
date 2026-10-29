/* ===== إخفاء كل عناصر Streamlit العلوية ===== */
#MainMenu {visibility: hidden !important; display: none !important;}
footer {visibility: hidden !important; display: none !important;}
header {visibility: hidden !important; display: none !important;}
[data-testid="stHeader"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stDeployButton {display: none !important;}
button[kind="header"] {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}

/* إخفاء الشريط العلوي بالكامل */
.stApp > header {
    display: none !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}
