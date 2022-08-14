from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from .class_lookup import STUDENTS
from .constants import MaxLengths


class TicketCodePDF(models.Model):
    num_of_items = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1), MaxValueValidator(3000)],
                                               help_text="The number of codes you want to generate. "
                                                         "Multiple of 100 recommended.")

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

    date = models.DateTimeField(default=timezone.now, verbose_name="Date Created")

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

    # links ticket codes to the pdf which created them. can also be null if created individually
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

    ss_period = models.PositiveIntegerField(null=True, blank=True, verbose_name="Special Serenade Period",
                                            help_text="The period that the special serenade is requested to be in.")

    is_handwritten = models.BooleanField(default=False)
    message = models.TextField(null=True, blank=True,
                               help_text="This is the DataURL of the message image. "
                                         "Leave it blank if you are manually creating the ticket.")

    # links ticket to the code which made it. can also be null if it was manually created by prefect
    code = models.OneToOneField(TicketCode, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="Corresponding TicketCode (optional)",
                                help_text="Links the ticket to the code which made it. "
                                          "Leave it blank if you are manually creating the ticket.")

    period = models.PositiveIntegerField(null=True, blank=True, help_text="The period chosen by the ticket sorter.")
    p1 = models.CharField(null=True, blank=True, max_length=4, verbose_name="Period 1 Classroom")
    p2 = models.CharField(null=True, blank=True, max_length=4, verbose_name="Period 2 Classroom")
    p3 = models.CharField(null=True, blank=True, max_length=4, verbose_name="Period 3 Classroom")
    p4 = models.CharField(null=True, blank=True, max_length=4, verbose_name="Period 4 Classroom")

    sort_order = models.PositiveIntegerField(null=True, blank=True,
                                             help_text="Used to determine what order the tickets "
                                                       "should be when printing.")

    def __str__(self):
        return f'{self.recipient_id} ({self.item_type})'

    def clean(self):
        if self.item_type == "Special Serenade":
            if self.ss_period is None:
                raise ValidationError("Must specify a period for special serenade.")
            else:
                if not 1 <= self.ss_period <= 4:
                    raise ValidationError("Period must be between 1 and 4 (inclusive).")
        if self.recipient_id not in STUDENTS:
            raise ValidationError("Invalid Recipient (Student ID not found).")

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['sort_order', 'pk']


class SortTicketsRequest(models.Model):
    num_serenaders = models.IntegerField(default=10, verbose_name="Number of serenading delivery groups")
    num_non_serenaders = models.IntegerField(default=10, verbose_name="Number of non-serenading delivery")
    max_serenades_per_class = models.IntegerField(default=2, verbose_name="Max number of serenades per class visit",
                                                  help_text="Lower values increase number of class visits required and "
                                                            "shifts load towards serenading groups. "
                                                            "Set to 0 to disable limit.")
    max_non_serenades_per_serenading_class = models.IntegerField(default=3,
                                                                 verbose_name="Max number of non-serenades per "
                                                                              "class visit",
                                                                 help_text="Only enforced for classes with at least "
                                                                           "one serenade. Lower values increase number "
                                                                           "of class visits required and shifts load "
                                                                           "towards non-serenading groups. Set to 0 to "
                                                                           "disable limit.")
    extra_special_serenades = models.BooleanField(default=True,
                                                  help_text="Special serenades will not be grouped with regular "
                                                            "serenades (no promises). "
                                                            "Increases number of class visits required.")
    enforce_distribution = models.BooleanField(default=True,
                                               help_text="More strictly force tickets to be split over multiple "
                                                         "periods. Ensures that people do not receive all their items "
                                                         "at once (no promises). "
                                                         "Increases number of class visits required.")

    date = models.DateTimeField(default=timezone.now, help_text="Date created")

    class Meta:
        verbose_name = "Sort Tickets Request"
        verbose_name_plural = "Sort Tickets Requests"


class DeliveryGroup(models.Model):
    code = models.CharField(max_length=3)
    is_serenading_group = models.BooleanField()
    is_printed = models.BooleanField(default=False)
    sort_request = models.ForeignKey(SortTicketsRequest, on_delete=models.CASCADE)
    tickets = models.ManyToManyField(Ticket)

    class Meta:
        verbose_name = "Delivery Group"
        verbose_name_plural = "Delivery Groups"
