from django.shortcuts import render

# Create your views here.
# 导入:
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import http
from django.views import View

# QQ第一个接口实现，就是页面扫码接口
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


# QQ第二个接口，重定向会我们自己的页面
# 导入:
from oauth.models import OAuthQQUser
import logging
logger = logging.getLogger('django')
from django.contrib.auth import login
# from oauth.utils import generate_access_token

class QQUserView(View):
    """用户扫码登录的回调处理"""

    def get(self, request):
        """Oauth2.0认证"""
        # 获取前端发送过来的 code 参数:
        code = request.GET.get('code')

        if not code:
            # 判断 code 参数是否存在
            return http.JsonResponse({'code': 400,
                                 'errmsg': '缺少code参数'})

        # 调用我们安装的 QQLoginTool 工具类
        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 携带 code 向 QQ服务器 请求 access_token
            access_token = oauth.get_access_token(code)

            # 携带 access_token 向 QQ服务器 请求 openid
            openid = oauth.get_open_id(access_token)

        except Exception as e:
            # 如果上面获取 openid 出错, 则验证失败
            logger.error(e)
            # 返回结果
            return http.JsonResponse({'code': 400,
                                 'errmsg': 'oauth2.0认证失败, 即获取qq信息失败'})
        pass



