from datetime import datetime, timedelta

from django import forms
from django.conf import settings

from schedule.models.events import EventRelation

import autocomplete_light

from clever_selects.form_fields import ChainedModelChoiceField
from clever_selects.forms import ChainedChoicesForm, ChainedChoicesModelForm

from datetimewidget.widgets import DateTimeWidget

from .models import OrderDetail, Customer, ProductCategory, Product, Barber, Appointment


class OrderDetailForm(ChainedChoicesModelForm):
    class Meta:
        model = OrderDetail
        exclude = []

    customer = autocomplete_light.forms.ModelChoiceField(Customer.objects.all(), widget=autocomplete_light.ChoiceWidget('CustomerAutocomplete'), label='Клиент')
    product = ChainedModelChoiceField(parent_field='category', ajax_url='/ajax/chained-products/', label='Товар', model=Product)


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
        self.post_date = kwargs.pop('date', None)
        self.post_barber = kwargs.pop('barber', None)
        self.appointment = kwargs.pop('appointment', None)
        choice_hours = settings.DAY_END - settings.DAY_START if not self.post_date else settings.DAY_END - self.post_date.hour + 1
        super(CreateAppointmentForm, self).__init__(*args, **kwargs)
        self.fields['barber'] = forms.ModelChoiceField(Barber.objects.all(), label='Парикмахер', initial=self.post_barber)
        start_date = datetime.now().replace(hour=settings.DAY_START, minute=0).strftime('%d/%m/%Y %H:%M')
        self.fields['date'] = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M'], required=True, widget=DateTimeWidget(attrs={'id': 'form_datetimepicker'}, options={'minuteStep': 60, 'weekStart': 1, 'minView': 1, 'startDate': start_date}, bootstrap_version=3), initial=self.post_date, label='Время')
        self.fields['duration'] = forms.ChoiceField(choices=((str(x), x) for x in range(1, choice_hours)), label='Длительность')
        for category in ProductCategory.objects.filter(service=True):
            self.fields['show_{}'.format(category.id)] = forms.BooleanField(label=category.name, required=False)
            self.fields['service_{}'.format(category.id)] = forms.ModelChoiceField(Product.objects.filter(product_category=category), label='', required=False)
            self.fields['cost_{}'.format(category.id)] = forms.DecimalField(min_value=0, label='Стоимость', required=False)

    def clean(self):
        if any(self.errors):
            return

        cleaned_data = super(CreateAppointmentForm, self).clean()

        events = Appointment.objects.get_appointments_for(cleaned_data['barber'], cleaned_data['date'], cleaned_data['date'] + timedelta(hours=int(cleaned_data['duration'])))
        if len(events) > 1 or (len(events) == 1 and Appointment.objects.get(pk=EventRelation.objects.get(event=events[0]).object_id) != self.appointment):
            raise forms.ValidationError('Парикмахер {} недоступен для записи в {} на {}ч.'.format(cleaned_data['barber'], cleaned_data['date'], cleaned_data['duration']))

        if not cleaned_data['barber'].is_available(cleaned_data['date'], cleaned_data['duration'], cleaned_data['customer']):
            raise forms.ValidationError('Парикмахер {} недоступен для записи в {} на {}ч.'.format(cleaned_data['barber'], cleaned_data['date'], cleaned_data['duration']))

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


class OrderAppointmentForm(ChainedChoicesForm):
    def __init__(self, *arg, **kwarg):
        super(OrderAppointmentForm, self).__init__(*arg, **kwarg)
        self.empty_permitted = False

    category = forms.ModelChoiceField(ProductCategory.objects.filter(service=False), label='Категория')
    product = ChainedModelChoiceField(parent_field='category', ajax_url='/ajax/chained-products/', label='Товар', model=Product)
    quantity = forms.IntegerField(min_value=1, initial=1, label='Количество')
    cost = forms.DecimalField(min_value=0, label='Цена')

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
