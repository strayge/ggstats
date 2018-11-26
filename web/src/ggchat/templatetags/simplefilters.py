from django import template
import hashlib

from django.urls import reverse
from django.utils.html import format_html

register = template.Library()

@register.filter
def div_int(value, arg):
    try:
        return int(value) // int(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def chat_hash(message_id):
    secret_post = "oXaVj3pLli3dLiIeK1jqsI6GZYxZX5YO"
    try:
        return hashlib.md5((str(message_id) + secret_post).encode('utf-8')).hexdigest()
    except:
        return "DEADBEEF"

@register.simple_tag
def channel_link(value):
    try:
        if value.streamer and value.streamer.username:
            text = value.streamer.username
        elif value.channel_id == 'r128':
            text = 'Флудилка'
        else:
            text = '#{}'.format(value.channel_id)
        url = reverse('channel', args=[value.channel_id])
        link = format_html('<a href="{}">{}</a>', url, text)
        return link
    except:
        return ''
