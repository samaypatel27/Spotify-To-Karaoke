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
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

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

SPOTIFY_TOKEN_INFO = "spotify_token_info"
YOUTUBE_TOKEN_INFO = "youtube_token_info"

SCOPES=[
            'https://www.googleapis.com/auth/youtube.force-ssl',
            'https://www.googleapis.com/auth/youtube'
        ]

# CHANGE THESE 5 Variables (should all be under PORT 3000 since they are frontend redirects)

# Redirect after OAuth
SPOTIFY_COMPLETE_REDIRECT = 'http://localhost:3000/user/dashboard'
YOUTUBE_COMPLETE_REDIRECT = 'http://localhost:3000/user/dashboard'

# Redirect if there is no session present (user is not logged in to one) will be trigger upon call of a route
YOUTUBE_ERROR_REDIRECT = 'http://localhost:3000/user/dashboard'
SPOTIFY_ERROR_REDIRECT = 'http://localhost:3000/'

# redirect after logout of both spotify and youtube
LOGOUT_REDIRECT = 'http://localhost:3000/'


@app.route('/spotify/login')
def autoLogin():
    sp_oauth = create_spotify_oauth()
    # this line above is what we use to call Spotify's API (client info is listed as a function down below)
    auth_url = sp_oauth.get_authorize_url()
    # redirects to spotifys custom url. when its done, it redirects to /redirect automatically
    return redirect(auth_url)

# creating a session is flask doesn't mean its stored serverside - it creates a cookie on the browser
# so we do 'WITHcredentials include', allowing the front end to send the cookie (basicalyl the session) to the backend. so now we know the token to clear
@app.route('/auth/logout')
def logout():
    session.clear()
    return redirect(LOGOUT_REDIRECT)

# in the developer settings, I set the redirect URI to /spotify/redirect, so it will redirect to here after
@app.route('/spotify/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    # we passed the auth_url as an argument, or query parameter in express, above, so we are getting the redirect code
    spotify_token_info = sp_oauth.get_access_token(code)
    # the redirect code here is exchanged for an authorization code
    session[SPOTIFY_TOKEN_INFO] = spotify_token_info
    # CREATES THE SESSION, stores authorization token
    return redirect(SPOTIFY_COMPLETE_REDIRECT)
    # calls the getPlaylist function after redirect is complete

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



# route for getting user data from Spotify API
@app.route('/spotify/user', methods = {'GET'})
def getUser():
    try:
        spotify_token_info = get_spotify_token_info_object()
    except:
        print('You are not logged in. Redirecting...')
        return redirect(SPOTIFY_ERROR_REDIRECT)
        # external is false because the spotify login is under the localhost:port url
    sp = spotipy.Spotify(auth=spotify_token_info['access_token'])
    JSONObjects = sp.current_user()
    userName = JSONObjects['display_name']
    user_image = JSONObjects['images'][0]['url']
    user_info = {
        'userName': userName,
        'image' : user_image
    }
    user = []
    user.append(user_info)
    return user

# route for syncing data from Spotify API --> SQLite database
@app.route('/spotify/sync', methods = {'POST'})
def syncData():
    try:
        spotify_token_info = get_spotify_token_info_object()
    except:
        print('You are not logged in. Redirecting...')
        return redirect(SPOTIFY_ERROR_REDIRECT)
        # external is false because the spotify login is under the localhost:port url
    
    sp = spotipy.Spotify(auth=spotify_token_info['access_token'])

    userInfo = sp.current_user()
    userName = userInfo['display_name']

    JSONObjects = sp.current_user_playlists(limit=50, offset=0)
    # strat: return this jsonify dict at the end of this route
    playlists = []

    items = JSONObjects['items']
    for playlist in items:
        # if the playlist doesn't belong to the user, we will not add it
        playlistOwner = playlist['owner']['display_name']
        if playlistOwner != userName:
            continue
        name = playlist['name']
        url = playlist['external_urls']['spotify']

        # make try catch (get the code from the spotify link because that link is the playlist id we will use in api calls)
        regex = re.search(r"https:\/\/open\.spotify\.com\/playlist\/([a-zA-Z0-9]+)", url)
        id = regex.group(1)

        if playlist['images']:
            playlist_image = playlist['images'][0]['url']
        else:
            playlist_image = None
        # create a dictionary
        playlist_info = {
                "name" : name,
                "id": id,
                "image": playlist_image 
        }
        # for debugging, if we want to just get the playlists, we return the playlists list
        playlists.append(playlist_info)

    connection = sqlite3.connect(currentDir + '\spotify.db')
    cursor = connection.cursor()

    createPlaylistTable = """
    DROP TABLE IF EXISTS playlists;

    CREATE TABLE playlists (
        playlist_id TEXT PRIMARY_KEY,
        playlist_name TEXT NOT NULL,
        playlist_image TEXT
    );
    """

    createVirtualPlaylistTable = """
    DROP TABLE IF EXISTS playlistsVirtual;

    CREATE VIRTUAL TABLE playlistsVirtual
    USING fts5 (playlist_id, playlist_name, playlist_image)
    """

    createSongsTable = """
    DROP TABLE IF EXISTS songs;

    CREATE TABLE songs (
        song_id INTEGER PRIMARY KEY,
        song_name TEXT NOT NULL,
        song_artists TEXT NOT NULL,
        song_album TEXT NOT NULL,
        song_image TEXT NOT NULL,
        playlist_id TEXT NOT NULl,
        FOREIGN KEY (playlist_id)
            REFERENCES playlists (playlist_id)
    );
    """

    createVirtualSongsTable = """
    DROP TABLE IF EXISTS songsVirtual;

    CREATE VIRTUAL TABLE songsVirtual
    USING fts5 (song_id, song_name, song_artists, song_album, song_image, playlist_id)

    """

    cursor.executescript(createPlaylistTable)
    cursor.executescript(createVirtualPlaylistTable)
    cursor.executescript(createSongsTable)
    cursor.executescript(createVirtualSongsTable)

    insertPlaylist = "INSERT INTO playlists VALUES (?, ?, ?)"
    insertSong = "INSERT INTO songs (song_name, song_artists, song_album, song_image, playlist_id) VALUES (?, ?, ?, ?, ?)"

    for playlist_info in playlists:
        # adds playlist to database
        cursor.execute(insertPlaylist, (playlist_info['id'], playlist_info['name'], playlist_info['image']))
        response = sp.playlist_items(playlist_info['id'])
        songs = response['items']
        for item in songs:
            track = item['track']
            if not track:
                continue
            artists = ""
            for artist in track['artists']:
                artists += " "  + artist['name']
            song = track.get('name', 'Unknown Track')
            albumInfo = track['album']
            album = albumInfo.get('name', 'Unknown Album')
            if track['album']['images']:
                image_url = track['album']['images'][0]['url']
            else:
                image_url = 'None'
            # adds song to song database
            cursor.execute(insertSong, (song, artists, album, image_url, playlist_info['id']))


    # now copy the table, once the playlist table has values in it
    copyPlaylistTable = """
    INSERT INTO playlistsVirtual (playlist_id, playlist_name, playlist_image)
    SELECT playlist_id, playlist_name, playlist_image FROM playlists
    """
    copySongTable = """
    INSERT INTO songsVirtual (song_id, song_name, song_artists, song_album, song_image, playlist_id)
    SELECT song_id, song_name, song_artists, song_album, song_image, playlist_id FROM songs
    """
    cursor.executescript(copyPlaylistTable)
    cursor.executescript(copySongTable)
    connection.commit()
    connection.close()
    
    return playlists

# retrieve playlists from database
@app.route("/db/playlists", methods = {'GET'})
def getPlaylists():
    connection = sqlite3.connect(currentDir + '\spotify.db')
    cursor = connection.cursor()

    if len(request.args.get('search')) < 1:
        selectPlaylists = f"""
        SELECT playlist_name, playlist_id, playlist_image
        FROM playlists
        """
    else:
        query = request.args.get('search') + '*'
        selectPlaylists = f"""
        SELECT playlist_name, playlist_id, playlist_image
        FROM playlistsVirtual
        WHERE playlist_name MATCH "{query}"
        """
    
    cursor.execute(selectPlaylists)
    playlists = cursor.fetchall()
    

    arrayOfPlaylists = []
    for item in playlists:
        playlist = {
            'id': item[1],
            'name': item[0],
            'image': item[2]
        }
        arrayOfPlaylists.append(playlist)

    connection.commit()
    connection.close()


    return arrayOfPlaylists

# retrieve songs from playlist
@app.route('/db/songs/<playlist_id>', methods = {'GET'})
def getSongs(playlist_id):
    connection = sqlite3.connect(currentDir + '\spotify.db')
    cursor = connection.cursor()

    if request.args.get('search') is None or len(request.args.get('search')) < 1:
        print("There is no arguments")
        selectSongsFromPlaylist = """
        SELECT song_id, song_name, song_artists, song_album, song_image
        FROM songs
        WHERE playlist_id = ?
        """
    else:
        print("There is arguments")
        query = request.args.get('search') + '*'
        selectSongsFromPlaylist = f"""
        SELECT song_id, song_name, song_artists, song_album, song_image
        FROM songsVirtual
        WHERE (playlist_id = ? AND song_name MATCH "{query}")
        """

    
    cursor.execute(selectSongsFromPlaylist, (playlist_id,))
    songs = cursor.fetchall()

    arrayOfSongs = []
    for item in songs:
        song = {
            'song_id' : item[0],
            'song_name' : item[1],
            'song_artists' : item[2],
            'song_album' : item[3],
            'song_image' : item[4]
        }
        arrayOfSongs.append(song)

    connection.commit()
    connection.close()
    return arrayOfSongs

# Example session
# {
#     "token_info": {
#         "access_token": "BQC6FXG...",
#         "expires_at": 1642678800,
#         "refresh_token": "AQD-yK8s..."
#     }
# }
# check if there is token data. if the token has expired, it automatically refreshes it
def get_spotify_token_info_object():
    spotify_token_info = session.get(SPOTIFY_TOKEN_INFO, None)
    # you can pass another parameter like that. If token_info doesn't exist, then session.get will just return "none"
    # this means that the user is not loggged in
    if not spotify_token_info:
        raise "There is no Spotify session present"
        
    now = int(time.time())
    is_expired = spotify_token_info['expires_at'] - now < 60
    # checks if session token has already been expired
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        spotify_token_info = sp_oauth.refresh_access_token()
    return spotify_token_info

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
        
   
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id="3828561373c5404eac1883037d3091e2",
        client_secret="16268d1b046e4f379d1bcaa1694f6827",
        # retrieved from dashboard
        redirect_uri=url_for('redirectPage', _external=True),
        # calls the redirectPage route
        scope="playlist-modify-public ugc-image-upload",
        cache_path = None
        # playlist-read-private playlist-modify-private user-read-private
    )

if (__name__) == "__main__":
    app.run(debug=True)