from flask import (Flask, session, url_for, redirect, render_template, g,
                     request, flash, jsonify, abort)
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, BaseView, expose
from bs4 import BeautifulSoup
from flask_mail import Mail, Message
from dotenv import load_dotenv
from datetime import datetime
from flask_login import LoginManager, UserMixin
app = Flask(__name__)
db = SQLAlchemy(app)
# this are all the configurations
mail = Mail(app)

load_dotenv()
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

app.config['SECRET_KEY'] = '49b2ff2ae97b7c12'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
# mail configurations
app.config['MAIL_USERNAME'] = 'lumulikenreagan@gmail.com'
app.config['MAIL_PASSWORD'] = '1234reagan'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'lumulikenreagan@gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_MAX_EMAILS'] = 3000
app.config['MAIL_SUPPRESS_SEND'] = True
app.config['MAIL_ASCCI_ATTACHMENTS'] = False
app.config['MAIL_DEBUG'] = True
# database path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS '] = True
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
admin = Admin(app)

class MyView(BaseView):
    def is_accessible(self):
        return login.current_user.is_authenticated() and login.current_user.is_admin

#  these are the classes to the database model
class User(UserMixin, db.Model):
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


class Posts(UserMixin, db.Model):
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


class Questions(UserMixin, db.Model):
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


class Answers(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.Text, nullable=False)
    upvote = db.Column(db.Integer, default=0)
    author = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(200), nullable=False, default=datetime.today().now)
    question_id = db.Column(db.ForeignKey('questions.id'))

    def __repr__(self):
        return 'Answers %s' % self.id

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Posts, db.session))
admin.add_view(ModelView(Questions, db.session))
admin.add_view(ModelView(Answers, db.session))
# function to strip html tags
def remove(html):
    out = BeautifulSoup(html, features="html.parser")
    return BeautifulSoup.get_text(out)

@app.route('/home')
def home():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.order_by(Posts.date.asc()).paginate(page=page, per_page=5)
        user = User.query.filter_by(name=session['username']).first()
        # checks for the first character in the email
        c = []
        for letter in user.email:
            c.append(letter)
        d = c[0]
        # counts for the post of the specific user
        count = Posts.query.filter_by(user_id=user.id).count()
        return render_template('home.html', post=post, user=user, count=count, d=d)

    else:
        return redirect(url_for('login'))

# this fuction gets called before any context
@app.before_request
def before_request():
    g.user = None
    if 'username' in session:
        g.user = session['username']

# the register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        session.pop('username', None)
        return render_template('register.html')
    name = request.form.get('name')
    email = request.form.get('email')
    url = hashlib.md5(email.encode('utf-8')).hexdigest()
    hobby = request.form.get('hobby')
    occupation = request.form.get('occupation')
    location = request.form.get('location')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if user:
        flash('the email entered already exists in our databases please choose a different one', 'danger')
        return redirect(url_for('register'))
    items = User(name=name, email=email,
             password=generate_password_hash(password=password, method='sha256'), url=url,
             hobby=hobby,
             location=location,
             occupation=occupation)
    db.session.add(items)
    db.session.commit()
    flash('you have successfully created your account you can now login to your account', 'success')
    return redirect(url_for('login'))

# the login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))
        # if there is a user in session he is automatically redirected back to the home route
    if request.method == 'GET':
        session.pop('username', None)
        return render_template('login.html')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password=password):
                session['username'] = user.name
                return redirect(url_for('home'))
            else:
                flash('invalid credentials please check your details and login again', 'danger')
                return redirect(url_for('login'))
        flash('the email entered does not exist in our database', 'danger')
        return redirect(url_for('register'))


@app.route('/account', methods=['GET', 'POST'])
def account():
    # the account route is only accesed by logged in users
    if 'username' in session:
        member = User.query.filter_by(name=session['username']).first()
        count = Posts.query.filter_by(user_id=member.id).count()
        user = User.query.filter_by(name=session['username']).first()
        if request.method == 'GET':
            return render_template('account.html', member=member, user=user, count=count)
        else:
            title = request.form.get('title')
            post = request.form.get('post')
            user = User.query.filter_by(name=session['username']).first()
            category = request.form.get('category')
            post = Posts(title=remove(title), post=remove(post), user_id=user.id, category=category)
        #    adds the posts to the database
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('account'))
    
    else:
        return redirect(url_for('login'))

# the logout route
@app.route('/logout')
def logout():
    # it pops out the sesssions available and redirects users back to the login route
    session.pop('username', None)
    return redirect(url_for('login'))

# the search route 
@app.route('/home/search', methods=['POST'])
def search():
    # it searches for users in the database
    name = request.form.get('name')
    item = '%' + name + '%'
    response = User.query.filter(User.name.like(item)).all()
    return render_template('post.html', response=response)


@app.route('/question', methods=['GET', 'POST'])
def question():
    page = request.args.get('page', type=int)
    user = User.query.filter_by(name=session['username']).first()
    count = Posts.query.filter_by(user_id=user.id).count()
    qn = Questions.query.paginate(page=page, per_page=6)
    return render_template('question.html', qn=qn, user=user, count=count)


@app.route('/ask', methods=['POST'])
def ask():
    # one must be authenticated to ask questions
    if not 'username' in session:
        return redirect(url_for('login'))
    question = request.form.get('question')
    category = request.form.get('category')
    out = remove(question)
    user = User.query.filter_by(name=session['username']).first()
    author = user.email
    url = user.url
    item = Questions(question=out, category=category, author=author, url=url)
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/answer/<int:id>', methods=['GET', 'POST'])
def answ(id):
    # one must be authenticated to answer questions
    if not 'username' in session:
        return redirect(url_for('login'))
    question = Questions.query.get_or_404(id)
    creat = User.query.filter_by(name=session['username']).first()
    count = Posts.query.filter_by(user_id=creat.id).count()
    if request.method == 'GET':
        return render_template('answer.html', question=question, count=count)
    ans = remove(request.form.get('answer'))
    user = User.query.filter_by(name=session['username']).first()
    author = user.email
    url = user.url
    item = Answers(answer=ans, question_id=question.id, author=author, url=url)
    db.session.add(item)
    db.session.commit()
    question.is_answered = True
    return redirect(url_for('question'))



@app.route('/invite', methods=['POST'])
def invite():
    if not 'username' in session:
        return redirect(url_for('login'))
    email = request.form.get('email')
    message = Message('invitation to join the smartmind blog', recipients=[email])
    message.html = """
    <h1>hello {{email}}<h1>
    <p>you are invited to join smartmind blog feel free to share your knowledge
    with others.You can respond to questions from other people and if you have some burning questions you can
    drop them.
    </p>

    """
    try:
        mail.send(message)
        flash('you have successfully invited {0} to join sharp mind blog'.format(email), 'success')
        return redirect(url_for('home'))
    except:
        flash('mail not send please check your connection and try again', 'danger')
        return redirect(url_for('home'))


@app.route('/complaint', methods=['POST'])
def complaint():
    if not 'username' in session:
        return redirect(url_for('login'))
    name = request.form.get('name')
    complaint = request.form.get('complaint')
    return redirect(url_for('home'))


@app.route('/all_post', methods=['GET', 'POST'])
def all_posts():
    if not 'username' in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(name=session['username']).first()
    post = Posts.query.filter_by(user_id=user.id).all()
    count = Posts.query.filter_by(user_id=user.id).count()
    return render_template('edit.html', post=post, count=count, user=user)

@app.route('/delete/post/<int:id>')
def delete(id):
    if not 'username' in session:
        return redirect(url_for('login'))
    post = Posts.query.get_or_404(id)
    user = User.query.filter_by(name=session['username']).first()   
    if post.user_id != user.id:
        return """<center>
        <h1>404 ERROR</h1>
        <br/>
        <h2 class="display-4">you cannot delete this post
         which does not belong to you </h2></center>""", 404
    db.session.delete(post)
    db.session.commit()
    flash('your post has been successfully deleted', 'success')
    return redirect(url_for('all_posts'))

@app.route('/edit/post/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if not 'username' in session:
        return redirect(url_for('login'))
    post = Posts.query.get_or_404(id)
    user = User.query.filter_by(name=session['username']).first()
    if request.method == 'GET':
        return render_template('editpost.html', post=post)
    if post.user_id != user.id:
        return """<center>
        <h1>404 ERROR</h1>
        <br/>
        <h2 class="display-4">you cannot edit this post
         which does not belong to you click here to return home page <a href="{{url_for('hz')}}">home</a></h4></center>""", 404
    post.post = request.form.get('edit')
    post.title = request.form.get('title')
    db.session.commit()
    flash('your post has been successfully edited', 'success')
    return redirect(url_for('all_posts'))

@app.route('/user/update', methods=['POST'])
def update():
    if not 'username' in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(name=session['username']).first()
    user.name = request.form.get('name')
    user.occupation = request.form.get('occupation')
    user.location = request.form.get('location')
    user.id = user.id
    db.session.commit()
    flash('you have updated your account succesfully please login again', 'success')
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/api')
def rest():
    users = User.query.filter_by().count()
    posts = Posts.query.filter_by().count()
    unanswered = Questions.query.group_by(Questions.is_answered==False).count()
    answered = Questions.query.group_by(Questions.is_answered==True).count()
    return jsonify({
        'users' : users,
        'posts' : posts,
        'unanswered questions' : unanswered,
        'answered': answered
    })

@app.route('/posts/programming')
def programming():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.filter_by(category='programming').order_by(Posts.date.asc()).paginate(page=page, per_page=5)
        user = User.query.filter_by(name=session['username']).first()
        # checks for the first character in the email
        c = []
        for letter in user.email:
            c.append(letter)
        d = c[0]
        # counts for the post of the specific user
        count = Posts.query.filter_by(user_id=user.id).count()
        return render_template('programming.html', post=post, user=user, count=count, d=d)

    else:
        return redirect(url_for('login'))

@app.route('/posts/sports')
def sports():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.filter_by(category='sports').order_by(Posts.date.asc()).paginate(page=page, per_page=5)
        user = User.query.filter_by(name=session['username']).first()
        # checks for the first character in the email
        c = []
        for letter in user.email:
            c.append(letter)
        d = c[0]
        # counts for the post of the specific user
        count = Posts.query.filter_by(user_id=user.id).count()
        return render_template('sports.html', post=post, user=user, count=count, d=d)

    else:
        return redirect(url_for('login'))

@app.route('/posts/education')
def education():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.filter_by(category='education').order_by(Posts.date.asc()).paginate(page=page, per_page=5)
        user = User.query.filter_by(name=session['username']).first()
        # checks for the first character in the email
        c = []
        for letter in user.email:
            c.append(letter)
        d = c[0]
        # counts for the post of the specific user
        count = Posts.query.filter_by(user_id=user.id).count()
        return render_template('education.html', post=post, user=user, count=count, d=d)

    else:
        return redirect(url_for('login'))

@app.route('/posts/mathematics')
def mathematics():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.filter_by(category='mathematics').order_by(Posts.date.asc()).paginate(page=page, per_page=5)
        user = User.query.filter_by(name=session['username']).first()
        # checks for the first character in the email
        c = []
        for letter in user.email:
            c.append(letter)
        d = c[0]
        # counts for the post of the specific user
        count = Posts.query.filter_by(user_id=user.id).count()
        return render_template('mathematics.html', post=post, user=user, count=count, d=d)

    else:
        return redirect(url_for('login'))

@app.route('/posts/entertainment')
def entertainment():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.filter_by(category='entertainment').order_by(Posts.date.asc()).paginate(page=page, per_page=5)
        user = User.query.filter_by(name=session['username']).first()
        # checks for the first character in the email
        c = []
        for letter in user.email:
            c.append(letter)
        d = c[0]
        # counts for the post of the specific user
        count = Posts.query.filter_by(user_id=user.id).count()
        return render_template('entertainment.html', post=post, user=user, count=count, d=d)

    else:
        return redirect(url_for('login'))

@app.route('/posts/politics')
def politics():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.filter_by(category='politics').order_by(Posts.date.asc()).paginate(page=page, per_page=5)
        user = User.query.filter_by(name=session['username']).first()
        # checks for the first character in the email
        c = []
        for letter in user.email:
            c.append(letter)
        d = c[0]
        # counts for the post of the specific user
        count = Posts.query.filter_by(user_id=user.id).count()
        return render_template('politics.html', post=post, user=user, count=count, d=d)

    else:
        return redirect(url_for('login'))    

@app.route('/posts/technology')
def technology():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.filter_by(category='technology').order_by(Posts.date.asc()).paginate(page=page, per_page=5)
        user = User.query.filter_by(name=session['username']).first()
        # checks for the first character in the email
        c = []
        for letter in user.email:
            c.append(letter)
        d = c[0]
        # counts for the post of the specific user
        count = Posts.query.filter_by(user_id=user.id).count()
        return render_template('technology.html', post=post, user=user, count=count, d=d)

    else:
        return redirect(url_for('login'))

@app.route('/edit/question/<int:id>', methods=['GET', 'POST'])
def editqn(id):
    if not 'username' in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(name=session['username']).first()
    quest = Questions.query.get_or_404(id)
    if request.method == 'GET':
        return render_template('editqn.html', quest=quest, user=user)
    if quest.id != user.id:
        return """<center>
        <h1>404 ERROR</h1>
        <br/>
        <h2 class="display-4">you cannot edit this question
         which does not belong to you click here to return home page <a href="{{url_for('hz')}}">home</a></h4></center>""", 404
    quest.question = request.form.get('edit')
    db.session.commit()
    flash('your question has been successfully edited', 'success')
    return redirect(url_for('all_posts'))



@app.route('/edit/answer/<int:id>')
def editans(id):
    pass


if __name__ == '__main__':
    app.run(debug=True)
    
