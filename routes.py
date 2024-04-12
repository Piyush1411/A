# user_auth.py
from flask import render_template, request, redirect, url_for, flash, session
from main import app
from models import db, User, Section, Book, Cart, Payment, Transaction, Order
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timedelta
import csv
import os
from uuid import uuid4

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('user/user.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('userName')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash('Username does not exist')
        return redirect(url_for('login'))
    
    if not check_password_hash(user.passhash, password):
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    session['user_id'] = user.id
    flash('Login successful')
    return redirect(url_for('profile'))

@app.route('/register')
def register():
    return render_template('user/user.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('email')
    username = request.form.get('userName')
    name = request.form.get('fullName')
    password = request.form.get('password1')
    confirm_password = request.form.get('password2')
    

    if not username or not password or not confirm_password:
        flash('Please fill out all fields')
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('register'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('register'))
    
    password_hash = generate_password_hash(password)
    
    new_user = User(username=username, passhash=password_hash, name=name)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

# decorator for auth_required

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('login'))
    return inner

# decorator for admin_required
def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You are not authorized to access this page')
            return redirect(url_for('home'))
        return func(*args, **kwargs)
    return inner

@app.route('/profile')
@auth_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('user/profile.html', user=user)

@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    username = request.form.get('userName')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('fullName')

    if not username or not cpassword or not password:
        flash('Please fill out all the required fields')
        return redirect(url_for('profile'))
    
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('profile'))
    
    if username != user.username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('profile'))
    
    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))

@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('index'))

 #--- admin pages
@app.route('/admin_login')
def admin_login():
    return render_template('librarian/librarian.html')

@app.route('/admin_login', methods=['POST'])
def admin_login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('admin_login'))
    
    user = User.query.filter_by(username=username).first()
    
    if not user:
        flash('Username does not exist')
        return redirect(url_for('admin_login'))
    
    if not check_password_hash(user.passhash, password):
        flash('Incorrect password')
        return redirect(url_for('admin_login'))
    
    session['user_id'] = user.id
    flash('Login successful')
    return redirect(url_for('admin_dash'))

@app.route('/admin_dash')
@admin_required
def admin_dash():
    sections = Section.query.all()
    section_names = [section.name for section in sections]
    section_sizes = [len(section.books) for section in sections]
    return render_template('librarian/librarian_dash.html', sections=sections, section_names=section_names, section_sizes=section_sizes)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

@app.route('/upload', methods=['POST'])
@admin_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File uploaded successfully')
        return redirect(url_for('upload_file'))

    flash('Invalid file type.')
    return redirect(request.url)

@app.route('/section/add')
@admin_required
def add_section():
    return render_template('section/add.html')

@app.route('/section/add', methods=['POST'])
@admin_required
def add_section_post():
    name = request.form.get('name')
    date_created = datetime.now()
    description = request.form.get('description')

    if not name or not description:
        flash('Please fill out all fields')
        return redirect(url_for('add_section_form'))

    section = Section(name=name, date_created=date_created, description=description)
    db.session.add(section)
    db.session.commit()

    flash('Section added successfully')
    return redirect(url_for('admin_dash'))


@app.route('/section/<int:id>/edit')
@admin_required
def edit_section(id):
    section=Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin_dash'))
    return render_template('section/edit.html', section=section)

@app.route('/section/<int:id>/edit', methods=['POST'])
@admin_required
def edit_section_post(id):
    section=Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin_dash'))
    name = request.form.get('name')
    date_created = request.form.get('date_created')
    description = request.form.get('description')
    if not name or not date_created or not description:
        flash('Please fill all the fields')
        return redirect(url_for('edit_section', id=id))
    section.name=name
    section.date_created=date_created
    section.description=description
    db.session.commit()
    flash('Section updated successfully')
    return redirect(url_for('admin_dash'))

@app.route('/section/<int:id>/delete')
@admin_required
def delete_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin_dash'))
    return render_template('section/delete.html', section=section)

@app.route('/section/<int:id>/delete', methods=['POST'])
@admin_required
def delete_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin_dash'))
    db.session.delete(section)
    db.session.commit()

    flash('Section deleted successfully')
    return redirect(url_for('admin_dash'))

