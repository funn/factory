from calendar import day_abbr
from pytz import timezone

from django import template
from django.conf import settings


register = template.Library()


@register.filter
def get_day_abbr(day, first_weekday):
    return day_abbr[(first_weekday + ((day - 1) % 7)) % 7]


@register.simple_tag
def render_appointment(events, time, barber, table_nodes): # TODO: This is plain horrible, hardcoded urls!!
    for occ in events[barber]:
        if int(time[:2]) == occ.start.astimezone(timezone(settings.TIME_ZONE)).hour:
            return '<td rowspan="{}" class="app_edit"><a href="/admin/edit_appointment/{}">x</a></td>'.format(occ.end.astimezone(timezone(settings.TIME_ZONE)).hour - occ.start.astimezone(timezone(settings.TIME_ZONE)).hour, barber.id)
    if int(time[:2]) in [hour[0] for hour in table_nodes[barber]]:
        return '<td class="app_create"><a href="/admin/create_appointment/{}">+</a></td>'.format(barber.id)
    return ''
