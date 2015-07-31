from django import forms
from django.conf import settings

import autocomplete_light

from smart_selects.form_fields import ChainedModelChoiceField

from .models import OrderDetail, Customer, ProductCategory, Product


class OrderDetailForm(forms.ModelForm):
    class Meta:
        model = OrderDetail
        exclude = []

    customer = autocomplete_light.forms.ModelChoiceField(Customer.objects.all(), widget=autocomplete_light.ChoiceWidget('CustomerAutocomplete'), label='Клиент')


class MonthlyScheduleForm(forms.Form):
    def __init__(self, *args, **kwargs):
        days = kwargs.pop('days')
        if days <= 0:
            raise ValueError('Days should be a positive value more than zero. days={}'.format(days))
        super(MonthlyScheduleForm, self).__init__(*args, **kwargs)
        for day in range(1, days+1):
            self.fields['day_{}'.format(day)] = forms.BooleanField(required=False)


class CreateAppointmentForm(forms.Form):
    customer = autocomplete_light.forms.ModelChoiceField(Customer.objects.all(), widget=autocomplete_light.ChoiceWidget('CustomerAutocomplete'), label='Клиент')
    duration = forms.ChoiceField(choices=((str(x), x) for x in range(1, settings.DAY_END - settings.DAY_START + 1)), label='Длительность')
    service_category = forms.ModelChoiceField(ProductCategory.objects.filter(service=True), label='Вид услуги')
    service = ChainedModelChoiceField('app', 'Product', 'service_category', 'product_category', show_all=False, auto_choose=True, label='Услуга')

    comment = forms.CharField(widget=forms.Textarea, label='Дополнительно')


class OrderAppointmentForm(forms.Form):
    category = forms.ModelChoiceField(ProductCategory.objects.all())
    product = forms.ModelChoiceField(Product.objects.all())
    quantity = forms.IntegerField()
    cost = forms.DecimalField()

