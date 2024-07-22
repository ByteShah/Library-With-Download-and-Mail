from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
user_bp = Blueprint('user', __name__)
book_search_bp = Blueprint('book_search', __name__)

from .auth import *
from .user import *
from .book import book_search_bp