def get_breadcrumb(category):

    # 定义一个字典:
    dict = {
        'cat1':'',
        'cat2':'',
        'cat3':''
    }
    # 判断 category 是哪一个级别的.
    # 注意: 这里的 category 是 GoodsCategory对象
    if category.parent is None:
        # 当前类别为一级类别
        dict['cat1'] = category.name
    # 因为当前这个表示自关联表, 所以关联的对象还是自己:
    elif category.parent.parent is None:
        # 当前类别为二级
        dict['cat2'] = category.name
        dict['cat1'] = category.parent.name
    else:
        # 当前类别为三级
        dict['cat3'] = category.name
        dict['cat2'] = category.parent.name
        dict['cat1'] = category.parent.parent.name

    return dict