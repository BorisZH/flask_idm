from idm import app, db_session, mail_sender
from flask import request, jsonify, make_response, session
from utils.auth import authenticate, login_required, make_sha256
import flask_login
from uuid import uuid1, uuid4
import json



@app.route('/login', methods={'POST'})
def login():
    from idm.role_model import User
    user = db_session.query(User).filter(User.login == request.json.get('login')).first()
    if user is not None:
        if user.password == make_sha256(request.json.get('pwd')):
            return jsonify({
                'id': user.id,
                'login': user.login, 
                'permissions': list(user.permissions),
                'organisation_id': user.organisation_id,
                'unit_id': user.unit_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'is_activated': user.is_activated,
                })
        else:
            return make_response('wrong login or password', 400)
    else:
        return make_response('User with id "{}" not found'.format( request.json.get('login')), 404)
    

@app.route('/users', methods={'GET'})
# @login_required()
def get_users_list():
    from idm.role_model import User
    org_id = request.args.get('organisation_id')
    term = User.organisation_id==org_id if org_id is not None else True
    data = [
        {
            'user_id': u.id,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'login': u.login,
            'is_activated': u.is_activated,
        } for u in db_session.query(User).filter(
            term
            ).all() if u.login != 'system']
    return jsonify(data)


@app.route('/users/<string:user_id>/', methods={'GET'})
# @login_required()
def user(user_id):
    from idm.role_model import User
    user = db_session.query(User).filter(User.id == user_id).first()
    if user is not None:
        return jsonify({
            'id': user.id,
            'login': user.login, 
            'permissions': list(user.permissions),
            'organisation_id': user.organisation_id,
            'unit_id': user.unit_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_activated': user.is_activated
            })
    else:
        return make_response('User with id "{}" not found'.format(user_id), 404)
 


# @app.route('/logout', methods=['GET'])
# @login_required()
# def logout():
#     flask_login.logout_user()
#     if session.get('was_once_logged_in'):
#         # prevent flashing automatically logged out message
#         del session['was_once_logged_in']
#     return jsonify({})


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


@app.route('/organisations/<string:org_id>/units', methods=['GET'])
# @login_required('organisation_admin')
def get_units(org_id):
    from idm.role_model import Unit

    units = db_session.query(Unit).filter(Unit.organisation_id == org_id).all()
    units = [] if units is None else units
    data = [{
        'id': u.id,
        'name': u.name,
    } for u in units]
    return jsonify(data)


@app.route('/organisations/<string:org_id>/units', methods=['POST'])
# @login_required(['create_unit', 'organisation_admin'])
def create_unit(org_id):
    from idm.role_model import Unit
    unit_id = str(uuid4())
    unit = Unit(
        id=unit_id, 
        name=request.json['name'], 
        organisation_id=org_id,
    )
    db_session.add(unit)
    db_session.commit()
    return jsonify({'id': unit_id})


@app.route('/organisations', methods=['GET'])
# @login_required('god_mode')
def get_organisations():
    from idm.role_model import Organisation

    orgs = db_session.query(Organisation).all()
    orgs = [] if orgs is None else orgs
    data = [{
        'id': o.id,
        'name': o.name,
        'organisation_type': o.organisation_type.org_type,
        'organisation_type_id': o.organisation_type_id,
    } for o in orgs]
    return jsonify(data)


@app.route('/organisations', methods=['POST'])
# @login_required('god_mode')
def create_organisation():
    from idm.role_model import Organisation
    org_id = str(uuid4())
    org = Organisation(
        id=org_id, 
        name=request.json['name'], 
        organisation_type_id=request.json['organisation_type_id'],
    )
    db_session.add(org)
    db_session.commit()
    return jsonify({'id': org_id})


@app.route('/organisation_types', methods=['GET'])
def org_types():
    from idm.role_model import OrganisationType

    orgs = db_session.query(OrganisationType).all()
    orgs = [] if orgs is None else orgs
    data = [{
        'id': o.id,
        'org_type': o.org_type,
    } for o in orgs]
    return jsonify(data)
