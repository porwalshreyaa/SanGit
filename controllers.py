from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv
from os import getenv
from functools import wraps
import os
from mutagen.mp3 import MP3
from models import *
from sqlalchemy import desc
current_dir= os.path.abspath(os.path.dirname(__file__))
# for admin stats
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import base64
from io import BytesIO

def minsec(seconds):
    seconds = round(seconds)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"

def ifban(func):
    @wraps(func)
    def inner(*args, **kwargs):
        email_id = session["email"]
        user = User.query.filter_by(email=email_id).first()
        if user.ban == 'True':
            return redirect(url_for("baned"))
        return func(*args, **kwargs)
    return inner

def log_req(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return inner

# configuration
load_dotenv()

app = Flask(__name__)
app.permanent_session_lifetime = timedelta(days=7)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+os.path.join(current_dir,"appdb.sqlite3")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = getenv('SECRET_KEY')

# general  user functionalities
@app.route("/", methods=["GET","POST"])
@log_req
@ifban
def dashboard():
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    latest_songs = Song.query.order_by(desc(Song.date_created))
    popular_songs = Song.query.all()
    if user.user_type=='admin':
        return redirect(url_for("admin_dashboard"))
    
    playlists = User_Playlist.query.filter_by(user_id=user._id).all()
    return render_template("featured_songs.html", latest_songs=latest_songs, popular_songs=popular_songs, user=user, playlists=playlists)

@app.route("/play/<int:songid>", methods=["GET", "POST"])
@ifban
def play(songid):
    latest_songs = Song.query.order_by(desc(Song.date_created))
    popular_songs = Song.query.all()
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    playlists = User_Playlist.query.filter_by(user_id=user._id).all()
    song = Song.query.get(songid)
    likers = song.liked_by
    dislikers = song.disliked_by
    if user in likers:
        like = True
    else:
        like = False
    if user in dislikers:
        dislike = True
    else:
        dislike = False

    return render_template("music.html", splay=song, user=user,  latest_songs=latest_songs, popular_songs=popular_songs, playlists=playlists, like=like, dislike=dislike)


@app.route("/play/like/<int:songid>", methods= ["GET"])
@ifban
def like(songid):
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    song = Song.query.get(songid)
    likers = song.liked_by
    dislikers = song.disliked_by
    
    if user in likers:
        likers.remove(user)
        db.session.commit()
    else:
        if user in dislikers:
            dislikers.remove(user)
        likers.append(user)
        db.session.commit()
        
    return redirect(url_for("play", songid=songid))
@app.route("/play/dislike/<int:songid>", methods= ["GET"])
@ifban
def dislike(songid):
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    song = Song.query.get(songid)
    dislikers = song.disliked_by
    likers = song.liked_by
    if user in dislikers:
        dislikers.remove(user)
        db.session.commit()
    else:
        if user in likers:
            likers.remove(user)
        dislikers.append(user)
        db.session.commit()
        
    return redirect(url_for("play", songid=songid))



@app.route("/profile", methods=["GET"])
@log_req
@ifban
def profile():
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    return render_template("profile.html", user=user)

@app.route("/profile", methods=["POST"])
@log_req
@ifban
def edit_profile():
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    if request.method == "POST":
        req_prof = request.form
        username = req_prof.get("username")
        email = req_prof.get("email")
        password = req_prof.get("password")
        if username != user.username:
            user.username = username
            db.session.commit()
        if email != user.email:
            user._id = email
            db.session.commit()
        if password != user._id:
            user.passhash = password
            db.session.commit()
        flash("success!")
    return redirect(url_for("profile"))


@app.route("/playlists", methods=["GET"])
@log_req
@ifban
def playlists():
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    playlists = User_Playlist.query.filter_by(user_id=user._id).all()
    playlists_songs_count = {}
    for playlist in playlists:
        playlists_songs_count[str(playlist._id)] = len(playlist.songs)
    return render_template("playlists.html", playlists=playlists,user=user, count=playlists_songs_count)

@app.route("/playlist/<int:playlist_id>", methods=["GET"])
@log_req
@ifban
def see_playlist(playlist_id):
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    playlists = User_Playlist.query.filter_by(user_id=user._id).all()
    id_playlist = User_Playlist.query.filter_by(_id=playlist_id).first()
    songs = Song.query.all()
    if id_playlist:
        song_results = id_playlist.songs
        return render_template("each_playlist.html", songs=songs, song_results=song_results,user=user, playlists=playlists)
    return redirect(url_for("dashboard"))

@app.route("/playlists", methods=["POST"])
@log_req
@ifban
def playlists_create():
    if request.method == 'POST':
        playlist_form = request.form
        playlist_name = playlist_form.get("pname")
        playlist_description = playlist_form.get("pdescription")
        email_id = session["email"]
        user = User.query.filter_by(email=email_id).first()
        user_playlist = User_Playlist(name = playlist_name, user_id = user._id, description= playlist_description)
        db.session.add(user_playlist)
        db.session.commit()
    return redirect(url_for("playlists"))

@app.route("/playlists/delete/<int:playlist_id>", methods=["GET"])
@log_req
@ifban
def playlists_delete(playlist_id):
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    id_playlist = User_Playlist.query.filter_by(_id=playlist_id).first()
    db.session.delete(id_playlist)
    db.session.commit()
    return redirect(url_for("playlists"))


@app.route("/search", methods=["GET", "POST"])
@ifban
def search():
    songs = Song.query.all()
    users = User.query.all()
    user = User.query.filter_by(email=session['email']).first()
    if request.method =='POST':
        form = request.form
        search_query = form.get("search_query")
        song_results = Song.query.filter(Song.name.ilike(f"%{search_query}%"))
        album_results = Album.query.filter(Album.name.ilike(f"%{search_query}%"))
        if song_results or album_results:
            return render_template("search.html", song_results=song_results.all(), album_results=album_results.all(), playlists=playlists, user=user)
    return redirect(url_for("dashboard"))


@app.route("/track/delete/<int:track_id>", methods=["GET"])
@log_req
def addto_playlist(track_id):
    users = User.query.all()
    tracks = Song.query.all()
    song = Song.query.filter_by(_id=track_id).first()
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for("see_tracks"))


@app.route("/track/delete/<int:track_id>", methods=["GET"])
@log_req
def rmfrom_playlist(track_id):
    users = User.query.all()
    tracks = Song.query.all()
    song = Song.query.filter_by(_id=track_id).first()
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for("see_tracks"))


# creator functionalities 

@app.route("/stats", methods=["GET"])
@log_req
@ifban
def stats():
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    songs= Song.query.all()
    return render_template("your_stats.html", user=user, songs=songs)

@app.route("/upload", methods=["POST"])
@log_req
@ifban
def upload_song():
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    if request.method == 'POST':
        if 'song' not in request.files or 'image' not in request.files:
            flash('No file part')
            return redirect(url_for("dashboard"))
        songfile = request.files['song']
        imagefile = request.files['image']
        if songfile.filename == '' or imagefile.filename == '':
            flash('No selected file')
            return redirect(url_for("dashboard"))
        if songfile and imagefile:
            songname = request.form['songname']
            songartist = request.form['songartist']
            if songname and songartist:
                songname = songname.strip().title()
                # songartist = songartist.strip().title()
                if songname == '':
                    flash('No selected file')
                    return redirect(url_for("dashboard"))
                songlyrics = request.form['songlyrics']
                if songlyrics:
                    songlyrics = songlyrics.strip().title()
                else:
                    songlyrics = ''
                songfile.save(os.path.join(current_dir,'static/songs/', songfile.filename))
                imagefile.save(os.path.join(current_dir,'static/images/', imagefile.filename))
                audio = MP3(os.path.join(current_dir,'static/songs/', songfile.filename))
                duration = minsec(audio.info.length)
                creation = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
                song = Song(name=songname, lyrics=songlyrics, date_created=creation, duration=duration,path=songfile.filename,img=imagefile.filename, created_by=user._id)
                db.session.add(song)
                db.session.commit()
    return redirect(url_for("dashboard"))

@app.route('/song/edit/<int:songid>', methods=['GET', 'POST'])
@log_req
@ifban
def edit_song(songid):
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    song = Song.query.filter_by(_id=songid).first()
    if request.method == 'POST':

        imagefile = request.files['image']
        if imagefile:
            imagefile.save(os.path.join(current_dir,'static/images/', imagefile.filename))
            song.img=imagefile.filename
            db.session.commit()
        if request.form.get("name"):
            song.name = (request.form.get("name")).strip().title()
            db.session.commit()
        if request.form.get("lyrics"):
            song.lyrics = (request.form.get("lyrics"))
            db.session.commit()
    return render_template('edit_song.html', user=user, song=song)


# basic functions

@app.route("/creator", methods=["POST", "GET"])
@log_req
@ifban
def creator_signup():
    email_id = session["email"]
    user = User.query.filter_by(email=email_id).first()
    if request.method == 'POST':
        if user.user_type == 'creator':
            return redirect(url_for("dashboard"))
        elif request.form.get("become_creator") == 'submit':
            user.user_type = 'creator'
            db.session.commit()
            flash('You are a creator!')
            return render_template("profile.html", user=user)
        else:
            return redirect(url_for("profile"))
    return redirect(url_for("profile"))

@app.route("/logout", methods=["GET"])
def logout():
    if "email" in session:
        session.pop('email', None)
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "email" in session:
        redirect(url_for("dashboard"))
    if request.method == "POST":
         content = request.form
         user_email = content.get("email")
         user_password = content.get("password")

         user = User.query.filter_by(email=user_email, passhash=user_password).first()

         if user:
            if "keep_me_logged" in request.form:
                session.permanent = True
            session["email"] = user_email
            return redirect(url_for("dashboard"))
         else:
             flash("Invalid Credentials!")
             return redirect(url_for("login"))
    return render_template("userLogin.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "email" in session: 
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        content = request.form
        req_email = content.get("email")
        req_username = content.get("username")
        req_password = content.get("password")
        req_passwordconfirm = content.get("password_check")
        if req_password != req_passwordconfirm:
            flash("Recheck Password!")
            return redirect(url_for("register"))
        elif User.query.filter_by(email=req_email).first():
            flash("User already exists!")
            return redirect(url_for("register"))
        elif User.query.filter_by(username=req_username).first():
            flash("Username occupied!")
            return redirect(url_for("register"))
        else:
            user = User(username= req_username, email=req_email, passhash= req_password, user_type = 'user')
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login"))
    return render_template("registration.html")

@app.route("/baned", methods=["GET"])
@log_req
def baned():
    return render_template("ban.html")

# admin routes

@app.route("/ban", methods=["GET", "POST"])
@log_req
def ban():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        user = User.query.filter_by(_id=user_id).first()
        if user.ban:
            user.ban = None
            # print("unban")
            db.session.commit()
        else:
            user.ban = 'True'
            db.session.commit()
            # print("ban")
        return redirect(url_for("see_users"))
    return redirect(url_for("see_users"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if "email" in session:
        if User.query.filter_by(email=session["email"], user_type='admin'):
            redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        content = request.form
        admin_password = content.get("password")
        admin_email = content['email']
        if User.query.filter_by(email=admin_email, passhash=admin_password, user_type='admin'):
            session["email"] = admin_email
            session.permanent = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Imposter Detected!", "error")
            return redirect(url_for("admin_login"))
    return render_template("superAdmin.html")


@app.route("/admin/dashboard", methods=["GET", "POST"])
@log_req
def admin_dashboard():
    user = User.query.filter_by(email=session["email"], user_type='admin')
    songs = Song.query.all()
    users = User.query.all()
    users_count = User.query.count()
    creators_count = User.query.filter_by(user_type='creator').count()
    songs_count = Song.query.count()
    return render_template("admin_stats.html", users_count = users_count, user=user, creators_count= creators_count, songs_count = songs_count)
    
@app.route("/users", methods=["GET", "POST"])
@log_req
def see_users():
    users = User.query.all()
    return render_template("see_users.html", users=users)

@app.route("/creators", methods=["GET", "POST"])
@log_req
def see_creators():
    users = User.query.filter_by(user_type = 'creator').all()
    return render_template("see_users.html", users=users)


@app.route("/tracks", methods=["GET", "POST"])
@log_req
def see_tracks():
    users = User.query.all()
    tracks = Song.query.all()
    return render_template("see_tracks.html", tracks=tracks, users = users)

@app.route("/track/delete/<int:track_id>", methods=["GET"])
@log_req
def tracks_delete(track_id):
    users = User.query.all()
    tracks = Song.query.all()
    song = Song.query.filter_by(_id=track_id).first()
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for("see_tracks"))

@app.route('/admin/stats')
@log_req
@ifban
def admin_stats():

    # Generate the figure **without using pyplot**.
    fig = Figure()
    ax = fig.subplots()
    ax.plot([1, 2])
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"<img src='data:image/png;base64,{data}'/>"