import base64
from pathlib import Path
from openai import OpenAI
import streamlit as st

client = OpenAI(api_key = st.secrets["OPEN_AI_KEY"])

def prepare_image(upload):
    formats = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg"
    }

    mime = formats[Path(upload.name).suffix.lower()]
    encoded = base64.b64encode(upload.getvalue()).decode("utf-8")

def transcribe_audio(upload):
    transcript = client.audio.transcriptions.create(
        model = "gpt-transcribe",
        file = (upload.name, upload.getvalue()))
    return transcript.text

def analyze_content(content, prompt):
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=prompt,
        input=[
            {
                "role": "user",
                "content": content
            }
        ],
        max_output_tokens=600
    )

    return response.output_text

# Check audio duration
def get_audio_duration(upload):
    audio = MutagenFile(BytesIO(upload.getvalue()))

    if audio is None:
        return None

    return audio.info.length


# -----------------------------
# STREAMLIT INTERFACE
# -----------------------------

st.title("Multimodal Content Analyzer")

st.write("Upload an image or audio file for AI-powered analysis.")

# Select input type
input_type = st.selectbox(
    "Select Input Type",
    ["Image", "Audio"]
)

# File uploader
if input_type == "Image":
    upload = st.file_uploader(
        "Upload an Image",
        type=["png", "jpg", "jpeg"]
    )

else:
    upload = st.file_uploader(
        "Upload an Audio File",
        type=["mp3", "wav", "m4a"]
    )

# Preview uploaded file
if upload is not None:

    # Check file size (5 MB maximum)
    if upload.size > 5 * 1024 * 1024:
        st.error("File exceeds the 5 MB limit.")
        upload = None

    else:
        if input_type == "Image":
            st.image(upload, caption="Uploaded Image", use_container_width=True)

        else:
            st.audio(upload)

            duration = get_audio_duration(upload)

            if duration is None:
                st.error("Unable to determine audio duration. Please upload a supported audio format.")
                upload = None

            elif duration > 60:
                st.error("Audio clip exceeds the 60-second limit.")
                upload = None

# Optional question
question = st.text_input(
    "Ask a question (Optional)",
    placeholder="What would you like to know about this content?"
)

# Analyze button
if st.button("Analyze"):

    if upload is None:
        st.warning("Please upload a valid file first.")

    else:

        # Default prompt if no question is provided
        if not question.strip():
            prompt = "Analyze the provided content and describe the important details."
        else:
            prompt = question

        with st.spinner("Analyzing content..."):

            try:

                if input_type == "Image":

                    content = [
                        {"type": "input_text", "text": prompt},
                        prepare_image(upload)
                    ]

                    result = analyze_content(content, "Analyze the uploaded image.")

                else:

                    transcript = transcribe_audio(upload)

                    content = [
                        {
                            "type": "input_text",
                            "text": f"Here is the audio transcript:\n{transcript}"
                        }
                    ]

                    result = analyze_content(content, prompt)

                st.subheader("Analysis Results")
                st.write(result)

            except Exception as e:
                st.error(f"An error occurred: {e}")