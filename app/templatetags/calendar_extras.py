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
    for occ_tuple in events[barber]:
        if int(time[:2]) == occ_tuple[0].start.astimezone(timezone(settings.TIME_ZONE)).hour:
            return '<td rowspan="{}" class="app_edit"><a href="/admin/edit_appointment/{}"><span class="glyphicon glyphicon-user"></a><p>{}<br>{}<br>{}<br>{}</p></td>'.format(occ_tuple[0].end.astimezone(timezone(settings.TIME_ZONE)).hour - occ_tuple[0].start.astimezone(timezone(settings.TIME_ZONE)).hour, barber.id, occ_tuple[1].customer.name, occ_tuple[1].customer.phone, occ_tuple[1].service.product_category.name, occ_tuple[1].service.name)
    if int(time[:2]) in [hour[0] for hour in table_nodes[barber]]:
        return '<td class="app_create"><a href="/admin/create_appointment/{}"><span class="glyphicon glyphicon-plus"></a></td>'.format(barber.id)
    return ''
