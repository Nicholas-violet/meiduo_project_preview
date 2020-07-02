from django.urls import path,re_path

from . import views

# urlpatterns是被Django自动识别的路由列表变量：定义该应用的所有路由信息
urlpatterns = [
    # 函数视图路由语法：
    # path('网络地址正则表达式', 函数视图名),
    # 订单确认
    re_path(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
    # 订单提交
    re_path(r'^orders/commit/$', views.OrderCommitView.as_view()),
]