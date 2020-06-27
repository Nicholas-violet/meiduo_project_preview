
# ===============================================================
# 以下只是作用于开发测试
import sys,os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo_mall.settings.dev')
# # 需要把外层meiduo_mall加入导包路径
sys.path.insert(0, '/Users/weiwei/Desktop/sz37_meiduo_mall/meiduo_mall')
# # 加载django环境
import django
django.setup()
# ===============================================================

from django.template import loader
from django.conf import settings
from goods.models import GoodsChannel,GoodsCategory,SKU,GoodsSpecification,SpecificationOption
from goods.models import SKUSpecification
from collections import OrderedDict
from copy import deepcopy

def get_breadcrumb(category):


    cats = {
        'cat1': None,
        'cat2': None,
        'cat3': None
    }

    # 如果category是1级分类，只要赋值cat1
    if category.parent is None:
        cats['cat1'] = category.name
    # 如果category是2级分类，只要赋值cat1，cat2
    elif category.parent.parent is None:
        cats['cat2'] = category.name
        cats['cat1'] = category.parent.name
    elif category.parent.parent.parent is None:
    # 如果category是3级分类，只要赋值cat1，cat2, cat3
        cats['cat3'] = category.name
        cats['cat2'] = category.parent.name
        cats['cat1'] = category.parent.parent.name

    return cats



def get_categories():
    # ============频道分组===========
    # categories = {} # python普通字典的键值对是无序的！
    categories = OrderedDict()  # 有序字典，键值对顺序是固定的；

    channels = GoodsChannel.objects.order_by(
        # order_by传入多个字段排序，如果group_id一样，按照sequence排
        'group_id',
        'sequence'
    )

    for channel in channels:
        # channel: 每一个频道对象

        # 模版参数中，第一次遍历到该分组，那么就在categories添加一个
        # 新的key(该key就是group_id)
        if channel.group_id not in categories:
            categories[channel.group_id] = {
                "channels": [],  # 当前频道组的1级分类
                "sub_cats": []  # 2级分类
            }

        # 构建当前分组的频道和分类信息
        cat1 = channel.category
        categories[channel.group_id]["channels"].append({
            "id": cat1.id,
            "name": cat1.name,
            "url": channel.url
        })

        # 所有父级分类是cat1这个1级别分类的2级分类
        cat2s = GoodsCategory.objects.filter(
            parent=cat1
        )
        for cat2 in cat2s:
            # cat2: 每一个2级分类对象
            cat3_list = []  # 根据cat2这个2级分类获取3级分类

            cat3s = GoodsCategory.objects.filter(
                parent=cat2
            )
            for cat3 in cat3s:
                # cat3: 每一个3级分类对象
                cat3_list.append({
                    "id": cat3.id,
                    "name": cat3.name
                })

            categories[channel.group_id]['sub_cats'].append({
                "id": cat2.id,
                "name": cat2.name,
                "sub_cats": cat3_list  # 3级分类
            })

    return categories


def get_goods_and_spec(sku_id):
    # 当前SKU商品
    sku = SKU.objects.get(pk=sku_id)
    # 记录当前sku的选项组合
    cur_sku_spec_options = SKUSpecification.objects.filter(sku=sku).order_by('spec_id')
    cur_sku_options = [] # [1,4,7]
    for temp in cur_sku_spec_options:
        # temp是SKUSpecification中间表对象
        cur_sku_options.append(temp.option_id)


    # Goods对象(SPU商品)
    goods = sku.goods
    # 罗列出和当前sku同类的所有商品的选项和商品id的映射关系
    # {(1,4,7):1, (1,3,7):2}
    sku_options_mapping = {}
    skus = SKU.objects.filter(goods=goods)
    for temp_sku in skus:
        # temp_sku:每一个sku商品对象
        sku_spec_options = SKUSpecification.objects.filter(sku=temp_sku).order_by('spec_id')
        sku_options = []
        for temp in sku_spec_options:
            sku_options.append(temp.option_id) # [1,4,7]
        sku_options_mapping[tuple(sku_options)] = temp_sku.id # {(1,4,7):1}



    # specs当前页面需要渲染的所有规格
    specs = GoodsSpecification.objects.filter(goods=goods).order_by('id')
    for index, spec in enumerate(specs):
        # spec每一个规格对象
        options = SpecificationOption.objects.filter(spec=spec)

        # 每一次选项规格的时候，准备一个当前sku的选项组合列表，便于后续使用
        temp_list = deepcopy(cur_sku_options) # [1,4,7]

        for option in options:
            # 每一个选项，动态添加一个sku_id值，来确定这个选项是否属于当前sku商品

            temp_list[index] = option.id # [1,3,7] --> sku_id?

            option.sku_id = sku_options_mapping.get(tuple(temp_list)) # 找到对应选项组合的sku_id

        # 在每一个规格对象中动态添加一个属性spec_options来记录当前规格有哪些选项
        spec.spec_options = options

    return goods, sku, specs


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



























