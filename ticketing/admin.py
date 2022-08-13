from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q
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
    list_display = ('pk', 'num_serenaders', 'num_non_serenaders', 'url', 'date')
    actions = ('delete_queryset_and_children',)

    @admin.display(description='URL')
    def url(self, obj):
        return reverse("ticketing:tickets", args=[obj.pk])

    def save_model(self, request, obj, form, change):
        num_tickets = Ticket.objects.count()
        if num_tickets < obj.num_serenaders + obj.num_non_serenaders:
            raise IndexError(f"Not enough tickets to do a sorting. {num_tickets} exist. "
                             f"At least {obj.num_serenaders + obj.num_non_serenaders} required.")
            return False
        super().save_model(request=request, obj=obj, form=form, change=change)
        tickets = Ticket.objects.all()
        groups_split = sort_tickets(tickets, obj.num_serenaders, obj.num_non_serenaders,
                                    max_serenades_per_class=obj.max_serenades_per_class,
                                    max_non_serenades_per_class=obj.max_non_serenades_per_class,
                                    extra_special_serenades=obj.extra_special_serenades,
                                    enforce_distribution=obj.enforce_distribution,
                                    delivery_group_balance=obj.delivery_group_balance)
        for is_serenading, groups in groups_split.items():
            for group in groups:
                tickets = [Ticket.objects.get(pk=ticket.pk) for ticket in group.tickets]
                delivery_group = DeliveryGroup(
                    code=group.name,
                    is_serenading_group=is_serenading,
                    sort_request=obj
                )
                delivery_group.save()
                delivery_group.tickets.add(*tickets)

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(reverse(f"ticketing:tickets", args=[obj.pk]))

    def delete_model(self, request, obj):
        if os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{obj.pk}"):
            os.rmdir(f"{DirectoryLocations().SORTED_TICKETS}/{obj.pk}")
        super().delete_model(request=request, obj=obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{obj.pk}"):
                os.rmdir(f"{DirectoryLocations().SORTED_TICKETS}/{obj.pk}")
        super().delete_queryset(request=request, queryset=queryset)

    @admin.action(description="Delete selected SortTicketRequests and all the DeliveryGroups they generated")
    def delete_queryset_and_children(self, request, queryset):
        for obj in queryset:
            for child in obj.deliverygroup_set.all():
                child.delete()
        self.delete_queryset(request=request, queryset=queryset)


class DeliveryGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_serenading_group', 'num_serenades', 'num_non_serenades', 'sort_request')

    @admin.display(description='Number of Serenade Tickets')
    def num_serenades(self, obj):
        return obj.tickets.filter(Q(item_type="Serenade") | Q(item_type="Special Serenade")).count()

    @admin.display(description='Number of Non-serenade Tickets')
    def num_non_serenades(self, obj):
        return obj.tickets.filter(Q(item_type="Chocolate") | Q(item_type="Rose")).count()

    def delete_model(self, request, obj):
        sort_request = obj.sort_request
        if os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{sort_request.pk}/{obj.pk}.pdf"):
            os.remove(f"{DirectoryLocations().SORTED_TICKETS}/{sort_request.pk}/{obj.pk}.pdf")
        super().delete_model(request=request, obj=obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            sort_request = obj.sort_request
            if os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{sort_request.pk}/{obj.pk}.pdf"):
                os.remove(f"{DirectoryLocations().SORTED_TICKETS}/{sort_request.pk}/{obj.pk}.pdf")
        super().delete_queryset(request=request, queryset=queryset)


admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketCode, TicketCodeAdmin)
admin.site.register(TicketCodePDF, TicketCodePDFAdmin)
admin.site.register(SortTicketsRequest, SortTicketAdmin)
admin.site.register(DeliveryGroup, DeliveryGroupAdmin)

admin.site.site_header = "BSHS Valentine's Day Ticketing System"
admin.site.site_title = "BSHS"
