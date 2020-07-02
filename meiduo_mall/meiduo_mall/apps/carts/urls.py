from django.urls import path,re_path

from . import views

# urlpatterns是被Django自动识别的路由列表变量：定义该应用的所有路由信息
urlpatterns = [
    # 函数视图路由语法：
    # path('网络地址正则表达式', 函数视图名),
    # 购物车的添加,展示,修改,删除
    re_path(r'^carts/$', views.CartsView.as_view()),
    # 全选购物车
    re_path(r'^carts/selection/$', views.CartSelectAllView.as_view()),

]