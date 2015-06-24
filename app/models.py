from django.db import models
from django.core.validators import RegexValidator

from smart_selects.db_fields import ChainedForeignKey


phone_regex = RegexValidator(regex=r'^(\+7|8)?\d{10}$', message="Некорректный номер телефона, ожидаемый ввод +79614567890 или 89614567890 или 9614567890")

class ProductCategory(models.Model):
    name = models.CharField(verbose_name='Название категории', max_length=200)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(verbose_name='Название товара', max_length=200)
    quantity = models.IntegerField(verbose_name='Количество')
    price = models.DecimalField(verbose_name='Цена', max_digits=8, decimal_places=2)
    product_category = models.ForeignKey(ProductCategory, verbose_name='Категория')

    def __str__(self):
        return self.name


class PhoneValidationMixin(models.Model):
    class Meta:
        abstract = True

    def clean(self):
        self.phone = '+7{}'.format(self.phone[-10:])


class Barber(PhoneValidationMixin):
    name = models.CharField(verbose_name='Имя', max_length=200)
    phone = models.CharField(max_length=12, validators=[phone_regex], verbose_name='Телефон')
    photo = models.ImageField(verbose_name='Фото', null=True)
    description = models.TextField(verbose_name='Описание', blank=True)

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
    quantity = models.IntegerField(verbose_name='Количество')
    cost = models.DecimalField(verbose_name='Цена', max_digits=8, decimal_places=2)
    date = models.DateTimeField(verbose_name='Время', auto_now_add=True)
    barber = models.ForeignKey(Barber, verbose_name='Парикмахер')
    customer = models.ForeignKey(Customer, verbose_name='Клиент')
