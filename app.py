import requests
import streamlit as st
from streamlit_lottie import st_lottie
from PIL import Image

# Import the new no-embeddings backend
import scho_backend as backend

st.set_page_config(page_title="ScholarShelf", page_icon=":books:", layout="wide")

def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Use local CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style/style.css")

# ---- LOAD ASSETS ----
lottie_bot = load_lottieurl("https://lottie.host/668636f4-92fc-4f23-bc3b-4cc4a00e3604/fNTNcqHty9.json")
lottie_main = load_lottieurl("https://lottie.host/accf15ff-6219-42b5-af4b-51d5adf09168/dUSw7cGNNG.json")
lottie_log = load_lottieurl("https://lottie.host/edd2bf86-25e5-4be1-aff1-8d3769b38c8a/NI6Fi27xCo.json")
image = Image.open('logo-t.png')

# ---- BACKEND STARTUP: LOAD ANY SAVED CHUNKS (optional)
backend.load_chunks_from_disk()


# Function to render the homepage
def render_homepage():
    with st.container():
        left_column, right_column = st.columns(2)
        with left_column:
            st.title("Welcome to ScholarShelf!")
            st.write("Your AI-Powered Companion for Smarter, Faster Knowledge Discovery.")
            st.write("##")


        with right_column:
            # st_lottie(lottie_log, height=300, key="greet")
            st.image(image, width=300)  

    
    # User categories
    user_type = st.selectbox(
        "Who are you?",
        ["Select", "Student", "Professional", "Educator"]
    )

    if user_type in ["Student", "Professional", "Educator"]:
        main_dashboard()

# Main Dashboard
def main_dashboard():
# ---- HEADER SECTION ----
    with st.container():
        st.write("##")
        st_lottie(lottie_main, height=350, key="main")
        st.title("📑 ScholarShelf")
        st.subheader("Hi, I am SchoBot! 🤖 :wave:")
        st.write(
            "An adaptive learning tool, here to personalize the learning experience for you."
        )
        st.write(
            """
            - Build your own digital library by uploading books to your shelf.
            - Ask me anything, and I'll fetch answers directly from your collection!
            - Easy and Fun way to learn!

            Sounds interesting? Try now!!!
            """
        )

    # ---- SHELF SECTION ----
    with st.container():
        st.write("---")
        left_column, right_column = st.columns(2)
        with left_column:
            st.header("Your Sacred Library :books:")
            st.write("##")
            
            # Source selector
            source = st.selectbox(
                "Select source:",
                ["All Texts", "Bible (KJV)", "Quran"]
            )
            
            source_key = None
            if source == "Bible (KJV)":
                source_key = "bible"
            elif source == "Quran":
                source_key = "quran"
            
            st.caption(f"Searching: {source}")

            # File Upload
            uploaded_file = st.file_uploader("Add your files", type=["txt", "pdf", "docx"], accept_multiple_files=True)
            if uploaded_file:
                if st.button("Process Upload"):
                    result_msg = backend.process_files(uploaded_file)
                    st.success(result_msg)

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("Ask about scripture?"):
            # Display user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Get AI response
            response = backend.answer_user_query(prompt, source=source_key)

            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

        with right_column:
            st_lottie(lottie_bot, height=300, key="bot")

# Run the Streamlit app
if __name__ == "__main__":
    render_homepage()
