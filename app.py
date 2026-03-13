import os
import json
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask_mail import Mail, Message
from cv_parser import parse_cv_with_ollama

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production')

UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'data/cv.json'
ALLOWED_EXTENSIONS = {'docx'}
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# Flask-Mail configuration (similar to BridgeSpace)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config.get('MAIL_USERNAME'))

mail = Mail(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_cv_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_cv_data(data):
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── Public routes ───────────────────────────────────────────────

@app.route('/')
def index():
    cv = load_cv_data()
    return render_template('index.html', cv=cv)

@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name    = data.get('name', '').strip()
    email   = data.get('email', '').strip()
    message = data.get('message', '').strip()
    if not name or not email or not message:
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400
    recipient = os.environ.get('CONTACT_RECIPIENT_EMAIL') or app.config.get('MAIL_DEFAULT_SENDER')
    if not recipient or not app.config.get('MAIL_SERVER'):
        # Fallback: log only if mail is not configured
        print(f"[CONTACT] (mail not configured) {name} <{email}>: {message}")
        return jsonify({'success': True})

    try:
        msg = Message(
            subject=f"[diogocordeiro.pt] New message from {name}",
            recipients=[recipient],
            reply_to=email or None,
        )
        msg.body = (
            f"New contact form submission from your portfolio site:\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n\n"
            f"Message:\n{message}\n"
        )
        mail.send(msg)
        return jsonify({'success': True})
    except Exception as e:
        print(f"[CONTACT][ERROR] failed to send email: {e}")
        return jsonify({'success': False, 'error': 'Unable to send email at the moment.'}), 500

# ── Admin routes ────────────────────────────────────────────────

@app.route('/admin', methods=['GET'])
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    cv = load_cv_data()
    return render_template('admin.html', cv=cv)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        token = request.form.get('g-recaptcha-response')
        if not RECAPTCHA_SITE_KEY or not RECAPTCHA_SECRET_KEY:
            error = 'reCAPTCHA is not configured.'
        elif not token:
            error = 'Please complete the reCAPTCHA.'
        else:
            try:
                resp = requests.post(
                    'https://www.google.com/recaptcha/api/siteverify',
                    data={
                        'secret': RECAPTCHA_SECRET_KEY,
                        'response': token,
                        'remoteip': request.remote_addr,
                    },
                    timeout=5,
                )
                result = resp.json()
                if not result.get('success'):
                    error = 'reCAPTCHA verification failed. Please try again.'
            except Exception:
                error = 'reCAPTCHA verification failed. Please try again.'

        if not error:
            if request.form.get('password') == ADMIN_PASSWORD:
                session['admin'] = True
                return redirect(url_for('admin'))
            error = 'Incorrect password.'

    return render_template('admin_login.html', error=error, recaptcha_site_key=RECAPTCHA_SITE_KEY)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    if not session.get('admin'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    if 'cv_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided.'}), 400

    file = request.files['cv_file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Please upload a .docx file.'}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        cv_data = parse_cv_with_ollama(filepath)
        save_cv_data(cv_data)
        return jsonify({'success': True, 'data': cv_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/cv-data')
def admin_cv_data():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(load_cv_data() or {})

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    app.run(host=host, port=port, debug=True)
