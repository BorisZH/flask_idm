from sqlalchemy import Column, Integer, Boolean, String, Date, DateTime, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime


Base = declarative_base()


role_permission = Table('roles_permissions', Base.metadata,
                        Column('permission_id', String, ForeignKey('permissions.id')),
                        Column('role_id', String, ForeignKey('roles.id'))
                        )


removed_permission_user_assign = Table('removed_permissions_user_asg', Base.metadata,
                                       Column('user_assignment_id', String, ForeignKey('user_assignment.id')),
                                       Column('permission_id', String, ForeignKey('permissions.id'))
                                      )


personal_permission_user_assign = Table('personal_permissions_user_asg', Base.metadata,
                                        Column('user_assignment_id', String, ForeignKey('user_assignment.id')),
                                        Column('permission_id', String, ForeignKey('permissions.id'))
                                       ) 


permissions_org_types = Table('permissions_orgtypes', Base.metadata,
                              Column('org_type_id', String, ForeignKey('organisation_types.id')),
                              Column('permission_id', String, ForeignKey('permissions.id'))
                             ) 


roles_user_assignment = Table('roles_user_assign', Base.metadata,
                              Column('role_id', String, ForeignKey('roles.id')), 
                              Column('user_assign_id', String, ForeignKey('user_assignment.id'))
                             )


class Permission(Base):
    __tablename__ = 'permissions'
    
    id = Column(String, primary_key=True)
    
    name = Column(String, unique=True)
    description = Column(String)
    roles = relationship('Role', 
                         secondary=role_permission, 
                         back_populates='included_permissions')
    removed_user_asg = relationship('UserAssignment', 
                                                secondary=removed_permission_user_assign, 
                                                back_populates='removed_permissions')
    personal_user_asg = relationship('UserAssignment', 
                                                 secondary=personal_permission_user_assign, 
                                                 back_populates='personal_permissions')
    organisation_types = relationship('OrganisationType',
                                      secondary=permissions_org_types,
                                      back_populates='avaliable_permissions'
                                     )


class Role(Base):
    __tablename__ = 'roles'

    id = Column(String, primary_key=True)
    organisation_id = Column(String, ForeignKey('organisations.id'))

    included_permissions = relationship('Permission', 
                            secondary=role_permission, 
                            back_populates='roles')
    organisation = relationship('Organisation', back_populates='roles')
    user_assignments = relationship('UserAssignment',
                                    secondary=roles_user_assignment,
                                    back_populates='roles'
                                    )
    

class Organisation(Base):
    __tablename__  = 'organisations'
    id = Column(String, primary_key=True)
    name = Column(String)
    organisation_type_id = Column(String, ForeignKey('organisation_types.id'))

    organisation_type = relationship('OrganisationType', back_populates='organisations')
    units = relationship('Unit', back_populates='organisation')
    roles = relationship('Role', back_populates='organisation') #роли, созданные конкретной организацией
    users = relationship('User', back_populates='organisation')


class OrganisationType(Base):
    __tablename__ = 'organisation_types'
    id = Column(String, primary_key=True)

    org_type = Column(String)

    organisations = relationship('Organisation', back_populates='organisation_type')
    avaliable_permissions = relationship('Permission', 
                               secondary=permissions_org_types, 
                               back_populates='organisation_types',
                              )


class Unit(Base):
    __tablename__ = 'units'

    id = Column(String, primary_key=True)
    organisation_id = Column(String, ForeignKey('organisations.id'))
    name = Column(String)

    organisation = relationship('Organisation', back_populates='units')
    users = relationship('User', back_populates='unit')


class UserAssignment(Base):
    __tablename__ = 'user_assignment'

    id = Column(String, primary_key=True)

    user = relationship('User', back_populates='user_assignment')
    roles = relationship('Role', 
                         secondary=roles_user_assignment,
                         back_populates='user_assignments'
                        )
    removed_permissions = relationship('Permission', 
                                       secondary=removed_permission_user_assign, 
                                       back_populates='removed_user_asg')
    personal_permissions = relationship('Permission', 
                                       secondary=personal_permission_user_assign, 
                                       back_populates='personal_user_asg')
    

class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True)
    unit_id = Column(String, ForeignKey('units.id'))
    organisation_id = Column(String, ForeignKey('organisations.id'))
    user_assignment_id = Column(String, ForeignKey('user_assignment.id'))
    login = Column(String)
    password = Column(String)
    email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    activation_str = Column(String)
    is_activated = Column(Boolean, default=False)

    organisation = relationship('Organisation', back_populates='users')
    unit = relationship('Unit', back_populates='users')
    user_assignment = relationship('UserAssignment', back_populates='user')

    def __init__(self, id, login, password, first_name, last_name, **kwargs):
        super().__init__(**kwargs)
        self.id = id
        self.login = login
        self.password = password
        self.first_name = first_name
        self.last_name = last_name

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.is_activated

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
    
    @property
    def god_mode(self):
        return 'god_mode' in self.permissions

    @property
    def permissions(self):
        permissions = [i.name for i in self.user_assignment.personal_permissions]
        for r in self.user_assignment.roles:
            permissions.extend([i.name for i in r.included_permissions])
        removed = [i.name for i in self.user_assignment.removed_permissions]
        return set(permissions).difference(set(removed))
        


