from flask import Flask, request
from flask_restful import reqparse, Api
from flask.views import MethodView
from flask import jsonify
from database import to_json, to_json_list, db_session
from sqlalchemy.dialects.mysql import insert
from werkzeug.datastructures import FileStorage
from flask import send_file, send_from_directory
from flask_cors import CORS
from models import Users, Questions, QuestionResult
from pandas import ExcelFile
import logging
import os
import secrets


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
    def get(self, pk=None):
        parser = reqparse.RequestParser()
        parser.add_argument('a', type=str)
        parser.add_argument('uid', type=str)
        parser.add_argument('title', type=str)
        args = parser.parse_args()

        data = to_json_list(Questions.query.all())
        if args.get('a') == 'getUserQuestion':
            data = to_json_list(Questions.query.filter(Questions.users.contains(args.get('uid'))).all())

        if pk:
            data = to_json(Questions.query.filter_by(id=pk).first())

        if args.get('a') == 'getUserQuestionResult':
            data = []
            table_data = []
            rs_data = to_json(QuestionResult.query.filter_by(user=args.get('uid'), title=args.get('title')).first())
            grades = {
                '1.政府主体-1': {'grades_IV': '领导很重视', 'grades_III': '领导重视', 'grades_II': '领导比较重视', 'grades_I': '领导重视不够'},
                '1.政府主体-2': {'grades_IV': '资金落实很到位', 'grades_III': '资金落实到位', 'grades_II': '资金落实比较到位', 'grades_I': '资金落实不够到位'},
                '1.政府主体-3': {'grades_IV': '检查督办很得力', 'grades_III': '检查督办得力', 'grades_II': '检查督办比较得力', 'grades_I': '检查督办不够得力'},
                '2.相关部门': {'grades_IV': '配合很协调', 'grades_III': '配合协调', 'grades_II': '配合比较协调', 'grades_I': '配合不够协调'},
                '3.主管部门-1': {'grades_IV': '工作很主动', 'grades_III': '工作主动', 'grades_II': '工作比较主动', 'grades_I': '工作不够主动'},
                '3.主管部门-2': {'grades_IV': '落实很具体', 'grades_III': '落实具体', 'grades_II': '落实比较具体', 'grades_I': '落实不够具体'},
                '3.主管部门-3': {'grades_IV': '推进很扎实', 'grades_III': '推进扎实', 'grades_II': '推进比较扎实', 'grades_I': '推进不够扎实'},
                '1.防治方案-1': {'grades_IV': '科学性很强', 'grades_III': '科学性强', 'grades_II': '科学性比较强', 'grades_I': '科学性不够强'},
                '1.防治方案-2': {'grades_IV': '针对性很强', 'grades_III': '针对性强', 'grades_II': '针对性比较强', 'grades_I': '针对性不够强'},
                '1.防治方案-3': {'grades_IV': '专业性很强', 'grades_III': '专业性强', 'grades_II': '专业性比较强', 'grades_I': '专业性不够强'},
                '2.作业设计-1': {'grades_IV': '非常合理', 'grades_III': '专业性强', 'grades_II': '专业性比较强', 'grades_I': '专业性不够强'},
                '2.作业设计-2': {'grades_IV': '与防治方案和技术规程非常一致', 'grades_III': '与防治方案和技术规程一致', 'grades_II': '与防治方案和技术规程基本一致', 'grades_I': '与防治方案和技术规程不够一致'},
                '2.作业设计-3': {'grades_IV': '操作性非常强', 'grades_III': '操作性强', 'grades_II': '操作性比较强', 'grades_I': '操作性不够强'},
                '3.专业档案-1': {'grades_IV': '很完备', 'grades_III': '完备', 'grades_II': '操作性比较强', 'grades_I': '操作性不够强'},
                '3.专业档案-2': {'grades_IV': '很规范', 'grades_III': '规范', 'grades_II': '比较规范', 'grades_I': '不够规范'},
                '3.专业档案-3': {'grades_IV': '很系统', 'grades_III': '系统', 'grades_II': '比较系统', 'grades_I': '不够系统'},
                '实施过程': {'grades_IV': '措施很扎实', 'grades_III': '措施扎实', 'grades_II': '措施比较扎实', 'grades_I': '措施不够扎实'},
                '防控效果': {'grades_IV': '发生面积大幅下降', 'grades_III': '发生面积下降', 'grades_II': '发生面积变化不大', 'grades_I': '发生面积上升'},
            }
            result = rs_data.get('result')
            total_score_list = []
            score = {}
            for result_index, result_value in enumerate(result):
                index = result_index + 1
                d = {'id': index, 'content': result_value.get('title'), 'item': '<strong>评价结果</strong>', 'evaluate': '',
                     'grades_IV': '<strong>优秀</strong>', 'grades_III': '<strong>良好</strong>',
                     'grades_II': '<strong>一般</strong>', 'grades_I': '<strong>较差</strong>', 'c': '', 'default': True}
                table_data.append(d)
                for section_index, section_value in enumerate(result_value.get('section_list')):
                    subentry_score_list = []
                    item_name = f"{section_index + 1}.{section_value.get('title')}"
                    for item in section_value.get('item_list'):
                        section_data = dict()
                        section_data['id'] = index
                        section_data['content'] = result_value.get('title')
                        section_data['item'] = item.get('title')
                        section_data['evaluate'] = ''
                        section_data['grades_IV'] = ''
                        section_data['grades_III'] = ''
                        section_data['grades_II'] = ''
                        section_data['grades_I'] = ''
                        section_data['c'] = ''

                        table_data.append(section_data)

                        subentry_score_list.append(int(item.get('scoring')) if item.get('scoring').isdigit() else 0)

                    item_score_list = score.get(result_value.get('title')).get('score_list') if score.get(result_value.get('title')) else None
                    if item_score_list:
                        item_score_list.append(sum(subentry_score_list))
                        score[result_value.get('title')]['total_score'] = sum(item_score_list)
                    else:
                        score[result_value.get('title')] = {'score_list': [sum(subentry_score_list)], 'total_score': sum(subentry_score_list)}
                        score[result_value.get('title')]['score_list'] = [sum(subentry_score_list)]

            for k, v in score.items():
                for i in table_data:
                    if i.get('content') == k:
                        i['c'] = v.get('total_score')

            data = {'title': '松材线虫病防控绩效评估综合评价表（定性）', 'data': table_data}

        return {'code': 200, 'data': data}

    def post(self):
        data = {}
        parser = reqparse.RequestParser()
        parser.add_argument('a', type=str)
        args = parser.parse_args()
        question_data = request.get_json()
        if args.get('a') == 'add':
            q = Questions.query.filter_by(id=question_data.get('id')).first()
            if q:
                q.title = question_data.get('title')
                q.content = question_data.get('content')
                q.start_at = question_data.get('surveyTime')[0]
                q.end_at = question_data.get('surveyTime')[1]
                q.save()
            else:
                Questions(title=question_data.get('title'),
                          content=question_data.get('content'),
                          start_at=question_data.get('surveyTime')[0],
                          end_at=question_data.get('surveyTime')[1]).save()
        if args.get('a') == 'result':
            qs = QuestionResult.query.filter_by(title=question_data.get('title'), user=question_data.get('uid')).first()
            if qs:
                qs.result = question_data.get('content')
                qs.save()
            else:
                QuestionResult(title=question_data.get('title'), result=question_data.get('content'),
                               user=question_data.get('uid')).save()

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
        parser = reqparse.RequestParser()
        parser.add_argument('a', type=str)
        parser.add_argument('token', type=str)
        args = parser.parse_args()
        data = []
        if args.get('a') == 'getUserInfo':
            u = Users.query.filter_by(token=args.get('token')).first()
            if u:
                data = to_json(u)
        else:
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
                      telephone=user_data.get('电话').get(k))
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


class Login(MethodView):
    def post(self):
        data = {'code': 200, 'data': 'success'}
        u = db_session.query(Users).filter_by(username=request.get_json().get('username')).first()
        if u:
            if u.check_password(request.get_json().get('password')):
                token = secrets.token_hex(16)
                db_session.query(Users).filter_by(id=u.id).update({'token': token})
                db_session.commit()
                data['data'] = {'token': token}
            else:
                data['error'] = {'message': '密码错误！'}
        else:
            data['error'] = {'message': '用户不存在！'}

        return data


class Logout(MethodView):
    def post(self):
        data = {'code': 200, 'data': 'success'}
        return data


api.add_resource(Index, "/api")
api.add_resource(Upload, '/upload')
api.add_resource(Download, '/download')
api.add_resource(Logout, '/logout')
api.add_resource(User, '/user', endpoint='user')
api.add_resource(User, '/user/<int:pk>', endpoint='users')
api.add_resource(QuestionManage, "/question", endpoint='question')
api.add_resource(QuestionManage, "/question/<int:pk>", endpoint='questions')
api.add_resource(Login, '/user/login', endpoint='user_login')
api.add_resource(Logout, '/user/logout', endpoint='user_logout')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)
