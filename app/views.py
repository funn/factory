from calendar import monthrange
from datetime import datetime, timedelta
from functools import wraps, partial
from pytz import timezone

from django.contrib import admin
from django.forms.formsets import formset_factory
from django.shortcuts import redirect, render, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import Http404, JsonResponse
from django.utils.timezone import make_aware, utc
from django.conf import settings

from schedule.models.events import Event, EventRelation
from schedule.models.calendars import Calendar
from schedule.periods import Day, Month

from clever_selects.views import ChainedSelectChoicesView

from .models import Barber, Appointment, ProductCategory, Product, OrderDetail
from .forms import MonthlyScheduleForm, CreateAppointmentForm, OrderAppointmentForm, EditAppointmentBaseFormset


def monthly_schedule(request, year, month):
    if int(year) > 2037 or int(year) < 1970 or int(month) < 1 or int(month) > 12:
        raise Http404

    MonthlyScheduleFormset = formset_factory(wraps(MonthlyScheduleForm)(partial(MonthlyScheduleForm, days=monthrange(int(year), int(month))[1])), extra=0)

    initial_data = []
    for barber in Barber.objects.all():
        data = {}
        calendar = Calendar.objects.get_or_create(name='barber_schedule')[0]
        month_period = Month(calendar.events.get_for_object(barber), datetime(int(year), int(month), 1))
        for day_period in month_period.get_days():
            if day_period.has_occurrences():
                data['day_{}'.format(day_period.start.day)] = True
        initial_data.append(data)

    if request.method == 'POST':
        formset = MonthlyScheduleFormset(request.POST, initial=initial_data)
        if formset.is_valid():
            for form, barber in zip(formset, Barber.objects.all()):
                for day in form.changed_data:
                    if not form.cleaned_data[day]:
                        calendar = Calendar.objects.get(name='barber_schedule')
                        events = calendar.events.get_for_object(barber)
                        period = Day(events, datetime(int(year), int(month), int(day[4:])))
                        if period.has_occurrences():
                            for occurrence in period.get_occurrences():
                                Event.objects.get(id=occurrence.event_id).delete()
                    else:
                        calendar = Calendar.objects.get_or_create(name='barber_schedule')[0]
                        event = Event(
                            start=make_aware(datetime(int(year), int(month), int(day[4:]), settings.DAY_START)),
                            end=make_aware(datetime(int(year), int(month), int(day[4:]), settings.DAY_END))
                        )
                        event.save()
                        calendar.events.add(event)
                        relation = EventRelation.objects.create_relation(event, barber)
                        relation.save()

    else:
        formset = MonthlyScheduleFormset(initial=initial_data)

    context = dict(
        admin.site.each_context(request),
        days=range(1, monthrange(int(year), int(month))[1] + 1),
        first_weekday=monthrange(int(year), int(month))[0],
        barbers=zip(Barber.objects.all(), formset),
        formset=formset,
        prev_date=(datetime(int(year), int(month), 1) - timedelta(days=1)),
        current_date=datetime.now(),
        next_date=(datetime(int(year), int(month), monthrange(int(year), int(month))[1]) + timedelta(days=1)),
    )
    if request.method == 'POST':
        return redirect(reverse('admin:monthly_schedule', kwargs={'year': year, 'month': month}), context)
    else:
        return render(request, 'admin/monthly_schedule.html', context)


def daily_schedule(request, year, month, day):
    Calendar.objects.get_or_create(name='barber_schedule')
    Calendar.objects.get_or_create(name='client_schedule')

    events = {}
    active_barbers = Barber.objects.get_active_barbers(make_aware(datetime(int(year), int(month), int(day))))

    for barber in active_barbers:
        app_ids = Appointment.objects.filter(barber=barber).values('id')
        events_list = []
        for app_id in app_ids:
            event = EventRelation.objects.filter(event__calendar__name='client_schedule').filter(object_id=app_id['id']).values('event_id')
            events_list.append(Event.objects.get(pk=event[0]['event_id'])) # Fucking horrible.
        events[barber] = Day(events_list, datetime(int(year), int(month), int(day))).occurrences
        events[barber] = list(zip(events[barber], [Appointment.objects.get(pk=EventRelation.objects.filter(event__calendar__name='client_schedule').get(event__id=occ.event_id).object_id) for occ in events[barber]]))

    table_nodes = {}
    for barber in active_barbers:
        if not table_nodes.get(barber):
            table_nodes[barber] = []

        busy_hours = {occ_tuple[0].start.astimezone(timezone(settings.TIME_ZONE)).hour: occ_tuple[0].end.astimezone(timezone(settings.TIME_ZONE)).hour-occ_tuple[0].start.astimezone(timezone(settings.TIME_ZONE)).hour for occ_tuple in events[barber]}
        hour_skip = 0
        for hour in range(settings.DAY_START, settings.DAY_END):
            if hour in busy_hours.keys():
                table_nodes[barber].append((hour, busy_hours[hour]))
                hour_skip = busy_hours[hour] - 1
            else:
                if hour_skip == 0:
                    table_nodes[barber].append((hour, None))
                else:
                    hour_skip -= 1

    context = dict(
        admin.site.each_context(request),
        hours=['{}-00'.format(hour) for hour in range(settings.DAY_START, settings.DAY_END)],
        events=events,
        barbers=active_barbers,
        table_nodes=table_nodes,
    )
    return render(request, 'admin/daily_schedule.html', context)


def create_appointment(request, barber):
    barber = get_object_or_404(Barber, pk=barber)
    if request.method == 'POST':
        form = CreateAppointmentForm(request.POST)
        if form.is_valid():
            duration = form.cleaned_data['duration']
            date = form.cleaned_data['date']
            appointment = Appointment(customer=form.cleaned_data['customer'], barber=barber, comment=form.cleaned_data['comment'])
            appointment.save() # TODO: Try-Except
            for category in ProductCategory.objects.filter(service=True):
                if form.cleaned_data['show_{}'.format(category.id)]:
                    order = OrderDetail.objects.create(category=category, product=form.cleaned_data['service_{}'.format(category.id)], quantity=1, cost=form.cleaned_data['cost_{}'.format(category.id)], date=date, barber=barber, customer=form.cleaned_data['customer'], appointment_fk=appointment)
                    appointment.orders.add(order)
            event = Event(start=date, end=date+timedelta(hours=int(duration)))
            event.save()
            calendar = Calendar.objects.get(name='client_schedule')
            calendar.events.add(event)
            relation = EventRelation.objects.create_relation(event, appointment)
            relation.save()
        else:
            date =datetime.now() # Ugly as shit.
    else:
        date = make_aware(datetime.strptime(request.GET['date'], '%a, %d %b %Y %H:%M:%S %Z'), utc).astimezone(timezone(settings.TIME_ZONE))
        form = CreateAppointmentForm(date=date, barber=barber)
    context = dict(
        admin.site.each_context(request),
        barber=barber,
        form=form,
        time='{}-00'.format(date.hour),
    )
    return render(request, 'admin/create_appointment.html', context)


def edit_appointment(request, appointment):
    appointment = get_object_or_404(Appointment, pk=appointment)
    EditAppointmentFormset = formset_factory(OrderAppointmentForm, formset=EditAppointmentBaseFormset, can_delete=True, extra=0)
    date_start = EventRelation.objects.get_events_for_object(appointment).values()[0]['start'].astimezone(timezone(settings.TIME_ZONE))
    date_end = EventRelation.objects.get_events_for_object(appointment).values()[0]['end'].astimezone(timezone(settings.TIME_ZONE))

    initial_data_form = {'customer': appointment.customer, 'comment':appointment.comment, 'duration': date_end.hour - date_start.hour}
    for service in ProductCategory.objects.filter(service=True):
        found = False
        for order in appointment.orders.all():
            if service == order.category:
                initial_data_form['show_{}'.format(service.id)] = True
                initial_data_form['service_{}'.format(service.id)] = order.product
                initial_data_form['cost_{}'.format(service.id)] = order.cost
                found = True
        if not found:
            initial_data_form['show_{}'.format(service.id)] = False

    initial_data_formset = []
    for order in appointment.orders.filter(category__service=False):
        initial_data_formset.append({'category': order.category,'product': order.product, 'quantity': order.quantity, 'cost': order.cost})

    if request.method == 'POST':
        formset = EditAppointmentFormset(request.POST, initial=initial_data_formset)
        form_app = CreateAppointmentForm(request.POST, date=date_start, initial=initial_data_form, appointment=appointment)
        if form_app.is_valid() and formset.is_valid():
            if form_app.has_changed():
                date = form_app.cleaned_data['date']
                event = EventRelation.objects.get_events_for_object(appointment).get()
                event.start = date
                event.end = event.start + timedelta(hours=int(form_app.cleaned_data['duration']))
                event.save()
                appointment.customer = form_app.cleaned_data['customer']
                appointment.comment = form_app.cleaned_data['comment']
                appointment.barber = form_app.cleaned_data['barber']
            for service in ProductCategory.objects.filter(service=True):
                order = appointment.orders.filter(category=service)
                if order:
                    order = order.get()
                    if form_app.cleaned_data['show_{}'.format(service.id)]:
                        order.cost = form_app.cleaned_data['cost_{}'.format(service.id)]
                        order.save()
                    else:
                        order.delete()
                else:
                    if form_app.cleaned_data['show_{}'.format(service.id)]:
                        order = OrderDetail.objects.create(category=service, product=form_app.cleaned_data['service_{}'.format(service.id)], quantity=1, cost=form_app.cleaned_data['cost_{}'.format(service.id)], date=date_start, barber=appointment.barber, customer=form_app.cleaned_data['customer'], appointment_fk=appointment)
                        appointment.orders.add(order)
            if formset.has_changed():
                bulk_edit = []
                bulk_create = []
                for index, form in enumerate(formset):
                    if form.has_changed():
                        product = initial_data_formset[index]['product'] if index < len(initial_data_formset) else None
                        order = appointment.orders.filter(product=product)
                        if form in formset.deleted_forms and order:
                            order = order.get()
                            order.delete()
                        else:
                            if order:
                                bulk_edit.append((order.get().id, {'product': form.cleaned_data['product'], 'cost': form.cleaned_data['cost'], 'quantity': form.cleaned_data['quantity']}))
                            else:
                                if form not in formset.deleted_forms:
                                    bulk_create.append({'category': form.cleaned_data['category'], 'product': form.cleaned_data['product'], 'quantity': form.cleaned_data['quantity'], 'cost': form.cleaned_data['cost']})
                for bulk in bulk_edit:
                    order = OrderDetail.objects.get(pk=bulk[0])
                    order.product = bulk[1]['product']
                    order.cost = bulk[1]['cost']
                    order.quantity = bulk[1]['quantity']
                    order.save()
                for bulk in bulk_create:
                    order = OrderDetail.objects.create(category=bulk['category'], product=bulk['product'], quantity=bulk['quantity'], cost=bulk['cost'], date=date_start, barber=appointment.barber, customer=appointment.customer, appointment_fk=appointment)
                    appointment.orders.add(order)
            appointment.save()
    else:
        formset = EditAppointmentFormset(initial=initial_data_formset)
        form_app = CreateAppointmentForm(date=date_start, initial=initial_data_form, barber=appointment.barber)

    return render(request, 'admin/edit_appointment.html', {'appointment': appointment, 'formset': formset, 'barber': appointment.barber, 'form': form_app, 'time':'{}-00'.format(date_start.hour)})


class AjaxChainedProducts(ChainedSelectChoicesView):
    def get_choices(self):
        vals_list = []
        id_list = []
        for product in Product.objects.filter(product_category__id=self.parent_value):
            id_list.append(product.id)
            vals_list.append(product.name)
        return tuple(zip(id_list, vals_list))


def get_product_price(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return JsonResponse(dict(price=product.price))
