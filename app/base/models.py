from flask_login import UserMixin
from sqlalchemy import BINARY, Column, Integer, String

from app import db, login_manager
from app.base.util import hash_pass


# 사용자

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    username = Column(String, unique = True)
    email = Column(String, unique = True)
    password = Column(BINARY)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id = id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username = username).first()
    return user if user else None


# 마스터데이터

class ChartOfAccount(db.Model):
    __tablename__ = "chart_of_account"

    account_code = db.Column(db.Integer, primary_key = True)
    account_category = db.Column(db.String(2), nullable = False)
    account_type = db.Column(db.String(2), nullable = False)
    account_group = db.Column(db.Integer, nullable = False)
    account_name = db.Column(db.String(100), unique = True, nullable = False)
    account_description = db.Column(db.Text, nullable = True)


class Product(db.Model):
    __tablename__ = "product"

    product_code = db.Column(db.String(10), primary_key = True)
    product_name = db.Column(db.String(100), nullable = False)
    product_type = db.Column(db.String(2), nullable = False)
    product_vat = db.Column(db.String(2), nullable = False)
    product_cost = db.Column(db.Integer, nullable = False)
    product_price = db.Column(db.Integer, nullable = True)
    product_description = db.Column(db.Text, nullable = True)


class Partner(db.Model):
    __tablename__ = "partner"

    partner_code = db.Column(db.String(10), primary_key = True)
    partner_name = db.Column(db.String(100), nullable = False)
    partner_type = db.Column(db.String(2), nullable = False)
    partner_description = db.Column(db.Text, nullable = True)


class Project(db.Model):
    __tablename__ = "project"

    project_code = db.Column(db.String(10), primary_key = True)
    project_name = db.Column(db.String(100), nullable = False)
    project_description = db.Column(db.Text, nullable = True)


class BankAccount(db.Model):
    __tablename__ = "bank_account"

    bank_account_number = db.Column(db.String(20), primary_key = True)
    bank_account_name = db.Column(db.String(100), nullable = False)
    bank_account_description = db.Column(db.Text, nullable = True)


class Company(db.Model):
    __tablename__ = "company"

    company_code = db.Column(db.String(10), primary_key = True)
    company_name = db.Column(db.String(100), nullable = False)
    company_tax_code = db.Column(db.String(20), nullable = True)
    company_address = db.Column(db.String(500), nullable = True)
    company_tel = db.Column(db.String(20), nullable = True)


# 거래

class Transaction(db.Model):
    __tablename__ = "transaction"

    id = db.Column(db.Integer, primary_key = True)

    document_number = db.Column(db.String(20), db.ForeignKey('journal_entry.document_number'), nullable = False)
    journal_entry = db.relationship('JournalEntry', backref = db.backref('transaction_set'))

    product_code = db.Column(db.String(10), db.ForeignKey('product.product_code'), nullable = True)
    product = db.relationship('Product', backref = db.backref('transaction_set'))

    account_code = db.Column(db.Integer, db.ForeignKey('chart_of_account.account_code'), nullable = False)
    account = db.relationship('ChartOfAccount', backref = db.backref('transaction_set'))

    transaction_quantity = db.Column(db.Integer, nullable = True)
    transaction_amount = db.Column(db.Integer, nullable = False)


# 전표
class JournalEntry(db.Model):
    __tablename__ = "journal_entry"

    document_number = db.Column(db.String(20), primary_key = True)
    document_type = db.Column(db.String(2), nullable = False)
    document_date = db.Column(db.String(10), nullable = False)

    partner_code = db.Column(db.String(10), db.ForeignKey('partner.partner_code'), nullable = True)
    partner = db.relationship('Partner', backref = db.backref('document_set'))

    project_code = db.Column(db.String(10), db.ForeignKey('project.project_code'), nullable = True)
    project = db.relationship('Project', backref = db.backref('document_set'))

    payment_type = db.Column(db.String(2), nullable=True)

    bank_account_number = db.Column(db.String(20), db.ForeignKey('bank_account.bank_account_number'), nullable = True)
    bank_account = db.relationship('BankAccount', backref = db.backref('document_set'))

    document_description = db.Column(db.Text, nullable = True)

    user_name = db.Column(db.String, db.ForeignKey('user.username'), nullable = False)
    user = db.relationship('User', backref = db.backref('document_set'))
