import json
import flask_login
import flask
from flask import render_template
from passlib.hash import sha256_crypt

import secrets

app = flask.Flask(__name__)
app.secret_key = secrets.secret_key
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

print("Starting ECQBPPL Trainer Server")

with open('database/database.json', encoding='utf8') as f:
    users = json.load(f)['users']

class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return

    user = User()
    user.id = username
    return user


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in users:
        return

    user = User()
    user.id = username
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return app.send_static_file('login.html')

    username = flask.request.form['username']
    if username in users and sha256_crypt.verify(flask.request.form['password'], users[username]['password']):
        user = User()
        user.id = username
        flask_login.login_user(user)
        return flask.redirect(flask.url_for('dashboard'))

    return app.send_static_file('login.html')


@app.route('/')
@app.route('/<state>')
@flask_login.login_required
def dashboard(state=None):
    # Reload data from database
    with open('database/database.json', encoding='utf8') as f:
        users = json.load(f)['users']

    with open('database/abbreviations.json', encoding='utf8') as f:
        topicsAbbreviations = json.load(f)['topicsAbbreviations']

    with open('database/questions.json') as f:
        questions = json.load(f)

    current_user = flask_login.current_user
    is_admin = users[current_user.id]["isAdmin"]
    return render_template('dashboard.html', state=state, is_admin=is_admin, topicsAbbreviations=topicsAbbreviations,
                           users=users, questions=questions)


@app.route('/api')
@flask_login.login_required
def protected():
    with open('database/questions.json') as f:
        data = json.load(f)
        return data, 200, {'content-type': 'application/json'}


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return app.send_static_file('login.html')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return app.send_static_file('login.html')


if __name__ == '__main__':
    app.run()
