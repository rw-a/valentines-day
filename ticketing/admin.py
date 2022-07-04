from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Ticket, TicketCode, TicketCodePDF
from .code_generator import CodesToPDF, generate_codes
from .constants import DirectoryLocations
from .class_lookup import STUDENTS
import os


class TicketCodePDFAdmin(admin.ModelAdmin):
    fields = ('num_of_items', 'item_type', 'date')
    list_display = ('pk', 'num_of_items', 'item_type', 'url')
    actions = ['delete_queryset_and_children']

    @admin.display(description='URL')
    def url(self, obj):
        return reverse("ticketing:codepdf", args=[obj.pk])

    def save_model(self, request, obj, form, change):
        super().save_model(request=request, obj=obj, form=form, change=change)
        ticket_codes = generate_codes(obj.num_of_items)
        CodesToPDF(ticket_codes, obj.item_type, f'{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf')
        for code in ticket_codes:
            ticket_code = TicketCode(
                code=code,
                item_type=obj.item_type,
                pdf=obj
            )
            ticket_code.save()

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(reverse("ticketing:codepdf", args=[obj.pk]))

    def delete_model(self, request, obj):
        if os.path.exists(f"{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf"):
            os.remove(f"{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf")
        super().delete_model(request=request, obj=obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if os.path.exists(f"{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf"):
                os.remove(f"{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf")
        super().delete_queryset(request=request, queryset=queryset)

    @admin.action(description="Delete selected Ticket Code PDFs and all the codes they generated")
    def delete_queryset_and_children(self, request, queryset):
        for obj in queryset:
            for child in obj.ticketcode_set.all():
                child.delete()
        self.delete_queryset(request=request, queryset=queryset)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # obj is not None, so this is an edit
            return ['num_of_items', 'item_type', 'date']  # Return a list or tuple of readonly fields' names
        else:  # This is an addition
            return []


class TicketCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'item_type', 'is_unconsumed',)
    actions = ('delete_ticket_codes_and_tickets',)

    @admin.action(description="Delete selected TicketCodes and the Tickets which they made.")
    def delete_ticket_codes_and_tickets(self, request, queryset):
        for obj in queryset:
            if hasattr(obj, 'ticket'):
                ticket = obj.student
                ticket.delete()
        super().delete_queryset(request=request, queryset=queryset)


class TicketAdmin(admin.ModelAdmin):
    list_display = ('recipient_nickname', 'recipient_id', 'item_type', 'period', 'is_handwritten',)
    actions = ('delete_tickets_and_ticket_codes',)

    @admin.display(description="Recipient")
    def recipient_name(self, obj):
        return STUDENTS[obj.recipient_name]['Name']

    @admin.action(description="Delete selected Tickets and the Ticket Codes which made them.")
    def delete_tickets_and_ticket_codes(self, request, queryset):
        for obj in queryset:
            ticket_code = obj.code
            if ticket_code is not None:
                ticket_code.delete()
        super().delete_queryset(request=request, queryset=queryset)


admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketCode, TicketCodeAdmin)
admin.site.register(TicketCodePDF, TicketCodePDFAdmin)

admin.site.site_header = "BSHS Valentine's Day Ticketing System"
admin.site.site_title = "BSHS"
