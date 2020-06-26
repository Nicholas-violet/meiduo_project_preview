"""
自定义文件存储后端，使得我们的image.url得出的结果前面拼接完整的fdfs请求url前缀
"""
# Storage：存储后端基类
from django.core.files.storage import Storage
from django.conf import settings
class FastDFSStorage(Storage):
    def open(self, name, mode='rb'):
        # 如果需要把上传的文件存储django本地，则需要在本地打开一个文件
        return None # 把图片上传fdfs，不是保存本地
    def save(self, name, content, max_length=None):
        # 保存文件逻辑：把文件上传到fdfs服务器上
        pass
    def url(self, name):
        # 该函数决定了，ImageField.url的结果
        # name: 当前字段在数据库中存储的值
        # name = group1/M00/00/02/CtM3BVrPB4GAWkTlAAGuN6wB9fU4220429
        # "http://image.meiduo.site:8888/" + name
        return settings.FDFS_URL + name
