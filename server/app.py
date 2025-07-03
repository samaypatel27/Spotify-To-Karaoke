from flask import Flask, request, url_for, session, redirect, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import re
import json
from flask_cors import CORS
import sqlite3
import os

# IDEA: Light/dark mode for useCOntext API
# only use redux Query

currentDir = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__)
# supporting credentials allow cookies to be included
CORS(app, supports_credentials=True, origins = ['http://localhost:3000'])

app.secret_key = "dsjifj904jfe"
# key to sign the session cookie

app.config['SESSION_COOKIE_NAME'] = 'Samays Cookie'

TOKEN_INFO = "token_info"

# this is the first route executed as it is the default route when you run the local host
@app.route('/testing')
def test():
    try:
        token_info = get_token()
    except:
        print('You are not logged in. Redirecting...')
        return redirect(url_for('autoLogin', _external=False))
        # external is false because the spotify login is under the localhost:port url
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    JSONObjects = sp.current_user_playlists(limit=50, offset=0)

    user_info = sp.current_user()

    return json.dumps(user_info)

@app.route('/auth/login')
def autoLogin():
    sp_oauth = create_spotify_oauth()
    # this line above is what we use to call Spotify's API (client info is listed as a function down below)
    auth_url = sp_oauth.get_authorize_url()
    # redirects to spotifys custom url. when its done, it redirects to /redirect automatically
    return redirect(auth_url)

@app.route('/redirect')
def redirectPage():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    # we passed the auth_url as an argument, or query parameter in express, above, so we are getting the redirect code
    token_info = sp_oauth.get_access_token(code)
    # the redirect code here is exchanged for an authorization code
    session[TOKEN_INFO] = token_info
    # CREATES THE SESSION, stores authorization token
    return redirect('http://localhost:3000/user/dashboard')
    # calls the getPlaylist function after redirect is complete
    # url_for('getPlaylist') returns /getMusic
    # _extrnal=true attaches the new url (/getMusic) to localhost:Whatever port

@app.route('/spotify/user', methods = {'GET'})
def getUser():
    try:
        token_info = get_token()
    except:
        print('You are not logged in. Redirecting...')
        return redirect(url_for('autoLogin', _external=False))
        # external is false because the spotify login is under the localhost:port url
    sp = spotipy.Spotify(auth=token_info['access_token'])
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

@app.route('/spotify/sync', methods = {'POST'})
def syncData():
    try:
        token_info = get_token()
    except:
        print('You are not logged in. Redirecting...')
        return redirect(url_for('autoLogin', _external=False))
        # external is false because the spotify login is under the localhost:port url
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

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

    cursor.executescript(createPlaylistTable)
    cursor.executescript(createVirtualPlaylistTable)
    cursor.executescript(createSongsTable)

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
    cursor.executescript(copyPlaylistTable)
    connection.commit()
    connection.close()
    
    return playlists

@app.route("/db/playlists", methods = {'GET'})
def getPlaylists():
    query = request.args.get('search') + '*'
    connection = sqlite3.connect(currentDir + '\spotify.db')
    cursor = connection.cursor()

    selectPlaylists = f"""
    SELECT playlist_name, playlist_id, playlist_image
    FROM playlistsVirtual
    WHERE playlistsVirtual MATCH "{query}"
    """

    cursor.execute(selectPlaylists)
    playlists = cursor.fetchall()
    
    print(playlists)

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

    print(arrayOfPlaylists)

    return arrayOfPlaylists


@app.route('/db/songs/<playlist_id>', methods = {'GET'})
def getSongs(playlist_id):
    connection = sqlite3.connect(currentDir + '\spotify.db')
    cursor = connection.cursor()

    selectSongsFromPlaylist = """
    SELECT song_id, song_name, song_artists, song_album, song_image
    FROM songs
    WHERE playlist_id = ?
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


    
# creating a playlist: name,description, public/collaborative option, and option to upload image or use default

@app.route('/other')
def something():
    
    print('Here are your Spotify Playlists:')
    playlist_names = dict.keys()
    # enumerate function to automatically increment an index
    # use enumerate to generate object for next route where you pass in playlist and recieive song
    # NEXT STEP: Create the front end, attaching login, then end method above after for loop by returning json to see and fetch data
    for index, value in enumerate(playlist_names, start=1):
        print('[', index, '] ', value)
    match = re.search(r"https:\/\/open\.spotify\.com\/playlist\/([a-zA-Z0-9]+)", dict.get('car chill'))
    id = match.group(1)

    token_info = get_token()
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # gets songs in playlist
    results = sp.playlist_tracks(id)
    return results['items']
    

    # number = input('Enter the playlist number you would like to convert into insturmentals:')
    # query = "let me go insturmental"
    # result = sp.search(q=query, type="track", limit=10)
    # return result

    playlistLink_arr = []

    

# check if there is token data. if there is not token data, we will redirect the users back to the login page
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    # you can pass another parameter like that. If token_info doesn't exist, then session.get will just return "none"
    # this means that the user is not loggged in
    if not token_info:
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    # checks if session has exceeded 60 seconds (guess)
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token()
        # creates a new token after refreshed
    return token_info

    
   
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id="3828561373c5404eac1883037d3091e2",
        client_secret="16268d1b046e4f379d1bcaa1694f6827",
        # retrieved from dashboard
        redirect_uri=url_for('redirectPage', _external=True),
        # calls the redirectPage route
        scope="playlist-read-private playlist-modify-private playlist-modify-public user-read-private ugc-image-upload"
    )

if (__name__) == "__main__":
    app.run(debug=True)