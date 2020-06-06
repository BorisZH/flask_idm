from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.auth import make_sha256
from sqlalchemy import MetaData
from sqlalchemy_schemadisplay import create_schema_graph 
from uuid import uuid4
import os
import json


def init_config():
    cfg_path = './configs'
    flask_cfg = 'config.py'
    mail_sender_cfg = 'send_mail.json'
    os.makedirs(cfg_path, exist_ok=True)
    if not os.path.exists(os.path.join(cfg_path, flask_cfg)):
        with open(os.path.join(cfg_path, flask_cfg), 'w+') as f:
            f.write('SECRET_KEY = \'{}\''.format(input('Enter secret key: ')))
    if not os.path.exists(os.path.join(cfg_path, mail_sender_cfg)):
        with open(os.path.join(cfg_path, mail_sender_cfg), 'w+') as f:
            data = {
                "SMTP_HOST": input('Enter smtp host: '),
                "SMTP_PORT": int(input('Enter smtp port: ')),
                "MAIL_USER": input('Enter mail username: '),
                "MAIL_PWD": input('Enter mail password: '),
                "SENDER": input('Enter mail sender: '),
                "ACTIVATION_MESSAGE": input('Enter activation message: '),
                "ACTIVATION_MESSAGE_SUBJECT": input('Enter activation message subject: '),
            }
            json.dump(data, f)
    

def create_db(inp_args):
    from idm.role_model import Permission, personal_permission_user_assign, UserAssignment, User, Base, Organisation, OrganisationType

    engine = create_engine('sqlite:///idm.db')
    session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    s = session()   

    permissions = [
        ('god_mode', 'Full access and anarchy'),
        ('create_permission', 'User can create permission'), 
        ('create_role', 'User can create role'), 
        ('set_role', 'User can assign role for other user'), 
        ('set_permission', 'User can assign permission for other user'), 
    ]
    for i, t in enumerate(permissions):
        db_obj = Permission(id=str(uuid4()), name=t[0], description=t[1])
        s.add(db_obj)
    s.commit()

    id_ = str(uuid4())
    ot = OrganisationType(id=id_, org_type='owner')
    o = Organisation(id=str(uuid4()), name='BuzzWords', organisation_type_id=id_)
    s.add(ot)
    s.add(o)

    id_ = str(uuid4())
    ot = OrganisationType(id=id_, org_type='client')
    o = Organisation(id=str(uuid4()), name='Test Organisation', organisation_type_id=id_)
    s.add(ot)
    s.add(o)

    id_ = str(uuid4())
    user_asg = UserAssignment(id=id_)
    s.add(user_asg)
    user = User(
        id=id_, 
        login='system', 
        password=None, 
        first_name='System', 
        last_name='', 
        user_assignment_id=id_,
        is_activated=True,
    )
    s.add(user)
    
    id_ = str(uuid4())
    user_asg = UserAssignment(id=id_)
    s.add(user_asg)
    user = User(
        id=id_, 
        login=inp_args.admin_login, 
        password=make_sha256(inp_args.admin_pwd),
        first_name='admin', 
        last_name='admin', 
        user_assignment_id=id_,
        is_activated=True,
    )
    s.add(user)
    s.commit()

    s.execute(personal_permission_user_assign.insert().values({'user_assignment_id': 0, 'permission_id':0}))
    s.execute(personal_permission_user_assign.insert().values({'user_assignment_id': 1, 'permission_id':0}))

    s.commit()
    s.close()

    if inp_args.save_schema is not None:
        # create the pydot graph object by autoloading all tables via a bound metadata object
        graph = create_schema_graph(metadata=MetaData('sqlite:///idm.db'),
        show_datatypes=False, # The image would get nasty big if we'd show the datatypes
        show_indexes=False, # ditto for indexes
        rankdir='LR', # From left to right (instead of top to bottom)
        concentrate=False # Don't try to join the relation lines together
        )

        graph.write_png(inp_args.save_schema + '.png') # write out the file

if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument(
        '--admin_login', 
        type=str,
        default='admin', 
        #required=True, 
        help='Login for first admin account with god_mode',
        )    
    args.add_argument(
        '--admin_pwd',
         type=str, 
         default='1q2w3e4r5t6y', 
         #required=True,
          help='password for first admin account with god_mode',
          )
    args.add_argument(
        '--save_schema', 
        type=str, 
        default=None, 
        help='file name for schema picture',
        )

    inp_args = args.parse_args()
    init_config()
    create_db(inp_args)
