from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

HTML_ONLY_MESSAGE = "This field can't contain only HTML tags."
PERIOD_ORDER_MESSAGE = "The end date can't be before the start date."


def strip_html(value):
    return strip_tags(value).strip()


def strip_html_required(value):
    cleaned = strip_html(value)
    if not cleaned:
        raise ValidationError(HTML_ONLY_MESSAGE, code="html_only")
    return cleaned


def validate_period(started_at, ended_at):
    if started_at and ended_at and ended_at < started_at:
        raise ValidationError(
            {"ended_at": ValidationError(PERIOD_ORDER_MESSAGE, code="period_order")}
        )
