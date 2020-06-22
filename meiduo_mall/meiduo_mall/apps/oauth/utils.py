# 导入:
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings

def generate_access_token(openid):
    """对传入的 openid 进行加密处理, 返回 token"""

        # QQ 登录保存用户数据的 token 有效期
    # settings.SECRET_KEY: 加密使用的秘钥
    # 过期时间: 600s = 10min
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                 expires_in=600)
    data = {'openid': openid}

    # 对 dict 进行加密
    token = serializer.dumps(data)

    # 加密完之后, 解码返回.
    return token.decode()


# 导入:
from itsdangerous import BadData


# 定义函数, 检验传入的 access_token 里面是否包含有 openid
def check_access_token(access_token):
    """
    检验用户传入的 token
    :param token: token
    :return: openid or None
    """

    # 调用 itsdangerous 中的类, 生成对象
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                 expires_in=600)
    try:
        # 尝试使用对象的 loads 函数
        # 对 access_token 进行反序列化( 类似于解密 )
       # 查看是否能够获取到数据:
       data = serializer.loads(access_token)

    except BadData:
        # 如果出错, 则说明 access_token 里面不是我们认可的.
        # 返回 None
        return None
    else:
        # 如果能够从中获取 data, 则把 data 中的 openid 返回
        return data.get('openid')
