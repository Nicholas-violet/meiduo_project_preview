from django.shortcuts import render

# Create your views here.
from django.views import View
from goods.models import SKU,GoodsCategory
from django.http import JsonResponse
from .utils import get_breadcrumb
from django.core.paginator import Paginator, EmptyPage



class ListView(View):

    def get(self, request, category_id):
        # 1.基本参数提取
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')

        # 2.参数校验
        # category = GoodsCategory.objects.get(category_id=category_id)

        # 3.数据处理
        # 判断category_id是否正确
        try:
            # 获取三级菜单分类信息:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '获取mysql数据出错'})

        # 查询面包屑导航
        breadcrumb = get_breadcrumb(category)

        # 排序方式:
        try:
            skus = SKU.objects.filter(category=category,
                                      is_launched=True).order_by(ordering)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '获取mysql数据出错'})

        # 用于分页的,paginator是分页器
        paginator = Paginator(skus, page_size)
        # 获取每页商品数据
        try:
            page_skus = paginator.page(page)
        except EmptyPage:
            # 如果page_num不正确，默认给用户400
            return JsonResponse({'code': 400,
                                 'errmsg': 'page数据出错'})
        # 获取列表页总页数
        total_page = paginator.num_pages

        # 定义列表:
        list = []
        # 整理格式:
        for sku in page_skus:
            list.append({
                'id': sku.id,
                'default_image_url': sku.default_image_url,
                'name': sku.name,
                'price': sku.price
            })

        # 4.返回响应
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'breadcrumb':breadcrumb,
            'list':list,
            'count':total_page
        })


class HotGoodsView(View):
    """商品热销排行"""

    def get(self, request, category_id):
        """提供商品热销排行 JSON 数据"""
        # 根据销量倒序
        try:
            skus = SKU.objects.filter(category_id=category_id,
                                  is_launched=True).order_by('-sales')[:2]
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':'获取商品出错'})
        # 转换格式:
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url,
                'name':sku.name,
                'price':sku.price
            })

        return JsonResponse({'code':0,
                             'errmsg':'OK',
                             'hot_skus':hot_skus})


# 导入:
from haystack.views import SearchView

class MySearchView(SearchView):
    '''重写SearchView类'''
    def create_response(self):
        page = self.request.GET.get('page')
        # 获取搜索结果
        context = self.get_context()
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id':sku.object.id,
                'name':sku.object.name,
                'price':sku.object.price,
                'default_image_url':sku.object.default_image_url,
                'searchkey':context.get('query'),
                'page_size':context['page'].paginator.num_pages,
                'count':context['page'].paginator.count
            })
        # 拼接参数, 返回
        return JsonResponse(data_list, safe=False)
