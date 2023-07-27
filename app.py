import json
import os
import random
import flask
from flask import render_template, request, send_file
from waitress import serve
import flask_login
from passlib.hash import sha256_crypt
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

PORT = config.getint("Server", "Port")

app = flask.Flask(__name__)
app.secret_key = config.get("Server", "SecretKey")
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
        remember = 'remember-me' in flask.request.form
        flask_login.login_user(user, remember=remember)
        return flask.redirect(flask.url_for('dashboard'))

    return app.send_static_file('login.html')


@app.route('/images/<image>')
@flask_login.login_required
def get_images(image=None):
    return send_file(os.path.join(app.root_path, 'database', 'images', image + '.png'), mimetype='image/png')


@app.route('/')
@app.route('/<state>')
@flask_login.login_required
def dashboard(state=None):
    reload_database()

    flask_user = flask_login.current_user
    current_user = users[flask_user.id]

    progress = {}
    for topic in topics_abbreviations.keys():
        if topic in current_user['questions'].keys():
            questions_correct_min = [0, 0, 0]
            questions_correct_exact = [0, 0, 0]
            questions_count = len(current_user['questions'][topic].items())

            for question_index, value in current_user['questions'][topic].items():
                if value['correctGuesses'] >= 1:
                    questions_correct_min[0] = questions_correct_min[0] + 1
                if value['correctGuesses'] >= 2:
                    questions_correct_min[1] = questions_correct_min[1] + 1
                if value['correctGuesses'] >= 3:
                    questions_correct_min[2] = questions_correct_min[2] + 1

                if value['correctGuesses'] == 1:
                    questions_correct_exact[0] = questions_correct_exact[0] + 1
                elif value['correctGuesses'] == 2:
                    questions_correct_exact[1] = questions_correct_exact[1] + 1
                elif value['correctGuesses'] >= 3:
                    questions_correct_exact[2] = questions_correct_exact[2] + 1

            progress_absolute = [round(questions_correct_min[0] / questions_count * 100),
                                 round(questions_correct_min[1] / questions_count * 100),
                                 round(questions_correct_min[2] / questions_count * 100)]
            progress_relative = [round(questions_correct_exact[0] / questions_count * 100),
                                 round(questions_correct_exact[1] / questions_count * 100),
                                 round(questions_correct_exact[2] / questions_count * 100)]

            progress[topic] = {
                'absolute':
                    {
                        '1': progress_absolute[0],
                        '2': progress_absolute[1],
                        '3': progress_absolute[2]
                    },
                'relative':
                    {
                        '1': progress_relative[0],
                        '2': progress_relative[1],
                        '3': progress_relative[2]
                    },
            }
        else:
            progress[topic] = {
                'absolute':
                    {
                        '1': 0,
                        '2': 0,
                        '3': 0
                    },
                'relative':
                    {
                        '1': 0,
                        '2': 0,
                        '3': 0
                    }
            }

    quiztype = request.args.get('quiztype')
    quiz = {}
    mockexam = {}

    if state == 'quiz':
        if quiztype is not None:
            # Init questions in user:
            if quiztype not in current_user['questions']:
                current_user['questions'][quiztype] = {}
                for index, q in enumerate(questions[quiztype]):
                    current_user['questions'][quiztype][index] = {"correctGuesses": 0}
            write_user_db()

            # Get the least known question
            least_known_questions = {}  # correctGuesses used as key

            for question_index, value in current_user['questions'][quiztype].items():
                if value['correctGuesses'] not in least_known_questions:
                    least_known_questions[value['correctGuesses']] = []
                least_known_questions[value['correctGuesses']].append(question_index)
            least_known_question_count = min(least_known_questions.keys())
            question = int(random.choice(least_known_questions[int(least_known_question_count)]))

            quiz = {
                'type': quiztype,
                'questionNumber': question,
            }
    elif state == 'mockexam':
        if quiztype is not None:
            indexes = random.sample(range(len(questions[quiztype])), 10)
            mockexam = {
                'type': quiztype,
                'questionNumbers': indexes,
            }

    return render_template('dashboard.html', state=state, is_admin=current_user["isAdmin"],
                           topics_abbreviations=topics_abbreviations, users=users,
                           questions=questions, quiz=quiz, mockexam=mockexam, progress=progress)


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
                "questions": {}
            }

            users[username] = new_user

            return success()
        else:
            return failure()

    elif request.method == 'DELETE':
        flask_user = flask_login.current_user
        # Admins can't delete own user
        if req_data['username'] != flask_user.id:
            del users[req_data['username']]
            return success()
        else:
            return failure()

    elif request.method == 'PUT':
        if not req_data['isAdmin']:
            # A user can only be converted to a default user, if there is at least 1 other admin left
            admin_count = 0
            for username in users:
                if users[username]['isAdmin']:
                    admin_count += 1

            if admin_count > 1:
                users[req_data['username']]['isAdmin'] = False
                return success()
            else:
                return failure()
        else:
            users[req_data['username']]['isAdmin'] = True
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

        true_answer = int(questions[quiz_type][question_number]['trueAnswer'])

        if true_answer == int(answer_index):
            correct = True
            current_user['questions'][quiz_type][str(question_number)]["correctGuesses"] += 1
            write_user_db()
        else:
            correct = False
            current_user['questions'][quiz_type][str(question_number)]["correctGuesses"] -= 1

        return {'correct': correct, 'trueAnswer': true_answer}, 200, {'content-type': 'application/json'}


@app.route('/api/mockexam', methods=['POST'])
@flask_login.login_required
def mockexam_api():
    req_data = request.get_json()
    flask_user = flask_login.current_user
    current_user = users[flask_user.id]

    if request.method == 'POST':
        mockexam_answers = req_data['mockexamAnswers']
        mockexam_type = req_data['quizType']
        correct_count = 0
        incorrect_count = 0
        answers_correct = {}

        for question_number, answer_index in mockexam_answers.items():
            question_number = int(question_number)
            answer_index = int(answer_index)
            true_answer = int(questions[mockexam_type][question_number]['trueAnswer'])
            answers_correct[question_number] = true_answer

            if answer_index == true_answer:
                correct_count += 1
                current_user['questions'][mockexam_type][str(question_number)]["correctGuesses"] += 1
            else:
                incorrect_count += 1
                current_user['questions'][mockexam_type][str(question_number)]["correctGuesses"] -= 1

        response_json = {'correctCount': correct_count,
                         'incorrectCount': incorrect_count,
                         "answersCorrect": answers_correct}

        write_user_db()

        return response_json, 200, {'content-type': 'application/json'}


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return app.send_static_file('login.html')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return app.send_static_file('login.html')


print('Server initialized')
print('Server running on http://localhost:' + str(PORT))
#serve(app, host='0.0.0.0', port=PORT)
