from django import forms
from django.core.exceptions import ValidationError
from .models import TicketCode
from .input_validation import is_code_exists, is_code_unconsumed, is_recipient_exists
from .class_lookup import STUDENTS
from .constants import MaxLengths


# the form that admins use to individually generate a code
class GeneratorForm(forms.Form):
    item_type = forms.ChoiceField(choices=[
            ('Chocolate', 'Chocolate'),
            ('Rose', 'Rose'),
            ('Serenade', 'Serenade'),
            ('Special Serenade', 'Special Serenade')
        ])


# the form that users use to redeem their code
class TicketForm(forms.Form):
    code = forms.CharField(label='Code', max_length=MaxLengths.TICKET_CODE, min_length=MaxLengths.TICKET_CODE)
    period = forms.ChoiceField(required=False, choices=[("-", "-"), (1, 1), (2, 2), (3, 3), (4, 4)])

    students = [(student_id, f"{student_dict['Name']} [{student_dict['ARC']}]")
                for student_id, student_dict in STUDENTS.items()]
    students.insert(0, (" ", ""))
    recipient_id = forms.ChoiceField(choices=students)      # note: will be stored as an ID

    templates = [
        (1, "Classic Ticket"),
        (2, "Clean Ticket")
    ]

    """If typed"""
    recipient_nickname = forms.CharField(max_length=MaxLengths.TICKET_RECIPIENT_NICKNAME, required=False)
    message = forms.CharField(max_length=MaxLengths.TICKET_MESSAGE, required=False)
    sender = forms.CharField(max_length=MaxLengths.TICKET_SENDER, required=False)
    typed_template = forms.ChoiceField(choices=templates, required=False)

    """If handwritten"""
    is_handwritten = forms.ChoiceField(required=True, choices=[(True, "Handwritten"), (False, 'Typed')])
    handwritten_message = forms.CharField(min_length=10, required=False)    # the dataURL of the png image
    handwriting_templates = templates[:]
    handwriting_templates.insert(0, (0, 'Blank'))
    handwriting_template = forms.ChoiceField(choices=handwriting_templates, required=False)

    def clean_code(self):
        # verifies that the code is valid and hasn't already been used
        code = self.cleaned_data['code'].upper()
        if not is_code_exists(code):
            raise ValidationError('This is not a valid code.')
        if not is_code_unconsumed(code):
            raise ValidationError('This code has already been used.')
        return code

    def clean_recipient_id(self):
        # verifies that the recipient actually exists
        recipient = self.cleaned_data['recipient_id'].upper()
        if not is_recipient_exists(recipient):
            raise ValidationError('This recipient does not exist.')
        return recipient

    def clean_recipient_nickname(self):
        recipient_nickname = self.cleaned_data['recipient_nickname']
        if not recipient_nickname.isascii():
            raise ValidationError('Can only use regular (ASCII) characters.')
        return recipient_nickname

    def clean_message(self):
        message = self.cleaned_data['message']
        if not message.isascii():
            raise ValidationError('Can only use regular (ASCII) characters.')
        return message

    def clean_sender(self):
        sender = self.cleaned_data['sender']
        if not sender.isascii():
            raise ValidationError('Can only use regular (ASCII) characters.')
        return sender

    def clean(self):
        # verifies that the period chosen is valid (if special serenade)
        cleaned_data = super().clean()
        if 'code' in cleaned_data:
            item_type = TicketCode.objects.filter(code=cleaned_data['code'])[0].item_type
            if item_type == "Special Serenade":
                period = cleaned_data['period']
                if period == "-":
                    raise ValidationError('Please choose a period')
                # I'm hard coding it because converting to int gives too many errors if it's not convertable
                elif not (period == "1" or period == "2" or period == "3" or period == "4"):
                    raise ValidationError('This is an invalid period.')
