from src import db
from datetime import datetime
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    hobby = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    Admin = db.Column(db.Boolean, default=False)
    occupation = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    author = db.relationship('Posts', backref='author', lazy=True)

    def __repr__(self):
        return 'User %s' % self.id

    def to_dict(self):
        return {
            'name': self.name,
            'location': self.location,
            'email': self.email,
            'id': self.id,
            'active': User.is_authenticated
        }


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    post = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(200), default=datetime.today().date)
    upvote = db.Column(db.Integer, default=0)
    category = db.Column(db.String, nullable=False)
    user_id = db.Column(db.ForeignKey('user.id'))

    def __repr__(self):
        return 'Posts %s' % self.id

    def to_dict(self):
        return {
            'posts': self.post,
            'title': self.title,
            'upvote': self.upvote,
            'id': self.id
        }


class Questions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    is_answered = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    upvote = db.Column(db.Integer, default=0)
    answer = db.relationship('Answers', backref='question')

    def __repr__(self):
        return ' Questions %s' % self.id

    def to_dict(self):
        return {
            'author': self.author,
            'answered': self.is_answered,
            'question': self.question,
            'id': self.id,
            'upvote': self.upvote
        }


class Answers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.Text, nullable=False)
    upvote = db.Column(db.Integer, default=0)
    author = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(200), nullable=False, default=datetime.today().now)
    question_id = db.Column(db.ForeignKey('questions.id'))

    def __repr__(self):
        return 'Answers %s' % self.id