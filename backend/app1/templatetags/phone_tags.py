from django import template
import re

register = template.Library()

@register.filter
def clean_phone(value):
    # Оставляем только цифры и плюс
    return re.sub(r'[^\d+]', '', value)