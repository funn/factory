import autocomplete_light
from .models import OrderDetail, Customer

class CustomerAutocomplete(autocomplete_light.AutocompleteModelBase):
    choices = Customer.objects.all()
    search_fields = ['name', 'phone']

autocomplete_light.register(CustomerAutocomplete, add_another_url_name='admin:app_customer_add')
