import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware

from schedule.models.events import Event
from schedule.periods import Month, Day

from .forms import MonthlyScheduleForm
from .models import Customer, Barber


class MonthlyScheduleViewTestCase(TestCase):
    fixtures = ['basic_testdata.json', 'admin.json', 'monthly_schedule_testdata.json']

    def test_index(self):
        index_url = reverse('admin:monthly_schedule', kwargs={'year': datetime.datetime.now().year, 'month': datetime.datetime.now().month})
        resp = self.client.get(index_url)
        self.assertEqual(resp.status_code, 302)

        self.client.login(username='admin', password='pa55w0rd')
        resp = self.client.get(index_url)
        self.assertEqual(resp.status_code, 200)

    def test_bad_date(self):
        self.client.login(username='admin', password='pa55w0rd')
        resp = self.client.get(reverse('admin:monthly_schedule', kwargs={'year': 1969, 'month': 10}))
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(reverse('admin:monthly_schedule', kwargs={'year': 1969, 'month': 10}))
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(reverse('admin:monthly_schedule', kwargs={'year': 2038, 'month': 1}))
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(reverse('admin:monthly_schedule', kwargs={'year': 2015, 'month': 0}))
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(reverse('admin:monthly_schedule', kwargs={'year': 2015, 'month': 14}))
        self.assertEqual(resp.status_code, 404)

    def test_get_values(self):
        self.client.login(username='admin', password='pa55w0rd')
        date = datetime.datetime(2015, 6, 1)
        resp = self.client.get(reverse('admin:monthly_schedule', kwargs={'year': date.year, 'month': date.month}))
        formset = resp.context['formset']
        self.assertEqual(len(formset), Barber.objects.all().count())
        for form, barber in zip(formset, Barber.objects.all()):
            month = Month(Event.objects.get_for_object(barber), date=date)
            self.assertEqual(len(form.visible_fields()), len(list(month.get_days())))
            self.assertEqual(len(form.changed_data), len(month.get_occurrences()))
            for day, occ in zip(form.changed_data, month.cached_get_sorted_occurrences()):
                self.assertEqual(int(day[4:]), occ.end.day)

    def test_add_events(self):
        self.client.login(username='admin', password='pa55w0rd')
        date = make_aware(datetime.datetime(2015, 6, 22))
        resp = self.client.get(reverse('admin:monthly_schedule', kwargs={'year': date.year, 'month': date.month}))
        data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-0-day_{}'.format(date.day): True,
            'form-1-day_{}'.format(date.day): True,
        }
        for index, days in enumerate(resp.context['formset'].initial):
            for key, value in days.items():
                data['form-{}-{}'.format(index, key)] = value

        resp = self.client.post(
            reverse('admin:monthly_schedule', kwargs={'year': date.year, 'month': date.month}),
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        for barber in Barber.objects.all():
            self.assertTrue(Day(Event.objects.get_for_object(barber), date=datetime.date(date.year, date.month, date.day)).has_occurrences())

    def test_delete_events(self):
        self.client.login(username='admin', password='pa55w0rd')
        date = make_aware(datetime.datetime(2015, 6, 10))
        resp = self.client.get(reverse('admin:monthly_schedule', kwargs={'year': date.year, 'month': date.month}))
        data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-0-day_{}'.format(date.day): False,
            'form-1-day_{}'.format(date.day): False,
        }
        for index, days in enumerate(resp.context['formset'].initial):
            for key, value in days.items():
                if int(key[4:]) != date.day:
                    data['form-{}-{}'.format(index, key)] = value

        resp = self.client.post(
            reverse('admin:monthly_schedule', kwargs={'year': date.year, 'month': date.month}),
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        for barber in Barber.objects.all():
            self.assertFalse(Day(Event.objects.get_for_object(barber), date=datetime.date(date.year, date.month, date.day)).has_occurrences())

    def test_add_and_delete_events(self):
        self.client.login(username='admin', password='pa55w0rd')
        date = make_aware(datetime.datetime(2015, 6, 10))
        resp = self.client.get(reverse('admin:monthly_schedule', kwargs={'year': date.year, 'month': date.month}))
        data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-0-day_{}'.format(date.day): False,
            'form-1-day_{}'.format(date.day): False,
            'form-0-day_23': True,
            'form-1-day_23': True,
        }
        for index, days in enumerate(resp.context['formset'].initial):
            for key, value in days.items():
                if int(key[4:]) != date.day:
                    data['form-{}-{}'.format(index, key)] = value

        resp = self.client.post(
            reverse('admin:monthly_schedule', kwargs={'year': date.year, 'month': date.month}),
            data=data,
        )
        self.assertEqual(resp.status_code, 302)
        for barber in Barber.objects.all():
            self.assertFalse(Day(Event.objects.get_for_object(barber), date=datetime.date(date.year, date.month, date.day)).has_occurrences())
            self.assertTrue(Day(Event.objects.get_for_object(barber), date=datetime.date(date.year, date.month, 23)).has_occurrences())


class CustomerTestCase(TestCase):
    def test_add_valid_customer(self):
        customer = Customer.objects.create(name='Some name', phone='9780991233')

    def test_add_bad_customer(self):
        customer = Customer.objects.create(name='Another name')
        with self.assertRaises(ValidationError):
            customer.full_clean()

        customer = Customer.objects.create(name='Another name', phone='2786547')
        with self.assertRaises(ValidationError):
            customer.full_clean()

    def test_phone_coercing(self):
        customer_list = []
        customer_list.append(Customer.objects.create(name='Name', phone='+79529132590'))
        customer_list.append(Customer.objects.create(name='Name', phone='89529132590'))
        customer_list.append(Customer.objects.create(name='Name', phone='9529132590'))
        phone_list = []
        for customer in customer_list:
            customer.full_clean()
            phone_list.append(customer.phone)
        self.assertTrue(all(phone == phone_list[0] for phone in phone_list))


class MonthlyScheduleFormTestCase(TestCase):
    def test_construct_form(self):
        days = 15
        form = MonthlyScheduleForm(days=days)
        self.assertEqual(days, len(form.visible_fields()))

        with self.assertRaises(ValueError):
            form = MonthlyScheduleForm(days=0)

        with self.assertRaises(ValueError):
            form = MonthlyScheduleForm(days=-5)
