from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import *


class QuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questions
        fields = '__all__'


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'


class QuestionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionResult
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        del representation['user']
        representation['uid'] = instance.user.id
        representation['username'] = instance.user.username
        representation['name'] = instance.user.name
        representation['address'] = instance.user.address
        representation['telephone'] = instance.user.telephone
        return representation



