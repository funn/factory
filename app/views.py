from calendar import monthrange
import datetime
from functools import wraps, partial

from django.contrib import admin
from django.forms.formsets import formset_factory
from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils.timezone import make_aware
from django.conf import settings

from schedule.models.events import Event, EventRelation
from schedule.models.calendars import Calendar
from schedule.periods import Day, Month

from .models import Barber
from .forms import MonthlyScheduleForm


def monthly_schedule(request, year, month):
    if int(year) > 2037 or int(year) < 1970 or int(month) < 1 or int(month) > 12:
        raise Http404

    MonthlyScheduleFormset = formset_factory(wraps(MonthlyScheduleForm)(partial(MonthlyScheduleForm, days=monthrange(int(year), int(month))[1])), extra=0)

    initial_data = []
    for barber in Barber.objects.all():
        data = {}
        calendar = Calendar.objects.get_or_create(name='barber_schedule')[0]
        month_period = Month(calendar.events.get_for_object(barber), datetime.datetime(int(year), int(month), 1))
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
                        period = Day(events, datetime.datetime(int(year), int(month), int(day[4:])))
                        if period.has_occurrences():
                            for occurrence in period.get_occurrences():
                                Event.objects.get(id=occurrence.event_id).delete()
                    else:
                        calendar = Calendar.objects.get_or_create(name='barber_schedule')[0]
                        event = Event(
                            start=make_aware(datetime.datetime(int(year), int(month), int(day[4:]), settings.DAY_START)),
                            end=make_aware(datetime.datetime(int(year), int(month), int(day[4:]), settings.DAY_END))
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
        prev_date=(datetime.datetime(int(year), int(month), 1) - datetime.timedelta(days=1)),
        current_date=datetime.datetime.now(),
        next_date=(datetime.datetime(int(year), int(month), monthrange(int(year), int(month))[1]) + datetime.timedelta(days=1)),
    )
    if request.method == 'POST':
        return redirect(reverse('admin:monthly_schedule', kwargs={'year': year, 'month': month}), context)
    else:
        return render(request, 'admin/monthly_schedule.html', context)

def daily_schedule(request, year, month, day):
    context = dict(
        admin.site.each_context(request),
    )
    return TemplateResponse(request, 'admin/daily_schedule.html', context)
