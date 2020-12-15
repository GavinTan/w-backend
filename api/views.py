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
from api.utils import get_result_data, excel_number_handle
from .serializers import *
from .models import *
import datetime
import os
import random
import string
import secrets
import json
import xlrd


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
        if file:
            return redirect(f'{settings.FRONTEND_BASE_API}/static/{file}')
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
            return redirect(f'{settings.FRONTEND_BASE_API}/questionResult')

        if a == 'getUserQuestionResult':

            rs_data = QuestionResult.objects.filter(Q(user=uid) & Q(title=title)).first()

            data = {
                'id': rs_data.id,
                'title': rs_data.title,
                'name': rs_data.user.name,
                'data': rs_data.result,
                'tableTotalScore': rs_data.total_score,
                'fill_time': (rs_data.created_at + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
                'end_at': rs_data.question.end_at.timestamp() * 1000
            }
            return Response(data, status=status.HTTP_200_OK)

        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        data = {}
        a = request.query_params.get('a', None)
        question_data = request.data
        if a == 'add':
            q = {
                'title': question_data.get('title'),
                'content': question_data.get('content'),
                'users': question_data.get('users'),
                'survey_number': question_data.get('survey_number'),
                'start_at': question_data.get('surveyTime')[0],
                'end_at': question_data.get('surveyTime')[1]
            }
            self.queryset.update_or_create(defaults=q, id=question_data.get('id'))

        if a == 'result':
            q = self.queryset.filter(title=question_data.get('title')).first()
            # q.completed_number += 1
            q.save()
            u = Users.objects.filter(id=question_data.get('uid')).first()
            qs = QuestionResult.objects.filter(Q(title=question_data.get('title')) & Q(user=u)).first()
            if qs:
                qs.result = question_data.get('content')
                qs.save()
            else:
                qid = question_data.get('id')
                content_data = question_data.get('content')
                result, total_score, content_score_list = get_result_data(content_data)
                QuestionResult(
                    question_id=qid,
                    title=question_data.get('title'),
                    result=result,
                    user=u,
                    total_score=total_score,
                    content_score_list=content_score_list
                ).save()

        return Response(data)

    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        self.queryset.filter(pk=pk).update(**request.data)
        return Response({})

    def delete(self, request, *args, **kwargs):
        del_id = request.data.get('id')
        self.model.objects.filter(id=del_id).delete()
        return Response({}, status.HTTP_200_OK)


class StatisticsView(viewsets.ModelViewSet):
    model = StatisticsData
    queryset = StatisticsData.objects
    serializer_class = StatisticsDataSerializer

    def list(self, request, *args, **kwargs):
        return Response(StatisticsData.objects.first().data, status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        base_path = settings.UPLOAD_PATH
        file_path = base_path.joinpath(request.data.get('file').get('data'))
        map_data = []
        workbook = xlrd.open_workbook(file_path)
        for index, value in enumerate(workbook.sheet_names()):

            sheet1_object = workbook.sheet_by_index(index)
            nrows = sheet1_object.nrows
            ncols = sheet1_object.ncols

            type_list = []

            for i in range(0, ncols):
                all_col = sheet1_object.col_values(i, 0, nrows)
                item = {
                    'title': all_col[0],
                    'type': [{
                        'title': all_col[1],
                        'unit': all_col[2],
                        'list': excel_number_handle(all_col[3: sheet1_object.nrows])
                    }]
                }
                res = list(filter(lambda x: x.get('title') == all_col[0], type_list))

                if len(res):
                    type_list_index = type_list.index(res[0])
                    res[0].get('type').append({
                        'title': all_col[1],
                        'unit': all_col[2],
                        'list': excel_number_handle(all_col[3: sheet1_object.nrows])
                    })
                    type_list[type_list_index] = res[0]
                else:
                    type_list.append(item)

            areaData = {
                'title': value,
                'id': index + 1,
                'type': type_list
            }

            map_data.append(areaData)
        StatisticsData.objects.update_or_create(data=map_data, id=1)
        return Response(map_data, status.HTTP_200_OK)


class QuestionResultView(viewsets.ModelViewSet):
    queryset = QuestionResult.objects
    model = QuestionResult
    serializer_class = QuestionResultSerializer

    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        self.queryset.filter(pk=pk).update(**request.data)
        return Response({})

    @action(methods=['delete'], detail=False, url_path='multipleDelete')
    def multiple_delete(self, request, *args, **kwargs):
        if request.data.get('list_id'):
            del_list_id = json.loads(request.data.get('list_id'))
            if del_list_id:
                self.model.objects.filter(id__in=del_list_id).delete()
                return Response({}, status.HTTP_200_OK)
            else:
                return Response({}, status.HTTP_404_NOT_FOUND)

        return Response({'error': '没有删除的list_id列表'})


class OpinionManageView(viewsets.ModelViewSet):
    model = OpinionManage
    queryset = OpinionManage.objects
    serializer_class = OpinionManageSerializer

    def list(self, request, *args, **kwargs):
        qsid = request.query_params.get('qsid', None)
        opinion_data = self.queryset.filter(question_result_id=qsid).first()
        if opinion_data:
            data = {
                'id': opinion_data.id,
                'title': opinion_data.question_result.title,
                'data': opinion_data.data,
                'tableTotalScore': opinion_data.question_result.total_score,
                'user': opinion_data.user.name,
                'edit': True,
                'update_at': (opinion_data.update_at + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            rs_data = QuestionResult.objects.filter(id=qsid).first()

            data = {
                'id': rs_data.id,
                'title': rs_data.title,
                'data': rs_data.result,
                'tableTotalScore': rs_data.total_score,
            }
        return Response(data)

    def create(self, request, *args, **kwargs):
        qsid = request.data.get('qsid')
        data = request.data.get('data')
        uid = request.data.get('uid')
        self.queryset.update_or_create(defaults={'question_result': QuestionResult.objects.filter(id=qsid).first(),
                                                 'data': data, 'user': Users.objects.filter(id=uid).first()}, question_result_id=qsid)
        return Response({'error': '没有删除的list_id列表'})


class UserView(viewsets.ModelViewSet):
    queryset = Users.objects
    model = Users
    serializer_class = UsersSerializer
    pagination_class = UsersPagination

    # def get_queryset(self):
    #     return self.queryset.filter(~Q(username='admin'))

    def get_queryset(self):
        return Users.objects.filter(~Q(username='admin')).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        a = request.query_params.get('a', None)
        keyword = request.query_params.get('keyword', None)
        token = request.query_params.get('token', None)
        if a == 'getUserInfo':
            return Response(self.queryset.filter(token=token).values().first() or {})
        users = self.get_queryset()
        if keyword:
            return Response({'data': users.values('id', 'name')})
        page = self.paginate_queryset(users)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):

        username = request.data.get('username')
        if username:
            first = Users.objects.filter(username=username).first()
            if first:
                return Response({}, status.HTTP_400_BAD_REQUEST)
            Users.objects.create(**request.data)
            return Response({}, status.HTTP_200_OK)

        file_path = settings.UPLOAD_PATH
        excel = ExcelFile(file_path.joinpath(request.data.get('file').get('data')))
        df = excel.parse(excel.sheet_names[0])
        table_data = df.to_dict()
        items = []
        username_list = []

        for k, v in table_data.get('用户名').items():
            username_list.append(v)
            items.append(Users(
                username=v,
                password=str(table_data.get('密码').get(k)),
                roles=['guest'],
                address=table_data.get('地址').get(k),
                name=table_data.get('姓名').get(k),
                telephone=table_data.get('电话').get(k)
            ))
        user_list = [value.get('username') for value in Users.objects.filter(username__in=username_list).values('username')]
        filter_items = list(filter(lambda i: i.username not in user_list, items))
        Users.objects.bulk_create(filter_items)
        return redirect(f'{settings.FRONTEND_BASE_API}/user')

    @action(methods=['delete'], detail=False, url_path='multipleDelete')
    def multiple_delete(self, request, *args, **kwargs):
        if request.data.get('list_id'):
            del_list_id = json.loads(request.data.get('list_id'))
            if del_list_id:
                self.queryset.filter(id__in=del_list_id).delete()
                return Response({}, status.HTTP_200_OK)
            else:
                return Response({}, status.HTTP_404_NOT_FOUND)

        return Response({'error': '没有删除的list_id列表'})


class Login(viewsets.ViewSet):
    def create(self, request, *args, **kwargs):
        data = {}
        username = request.data.get('username')
        # Users(username='admin', name='admin', password='123456', roles=['admin']).save()
        u = Users.objects.filter(username=request.data.get('username'))
        if u:
            if u.first().password == request.data.get('password') or u.first().check_password(request.data.get('password')):
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
