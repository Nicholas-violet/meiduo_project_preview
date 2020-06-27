from django.shortcuts import render

# Create your views here.
from django import http
from django.views import View
from users.models import User
from meiduo_mall.utils.views import LoginRequiredMixin
# from utils.views import LoginRequiredMixin


# 用户名重复注册
class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        '''判断用户名是否重复'''
        # 1.查询username在数据库中的个数
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return http.JsonResponse({'code':400,'errmsg':'访问数据库失败'})

        # 2.返回结果(json) ---> code & errmsg & count
        return http.JsonResponse({'code': 0,'errmsg': 'ok','count':count})


# 手机号重复注册
class MobileCountView(View):

    def get(self, request, mobile):
        '''判断手机号是否重复注册'''
        # 1.查询mobile在mysql中的个数
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return http.JsonResponse({'code':400, 'errmsg':'查询数据库出错'})

        # 2.返回结果(json)
        return http.JsonResponse({'code':0, 'errmsg':'ok', 'count':count})


import json
import re
# from django import http
from django_redis import get_redis_connection
# 导入:
# from django.contrib.auth import login

# 用户注册接口设计
class RegisterView(View):

    def post(self, request):
        '''接收参数, 保存到数据库'''
        # 1.接收参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        allow = dict.get('allow')
        sms_code_client = dict.get('sms_code')

        # 2.校验(整体)
        if not all([username, password, password2, mobile, sms_code_client]):
            return http.JsonResponse({'code':400,
                                      'errmsg':'缺少必传参数'})

        # 3.username检验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'username格式有误'})

        # 4.password检验
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'password格式有误'})

        # 5.password2 和 password
        if password != password2:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '两次输入不对'})
        # 6.mobile检验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'mobile格式有误'})
        # 7.allow检验
        if allow != True:
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'allow格式有误'})

        # 8.sms_code检验 (链接redis数据库)
        redis_conn = get_redis_connection('verify_code')

        # 9.从redis中取值
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 10.判断该值是否存在
        if not sms_code_server:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '短信验证码过期'})
        # 11.把redis中取得值和前端发的值对比
        if sms_code_client != sms_code_server.decode():
            return http.JsonResponse({'code': 400,
                                      'errmsg': '验证码有误'})

        # 12.保存到数据库 (username password mobile)
        try:
            user =  User.objects.create_user(username=username,
                                             password=password,
                                             mobile=mobile)
        except Exception as e:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '保存到数据库出错'})

        # 添加如下代码
        # 实现状态保持
        login(request, user)

        # 13.拼接json返回
        response =  http.JsonResponse({'code': 0,
                                 'errmsg': 'ok'})

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 14 天
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)

        # 返回响应结果
        return response



import json
from django.contrib.auth import login, authenticate,logout


# 登录
class LoginView(View):

    def post(self, request):
        '''实现登录接口'''
        # 1.接收参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        remembered = dict.get('remembered')


        # 2.校验(整体 + 单个)
        if not all([username, password]):
            return http.JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        # 3.验证是否能够登录
        user = authenticate(username=username,
                            password=password)

        # 判断是否为空,如果为空,返回
        if user is None:
            return http.JsonResponse({'code': 400,
                                 'errmsg': '用户名或者密码错误'})

        # 4.状态保持
        login(request, user)

        # 5.判断是否记住用户
        if remembered != True:
            # 7.如果没有记住: 关闭立刻失效
            request.session.set_expiry(0)
        else:
            # 6.如果记住:  设置为两周有效
            request.session.set_expiry(None)

        # 8.返回json
        response = http.JsonResponse({'code': 0,
                             'errmsg': 'ok'})

        # 在响应对象中设置用户名信息.
        # 将用户名写入到 cookie，有效期 14 天
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)

        # 返回响应结果
        return response


# 退出登录
class LogoutView(View):
    """定义退出登录的接口"""

    def delete(self, request):
        """实现退出登录逻辑"""

        # 清理 session
        logout(request)

        # 创建 response 对象.
        response = http.JsonResponse({'code':0,
                                 'errmsg':'ok'})

        # 调用对象的 delete_cookie 方法, 清除cookie
        response.delete_cookie('username')

        # 返回响应
        return response



# 给该类视图增加 Mixin 扩展类
class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""

    def get(self, request):
        """提供个人信息界面"""

        # 获取界面需要的数据,进行拼接
        info_data = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }

        # 返回响应
        return http.JsonResponse({'code':0,
                             'errmsg':'ok',
                             'info_data':info_data})



import logging
logger = logging.getLogger('django')

class EmailView(View):
    """添加邮箱"""

    def put(self, request):
        """实现添加邮箱逻辑"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return http.JsonResponse({'code': 400,
                                 'errmsg': '缺少email参数'})
        if not re.match(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
            return http.JsonResponse({'code': 400,
                                 'errmsg': '参数email有误'})


        # 赋值 email 字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                 'errmsg': '添加邮箱失败'})
        # 变换 email 的格式: 从 '123456@qq.com' 变为: '<123456@qq.com>'
        email = '<' + email + '>'
        # 从 celery_tasks 中导入:
        from celery_tasks.email.tasks import send_verify_email
        # 调用发送的函数:
        # 用定义好的函数替换原来的字符串:
        verify_url = request.user.generate_verify_email_url()
        # 发送验证链接:
        send_verify_email.delay(email, verify_url)

        return http.JsonResponse({'code': 0,
                             'errmsg': '添加邮箱成功'})


class VerifyEmailView(View):
    """验证邮箱"""

    def put(self, request):
        """实现邮箱验证逻辑"""
        # 接收参数
        token = request.GET.get('token')

        # 校验参数：判断 token 是否为空和过期，提取 user
        if not token:
            return  http.JsonResponse({'code':400,
                                  'errmsg':'缺少token'})

        # 调用上面封装好的方法, 将 token 传入
        user = User.check_verify_email_token(token)
        if not user:
            return  http.JsonResponse({'code':400,
                                  'errmsg':'无效的token'})

        # 修改 email_active 的值为 True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':400,
                                 'errmsg':'激活邮件失败'})

        # 返回邮箱验证结果
        return http.JsonResponse({'code':0,
                             'errmsg':'ok'})


from .models import Address

class CreateAddressView(View):
    """新增地址"""

    def post(self, request):
        """实现新增地址逻辑"""

        # 获取地址个数:
        try:
           count = Address.objects.filter(user=request.user,
                                       is_deleted=False).count()
        except Exception as e:
            return http.JsonResponse({'code': 400,
                                 'errmsg': '获取地址数据出错'})
        # 判断是否超过地址上限：最多20个
        if count >= 20:
            return http.JsonResponse({'code': 400,
                                 'errmsg': '超过地址数量上限'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})


        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        # 保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
            )

            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                 'errmsg': '新增地址失败'})

        # 新增地址成功，将新增的地址响应给前端实现局部刷新
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        return http.JsonResponse({'code': 0,
                             'errmsg': '新增地址成功',
                             'address':address_dict})



class AddressView(View):
    """用户收货地址"""

    def get(self, request):
        """提供地址管理界面
        """
        # 获取所有的地址:
        addresses = Address.objects.filter(user=request.user,
                                           is_deleted=False)

        # 创建空的列表
        address_dict_list = []
        # 遍历
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }

            # 将默认地址移动到最前面
            default_address = request.user.default_address
            if default_address.id == address.id:
                  # 查询集 addresses 没有 insert 方法
                address_dict_list.insert(0, address_dict)
            else:
                address_dict_list.append(address_dict)

        default_id = request.user.default_address_id

        return http.JsonResponse({'code':0,
                             'errmsg':'ok',
                             'addresses':address_dict_list,
                             'default_address_id':default_id})



class UpdateDestroyAddressView(View):
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.JsonResponse({'code': 400,
                                  'errmsg': '缺少必传参数'})


        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user = request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
            )
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                 'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return http.JsonResponse({'code': 0,
                             'errmsg': '更新地址成功',
                             'address': address_dict})


    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        return http.JsonResponse({'code': 0,
                             'errmsg': '删除地址成功'})



class DefaultAddressView(View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return http.JsonResponse({'code': 0,
                             'errmsg': '设置默认地址成功'})



class UpdateTitleAddressView(View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return http.JsonResponse({'code': 0,
                             'errmsg': '设置地址标题成功'})



class ChangePasswordView(LoginRequiredMixin, View):
    """修改密码"""

    def put(self, request):
        """实现修改密码逻辑"""
        # 接收参数
        dict = json.loads(request.body.decode())
        old_password = dict.get('old_password')
        new_password = dict.get('new_password')
        new_password2 = dict.get('new_password2')

        # 校验参数
        if not all([old_password, new_password, new_password2]):
           return http.JsonResponse({'code':400,
                                'errmsg':'缺少必传参数'})


        result = request.user.check_password(old_password)
        if not result:
            return http.JsonResponse({'code':400,
                                 'errmsg':'原始密码不正确'})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return http.JsonResponse({'code':400,
                                 'errmsg':'密码最少8位,最长20位'})

        if new_password != new_password2:
            return http.JsonResponse({'code':400,
                                 'errmsg':'两次输入密码不一致'})

        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code':400,
                                 'errmsg':'修改密码失败'})

        # 清理状态保持信息
        logout(request)

        response = http.JsonResponse({'code':0,
                                 'errmsg':'ok'})

        response.delete_cookie('username')

        # # 响应密码修改结果：重定向到登录界面
        return response


from goods.models import SKU

class UserBrowseHistory(View):

     # 保存用户浏览记录
    def post(self, request):
        """保存用户浏览记录"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 校验参数:
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({'code':400,
                                'errmsg':'sku不存在'})

        # 保存用户浏览数据
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        user_id = request.user.id

        # 先去重: 这里给 0 代表去除所有的 sku_id
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 再存储
        pl.lpush('history_%s' % user_id, sku_id)
        # 最后截取: 界面有限, 只保留 5 个
        pl.ltrim('history_%s' % user_id, 0, 4)
        # 执行管道
        pl.execute()

        # 响应结果
        return http.JsonResponse({'code': 0,
                             'errmsg': 'OK'})

    def get(self, request):
        """获取用户浏览记录"""
        # 获取Redis存储的sku_id列表信息
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)

        # 根据sku_ids列表数据，查询出商品sku信息
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image_url,
                'price': sku.price
            })

        return http.JsonResponse({'code': 0,
                             'errmsg': 'OK',
                             'skus': skus})


