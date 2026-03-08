import os
import io
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Local AI utilities
from utils.pdf_reader import extract_text
from utils.summarizer import local_analyze, ask_neural_query

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'summarix_2026_secure_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///summarix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    papers = db.relationship('ResearchPaper', backref='owner', lazy=True)

class ResearchPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=request.form['username'], password=hashed_pw)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Username already exists.')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid Credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    history = ResearchPaper.query.filter_by(user_id=current_user.id).order_by(ResearchPaper.date_created.desc()).all()
    return render_template('dashboard.html', name=current_user.username, history=history)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files.get('file')
    if not file: return jsonify({"error": "No file"}), 400
    if not os.path.exists(app.config['UPLOAD_FOLDER']): os.makedirs(app.config['UPLOAD_FOLDER'])
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    try:
        text = extract_text(filepath)
        result = local_analyze(text)
        new_paper = ResearchPaper(filename=file.filename, summary=result['summary'], user_id=current_user.id)
        db.session.add(new_paper)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/download/<int:paper_id>')
@login_required
def download_summary(paper_id):
    paper = ResearchPaper.query.get_or_404(paper_id)
    if paper.user_id != current_user.id: return "Unauthorized", 403
    buffer = io.BytesIO()
    content = f"SUMMaRIX AI - RESEARCH SUMMARY\nFile: {paper.filename}\n\n{paper.summary}"
    buffer.write(content.encode())
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"summary_{paper.filename}.txt", mimetype='text/plain')

@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    try:
        ResearchPaper.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/chat_query', methods=['POST'])
@login_required
def chat_query():
    data = request.json
    paper = ResearchPaper.query.get(data.get('paper_id'))
    full_text = extract_text(os.path.join(app.config['UPLOAD_FOLDER'], paper.filename))
    answer = ask_neural_query(data.get('question'), full_text[:2000])
    return jsonify({"answer": answer})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)