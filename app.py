"""

This is a simple blog web application with user administration.

The aim of this web application is to show how to use Flask
framework to start the web server, do simple web page routing
and web page error handling.

Bootstrap framework is used for the formatting of this web
application. This example also shows how to use templates to
format generated web pages.

@author     Gregor Anželj <gregor.anzelj@gmail.com>
@license    GNU GPL
@copyright  (C) Gregor Anželj 2020

"""

# Import Flask modules
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.exceptions import HTTPException

# Import Flask WTForms modules
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length

# Import Flask SQLAlchemy modules
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, exc

# Import other modules
from datetime import datetime
from hashlib import md5


# ========== Create application ========== #

app = Flask(__name__, instance_relative_config=False)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)


# When SQLAlchemy Integrity Error occurs
class SQLAlchemyIntegrityError(HTTPException):
    code = 601
    name = 'SQLAlchemy IntegrityError'
    description = 'This username already exists in the database. Select different username when creating a new user.'


# ========== Route definitions ========== #
#
#  HTTP method | URL path          | Controller function
# -------------+-------------------+----------------------
#  GET         | /                 | list_posts()
#  GET         | /posts            | list_posts()
#  GET, POST   | /post/add         | add_post()
#  GET, POST   | /post/edit/<id>   | edit_post(id)
#  GET, POST   | /post/delete/<id> | delete_post(id)
#  GET         | /post/view/<id>   | view_post(id)
#  GET, POST   | /login            | user_login()
#  GET, POST   | /logout           | user_logout()
#  GET, POST   | /user/password    | change_password()
#  GET, POST   | /user/add         | add_user()
#  GET, POST   | /user/edit/<id>   | edit_user(id)
#  GET, POST   | /user/delete/<id> | delete_user(id)
#  GET         | /admin            | view_admin()
# -------------+-------------------+----------------------
#

# Index page for blog web application
@app.route('/', methods=['GET'])
@app.route('/posts', methods=['GET'])
def list_posts():
    # Get all authors and their blog posts, newest first
    records = db.session.query(Blogpost).order_by(Blogpost.created.desc()).all()

    return render_template('index.html', user=session, data=records)


# Add new blog post
@app.route('/post/add', methods=['GET', 'POST'])
def add_post():
    # Setup form
    form = AddPostForm()

    # Process form
    if form.validate_on_submit():
        # Handle creating blog post in the database
        if request.method == 'POST' and 'submit' in request.form:

            # Save blog post to the database
            timestamp = datetime.now()
            record = Blogpost(
                created = timestamp,
                updated = timestamp,
                title   = request.form.get('title'),
                summary = request.form.get('summary'),
                content = request.form.get('content'),
                author_id = session['user_id']
            )
            db.session.add(record)
            db.session.commit()
            #flash('Blogpost was successfully created.')

        return redirect(url_for('list_posts'))

    return render_template('post.html', user=session, type='add', title='Add post', form=form)


# Edit existing blog post
@app.route('/post/edit/<id>', methods=['GET', 'POST'])
def edit_post(id):
    # Get existing blog post by id
    record = db.session.query(Blogpost).get(id)

    # Setup form
    form = EditPostForm(obj=record)

    # Process form
    if form.validate_on_submit():
        # Handle updating blog post in the database
        if request.method == 'POST' and 'submit' in request.form:

            # Update blog post in the database
            timestamp = datetime.now()
            record.updated = timestamp
            record.title   = request.form.get('title')
            record.summary = request.form.get('summary')
            record.content = request.form.get('content')
            db.session.commit()
            #flash('Blogpost was successfully updated.')

        return redirect(url_for('list_posts'))

    return render_template('post.html', user=session, type='edit', title='Edit post', form=form, item=record)


# Delete existing blog post
@app.route('/post/delete/<id>', methods=['GET', 'POST'])
def delete_post(id):
    # Get existing blog post by id
    record = db.session.query(Blogpost).get(id)

    # Setup form
    form = DeletePostForm()

    # Process form
    if form.validate_on_submit():
        # Handle deleting blog post from the database
        if request.method == 'POST' and 'submit' in request.form:

            # Delete blog post from the database
            db.session.delete(record)
            db.session.commit()
            #flash('Blogpost was successfully deleted.')

        return redirect(url_for('list_posts'))

    return render_template('post.html', user=session, type='delete', title='Delete post', form=form, item=record)


# View and read blog post
@app.route('/post/view/<id>', methods=['GET', 'POST'])
def view_post(id):
    # Get existing blog post by id
    record = db.session.query(Blogpost).get(id)

    return render_template('view.html', user=session, title='View post', item=record)


# User login page
@app.route('/login', methods=['GET', 'POST'])
def user_login():
    # Setup form
    form = LoginForm()

    # Process form
    if form.validate_on_submit():
        if request.method == 'POST' and 'submit' in request.form:
            # Get user data from the database
            user = db.session.query(User).filter_by(username=request.form.get('username')).first()

            # Handle user login
            if user:
                password = md5(request.form.get('password').encode('utf-8')).hexdigest()
                if user.password.lower() == password:
                    session['firstname'] = user.firstname
                    session['lastname'] = user.lastname
                    session['username'] = user.username
                    session['user_id']  = user.id
                    session['loggedin'] = True
                    session['is_admin'] = user.admin
                    # flash('User successfully loggedin.')
                else:
                    return redirect(url_for('user_login'))
                    # flash('Incorrect password.')
            else:
                return redirect(url_for('user_login'))
                # flash('User not found.')

            return redirect(url_for('list_posts'))

    return render_template('login.html', user=session, title='Sign in', form=form)


# User logout page
@app.route('/logout', methods=['GET', 'POST'])
def user_logout():
    # Setup form
    form = LogoutForm()

    # Process form
    if form.validate_on_submit():
        # Handle user logout
        if request.method == 'POST' and 'submit' in request.form:
            # Clear session with user's data
            session.clear()

            return redirect(url_for('list_posts'))

    return render_template('form.html', user=session, type='logout', title='Sign out', form=form)


# Change user password
@app.route('/user/password', methods=['GET', 'POST'])
def change_password():
    # Setup form
    form = ChangePasswordForm()

    # Get user data from the database, if user is loggedin
    if 'username' in session.keys():
        user = db.session.query(User).filter_by(username=session['username']).first()
    else:
        user = None

    # Process form
    if form.validate_on_submit():
        # Handle user password change
        if request.method == 'POST' and 'submit' in request.form:
            if user:
                password = md5(form.password.data.encode('utf-8')).hexdigest()
                if user.password.lower() == password and \
                   form.passnew1.data == form.passnew2.data:

                    # Change user password in the database
                    user.password = md5(form.passnew1.data.encode('utf-8')).hexdigest()
                    db.session.commit()
                    # flash('User password successfully changed.')
                else:
                    return redirect(url_for('change_password'))
                    # flash('Incorrect current password.')
            else:
                pass
                # flash('User not found.')

        return redirect(url_for('list_posts'))

    return render_template('form.html', user=session, type='passwd', title='Change password', form=form)


# Add new user
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    # Setup form
    form = AddUserForm()

    # Process form
    if form.validate_on_submit():
        # Handle adding user to the database
        if request.method == 'POST' and 'submit' in request.form:

            # Save user details to the database
            record = User(
                firstname = request.form.get('firstname'),
                lastname = request.form.get('lastname'),
                username = request.form.get('username'),
                password = md5(request.form.get('password').encode('utf-8')).hexdigest(),
                admin = request.form.get('admin')
            )
            try:
                db.session.add(record)
                db.session.commit()
                #flash('User was successfully created.')
            except exc.IntegrityError:
                db.session.rollback()
                #flash('Username already exists.')
                error = SQLAlchemyIntegrityError()
                return render_template('error.html', user=session, error=error)

        # If admin is creating new user then redirect to administration index page
        if getattr(session, 'is_admin', False):
            return redirect(url_for('view_admin'))
        # otherwise (= user registered new account) redirect to site index page
        else:
            return redirect(url_for('index'))

    return render_template('user.html', user=session, type='add', title='Add user', form=form)


# Edit existing user
@app.route('/user/edit/<id>', methods=['GET', 'POST'])
def edit_user(id):
    # Get an existing user
    record = db.session.query(User).get(id)

    # Setup form
    form = EditUserForm(obj=record)

    # Process form
    if form.validate_on_submit():
        # Handle updating user in the database
        if request.method == 'POST' and 'submit' in request.form:

            # Save user details to the database
            # User should not be able to change their username
            # Password can be changed using separate form
            record.firstname = request.form.get('firstname')
            record.lastname = request.form.get('lastname')
            record.admin = request.form.get('admin')
            db.session.commit()
            #flash('User was successfully updated.')

        return redirect(url_for('view_admin'))

    return render_template('user.html', user=session, type='edit', title='Edit user', form=form)


# Delete existing user
@app.route('/user/delete/<id>', methods=['GET', 'POST'])
def delete_user(id):
    # Get a given existing user
    record = db.session.query(User).get(id)

    # Setup form
    form = DeleteUserForm()

    # Process form
    if form.validate_on_submit():
        # Handle deleting user from the database
        if request.method == 'POST' and 'submit' in request.form:

            # Delete user from the database
            db.session.delete(record)
            db.session.commit()
            # flash('User was successfully deleted.')

        return redirect(url_for('view_admin'))

    return render_template('user.html', user=session, type='delete', title='Delete user', form=form)


# Admin page for blog web application
@app.route('/admin', methods=['GET'])
def view_admin():
    # Get all user (= blog post authors)
    users = db.session.query(User).order_by(User.firstname.desc(), User.lastname.desc()).all()

    # Get all blog posts
    posts = db.session.query(Blogpost).order_by(Blogpost.created.desc(), Blogpost.id.desc()).all()

    return render_template('admin.html', user=session, users=users, posts=posts)


# Handle HTTP exceptions
@app.errorhandler(HTTPException)
def handle_exception(error):
    return render_template('error.html', user=session, error=error), error.code


# ========== Form definitions ========== #

# Form to add blog post
class AddPostForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[DataRequired('You must provide blog post title!')]
    )
    summary = TextAreaField(
        'Summary',
        validators=[DataRequired('You must provide blog post summary!')]
    )
    content = TextAreaField(
        'Content',
        validators=[DataRequired('You must provide blog post content!')]
    )
    submit = SubmitField('Create')


# Form to edit blog post
class EditPostForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[DataRequired('You must provide blog post title!')]
    )
    summary = TextAreaField(
        'Summary',
        validators=[DataRequired('You must provide blog post summary!')]
    )
    content = TextAreaField(
        'Content',
        validators=[DataRequired('You must provide blog post content!')]
    )
    submit = SubmitField('Update')


# Form to delete blog post
class DeletePostForm(FlaskForm):
    submit = SubmitField('Delete')


# Form to sign in user
class LoginForm(FlaskForm):
    username = StringField(
        'Username',
        validators = [DataRequired('You must provide username to sign in!')]
    )
    password = PasswordField(
        'Password',
        validators = [
            DataRequired('You must provide password to sign in!'),
            Length(5, 20, 'Your password is either too short or too long!')
        ],
        description='Password must be between 5 and 20 characters.'
    )
    submit = SubmitField('Sign in')


# Form to sign out user
class LogoutForm(FlaskForm):
    submit = SubmitField('Sign out')


# Form to change user password
class ChangePasswordForm(FlaskForm):
    password = PasswordField(
        'Current password',
        validators = [
            DataRequired('You must provide password.'),
            Length(5, 20, 'The password is either too short or too long.')
        ],
    )
    passnew1 = PasswordField(
        'New password',
        validators = [
            DataRequired('You must provide password.'),
            Length(5, 20, 'The password is either too short or too long.')
        ],
        description='Password must be between 5 and 20 characters.'
    )
    passnew2 = PasswordField(
        'New password again',
        validators = [
            DataRequired('You must provide password.'),
            Length(5, 20, 'The password is either too short or too long.')
        ],
    )
    submit = SubmitField('Change')


# Form to add new user
class AddUserForm(FlaskForm):
    firstname = StringField(
        'First name',
        validators = [DataRequired('You must provide first name.')]
    )
    lastname = StringField(
        'Last name',
        validators = [DataRequired('You must provide last name.')]
    )
    username = StringField(
        'Username',
        validators = [DataRequired('You must provide username.')]
    )
    password = PasswordField(
        'Password',
        validators = [
            DataRequired('You must provide password.'),
            Length(5, 20, 'The password is either too short or too long.')
        ],
        description='Password must be between 5 and 20 characters.'
    )
    admin = BooleanField(
        'Admin rights?',
        render_kw={
            'data-toggle': 'toggle',
            'data-size': 'xs',  # Extra small
            'data-on': 'Yes',
            'data-off': 'No',
            'data-onstyle': 'success',
            'data-offstyle': 'danger'
        }
    )
    submit = SubmitField('Create')


# Form to edit user
class EditUserForm(FlaskForm):
    firstname = StringField(
        'First name',
        validators = [DataRequired('You must provide first name.')]
    )
    lastname = StringField(
        'Last name',
        validators = [DataRequired('You must provide last name.')]
    )
    # Username must be disabled, so it cannot be changed in order to stay unique.
    username = StringField(
        'Username',
        render_kw={
            'disabled': 'disabled'
        }
    )
    admin = BooleanField(
        'Admin rights?',
        render_kw={
            'data-toggle': 'toggle',
            'data-size': 'xs',  # Extra small
            'data-on': 'Yes',
            'data-off': 'No',
            'data-onstyle': 'success',
            'data-offstyle': 'danger'
        }
    )
    submit = SubmitField('Update')


# Form to delete user
class DeleteUserForm(FlaskForm):
    submit = SubmitField('Delete')


# ========== Database model definitions ========== #

# Database model for User entity
class User(db.Model):
    __tablename__ = 'user'
    id        = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    firstname = db.Column(db.String, nullable=False)
    lastname  = db.Column(db.String, nullable=False)
    username  = db.Column(db.String, nullable=False, unique=True)
    password  = db.Column(db.String, nullable=False)
    admin     = db.Column(db.Boolean, default=0)
    #blogposts = db.relationship('Blogpost', backref='author', lazy='dynamic')

    def __init__(self, firstname, lastname, username, password, admin):
        self.firstname = firstname
        self.lastname  = lastname
        self.username  = username
        self.password  = password
        self.admin     = admin

    def __repr__(self):
        return '<User %r>' % self.username


# Database model for Blogpost entity
class Blogpost(db.Model):
    __tablename__ = 'blogpost'
    id      = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, nullable=False)
    updated = db.Column(db.DateTime, nullable=False)
    title   = db.Column(db.String, nullable=False)
    summary = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey(User.id))
    # Relationship
    author = db.relationship('User')

    def __init__(self, created, updated, title, summary, content, author_id):
        self.created = created
        self.updated = updated
        self.title   = title
        self.summary = summary
        self.content = content
        self.author_id = author_id

    def __repr__(self):
        return '<Blogpost %r>' % self.title


# ========== Create DB with default values ========== #

with app.app_context():
    # Create the database/tables if it/they don't exist yet
    # This call has to be after database model definitions!
    db.create_all()

    # Check if 'admin' user exist in the database
    exists = User.query.filter_by(username='admin').first()

    # Add 'admin' user to the database if there are no users
    if not exists:
        admin = User(
            firstname = 'Admin',
            lastname  = 'User',
            username  = 'admin',
            password  = md5('admin'.encode('utf-8')).hexdigest(),
            admin     = True
        )
        db.session.add(admin)
        db.session.commit()

    # Check if test data exist in the database
    exists = Blogpost.query.first()

    # Add test data to the database if it doesn't exist
    if not exists:
        timestamp = datetime.now()
        posts = [
            Blogpost(
                created = timestamp,
                updated = timestamp,
                title   = 'Lorem ipsum dolor sit amet',
                summary = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed dictum tincidunt eleifend. Morbi vulputate bibendum consectetur. Aenean mollis, massa pellentesque porta elementum, velit magna convallis libero, eu iaculis augue ex in nunc. Sed pretium nibh sagittis, aliquam leo ut, aliquet libero. Morbi justo lacus, accumsan eget mattis non, mollis eget risus. Nam vitae tortor elit. Fusce eget nunc sed urna vestibulum vulputate.',
                content = 'Nam non ante eget justo vehicula fermentum a ut erat. Sed quis tellus sit amet odio aliquet commodo. Suspendisse tincidunt ante sed iaculis varius. Nullam malesuada mauris eget libero commodo consectetur. Nunc a sem neque. Vestibulum tempor rhoncus justo vel congue. Donec sodales orci porttitor massa convallis condimentum. Etiam at sem eros. Aenean congue iaculis viverra. Nulla elementum scelerisque ligula, nec malesuada enim maximus quis. Morbi vitae orci volutpat nibh sagittis finibus in ac erat. Curabitur ut enim eu purus ornare egestas. Donec gravida est et bibendum aliquam. In fermentum ultricies leo, vel gravida odio rutrum vitae. Phasellus nec cursus justo, sit amet porta orci. Maecenas ultricies, mauris et fermentum mollis, metus metus feugiat lacus, vitae congue mi diam a arcu.',
                author_id = 1
            ),
            Blogpost(
                created = timestamp,
                updated = timestamp,
                title   = 'Integer et posuere tortor',
                summary = 'Integer et posuere tortor. Maecenas pellentesque suscipit velit, a lobortis nunc cursus ac. Suspendisse potenti. Vestibulum imperdiet, nibh vitae rhoncus luctus, nisi orci eleifend nibh, eget porta libero lacus quis lacus. In auctor gravida lacinia. Sed vel sagittis nisi. Donec pellentesque cursus euismod.',
                content = 'Quisque vel leo rutrum, laoreet tellus quis, suscipit magna. Fusce ut quam vitae arcu efficitur mattis a ut lectus. Proin ante dolor, pellentesque ac pulvinar et, porttitor sit amet nunc. Phasellus quis purus varius, mattis sapien eu, pellentesque sem. Nunc placerat sit amet turpis pretium auctor. Integer laoreet eget risus sit amet pharetra. Mauris vitae posuere nunc, quis lacinia est. Nulla placerat erat pharetra justo condimentum ultrices. Sed eget congue felis, vel vehicula metus. Nam varius tellus neque, quis scelerisque est fermentum eget. Duis commodo pharetra justo sit amet maximus. Praesent convallis massa non odio iaculis, nec tincidunt eros accumsan. Maecenas facilisis ligula molestie arcu porta, ac dictum lectus maximus. Maecenas sed ex at ex cursus fermentum vitae non elit.',
                author_id = 1
            ),
            Blogpost(
                created = timestamp,
                updated = timestamp,
                title   = 'Aliquam tincidunt tortor auctor',
                summary = 'Aliquam tincidunt tortor auctor. Suspendisse potenti. Aenean laoreet purus eget est aliquet ullamcorper. Etiam nec nisi libero. Donec id dolor nisl. Vestibulum vitae blandit est. Nullam pretium tellus fringilla, molestie urna quis, pharetra justo.',
                content = 'In id dolor vitae nisi malesuada vehicula. Etiam euismod feugiat sagittis. Duis lectus mi, rutrum ac sem fringilla, vehicula porta massa. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Pellentesque quis efficitur mauris. Integer ultricies leo a cursus dapibus. Praesent volutpat bibendum lectus eget sollicitudin. Donec rutrum libero neque, non vehicula tortor pellentesque quis. Maecenas eu elit efficitur, ornare ante eget, laoreet velit. Curabitur placerat sapien molestie est accumsan, at iaculis diam aliquam. Nullam bibendum est vitae ex placerat, vel sollicitudin arcu sollicitudin. Pellentesque sit amet pharetra purus, nec aliquam leo. Fusce ac libero tincidunt nisl convallis feugiat.',
                author_id = 1
            )
        ]
        for post in posts:
            db.session.add(post)
        db.session.commit()


# ========== Run application ========== #

if __name__ == '__main__':
    # Run application and development server
    app.run(debug=True)
