from django.conf.urls import include, url
from django.contrib import admin

from app.adminplus import AdminPlus
from app.views import AjaxChainedProducts

admin.site = AdminPlus()
admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ajax/chained-products/$', AjaxChainedProducts.as_view(), name='ajax_chained_products'),
    url(r'^autocomplete/', include('autocomplete_light.urls'))
]
