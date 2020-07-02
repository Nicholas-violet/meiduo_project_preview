from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import JsonResponse
from goods.models import SKU
import json
from django_redis import get_redis_connection
import pickle
import base64


# 添加,展示,修改,删除购物车
class CartsView(View):
    """ 购物车管理 """

    """ 添加购物车 """
    def post(self, request):
        """ 添加购物车 """

        # =================1接收参数=================
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # =================2参数校验=================
        # 2.1校验参数是否完整
        if not all([sku_id,count,selected]):
            return JsonResponse({
                'code':400,
                'errmsg':'缺少必传参数!'
            })

        # 2.2校验商品是否存在,即sku_id是否存在数据库里面
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg':'商品不存在'
            })

        # 2.3判断传数值count是不是数字类型,
        # 这一个count现在是str类型,并且他是纯数字的str类型
        if isinstance(count, str) and not count.isdigit():
            return JsonResponse({
                'code':400,
                'errmsg':'conut参数错误'
            })

        # 2.4判断selected是不是boolean类型,isinstance是判断一个是不是什么类型的,返回的是true,false
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({
                    'code':400,
                    'errmsg':'selected 有误'
                })

        # ============判断用户是否登录==========
        if request.user.is_authenticated:
            # 用户登录了,操作redis数据库的购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()

            # 新增购物车数据
            pl.hincrby('carts_%s'%request.user.id, sku_id, count)
            # 新增的选中的状态
            if selected:
                pl.sadd('selected_%s'%request.user.id, sku_id)

            # 执行管道
            pl.execute()

            # 响应结果
            return JsonResponse({
                'code':0,
                'errmsg':'添加购物车成功'
            })



        else:
            # 用户没有登录,操作cookie购物车
            cookie_cart = request.COOKIES.get('carts')
            # 如果用户操作过 cookies 购物车
            if cookie_cart:
                # 将cookie_cart 转成base64的bytes,最后吧bytes转换为字典
                cart_dict = pickle.loads(base64.b64decode(cookie_cart))

            # 如果没有操作过 cookies 购物车
            else:
                cart_dict = {}

            # 判断要加入购物车的商品是否已经存在,如果存在就增加数值,不存在就添加.

            # 如果存在
            if sku_id in cart_dict:
                # 数量累加
                count += cart_dict[sku_id]['count']

            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }

            # 将字典转成bytes,在将bytes转成base64的bytes,最后吧butes转成字符串
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 创建响应对象
            response = JsonResponse({
                'code':0,
                'errmsg':'添加购物车成功'
            })

            response.set_cookie('carts', cart_data)

            return response

    """ 展示购物车 """
    def get(self, request):
        """ 展示购物车 """
        user = request.user
        # 用户已经登录,就查询redis数据库
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')

            # 获取redis中的购物车的信息数据
            item_dict = redis_conn.hgetall('carts_%s'%user.id)
            # 获取redis中的选定状态
            cart_selected = redis_conn.smembers('selected_%s'%user.id)

            # 将redis中 数据构造成和cookies一样的,方便统一查询

            cart_dict = {}
            for sku_id, count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count':int(count),
                    'selected':sku_id in cart_selected
                }

        # 用户未登录,就查询cookies数据库
        else:
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                # 将cart_str转成bytes,再将bytes转成base64的bytes,最后转化成为字典
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name':sku.name,
                'count':cart_dict.get(sku.id).get('count'),
                'selected':cart_dict.get(sku.id).get('selected'),
                'default_image_url':sku.default_image_url,
                'price':sku.price,
                'amount':sku.price * cart_dict.get(sku.id).get('count'),
            })

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'cart_skus':cart_skus
        })

    """ 修改购物车 """
    def put(self, request):
        """ 修改购物车 """
        # ===========接收参数开始 ===========
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)
        # ===========接收参数结束 ===========

        # =========== 校验参数开始 ============
        # 判断参数是否齐全
        if not all([sku_id, count]):
            return JsonResponse({'code':400,
                                       'errmsg': '缺少必传参数'})
        # 判断sku_id是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code':400,
                                       'errmsg': 'sku_id不存在'})
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':400,
                                       'errmsg': 'count有误'})
        # 判断selected是否为bool值
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code':400,
                                           'errmsg': 'selected有误'})
        # =========== 校验参数结束 ============


        # ================== 数据处理与返回开始 ===================
        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，修改redis购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 因为接口设计为幂等的，直接覆盖
            pl.hset('carts_%s' % user.id, sku_id, count)
            # 是否选中
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

            # 创建响应对象
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image_url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            return JsonResponse({'code': 0,
                                 'errmsg': '修改购物车成功',
                                 'cart_sku': cart_sku})


        # ===== 操作cookies结束 =====

        # ===== 操作redis开始 =====
        else:
            # 用户未登录,操作cookies购物车
            # 用户未登录，修改cookie购物车
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                # 将cookie_cart转成bytes,再将bytes转成base64的bytes,最后将bytes转字典
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}
            # 因为接口设计为幂等的，直接覆盖
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将字典转成bytes,再将bytes转成base64的bytes,最后将bytes转字符串
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 创建响应对象
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected
            }
            response = JsonResponse({'code': 0,
                                     'errmsg': '修改购物车成功',
                                     'cart_sku': cart_sku})
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', cart_data)

            return response
        # ===== 操作redis结束 =====
        # ================== 数据处理与返回结束 ===================

    """删除购物车"""
    def delete(self, request):
        """删除购物车"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 判断sku_id是否存在
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg': '商品不存在'
            })

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户未登录，删除redis购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 删除键，就等价于删除了整条记录
            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

            # 删除结束后，没有响应的数据，只需要响应状态码即可
            return JsonResponse({
                'code': 0,
                'errmsg': '删除购物车成功'
            })

        else:
            # 用户未登录，删除cookie购物车
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                # 将cookie_cart转成bytes,再将bytes转成base64的bytes,最后将bytes转字典
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

            # 创建响应对象
            response = JsonResponse({'code': 0,
                                     'errmsg': '删除购物车成功'})
            if sku_id in cart_dict:
                del cart_dict[sku_id]
                # 将字典转成bytes,再将bytes转成base64的bytes,最后将bytes转字符串
                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 响应结果并将购物车数据写入到cookie
                response.set_cookie('carts', cart_data)

            return response



# 全选购物车
class CartSelectAllView(View):
    """全选购物车"""

    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected', True)

        # 校验参数
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({
                    'code':400,
                    'errmsg':'参数selected有误'
                })

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，操作 redis 购物车
            redis_conn = get_redis_connection('carts')
            item_dict = redis_conn.hgetall('carts_%s' % user.id)
            sku_ids = item_dict.keys()

            if selected:
                # 全选
                redis_conn.sadd('selected_%s' % user.id, *sku_ids)
            else:
                # 取消全选
                redis_conn.srem('selected_%s' % user.id, *sku_ids)

            return JsonResponse({
                'code': 0,
                'errmsg': '全选购物车成功'
            })
        else:
            # 用户未登录，操作 cookie 购物车
            cookie_cart = request.COOKIES.get('carts')
            response = JsonResponse({
                'code': 0,
                'errmsg': '全选购物车成功'
            })
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

                for sku_id in cart_dict.keys():
                    cart_dict[sku_id]['selected'] = selected

                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

                response.set_cookie('carts', cart_data)

            return response



# 展示商品页面简单购物车
class CartsSimpleView(View):
    """商品页面右上角购物车"""
    def get(self, request):

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，查询 Redis 购物车
            redis_conn = get_redis_connection('carts')
            item_dict = redis_conn.hgetall('carts_%s' % user.id)
            cart_selected = redis_conn.smembers('selected_%s' % user.id)

            # 将 redis 中的两个数据统一格式，跟 cookie 中的格式一致，方便统一查询
            cart_dict = {}
            for sku_id, count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            # 用户未登录，查询 cookie 购物车
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

        # 构造简单购物车 JSON 数据
        cart_skus = []
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image_url
            })

        # 响应 json 列表数据
        return JsonResponse({
            'code': 0,
            'errmsg': 'OK',
            'cart_skus': cart_skus
        })










