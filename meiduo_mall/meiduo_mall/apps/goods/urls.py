from django.urls import path,re_path

from . import views

# urlpatterns是被Django自动识别的路由列表变量：定义该应用的所有路由信息
urlpatterns = [
    # 函数视图路由语法：
    # path('网络地址正则表达式', 函数视图名),

    # 商品列表页
    re_path(r'^list/(?P<category_id>\d+)/skus/$', views.ListView.as_view()),
    # 热销商品排行
    re_path(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view()),
    # 全文检索
    re_path(r'^search/$', views.MySearchView()),
]