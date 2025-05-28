import streamlit as st
import database
import auth

st.set_page_config(
    page_title="TheraCare - Sign Up",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide the sidebar
st.markdown("""
    <style>
        section[data-testid="stSidebar"][aria-expanded="true"]{
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("TheraCare - Sign Up")
    
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sign Up"):
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            if database.get_user_by_username(username):
                st.error("Username already exists")
                return
            
            password_hash = auth.hash_password(password)
            user_id = database.create_user(username, email, password_hash)
            
            if user_id:
                # Set session state
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.session_state.logged_in = True
                st.session_state.token = auth.create_access_token({"sub": username})
                
                st.success("Account created successfully!")
                st.switch_page("pages/2_Dashboard.py")
            else:
                st.error("Error creating account")
    with col2:
        if st.button("Back to Login"):
            st.switch_page("pages/1_Login.py")

if __name__ == "__main__":
    main() 