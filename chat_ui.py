import streamlit as st
from datetime import datetime
from rag import ask_bot  # import your chatbot function here

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="centered")

# Title and description
st.title("🤖 Personal Assistant Chatbot")
st.write("Ask me anything — I can answer questions, check your calendar, or explain your notes!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Type your message here..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask_bot(prompt)  # <--- your function from your RAG + calendar system
            st.markdown(response)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
