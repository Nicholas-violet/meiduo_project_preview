from django.urls import path,re_path

from . import views

# urlpatterns是被Django自动识别的路由列表变量：定义该应用的所有路由信息
urlpatterns = [
    # 函数视图路由语法：
    # path('网络地址正则表达式', 函数视图名),
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    re_path(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    re_path(r'^register/$', views.RegisterView.as_view()),
    re_path(r'^login/$', views.LoginView.as_view()),
    re_path(r'^logout/$', views.LogoutView.as_view()),
    # 用户中心的子路由
    re_path(r'^info/$', views.UserInfoView.as_view()),
    re_path(r'^emails/$', views.EmailView.as_view()),
    # 验证邮箱
    re_path(r'^emails/verification/$', views.VerifyEmailView.as_view()),
    # 新增收货地址
    re_path(r'^addresses/create/$', views.CreateAddressView.as_view()),
    # 访问地址的子路由:
    re_path(r'^addresses/$', views.AddressView.as_view()),

]