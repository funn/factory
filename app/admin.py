from datetime import datetime

from django.contrib import admin

from .models import *
from .forms import OrderDetailForm
from .views import monthly_schedule


@admin.register(Customer, site=admin.site)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')
    search_fields = ('name', 'phone')


@admin.register(ProductCategory, site=admin.site)
class ProductCategoryAdmin(admin.ModelAdmin):
    def count(self, obj):
        return Product.objects.filter(product_category_id=obj.id).count()
    count.short_description = 'Количество товаров'

    list_display = ('name', 'count')


@admin.register(Product, site=admin.site)
class ProductAdmin(admin.ModelAdmin):
    list_editable = ('quantity',)
    list_display = ('name', 'product_category', 'price', 'quantity')
    list_filter = ('product_category',)


@admin.register(OrderDetail, site=admin.site)
class OrderDetailAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('customer', 'category', 'product', 'quantity', 'cost', 'date', 'barber')
    form = OrderDetailForm


admin.site.register(Barber)
admin.site.register_view('monthly_schedule/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/', 'Расписание на месяц', view=monthly_schedule, default_view='monthly_schedule/{}/{}/'.format(datetime.now().year, datetime.now().month), urlname='monthly_schedule')
