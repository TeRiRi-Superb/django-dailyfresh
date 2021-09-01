from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField


# Create your models here.
class GoodsType(BaseModel):
    '''商品种类'''
    name = models.CharField(max_length=20, verbose_name='种类')
    logo = models.CharField(max_length=20, verbose_name='标签')
    image = models.ImageField(upload_to='type', verbose_name='商品类型图片')

    class Meta:
        db_table = 'df_goods_type'
        verbose_name = '商品种类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsSKU(BaseModel):
    '''商品模型类'''
    static_choice = (
        (0, '下线'),
        (1, '上线'),
    )

    type = models.ForeignKey('GoodsType', verbose_name='商品种类', on_delete=models.DO_NOTHING)
    goods = models.ForeignKey('Goods', verbose_name='商品SPU', on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=20, verbose_name='商品名称')
    content = models.CharField(max_length=50, verbose_name='商品简介')
    price = models.DecimalField(max_length=256, max_digits=10, decimal_places=2, verbose_name='商品价格')
    unite = models.CharField(max_length=10, verbose_name='商品单位')
    stock = models.IntegerField(default=1, verbose_name='商品库存')
    sales = models.IntegerField(default=0, verbose_name='商品销量')
    image = models.ImageField(upload_to='goods', verbose_name='商品类型图片')
    status = models.SmallIntegerField(default=1, choices=static_choice, verbose_name='商品状态')

    class Meta:
        db_table = 'df_goods_SKU'
        verbose_name = '商品SKU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Goods(BaseModel):
    '''商品SPU'''
    name = models.CharField(max_length=20, verbose_name='商品名称')
    content = HTMLField(blank=True, verbose_name='商品详情')

    class Meta:
        db_table = 'df_goods_SPU'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsImage(BaseModel):
    image = models.ImageField(upload_to='products', verbose_name='商品图片路径')
    product = models.ForeignKey(GoodsSKU, verbose_name='商品', on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'goods_image'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name


class GoodsBanner(BaseModel):
    image = models.ImageField(upload_to='banner', verbose_name='轮播图片')
    index = models.SmallIntegerField(default=0, verbose_name='轮播索引')
    goods = models.ForeignKey(GoodsSKU, verbose_name='商品', on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'goods_banner'
        verbose_name = '首页轮播商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.goods.name


class TypeShow(BaseModel):
    DISPLAY_TYPE_CHOICES = (
        (0, '文字'),
        (1, '图片')
    )
    display_type = models.SmallIntegerField(choices=DISPLAY_TYPE_CHOICES, default=1, verbose_name='展示类型')
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')
    goods = models.ForeignKey(GoodsSKU, verbose_name='商品SKU', on_delete=models.DO_NOTHING)
    goods_type = models.ForeignKey(GoodsType, verbose_name='商品种类', on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'goods_show'
        verbose_name = '分类商品展示'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.goods_type.name


class IndexBanner(BaseModel):
    name = models.CharField(max_length=20, verbose_name='活动名称')
    image = models.ImageField(upload_to='banner', verbose_name='活动图片')
    index = models.SmallIntegerField(default=0, verbose_name='轮播索引')
    url = models.CharField(max_length=256, verbose_name='活动链接')

    class Meta:
        db_table = 'Index_banner'
        verbose_name = '主页活动商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
