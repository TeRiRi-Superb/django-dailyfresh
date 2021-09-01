from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse
from django.views.generic import View
from django_redis import get_redis_connection
from apps.Goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods
from apps.Users.models import Address
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime
from django.db import transaction
from django.conf import settings
from alipay import AliPay
import os


class PlaceView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user

        sku_ids = request.POST.getlist('sku_id')

        total_count = 0
        total_price = 0
        skus = []
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)

            conn = get_redis_connection('default')
            key = f'cart_{user.id}'
            count = conn.hget(key, sku_id)
            price =sku.price
            amount = price * int(count)
            # 总价格和总数量
            total_count += int(count)
            total_price += amount

            sku.amount = amount
            sku.count = int(count)

            skus.append(sku)

        addr = Address.object.filter(user=user)

        freight = 10

        payment = total_price + freight

        sku_con = ','.join(sku_ids)

        context = {
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'addr': addr,
            'payment': payment,
            'freight': freight,
            'sku_con': sku_con,
        }

        return render(request, 'order.html', context)


class CommitView(View):
    # sql事务
    @transaction.atomic
    def post(self, request):

        user = request.user

        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        addr_id = request.POST.get('add_id')
        pay_id = request.POST.get('pay_id')
        skus = request.POST.get('skus')

        if not all([addr_id, pay_id, skus]):
            return JsonResponse({'res': 1, 'errmsg': '数据不全'})

        skus_id = skus.split(',')

        if pay_id not in OrderInfo.PAY_METHOD_DIC.keys():
            return JsonResponse({'res': 2, 'errmsg': '无效支付方式'})

        try:
            addr = Address.object.get(id=addr_id)
        except addr.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '无效地址'})

        # todo:订单核心业务
        order_id = datetime.now().strftime('%Y%m%d%H%M%S')+str(user.id)

        tr_price =10

        total_count = 0
        total_price = 0

        # todo:创建保存点
        save_id = transaction.savepoint()

        # 创建订单表
        order = OrderInfo.objects.create(order_id=order_id, pay_method=pay_id, product_count=total_count, product_price=total_price, transit_price=tr_price, user=user, addr=addr, )

        conn = get_redis_connection('default')
        key = f'cart_{user.id}'

        # todo:循环购物车传过来的商品id 创建订单商品
        for sku_id in skus_id:
            for i in range(3):
                try:
                    sku = GoodsSKU.objects.get(id=sku_id)
                except sku.DoesNotExist:
                    # todo:出错 事务回滚到保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                count = conn.hget(key, sku_id)



                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '库存不足'})

                # todo：更新商品库存 和销量 乐观锁
                origin_stock = sku.stock
                new_stock = origin_stock - int(count)
                new_sales = origin_stock + sku.sales

                # todo:在更新时判断 之前取得的库存是否和现在相同 加乐观锁 返回更新的条数
                new_num = GoodsSKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)

                if new_num == 0:
                    # todo:尝试三次 若三次都没下单成功就失败
                    if i == 2:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 7, 'errmsg': '下单失败'})
                    continue

                OrderGoods.objects.create(
                    count=count,
                    price=sku.price,
                    product=sku,
                    order_info=order
                )

                amount = int(count)*sku.price

                total_count += int(count)
                total_price += amount

                break

        # todo:更新订单表
        order.product_count = total_count
        order.product_price = total_price
        order.save()

        # todo: 传列表参时 参数前加* [1,2] (key, *[1,2]) 相当于 (key, 1，2)
        conn.hdel(key, *skus_id)
        return JsonResponse({'res': 5, 'message': '订单创建成功', })


class OrderPayView(View):

    def post(self, request):
        # todo:判断是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # todo:接收参数 判断参数
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '参数为空'})

        # 查询订单
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=3, order_status=1)
        except order.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单不存在'})

        private_key = open('apps/order/private2048.txt').read()
        public_key = open('apps/order/alipay_public_key.pem').read()

        # 初始化api
        alipay = AliPay(
            appid="2021000117695387",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=str(private_key),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=str(public_key),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False
        )

        subject = "iphone 11 pro"

        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        total_amount = order.product_price + order.transit_price  # DecimalField类型 会转换从json类型

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=str(order_id),
            total_amount=str(total_amount),
            subject=subject,
            return_url='https://www.baidu.com/',
            notify_url='https://example.com/notify'  # 可选, 不填则使用默认notify url
        )

        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string

        return JsonResponse({'res': 3, 'pay_url': pay_url})


class PaySearchView(View):
    '''
    订单状态查询
    '''
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # todo:接收参数 判断参数
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '参数为空'})

        # 查询订单
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, pay_method=3, order_status=1)
        except order.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单不存在'})

        private_key = open('apps/order/private2048.txt').read()
        public_key = open('apps/order/alipay_public_key.pem').read()

        # 初始化api
        alipay = AliPay(
            appid="2021000117695387",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=str(private_key),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=str(public_key),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False
        )

        respone = alipay.api_alipay_trade_query(order_id)

        code = respone.get('code')
        while True:
            if code == '10000' and respone.get('trade_status') == 'TRADE_SUCCESS':

                trade_no = respone.get('trade_no')

                order.trance_num = trade_no
                order.order_status = 4
                order.save()

                return JsonResponse({'res': 3, 'success': '订单已支付'})

            elif code == '40004' or (code == 10000 and respone.get('trade_status') == 'WAIT_BUYER_PAY'):
                import time
                time.sleep(5)
                continue
            else:
                print(code)
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})


class CommentView(LoginRequiredMixin, View):
    """订单评论"""

    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except:
            return redirect(reverse('user:userorder'))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_status_dic[order.order_status]

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_info=order)
        for order_sku in order_skus:
            amount = order_sku.count * order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, "order_comment.html", {"order": order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:userorder"))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            sku_id = request.POST.get("sku_%d" % i)  # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '')  # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order_info=order, product_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5  # 已完成
        order.save()

        return redirect(reverse("user:userorder", kwargs={"page": 1}))

