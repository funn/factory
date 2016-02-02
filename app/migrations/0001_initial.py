# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('comment', models.TextField(blank=True, verbose_name='Дополнительно')),
            ],
        ),
        migrations.CreateModel(
            name='Barber',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Имя')),
                ('phone', models.CharField(max_length=12, validators=[django.core.validators.RegexValidator(message='Некорректный номер телефона, ожидаемый ввод +79614567890 или 89614567890 или 9614567890', regex='^(\\+7|8)?\\d{10}$')], verbose_name='Телефон')),
                ('photo', models.ImageField(upload_to='', null=True, verbose_name='Фото')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Имя')),
                ('phone', models.CharField(max_length=12, validators=[django.core.validators.RegexValidator(message='Некорректный номер телефона, ожидаемый ввод +79614567890 или 89614567890 или 9614567890', regex='^(\\+7|8)?\\d{10}$')], verbose_name='Телефон')),
                ('comment', models.TextField(blank=True, verbose_name='Дополнительно')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderDetail',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Количество')),
                ('cost', models.DecimalField(validators=[django.core.validators.MinValueValidator(0)], max_digits=8, decimal_places=2, verbose_name='Цена')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Время')),
                ('appointment_fk', models.ForeignKey(blank=True, null=True, to='app.Appointment')),
                ('barber', models.ForeignKey(to='app.Barber', verbose_name='Парикмахер')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название товара')),
                ('quantity', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Количество')),
                ('price', models.DecimalField(validators=[django.core.validators.MinValueValidator(0)], max_digits=8, decimal_places=2, verbose_name='Цена')),
            ],
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название категории')),
                ('service', models.BooleanField(verbose_name='Услуга')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_category',
            field=models.ForeignKey(to='app.ProductCategory', verbose_name='Категория'),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='category',
            field=models.ForeignKey(to='app.ProductCategory', verbose_name='Категория'),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='customer',
            field=models.ForeignKey(to='app.Customer', verbose_name='Клиент'),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='product',
            field=models.ForeignKey(to='app.Product', verbose_name='Товар'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='barber',
            field=models.ForeignKey(to='app.Barber', verbose_name='Парикмахер'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='customer',
            field=models.ForeignKey(to='app.Customer', verbose_name='Клиент'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='orders',
            field=models.ManyToManyField(to='app.OrderDetail'),
        ),
    ]
