from collections import OrderedDict
from django.conf import settings
from django.template import loader
import os
import time
from goods.models import GoodsChannel, GoodsCategory
from contents.models import ContentCategory, Content

# 添加生成 html 文件的函数:
def generate_static_index_html():
    # =====================生成上面字典格式数据=======================
    # 第一部分: 从数据库中取数据:
    # 定义一个有序字典对象
    categories = OrderedDict()

    # 对 GoodsChannel 进行 group_id 和 sequence 排序, 获取排序后的结果:
    channels = GoodsChannel.objects.order_by('group_id',
                                             'sequence')

    # 遍历排序后的结果: 得到所有的一级菜单( 即,频道 )
    for channel in channels:
        # 从频道中得到当前的 组id
        group_id = channel.group_id

        # 判断: 如果当前 组id 不在我们的有序字典中:
        if group_id not in categories:
            # 我们就把 组id 添加到 有序字典中
            # 并且作为 key值, value值 是 {'channels': [], 'sub_cats': []}
            categories[group_id] =  {
                                     'channels': [],
                                     'sub_cats': []
                                    }

        # 获取当前频道的分类名称
        cat1 = channel.category

        # 给刚刚创建的字典中, 追加具体信息:
        # 即, 给'channels' 后面的 [] 里面添加如下的信息:
        categories[group_id]['channels'].append({
            'id':   cat1.id,
            'name': cat1.name,
            'url':  channel.url
        })

        # 根据 cat1 的外键反向, 获取下一级(二级菜单)的所有分类数据, 并遍历:
        cat2s = GoodsCategory.objects.filter(parent=cat1)
        # cat1.goodscategory_set.all()
        for cat2 in cat2s:
            # 创建一个新的列表:
            cat2.sub_cats = []
            cat3s = GoodsCategory.objects.filter(parent=cat2)
            # 根据 cat2 的外键反向, 获取下一级(三级菜单)的所有分类数据, 并遍历:
            for cat3 in cat3s:
                # 拼接新的列表: key: 二级菜单名称, value: 三级菜单组成的列表
                cat2.sub_cats.append(cat3)
            # 所有内容在增加到 一级菜单生成的 有序字典中去:
            categories[group_id]['sub_cats'].append(cat2)

    # =====================生成首页广告部分数据=======================
    # 我们定义一个字典, 里面将要存储广告内容部分:
    contents = {}
    # 从 ContentCategory 模型类中获取所有数据, 存放到 content_categories 中:
    content_categories = ContentCategory.objects.all()
    # 遍历刚刚获取的所有数据: 拿到每一个广告分类 cat:
    for cat in content_categories:
        # 根据广告分类的 外键反向
        # 获取广告内容中状态为 True 并且按 sequence 排序的部分,
        # 赋值给上面定义的字典, 快捷键(cat.key) 作为 key, 排序的部分作为value
        contents[cat.key] = Content.objects.filter(category=cat,
                                                   status=True).order_by('sequence')


    # 第二部分: 模板渲染部分:
    # 把上面两部分获取的有序字典和字典作为变量,拼接新的字典 context
    context = {
        'categories': categories,
        'contents': contents
    }

    # =====================获取模板,把数据添加进去生成页面====================
    # 根据导入的 loader 获取 'index.html' 模板
    template = loader.get_template('index.html')

    # 拿到模板, 然后将 context 渲染到模板中, 生成渲染过的模板
    html_text = template.render(context)

    # 我们拼接新的 index.html 模板将要生成的所在地地址:
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')

    # 以写的权限,将渲染过的模板重新生成, 写入到文件中.
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)