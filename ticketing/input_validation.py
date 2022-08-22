from .models import TicketCode
from .class_lookup import STUDENTS


def is_code_exists(code):
    return TicketCode.objects.filter(code=code).count() > 0


def is_code_unconsumed(code):
    # if the code doesn't exist, also returns false
    if is_code_exists(code):
        return TicketCode.objects.get(code=code).is_unconsumed
    else:
        return False


def is_recipient_exists(recipient):
    return recipient in STUDENTS
