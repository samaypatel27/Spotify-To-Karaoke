# About
Full-stack React-app, using Spotify & YouTube APIs/OAuth 2.0 to develop a platform to convert spotify playlists into karaoke equivalents on YouTube

# Stacks
OLD CLIENT:<br>
Front-End: React.js, CSS, Bootstrap <br>
Back-End: Python (Flask), SQLite

# Instructions
1. This project uses Flask for the backend. Python packages will need to be installed on a virtual environment created in the **Server** folder
   Install dependencies after creating and activating your virtual environment: <br>```pip install Flask Flask-Cors requests spotipy google-auth google-auth-oauthlib```
2. Download the _client_secret.json_ file and place it in the Server folder. This file contains information for the YouTube Data API and is accessed in the backend
3. For development purposes, SQLite is used for storage. Download the **DB Browser for SQLite** app from the internet, or from the official website. Then, create a database file by selecting "create database" in the app and placing it in the Server folder

# Backend Routes
<ins>Authentication</ins>
<br>
This backend was designed so that both Spotify and YouTube sessions/cookies are sent to the browser, but it is ideal to perform the Spotify login first on the front-end
There are four variables that can be changed (All in CAPS) and is listed with the first 100 lines. The first two links below will redirect to a link specified in those variables.
<br>
The backend runs on PORT 5000 and the frontend runs on PORT 3000, so include http://localhost:PORT/ in API calls in the front end, and redirect links to the front end (specified in variables mentioned above)
<br>
**GET:**
<br>
```/spotify/login``` is the link to login with Spotify<br>
```/youtube/login``` is the link to login with YouTube<br>
```/auth/logout``` clears Flask session for Spotify and YouTube<br>

<ins>Spotify Routes</ins>
<br>
Once the user is logged in to Spotify, these routes can be used. If these routes are called without the user being logged in, they will be redirected to url specified in SPOTIFY_ERROR_REDIRECT variable
<br>
**GET:**
<br>
```/spotify/user``` returns an array object with length 1, The object has these specific children: userName, image<br>
(if response.data[0] represents the object, response.data[0].userName is the username and response.data[0].image is the link to user's profile picture<br>
```/db/playlists``` returns an array of objects representing each playlist. Each object has these specific children: id, name, image.<br>
   You can optinally pass a query "search", but is not required. This performs full-text search on the playlists. Example: ```/db/playlist?search=drivingplaylist```<br>
```/db/songs/<playlist_id>``` pass a parameter of the playlist ID (can be retrieved from the route above) and returns an array of objects representing each song. Each object has these specific children: song_id, song_name, song_artists, song_album, song_image (NOTE: song_artists is a string an not an array of artists)










# Disclaimer
The publicity of this repository is for viewing and recuriting purposes only.
