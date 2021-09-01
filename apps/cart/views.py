from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from apps.Goods.models import GoodsSKU
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin


class CartView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user

        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'
        sku_dict = conn.hgetall(cart_key)

        total_count = 0
        sku_list = []
        for sku_id, count in sku_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)

            ment = sku.price * int(count)
            sku.count = int(count)
            sku.ment = ment
            sku_list.append(sku)

            total_count += int(count)

        context = {
            'sku_list': sku_list,
            'total_count': total_count,
        }

        return render(request, 'cart.html', context)


class CartAddView(View):

    def post(self, request):

        user = request.user

        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        if not all([sku_id, count]):
            return JsonResponse({'res': 0, 'errmsg': '数据不完整'})

        try:
            count = int(count)
        except:
            return JsonResponse({'res': 1, 'errmsg': '数据错误'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except sku.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '查不到商品'})

        sku_stock = sku.stock

        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'
        # 如果hget没有查到 hget返回None
        cart_non = conn.hget(cart_key, sku_id)

        # 如果redis中有对应的sku_id 就将sku_id对应的值相加
        if cart_non:
            count += int(cart_non)

        if count > sku_stock:
            return JsonResponse({'res': 3, 'errmsg': '库存不足'})

        conn.hset(cart_key, sku_id, count)

        cart_len = conn.hlen(cart_key)

        return JsonResponse({'res': 4, 'cart_len': cart_len, 'message': '添加成功'})


class UpCartView(View):
    def post(self, request):
        user = request.user

        if not user.is_authenticated:
            return JsonResponse({'res':0, 'errmsg':'没有登录'})

        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不全'})

        try:
            is_sku = GoodsSKU.objects.get(id=sku_id)
        except is_sku.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        try:
            count = int(count)
        except is_sku.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品数量出错'})

        sku_stock = is_sku.stock

        if sku_stock < int(count):
            return JsonResponse({'res': 4, 'count': sku_stock, 'errmsg': '库存不足'})

        conn = get_redis_connection('default')
        cart_key = f'cart_{user.id}'

        conn.hset(cart_key, sku_id, count)

        sku_dict = conn.hgetall(cart_key)
        total_count = 0
        for sku, count in sku_dict.items():
            total_count += int(count)

        return JsonResponse({'res': 5, 'message': '成功', 'total_count': total_count})


class DelCartView(View):
    def post(self, request):

        user = request.user

        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        sku_id = request.POST.get('sku_id')

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except sku.DoesNotExist:
            return JsonResponse({'res': 1, 'errmsg': '商品不存在'})

        conn = get_redis_connection('default')
        sku_key = f'cart_{user.id}'
        conn.hdel(sku_key, sku_id)
        print(sku_id)
        total_count = 0
        all_sku = conn.hgetall(sku_key)
        for id, count in all_sku.items():
            total_count += int(count)

        return JsonResponse({'res': 3, 'total_count': total_count, 'message': '成功'})