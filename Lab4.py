import streamlit as st
from openai import OpenAI
import sys

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from pathlib import Path
from pypdf import PdfReader
import os

if 'openai_client' not in st.session_state:
    api_key = st.secrets["OPEN_AI_KEY"]
    st.session_state.openai_client = OpenAI(api_key=api_key)

# Create ChromaDB client
chroma_client = chromadb.PersistentClient(path = './ChromaDB_for_Lab')
collection = chroma_client.get_or_create_collection('Lab4Collection')

def add_to_collection(collection, text, file_name):

    # Create an embedding
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input = text,
        model = 'text-embedding-3-small'
    )

    # Get the embedding
    embedding = response.data[0].embedding

    # Add embedding and document to ChromaDB
    collection.add(
        documents = [text],
        ids = file_name,
        embeddings = [embedding]
    )

# Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


# Populate collection with PDFs
# use extract_text_from_pdf
# and add_to_collection
def load_pdfs_to_collection(folder_path, collection):
    loaded_files = []
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith('.pdf'):
            pdf_path = os.path.join(folder_path, file_name)
            text = extract_text_from_pdf(pdf_path)

            if text.strip():  # skip empty extractions
                add_to_collection(collection, text, file_name)
                loaded_files.append(file_name)
            else:
                print(f"Warning: no text extracted from {file_name}")

    return loaded_files


# Check if collection is empty and load PDFs
if collection.count() == 0:
    loaded = load_pdfs_to_collection('./Lab-04-Data', collection)


    
st.title("My Lab4 Chatbot Using RAG")



topic = st.sidebar.text_input("Topic", placeholder = "Type your topic")

if topic:
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input = topic,
        model = 'text-embedding-3-small'
    )

    # Get the embedding
    query_embedding = response.data[0].embedding

    # Get text related to the question
    results = collection.query(
        query_embeddings=[query_embedding],
        n_result = 3
    )

    # Display the results
    st.subheader(f'Results for: {topic}')

    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        doc_id = results['ids'][0][i]

        st.write(f'**{i + 1}. {doc_id}**')

else:
    st.info('Enter a topic in the sidebar to search the collection')




openAI_model = "gpt-4o-mini"

SYSTEM_PROMPT = """You are a helpful assistant. Follow this conversation pattern strictly:

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
    if msg["role"] == "system":
        continue
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

