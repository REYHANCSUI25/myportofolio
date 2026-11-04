from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

HTML_ONLY_MESSAGE = "This field can't contain only HTML tags."


def strip_html(value):
    return strip_tags(value).strip()


def strip_html_required(value):
    cleaned = strip_html(value)
    if not cleaned:
        raise ValidationError(HTML_ONLY_MESSAGE, code="html_only")
    return cleaned
