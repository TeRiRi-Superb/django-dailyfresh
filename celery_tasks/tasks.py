from celery import Celery
from django.core.mail import send_mail
from django.conf import settings
import os
import django

# 初始化celery需要的配置文件
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "day_project.settings")
django.setup()
# 实例化对象
app = Celery('celery_tasks.tasks', broker='redis://:123456@127.0.0.1:6379/8')

from apps.Goods.models import GoodsType, GoodsBanner, IndexBanner, TypeShow
from django.template import loader


@app.task
def send_register_email(username, token, email):
    message = ''
    h_message = f'<h1>{username}欢迎注册天天生鲜会员</h1>请点击以下链接激活账户<br/>http://127.0.0.1:8000/user/active/{token}'
    send_mail(settings.EMAIL_SUBJECT_PREFIX, message, settings.EMAIL_HOST_USER, [email], html_message=h_message)


# 创建任务函数
@app.task
def static_html():
    # 查询商品种类
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

    # 查询购物车
    # 购物车中商品数量

    content = {
        'type': types,
        'banner_type': banner_type,
        'safe_type': safe_type,
    }

    # 加载静态化页面
    static = loader.get_template('static_main.html')
    # 渲染上下文
    html = static.render(content)

    # 写保存路径
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')

    # 生成静态化文件
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(html)
