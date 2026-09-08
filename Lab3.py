import streamlit as st
from openai import OpenAI

st.title("My Lab3 question answering chatbot")

openAI_model = "gpt-4o-mini"

if 'client' not in st.session_state:
    api_key = st.secrets["OPEN_AI_KEY"]
    st.session_state.client = OpenAI(api_key = api_key)

SYSTEM_PROMPT = """You are a helpful assistant. Follow this conversation pattern strictly:

# This is for the 10-year old part
- Use simple, everyday words and short sentences.
- Avoid jargon and technical terms; if you must use one, explain it simply right after.
- Use relatable examples or comparisons (like toys, games, animals, or everyday situations) to make ideas easier to picture.
- Keep a friendly, encouraging tone.

1. Wait for the user to ask a question.
2. Answer the question clearly and concisely.
3. After answering, ask: "Do you want more info?"
4. If the user says yes (or anything affirmative):
   - Provide additional, more detailed information on the same topic.
   - Then ask again: "Do you want more info?"
   - Repeat this loop for as long as the user keeps saying yes.
5. If the user says no (or anything negative):
   - Respond with something like "Sounds good!" and then ask: "What can I help you with?"
   - Wait for a new question and start the pattern over from step 1.

Always keep track of the current topic so that "more info" responses stay relevant to the original question, until the user moves on to a new question.
"""

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "What can I help you with?"}
    ]

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

