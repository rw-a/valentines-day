from .models import TicketCode
from .class_lookup import STUDENTS


def is_code_exists(code):
    for ticket in TicketCode.objects.all():
        # checks if this code has been registered to a code
        if ticket.code.upper() == code.upper():
            return True
    return False


def is_code_unconsumed(code):
    # if the code doesn't exist, also returns false
    for ticket in TicketCode.objects.all():
        # checks if this code has been registered to a code
        if ticket.code.upper() == code.upper():
            if ticket.is_unconsumed:
                return True
            else:
                return False
    return False


def is_recipient_exists(recipient):
    if recipient.upper() in STUDENTS:
        return True
    else:
        return False
