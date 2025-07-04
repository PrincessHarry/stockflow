from django import template

register = template.Library()

@register.filter
def class_name(value):
    """
    Returns the class name of an object
    """
    return value.__class__.__name__ 