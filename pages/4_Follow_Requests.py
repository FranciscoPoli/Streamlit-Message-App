import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from main import load_css
from st_pages import hide_pages



def create_follow_request(user_to_follow):
    # Retrieve existing follow data
    existing_follow_data = st.session_state["existing_follow_data"]

    # Create new follow request data
    new_follow_request = pd.DataFrame(
        [
            {
                "Follower ID": st.session_state["username"],
                "Followed User": user_to_follow,
                "Follow Status": "Pending",
            }
        ]
    )

    # Append new request to existing data
    existing_follow_data = pd.concat([existing_follow_data, new_follow_request], ignore_index=True)
    # Update session state with latest data
    st.session_state["existing_follow_data"] = existing_follow_data
    # Update Google Sheets with modified data
    conn.update(worksheet="Follows", data=existing_follow_data)

    st.success(f"Request sent to {user_to_follow}")



load_css()
conn = st.connection("gsheets", type=GSheetsConnection)

authentication_status = st.session_state.get("authentication_status", False)
if authentication_status:
    st.session_state["authenticator"].logout(location="sidebar")

    st.write(f'Username: :blue[{st.session_state["username"]}]')

    tab1, tab2, tab3 = st.tabs(["Follow Requests", "Users you Follow", "Search for User"])

    # Fetch data if not already in session state
    if "existing_user_data" not in st.session_state:
        st.session_state["existing_user_data"] = conn.read(worksheet="Users", usecols=list(range(3)), ttl=35).dropna(how="all")
    if "existing_follow_data" not in st.session_state:
        st.session_state["existing_follow_data"] = conn.read(worksheet="Follows", usecols=list(range(3)), ttl=35).dropna(how="all")

    existing_user_data = st.session_state["existing_user_data"]
    existing_follow_data = st.session_state["existing_follow_data"]

    with tab1:
        # List of pending follow requests for the user
        current_user_follows = existing_follow_data.query(f"`Followed User` == '{st.session_state['username']}' and `Follow Status` == 'Pending'")

        if current_user_follows.empty is False:
            st.markdown("You have requests of people to follow you!")
            # follower_IDs = current_user_follows['Follower ID']
            # for follower_ID in follower_IDs:

            i = 0
            columns = st.columns(2)

            for index, row in current_user_follows.iterrows():
                follower_ID = row['Follower ID']

                with columns[i % 2]:
                    div = f"""
                                <div class="user-line">
                                    <p><span style="color: white;">User: </span><strong>{follower_ID}</strong></p>
                                </div>
                                <div class="chat-bubble">
                                    <p>Wants to follow you!</p>
                                </div>
                            """
                    st.markdown(div, unsafe_allow_html=True)
                    _, col1, col2 = st.columns([6,2,2])
                    with col1:
                        accept = st.button("ACCEPT", key=f"accept_{follower_ID}_{index}")

                    with col2:
                        decline = st.button("DECLINE", key=f"decline_{follower_ID}_{index}", type="primary")

                    # Conditional updating inside accept/decline blocks
                    if accept:
                        row.loc["Follow Status"] = "Accepted"
                        st.success("Request Accepted")
                    elif decline:
                        row.loc["Follow Status"] = "Declined"
                        st.error("Request Declined")

                i += 1

            # Update session state and Google Sheets after processing all requests
            st.session_state["existing_follow_data"].update(current_user_follows)
            conn.update(worksheet="Follows", data=st.session_state["existing_follow_data"])

        else:
            st.write("You have no pending requests to follow you")

    with tab2:
        # List of users that you follow
        current_users_followed = existing_follow_data.query(f"`Follower ID` == '{st.session_state['username']}' and `Follow Status` == 'Accepted'")

        if current_users_followed.empty is False:

            # Show User list
            i = 0
            columns = st.columns(2)
            for index, row in current_users_followed.iterrows():
                followed_user = row['Followed User']

                with columns[i % 2]:  # Alternate the messages between 2 columns
                    div = f"""
                                <div class="user-line">
                                    <p><span style="color: white;">User: </span><strong>{followed_user}</strong></p>
                                </div>
                                <div class="chat-bubble">
                                    <p>You are following</p>
                                </div>
                            """
                    st.markdown(div, unsafe_allow_html=True)

                    # Show Unfollow buttons
                    innercol1, innercol2 = st.columns([8, 2])


                    with innercol2:
                        unfollow = st.button("Unfollow", key=f"Unfollow_{followed_user}_{index}", type="primary")
                        if unfollow:
                            # Update "Follow Status" to "Declined" in both session state and Google Sheets
                            st.session_state["existing_follow_data"].loc[index, "Follow Status"] = "Declined"
                            conn.update(worksheet="Follows", data=st.session_state["existing_follow_data"])
                            st.success(f"You are no longer following {followed_user}")
                            # Refresh the page to reflect the change immediately
                            st.experimental_rerun()
                i +=1
        else:
            st.write("You are not following anybody")


    with tab3:
        # with st.form("Search Messages"):
        user_list = existing_user_data["Username"].tolist()
        user_search = st.multiselect("Search User", options=user_list)
            # search = st.form_submit_button("Search")

        st.markdown("---")
        filtered_users = existing_user_data.copy()

        if user_search:
            filtered_users = filtered_users.loc[filtered_users['Username'].isin(user_search)]

        # Show User list
        i = 0
        columns = st.columns(2)
        for index, row in filtered_users.iterrows():
            username = row['Username']
            profile = "Profile Public" if row['Profile Public'] == True else "Profile Private"

            with columns[i % 2]: #Alternate the messages between 2 columns
                div = f"""
                    <div class="user-line">
                        <p><span style="color: white;">User: </span><strong>{username}</strong></p>
                    </div>
                    <div class="chat-bubble">
                        <p>{profile}</p>
                    </div>
                """
                st.markdown(div, unsafe_allow_html=True)

                # Show Follow buttons
                innercol1, innercol2 = st.columns([7, 3])

                # Show Follow buttons, disabling for own user, followed users, and pending requests
                button_state = (username == st.session_state["username"]
                        or st.session_state["existing_follow_data"].query(f"`Follower ID` == '{st.session_state['username']}' "
                                                                          f"and (`Followed User` == '{username}' "
                                                                          f"and `Follow Status` in ['Pending', 'Accepted'])").shape[0] > 0
                                                                        )
                with innercol2:
                    follow_request = st.button("Request Follow", key=f"Follow_{username}", disabled=button_state,
                                               on_click=create_follow_request, args=[username])

            i += 1

else:
    # hide_pages(["Feed", "My Messages", "Follow Requests", "My Profile"])
    # st.switch_page("main.py")
    st.write('Please login')