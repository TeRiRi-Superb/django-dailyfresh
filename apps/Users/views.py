from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from apps.Goods.models import GoodsSKU
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from apps.Users.models import User, Address
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.contrib.auth.mixins import LoginRequiredMixin
from itsdangerous import SignatureExpired
from django.conf import settings
from celery_tasks.tasks import send_register_email
from django_redis import get_redis_connection
from apps.order.models import OrderInfo, OrderGoods
from django.core.paginator import Paginator

# Create your views here.


def register(request):
    '''
    通过判断请求的类型 将显示页面和注册判断写进一个函数
    get类型就显示页面
    post类型就请求注册
    '''
    if request.method == 'GET':
        return render(request, 'register.html')

    else:
        username = request.POST.get('user_name')
        passwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([username, passwd, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名重复'})
        # 保存用户
        user = User.objects.create_user(username=username, password=passwd, email=email)
        # 默认是激活，需要手动改为0
        user.is_active = 0
        user.save()

        return redirect(reverse('goods:main'))


# def login(request):
#     return render(request, 'login.html')


# 类试图的写法
class RedirectLine(View):
    '''注册类'''
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        passwd = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([username, passwd, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名重复'})
        # 保存用户
        user = User.objects.create_user(username=username, password=passwd, email=email)
        # 默认是激活，需要手动改为0
        user.is_active = 0
        user.save()

        # 创建一个token 加密用户数据
        serializer = Serializer(settings.SECRET_KEY, 3600)
        # 设置需要加密信息
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        # 原数据是byte类型 转码成utf8
        token = token.decode()

        # 发送邮件
        # message = ''
        # h_message = f'<h1>{username}欢迎注册天天生鲜会员</h1>请点击以下链接激活账户<br/>http://127.0.0.1:8000/user/active/{token}'
        # send_mail(settings.EMAIL_SUBJECT_PREFIX, message, settings.EMAIL_HOST_USER, [email], html_message=h_message)

        # 异步发送邮件
        send_register_email.delay(username, token, email)

        return redirect(reverse('goods:main'))


# 解密用户数据
class ActiveView(View):
    '''激活账户'''
    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            user_id = info['confirm']

            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

        except SignatureExpired as e:
            return HttpResponse('已过期')

        return HttpResponse('激活成功')


class LoginView(View):
    '''登录类'''
    def get(self, request):
        # 检查是否有cookie
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        username = request.POST.get('username')
        pwd = request.POST.get('pwd')

        # 使用内置的认证系统
        user = authenticate(username=username, password=pwd)

        if user is not None:
            if user.is_active:
                # 使用内置的方法记录登录状态
                login(request, user)
                #
                next_url = request.GET.get('next', reverse('goods:main'))

                remember = request.POST.get('remember')

                response = redirect(next_url)
                # 判断是否勾选了‘记住用户名’
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '账户密码错误'})


class UserInfo(LoginRequiredMixin, View):
    '''用户中心'''
    def get(self, request):

        user = request.user

        address = Address.object.get_default_address(user=user)

        con = get_redis_connection('default')

        history_key = f'history_{user.id}'
        sku_id = con.lrange(history_key, 0, 4)

        sku_ls = []
        for id in sku_id:
            goods = GoodsSKU.objects.get(id=id)
            sku_ls.append(goods)

        content = {'info': 'info', 'address': address, 'goods': sku_ls}

        return render(request, 'user_center_info.html', content)


class UserOrder(LoginRequiredMixin, View):
    '''个人订单'''
    def get(self, request, page):
        user = request.user

        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        for order in orders:
            order_skus = OrderGoods.objects.filter(order_info_id=order.id)

            for order_sku in order_skus:

                amount = order_sku.count * order_sku.price
                order_sku.amount = amount

            status_name = OrderInfo.ORDER_status_dic[order.order_status]

            order.status_name = status_name
            order.order_skus = order_skus

        page = int(page)
        paginator = Paginator(orders, 1)

        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page < 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        order_pages = paginator.page(page)

        context = {
            'order_pages': order_pages,
            'pages': pages,
            'order': 'order'
            }


        return render(request, 'user_order.html', context)


class UserAddress(LoginRequiredMixin, View):
    '''地址'''
    def get(self, request):
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except:
        #     address = None

        address = Address.object.get_default_address(user=user)

        return render(request, 'user_address.html', {'site': 'site', 'address': address})

    def post(self, request):
        recipient = request.POST.get('recipient')
        address = request.POST.get('address')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        user = request.user

        if not all([recipient, zip_code, address, phone]):
            return render(request, 'user_address.html', {'errmsg': '信息不完整'})

        # try:
        #     addr = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     addr = None

        addr = Address.object.get_default_address(user=user)

        if addr:
            is_defualt = False
        else:
            is_defualt = True

        Address.object.create(user=user,
                               receiver=recipient,
                               addr=address,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_defualt,
                               )

        return redirect(reverse('user:useraddress'))



class LogOut(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:main'))
