import os
from os.path import join, dirname

from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


class Config(object):
    BASE_DIR = dirname(__file__)
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    PAGE_LIMIT = 10
    DEFAULT_PAGE = 1
    SECRET_KEY = 'thisisthesecretkey'

app_configuration = {
    'development': Config,
}