import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageOps
# FastAPI Server URL
FASTAPI_URL = "http://127.0.0.1:8000"


user_image_path = "C:/Users/shris/OneDrive/Pictures/photo.jpeg"
user_image = Image.open(user_image_path)

# Make the image circular
def make_circle(img):
    size = (100, 100)  # Set desired size
    img = img.resize(size, Image.LANCZOS)  # Use LANCZOS instead of ANTIALIAS
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    img = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
    img.putalpha(mask)
    return img

circular_user_image = make_circle(user_image)

# Streamlit Page Config
st.set_page_config(page_title="AI Chatbot & Email Assistant", layout="wide")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "emails" not in st.session_state:
    st.session_state.emails = []
if "selected_email" not in st.session_state:
    st.session_state.selected_email = None
if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""


with st.sidebar:
    st.title("🤖 AI Chatbot")
    chat_container = st.container()
    user_message = st.text_input("", placeholder="Ask anything...                                        ⬇️", key="chat_input")
    
    if user_message:
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        response = requests.post(f"{FASTAPI_URL}/chatBot", json={"message": user_message})
        ai_response = response.json().get("response", "Error in response")
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        
        # Clear the input box after entry
        st.session_state.user_message = ""
    
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                col1, col2 = st.columns([1, 9])  # Two-column layout
                with col1:
                    st.image(circular_user_image, width=40)  # Show user profile picture
                with col2:
                    st.markdown(f"**You:** {chat['content']}")  # Show user message
            else:
                col1, col2 = st.columns([1, 9])
                with col1:
                    st.markdown("🤖")  # Show AI icon
                with col2:
                    st.markdown(f"**AI:** {chat['content']}")  # Show AI response

# Main Content: Email Assistant
st.title("📩 Email Assistant")

# Fetch latest emails if not already loaded
if not st.session_state.emails:
    response = requests.post(f"{FASTAPI_URL}/get_email")
    emails = response.json().get("latest_emails", [])
    st.session_state.emails = emails.split("\n\n---\n\n")  # Splitting emails using separator

# Display emails in a dropdown
selected_email = st.selectbox("Select an Email", ["-- Select an email --"] + st.session_state.emails)
if selected_email != "-- Select an email --":
    st.session_state.selected_email = selected_email

# Display selected email content
if st.session_state.selected_email:
    st.subheader("📜 Selected Email:")
    st.text_area("Email Content", st.session_state.selected_email, height=200, disabled=True)

    if st.button("Generate AI Response"):
        response = requests.post(f"{FASTAPI_URL}/generate-email-response", json={"email": st.session_state.selected_email})
        st.session_state.ai_response = response.json().get("email_response", "Failed to generate response.")

    if st.session_state.ai_response:
        st.subheader("🤖 AI-Generated Reply:")
        st.text_area("AI Reply", st.session_state.ai_response, height=200)
