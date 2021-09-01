from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from db.base_model import BaseModel


class User(AbstractUser, BaseModel):


    def generate_active_token(self):
        '''生成用户签名字符串'''
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': self.id}
        token = serializer.dumps(info)
        return token.decode()

    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class AddressModel(models.Manager):
    '''self.model: 表示当前引用的是哪个模型类
        Address.object.get
        可以直接写 self.get
        地址模型管理器类的使用场景
        1.改变原有的查询集结果
        2.封装方法：用户操作对应的模型类的操作
    '''
    def get_default_address(self, user):
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            address = None

        return address



class Address(BaseModel):
    user = models.ForeignKey('User', verbose_name='所属账户', on_delete=models.DO_NOTHING)
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=50, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, verbose_name='邮编')
    phone = models.CharField(max_length=11, verbose_name='电话号码')
    is_default = models.BooleanField(default='True', verbose_name='默认收货地址')

    object = AddressModel()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name