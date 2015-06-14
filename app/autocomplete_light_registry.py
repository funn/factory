import autocomplete_light
from .models import OrderDetail, Customer

class OrderDetailsAutocomplete(autocomplete_light.AutocompleteModelBase):
    choices = Customer.objects.all()
    search_fields = ['name', 'phone']
    model = OrderDetail

autocomplete_light.register(OrderDetailsAutocomplete, add_another_url_name='admin:app_customer_add')
