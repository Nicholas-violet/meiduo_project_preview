from django.shortcuts import render

# Create your views here.
from django.views import View
from areas.models import Area
from django import http

class ProvinceAreasView(View):
    """省级地区"""

    def get(self, request):
        """提供省级地区数据
        1.查询省级数据
        2.序列化省级数据
        3.响应省级数据
        4.补充缓存逻辑
        """


        try:
            # 1.查询省级数据
            province_model_list = Area.objects.filter(parent__isnull=True)

            # 2.整理省级数据
            province_list = []
            for province_model in province_model_list:
                province_list.append({'id': province_model.id,
                                      'name': province_model.name})

        except Exception as e:
              # 如果报错, 则返回错误原因:
            return http.JsonResponse({'code': 400,
                                 'errmsg': '省份数据错误'})

        # 3.返回整理好的省级数据
        return http.JsonResponse({'code': 0,
                             'errmsg': 'OK',
                             'province_list': province_list})