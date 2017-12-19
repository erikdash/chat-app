from flask import Flask, request, abort, url_for, redirect, session, render_template, flash, g, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from models import db, User, Chatroom, Message
from flask_debugtoolbar import DebugToolbarExtension
import sys
import json
##############################################################################
app = Flask(__name__)

global new_messages

app.debug = False
app.config['SECRET_KEY'] = 'tempkey'

toolbar = DebugToolbarExtension(app)
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'chat.db')
))

db.init_app(app)

@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    db.drop_all()
    db.create_all()
    print('Initialized the database.')

@app.route("/")
def default():
    global new_messages
    new_messages = []
    return redirect(url_for("login"))

@app.route("/login/")
def login():
    return render_template("login.html")

@app.route("/profile/", methods=["GET", "POST"])
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username=None):
    user = User.query.filter_by(username=request.form['user']).first()
    if request.method == "POST":
        if not username:
            if user and user.password == request.form['pass']:
                session["user_id"] = user.id
                session["new_messages"] = []
                session["all_new"] = []
                return redirect(url_for("display_all"))
            else:
                flash("Invalid username or password, please try again")
    return render_template("login.html")

def get_user_id(username):
	rv = User.query.filter_by(username=username).first()
	return rv.id if rv else None

@app.route("/all/", methods=["GET"])
def display_all():
    rooms = Chatroom.query.all()
    if len(rooms) == 0:
        flash("No rooms available. Please create one to begin chatting!") # message for if no rooms exist
    return render_template("allrooms.html", rooms=rooms, username=User.query.filter_by(id=session["user_id"]).first().username)

@app.route("/chatroom/<username>/<room_id>/", methods=["GET"])
def chatroom(username, room_id):
    user = User.query.filter_by(id=session["user_id"]).first()
    room = Chatroom.query.filter_by(id=room_id).first()
    if user.in_room == False and room is not None: # user not already in a room
        user.in_room = True
        db.session.add(user)
        db.session.commit()
        messages = Message.query.filter_by(room_id=room_id).all()
        room_title=Chatroom.query.filter_by(id=room_id).first().title
        session["room_id"] = room_id
        return render_template("chatroom.html", username=username, title=room_title, room_id=room_id, messages=messages)
    elif user.in_room == True and room is not None: # user is in a room
        flash("You're already in a room!")
        return redirect(url_for("display_all"))
    else: # room has been deleted
        flash("Room has been deleted")
        return redirect(url_for("display_all"))

@app.route("/leaveroom/")
def leave_room():
    user = User.query.filter_by(id=session["user_id"]).first()
    user.in_room = False #change in_room status
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("display_all"))

@app.route("/deleteroom/<username>/<room_id>/", methods=["GET"])
def deleteroom(username, room_id):
    to_delete = Chatroom.query.filter_by(id=room_id).first()
    db.session.delete(to_delete)
    db.session.commit()
    rooms = Chatroom.query.all()
    return redirect(url_for("display_all", rooms=rooms, username=username))


@app.route("/new_room/<username>/", methods=["POST"])
def new_room(username):
    user = User.query.filter_by(username=username).first()
    new_room = Chatroom(request.form['title'])
    new_room.creator = user
    db.session.add(new_room)
    db.session.commit()
    rooms = Chatroom.query.all()
    return redirect(url_for("display_all", rooms=rooms, username=username))


@app.route("/new_message/", methods=["POST"])
def new_message():
    user = User.query.filter_by(username=request.form["username"]).first()
    new_message = Message(request.form['messageText'])
    new_message.author_id = user.id
    new_message.room_id=request.form["room_id"]
    room = Chatroom.query.filter_by(id=request.form["room_id"]).first()
    room.messages.append(new_message)
    db.session.add(new_message)
    db.session.add(room)
    db.session.commit()
    new_messages.append(new_message.id) # add new message to global new messages
    return "OK!"

@app.route("/signup/", methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        if not request.form['user']:
            flash('You have to enter a username')
        elif not request.form['pass']:
            flash('You have to enter a password')
        elif get_user_id(request.form['user']) is not None:
            flash('The username is already taken')
        else:
            new_user = User(request.form['user'], request.form['pass'])
            db.session.add(new_user)
            db.session.commit()
            session["user_id"] = new_user.id
            session["new_messages"] = []
            session["all_new"] = []
            flash('You were successfully registered and can login now')
            return redirect(url_for('display_all'))
    return render_template('signup.html')

@app.route("/logout/", methods=["GET"])
def unlogger():
    user = User.query.filter_by(id=session["user_id"]).first()
    user.in_room = False
    db.session.add(user)
    db.session.commit()
    session.pop("user_id", None)
    flash("Logged out!")
    return redirect(url_for("login"))

@app.route("/messages/", methods=["GET"])
def get_items():
    if Chatroom.query.filter_by(id=session["room_id"]).first() == None: # polls to see if room has been deleted while this user is in it
        api_messages = [{
            'author': "exit",
            'text': "exit"}] # exit indicates that the script should make this user to leave room
        return json.dumps(api_messages)

    global new_messages
    if new_messages != []:
        session["new_messages"] = [message for message in new_messages if message not in session["all_new"]]
        [session["all_new"].append(message) for message in new_messages if message not in session["all_new"]]
        if session["new_messages"] == []:
            api_messages = []
        else:
            api_messages = [Message.query.filter_by(id=message).first().json_format() for message in session["new_messages"] if Message.query.filter_by(id=message).first().room_id == int(session["room_id"])]
    else:
        api_messages = []

    return json.dumps(api_messages)


@app.before_request
def before_request():
    g.user = None
    if "user_id" in session:
        g.user = User.query.get(session["user_id"])

@app.before_first_request
def reset():
    for row in User.query.all():
       row.in_room = False
       db.session.add(row)
       db.session.commit()

if __name__ == "__main__":
    global new_messages
    new_messages = []
    jinja_env_auto_reload=True
    app.config['TEMPLATES_AUTO_RELOAD']=True
    app.run(host="0.0.0.0", debug = True, threaded=True)
