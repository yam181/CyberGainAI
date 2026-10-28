
import streamlit as st
import requests

st.set_page_config(
    page_title="CyberGain AI",
    page_icon="🛡️",
    layout="centered"
)

SYSTEM_PROMPT = """
أنت CyberGain AI، معلم متخصص في IT وCloud والشبكات وLinux
وWindows Server والأمن السيبراني الدفاعي.

قواعدك:
1. أجب بالعربية البسيطة.
2. أجب بجملة أو جملتين فقط.
3. استخدم كلمات سهلة جدًا للمبتدئين.
4. أعطِ مثالًا بسيطًا عند الحاجة.
5. لا تضف تفاصيل غير ضرورية.
6. إذا طلب المستخدم خطوات، أعطه خطوة واحدة كل مرة.
7. إذا لم يفهم المستخدم، اشرح بطريقة أسهل.
8. لا تخترع معلومات.
9. ركّز على حماية الأجهزة والشبكات.
10. لا تطلب كلمات مرور أو مفاتيح سرية.
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

question = st.chat_input("اسأل سؤالك عن IT أو Cloud...")

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
                conversation = [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ] + st.session_state.messages

                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "llama3.2:3b",
                        "messages": conversation,
                        "stream": False,
                        "options": {
                            "num_predict": 80,
                            "temperature": 0.2
                        }
                    },
                    timeout=180
                )

                response.raise_for_status()
                answer = response.json()["message"]["content"]

            except requests.exceptions.ConnectionError:
                answer = "❌ شغّل Ollama ثم حاول مرة ثانية."

            except requests.exceptions.Timeout:
                answer = "⏳ تأخر الرد. حاول مرة ثانية."

            except requests.exceptions.RequestException:
                answer = "❌ حدث خطأ بالاتصال."

            except (KeyError, ValueError):
                answer = "❌ حدث خطأ في قراءة الرد."

            st.markdown(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

