from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import insert
import datetime
import os

db_user = os.environ.get("W_DB_USER") or 'root'
db_pass = os.environ.get("W_DB_PASSWORD") or 'abcu123456'
db_host = os.environ.get("W_DB_HOST") or '127.0.0.1'
db_name = os.environ.get("W_DB_NAME") or 'w'
engine = create_engine(f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}', convert_unicode=True, pool_size=0, max_overflow=-1)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def to_json(model):
    """ Returns a JSON representation of an SQLAlchemy-backed object. """
    json = {}
    # json['fields'] = {}
    # json['pk'] = getattr(model, 'id')
    for col in model._sa_class_manager.mapper.mapped_table.columns:
        # json['fields'][col.name] = getattr(model, col.name)
        if isinstance(getattr(model, col.name), datetime.datetime):
            json[col.name] = getattr(model, col.name).strftime('%Y-%m-%d %H:%M:%S')
        else:
            json[col.name] = getattr(model, col.name)
        if col.name == 'roles':
            if getattr(model, col.name):
                json[col.name] = getattr(model, col.name).split(',')
            else:
                json[col.name] = ['']

    # return dumps([json])
    return json


def to_json_list(model_list):
    json_list = []
    for model in model_list:
        json_list.append(to_json(model))
    return json_list
