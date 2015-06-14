from django import forms

import autocomplete_light

from .models import OrderDetail, Customer


class OrderDetailForm(forms.ModelForm):
    class Meta:
        model = OrderDetail
        exclude = []

    customer = autocomplete_light.forms.ModelChoiceField(Customer.objects.all(), widget=autocomplete_light.ChoiceWidget('OrderDetailsAutocomplete'), label='Клиент')
