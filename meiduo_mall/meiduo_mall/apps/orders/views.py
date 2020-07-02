from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from goods.models import SKU
# from meiduo_mall.apps.users.models import Address
from users.models import Address
from meiduo_mall.utils.views import LoginRequiredMixin
from decimal import Decimal

class OrderSettlementView(LoginRequiredMixin, View):
    """结算订单"""

    def get(self, request):
        """提供订单结算页面"""
        # 获取登录用户
        user = request.user
        # 查询地址信息
        try:
            addresses = Address.objects.filter(user=request.user,
                                               is_deleted=False)
        except Exception as e:
            # 如果地址为空，渲染模板时会判断，并跳转到地址编辑页面
            addresses = None

        # 从Redis购物车中查询出被勾选的商品信息
        redis_conn = get_redis_connection('carts')
        item_dict = redis_conn.hgetall('carts_%s' % user.id)
        cart_selected = redis_conn.smembers('selected_%s' % user.id)
        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(item_dict[sku_id])

        # 查询商品信息
        sku_list = []

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image_url,
                'count':cart[sku.id],
                'price':sku.price
            })

        # 补充运费
        freight = Decimal('10.00')

        list = []
        for address in addresses:
            list.append({
                'id':address.id,
                'province':address.province.name,
                'city':address.city.name,
                'district':address.district.name,
                'place':address.place,
                'receiver':address.receiver,
                'mobile':address.mobile
            })

        # 渲染界面
        context = {
            'addresses': list,
            'skus': sku_list,
            'freight': freight,
        }

        return JsonResponse({'code':0,
                             'errmsg':'ok',
                             'context':context})