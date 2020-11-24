from django.test import TestCase

from django.shortcuts import render
from django.contrib.auth.models import User
import random
from rest_framework.response import Response
# Create your views here.

from rest_framework import serializers
from rest_framework import pagination
from rest_framework.viewsets import ModelViewSet
from collections import OrderedDict, namedtuple


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class UserPagination(pagination.PageNumberPagination):
    page_size = 20

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.page_size),
            ('results', data)
        ]))


class UserViewset(ModelViewSet):
    serializer_class = UserSerializer
    pagination_class = UserPagination

    def get_queryset(self):
        return User.objects.all()

    def list(self, request, *args, **kwargs):

        status = request.query_params.get("status")
        users = self.get_queryset()
        if status == '1':
            self.paginator.page_size = users.count()

        page = self.paginate_queryset(users)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
