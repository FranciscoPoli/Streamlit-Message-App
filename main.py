import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_option_menu import option_menu
from st_pages import Page, show_pages, hide_pages


def load_css():
    with open("static/styles.css", "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)


def inputs_unchanged(usernames, passwords):
    # Initialize session states to compare in future runs
    if "username_list" not in st.session_state:
        st.session_state["username_list"] = usernames
    if "password_list" not in st.session_state:
        st.session_state["password_list"] = passwords

    # Check if usernames or passwords have been changed or added
    return st.session_state["username_list"] == usernames and st.session_state["password_list"] == passwords


def st_authentication():
    # Fetch data if not already in session state
    if "existing_user_data" not in st.session_state:
        st.session_state["existing_user_data"] = conn.read(worksheet="Users", usecols=list(range(3)), ttl=5).dropna(how="all")
    # existing_user_data = conn.read(worksheet="Users", usecols=list(range(3)), ttl=5).dropna(how="all")
    existing_user_data = st.session_state["existing_user_data"]

    usernames = existing_user_data["Username"].tolist()
    passwords = existing_user_data["Password"].tolist()

    unchanged = inputs_unchanged(usernames, passwords)

    # create dictionary to pass credentials to stauth.Authenticate
    credentials = {"usernames": {}}
    for username, password in zip(usernames, passwords):
        credentials["usernames"][username] = {"password": password, "name": ""}

    if "authenticator" not in st.session_state or not unchanged:
        authenticator = stauth.Authenticate(credentials, cookie_name="Practice_Twitter", key="uihlkoadfi54",
                                        cookie_expiry_days=0.2)
        st.session_state["authenticator"] = authenticator
    # if "authenticator" not in st.session_state:
    #     st.session_state["authenticator"] = authenticator


def signUp():
    authentication_status = st.session_state.get("authentication_status", False)
    if authentication_status:
        st.write(f'You are already logged in *{st.session_state["username"]}*')
        st.session_state["authenticator"].logout(location="sidebar")
    else:
        with st.form("User Creation"):
            username = st.text_input("Choose a username").lower()
            password = st.text_input("Create a password", type = "password")
            password_confirm = st.text_input("Confirm password", type = "password")
            submitted = st.form_submit_button("Submit")


        if submitted:
            # Fetch existing user data
            existing_user_data = st.session_state["existing_user_data"]

            if username == "":
                st.warning("Please enter a username")
                st.stop()

            elif existing_user_data["Username"].isin([username]).any():
                st.warning("That username is already taken")

            elif password == "":
                st.warning("Please enter a password")
                st.stop()

            elif password != password_confirm:
                st.warning("The passwords do not match")
                st.stop()

            else:
                password_list = []
                password_list.append(password)
                hashed_passwords = stauth.Hasher(password_list).generate()
                new_user_data = pd.DataFrame(
                    [
                        {
                            "Username":username,
                            "Password":hashed_passwords[0],
                            "Profile Public": True
                        }
                    ]
                )
                # Add the new user data to the existing data
                updated_df = pd.concat([existing_user_data, new_user_data], ignore_index=True)

                # Update session state
                st.session_state["existing_user_data"] = updated_df
                # Update Google Sheets with the new user data
                conn.update(worksheet="Users", data=updated_df)

                st.success("User created")

def logIn():

    st_authentication()
    st.session_state["authenticator"].login(fields={'Form name': 'Login'}, location="main")

    if st.session_state["authentication_status"]:
        st.session_state["authenticator"].logout(location="sidebar")
        st.write(f'Welcome *{st.session_state["username"]}*')
        st.title('Some content')
    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] is None:
        st.warning('Please enter your username and password')

st.set_page_config(page_title='Streamlit practice Twitter', layout='wide')


show_pages(
        [
            Page("main.py", "Login"),
            Page("pages/1_Feed.py", "Feed"),
            Page("pages/2_Messages.py", "My Messages"),
            Page("pages/4_Follow_Requests.py", "Follow Requests"),
            Page("pages/5_User_Profile.py", "My Profile"),

        ]
)

# Establishing a Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None

if st.session_state["authentication_status"]:
    st.session_state["authenticator"].logout(location="sidebar")
    # hide_pages(["Login"])
    # st.switch_page("pages/1_Feed.py")
    st.markdown("You are already logged in")

else:
    # hide_pages(["Feed", "My Messages", "Follow Requests", "My Profile"])
    st.title("Hi! Welcome to my practice Twitter.")
    st.markdown("Please login or create a new user!")

    _, col, _ = st.columns([2.5, 5, 2.5])
    with col:
        toggle_bar = option_menu(
                    menu_title=None,
                    options=["Log In", "Sign Up!"],
                    orientation="horizontal",
                    styles={
                        "container": {"padding": "0!important"},
                        "nav-link": {
                            "font-size": "20px",
                            "margin": "0px",
                            "text-align": "center",
                            "--hover-color": "#bbb"},
                        "nav-link-selected": {"font-weight": "bold"}
                    }
                )


    if toggle_bar == "Sign Up!":
        signUp()

    elif toggle_bar == "Log In":
        logIn()

