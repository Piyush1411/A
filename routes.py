# user_auth.py
from flask import render_template, request, redirect, url_for, flash, session
from main import app
from models import db, User, Section, Book, Issue, Return, Cart, Payment, Transaction, Order
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
    return redirect(url_for('user_dash'))

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
    for section in sections:
       print(section.books)
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

@app.route('/category/<int:id>/')
@admin_required
def show_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Sectiondoes not exist')
        return redirect(url_for('admin_dash'))
    return render_template('section/show.html', section=section)


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
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin_dash'))

    name = request.form.get('name')
    date_created_str = request.form.get('date_created')
    description = request.form.get('description')

    if not name or not date_created_str or not description:
        flash('Please fill all the fields')
        return redirect(url_for('edit_section', id=id))

    try:
        date_created = datetime.strptime(date_created_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format')
        return redirect(url_for('edit_section', id=id))

    section.name = name
    section.date_created = date_created
    section.description = description
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

@app.route('/book/add/<int:section_id>')
@admin_required
def add_book(section_id):
    sections = Section.query.all()
    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('librarian_dash'))
    now = datetime.now().strftime('%Y-%m-%d')
    return render_template('books/add.html', section=section, sections=sections, now=now)

@app.route('/book/add/', methods=['POST'])
@admin_required
def add_book_post():
    name = request.form.get('name')
    content = request.form.get('content')
    author = request.form.get('author')
    price = request.form.get('price')
    section_id = request.form.get('section_id')
    
    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin_dash'))

    if not name or not content or not author or not price:
        flash('Please fill out all fields')
        return redirect(url_for('add_book', section_id=section_id))
    try:
        price = float(price)
        
    except ValueError:
        flash('Invalid price')
        return redirect(url_for('add_book', section_id=section_id))

    if price <= 0:
        flash('Invalid price')
        return redirect(url_for('add_book', section_id=section_id))
    
    book = Book(name=name, content=content, author=author, price=price, section=section)
    db.session.add(book)
    db.session.commit()

    flash('Product added successfully')
    return redirect(url_for('show_section', id=section_id))

@app.route('/book/<int:id>/edit')
def edit_book(id):
    sections = Section.query.all()
    book = Book.query.get(id)
    return render_template('books/edit.html', sections=sections, book = book)

@app.route('/book/<int:id>/edit', methods=['POST'])
def edit_book_post(id):
    name = request.form.get('name')
    content = request.form.get('content')
    author = request.form.get('author')
    price = request.form.get('price')
    section_id = request.form.get('section_id')

    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin_dash'))

    if not name or not content or not author or not price:
        flash('Please fill out all fields')
        return redirect(url_for('add_book', section_id=section_id))
    try:
        price = float(price)
    except ValueError:
        flash('Invalid price')
        return redirect(url_for('add_book', section_id=section_id))

    if price <= 0:
        flash('Invalid price')
        return redirect(url_for('add_book', section_id=section_id))
    
    book = Book.query.get(id)
    book.name = name
    book.content = content
    book.author = author
    book.price = price
    book.section_id = section_id
    db.session.commit()

    flash('Book edited successfully')
    return redirect(url_for('show_section', id=section_id))


@app.route('/book/<int:id>/delete')
def delete_book(id):
    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin_dash'))
    return render_template('books/delete.html', book=book)

@app.route('/book/<int:id>/delete', methods=['POST'])
@admin_required
def delete_book_post(id):
    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin_dash'))
    section_id = book.section.id
    db.session.delete(book)
    db.session.commit()

    flash('Book deleted successfully')
    return redirect(url_for('show_section', id=section_id))

# --- user pages

@app.route('/user_dash')
@auth_required
def user_dash():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin_dash'))
    
    sections = Section.query.all()

    sname = request.args.get('sname') or ''
    bname = request.args.get('bname') or ''
    price = request.args.get('price')
    
    if price:
        try:
            price = float(price)
        except ValueError:
            flash('Invalid Price')
            return redirect(url_for('user_dash'))
        if price <= 0:
            flash('Invalid Price')
            return redirect(url_for('user_dash'))
    
    #parameter = request.args.get('parameter')
    #query = request.args.get('query')
    
    ##parameters = {'cname': 'Category Name','pname': 'Product Name','price': 'Max Price'}

    ##if parameter == 'cname':
        #categories = Category.query.filter(Category.name.ilike(f'%{query}%')).all()
        #return render_template('user_dash.html', categories=categories, query=query, parameters=parameters)
    ##elif parameter == 'pname':
        #return render_template('user_dash.html', categories=categories, param=parameter, pname=query, parameters=parameters, query=query)
    ##elif parameter == 'price':
        #query = float(query)
        #return render_template('user_dash.html', categories=categories, param=parameter, price=query, parameters=parameters, query=query)
    
    if sname:
        sectionss = Section.query.filter(Section.name.ilike(f'%{sname}%')).all()
    
    return render_template('user/user_dash.html', sections=sections, sname=sname, bname=bname,price=price)#, parameters=parameters)

@app.route('/add_to_cart/<int:book_id>', methods = ['POST'])
@auth_required
def add_to_cart(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('user_dash'))
    quantity = request.form.get('quantity')
    try:
        quantity = int(quantity)
    except ValueError:
        flash('Invalid quantity')
        return redirect(url_for('user_dash'))
    if quantity <= 0 or quantity > 5:
        flash(f'Invalid quantity, should be between 1 and 6')
        return redirect(url_for('user_dash'))
    
    cart = Cart.query.filter_by(user_id=session['user_id'], book_id=book_id).first()

    if cart:
        if quantity + cart.quantity > 5:
            flash(f'Invalid quantity, should be between 1 and 6')
            return redirect(url_for('user_dash'))
        cart.quantity += quantity
    else:
        cart = Cart(user_id=session['user_id'], book_id=book_id, quantity=quantity)
        db.session.add(cart)
    
    db.session.commit()

    flash('Product added to cart succesfully')
    return redirect(url_for('user_dash'))

@app.route('/cart')
@auth_required
def cart():
    carts = Cart.query.filter_by(user_id=session['user_id']).all()
    total = sum([cart.book.price * cart.quantity for cart in carts])
    return render_template('user/cart.html', carts=carts, total=total)

@app.route('/cart/<int:id>/delete', methods=['POST'])
@auth_required
def delete_cart(id):
    cart = Cart.query.get(id)
    if not cart:
        flash('Cart does not exist')
        return redirect(url_for('cart'))
    if cart.user_id != session['user_id']:
        flash('You are not authorized to access this page')
        return redirect(url_for('cart'))
    db.session.delete(cart)
    db.session.commit()
    flash('Cart deleted successfully')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
@auth_required
def checkout():
    carts = Cart.query.filter_by(user_id=session['user_id']).all()
    if not carts:
        flash('Cart is empty')
        return redirect(url_for('cart'))

    transaction = Transaction(user_id=session['user_id'], datetime=datetime.now())
    for cart in carts:
        order = Order(transaction=transaction, book=cart.book, quantity=cart.quantity, price=cart.book.price)
        db.session.add(order)
        db.session.delete(cart)
    db.session.add(transaction)
    db.session.commit()

    flash('Welcome to Payment site')
    return redirect(url_for('payments'))

@app.route('/payments')
@auth_required
def payments():
    transaction = Transaction(user_id=session['user_id'], datetime=datetime.now())
    if not transaction:
        flash('Transaction not found')
        return redirect(url_for('cart'))
    total = sum([order.price * order.quantity for order in transaction.orders])
    GST = total * 0.18
    amount_payable = total + GST
    payment = Payment(user_id=session['user_id'], transaction=transaction, amount_payable=amount_payable, status='success', datetime=datetime.now())
    db.session.add(payment)
    db.session.commit()
    if not payment:
        flash('Payment not found')
        return redirect(url_for('cart'))

    return render_template('payments.html', payment=payment, total=total, GST=GST, amount_payable=amount_payable)

@app.route('/payments/<int:id>', methods=['POST'])
@auth_required
def payments_post(id):
    payment = Payment.query.get(id)
    if not payment:
        flash('Payment not found')
        return redirect(url_for('cart'))

    flash('Payment successful')
    return redirect(url_for('orders'))

@app.route('/orders')
@auth_required
def orders(payment_id):
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.datetime.desc()).all()
    return render_template('user/orders.html', transactions=transactions)
