import streamlit as st
import database
import auth

st.set_page_config(
    page_title="TheraCare - Login",
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
    st.title("TheraCare - Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            user = database.get_user_by_username(username)
            if user and auth.verify_password(password, user[3]):  # user[3] is password_hash
                token = auth.create_access_token({"sub": user[1]})  # user[1] is username
                st.session_state.token = token
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_id = user[0]  # user[0] is id
                st.switch_page("pages/2_Dashboard.py")
            else:
                st.error("Invalid username or password")
    with col2:
        if st.button("Sign Up"):
            st.switch_page("pages/3_Signup.py")

if __name__ == "__main__":
    main() 