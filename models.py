from database import Base, engine, db_session
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import insert


class Questions(Base):
    __tablename__ = 'questions'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(64), unique=True, index=True, comment='问卷标题')
    survey_number = Column(Integer, default=0, comment='调研人数')
    completed_number = Column(Integer, default=0, comment='完成人数')
    users = Column(String(128), comment='参与调查人员')
    content = Column(JSON, comment='问卷内容')
    status = Column(Boolean, default=False)
    start_at = Column(DateTime, comment='问卷开始时间')
    end_at = Column(DateTime, comment='问卷结束时间')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def save(self):
        if self.id is None:
            db_session.add(self)
        return db_session.commit()

    def destroy(self):
        db_session.delete(self)
        return db_session.commit()


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, comment='用户名')
    password = Column(String(255), nullable=False, comment='密码')
    name = Column(String(64), comment='姓名')
    address = Column(String(64), comment='地址')
    telephone = Column(String(64), comment='电话')
    questions = Column(String(64), comment='调研问卷')
    token = Column(String(128), comment='Token', default='')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def save(self):
        data = self.to_json()
        del data['id']
        del data['created_at']
        del data['updated_at']
        data['password'] = generate_password_hash(str(self.password))
        db_session.execute(insert(Users).values(data).on_duplicate_key_update(**data))
        return db_session.commit()

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def destroy(self):
        db_session.delete(self)
        return db_session.commit()


if __name__ == '__main__':
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
