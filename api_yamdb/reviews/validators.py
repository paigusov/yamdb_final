import datetime
from django.core.exceptions import ValidationError


def NotLaterThisYearValidator(value):
    if value > datetime.date.today().year:
        raise ValidationError(
            ('Год выхода %(value) не может быть позже текущего года!'),
            params={'value': value},
        )
