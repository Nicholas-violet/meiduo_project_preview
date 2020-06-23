from django.shortcuts import render

# Create your views here.
from django.views import View
from areas.models import Area
from django import http
# 导入:
from django.core.cache import cache

class ProvinceAreasView(View):

    def get(self, request):

        # 增加: 判断是否有缓存
        province_list = cache.get('province_list')

        if not province_list:
            try:
                province_model_list = Area.objects.filter(parent__isnull=True)

                province_list = []
                for province_model in province_model_list:
                    province_list.append({'id': province_model.id,
                                          'name': province_model.name})

                # 增加: 缓存省级数据
                cache.set('province_list', province_list, 3600)
            except Exception as e:
                return http.JsonResponse({'code': 400,
                                      'errmsg': '省份数据错误'})

        return http.JsonResponse({'code': 0,
                             'errmsg': 'OK',
                             'province_list': province_list})