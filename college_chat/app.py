from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'college-chat-secret-key-change-later'
socketio = SocketIO(app, cors_allowed_origins="*")

DATA_FILE = 'chat_data.json'


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "messages": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_user_by_email(email):
    data = load_data()
    for user in data['users']:
        if user['email'] == email:
            return user
    return None


def get_user_by_id(user_id):
    data = load_data()
    for user in data['users']:
        if user['id'] == user_id:
            return user
    return None


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    return redirect(url_for('login_page'))


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'GET':
        return render_template('register.html')

    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not name or not email or not password:
        flash('All fields are required.')
        return redirect(url_for('register_page'))

    if not email.endswith('@vitbhopal.ac.in'):
        flash('Please use your college email ending in @vitbhopal.ac.in')
        return redirect(url_for('register_page'))

    data = load_data()

    if get_user_by_email(email):
        flash('An account with this email already exists.')
        return redirect(url_for('register_page'))

    is_first_user = len(data['users']) == 0

    new_user = {
        "id": len(data['users']) + 1,
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "role": "admin" if is_first_user else "student",
        "is_approved": True if is_first_user else False,
        "created_at": datetime.utcnow().isoformat()
    }

    data['users'].append(new_user)
    save_data(data)

    if is_first_user:
        flash('Registered! You are the first user, so you are the Admin. Please log in.')
    else:
        flash('Registered! Please wait for an admin to approve your account before logging in.')

    return redirect(url_for('login_page'))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    user = get_user_by_email(email)

    if not user or not check_password_hash(user['password_hash'], password):
        flash('Invalid email or password.')
        return redirect(url_for('login_page'))

    if not user['is_approved']:
        flash('Your account is not approved yet. Please wait for admin approval.')
        return redirect(url_for('login_page'))

    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['role'] = user['role']

    return redirect(url_for('chat_page'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/chat')
def chat_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    data = load_data()
    messages = data['messages'][-50:]

    return render_template(
        'chat.html',
        user_name=session['user_name'],
        role=session['role'],
        messages=messages
    )


@app.route('/admin')
def admin_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    if session.get('role') != 'admin':
        flash('You are not authorized to view this page.')
        return redirect(url_for('chat_page'))

    data = load_data()
    pending_users = [u for u in data['users'] if not u['is_approved']]

    return render_template('admin.html', pending_users=pending_users, user_name=session['user_name'])


@app.route('/admin/approve/<int:user_id>')
def approve_user(user_id):
    if session.get('role') != 'admin':
        flash('You are not authorized to do this.')
        return redirect(url_for('chat_page'))

    data = load_data()
    for user in data['users']:
        if user['id'] == user_id:
            user['is_approved'] = True
            break
    save_data(data)

    flash('User approved successfully.')
    return redirect(url_for('admin_page'))


@socketio.on('connect')
def handle_connect():
    if 'user_id' not in session:
        return False
    join_room('general')


@socketio.on('send_message')
def handle_send_message(data_from_client):
    if 'user_id' not in session:
        return

    text = data_from_client.get('text', '').strip()
    if not text:
        return

    data = load_data()

    new_message = {
        "user_name": session['user_name'],
        "text": text,
        "created_at": datetime.utcnow().strftime('%I:%M %p')
    }

    data['messages'].append(new_message)
    save_data(data)

    emit('receive_message', new_message, room='general')


if __name__ == '__main__':
    socketio.run(app, debug=False, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
