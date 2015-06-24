from django import forms

import autocomplete_light

from .models import OrderDetail, Customer


class OrderDetailForm(forms.ModelForm):
    class Meta:
        model = OrderDetail
        exclude = []

    customer = autocomplete_light.forms.ModelChoiceField(Customer.objects.all(), widget=autocomplete_light.ChoiceWidget('OrderDetailsAutocomplete'), label='Клиент')


class MonthlyScheduleForm(forms.Form):
    def __init__(self, *args, **kwargs):
        days = kwargs.pop('days')
        if days <= 0:
            raise ValueError('Days should be a positive value more than zero. days={}'.format(days))
        super(MonthlyScheduleForm, self).__init__(*args, **kwargs)
        for day in range(1, days+1):
            self.fields['day_{}'.format(day)] = forms.BooleanField(required=False)
