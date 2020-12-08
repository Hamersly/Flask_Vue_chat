import os
from flask import Flask, render_template, request, jsonify, redirect, flash, session, url_for
from flask_cors import CORS, cross_origin
from collections import deque
from forms import LoginForm
import time
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


# ************************Config************************

class CustomFlask(Flask):  # Заменяет "{{ }}" на "%% %%"
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(
        dict(variable_start_string='%%', variable_end_string='%%'))


app = CustomFlask(__name__)
app.secret_key = ''
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, supports_credentials=True)


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ************************Db************************

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    timeAndUser = db.Column(db.String())
    message = db.Column(db.String())

    def __repr__(self):
        return f"<User {self.username}>"


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), index=True, unique=True)

    def __repr__(self):
        return f"{self.username}"


class NowTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nowTime = db.Column(db.Integer())

    def __repr__(self):
        return f"{self.nowTime}"


# ************************Secondary_functions************************

def messDecoder(data):
    """Перевод POST-запроса из b-кода в строку"""
    value = data.decode('utf-8')
    value = value[12:-2]
    return value


def timerClearMess():
    """Очистка списка сообщений и юзеров с заданным интервалом"""
    seconds = time.time()
    result = time.gmtime(seconds)
    indexTimer = 7
    try:
        nowDay = NowTime.query.all()
        nowDay = nowDay[0]
        nowDay = nowDay.nowTime
    except Exception as ex:
        print(ex)
        nowDay = None
    if nowDay != result[indexTimer]:
        messages = Messages.query.all()
        for mess in messages:
            db.session.delete(mess)
            print('delete')
        users = Users.query.all()
        for user in users:
            db.session.delete(user)
        nowtime = NowTime.query.all()
        for t in nowtime:
            db.session.delete(t)
        db.session.commit()
        newTime = NowTime(nowTime=result[indexTimer])
        db.session.add(newTime)
        db.session.commit()


# ************************Routes************************

@app.route('/chat-post/', methods=['POST'])
def addMessage():
    """Получение и добавление в список новых сообщений через WEB-интерфейс"""
    if request.method == 'POST':
        data = messDecoder(request.data)
        data = data.split('\\n')
        newMess = Messages(
            username=data[0], timeAndUser=data[1], message=data[2])
        db.session.add(newMess)
        db.session.commit()
    return 'ok'


@app.route('/chat/', methods=['GET'])
def addName():
    """Добавление имени в список присутствующих в чате"""
    user = request.args['name']
    activeUsers = Users.query.all()
    for actUser in activeUsers:
        if user in actUser.username:
            return redirect('/')
    try:
        newUser = Users(username=user)
        db.session.add(newUser)
        db.session.commit()
    except Exception as ex:
        print(ex)
        return redirect('/')
    return render_template('index.html', user=user)


@app.route('/', methods=['GET', 'POST'])
def validate():
    """Валидация данных пользователя на стартовой странице"""
    timerClearMess()
    form = LoginForm()
    if request.method == 'POST' and form.validate():
        name = request.form.get('username')
        activeUsers = Users.query.all()
        for user in activeUsers:
            if name in user.username:
                flash('Такое имя уже есть в системе!')
                return redirect('/')
        return redirect(url_for('addName', name=name))
    return render_template('first.html', title='Регистрация', message='message', form=form)


@app.route('/remove-user/', methods=['POST'])
def removeUser():
    """Запрос на удаление имени юзера из списка при его выходе из чата"""
    try:
        name = messDecoder(request.data)
        user = Users.query.filter_by(username=name).first()
        db.session.delete(user)
        db.session.commit()
    except Exception as ex:
        print(ex)
    return 'ok'


# ************************API_routes************************

@app.route('/api/add-message/', methods=['POST'])
def addMessageApi():
    """Добавление в список новых сообщений через API"""
    message = messDecoder(request.data)  # {"message":"{{UserName}}\n{{Time and userName}}\n{{Message}}"}
    message = message.split('\\n')
    try:
        newMess = Messages(username=message[0], timeAndUser=message[1], message=message[2])
        db.session.add(newMess)
        db.session.commit()
    except Exception as ex:
        print(ex)
        return jsonify('ERROR!')
    return jsonify('OK')


@app.route('/api/lists/')
def getMessageApi():
    """Запрос списка сообщений и списка зарестрированных пользователей"""
    messages = Messages.query.all()
    messageList = [{
        'name': mess.username,
        'timeAndUser': mess.timeAndUser,
        'message': mess.message
    } for mess in messages]
    users = Users.query.all()
    activeUsers = [{
        'username': user.username
    } for user in users]
    info = [activeUsers, messageList]
    timerClearMess()
    return jsonify(info)


@app.route('/api/remove-user/', methods=['POST'])
def removeUserApi():
    """Запрос на удаление имени юзера из списка при его выходе из чата"""
    name = messDecoder(request.data)
    user = Users.query.filter_by(username=name).first()
    db.session.delete(user)
    db.session.commit()
    return jsonify('OK')


@app.route('/api/add-user/', methods=['POST'])
def addUser():
    """Запрос на добавление пользователя"""
    name = messDecoder(request.data)  # {"message":"Alexander"}
    activeUsers = Users.query.all()
    for user in activeUsers:
        if name in user.username:
            return jsonify('Такое имя уже есть в системе!')
    try:
        newUser = Users(username=user)
        db.session.add(newUser)
        db.session.commit()
    except Exception as ex:
        print(ex)
        return jsonify('ERROR!')
    return jsonify('OK')


if __name__ == "__main__":
    app.run()
