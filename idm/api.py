from idm import app, db_session, mail_sender
from flask import request, jsonify, make_response, session
from utils.auth import authenticate, login_required, make_sha256
import flask_login
from uuid import uuid1, uuid4
import json



@app.route('/login', methods={'POST'})
def login():
    if authenticate(request):
        return jsonify({'state': 'success'})
    else:
        return make_response({'state': 'wrong login or password'}, 400)


@app.route('/users', methods={'GET'})
@login_required()
def get_users_list():
    from idm.role_model import User
    data = [
        {
            'user_id': u.id,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'login': u.login,
        } for u in db_session.query(User).filter(
            User.organisation_id==flask_login.current_user.organisation_id
            ).all() if u.login != 'system']
    return jsonify(data)


@app.route('/users/me', methods={'GET'})
@login_required()
def user():
    return jsonify({'login': flask_login.current_user.login, 'permissions': list(flask_login.current_user.permissions)})


@app.route('/logout', methods=['GET'])
@login_required()
def logout():
    flask_login.logout_user()
    if session.get('was_once_logged_in'):
        # prevent flashing automatically logged out message
        del session['was_once_logged_in']
    return jsonify({})


@app.route('/users', methods=['POST'])
def create_new_user():
    from idm.role_model import User, UserAssignment
    jsn = request.json
    id_ = str(uuid4())
    ua = UserAssignment(
        id=id_,
    )
    db_session.add(ua)
    u = User(
        id=id_,
        unit_id = jsn['unit_id'],
        organisation_id = jsn['org_ig'],
        user_assignment_id = id_,
        login = jsn['login'],
        password = make_sha256(jsn['pwd']),
        email = jsn['email'],
        first_name = jsn['f_name'],
        last_name = jsn['l_name'],
        activation_str = str(uuid1()),
    )
    db_session.add(u)
   
    resp = send_activation(id_)
    db_session.commit()
    return resp


@app.route('/users/<string:user_id>/send_activation', methods=['GET'])
def send_activation(user_id):
    from idm.role_model import User
    user = db_session.query(User).filter(User.id == user_id).first()
    if user is not None:
        if user.is_activated:
            return make_response('User is already activated', 400)
        else:
            conf = json.load(open('./configs/send_mail.json', 'r'))
            text = conf['ACTIVATION_MESSAGE'].format(user.login, user.activation_str)
            mail_sender.send_mail(
                to_addrs=[user.email],
                subject= conf['ACTIVATION_MESSAGE_SUBJECT'],
                msg_text=text,
                use_sign=False,
            )
            return make_response('ok', 200)
    else:
        return make_response('User with id "{}" not found'.format(user_id), 404)


@app.route('/users/activate', methods=['GET'])
def activate_user():
    from idm.role_model import User
    login = request.args['user_login']
    key = request.args['key']
    user = db_session.query(User).filter(User.login == login).first()
    if user is not None:
        if user.activation_str == key:
            if not user.is_activated:
                user.is_activated = True
                db_session.add(user)
                db_session.commit()
                return make_response('ok', 200)
            else:
                return make_response('User is already activated', 409)
        else:
            return make_response('Wrong activation key', 400)
    else:
        return make_response('User "{}" not found'.format(login), 404)
