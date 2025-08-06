from extensions import db

class User(db.Model):
    __tablename__ = "users"
    # id is the access token, when it is refreshed, the token is updated in the database as well
    id = db.Column(db.String(), primary_key = True)

    name = db.Column(db.String(), nullable = False)
    image = db.Column(db.String(), nullable = False)

    # Cascade allows deletion of this and its back populated children
    playlists = db.relationship('Playlist', back_populates='user', cascade="all, delete")

class Playlist(db.Model):
    __tablename__ = "playlists"
    id = db.Column(db.String(), primary_key = True)
    name = db.Column(db.String(), nullable = False)
    # some playlists do not have profile picture
    image = db.Column(db.String(), nullable = True)
    user_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable = False)

    user = db.relationship('User', back_populates='playlists')

    songs = db.relationship('Song', back_populates='playlist', cascade="all, delete")

class Song(db.Model):
    __tablename__ = "songs"
    # Auto incremented ID/primary key
    id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    name = db.Column(db.String(), nullable = False)
    artists = db.Column(db.String(), nullable = False)
    album = db.Column(db.String(), nullable = False)
    image = db.Column(db.String(), nullable = False)
    playlist_id = db.Column(db.String(), db.ForeignKey('playlists.id'), nullable = False)

    playlist = db.relationship('Playlist', back_populates='songs')