from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'upload', views.FileUploadView, basename='upload')
router.register(r'download', views.FileDownloadView, basename='download')
router.register(r'statistics', views.StatisticsView, basename='statistics')
router.register(r'question', views.QuestionManageView, basename='question')
router.register(r'user/login', views.Login, basename='login')
router.register(r'logout', views.Logout, basename='logout')
router.register(r'user', views.UserView, basename='user')
router.register(r'questionResult', views.QuestionResultView, basename='question_result')


urlpatterns = [
    path('', include(router.urls)),
]
