import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageOps
import html

# FastAPI Server URL

st.set_page_config(page_title="AI Chatbot & Email Assistant", layout="wide")

# Load CSS from external file
def load_css(file_name):
    with open(file_name, "r") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Call the function to load CSS
load_css("style.css")
FASTAPI_URL = "http://127.0.0.1:8000"


# Load user profile image
user_image_path = "C:/Users/shris/OneDrive/Pictures/photo.jpeg"
user_image = Image.open(user_image_path)

# Make the image circular
def make_circle(img):
    size = (100, 100)
    img = img.resize(size, Image.LANCZOS)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    img = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
    img.putalpha(mask)
    return img

circular_user_image = make_circle(user_image)

# Streamlit Page Config

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "emails" not in st.session_state:
    st.session_state.emails = []
if "selected_email" not in st.session_state:
    st.session_state.selected_email = ""
if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""
if "db_query" not in st.session_state:
    st.session_state.db_query = ""
if "db_result" not in st.session_state:
    st.session_state.db_result = ""

# Sidebar - AI Chatbot
with st.sidebar:
    st.markdown("<h3 style='text-align: center; font-size: 25px;'>🧐 AI Chatbot</h3>", unsafe_allow_html=True)
    chat_container = st.container()
    user_message = st.text_input("", placeholder="Ask anything... ⬇️", key="chat_input", label_visibility="collapsed")

    if user_message and "last_chat_input" not in st.session_state or user_message != st.session_state.get("last_chat_input", ""):
        st.session_state.last_chat_input = user_message
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        response = requests.post(f"{FASTAPI_URL}/chatBot", json={"message": user_message})
        ai_response = response.json().get("response", "Error in response")
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    with chat_container:
        for chat in st.session_state.chat_history:
            col1, col2 = st.columns([1, 9])
            with col1:
                if chat["role"] == "user":
                    st.image(circular_user_image, width=40)
                else:
                    st.markdown("🧐")
            with col2:
                st.markdown(f"**{'You' if chat['role'] == 'user' else 'AI'}:** {chat['content']}")

# Layout: Two Columns
col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("<h3 style='text-align: center; font-size: 30px;'>📬 Email Assistant</h3>", unsafe_allow_html=True)

    # Fetch latest emails
    if not st.session_state.emails:
        response = requests.post(f"{FASTAPI_URL}/get_email")
        emails = response.json().get("latest_emails", [])
        st.session_state.emails = emails.split("\n\n---\n\n")

    # Email selection
    selected_email = st.selectbox("Select an Email", ["-- Select an email --"] + st.session_state.emails)
    if selected_email != "-- Select an email --":
        st.session_state.selected_email = selected_email

    # Display selected email
    if st.session_state.selected_email:
        st.markdown(f"<div class='email-card'><b>📜 Selected Email:</b><br>{st.session_state.selected_email}</div>", unsafe_allow_html=True)

        if st.button("Generate AI Response", key="generate_response"):
            if "last_email_processed" not in st.session_state or st.session_state.selected_email != st.session_state.last_email_processed:
                st.session_state.last_email_processed = st.session_state.selected_email
                response = requests.post(f"{FASTAPI_URL}/email_chatBot", json={"email_content": st.session_state.selected_email})
                st.session_state.ai_response = response.json().get("response", "Failed to generate response.")

        if st.session_state.ai_response:
            st.markdown(f"<div class='email-card'><b>🧐 AI-Generated Reply:</b><br>{st.session_state.ai_response}</div>", unsafe_allow_html=True)

# Vertical Divider
st.markdown("<hr style='border: 1px solid #ccc;'>", unsafe_allow_html=True)

with col2:
    st.markdown("<h3 style='text-align: center; font-size: 28px;'>🔍 Interaction with Database</h3>", unsafe_allow_html=True)
    db_query = st.text_area("Enter a natural language query:", placeholder="How many work orders are there?")

    if st.button("Generate Ans :-", key="query_db"):
        if db_query:
            response = requests.post(f"{FASTAPI_URL}/query-database-nl", json={"query": db_query})
            st.session_state.db_result = response.json().get("result", "Failed to fetch data.")

    if st.session_state.db_result:
        st.markdown(f"<div class='query-container'><b>📊 Query Result:</b><br>{st.session_state.db_result}</div>", unsafe_allow_html=True)
