from django import template
import hashlib

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