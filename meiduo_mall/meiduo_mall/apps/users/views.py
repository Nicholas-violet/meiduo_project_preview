from django.shortcuts import render

# Create your views here.
from django import http
from django.views import View
from users.models import User


# 用户名重复注册
class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        '''判断用户名是否重复'''
        # 1.查询username在数据库中的个数
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return http.JsonResponse({'code':400,'errmsg':'访问数据库失败'})

        # 2.返回结果(json) ---> code & errmsg & count
        return http.JsonResponse({'code': 0,'errmsg': 'ok','count':count})


# 手机号重复注册
class MobileCountView(View):

    def get(self, request, mobile):
        '''判断手机号是否重复注册'''
        # 1.查询mobile在mysql中的个数
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return http.JsonResponse({'code':400, 'errmsg':'查询数据库出错'})

        # 2.返回结果(json)
        return http.JsonResponse({'code':0, 'errmsg':'ok', 'count':count})