from django import template

register = template.Library()

@register.filter
def get_color(index):
    colors = ['#E0F2FE', '#D1FAE5', '#FEF3C7', '#FEE2E2']
    return colors[(index - 1) % len(colors)]