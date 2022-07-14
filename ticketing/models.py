from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from .class_lookup import STUDENTS
from .constants import MaxLengths


class TicketCodePDF(models.Model):
    num_of_items = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(3000)],
                                               help_text="The number of codes you want to generate")

    item_type = models.CharField(
        max_length=20,
        choices=[
            ('Chocolate', 'Chocolate'),
            ('Rose', 'Rose'),
            ('Serenade', 'Serenade'),
            ('Special Serenade', 'Special Serenade')
        ],
        default='Serenade'
    )

    date = models.DateTimeField(default=timezone.now, help_text="Date created")

    def __str__(self):
        return f'<{self.pk}> {self.num_of_items} {self.item_type}s'

    class Meta:
        verbose_name = "Ticket Code PDF"
        verbose_name_plural = "Ticket Codes PDFs"


class TicketCode(models.Model):
    code = models.CharField(max_length=MaxLengths.TICKET_CODE)
    is_unconsumed = models.BooleanField(default=True)

    item_type = models.CharField(
        max_length=20,
        choices=[
            ('Chocolate', 'Chocolate'),
            ('Rose', 'Rose'),
            ('Serenade', 'Serenade'),
            ('Special Serenade', 'Special Serenade')
        ],
        default='Serenade'
    )

    # links ticket codes to the pdf which created them. can also be ull if created individually
    pdf = models.ForeignKey(TicketCodePDF, on_delete=models.SET_NULL, null=True, blank=True,
                            verbose_name="Corresponding TicketCodePDF (optional)",
                            help_text="Links the code to the PDF which generated it. "
                                      "Leave it blank if you are manually creating the code "
                                      "(which you probably shouldn't be doing anyways).")

    def __str__(self):
        if self.is_unconsumed:
            return f'!{self.item_type} ({self.code})'
        else:
            return f'{self.item_type} ({self.code})'

    def clean(self):
        if len(self.code) != MaxLengths.TICKET_CODE:
            raise ValidationError(f"Code must be exactly {MaxLengths.TICKET_CODE} characters long.")

    class Meta:
        verbose_name = "Ticket Code"
        verbose_name_plural = "Ticket Codes"


class Ticket(models.Model):
    recipient_id = models.CharField(max_length=12,  # student ID length is 11
                                    help_text="The Student ID of the recipient of this ticket")
    item_type = models.CharField(
        max_length=20,
        choices=[
            ('Chocolate', 'Chocolate'),
            ('Rose', 'Rose'),
            ('Serenade', 'Serenade'),
            ('Special Serenade', 'Special Serenade')
        ],
        default='Serenade'
    )
    template = models.IntegerField()

    period = models.PositiveIntegerField(null=True, blank=True, help_text="Only add if this is a special serenade.")

    # These are only if the ticket is typed instead of handwritten
    recipient_nickname = models.CharField(max_length=MaxLengths.TICKET_RECIPIENT_NICKNAME, null=True, blank=True,
                                          help_text="The nickname of the recipient given by the sender")
    message = models.CharField(max_length=MaxLengths.TICKET_MESSAGE, null=True, blank=True)
    sender = models.CharField(max_length=MaxLengths.TICKET_SENDER, null=True, blank=True)

    # These are if the ticket is handwritten instead of typed
    is_handwritten = models.BooleanField(default=False)
    handwritten_message = models.TextField(null=True, blank=True)

    # links ticket to the code which made it. can also be null if it was manually created by prefect
    code = models.OneToOneField(TicketCode, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="Corresponding TicketCode (optional)",
                                help_text="Links the ticket to the code which made it. "
                                          "Leave it blank if you are manually creating the ticket "
                                          "(like you are doing so right now).")

    def __str__(self):
        return f'{self.recipient_id} ({self.item_type})'

    def clean(self):
        if self.item_type == "Special Serenade":
            if self.period is None:
                raise ValidationError("Must specify a period for special serenade.")
            else:
                if not 1 <= self.period <= 4:
                    raise ValidationError("Period must be between 1 and 4 (inclusive).")
        if self.recipient_id not in STUDENTS:
            raise ValidationError("Invalid Recipient (Student ID not found).")

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"


class SortTicketsRequest(models.Model):
    num_serenaders = models.IntegerField(default=10)
    num_non_serenaders = models.IntegerField(default=10)
    max_serenades_per_class = models.IntegerField(default=5)
    max_non_serenades_per_serenading_class = models.IntegerField(default=10)
    extra_special_serenades = models.BooleanField(default=True)
    date = models.DateTimeField(default=timezone.now, help_text="Date created")
