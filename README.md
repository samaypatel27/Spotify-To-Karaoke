# About
Full-stack React-app, using Spotify & YouTube APIs/OAuth 2.0 to develop a platform to convert spotify playlists into karaoke equivalents on YouTube

# Stacks
OLD CLIENT:<br>
Front-End: React.js, CSS, Bootstrap <br>
Back-End: Python (Flask), PostegreSQL/SQLAlchemy

# Instructions
1. This project uses Flask for the backend. Python packages will need to be installed on a virtual environment created in the **Server** folder
   Install dependencies after creating and activating your virtual environment: <br>```pip install SQLAlchemy Flask Flask-Cors requests spotipy google-auth google-auth-oauthlib```
2. Download the _client_secret.json_ file and place it in the Server folder. This file contains information for the YouTube Data API and is accessed in the backend
3. For development purposes, PostegreSQL is used for storage. You can optionally download an app to view the data, PG Admin is a good suggestion.
4. Create a new client folder to use. Keep the old client folder. If you want to test/view project with the old client folder, do ```npm start``` in the client folder and ```flask run``` in the server folder. You can only run the backend if you have installed the flask library in your virtual env.
5. Add the .env to the server file

# Database Design
This can be viewed in server/models.py. There are 3 tables that will hold the information for everyone who uses this application. The playlists and songs table are marked with a Foreign key that references to their parents.

# Backend Routes
<ins>Authentication</ins>
<br>
This backend was designed so that both Spotify and YouTube sessions/cookies are sent to the browser, but it is ideal to perform the Spotify login first on the front-end
There are FIVE variables that can be changed (All in CAPS) and is listed with the first 100 lines. The first two links below will redirect to a link specified in those variables.
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
**POST:**
```/spotify/sync``` This route should be executed when the user logs in for the very first time with OAuth, and if the user wants their data refreshed. Data refreshing is important because Spotify Data
is only taken from the database. This POST route adds user data, playlist data, and song data into the PostegreSQL Database Schema <br><br>

**GET:**
<br>
```/db/user``` returns an object with "name" and "image", image is an image URL link<br>
```/db/playlists``` returns an array of objects representing each playlist. Each object has these specific children: id, name, image.<br>
   You can optinally pass a query "search", but is not required. This performs full-text search on the playlists. Example: ```/db/playlist?search=drivingplaylist```<br>
```/db/songs/<playlist_id>``` pass a parameter of the playlist ID (can be retrieved from the route above) and returns an array of objects representing each song. Each object has these specific children: id, name, artist, album, image (NOTE: song_artists is a string an not an array of artists)<br>
You can also search for specific songs by passing in a search query. Example: ```/db/songs/somerandomid?search=gravity```. Currently, the search feature only search's by song name, not artist or anything else, but that could change in the future.


<ins>YouTube Routes</ins>
<br>
**GET:**
<br>
```/youtube/playlists``` returns an array of objects of all of the youtube playlists. Each object has these specific children: id, title, description, thumbnail (thumbnail is a link to an image)
<br><br>
**POST:**
<br>
```/youtube/playlists``` returns a link to a newly created YouTube Playlist. This is the route in charge of the conversion and creation of the YouTUbe Karaoke playlist. A body is required, and the body
must be an array of strings, which represent the songs to search for. For now, each element in the array should represent a query that is like ' songName "-" artistName `<br>
Example array in the frontend that can be passed in the body: ['Get You - Daniel Ceasar', 'Reality in Motion - Tame Impala']<br>
You MUST also pass in 3 queries representing the title, description, is_public (a boolean)<br>
Example query request (required for POST only): ```/youtube/playlists?title=myKaraokePlaylists&description=formyfriend&is_public=False```










# Disclaimer
SQLite only allows one write operation to allowed at a certain time. Therefore, if you are running the flask server previously and the end it, a SQLite connection is still maintained. When you reboot the server,
write operations such as ```/spotify/sync``` will result in a connection already established error. However, this isn't important since anything in React's useEffect() runs twice in development mode, so after the error, the previous connection is broken and it will successful write to the SQLite db file the second time.
