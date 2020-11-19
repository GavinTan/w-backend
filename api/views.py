from django.shortcuts import render, redirect
from django.conf import settings
from django.db.models import Q
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.utils.timezone import localtime
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from pandas import ExcelFile
from .serializers import *
from .models import *
import os
import random
import string
import secrets
import json

# Create your views here.


class FileUploadView(viewsets.ViewSet):
    parser_classes = (MultiPartParser,)

    def create(self, request, format=None):
        if request.FILES:
            file_list = list()
            upload_dir = settings.UPLOAD_PATH
            filename = ''
            for i in request.FILES:
                file_obj = request.FILES.get(i)
                filename = file_obj.name
                file_list.append(request.scheme + '://' + request.META.get('HTTP_HOST') + '/upload/' + filename)
                file = upload_dir.joinpath(filename)
                if os.path.exists(file):
                    random_str = ''.join(random.sample(string.ascii_letters + string.digits, 6))
                    os.rename(file, upload_dir.joinpath(filename + '.' + random_str))
                with open(file, 'wb+') as f:
                    for chunk in file_obj.chunks():
                        f.write(chunk)
                os.system('dos2unix {}'.format(file))
            return Response(filename, status.HTTP_201_CREATED)
        else:
            return Response({'error': '参数不正确'})


class FileDownloadView(viewsets.ViewSet):
    def list(self, request):
        file = request.query_params.get('file', None)
        print(file)
        if file:
            return redirect(f'/static/{file}')
        return Response({'error': '文件不存在'})


class QuestionManageView(viewsets.ModelViewSet):
    model = Questions
    queryset = Questions.objects
    serializer_class = QuestionsSerializer

    def list(self, request, *args, **kwargs):
        a = request.query_params.get('a', None)
        uid = request.query_params.get('uid', None)
        title = request.query_params.get('title', None)

        if a == 'getUserQuestion':

            data = []
            for i in self.queryset.values():
                title = i.get('title')
                users = i.get('users') or ''
                user_list = users.split(',')
                qs = QuestionResult.objects.filter(Q(user=uid) & Q(title=title)).values().first()
                if qs:
                    i['fill'] = True

                i['start_at'] = localtime(i['start_at']).strftime("%Y-%m-%d %H:%M:%S")
                i['end_at'] = localtime(i['end_at']).strftime("%Y-%m-%d %H:%M:%S")
                i['updated_at'] = localtime(i['updated_at']).strftime("%Y-%m-%d %H:%M:%S")
                i['created_at'] = localtime(i['created_at']).strftime("%Y-%m-%d %H:%M:%S")

                if uid in user_list:
                    data.append(i)
            return Response(data, status=status.HTTP_200_OK)

        if a == 'getQuestionResult':
            return redirect('/questionResult')

        if a == 'getUserQuestionResult':
            data = []
            table_data = []
            rs_data = QuestionResult.objects.filter(Q(user=uid) & Q(title=title)).values().first()

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

            data = {'title': rs_data.get('title'), 'data': table_data}
            return Response(data, status=status.HTTP_200_OK)

        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        data = {}
        a = request.query_params.get('a', None)
        question_data = request.data
        if a == 'add':
            q = {'title': question_data.get('title'), 'content': question_data.get('content'),
                 'start_at': question_data.get('surveyTime')[0], 'end_at': question_data.get('surveyTime')[1]}

            self.queryset.update_or_create(defaults=q, id=question_data.get('id'))

        if a == 'result':
            q = self.queryset.filter(title=question_data.get('title')).first()
            q.completed_number += 1
            q.save()
            u = Users.objects.filter(id=question_data.get('uid')).first()
            qs = QuestionResult.objects.filter(Q(title=question_data.get('title')) & Q(user=u)).first()
            if qs:
                qs.result = question_data.get('content')
                qs.save()
            else:
                QuestionResult(title=question_data.get('title'), result=question_data.get('content'), user=u).save()

        return Response(data)

    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        self.queryset.filter(pk=pk).update(**request.data)
        return Response({})


class QuestionResultView(viewsets.ModelViewSet):
    queryset = QuestionResult.objects
    model = QuestionResult
    serializer_class = QuestionResultSerializer

    @action(methods=['delete'], detail=False, url_path='multipleDelete')
    def multiple_delete(self, request, *args, **kwargs):
        if request.data.get('list_id'):
            del_list_id = json.loads(request.data.get('list_id'))
            if del_list_id:
                self.model.objects.filter(id__in=del_list_id).delete()
                return Response({}, status.HTTP_204_NO_CONTENT)
            else:
                return Response({}, status.HTTP_404_NOT_FOUND)

        return Response({'error': '没有删除的list_id列表'})


class UserView(viewsets.ModelViewSet):
    queryset = Users.objects
    model = Users
    serializer_class = UsersSerializer

    def get_queryset(self):
        return self.queryset.filter(~Q(username='admin'))

    def list(self, request, *args, **kwargs):
        a = request.query_params.get('a', None)
        token = request.query_params.get('token', None)
        if a == 'getUserInfo':
            return Response(self.queryset.filter(token=token).values().first() or {})
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        file_path = settings.UPLOAD_PATH
        excel = ExcelFile(file_path.joinpath(request.data.get('file').get('data')))
        df = excel.parse(excel.sheet_names[0])
        table_data = df.to_dict()
        for k, v in table_data.get('用户名').items():
            user_data = {'username': v, 'password': table_data.get('密码').get(k),
                         'address': table_data.get('地址').get(k), 'name': table_data.get('姓名').get(k),
                         'telephone': table_data.get('电话').get(k)}
            Users.objects.update_or_create(defaults=user_data, username=v)

        return redirect('/user')

    @action(methods=['delete'], detail=False, url_path='multipleDelete')
    def multiple_delete(self, request, *args, **kwargs):
        if request.data.get('list_id'):
            del_list_id = json.loads(request.data.get('list_id'))
            if del_list_id:
                self.queryset.filter(id__in=del_list_id).delete()
                return Response({}, status.HTTP_204_NO_CONTENT)
            else:
                return Response({}, status.HTTP_404_NOT_FOUND)

        return Response({'error': '没有删除的list_id列表'})


class Login(viewsets.ViewSet):
    def create(self, request, *args, **kwargs):
        data = {}
        # Users(username='admin', name='admin', password='123456', roles=['admin']).save()
        u = Users.objects.filter(username=request.data.get('username'))
        if u:
            if u.first().check_password(request.data.get('password')):
                token = secrets.token_hex(16)
                u.update(token=token)
                data = {'token': token}
            else:
                data['error'] = {'message': '密码错误！'}
        else:
            data['error'] = {'message': '用户不存在！'}

        return Response(data)


class Logout(viewsets.ViewSet):
    def create(self, request, *args, **kwargs):
        data = {}
        return Response(data)