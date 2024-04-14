#models.py
from main import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    passhash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    payment = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')
    issue_date = db.relationship('Issue', backref='user', lazy=True, cascade='all, delete-orphan')
#class Upload(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#   name = db.Column(db.String(32), unique=True)
    

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    date_created = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(2048), nullable=False)
    books = db.relationship('Book', backref='section', lazy=True, cascade='all, delete-orphan')

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    content = db.Column(db.String(2048), nullable=False)
    author = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    #upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'))
    #uploads = db.relationship('Upload', backref='book', lazy=True, cascade='all, delete-orphan')
    carts = db.relationship('Cart', backref='book', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='book', lazy=True, cascade='all, delete-orphan')
    
class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    issue = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    amount_payable = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    payment = db.relationship('Payment', backref='transaction', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='transaction', lazy=True, cascade='all, delete-orphan')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    issue_date = db.relationship('Issue', backref='orders', lazy=True, cascade='all, delete-orphan')

with app.app_context():
    db.create_all()
    # if admin exists, else create admin
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        password_hash = generate_password_hash('admin')
        admin = User(username='librarian', passhash=password_hash, name='Librarian', is_admin=True)
        db.session.add(admin)
        db.session.commit()
