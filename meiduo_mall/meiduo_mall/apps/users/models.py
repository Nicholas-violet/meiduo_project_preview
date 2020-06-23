from django.db import models

# Create your models here.
# 导入
from django.contrib.auth.models import AbstractUser
# 导入:
from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from django.conf import settings
from utils.BaseModel import BaseModel

# 我们重写用户模型类, 继承自 AbstractUser
class User(AbstractUser):
    """自定义用户模型类"""

    # 额外增加 mobile 字段
    mobile = models.CharField(max_length=11,unique=True,verbose_name='手机号')



    # 新增 email_active 字段
    # 用于记录邮箱是否激活, 默认为 False: 未激活
    email_active = models.BooleanField(default=False,
                                       verbose_name='邮箱验证状态')

    # 新增
    default_address = models.ForeignKey('Address',
                                        related_name='users',
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


    # 在 str 魔法方法中, 返回用户名称
    def __str__(self):
        return self.username


    def generate_verify_email_url(self):
        """
        生成邮箱验证链接
        :param user: 当前登录用户
        :return: verify_url
        """
        # 调用 itsdangerous 中的类,生成对象
        # 有效期: 1天
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                     expires_in=60 * 60 * 24)
        # 拼接参数
        data = {'user_id': self.id, 'email': self.email}
        # 加密生成 token 值, 这个值是 bytes 类型, 所以解码为 str:
        token = serializer.dumps(data).decode()
        # 拼接 url
        verify_url = settings.EMAIL_VERIFY_URL + token
        # 返回
        return verify_url

        # 定义验证函数:
    @staticmethod
    def check_verify_email_token(token):
        """
        验证token并提取user
        :param token: 用户信息签名后的结果
        :return: user, None
        """
        # 调用 itsdangerous 类,生成对象
        # 邮件验证链接有效期：一天
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                     expires_in=60 * 60 * 24)
        try:
            # 解析传入的 token 值, 获取数据 data
            data = serializer.loads(token)
        except BadData:
            # 如果传入的 token 中没有值, 则报错
            return None
        else:
            # 如果有值, 则获取
            user_id = data.get('user_id')
            email = data.get('email')

            # 获取到值之后, 尝试从 User 表中获取对应的用户
        try:
            user = User.objects.get(id=user_id,
                                    email=email)
        except Exception as e:
            # 如果用户不存在, 则返回 None
            return None
        else:
            # 如果存在则直接返回
            return user



# 增加地址的模型类, 放到User模型类的下方:
class Address(BaseModel):
    """
    用户地址
    """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='addresses',
                             verbose_name='用户')

    province = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='province_addresses',
                                 verbose_name='省')

    city = models.ForeignKey('areas.Area',
                             on_delete=models.PROTECT,
                             related_name='city_addresses',
                             verbose_name='市')

    district = models.ForeignKey('areas.Area',
                                 on_delete=models.PROTECT,
                                 related_name='district_addresses',
                                 verbose_name='区')

    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20,
                           null=True,
                           blank=True,
                           default='',
                           verbose_name='固定电话')

    email = models.CharField(max_length=30,
                             null=True,
                             blank=True,
                             default='',
                             verbose_name='电子邮箱')

    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']












