import flask_login
from functools import wraps
from flask_login import LoginManager, login_user
from flask import make_response
import hashlib


def make_sha256(inp_str, salt='qsmkcdo'):
    return hashlib.sha256((inp_str + salt).encode()).hexdigest()


login_manager = LoginManager()


def login_required(permissions=None):
    def wrapper(func):
        @wraps(func)
        def decorated_view(permissions=permissions, *args, **kwargs):            
            permissions = [permissions] if isinstance(permissions, str) else permissions
            permissions = permissions if permissions is not None else []
            if not flask_login.current_user.is_authenticated:
                return login_manager.unauthorized()
            if not user.is_activated:
                return make_response('User is not activated', 401)
            if not (flask_login.current_user.permissions.issubset(set(permissions)) or 'god_mode' in flask_login.current_user.permissions):
                return make_response('User has not permissions', 403)
            return func(*args, **kwargs)
        return decorated_view
    return wrapper


@login_manager.user_loader
def user_loader(id):
    from idm import db_session
    from idm.role_model import User
    return db_session.query(User).filter(User.id == id).one()


def authenticate(req):
    from idm.role_model import User
    from idm import db_session
    login = req.json.get('login')
    pwd = make_sha256(req.json.get('pwd', ''))
    
    remember = req.json.get('remeber_me')
    
    user = db_session.query(User).filter(User.login == login).first() if login else None

    if user is not None and user.password == pwd:
        return login_user(user, remember)
    return False



