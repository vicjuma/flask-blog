from bs4 import BeautifulSoup
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (Flask, session, url_for, redirect, render_template, g,
                   request, flash, jsonify, abort, Blueprint)

from src.models import User, Questions, Posts, Answers
from src import db, mail
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

views_blueprint = Blueprint('users', __name__, template_folder='../templates')


def remove(html):
    out = BeautifulSoup(html, features="html.parser")
    return BeautifulSoup.get_text(out)


@views_blueprint.route('/home')
def home():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.order_by(Posts.date.asc()).paginate(page=page, per_page=6)
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
        return redirect(url_for('users.login'))


# this fuction gets called before any context
@views_blueprint.before_request
def before_request():
    g.user = None
    if 'username' in session:
        g.user = session['username']


# the register route
@views_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        session.pop('username', None)
        return render_template('register.html')
    name = request.form.get('name')
    email = request.form.get('email')
    url = hashlib.md5(email.encode('utf-8')).hexdigest()
    hobby = request.form.get('hobkby')
    occupation = request.form.get('occupation')
    location = request.form.get('location')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if user:
        flash('the email entered already exists in our databases please choose a different one', 'danger')
        return redirect(url_for('users.register'))
    items = User(name=name, email=email,
                 password=generate_password_hash(password=password, method='sha256'), url=url,
                 hobby=hobby,
                 location=location,
                 occupation=occupation)
    db.session.add(items)
    db.session.commit()
    flash('you have successfully created your account you can now login to your account', 'success')
    return redirect(url_for('users.login'))


# the login route
@views_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('users.home'))
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
                return redirect(url_for('users.home'))
            else:
                flash('invalid credentials please check your details and login again', 'danger')
                return redirect(url_for('users.login'))
        flash('the email entered does not exist in our database please register for an account', 'danger')
        return redirect(url_for('users.register'))


@views_blueprint.route('/account', methods=['GET', 'POST'])
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
            return redirect(url_for('users.account'))

    else:
        return redirect(url_for('users.login'))


# the logout route
@views_blueprint.route('/logout')
def logout():
    # it pops out the sesssions available and redirects users back to the login route
    session.pop('username', None)
    return redirect(url_for('users.login'))


# the search route
@views_blueprint.route('/home/search', methods=['POST'])
def search():
    # it searches for users in the database
    name = request.form.get('name')
    item = '%' + name + '%'
    user = User.query.filter_by(name=session['username']).first()
    response = User.query.filter(User.name.like(item)).all()
    return render_template('post.html', response=response, user=user)


@views_blueprint.route('/question', methods=['GET', 'POST'])
def question():
    page = request.args.get('page', type=int)
    user = User.query.filter_by(name=session['username']).first()
    count = Posts.query.filter_by(user_id=user.id).count()
    qn = Questions.query.paginate(page=page, per_page=6)
    return render_template('question.html', qn=qn, user=user, count=count)


@views_blueprint.route('/ask', methods=['POST'])
def ask():
    # one must be authenticated to ask questions
    if not 'username' in session:
        return redirect(url_for('users.login'))
    question = request.form.get('question')
    category = request.form.get('category')
    out = remove(question)
    user = User.query.filter_by(name=session['username']).first()
    author = user.email
    url = user.url
    item = Questions(question=out, category=category, author=author, url=url)
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('users.home'))


@views_blueprint.route('/answer/<int:id>', methods=['GET', 'POST'])
def answ(id):
    # one must be authenticated to answer questions
    if not 'username' in session:
        return redirect(url_for('users.login'))
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
    return redirect(url_for('users.question'))


@views_blueprint.route('/invite', methods=['POST'])
def invite():
    if not 'username' in session:
        return redirect(url_for('users.login'))
    email = request.form.get('email')
    message = Message('invitation to join the smartmind blog', recipients=[email])
    message.html = """
    <h1>hello {{email}}<h1>
    <p>you are invited to join smartmind blog feel free to share your knowledge
    with others.You can respond to questions from other people and if you have some burning questions you can
    drop them.
    click {{link}} to join this active blog
    </p>

    """
    try:
        mail.send(message)
        flash('you have successfully invited {0} to join sharp mind blog'.format(email), 'success')
        return redirect(url_for('users.home'))
    except:
        flash('mail not send please check your connection and try again', 'danger')
        return redirect(url_for('users.home'))


@views_blueprint.route('/complaint', methods=['POST'])
def complaint():
    if not 'username' in session:
        return redirect(url_for('users.login'))
    name = request.form.get('name')
    complaint = request.form.get('complaint')
    return redirect(url_for('users.home'))


@views_blueprint.route('/all_post', methods=['GET', 'POST'])
def all_posts():
    if not 'username' in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(name=session['username']).first()
    post = Posts.query.filter_by(user_id=user.id).all()
    count = Posts.query.filter_by(user_id=user.id).count()
    return render_template('edit.html', post=post, count=count, user=user)


@views_blueprint.route('/delete/post/<int:id>')
def delete(id):
    if not 'username' in session:
        return redirect(url_for('users.login'))
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
    return redirect(url_for('users.all_posts'))


@views_blueprint.route('/edit/post/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if not 'username' in session:
        return redirect(url_for('login'))
    post = Posts.query.get_or_404(id)
    user = User.query.filter_by(name=session['username']).first()
    if request.method == 'GET':
        return render_template('editpost.html', post=post)
    if post.user_id != user.id:
        return """<center>
        <h1>403 ERROR</h1>
        <br/>
        <h2 class="display-4">you are prohibited to edit other people posts</h2></center>""", 403
    post.post = request.form.get('edit')
    post.title = request.form.get('title')
    db.session.commit()
    flash('your post has been successfully edited', 'success')
    return redirect(url_for('users.all_posts'))


@views_blueprint.route('/user/update', methods=['POST'])
def update():
    if not 'username' in session:
        return redirect(url_for('users.login'))
    user = User.query.filter_by(name=session['username']).first()
    user.name = request.form.get('name')
    user.occupation = request.form.get('occupation')
    user.location = request.form.get('location')
    user.id = user.id
    db.session.commit()
    flash('you have updated your account succesfully please login again', 'success')
    session.pop('username', None)
    return redirect(url_for('users.login'))


@views_blueprint.route('/api')
def rest():
    users = User.query.filter_by().count()
    posts = Posts.query.filter_by().count()
    unanswered = Questions.query.group_by(Questions.is_answered == False).count()
    answered = Questions.query.group_by(Questions.is_answered == True).count()
    return jsonify({
        'users': users,
        'posts': posts,
        'unanswered questions': unanswered,
        'answered': answered
    })


@views_blueprint.route('/posts/programming')
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
        return redirect(url_for('users.login'))


@views_blueprint.route('/posts/sports')
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
        return redirect(url_for('users.login'))


@views_blueprint.route('/posts/education')
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
        return redirect(url_for('users.login'))


@views_blueprint.route('/posts/mathematics')
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
        return redirect(url_for('users.login'))


@views_blueprint.route('/posts/entertainment')
def entertainment():
    if 'username' in session:
        page = request.args.get('page', type=int)
        post = Posts.query.filter_by(category='entertainment').order_by(Posts.date.asc()).paginate(page=page,
                                                                                                   per_page=5)
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
        return redirect(url_for('users.login'))


@views_blueprint.route('/posts/politics')
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
        return redirect(url_for('users.login'))


@views_blueprint.route('/posts/technology')
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
        return redirect(url_for('users.login'))


@views_blueprint.route('/edit/question/<int:id>', methods=['GET', 'POST'])
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
    return redirect(url_for('users.question'))
