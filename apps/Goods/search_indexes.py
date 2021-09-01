from haystack import indexes
from .models import GoodsSKU


class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    # 类名必须为需要检索的Model_name+Index，这里需要检索GoodsSKU，所以创建GoodsSKUIndex
    text = indexes.CharField(document=True, use_template=True)  # 创建一个text字段

    def get_model(self):  # 重载get_model方法，必须要有！
        return GoodsSKU

    def index_queryset(self, using=None):
        return self.get_model().objects.all()