
import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="CyberGain AI",
    page_icon="🛡️",
    layout="centered"
)

SYSTEM_PROMPT = """
أنت CyberGain AI، مساعد متخصص في IT وCloud والشبكات
وLinux وWindows Server والأمن السيبراني الدفاعي.

القواعد:
- أجب بالعربية البسيطة.
- اجعل الإجابة قصيرة، جملة أو جملتين.
- استخدم كلمات سهلة للمبتدئين.
- أعط مثالًا بسيطًا عند الحاجة.
- إذا طلب المستخدم خطوات، أعطه خطوة واحدة كل مرة.
- لا تخترع معلومات.
- ركز على الحماية والاستخدام المصرح به.
"""

st.title("🛡️ CyberGain AI")
st.caption("مساعدك في IT وCloud والشبكات")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.button("🗑️ محادثة جديدة"):
    st.session_state.messages = []
    st.rerun()

question = st.chat_input("اسأل عن IT أو Cloud...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("🧠 يفكر..."):
            try:
                api_key = st.secrets["GROQ_API_KEY"]
                client = Groq(api_key=api_key)

                chat_messages = [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    }
                ] + st.session_state.messages

                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=chat_messages,
                    max_tokens=120,
                    temperature=0.2
                )

                answer = response.choices[0].message.content

                if not answer:
                    answer = "ما وصلني جواب. جرّب تسأل مرة ثانية."

            except Exception as e:
                st.error(
                    f"نوع الخطأ: {type(e).__name__}"
                )
                st.error(str(e))
                answer = "تعذّر الحصول على رد. اقرأ الخطأ أعلاه."

            st.markdown(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
