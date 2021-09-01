from django.shortcuts import render, reverse, redirect
from django.views.generic import View
from django.core.cache import cache
from .models import GoodsType, GoodsBanner, IndexBanner, TypeShow, GoodsSKU
from django.core.paginator import Paginator
from apps.order.models import OrderGoods
from django_redis import get_redis_connection

# Create your views here.

# 主页信息
class MainView(View):
    def get(self, request):
        content = cache.get('main_html_page')
        # 查询商品种类
        if content is None:
            print('设置缓存')
            types = GoodsType.objects.all()

            # 查询轮播图种类 order_by按什么字段排序默认是升序降序在字段前加-号
            banner_type = GoodsBanner.objects.all().order_by('index')

            # 促销商品种类
            safe_type = IndexBanner.objects.all().order_by('index')

            # 查询商品展示种类
            for ty in types:
                image_show = TypeShow.objects.filter(goods_type=ty, display_type=1).order_by('index')
                con_show = TypeShow.objects.filter(goods_type=ty, display_type=0).order_by('index')

                # 给types动态增加属性
                ty.image_show = image_show
                ty.con_show = con_show

            content = {
                'type': types,
                'banner_type': banner_type,
                'safe_type': safe_type,
            }

            cache.set('main_html_page', content, 3600)
        # 查询购物车
        # 购物车中商品数量

        user = request.user

        # 用户没有登录 购物车商品数量默认显示0
        cart_num = 0
        if user.is_authenticated:
            con = get_redis_connection('default')
            car_key = f'cart_{user.id}'
            cart_num = con.hlen(car_key)

        content.update(cart_num=cart_num)

        return render(request, 'main.html', content)


# 商品详情页信息
class DetailView(View):
    def get(self, request, goods_id):
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except sku.DoesNotExist:
            return redirect(reverse('goods:main'))

        types = GoodsType.objects.all()
        order = OrderGoods.objects.filter(product=sku).exclude(comment='')
        sku_type = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]
        same_spu = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)


        user = request.user

        # 用户没有登录 购物车商品数量默认显示0
        cart_num = 0
        if user.is_authenticated:
            con = get_redis_connection('default')
            car_key = f'cart_{user.id}'
            cart_num = con.hlen(car_key)

            conn = get_redis_connection('default')
            history_key = f'history_{user.id}'
            conn.lrem(history_key, 0, goods_id)
            conn.lpush(history_key, goods_id)
            conn.ltrim(history_key, 0, 4)

        context = {
            'sku': sku,
            'types': types,
            'order': order,
            'sku_type': sku_type,
            'cart_num': cart_num,
            'same_spu': same_spu
        }

        return render(request, 'detail.html', context)


# 商品列表页信息
class ListView(View):
    def get(self, request, type_id, page):
        try:
            type = GoodsType.objects.get(id=type_id)

        except type.DoesNotExist:
            return redirect(reverse('goods:main'))

        # 商品排序
        sort = request.GET.get('sort')
        if sort == 'defualt':
            list_product = GoodsSKU.objects.filter(type=type).order_by('-id')
        elif sort == 'price':
            list_product = GoodsSKU.objects.filter(type=type).order_by('-price')
        else:
            list_product = GoodsSKU.objects.filter(type=type).order_by('-sales')

        # 获取商品分类信息
        sku_type = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]
        types = GoodsType.objects.all()

        user = request.user

        # 用户没有登录 购物车商品数量默认显示0
        cart_num = 0
        if user.is_authenticated:
            con = get_redis_connection('default')
            car_key = f'cart_{user.id}'
            cart_num = con.hlen(car_key)

        # 商品分页显示
        paginator = Paginator(list_product, 1)

        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages+1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page < 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        try:
            page = int(page)
        except:
            page = 1

        if page > paginator.num_pages:
            page = 1

        skus_page = paginator.page(page)



        context = {
            'type': type,
            'types': types,
            'sort': sort,
            'cart_num': cart_num,
            'sku_type': sku_type,
            'skus_page': skus_page,
            'pages': pages,
        }


        return render(request, 'list.html', context)