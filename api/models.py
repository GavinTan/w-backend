from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.


class Questions(models.Model):
    class Meta:
        verbose_name = '问卷管理'

    title = models.CharField('问卷标题', unique=True, max_length=128)
    survey_number = models.IntegerField('数据库地址', default=0)
    completed_number = models.IntegerField('调研人数', default=0)
    users = models.CharField('参与调查人员', max_length=128)
    content = models.JSONField('问卷内容', default=list)
    status = models.BooleanField('问卷状态', default=False)
    start_at = models.DateTimeField('问卷开始时间')
    end_at = models.DateTimeField('问卷结束时间')
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)


class Users(models.Model):

    class Meta:
        verbose_name = '用户列表'

    username = models.CharField('用户名', unique=True, max_length=64)
    password = models.CharField('密码', max_length=255)
    name = models.CharField('姓名', max_length=64)
    address = models.CharField('地址', max_length=128)
    telephone = models.CharField('地址', max_length=64)
    questions = models.CharField('调研问卷', max_length=64)
    token = models.CharField('token', max_length=128)
    roles = models.JSONField('权限', default=list)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    def save(self, *args, **kwargs):
        self.password = make_password(str(self.password))
        return super().save(*args, **kwargs)

    def check_password(self, password):
        return check_password(password, self.password)


class QuestionResult(models.Model):
    class Meta:
        verbose_name = '问卷调研结果'

    title = models.CharField('问卷标题', max_length=128)
    result = models.JSONField('调研结果', default=list)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    total_score = models.IntegerField('测评表总分', default=0)
    content_score_list = models.JSONField('分项总分', default=list)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    question = models.ForeignKey('Questions', related_query_name='question_result', on_delete=models.CASCADE)