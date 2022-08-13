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
import shutil
import random


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
    actions = ('delete_ticket_codes_and_tickets', 'generate_tickets')

    @admin.action(description="Delete selected TicketCodes and the Tickets which they made.")
    def delete_ticket_codes_and_tickets(self, request, queryset):
        for obj in queryset:
            if hasattr(obj, 'ticket'):
                ticket = obj.ticket
                if os.path.exists(f"{DirectoryLocations().REDEEMED_TICKETS}/{ticket.pk}.svg"):
                    os.remove(f"{DirectoryLocations().REDEEMED_TICKETS}/{ticket.pk}.svg")
                ticket.delete()
        super().delete_queryset(request=request, queryset=queryset)

    @admin.action(description="Randomly generate tickets from unconsumed TicketCodes. For testing use only!")
    def generate_tickets(self, request, queryset):
        existing_recipients = [ticket.recipient_id for ticket in Ticket.objects.all()]
        for index, ticket_code in enumerate(queryset):
            if ticket_code.is_unconsumed:
                # 50% chance to double up a person
                if random.random() > 0.5 and len(existing_recipients) > 0:
                    recipient_id = random.choice(existing_recipients)
                else:
                    recipient_id = random.choice(list(STUDENTS.keys()))
                existing_recipients.append(recipient_id)

                recipient_name = STUDENTS[recipient_id]['Name']
                message = f'<?xml version="1.0" encoding="UTF-8" standalone="no" ?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="600" height="356" viewBox="0 0 600 356" xml:space="preserve"><desc>Created with Fabric.js 5.2.1</desc><defs></defs><g transform="matrix(1 0 0 1 57.01 77.45)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ><tspan x="-38.51" y="9.42" >{recipient_name}</tspan></text></g><g transform="matrix(1 0 0 1 226.26 182.44)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ><tspan x="-55.76" y="9.42" >{index}</tspan></text></g><g transform="matrix(1 0 0 1 103.5 229.45)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ></text></g><g transform="matrix(1 0 0 1 103.5 277.45)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ></text></g><g transform="matrix(1 0 0 1 177.79 325.45)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ><tspan x="-20.29" y="9.42" >TEST</tspan></text></g></svg>'

                ticket = Ticket(
                    recipient_id=recipient_id,
                    item_type=ticket_code.item_type,
                    is_handwritten=False,
                    template=1,
                    message=message,
                    code=ticket_code
                )
                if ticket.item_type == "Special Serenade":
                    ticket.ss_period = random.choice([1, 2, 3, 4])
                ticket.save()

                # create the ticket file
                with open(f'{DirectoryLocations.REDEEMED_TICKETS}/{ticket.pk}.svg', 'wb') as file:
                    file.write(bytes(message, 'utf-8'))

                # mark the ticket code as consumed
                ticket_code.is_unconsumed = False
                ticket_code.save()


class TicketAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'item_type', 'is_handwritten', 'period', 'classroom', 'sort_order')
    actions = ('delete_tickets_and_ticket_codes',)

    @admin.display(description="Recipient")
    def recipient(self, obj):
        return f"{STUDENTS[obj.recipient_id]['Name']} [{STUDENTS[obj.recipient_id]['ARC']}]"

    @admin.display(description="Chosen Classroom")
    def classroom(self, obj):
        if obj.period is not None:
            return getattr(obj, f'p{obj.period}')
        else:
            return None

    def delete_model(self, request, obj):
        if os.path.exists(f"{DirectoryLocations().REDEEMED_TICKETS}/{obj.pk}.svg"):
            os.remove(f"{DirectoryLocations().REDEEMED_TICKETS}/{obj.pk}.svg")
        super().delete_model(request=request, obj=obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if os.path.exists(f"{DirectoryLocations().REDEEMED_TICKETS}/{obj.pk}.svg"):
                os.remove(f"{DirectoryLocations().REDEEMED_TICKETS}/{obj.pk}.svg")
        super().delete_queryset(request=request, queryset=queryset)

    @admin.action(description="Delete selected Tickets and the Ticket Codes which made them.")
    def delete_tickets_and_ticket_codes(self, request, queryset):
        for obj in queryset:
            ticket_code = obj.code
            if ticket_code is not None:
                ticket_code.delete()
        self.delete_queryset(request=request, queryset=queryset)


class SortTicketAdmin(admin.ModelAdmin):
    list_display = ('pk', 'num_serenaders', 'num_non_serenaders', 'url', 'date')
    actions = ('delete_queryset_and_children',)

    @admin.display(description='URL')
    def url(self, obj):
        return reverse("ticketing:tickets", args=[obj.pk])

    def save_model(self, request, obj, form, change):
        super().save_model(request=request, obj=obj, form=form, change=change)
        tickets = Ticket.objects.all()
        groups_split = sort_tickets(tickets, obj.num_serenaders, obj.num_non_serenaders,
                                    max_serenades_per_class=obj.max_serenades_per_class,
                                    max_non_serenades_per_class=obj.max_non_serenades_per_class,
                                    extra_special_serenades=obj.extra_special_serenades,
                                    enforce_distribution=obj.enforce_distribution,
                                    delivery_group_balance=obj.delivery_group_balance)
        for is_serenading, groups in groups_split.items():
            for group_index, group in enumerate(groups):
                tickets = []
                for ticket_index, ticket_to_sort in enumerate(group.tickets):
                    ticket = Ticket.objects.get(pk=ticket_to_sort.pk)
                    ticket.p1 = ticket_to_sort.p1.clean_name
                    ticket.p2 = ticket_to_sort.p2.clean_name
                    ticket.p3 = ticket_to_sort.p3.clean_name
                    ticket.p4 = ticket_to_sort.p4.clean_name
                    ticket.period = ticket_to_sort.chosen_period
                    sort_order = int(f"{'1' if is_serenading else '0'}{group_index + 1}{str(ticket_index).zfill(4)}")
                    ticket.sort_order = sort_order
                    ticket.save()
                    tickets.append(ticket)

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
            shutil.rmtree(f"{DirectoryLocations().SORTED_TICKETS}/{obj.pk}")
        super().delete_model(request=request, obj=obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{obj.pk}"):
                shutil.rmtree(f"{DirectoryLocations().SORTED_TICKETS}/{obj.pk}")
        super().delete_queryset(request=request, queryset=queryset)

    @admin.action(description="Delete selected SortTicketRequests and all the DeliveryGroups they generated")
    def delete_queryset_and_children(self, request, queryset):
        for obj in queryset:
            for group in obj.deliverygroup_set.all():
                group.delete()
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
        if os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{sort_request.pk}/{obj.code}.pdf"):
            os.remove(f"{DirectoryLocations().SORTED_TICKETS}/{sort_request.pk}/{obj.code}.pdf")
        super().delete_model(request=request, obj=obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            sort_request = obj.sort_request
            if os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{sort_request.pk}/{obj.code}.pdf"):
                os.remove(f"{DirectoryLocations().SORTED_TICKETS}/{sort_request.pk}/{obj.code}.pdf")
        super().delete_queryset(request=request, queryset=queryset)


admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketCode, TicketCodeAdmin)
admin.site.register(TicketCodePDF, TicketCodePDFAdmin)
admin.site.register(SortTicketsRequest, SortTicketAdmin)
admin.site.register(DeliveryGroup, DeliveryGroupAdmin)

admin.site.site_header = "BSHS Valentine's Day Ticketing System"
admin.site.site_title = "BSHS"
