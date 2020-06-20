# 从你刚刚下载的包中导入 Celery 类
from celery import Celery


# 利用导入的 Celery 创建对象。这里的 'meiduo' 字符串可以使用别的字符串替换.
celery_app = Celery('meiduo')

# 将刚刚的 config 配置给 celery
# 里面的参数为我们创建的 config 配置文件:
celery_app.config_from_object('celery_tasks.config')

# 让 celery_app 自动捕获目标地址下的任务:
# 就是自动捕获 tasks
celery_app.autodiscover_tasks(['celery_tasks.sms'])