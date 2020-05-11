from flask import Blueprint, session, redirect, url_for, abort, request, render_template
from werkzeug.security import check_password_hash
from src import mail, db
from flask_mail import Message
from src.models import User, Posts, Questions, Answers

admin_blueprint = Blueprint('admin', __name__, template_folder='../templates')

@admin_blueprint.route('/login', methods=['GET', 'POST'])
def admin_login():
    if 'username' in session:
        session.pop('username', None)
        return redirect(url_for('admin.admin_login'))
    else:
        if request.method == 'GET':
            session.pop('username', None)
            return render_template('admin/admin_login.html')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            try:
                if user.Admin == True:
                    if check_password_hash(user.password, password=password):
                        session['admin'] = user.name
                        return redirect(url_for('admin.dashboard'))
                    else:
                        flash('invalid credentials please check your details and login again', 'danger')
                        return redirect(url_for('admin.admin_login'))
                abort(403)
                return redirect(url_for('users.home'))
            except:
                abort(403)



@admin_blueprint.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'admin' in session:
        users = User.query.filter_by().all()
        if request.method == 'GET':
            return render_template('admin/dashboard.html', users=users)
    else:
        return redirect(url_for('admin.admin_login'))


@admin_blueprint.route('/logout')
def logout_admin():
    if 'admin' in session:
        session.pop('admin', None)
        return redirect(url_for('admin.admin_login'))
    else:
        return redirect(url_for('admin.admin_login'))


@admin_blueprint.route('/posts')
def admin_posts():
    if 'admin' in session:
        posts = Posts.query.filter_by().all()
        if request.method == 'GET':
            return render_template('admin/admin_posts.html', posts=posts)
    else:
        return redirect(url_for('admin.admin_login'))


@admin_blueprint.route('/questions')
def admin_questions():
    if 'admin' in session:
         question = Questions.query.filter_by().all()
         return render_template('admin/admin_questions.html', question=question)
    else:
        return redirect(url_for('admin.admin_login'))

@admin_blueprint.route('/send/email', methods=['GET', 'POST'])
def inform():
    user = User.query.filter_by().all()
    if request.method == 'GET':
        return render_template('admin/email.html', user=user)
    
    else:
        title = request.form.get('title')
        email = request.form.get('email')
        recepient = request.form.get('recepient')
        
        message = Message(subject=title, recipients=[recepient])
        message.html = email
        mail.send(message=message)
        flash('mail send', success)
        return redirect(url_for('admin.infom'))
