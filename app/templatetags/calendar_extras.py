from calendar import day_abbr

from django import template


register = template.Library()

@register.filter
def get_day_abbr(day, first_weekday):
    return day_abbr[(first_weekday + ((day - 1) % 7)) % 7]
