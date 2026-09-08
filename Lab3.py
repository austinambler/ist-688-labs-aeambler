import streamlit as st
from openai import OpenAI

st.title("My Lab3 question answering chatbot")

openAI_model = "gpt-4o-mini"

if 'client' not in st.session_state:
    api_key = st.secrets["OPEN_AI_KEY"]
    st.session_state.client = OpenAI(api_key = api_key)

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    chat_msg = st.chat_message(msg["role"])
    chat_msg.write(msg["content"])

# set buffer limit
max_messages = 2

# define function to get buffered messages
def get_buffered_messages(messages, max_messages = max_messages):

    system_msgs = [m for m in messages if m["role"] == "system"]
    user_idxs = [i for i, m in enumerate(messages) if m["role"] == "user"][-max_messages:]
    assistant_idxs = [i for i, m in enumerate(messages) if m["role"] == "assistant"][-max_messages:]

    keep_idxs = sorted(set(user_idxs + assistant_idxs))
    trimmed = [messages[i] for i in keep_idxs]

    return system_msgs + trimmed


if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    client = st.session_state.client

    buffered_messages = get_buffered_messages(st.session_state.messages)

    stream = client.chat.completions.create(
        model = openAI_model,
        messages = buffered_messages,
        stream = True
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})

