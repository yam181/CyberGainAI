            ):
                st.session_state[f"confirm_{cid}"] = True

        if st.session_state.get(f"confirm_{cid}", False):
            st.caption(f"حذف «{title}»؟")
            yes_col, no_col = st.columns(2)

            with yes_col:
                if st.button("نعم", key=f"yes_{cid}"):
                    try:
                        delete_conversation(cid)
                        st.session_state.pop(
                            f"confirm_{cid}", None
                        )
                        st.rerun()
                    except Exception as e:
                        show_error(e)

            with no_col:
                if st.button("إلغاء", key=f"no_{cid}"):
                    st.session_state.pop(
                        f"confirm_{cid}", None
                    )
                    st.rerun()


# =====================================
# واجهة المحادثة
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
        first_message = len(st.session_state.messages) == 0

        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
        })

        save_message(cid, "user", prompt)

        with st.chat_message("user", avatar=None):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=None):
            with st.spinner("NEXORA يفكّر..."):
                result = groq.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
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

        if first_message:
            update_title(cid, generate_title(prompt))

        update_activity(cid)
        st.rerun()

    except Exception as e:
        st.error("حدث خطأ أثناء إرسال الرسالة أو حفظها.")
        show_error(e)
