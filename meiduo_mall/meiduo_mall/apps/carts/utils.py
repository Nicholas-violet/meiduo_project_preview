import pickle,base64
from django_redis import get_redis_connection

# 逻辑分析
"""
1.合并方向：cookie 购物车数据合并到 Redis 购物车数据中。
2.合并数据：购物车商品数据和勾选状态。
3.合并方案：
    3.1 Redis 数据库中的购物车数据保留。

    3.2 如果 cookie 中的购物车数据在 Redis 数据库中已存在
        将 cookie 购物车数据覆盖 Redis 购物车数据。

    3.3 如果 cookie 中的购物车数据在 Redis 数据库中不存在，
        将 cookie 购物车数据新增到 Redis。

    3.4 最终购物车的勾选状态以 cookie 购物车勾选状态为准。
"""

def merge_cart_cookie_to_redis(request, user, response):
    """
    登录后合并cookie购物车数据到Redis
    :param request: 本次请求对象，获取 cookie 中的数据
    :param response: 本次响应对象，清除 cookie 中的数据
    :param user: 登录用户信息，获取 user_id
    :return: response
    """
    # 获取cookie中的购物车数据
    cookie_cart = request.COOKIES.get('carts')
    # cookie中没有数据就响应结果
    if not cookie_cart:
        return response
    cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

    new_dict = {}
    new_add = []
    new_remove = []
    # 同步cookie中购物车数据
    for sku_id, item in cart_dict.items():
        new_dict[sku_id] = item['count']

        if item['selected']:
            new_add.append(sku_id)
        else:
            new_remove.append(sku_id)

    # 将new_cart_dict写入到Redis数据库
    redis_conn = get_redis_connection('carts')
    pl = redis_conn.pipeline()
    pl.hmset('carts_%s' % user.id, new_dict)
    # 将勾选状态同步到Redis数据库
    if new_add:
        pl.sadd('selected_%s' % user.id, *new_add)
    if new_remove:
        pl.srem('selected_%s' % user.id, *new_remove)
    pl.execute()

    # 清除cookie
    response.delete_cookie('carts')

    return response