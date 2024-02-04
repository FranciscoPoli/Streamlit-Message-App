import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime
import uuid
from main import load_css
from st_pages import hide_pages



def create_message(message):
    timestamp = datetime.datetime.now
    message_id = uuid.uuid4()
    new_message = pd.DataFrame(
        [
            {
                "Message ID": message_id,
                "Username": st.session_state["original_username"],
                "Message": message,
                "Timestamp": timestamp,
                "Like Count": int(0),
            }
        ]
    )
    return new_message


load_css()
conn = st.connection("gsheets", type=GSheetsConnection)

authentication_status = st.session_state.get("authentication_status", False)
if authentication_status:
    st.session_state["authenticator"].logout(location="sidebar")

    st.write(f'Username: :blue[{st.session_state["original_username"]}]')

    tab1, tab2 = st.tabs(["Post a Message", "Your Posts"])

    # Fetch existing messages data initially and store in session state
    if "existing_message_data" not in st.session_state:
        st.session_state["existing_message_data"] = conn.read(worksheet="Messages", usecols=list(range(5)), ttl=5).dropna(how="all")

    with tab1:
        with st.form("Post_Message", clear_on_submit=True):
            message = st.text_area("Post a Message", max_chars=200)
            posted = st.form_submit_button("Post", type="primary")

        if posted:
            new_message = create_message(message)

            # Add the new message data to the existing data
            updated_df = pd.concat([st.session_state["existing_message_data"], new_message], ignore_index=True)
            # Update messages in session state
            st.session_state["existing_message_data"] = updated_df

            # Update Google Sheets with the new message data
            conn.update(worksheet="Messages", data=updated_df)
            st.success("Message Posted")

    with tab2:
        current_user_messages = st.session_state.get("existing_message_data", []).query(f"Username == '{st.session_state['original_username']}'")

        if current_user_messages.empty is False:

            messages = current_user_messages['Message']
            like_counts = current_user_messages['Like Count']
            for message, like_count in zip(messages, like_counts):
                div = f"""
                <div class="user-line">
                    <p><strong>{st.session_state['original_username']}</strong> <span style="color: white;">posted:</span></p>
                </div>          
                    <div class="chat-bubble">
                        <p>{message}</p>
                        <p style="text-align: right; color: orange;"><strong>Likes: {int(like_count)}</strong></p>
                    </div>
                
                """
                st.markdown(div, unsafe_allow_html=True)
        else:
            st.write("You have posted no messages yet")

else:
    # hide_pages(["Feed", "My Messages", "Follow Requests", "My Profile"])
    # st.switch_page("main.py")
    st.write('Please login')

