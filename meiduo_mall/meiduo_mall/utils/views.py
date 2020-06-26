from django.http import JsonResponse

def my_decorator(func):
    '''自定义的装饰器:判断是否登录'''
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            # 如果用户登录, 则进入这里,正常执行
            return func(request, *args, **kwargs)
        else:
            # 如果用户未登录,则进入这里,返回400的状态码
            return JsonResponse({'code':400,
                                 'errmsg':'请登录后重试'})
    return wrapper



class LoginRequiredMixin(object):
    '''自定义的Mixin扩展类'''

    # 重写的 as_view 方法
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        # 调用上面的装饰器进行过滤处理:
        return my_decorator(view)