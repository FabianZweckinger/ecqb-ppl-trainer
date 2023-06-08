import json
import random

import flask_login
import flask
from flask import render_template, request
from passlib.hash import sha256_crypt

import secrets

app = flask.Flask(__name__)
app.secret_key = secrets.secret_key
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

print("Starting ECQBPPL Trainer Server")

users = {}
topics_abbreviations = {}
questions = {}


def write_user_db():
    with open('database/users.json', 'w') as f:
        json.dump(users, f)


def reload_database():
    with open('database/users.json', encoding='utf8') as f:
        global users
        users = json.load(f)

    with open('database/topicAbbreviations.json', encoding='utf8') as f:
        global topics_abbreviations
        topics_abbreviations = json.load(f)

    with open('database/questions.json', encoding='utf8') as f:
        global questions
        questions = json.load(f)


reload_database()


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
    reload_database()

    flask_user = flask_login.current_user
    current_user = users[flask_user.id]

    quiztype = request.args.get('quiztype')
    quiz = {}

    if quiztype is not None:
        # Init questions in user:
        if quiztype not in current_user['questions']:
            current_user['questions'][quiztype] = {}
            for index, q in enumerate(questions[quiztype]):
                print(index)
                current_user['questions'][quiztype][index] = {"correctGuesses": 0}
        write_user_db()

        # Get the least known question
        least_known_questions = {}  # correctGuesses used as key

        for question_index, value in current_user['questions'][quiztype].items():
            if value['correctGuesses'] not in least_known_questions:
                least_known_questions[value['correctGuesses']] = []
            least_known_questions[value['correctGuesses']].append(question_index)
        least_known_question_count = min(current_user['questions'][quiztype].keys())

        question = int(random.choice(least_known_questions[int(least_known_question_count)]))

        quiz = {
            'type': quiztype,
            'questionNumber': question,
        }

    return render_template('dashboard.html', state=state, is_admin=current_user["isAdmin"],
                           topics_abbreviations=topics_abbreviations,
                           users=users, questions=questions, quiz=quiz)


@app.route('/api/questions')
@flask_login.login_required
def questions_api():
    with open('database/questions.json', encoding='utf8') as f:
        data = json.load(f)
        return data, 200, {'content-type': 'application/json'}


@app.route('/api/user', methods=['POST', 'DELETE', 'PUT'])
@flask_login.login_required
def user_api():

    def success():
        write_user_db()
        return {'success': True}, 200, {'content-type': 'application/json'}

    def failure():
        return {'success': False}, 200, {'content-type': 'application/json'}

    req_data = request.get_json()

    if request.method == 'POST':
        username = req_data['username']
        password = req_data['password']

        if username not in users:
            new_user = {
                "password": sha256_crypt.using(rounds=5000).hash(password),
                "isAdmin": False,
                "questions": []
            }

            users[username] = new_user

            return success()
        else:
            return failure()

    elif request.method == 'DELETE':
        del users[req_data['username']]
        return success()

    elif request.method == 'PUT':
        users[req_data['username']]['isAdmin'] = req_data['isAdmin']
        return success()


@app.route('/api/quiz', methods=['POST'])
@flask_login.login_required
def quiz_api():

    req_data = request.get_json()
    flask_user = flask_login.current_user
    current_user = users[flask_user.id]

    if request.method == 'POST':
        answer_index = req_data['answerIndex']
        quiz_type = req_data['quizType']
        question_number = int(req_data['questionNumber'])

        true_answer = int(questions[quiz_type][question_number]['true_answer'])
        correct = False
        if true_answer == int(answer_index):
            correct = True

        correct_guesses = current_user['questions'][quiz_type][str(question_number)]["correctGuesses"] + 1
        current_user['questions'][quiz_type][str(question_number)]["correctGuesses"] = correct_guesses
        write_user_db()

        return {'correct': correct, 'true-answer': true_answer}, 200, {'content-type': 'application/json'}


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return app.send_static_file('login.html')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return app.send_static_file('login.html')


if __name__ == '__main__':
    app.run()
