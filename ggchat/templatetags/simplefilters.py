from django import template

register = template.Library()

@register.filter
def div_int(value, arg):
    try:
        return int(value) // int(arg)
    except (ValueError, ZeroDivisionError):
        return None
