from django.shortcuts import render

# Create your views here.
from django import http
from django.views import View
from users.models import User

class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        '''判断用户名是否重复'''
        # 1.查询username在数据库中的个数
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return http.JsonResponse({'code':400,
                                 'errmsg':'访问数据库失败'})

        # 2.返回结果(json) ---> code & errmsg & count
        return http.JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count':count})