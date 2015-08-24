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
    def __init__(self, *args, **kwargs):
        hour = kwargs.pop('hour')
        super(CreateAppointmentForm, self).__init__(*args, **kwargs)
        self.fields['duration'] = forms.ChoiceField(choices=((str(x), x) for x in range(1, settings.DAY_END - hour + 1)), label='Длительность')
        for category in ProductCategory.objects.filter(service=True):
            self.fields['show_{}'.format(category.id)] = forms.BooleanField(label=category.name, required=False)
            self.fields['service_{}'.format(category.id)] = forms.ModelChoiceField(Product.objects.filter(product_category=category), label='', required=False)
            self.fields['cost_{}'.format(category.id)] = forms.DecimalField(min_value=0, label='Стоимость', required=False)

    def clean(self):
        cleaned_data = super(CreateAppointmentForm, self).clean()
        at_least_one = False
        for category in ProductCategory.objects.filter(service=True):
            if cleaned_data['show_{}'.format(category.id)] and not cleaned_data['service_{}'.format(category.id)]:
                raise forms.ValidationError('Не выбрана услуга в категории {}.'.format(category.name))
            if cleaned_data['show_{}'.format(category.id)] and cleaned_data['service_{}'.format(category.id)]:
                at_least_one = True
            if cleaned_data['show_{}'.format(category.id)] and not cleaned_data['cost_{}'.format(category.id)]:
                raise forms.ValidationError('Не указана цена в категории {}.'.format(category.name))
        if not at_least_one:
            raise forms.ValidationError('Выберите хотя бы одну услугу.')

    customer = autocomplete_light.forms.ModelChoiceField(Customer.objects.all(), widget=autocomplete_light.ChoiceWidget('CustomerAutocomplete'), label='Клиент')
    comment = forms.CharField(widget=forms.Textarea, label='Дополнительно', required=False)


class OrderAppointmentForm(forms.Form):
    def __init__(self, *arg, **kwarg):
        super(OrderAppointmentForm, self).__init__(*arg, **kwarg)
        self.empty_permitted = False

    category = forms.ModelChoiceField(ProductCategory.objects.filter(service=False), label='Категория')
    product = ChainedModelChoiceField('app', 'Product', 'category', 'product_category', show_all=False, auto_choose=True, label='Товар')
    quantity = forms.IntegerField(min_value=1, initial=1)
    cost = forms.DecimalField(min_value=0)

class EditAppointmentBaseFormset(forms.formsets.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        products = []
        for form in self.forms:
            product = form.cleaned_data['product']
            if form not in self.deleted_forms:
                if product in products:
                    raise forms.ValidationError('{} добавлен несколько раз.'.format(product.name))
                products.append(product)
