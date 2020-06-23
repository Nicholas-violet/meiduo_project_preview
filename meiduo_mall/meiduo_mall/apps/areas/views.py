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



class SubAreasView(View):
    """子级地区：市和区县"""

    def get(self, request, pk):
        """提供市或区地区数据
        1.查询市或区数据
        2.序列化市或区数据
        3.响应市或区数据
        4.补充缓存数据
        """
        # 判断是否有缓存
        sub_data = cache.get('sub_area_' + pk)

        if not sub_data:

            # 1.查询市或区数据
            try:
                sub_model_list = Area.objects.filter(parent=pk)
                # 查询市或区的父级
                parent_model = Area.objects.get(id=pk)


                # 2.序列化市或区数据
                sub_list = []
                for sub_model in sub_model_list:
                    sub_list.append({'id': sub_model.id,
                                     'name': sub_model.name})

                sub_data = {
                    'id':parent_model.id, # pk
                    'name':parent_model.name,
                    'subs': sub_list
                }

                # 缓存市或区数据
                cache.set('sub_area_' + pk, sub_data, 3600)
            except Exception as e:
                return http.JsonResponse({'code': 400,
                                     'errmsg': '城市或区县数据错误'})

        # 3.响应市或区数据
        return http.JsonResponse({'code': 0,
                             'errmsg': 'OK',
                             'sub_data': sub_data})







