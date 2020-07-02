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
import json
from .models import OrderInfo,OrderGoods

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



from django.utils import timezone

class OrderCommitView(View):
    """提交订单"""

    def post(self, request):
        """保存订单信息和订单商品信息"""
        # 获取当前要保存的订单数据
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        # 校验参数
        if not all([address_id, pay_method]):
            return JsonResponse({'code':400,
                                'errmsg':'缺少必传参数'})
        # 判断address_id是否合法
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return JsonResponse({'code':400,
                                'errmsg':'参数address_id有误'})
        # 判断pay_method是否合法
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'],
                              OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code':400,
                                'errmsg':'参数pay_method有误'})

        # 获取登录用户
        user = request.user
        # 生成订单编号：年月日时分秒+用户编号
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
        # 保存订单基本信息 OrderInfo（一）
        order = OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            address=address,
            total_count=0,
            total_amount=Decimal('0'),
            freight=Decimal('10.00'),
            pay_method=pay_method,
            status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']
            if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']
            else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        )


        # 从 redis 读取购物车中被勾选的商品信息
        redis_conn = get_redis_connection('carts')
        item_dict = redis_conn.hgetall('carts_%s' % user.id)
        cart_selected = redis_conn.smembers('selected_%s' % user.id)
        carts = {}
        for sku_id in cart_selected:
            carts[int(sku_id)] = int(item_dict[sku_id])
        # 获取选中的商品id:
        sku_ids = carts.keys()

        # 遍历购物车中被勾选的商品信息
        for sku_id in sku_ids:
            # 查询 SKU 信息
            sku = SKU.objects.get(id=sku_id)
            # 判断 SKU 库存
            sku_count = carts[sku.id]
            if sku_count > sku.stock:
                return JsonResponse({'code': 400,
                                     'errmsg': '库存不足'})

            # SKU减少库存，增加销量
            sku.stock -= sku_count
            sku.sales += sku_count
            sku.save()

            # 修改SPU销量
            sku.goods.sales += sku_count
            sku.goods.save()

            # 保存订单商品信息 OrderGoods（多）
            OrderGoods.objects.create(
                order=order,
                sku=sku,
                count=sku_count,
                price=sku.price,
            )

            # 保存商品订单中总价和总数量
            order.total_count += sku_count
            order.total_amount += (sku_count * sku.price)

        # 添加邮费和保存订单信息
        order.total_amount += order.freight
        order.save()

        # 清除购物车中已结算的商品
        redis_conn.hdel('carts_%s' % user.id, *cart_selected)
        redis_conn.srem('selected_%s' % user.id, *cart_selected)

        # 响应提交订单结果
        return JsonResponse({'code': 0,
                             'errmsg': '下单成功',
                             'order_id': order.order_id})

