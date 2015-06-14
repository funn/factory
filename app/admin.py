from django.contrib import admin

from .models import *
from .forms import OrderDetailForm


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')
    search_fields = ('name', 'phone')


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    def count(self, obj):
        return Product.objects.filter(product_category_id=obj.id).count()
    count.short_description = 'Количество товаров'

    list_display = ('name', 'count')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_editable = ('quantity',)
    list_display = ('name', 'product_category', 'price', 'quantity')
    list_filter = ('product_category',)


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    list_display = ('customer', 'category', 'product', 'quantity', 'cost', 'date', 'barber')
    form = OrderDetailForm


admin.site.register(Barber)
