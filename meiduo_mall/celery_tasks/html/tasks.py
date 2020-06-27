
import os

from django.conf import settings
from django.template import loader
from goods.utils import get_categories,get_goods_and_spec

from celery_tasks.main import celery_app

# ========定义一个函数，实现渲染sku商品详情页面===========
@celery_app.task(name='generate_static_sku_detail_html')
def generate_static_sku_detail_html(sku_id):

    # 分组频道参数
    categories = get_categories()

    goods, sku, specs = get_goods_and_spec(sku_id)

    # =================模版渲染===================
    # 构建模版参数
    context = {
        'categories': categories, # 用于构建详情页面商品频道
        'goods': goods, # 当前sku商品的spu商品（Goods模型类）
        'sku': sku,
        'specs': specs # 传入的是当前sku商品从属的spu拥有的规格及其选项
    }

    # 获取模版
    template = loader.get_template('detail.html')
    # 调用模版渲染函数，得出完整的html页面
    sku_html_text = template.render(context=context)
    # 写入静态文件
    file_path = os.path.join(
        settings.GENERATED_STATIC_HTML_DIR,
        'goods/' + str(sku_id) + '.html' # goods/16.html
    )
    with open(file_path, 'w') as f:
        f.write(sku_html_text)

if __name__ == "__main__":
    for num in range(1, 17):
        generate_static_sku_detail_html(num)

