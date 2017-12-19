from flask_sqlalchemy import SQLAlchemy
###########################################
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80), unique=False)
    in_room = db.Column(db.Boolean(), unique=False)
    def __repr__(self):
        return self.username
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.in_room = False

class Chatroom(db.Model):
    __tablename__ = 'chatroom'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship("User", backref="created_rooms")
    messages = db.relationship("Message", backref='room')
    def __init__(self, title):
        self.title = title
    def __repr__(self):
        return self.title

class Message(db.Model):
    __tablename__ = 'message'
    id = id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(), unique=False)
    room_id = db.Column(db.Integer, db.ForeignKey('chatroom.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship("User", backref="messages")
    def __init__(self, text):
        self.text=text
    def __repr__(self):
        return "{}:\t{}".format(self.author.username, self.text)
    def json_format(self):
        return {
            'author': self.author.username,
            'text': self.text
        }
