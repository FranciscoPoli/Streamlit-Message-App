import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from st_pages import hide_pages


def change_status(is_public):
    # Access and update user data from session state
    existing_user_data = st.session_state.get("existing_user_data", [])
    existing_user_data.loc[existing_user_data['Username'] == f'{st.session_state["original_username"]}', 'Profile Public'] = not is_public  # Toggle the value

    # Update Google Sheets and session state
    conn.update(worksheet="Users", data=existing_user_data)
    st.session_state["existing_user_data"] = existing_user_data


conn = st.connection("gsheets", type=GSheetsConnection)

authentication_status = st.session_state.get("authentication_status", False)
if authentication_status:
    st.session_state["authenticator"].logout(location="sidebar")

    st.write(f'Username: :blue[{st.session_state["original_username"]}]')

    # Fetch existing user data initially and store in session state
    if "existing_user_data" not in st.session_state:
        st.session_state["existing_user_data"] = conn.read(worksheet="Users", usecols=list(range(3)), ttl=35).dropna(how="all")


    current_user = st.session_state["existing_user_data"].query(f"Username == '{st.session_state['original_username']}'")
    is_public = current_user['Profile Public'].iloc[0]

    if is_public:
        st.write('Your profile is public. Everybody can read your Posts')
    else:
        st.write('Your profile is private. People have to follow you to read your Posts')

    profile_status = st.toggle('Profile Public', value=is_public, key="profile_toggle", on_change=change_status, args=[is_public])


else:
    # hide_pages(["Feed", "My Messages", "Follow Requests", "My Profile"])
    # st.switch_page("main.py")
    st.write('Please login')