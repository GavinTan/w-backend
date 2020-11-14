from flask import Flask, request
from flask_restful import reqparse, Api
from flask.views import MethodView
from flask import jsonify
from database import to_json, to_json_list, db_session
from werkzeug.datastructures import FileStorage
from flask import send_file, send_from_directory
from flask_cors import CORS
from models import Users, Questions
from pandas import ExcelFile
import logging
import os


app = Flask(__name__)
api = Api(app, catch_all_404s=True)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

# log = logging.getLogger(__file__)
# handler = logging.FileHandler('server.log')
# app.logger.addHandler(handler)
# app.logger.setLevel(logging.INFO)

PROJECT_HOME = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = f'{PROJECT_HOME}/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def create_new_folder(local_dir):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    return local_dir


class Index(MethodView):
    def get(self, id):
        data = {}
        return {'code': 200, 'data': data}


class QuestionManage(MethodView):
    def get(self):
        data = to_json_list(Questions.query.all())
        return {'code': 200, 'data': data}

    def post(self):
        data = {}
        parser = reqparse.RequestParser()
        parser.add_argument('a', type=str)
        args = parser.parse_args()
        question_data = request.get_json()
        q = Questions.query.filter_by(title=question_data.get('title')).first()
        if q:
            Questions.query.filter_by(title=question_data.get('title')).update(content=question_data.get('contentList')).save()
        else:
            Questions(title=question_data.get('title'),
                      content=question_data.get('contentList'),
                      start_at=question_data.get('surveyTime')[0],
                      end_at=question_data.get('surveyTime')[1]).save()
        return {'code': 200, 'data': data}

    def delete(self, pk=None):
        # delete a single user
        pass

    def put(self, pk=None):
        data = []
        question_data = request.get_json()
        db_session.query(Questions).filter_by(id=pk).update(question_data)
        db_session.commit()
        return {'code': 200, 'data': data}


class User(MethodView):
    def get(self, pk=None):
        data = to_json_list(Users.query.all())
        if pk:
            data = to_json_list(Users.query.filter_by(id=pk).all())
        return {'code': 200, 'data': data}

    def post(self):
        file_path = app.config['UPLOAD_FOLDER']
        excel = ExcelFile(os.path.join(file_path, request.get_json().get('file')))
        df = excel.parse(excel.sheet_names[0])
        user_data = df.to_dict()
        for k, v in user_data.get('用户名').items():
            u = Users(username=v, password=user_data.get('密码').get(k),
                      address=user_data.get('地址').get(k),
                      name=user_data.get('姓名').get(k),
                      telephone=user_data.get('电话').get(k)
                      )
            u.save()
        data = to_json_list(Users.query.all())
        return {'code': 200, 'data': data}


class Upload(MethodView):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=FileStorage, location='files')
        args = parser.parse_args()
        file = args['file']
        create_new_folder(app.config['UPLOAD_FOLDER'])
        saved_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(saved_path)
        return file.filename, 201


class Download(MethodView):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=str)
        parser.add_argument('dir', type=str)
        args = parser.parse_args()
        return send_from_directory(args.get('dir') or os.getcwd(), args.get('file'), as_attachment=True)


class Logout(MethodView):
    def post(self):
        data = {'code': 200, 'data': 'success'}
        return data


def register_api(view, endpoint, url, pk='id', pk_type='int'):
    view_func = view.as_view(endpoint)
    app.add_url_rule(url, defaults={pk: None},
                     view_func=view_func, methods=['GET',])
    app.add_url_rule(url, view_func=view_func, methods=['POST',])
    app.add_url_rule('%s<%s:%s>' % (url, pk_type, pk), view_func=view_func,
                     methods=['GET', 'PUT', 'DELETE'])


api.add_resource(Index, "/api")
api.add_resource(Upload, '/upload')
api.add_resource(Download, '/download')
api.add_resource(Logout, '/logout')
api.add_resource(User, '/user', endpoint='user')
api.add_resource(User, '/user/<int:pk>', endpoint='users')
api.add_resource(QuestionManage, "/question", endpoint='question')
api.add_resource(QuestionManage, "/question/<int:pk>", endpoint='questions')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)
