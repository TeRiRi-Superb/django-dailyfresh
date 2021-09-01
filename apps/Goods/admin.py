from django.contrib import admin
from apps.Goods.models import GoodsType, GoodsBanner, IndexBanner, GoodsSKU, Goods, TypeShow
from django.core.cache import cache
# Register your models here.


class IndexShowHtml(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        from celery_tasks.tasks import static_html
        static_html.delay()

        cache.delete('main_html_page')

    def delete_model(self, request, obj):
        super().delete_model(request, obj)

        from celery_tasks.tasks import static_html
        static_html.delay()

        cache.delete('main_html_page')


admin.site.register(GoodsType)
admin.site.register(GoodsBanner)
admin.site.register(IndexBanner)
admin.site.register(GoodsSKU)
admin.site.register(Goods)
admin.site.register(TypeShow)
