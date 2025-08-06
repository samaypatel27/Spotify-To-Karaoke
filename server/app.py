# BACKEND FILE: Routes for Spotify OAuth Login, Syncing and retrieving data from Spotify API & SQLite database
from flask import Flask, make_response, request, url_for, session, redirect, jsonify
import spotipy
import requests
from spotipy.oauth2 import SpotifyOAuth
import time
import re
import json
from flask_cors import CORS
import sqlite3
import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from extensions import db
from models import User, Playlist, Song
from spotify import spotifyDB

currentDir = os.path.dirname(os.path.abspath(__file__))

# Google OAuth 2.0 isn't allowed in backend because it isn't secure, it says you need https BUT this specific environment variable fixes the issue
# found on stack overflow
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


app = Flask(__name__)
# supporting credentials allow cookies to be included
CORS(app, supports_credentials=True, origins = ['http://localhost:3000'])

app.secret_key = "dsjifj904jfe"
# key to sign the session cookie

app.config['SESSION_COOKIE_NAME'] = 'Samays Cookie'


YOUTUBE_TOKEN_INFO = "youtube_token_info"

SCOPES=[
            'https://www.googleapis.com/auth/youtube.force-ssl',
            'https://www.googleapis.com/auth/youtube'
        ]

# CHANGE THESE 5 Variables (should all be under PORT 3000 since they are frontend redirects)

# Redirect after OAuth

YOUTUBE_COMPLETE_REDIRECT = 'http://localhost:3000/user/dashboard'

# Redirect if there is no session present (user is not logged in to one) will be trigger upon call of a route
YOUTUBE_ERROR_REDIRECT = 'http://localhost:3000/user/dashboard'
# redirect after logout of both spotify and youtube
LOGOUT_REDIRECT = 'http://localhost:3000/'

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
# routes
# Initialize extensions
db.init_app(app)
app.register_blueprint(spotifyDB)

# creating a session is flask doesn't mean its stored serverside - it creates a cookie on the browser
# so we do 'WITHcredentials include', allowing the front end to send the cookie (basicalyl the session) to the backend. so now we know the token to clear
@app.route('/auth/logout')
def logout():
    session.clear()
    return redirect(LOGOUT_REDIRECT)

@app.route('/youtube/login')
def youtubeLogin():
    # Required, call the from_client_secrets_file method to retrieve the client ID from a
    # client_secret.json file. The client ID (from that file) and access scopes are required. (You can
    # also use the from_client_config method, which passes the client configuration as it originally
    # appeared in a client secrets file but doesn't access the file itself.)
    flow = Flow.from_client_secrets_file('client_secret.json',
    SCOPES)

    # Required, indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required. The value must exactly
    # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
    # configured in the API Console. If this value doesn't match an authorized URI,
    # you will get a 'redirect_uri_mismatch' error.
    # Access redirect URIs from the client config
    redirect_uri = flow.client_config['redirect_uris'][0]
    print(redirect_uri)
    flow.redirect_uri = redirect_uri

    # Generate URL for request to Google's OAuth 2.0 server.
    # Use kwargs to set optional request parameters.
    authorization_url, state = flow.authorization_url(
        # Recommended, enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Optional, enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true',
        # Optional, if your application knows which user is trying to authenticate, it can use this
        # parameter to provide a hint to the Google Authentication Server.
        login_hint='hint@example.com',
        # Optional, set prompt to 'consent' will prompt the user for consent
        prompt='consent')
    session['state'] = state
    return redirect(authorization_url)

@app.route("/youtube/redirect")
def redirectYoutube():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        SCOPES,
        state=state)
    # Access redirect URIs from the client config
    redirect_uri = flow.client_config['redirect_uris'][0]
    flow.redirect_uri = redirect_uri

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store the credentials in the session.
    # ACTION ITEM for developers:
    #     Store user's access and refresh tokens in your data store if
    #     incorporating this code into your real app.
    credentials = flow.credentials
    session[YOUTUBE_TOKEN_INFO] = {
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'granted_scopes': credentials.granted_scopes}
    return redirect(YOUTUBE_COMPLETE_REDIRECT)

# GET: Get all youtube playlists from the account
# POST: make playlist, search based on queries, and then add the 1st found query to that playlist
@app.route("/youtube/playlists", methods = {'GET', 'POST'})
def youtubePlaylists():
    try:
        youtube_token_info = get_youtube_token_info_object()
    except Exception as e:
        print("Not logged in to youtube")
        return redirect(YOUTUBE_ERROR_REDIRECT)
    access_token = youtube_token_info['access_token']
    # YouTube API endpoint for user's playlists
    url = "https://www.googleapis.com/youtube/v3/playlists"

    if request.method == 'GET':

        # array we will use to return all playlist object information
        all_playlists = []

        # youtube api only returns 50 playlists at a time because it doesn't want to dump large amount of data,
        # so we have to account for this, as it provides up a token to access another page for its api responses
        next_page_token = None
        
        while True:
            # Parameters for the API request
            params = {
                'part': 'snippet,contentDetails,status',
                'mine': 'true',  # Get playlists owned by authenticated user
                'maxResults': 50,  # Maximum allowed per request
                'access_token': access_token
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            # Make the API request
            response = requests.get(url, params=params)
            
            if response.status_code == 401:
                return {"error": "Unauthorized - token may be expired"}
            elif response.status_code != 200:
                return {"error": f"API request failed with status {response.status_code}"}
            
            data = response.json()
            
            # Process each playlist
            for playlist in data.get('items', []):

                snippet = playlist.get('snippet', {})
                
                # Get highest quality thumbnail available
                thumbnails = snippet.get('thumbnails', {})
                highest_thumbnail = None
                
                # Check for thumbnails in order of quality (highest to lowest)
                for quality in ['maxres', 'standard', 'high', 'medium', 'default']:
                    if quality in thumbnails and thumbnails[quality].get('url'):
                        highest_thumbnail = thumbnails[quality]['url']
                        break
                
                playlist_info = {
                    'id': playlist.get('id'),
                    'title': snippet.get('title'),
                    'description': snippet.get('description'),
                    'thumbnail': highest_thumbnail
                }
                
                all_playlists.append(playlist_info)
            
            # Check if there are more pages
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
        
        return all_playlists

    elif request.method == 'POST':
        # Get query parameters
        title = request.args.get('title')
        description = request.args.get('description')
        is_public = request.args.get('public', 'false').lower() == 'true'
        
        # get the body passed (song queries list)
        data = request.get_json()
        song_queries = data.get('songs', [])

        # Create new YouTube playlist
        playlist_id = create_youtube_playlist(title, description, is_public, access_token)
        
        # Store search results for each song (we'll use this later)
        all_search_results = []
        
        # Loop through each song query
        for song_query in song_queries:
            # Search YouTube for karaoke version
            search_results = search_youtube_videos(song_query, access_token)
            
            # Store the first 5 results for later use
            all_search_results.append(search_results[:5])
            
            # Add the first result (0th index) to the playlist
            if search_results:
                first_video_id = search_results[0]['id']
                add_video_to_playlist(playlist_id, first_video_id, access_token)

        # Create the YouTube playlist link
        playlist_link = f"https://www.youtube.com/playlist?list={playlist_id}"
        return make_response(playlist_link, 200)
        


def create_youtube_playlist(title, description, is_public, access_token):
    """Create a new YouTube playlist and return its ID"""
    url = "https://www.googleapis.com/youtube/v3/playlists"
    
    # Set privacy status
    privacy_status = "public" if is_public else "private"
    
    payload = {
        "snippet": {
            "title": title,
            "description": description
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }
    
    params = {
        'part': 'snippet,status',
        'access_token': access_token
    }
    
    response = requests.post(url, json=payload, params=params)
    data = response.json()
    
    # Return the new playlist ID
    return data['id']


def search_youtube_videos(query, access_token):
    """Search YouTube and return first 5 video results"""
    url = "https://www.googleapis.com/youtube/v3/search"
    
    params = {
        'part': 'snippet',
        'q': query + ' - karaoke',  # This will be "song title + artist + -karaoke"
        'type': 'video',
        'maxResults': 5,
        'access_token': access_token
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Extract video info we need
    search_results = []
    for item in data.get('items', []):
        video_info = {
            'id': item['id']['videoId'],
            'title': item['snippet']['title']
        }
        search_results.append(video_info)
    
    return search_results


def add_video_to_playlist(playlist_id, video_id, access_token):
    """Add a video to the specified playlist"""
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    
    payload = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }
    
    params = {
        'part': 'snippet',
        'access_token': access_token
    }
    
    response = requests.post(url, json=payload, params=params)
    return response.json()


def get_youtube_token_info_object():
    youtube_token_info = session.get(YOUTUBE_TOKEN_INFO, None)

    if not youtube_token_info:
        raise "There is no YouTube/Google Session present"

    # Create credentials object from stored token info
    credentials = Credentials(
        token=youtube_token_info['access_token'],
        refresh_token=youtube_token_info['refresh_token'],
        token_uri=youtube_token_info['token_uri'],
        client_id=youtube_token_info['client_id'],
        client_secret=youtube_token_info['client_secret']
    )
    
    if credentials.expired:
        # Refresh the token
        credentials.refresh(Request())
        
        # Update session with new token info
        session['YOUTUBE_TOKEN_INFO'].update({
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token
        })
        
        print("Token refreshed successfully")
        return youtube_token_info
     
    return youtube_token_info
        

# Create tables
with app.app_context():
    db.create_all()
if (__name__) == "__main__":
    app.run(debug=True)
    