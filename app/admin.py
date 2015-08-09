from datetime import datetime

from django.contrib import admin

from .models import *
from .forms import OrderDetailForm
from .views import monthly_schedule, daily_schedule, create_appointment, edit_appointment


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

    formfield_overrides = {
        models.DecimalField: {'min_value': 0},
    }


@admin.register(OrderDetail, site=admin.site)
class OrderDetailAdmin(admin.ModelAdmin):
    exclude = ('appointment',)
    date_hierarchy = 'date'
    list_display = ('customer', 'category', 'product', 'quantity', 'cost', 'date', 'barber')
    form = OrderDetailForm

    formfield_overrides = {
        models.DecimalField: {'min_value': 0},
    }


admin.site.register(Barber)
admin.site.register_view('monthly_schedule/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/', 'Расписание на месяц', view=monthly_schedule, default_view='monthly_schedule/{}/{}/'.format(datetime.now().year, datetime.now().month), urlname='monthly_schedule')
admin.site.register_view('daily_schedule/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/', 'Расписание на день', view=daily_schedule, default_view='daily_schedule/{}/{}/{}'.format(datetime.now().year, datetime.now().month, datetime.now().day), urlname='daily_schedule')
admin.site.register_view('create_appointment/(?P<barber>[0-9]{1,2})/', view=create_appointment, visible=False, urlname='create_appointment')
admin.site.register_view('edit_appointment/(?P<appointment>[0-9]*)/', view=edit_appointment, visible=False, urlname='edit_appointment')
