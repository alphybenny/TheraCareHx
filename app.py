import streamlit as st
from database import init_db
import auth

# Hide the sidebar navigation
st.set_page_config(
    page_title="TheraCare",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize database
init_db()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "gorilla_id" not in st.session_state:
    st.session_state.gorilla_id = None

# Check authentication
def check_auth():
    if not st.session_state.logged_in:
        st.switch_page("pages/1_Login.py")

# Main app
def main():
    if not st.session_state.logged_in:
        st.switch_page("pages/1_Login.py")
    else:
        st.switch_page("pages/2_Dashboard.py")

if __name__ == "__main__":
    main() 