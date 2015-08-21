from datetime import timedelta

from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.conf import settings

from schedule.models.events import Event, EventRelation
from schedule.periods import Day, Period

from smart_selects.db_fields import ChainedForeignKey


phone_regex = RegexValidator(regex=r'^(\+7|8)?\d{10}$', message="Некорректный номер телефона, ожидаемый ввод +79614567890 или 89614567890 или 9614567890")


class ProductCategory(models.Model):
    name = models.CharField(verbose_name='Название категории', max_length=200)
    service = models.BooleanField(verbose_name='Услуга')

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(verbose_name='Название товара', max_length=200)
    quantity = models.PositiveIntegerField(verbose_name='Количество', validators=[MinValueValidator(1)], default=1)
    price = models.DecimalField(verbose_name='Цена', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    product_category = models.ForeignKey(ProductCategory, verbose_name='Категория')

    def __str__(self):
        return self.name


class PhoneValidationMixin(models.Model):
    class Meta:
        abstract = True

    def clean(self):
        self.phone = '+7{}'.format(self.phone[-10:])


class BarberManager(models.Manager):
    def get_active_barbers(self, day):
        active_barbers = []
        for barber in self.all():
            barber_schedule_data_raw = EventRelation.objects.filter(event__calendar__name='barber_schedule').filter(object_id=barber.id).values('event')
            barber_schedule_data = []
            for item in barber_schedule_data_raw.values():
                barber_schedule_data.append(Event.objects.get(pk=item['event_id']))
            if Day(barber_schedule_data, day).has_occurrences():
                active_barbers.append(barber)
        return active_barbers


class Barber(PhoneValidationMixin):
    name = models.CharField(verbose_name='Имя', max_length=200)
    phone = models.CharField(max_length=12, validators=[phone_regex], verbose_name='Телефон')
    photo = models.ImageField(verbose_name='Фото', null=True)
    description = models.TextField(verbose_name='Описание', blank=True)

    objects = BarberManager()

    def is_available(self, date, duration, customer=None):
        if date.hour < settings.DAY_START or date.hour + int(duration) > settings.DAY_END:
            return False # Not operating on this hours.

        barber_schedule_data = [Event.objects.get(pk=item['event_id']) for item in EventRelation.objects.filter(event__calendar__name='barber_schedule').filter(object_id=self.id).values('event').values()]
        if not Day(barber_schedule_data, date).has_occurrences():
            return False # Barber doesn't work this day.

        client_schedule_data = [Event.objects.get(pk=EventRelation.objects.filter(event__calendar__name='client_schedule').get(object_id=appointment.id).event_id) for appointment in Appointment.objects.filter(barber=self) if appointment.customer != customer]
        if Period(client_schedule_data, date + timedelta(minutes=1), date + timedelta(hours=int(duration)-1, minutes=59)).has_occurrences():
            return False # Barber got another client at this time.

        return True

    def __str__(self):
        return self.name


class Customer(PhoneValidationMixin):
    name = models.CharField(verbose_name='Имя', max_length=200)
    phone = models.CharField(max_length=12, validators=[phone_regex], verbose_name='Телефон')
    comment = models.TextField(verbose_name='Дополнительно', blank=True)

    def __str__(self):
        return "{}, {}".format(self.name, self.phone)


class OrderDetail(models.Model):
    category = models.ForeignKey(ProductCategory, verbose_name='Категория')
    product = ChainedForeignKey(Product, chained_field='category', chained_model_field='product_category', show_all=False, auto_choose=True, verbose_name='Товар')
    quantity = models.PositiveIntegerField(verbose_name='Количество', validators=[MinValueValidator(1)], default=1)
    cost = models.DecimalField(verbose_name='Цена', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateTimeField(verbose_name='Время', auto_now_add=True)
    barber = models.ForeignKey(Barber, verbose_name='Парикмахер')
    customer = models.ForeignKey(Customer, verbose_name='Клиент')
    appointment_fk = models.ForeignKey('Appointment', null=True, blank=True)


class Appointment(models.Model):
    customer = models.ForeignKey(Customer, verbose_name='Клиент')
    barber = models.ForeignKey(Barber, verbose_name='Парикмахер')
    orders = models.ManyToManyField(OrderDetail)
    comment = models.TextField(verbose_name='Дополнительно', blank=True)

