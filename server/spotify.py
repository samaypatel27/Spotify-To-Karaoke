from flask import Blueprint, request, url_for, jsonify, session, redirect, make_response
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import re
import sqlite3
import os
from dotenv import load_dotenv
from extensions import db
from models import User, Playlist, Song

currentDir = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

spotifyDB = Blueprint('spotifyDB', __name__)

# Change this single variable. This is when the Spotify OAuth is complete, the user is logged in
SPOTIFY_COMPLETE_REDIRECT = 'http://localhost:3000/user/dashboard'

SPOTIFY_TOKEN_INFO = "spotify_token_info"


@spotifyDB.route('/spotify/login')
def autoLogin():
    sp_oauth = create_spotify_oauth()
    # this line above is what we use to call Spotify's API (client info is listed as a function down below)
    auth_url = sp_oauth.get_authorize_url()
    # redirects to spotifys custom url. when its done, it redirects to /redirect automatically
    return redirect(auth_url)


# in the developer settings, I set the redirect URI to /spotify/redirect, so it will redirect to here after
@spotifyDB.route('/spotify/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    # we passed the auth_url as an argument, or query parameter in express, above, so we are getting the redirect code
    spotify_token_info = sp_oauth.get_access_token(code)
    # the redirect code here is exchanged for an authorization code
    session[SPOTIFY_TOKEN_INFO] = spotify_token_info
    # CREATES THE SESSION, stores authorization token

    # Get the user_info and store as a complete seperate object (not provided by the sp_oauth)

    sp = spotipy.Spotify(auth=spotify_token_info['access_token'])
    user_info = sp.current_user()
    session['spotify_user_id'] = user_info['id']

    return redirect(SPOTIFY_COMPLETE_REDIRECT)
    # calls the getPlaylist function after redirect is complete

# route for syncing data from Spotify API --> PostegreSQL database, should be called ONLY when user logs in first time, or asks to refresh data
@spotifyDB.route('/spotify/sync', methods = {'POST'})
def syncData():
    try:
        spotify_token_info = get_spotify_token_info_object()
    except Exception as e:
        print('You are not logged in. Redirecting...')
        return make_response(str(e), 401)

    # to avoid errors if this route is called Twice (React Strict Mode feature) result of UseEffect()
    isSyncing = session.get('syncing', None)
    if isSyncing:
        return make_response("Already syncing", 200)

    session['syncing'] = True
    # Initialize Spotify API
    sp = spotipy.Spotify(auth=spotify_token_info['access_token'])

    # Get User Data from Spotify API
    userData = sp.current_user()
    userData_name = userData['display_name']
    userData_image = userData['images'][0]['url']

    try:  
        user = User.query.filter(User.id == session['spotify_user_id']).one()
        # if user exists, then we want to refresh the data. So we can delete all of the data
        # Deletes user, and all coressponding playlists and songs
        db.session.delete(user)
        db.session.flush()
    except Exception as e:
        print("User not in database")

    user = User(id = session['spotify_user_id'], name = userData_name, image = userData_image)
    db.session.add(user)
    db.session.flush()

    # Get Playlist Data from Spotify API
    user_playlists = sp.current_user_playlists(limit=50, offset=0)
    
    arr = []
    print(len(user_playlists['items']))

    for playlist in user_playlists['items']:
        # if the playlist doesn't belong to the user, we will not add it
        playlistOwner = playlist['owner']['display_name']
        if playlistOwner != userData_name:
            continue

        # Obtain playlist name
        playlistData_name = playlist['name']

        # Obtain playlist ID
        url = playlist['external_urls']['spotify']
        regex = re.search(r"https:\/\/open\.spotify\.com\/playlist\/([a-zA-Z0-9]+)", url)
        playlistData_id = regex.group(1)

        # obtain playlist image
        if playlist['images']:
            playlistData_image = playlist['images'][0]['url']
        else:
            playlistData_image = None
        # initialize playlist object and commit to database
        playlist = Playlist(id = playlistData_id, name = playlistData_name, image = playlistData_image, user_id = session['spotify_user_id'])
        db.session.add(playlist)
        db.session.flush()

        playlist_info = {
            "name": playlistData_name,
            "id": playlistData_id,
            "image": playlistData_image
        }
        arr.append(playlist_info)

        # Get Songs JSON from Spotify API, based on playlist ID
        user_songs = sp.playlist_items(playlistData_id)
        for el in user_songs['items']:
            track = el['track']
            if not track:
                continue
            songData_artists = ""
            for artist in track['artists']:
                songData_artists += " "  + artist['name']
            songData_name = track.get('name', 'Unknown Track')
            albumInfo = track['album']
            songData_album = albumInfo.get('name', 'Unknown Album')
            if track['album']['images']:
                songData_image = track['album']['images'][0]['url']
            else:
                songData_image = 'None'
            # adds song to song database
            song = Song(name = songData_name, artists = songData_artists, album = songData_album, image = songData_image, playlist_id = playlistData_id)
            db.session.add(song)
    db.session.commit()

    session.pop('syncing')
    return make_response("Spotify Data Successfully Synced to DB", 200)

@spotifyDB.route("/db/user", methods = {'GET'})
def getUser():
    user = db.session.query(User).filter(User.id == session['spotify_user_id']).one()
    obj = {
        "name": user.name,
        "image": user.image
    }
    return jsonify(obj)

# retrieve playlists from database
@spotifyDB.route("/db/playlists", methods = {'GET'})
def getPlaylists():
    user_id = session['spotify_user_id']
    # filter by user token, and optionally search query
    if request.args.get('search') is None or len(request.args.get('search')) < 1:
        playlists = db.session.query(Playlist.id, Playlist.name, Playlist.image).filter(Playlist.user_id == user_id).all()
    else:
        searchQuery = '%' + request.args.get('search') + '%'
        playlists = db.session.query(Playlist.id, Playlist.name, Playlist.image).filter(Playlist.user_id == user_id, Playlist.name.ilike(searchQuery)).all()
    
    arrayOfPlaylists = []
    for playlist in playlists:
        playlist = {
            'id': playlist.id,
            'name': playlist.name,
            'image': playlist.image
        }
        arrayOfPlaylists.append(playlist)
    return arrayOfPlaylists


# retrieve songs from playlist
@spotifyDB.route('/db/songs/<playlist_id>', methods = {'GET'})
def getSongs(playlist_id):
    # filter by playlist id, and optionally search query
    if request.args.get('search') is None or len(request.args.get('search')) < 1:
        songs = db.session.query(Song).filter(Song.playlist_id == playlist_id).all()
        
    else:
        searchQuery = '%' + request.args.get('search') + '%'
        songs = db.session.query(Song).filter(Song.playlist_id == playlist_id, Song.name.ilike(searchQuery)).all()

    arrayOfSongs = []
    for song in songs:
        song = {
            'id' : song.id,
            'name' : song.name,
            'artists' : song.artists,
            'album' : song.album,
            'image' : song.image
        }
        arrayOfSongs.append(song)

    return arrayOfSongs

# Example session (the user_id is not given when you log in so we add to the session seperately)
# {
#     "spotify_token_info": {
#         "access_token": "BQC6FXG...",
#         "expires_at": 1642678800,
#         "refresh_token": "AQD-yK8s..."
#     }
#     "user_id": "FDXDF42"
# }
# check if there is token data. if the token has expired, it automatically refreshes it
def get_spotify_token_info_object():
    spotify_token_info = session.get(SPOTIFY_TOKEN_INFO, None)
    # you can pass another parameter like that. If token_info doesn't exist, then session.get will just return "none"
    # this means that the user is not loggged in
    if not spotify_token_info:
        raise ValueError("Spotify Token does not exist. On frontend, redirect to homepage/logged out state")
        
    now = int(time.time())
    is_expired = spotify_token_info['expires_at'] - now < 60
    # checks if session token has already been expired
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        spotify_token_info = sp_oauth.refresh_access_token(spotify_token_info['refresh_token'])
    return spotify_token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id="3828561373c5404eac1883037d3091e2",
        client_secret="16268d1b046e4f379d1bcaa1694f6827",
        # retrieved from dashboard
        redirect_uri=url_for('spotifyDB.redirectPage', _external=True),
        # calls the redirectPage route
        scope="playlist-modify-public ugc-image-upload",
        cache_path = None
        # playlist-read-private playlist-modify-private user-read-private
    )



