from django.shortcuts import render

# Create your views here.
# 导入:
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import http
from django.views import View


class QQFirstView(View):
    """提供QQ登录页面网址"""

    def get(self, request):
        # next 表示从哪个页面进入到的登录页面
        # 将来登录成功后，就自动回到那个页面
        next = request.GET.get('next')

        # 获取 QQ 登录页面网址
        # 创建 OAuthQQ 类的对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 调用对象的获取 qq 地址方法
        login_url = oauth.get_qq_url()

        # 返回登录地址
        return http.JsonResponse({
                                'code': 0,
                                'errmsg': 'OK',
                                'login_url':login_url
        })