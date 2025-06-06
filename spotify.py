import streamlit as st
import spotipy as sp
from spotipy.oauth2 import SpotifyOAuth
import os

CLIENT_ID = st.secrets.spotify["CLIENT_ID"]
CLIENT_SECRET = st.secrets.spotify["CLIENT_SECRET"]
REDIRECT_URI = st.secrets.spotify["REDIRECT_URI"]
CACHE_PATH = ".spotipy_cache"

#scopes
# 'user-read-recently-played': To read the user's recently played tracks
# 'user-top-read': top artists and tracks
# 'user-read-private': basic profile info
SCOPES = "user-read-recently-played user-top-read user-read-private" 

st.set_page_config(
        page_title="Spotify",
        layout="centered")

st.header("Spotify")

def get_spotify_oauth():
    """Initializes and returns a SpotifyOAuth object."""
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        cache_path=CACHE_PATH,
        show_dialog=True
    )

def get_spotify_client():
    """Returns an authenticated Spotipy client, handling token refresh."""
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        query_params = st.query_params
        code = query_params.get("code")

        if code:
            token_info = sp_oauth.get_access_token(code)
            st.query_params.clear()
            st.rerun()
        else:
            st.session_state["logged_in"] = False
            return None
        
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        
    if token_info:
        st.session_state["logged_in"] = True
        return sp.Spotify(auth=token_info["access_token"])
    else:
        st.session_state["logged_in"] = False
        return None
    
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Attempt to get the Spotify client
sp = get_spotify_client()

if not st.session_state["logged_in"] or sp is None:
    # Not logged in, show login button
    st.info("Please log in to Spotify to access your data.")
    auth_url = get_spotify_oauth().get_authorize_url()
    st.link_button("Login with Spotify", url=auth_url)
    st.stop() # Stop execution here until logged in
else:
    # Logged in, show user info and data options
    st.success("Successfully logged in to Spotify!")

    try:
        # Get user profile information
        user_profile = sp.current_user()
        if user_profile:
            st.header(f"Welcome, {user_profile['display_name']}!")
            if user_profile.get('images'):
                st.image(user_profile['images'][0]['url'], width=100)
        
    except sp.oauth2.SpotifyOauthError as e:
        st.error(f"Authentication error: {e}. Please try logging in again.")
        st.session_state["logged_in"] = False # Reset login state
        # You might want to delete the cache file here to force a fresh login
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH)
        st.link_button("Login with Spotify", url=get_spotify_oauth().get_authorize_url())
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        # Consider logging the full traceback in a real application
        # import traceback
        # st.error(traceback.format_exc())

    st.markdown("---")
    if st.button("Logout"):
        if os.path.exists(CACHE_PATH):
            os.remove(CACHE_PATH) # Delete the token cache
        st.session_state["logged_in"] = False
        st.experimental_rerun() # Rerun the app to show login button

artists = sp.current_user_top_artists()
songs = sp.current_user_top_tracks("long_term")

col1, col2 = st.columns((2))

col1.write(artists)
col2.write(songs)