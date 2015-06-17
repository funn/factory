from calendar import monthrange
import datetime
from functools import wraps, partial

from django.template.response import TemplateResponse
from django.contrib import admin
from django.forms.formsets import formset_factory

from schedule.models.events import Event, EventRelation
from schedule.periods import Day, Month

from .models import Barber
from .forms import MonthlyScheduleForm


def monthly_schedule(request, year, month):
    MonthlyScheduleFormset = formset_factory(wraps(MonthlyScheduleForm)(partial(MonthlyScheduleForm, days=monthrange(int(year), int(month))[1])), extra=Barber.objects.count())

    initial_data = []
    for barber in Barber.objects.all():
        data = {}
        month_period = Month(EventRelation.objects.get_events_for_object(barber), datetime.date(int(year), int(month), 1))
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
                        events = Event.objects.get_for_object(barber)
                        period = Day(events, datetime.date(int(year), int(month), int(day[4:])))
                        if period.has_occurrences():
                            for occurrence in period.get_occurrences():
                                Event.objects.get(id=occurrence.event_id).delete()
                    else:
                        event = Event(start=datetime.datetime(int(year), int(month), int(day[4:]), 12), end=datetime.datetime(int(year), int(month), int(day[4:]), 12)+datetime.timedelta(hours=10))
                        event.save()
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
        prev_date=(datetime.date(int(year), int(month), 1) - datetime.timedelta(days=1)),
        current_date=datetime.datetime.now(),
        next_date=(datetime.date(int(year), int(month), monthrange(int(year), int(month))[1]) + datetime.timedelta(days=1)),
    )
    return TemplateResponse(request, 'admin/monthly_schedule.html', context)
