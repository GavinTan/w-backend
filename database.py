from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime

db_user = 'root'
db_pass = 'abcu123456'
db_host = '192.168.8.192'
db_name = 'xx'
engine = create_engine(f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}', convert_unicode=True)
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

    # return dumps([json])
    return json


def to_json_list(model_list):
    json_list = []
    for model in model_list:
        json_list.append(to_json(model))
    return json_list
