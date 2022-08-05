from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .constants import DirectoryLocations
from .class_lookup import STUDENTS
from .models import Ticket, TicketCode, TicketCodePDF, SortTicketsRequest, DeliveryGroup
from .code_generator import CodesToPDF, generate_codes
from .ticket_sorter import sort_tickets
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

    @admin.action(description="Delete selected Ticket Codes PDFs and all the codes they generated")
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
    list_display = ('recipient', 'item_type', 'period', 'is_handwritten',)
    actions = ('delete_tickets_and_ticket_codes',)

    @admin.display(description="Recipient")
    def recipient(self, obj):
        return f"{STUDENTS[obj.recipient_id]['Name']} [{STUDENTS[obj.recipient_id]['ARC']}]"

    @admin.action(description="Delete selected Tickets and the Ticket Codes which made them.")
    def delete_tickets_and_ticket_codes(self, request, queryset):
        for obj in queryset:
            ticket_code = obj.code
            if ticket_code is not None:
                ticket_code.delete()
        super().delete_queryset(request=request, queryset=queryset)


class SortTicketAdmin(admin.ModelAdmin):
    list_display = ('pk', 'num_serenaders', 'num_non_serenaders','url', 'date')

    @admin.display(description='URL')
    def url(self, obj):
        return reverse("ticketing:codepdf", args=[obj.pk])

    def save_model(self, request, obj, form, change):
        num_tickets = Ticket.objects.count()
        if num_tickets < obj.num_serenaders + obj.num_non_serenaders:
            raise IndexError(f"Not enough tickets to do a sorting. {num_tickets} exist. "
                             f"At least {obj.num_serenaders + obj.num_non_serenaders} required.")
            return False
        super().save_model(request=request, obj=obj, form=form, change=change)
        tickets = Ticket.objects.all()
        groups_split = sort_tickets(tickets, obj.num_serenaders, obj.num_non_serenaders, obj.max_serenades_per_class,
                                    obj.max_non_serenades_per_serenading_class, obj.extra_special_serenades)
        for is_serenading, groups in groups_split.items():
            for index, group in enumerate(groups):
                tickets = [Ticket.objects.get(code=ticket.code) for ticket in group]
                code = f"{'S' if is_serenading else 'N'}{index + 1}"
                delivery_group = DeliveryGroup(
                    code=code,
                    is_serenading_group=is_serenading,
                    sort_request=obj
                )
                delivery_group.tickets.add(*tickets)
                delivery_group.save()

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(reverse(f"ticketing:tickets/{obj.pk}", args=[obj.pk]))

    def delete_model(self, request, obj):
        if os.path.exists(f"{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf"):
            os.remove(f"{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf")
        super().delete_model(request=request, obj=obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if os.path.exists(f"{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf"):
                os.remove(f"{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf")
        super().delete_queryset(request=request, queryset=queryset)


class DeliveryGroupAdmin(admin.ModelAdmin):
    list_display = ('sort_request', 'code')


admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketCode, TicketCodeAdmin)
admin.site.register(TicketCodePDF, TicketCodePDFAdmin)
admin.site.register(SortTicketsRequest, SortTicketAdmin)
admin.site.register(DeliveryGroup, DeliveryGroupAdmin)

admin.site.site_header = "BSHS Valentine's Day Ticketing System"
admin.site.site_title = "BSHS"
