from calendar import monthrange
from datetime import datetime, timedelta
from functools import wraps, partial
from json import dumps as json_dumps
from pytz import timezone

from django.contrib import admin
from django.forms.formsets import formset_factory
from django.shortcuts import redirect, render, get_object_or_404
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.utils.timezone import make_aware, utc
from django.conf import settings

from schedule.models.events import Event, EventRelation
from schedule.models.calendars import Calendar
from schedule.periods import Day, Month

from .models import Barber, Appointment, Customer
from .forms import MonthlyScheduleForm, CreateAppointmentForm


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
        status = 400
        if form.is_valid():
            date = make_aware(datetime.strptime(request.POST['date'], '%a, %d %b %Y %H:%M:%S %Z'), utc).astimezone(timezone(settings.TIME_ZONE))
            duration = form.cleaned_data['duration']
            customer = form.cleaned_data['customer']
            comment = form.cleaned_data['comment']
            service = form.cleaned_data['service']
            if barber.is_available(date, duration):
                appointment = Appointment(customer=customer, barber=barber, comment=comment, service=service)
                appointment.save()
                event = Event(start=date, end=date+timedelta(hours=int(duration)))
                event.save()
                calendar = Calendar.objects.get(name='client_schedule')
                calendar.events.add(event)
                relation = EventRelation.objects.create_relation(event, appointment)
                relation.save()
                status = 201

        return HttpResponse(status=status)

    form = CreateAppointmentForm()
    context = dict(
        admin.site.each_context(request),
        barber=barber,
        form=form,
    )
    return render(request, 'admin/create_appointment.html', context)
