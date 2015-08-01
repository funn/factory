from django import forms
from django.conf import settings

import autocomplete_light

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
    def __init__(self, *args, **kwargs):
        super(CreateAppointmentForm, self).__init__(*args, **kwargs)
        for category in ProductCategory.objects.filter(service=True):
            self.fields['show_{}'.format(category.id)] = forms.BooleanField(label=category.name, required=False)
            self.fields['service_{}'.format(category.id)] = forms.ModelChoiceField(Product.objects.filter(product_category=category), label='', required=False)

    def clean(self):
        cleaned_data = super(CreateAppointmentForm, self).clean()
        at_least_one = False
        for category in ProductCategory.objects.filter(service=True):
            if cleaned_data['show_{}'.format(category.id)] and not cleaned_data['service_{}'.format(category.id)]:
                raise forms.ValidationError('Did not select service in "{}" category.'.format(category.name))
            if cleaned_data['show_{}'.format(category.id)] and cleaned_data['service_{}'.format(category.id)]:
                at_least_one = True
        if not at_least_one:
            raise forms.ValidationError('Choose at least one service.')

    customer = autocomplete_light.forms.ModelChoiceField(Customer.objects.all(), widget=autocomplete_light.ChoiceWidget('CustomerAutocomplete'), label='Клиент')
    duration = forms.ChoiceField(choices=((str(x), x) for x in range(1, settings.DAY_END - settings.DAY_START + 1)), label='Длительность')
    comment = forms.CharField(widget=forms.Textarea, label='Дополнительно', required=False)


class OrderAppointmentForm(forms.Form):
    category = forms.ModelChoiceField(ProductCategory.objects.all())
    product = forms.ModelChoiceField(Product.objects.all())
    quantity = forms.IntegerField()
    cost = forms.DecimalField()
