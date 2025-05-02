from django import template
from django.utils.safestring import SafeString

register = template.Library()

@register.filter(name='addclass')
def addclass(field, css_class):
    if isinstance(field, SafeString):
        return field
    return field.as_widget(attrs={'class': css_class})