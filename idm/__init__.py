"""
The flask application package.
"""
from flask import Flask
from sqlalchemy import create_engine
from utils.auth import login_manager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.mail_sender import MailSender
app = Flask(__name__)
login_manager.init_app(app=app)
engine = create_engine('sqlite:///idm.db?check_same_thread=False')
 

sm = sessionmaker(bind=engine)
db_session = sm()
mail_sender = MailSender('./configs/send_mail.json')


import idm.api
