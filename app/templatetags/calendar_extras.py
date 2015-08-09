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
            name = '<p class="customer_name">{}</p>'.format(occ_tuple[1].customer.name)
            phone = '<p class="customer_phone">{}</p>'.format(occ_tuple[1].customer.phone)
            service_list = ''
            for service in occ_tuple[1].services.all():
                service_list += '<li class="list-group-item">{}: {}</li>'.format(service.product_category.name, service.name)
            service_list = '<ul class="list-group">' + service_list + '</ul>'
            return '<td rowspan="{}" class="app_edit"><a href="/admin/edit_appointment/{}"><span class="glyphicon glyphicon-user"></a>{}{}{}</td>'.format(occ_tuple[0].end.astimezone(timezone(settings.TIME_ZONE)).hour - occ_tuple[0].start.astimezone(timezone(settings.TIME_ZONE)).hour, occ_tuple[1].id, name, phone, service_list)
    if int(time[:2]) in [hour[0] for hour in table_nodes[barber]]:
        return '<td class="app_create"><a href="/admin/create_appointment/{}"><span class="glyphicon glyphicon-plus"></a></td>'.format(barber.id)
    return ''


class EscapeScriptNode(template.Node):
    TAG_NAME = 'escapescript'

    def __init__(self, nodelist):
        super(EscapeScriptNode, self).__init__()
        self.nodelist = nodelist

    def render(self, context):
        out = self.nodelist.render(context)
        escaped_out = out.replace(u'</script>', u'<\\/script>')
        return escaped_out


@register.tag(EscapeScriptNode.TAG_NAME)
def media(parser, token):
    nodelist = parser.parse(('end' + EscapeScriptNode.TAG_NAME,))
    parser.delete_first_token()
    return EscapeScriptNode(nodelist)
