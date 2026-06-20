import re 
from django.core.exceptions import ValidationError

def validate_iranian_phone(value):
    pattern = r'^09[0-9]{9}$'
    if not re.match(pattern, value):
        raise ValidationError(
            "شماره موبایل باید با 09 شروع شود و 11 رقم باشد "
            )