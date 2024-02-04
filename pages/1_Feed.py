import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from main import load_css
from st_pages import hide_pages

def show_message(username, message, like_count):
    div = f"""
            <div class="user-line">
                <p><strong>{username}</strong> <span style="color: white;">posted:</span></p>
            </div>          
                <div class="chat-bubble">
                    <p>{message}</p>
                    <p style="text-align: right; color: orange;"><strong>Likes: {int(like_count)}</strong></p>
                </div>
    
            """
    st.markdown(div, unsafe_allow_html=True)
    return div


def change_like_status(message_ID):
    existing_message_data = st.session_state.get("existing_message_data", [])
    existing_like_data = st.session_state.get("existing_like_data", [])

    like_status = st.session_state.get(f"like_status{message_ID}", False)

    if like_status:
        # Decrease like count and remove like
        like_count = existing_message_data.loc[existing_message_data["Message ID"] == message_ID, "Like Count"] - 1
        existing_message_data.loc[existing_message_data["Message ID"] == message_ID, "Like Count"] = like_count
        existing_like_data = existing_like_data.loc[(existing_like_data["Message ID"] != message_ID)
                                                    | ((existing_like_data["Message ID"] == message_ID)
                                                    & (existing_like_data["Username"] != st.session_state["original_username"]))
                                                    ]
    else:
        # Increase like count and add like
        like_count = existing_message_data.loc[existing_message_data["Message ID"] == message_ID, "Like Count"] + 1
        existing_message_data.loc[existing_message_data["Message ID"] == message_ID, "Like Count"] = like_count
        new_like_data = pd.DataFrame(
            [
                {"Username": st.session_state["original_username"],
                 "Message ID": message_ID}
            ]
        )
        existing_like_data = pd.concat([existing_like_data, new_like_data], ignore_index=True)

    # Update session state
    st.session_state[f"like_status{message_ID}"] = not like_status
    st.session_state["existing_message_data"] = existing_message_data
    st.session_state["existing_like_data"] = existing_like_data

    # Update Google Sheets
    conn.update(worksheet="Likes", data=existing_like_data)
    conn.update(worksheet="Messages", data=existing_message_data)


load_css()
conn = st.connection("gsheets", type=GSheetsConnection)

authentication_status = st.session_state.get("authentication_status", False)
if authentication_status:
    st.session_state["authenticator"].logout(location="sidebar")

    st.write(f'Username: :blue[{st.session_state["original_username"]}]')
    tab1, tab2, tab3 = st.tabs(["Feed", "Liked Messages", "Search for Message"])

    # Fetch data if not already in session state
    if "existing_message_data" not in st.session_state:
        st.session_state["existing_message_data"] = conn.read(worksheet="Messages", usecols=list(range(5)), ttl=35).dropna(how="all")
    if "existing_user_data" not in st.session_state:
        st.session_state["existing_user_data"] = conn.read(worksheet="Users", usecols=list(range(3)), ttl=35).dropna(how="all")
    if "existing_like_data" not in st.session_state:
        st.session_state["existing_like_data"] = conn.read(worksheet="Likes", usecols=list(range(2)), ttl=35).dropna(how="all")
    if "existing_follow_data" not in st.session_state:
        st.session_state["existing_follow_data"] = conn.read(worksheet="Follows", usecols=list(range(3)), ttl=35).dropna(how="all")

    existing_message_data = st.session_state["existing_message_data"]
    existing_user_data = st.session_state["existing_user_data"]
    existing_like_data = st.session_state["existing_like_data"]
    existing_follow_data = st.session_state["existing_follow_data"]

    # Initialize like status from Google Sheets
    for message_ID in existing_like_data["Message ID"]:
        # Check like status directly in the dataframe
        like_status = existing_like_data.loc[(existing_like_data["Username"] == st.session_state["original_username"]) & (existing_like_data["Message ID"] == message_ID)].shape[0] > 0

        # Add the value to the session state
        st.session_state[f"like_status{message_ID}"] = like_status

    with tab1:
        # List of likes from the user
        current_user_likes = existing_like_data.query(f"Username == '{st.session_state['original_username']}'")
        current_user_likes_list = current_user_likes["Message ID"].tolist()

        # Search for Followed Users
        current_followed_users = existing_follow_data.query(f"`Follower ID` == '{st.session_state['original_username']}' and `Follow Status` == 'Accepted'")
        current_followed_users_list = current_followed_users["Followed User"].tolist()

        # Search for public Users
        public_users = existing_user_data.loc[existing_user_data['Profile Public'] == True]
        public_users_list = public_users["Username"].tolist()  # Convert Series to list

        # Combine public and followed users, removing duplicates
        all_users_list = list(set(public_users_list + current_followed_users_list + [st.session_state['original_username']]))

        # Search for messages from the combined list of users
        all_messages = existing_message_data.loc[existing_message_data['Username'].isin(all_users_list)]


        # Show the messages in the Feed
        usernames = all_messages['Username']
        messages = all_messages['Message']
        like_counts = all_messages['Like Count']
        message_IDs = all_messages['Message ID']
        for username, message, like_count, message_ID in zip(usernames, messages, like_counts, message_IDs):
            div = show_message(username, message, like_count)

            #Show Like and Follow buttons
            col1, col2 = st.columns([10, 1.5])

            with col2:
                # Retrieve like status from session state
                like_status = st.session_state.get(f"like_status{message_ID}", False)

                # Create the toggle widget
                like_state = st.toggle('Like', key=f'Tab1_Like{message_ID}', value=like_status, on_change=change_like_status,
                                       args=[message_ID])

    with tab2:
        # Search for my Favorite Messages
        favorite_messages = existing_message_data.loc[existing_message_data['Message ID'].isin(current_user_likes_list)]

        if favorite_messages.empty is False:
            # Show the messages in the Feed
            usernames = favorite_messages['Username']
            messages = favorite_messages['Message']
            like_counts = favorite_messages['Like Count']
            message_IDs = favorite_messages['Message ID']
            for username, message, like_count, message_ID in zip(usernames, messages, like_counts, message_IDs):
                div = show_message(username, message, like_count)

                # Show Like buttons
                col1, col2 = st.columns([10, 1.5])

                with col2:
                    # Retrieve like status from session state
                    like_status = st.session_state.get(f"like_status{message_ID}", False)

                    # Create the toggle widget
                    like_state = st.toggle('Like', key=f'Tab2_Like{message_ID}', value=like_status, on_change=change_like_status,
                                           args=[message_ID])
        else:
            st.write("You have not liked any messages yet")

    with tab3:

        with st.form("Search Messages"):
            text_search = st.text_input("Search for text in the Message").lower()
            user_search = st.selectbox("Search by User", options=all_users_list, index=None)
            search = st.form_submit_button("Search")

        filtered_messages = all_messages.copy()

        if user_search and text_search:
            filtered_messages = filtered_messages.query("Username == @user_search & Message.str.contains(@text_search, case=False)")

        elif user_search and not text_search:
            filtered_messages = filtered_messages.query("Username == @user_search")

        elif not user_search and text_search:
            filtered_messages = filtered_messages.query("Message.str.contains(@text_search, case=False)")

        for index, row in filtered_messages.iterrows():
            show_message(row['Username'], row['Message'], row['Like Count'])

            # Show Like buttons
            col1, col2 = st.columns([10, 1.5])

            with col2:
                # Retrieve like status from session state
                like_status = st.session_state.get(f'like_status{row["Message ID"]}', False)

                # Create the toggle widget
                like_state = st.toggle('Like', key=f'Tab3_Like{row["Message ID"]}', value=like_status,
                                       on_change=change_like_status,
                                       args=[row["Message ID"]])

else:
    # hide_pages(["Feed", "My Messages", "Follow Requests", "My Profile"])
    # st.switch_page("main.py")
    st.write('Please login')