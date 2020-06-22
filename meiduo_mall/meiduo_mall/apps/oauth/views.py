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
from oauth.utils import generate_access_token
from django.db import DatabaseError
import json, re
from django_redis import get_redis_connection
from oauth.utils import check_access_token
from users.models import User

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
        # pass


    def post(self, request):
        """美多商城用户绑定到openid"""

        # 1.接收参数
        dict = json.loads(request.body.decode())
        mobile = dict.get('mobile')
        password = dict.get('password')
        sms_code_client = dict.get('sms_code')
        access_token = dict.get('access_token')

        # 2.校验参数
        # 判断参数是否齐全
        if not all([mobile, password, sms_code_client]):
            return http.JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                 'errmsg': '请输入正确的手机号码'})

        # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.JsonResponse({'code': 400,
                                 'errmsg': '请输入8-20位的密码'})

        # 3.判断短信验证码是否一致
        # 创建 redis 链接对象:
        redis_conn = get_redis_connection('verify_code')

        # 从 redis 中获取 sms_code 值:
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 判断获取出来的有没有:
        if sms_code_server is None:
            # 如果没有, 直接返回:
            return http.JsonResponse({'code': 400,
                                 'errmsg': '验证码失效'})

        # 如果有, 则进行判断:
        if sms_code_client != sms_code_server.decode():
            # 如果不匹配, 则直接返回:
            return http.JsonResponse({'code': 400,
                                 'errmsg': '输入的验证码有误'})

            # 调用我们自定义的函数, 检验传入的 access_token 是否正确:
        # 错误提示放在 sms_code_errmsg 位置
        openid = check_access_token(access_token)
        if not openid:
            return http.JsonResponse({'code': 400,
                                 'errmsg': '缺少openid'})

        # 4.保存注册数据
        try:
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            # 用户不存在,新建用户
            user = User.objects.create_user(username=mobile,
                                            password=password,
                                            mobile=mobile)
        else:
            # 如果用户存在，检查用户密码
            if not user.check_password(password):
                return http.JsonResponse({'code': 400,
                                     'errmsg': '输入的密码不正确'})

        # 5.将用户绑定 openid
        try:
            OAuthQQUser.objects.create(openid=openid, user=user)
        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': '往数据库添加数据出错'})

        # 6.实现状态保持
        login(request, user)

        # 7.创建响应对象:
        response = http.JsonResponse({'code': 0, 'errmsg': 'ok'})

        # 8.登录时用户名写入到 cookie，有效期14天
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)

        # 9.响应++
        return response



