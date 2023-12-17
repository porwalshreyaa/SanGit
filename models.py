from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()



user_likes_song = db.Table('user_likes_song',
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
)

user_dislikes_song = db.Table('user_dislikes_song',
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
)

playlists_x_songs = db.Table('playlists_x_songs',
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id'), primary_key=True),
    db.Column('playlist_id', db.Integer, db.ForeignKey('user_playlist.id'), primary_key=True)
)

album_songs = db.Table('album_songs',
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id'), primary_key=True),
    db.Column('album_id', db.Integer, db.ForeignKey('albums.id'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'users'
    _id = db.Column("id", db.Integer, autoincrement=True, primary_key=True)
    passhash = db.Column("passhash", db.String(512), nullable=False)
    username = db.Column("username", db.String(), unique=True, nullable=False)
    email = db.Column("email", db.String(64), unique=True, nullable=False)
    user_type = db.Column("user_type", db.String(8), nullable=False )
    ban  = db.Column("ban", db.String(), nullable=True )
    liked_songs = db.relationship('Song', secondary = user_likes_song, back_populates='liked_by')
    disliked_songs = db.relationship('Song', secondary = user_dislikes_song, back_populates='disliked_by')
    
class Song(db.Model):
    __tablename__ = 'songs'
    _id = db.Column("id", db.Integer, autoincrement=True,primary_key=True)
    name = db.Column("name", db.String(), nullable=False)
    lyrics = db.Column("lyrics", db.String(), nullable=True)
    date_created = db.Column("date_created", db.String(), nullable=False)
    duration = db.Column("duration", db.String(), nullable=False)
    path = db.Column("path", db.String(), nullable=False)
    img = db.Column("img", db.String(), nullable=True)
    created_by = db.Column("created_by", db.Integer, db.ForeignKey('users.id'))
    liked_by =  db.relationship('User', secondary = user_likes_song, back_populates='liked_songs')
    disliked_by =  db.relationship('User', secondary = user_dislikes_song, back_populates='disliked_songs')
    part_of = db.relationship('Album', secondary = album_songs, back_populates='songs')

class Album(db.Model):
    __tablename__ = 'albums'
    _id = db.Column("id", db.Integer, autoincrement=True, primary_key=True)
    name = db.Column("name", db.String(), nullable=False)
    genre = db.Column("genre", db.String(), nullable=True)
    artist = db.Column("artist", db.String(), nullable=False)
    created_by = db.Column("created_by", db.Integer, db.ForeignKey('users.id'))
    songs = db.relationship("Song", secondary = album_songs, back_populates='part_of')
   
class User_Playlist(db.Model):
    __tablename__= 'user_playlist'
    _id = db.Column("id", db.Integer, autoincrement=True, primary_key=True)
    name = db.Column("name", db.String(), nullable=False)
    user_id = db.Column("user_id", db.Integer(), nullable=False)
    description = db.Column("description", db.String(), nullable=True)
    songs = db.relationship('Song', secondary='playlists_x_songs', backref = db.backref('playlist'))
