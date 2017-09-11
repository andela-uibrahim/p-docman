import json
import os
import bcrypt
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, Text
from sqlalchemy.types import TypeDecorator, TEXT, JSON
from sqlalchemy.exc import SQLAlchemyError

def to_camel_case(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + "".join(x.title() for x in components[1:])

db = SQLAlchemy()

class ModelOpsMixin(object):
    """
    Contains the serialize method to convert objects to a dictionary
    """

    def serialize(self):
        return {to_camel_case(column.name): getattr(self, column.name)
                for column in self.__table__.columns
                if column.name not in ['contribution_type_id']}

    def save(self):
        """Saves an instance of the model to the database"""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False

class User(db.Model, ModelOpsMixin):
    __tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True,  nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    email = db.Column(db.String(80), unique=True,  nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(80), default="regular")
    documents = db.relationship( 'Document', backref='user', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    
    def __repr__(self):
        return '<ContributionType %r>' % self.username
    
    def verify_password(self, password):
        pwhash = bcrypt.hashpw(password, self.password)
        return self.password == pwhash

class Document(db.Model, ModelOpsMixin):
    __tablename__ = "Document"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    content = db.Column(TEXT,  nullable=False)
    access = db.Column(db.String(80), default='public')
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('User.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return '<Document %r>' % self.title