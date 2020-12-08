from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import *
from rest_framework import pagination
from rest_framework.response import Response
from collections import OrderedDict
from rest_framework import status


class QuestionsSerializer(serializers.ModelSerializer):

    survey_number = serializers.SerializerMethodField()
    completed_number = serializers.SerializerMethodField()

    class Meta:
        model = Questions
        fields = '__all__'

    def get_survey_number(self, obj):
        return len(obj.users.split(',')) if obj.users else 0

    def get_completed_number(self, obj):
        return obj.questionresult_set.count()


class UsersPagination(pagination.PageNumberPagination):
    page_size = 15

    def get_paginated_response(self, data):

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_size', self.page_size),
            ('data', data)
        ]))


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'


class StatisticsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatisticsData
        fields = '__all__'


class QuestionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionResult
        exclude = ('result',)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        del representation['user']
        representation['uid'] = instance.user.id
        representation['username'] = instance.user.username
        representation['name'] = instance.user.name
        representation['address'] = instance.user.address
        representation['telephone'] = instance.user.telephone
        return representation





