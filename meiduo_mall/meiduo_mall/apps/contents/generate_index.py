from django.template import loader
import os
from django.conf import settings


def generate_static_index_html():




    # 第二部分: 模板渲染部分:========================================================
    # 把上面两部分获取的有序字典和字典作为变量,拼接新的字典 context
    context = {
        'categories': None,
        'contents': None
    }


    # =====================获取模板,把数据添加进去生成页面====================
    # 获取末班,然后吧数据加载进去
    template = loader.get_template('index.html')

    html_text = template.render(context)

    # 拼接行的index.html模板生成的保存路径
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')

    # 以写的方式打开文件,将渲染之后的模板重新生成,带入到文件中
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)





