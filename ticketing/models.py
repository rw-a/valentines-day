import re
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models.indexes import Index
from .constants import MaxLengths, TEMPLATES
from .timetable_parser import BAD_ROOM_FORMAT


PERIOD_CHOICES = [
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4)
]


class SortTicketsRequest(models.Model):
    num_serenaders = models.IntegerField(
        default=10, validators=[MaxValueValidator(100), MinValueValidator(1)],
        verbose_name="Number of serenading delivery groups")
    num_non_serenaders = models.IntegerField(
        default=10, validators=[MaxValueValidator(100), MinValueValidator(1)],
        verbose_name="Number of non-serenading delivery groups")

    date = models.DateTimeField(default=timezone.now, help_text="Date created")

    def __str__(self):
        return f"Sort Request {self.pk} ({self.date})"

    class Meta:
        verbose_name = "Sort Tickets Request"


class DeliveryGroup(models.Model):
    code = models.CharField(max_length=10)

    is_serenading_group = models.BooleanField()

    # A JSON list containing which parts have been printed as numbers (e.g. [1, 2, 4])
    parts_printed = models.JSONField()

    sort_request = models.ForeignKey(SortTicketsRequest, on_delete=models.CASCADE)

    date = models.DateTimeField(default=timezone.now, help_text="Date created")

    def __str__(self):
        return f"Delivery Group: {self.code}"

    class Meta:
        verbose_name = "Delivery Group"


class Classroom(models.Model):
    period = models.PositiveIntegerField(choices=PERIOD_CHOICES)

    original_name = models.CharField(max_length=100)
    clean_name = models.CharField(max_length=100, blank=True, null=True)

    @property
    def is_bad(self) -> bool:
        return bool(re.match(BAD_ROOM_FORMAT, self.clean_name))

    @property
    def tickets(self):
        if self.period == 1:
            return self.tickets_p1.all()
        elif self.period == 2:
            return self.tickets_p2.all()
        elif self.period == 3:
            return self.tickets_p3.all()
        elif self.period == 4:
            return self.tickets_p4.all()

    @property
    def recipients(self):
        if self.period == 1:
            return self.recipients_p1.all()
        elif self.period == 2:
            return self.recipients_p2.all()
        elif self.period == 3:
            return self.recipients_p3.all()
        elif self.period == 4:
            return self.recipients_p4.all()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        # Derive clean name
        dotless_name = self.original_name.replace('.', '')
        clean_name = re.sub("([A-Z])G", r"\g<1>0", dotless_name)
        self.clean_name = clean_name

        super().save()

    def __str__(self):
        return f"{self.period}-{self.clean_name}"

    class Meta:
        verbose_name = "Classroom"

        indexes = [
            Index(fields=['period', 'original_name'])
        ]

        unique_together = [
            ['period', 'original_name']
        ]


class Recipient(models.Model):
    # Currently id = full name + arc class
    recipient_id = models.CharField(max_length=250, unique=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)

    arc = models.CharField(max_length=10)

    grade = models.IntegerField(choices=[
        (0, "Teacher"),
        (7, 7),
        (8, 8),
        (9, 9),
        (10, 10),
        (11, 11),
        (12, 12)
    ])

    p1 = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, related_name='recipients_p1',
        null=True, blank=True, editable=False, verbose_name="Period 1 Classroom")
    p2 = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, related_name='recipients_p2',
        null=True, blank=True, editable=False, verbose_name="Period 2 Classroom")
    p3 = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, related_name='recipients_p3',
        null=True, blank=True, editable=False, verbose_name="Period 3 Classroom")
    p4 = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, related_name='recipients_p4',
        null=True, blank=True, editable=False, verbose_name="Period 4 Classroom")

    def __str__(self):
        return self.recipient_id

    class Meta:
        verbose_name = "Recipient"
        indexes = [
            Index(fields=['recipient_id'])
        ]


class TicketCodePDF(models.Model):
    num_of_items = models.PositiveIntegerField(
        default=100, validators=[MinValueValidator(1), MaxValueValidator(3000)],
        help_text="The number of codes you want to generate. Multiple of 100 recommended."
    )

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
        verbose_name_plural = "Ticket Code PDFs"


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
    pdf = models.ForeignKey(
        TicketCodePDF, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Corresponding TicketCodePDF (optional)",
        help_text="Links the code to the PDF which generated it. Leave it blank if you are "
                  "manually creating the code (which you probably shouldn't be doing anyway).")

    date = models.DateTimeField(default=timezone.now, help_text="Date created")

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
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE)

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
    template = models.CharField(max_length=100)

    ss_period = models.PositiveIntegerField(
        choices=PERIOD_CHOICES, null=True, blank=True, verbose_name="Special Serenade Period",
        help_text="The period that the special serenade is requested to be in."
    )

    is_handwritten = models.BooleanField(default=False)

    # links ticket to the code which made it. can also be null if it was manually created by prefect
    code = models.OneToOneField(
        TicketCode, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Corresponding TicketCode (optional)",
        help_text="Links the ticket to the code which made it. "
                  "Leave it blank if you are manually creating the ticket.")

    date = models.DateTimeField(default=timezone.now, help_text="Date created")

    def __str__(self):
        return f'{self.recipient_id} ({self.item_type})'

    def clean(self):
        if self.item_type == "Special Serenade" and self.ss_period is None:
            raise ValidationError("Must specify a period for special serenade.")

        if self.template != "Blank" and self.template not in TEMPLATES.keys():
            raise ValidationError(f"Template '{self.template}' not found (case sensitive).")

    class Meta:
        verbose_name = "Ticket"


class SortedTicket(models.Model):
    """
    Represents the information of a ticket based on the sorting results of a SortTicketsRequest.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    delivery_group = models.ForeignKey(DeliveryGroup, on_delete=models.CASCADE)

    period = models.PositiveIntegerField(
        null=True, blank=True, editable=False,
        help_text="The period chosen by the ticket sorter. "
                  "Will be automatically determined so do not touch.")
    p1 = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, related_name='tickets_p1',
        null=True, blank=True, editable=False, verbose_name="Period 1 Classroom",
        help_text="Will be automatically determined so do not touch.")
    p2 = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, related_name='tickets_p2',
        null=True, blank=True, editable=False, verbose_name="Period 2 Classroom",
        help_text="Will be automatically determined so do not touch.")
    p3 = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, related_name='tickets_p3',
        null=True, blank=True, editable=False, verbose_name="Period 3 Classroom",
        help_text="Will be automatically determined so do not touch.")
    p4 = models.ForeignKey(
        Classroom, on_delete=models.SET_NULL, related_name='tickets_p4',
        null=True, blank=True, editable=False, verbose_name="Period 4 Classroom",
        help_text="Will be automatically determined so do not touch.")

    sort_order = models.PositiveIntegerField(
        null=True, blank=True, editable=False,
        help_text="Used to determine what order the tickets should be when printing. "
                  "Will be automatically determined so do not touch.")

    @property
    def has_no_choice(self) -> bool:
        num_periods_available = 0

        if self.p1 is not None:
            num_periods_available += 1

        if self.p2 is not None:
            num_periods_available += 1

        if self.p3 is not None:
            num_periods_available += 1

        if self.p4 is not None:
            num_periods_available += 1

        return num_periods_available <= 1

    def __str__(self):
        return f"Ticket {str(self.ticket)} for request {self.delivery_group.sort_request.pk}"

    class Meta:
        verbose_name = "Sorted Ticket"
        ordering = ["sort_order"]
        indexes = [
            Index(fields=['sort_order'])
        ]
