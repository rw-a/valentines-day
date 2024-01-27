from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q
from django.utils.html import format_html
from .constants import DirectoryLocations
from .models import (Ticket, TicketCode, TicketCodePDF, SortTicketsRequest, DeliveryGroup,
                     Recipient, Classroom, SortedTicket)
from .code_generator import CodesToPDF, generate_codes
from .ticket_sorter import TicketSorter
from vdaywebsite.settings import ORG_NAME, NUM_TICKETS_PER_PDF
import os
import math
import shutil
import random


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('clean_name', 'original_name', 'period')


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('recipient_id', 'p1', 'p2', 'p3', 'p4')


@admin.register(TicketCodePDF)
class TicketCodePDFAdmin(admin.ModelAdmin):
    fields = ('num_of_items', 'item_type', 'date')
    list_display = ('pk', 'num_of_items', 'item_type', 'url')
    actions = ['delete_queryset_and_children']
    date_hierarchy = "date"

    @admin.display(description='URL')
    def url(self, obj):
        url = reverse("ticketing:codepdf", args=[obj.pk])
        return format_html("<a href='{url}'>{url}</a>", url=url)

    def save_model(self, request, obj, form, change):
        super().save_model(request=request, obj=obj, form=form, change=change)

        codes = generate_codes(obj.num_of_items)
        CodesToPDF(
            codes,
            obj.item_type,
            f'{DirectoryLocations().GENERATED_TICKET_CODES}/{obj.pk}.pdf'
        )

        ticket_codes = [
            TicketCode(
                code=code,
                item_type=obj.item_type,
                pdf=obj
            )
            for code in codes
        ]

        TicketCode.objects.bulk_create(ticket_codes)

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
        # Delete children ticket codes first
        for obj in queryset:
            obj.ticketcode_set.all().delete()

        self.delete_queryset(request=request, queryset=queryset)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # obj is not None, so this is an edit
            return ['num_of_items', 'item_type', 'date']  # Return a list or tuple of readonly fields' names
        else:  # This is an addition
            return []


@admin.register(TicketCode)
class TicketCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'item_type', 'is_unconsumed',)
    actions = ('delete_ticket_codes_and_tickets', 'generate_tickets')
    date_hierarchy = "date"

    @admin.action(description="Delete selected TicketCodes and the Tickets which they made.")
    def delete_ticket_codes_and_tickets(self, request, queryset):
        for obj in queryset:
            if hasattr(obj, 'ticket'):
                ticket = obj.ticket
                if os.path.exists(f"{DirectoryLocations().REDEEMED_TICKETS}/{ticket.pk}.svg"):
                    os.remove(f"{DirectoryLocations().REDEEMED_TICKETS}/{ticket.pk}.svg")
                ticket.delete()
        super().delete_queryset(request=request, queryset=queryset)

    @admin.action(description="Randomly generate tickets from unconsumed TicketCodes. "
                              "For testing use only!")
    def generate_tickets(self, request, queryset):
        all_recipients = Recipient.objects.all()
        existing_recipients = [ticket.recipient for ticket in Ticket.objects.all()]

        for index, ticket_code in enumerate(queryset):
            if ticket_code.is_unconsumed:
                # 50% chance to double up a person
                if random.random() > 0.5 and len(existing_recipients) > 0:
                    recipient = random.choice(existing_recipients)
                else:
                    recipient = random.choice(all_recipients)
                existing_recipients.append(recipient)

                # Randomly choose whether handwritten or typed
                if random.random() > 0.5:
                    is_handwritten = False
                    message = f'<?xml version="1.0" encoding="UTF-8" standalone="no" ?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="600" height="356" viewBox="0 0 600 356" xml:space="preserve"><desc>Created with Fabric.js 5.2.1</desc><defs></defs><g transform="matrix(1 0 0 1 57.01 77.45)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ><tspan x="-38.51" y="9.42" >{recipient.full_name}</tspan></text></g><g transform="matrix(1 0 0 1 226.26 182.44)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ><tspan x="-55.76" y="9.42" >{index}</tspan></text></g><g transform="matrix(1 0 0 1 103.5 229.45)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ></text></g><g transform="matrix(1 0 0 1 103.5 277.45)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ></text></g><g transform="matrix(1 0 0 1 177.79 325.45)" style=""  >		<text xml:space="preserve" font-family="Calibri" font-size="30" font-style="normal" font-weight="normal" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(0,0,0); fill-rule: nonzero; opacity: 1; white-space: pre;" ><tspan x="-20.29" y="9.42" >TEST</tspan></text></g></svg>'
                else:
                    is_handwritten = True
                    message = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 3010 1790" width="1368.1817885272765" height="813.6363460012708"><path d="M 48.903,59.552 C 49.278,60.506 49.139,60.522 49.375,61.493" stroke-width="3.255" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 49.375,61.493 C 49.273,62.937 49.514,62.914 49.375,64.368" stroke-width="2.988" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 49.375,64.368 C 49.793,66.646 49.537,66.660 49.903,68.941" stroke-width="2.748" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 49.903,68.941 C 50.072,72.201 50.057,72.180 49.903,75.438" stroke-width="2.495" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 49.903,75.438 C 49.603,77.486 49.794,77.500 49.346,79.539" stroke-width="2.644" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 49.346,79.539 C 48.970,81.819 49.061,81.823 48.818,84.112" stroke-width="2.628" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 48.818,84.112 C 48.818,85.813 48.706,85.807 48.818,87.515" stroke-width="2.754" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 48.818,87.515 C 48.818,88.278 48.818,88.278 48.818,89.042" stroke-width="2.985" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 34.698,62.978 C 35.045,62.170 35.198,62.361 35.697,61.743" stroke-width="3.312" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 35.697,61.743 C 37.369,60.482 37.336,60.671 39.279,59.981" stroke-width="2.884" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 39.279,59.981 C 42.995,59.182 42.900,59.030 46.759,58.840" stroke-width="2.442" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 46.759,58.840 C 52.814,58.356 52.795,58.291 58.878,58.198" stroke-width="2.051" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 58.878,58.198 C 65.168,58.198 65.164,58.035 71.459,58.198" stroke-width="1.935" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 71.459,58.198 C 76.625,58.198 76.625,58.198 81.790,58.198" stroke-width="2.047" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 81.790,58.198 C 84.498,58.393 84.454,58.198 87.118,58.198" stroke-width="2.408" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 87.118,58.198 C 88.102,57.727 87.661,58.158 88.117,57.727" stroke-width="2.894" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 88.117,57.727 C 87.532,57.831 88.131,57.727 87.174,58.198" stroke-width="3.127" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 83.385,77.090 C 85.036,76.716 85.002,76.618 86.618,76.147" stroke-width="3.061" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 86.618,76.147 C 88.376,75.179 88.472,75.481 90.257,74.620" stroke-width="2.805" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 90.257,74.620 C 92.577,74.673 92.278,74.020 94.423,73.828" stroke-width="2.731" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 94.423,73.828 C 95.492,72.838 95.688,73.250 96.478,71.773" stroke-width="2.835" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 96.478,71.773 C 97.595,71.080 97.151,71.047 97.741,70.247" stroke-width="2.951" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 97.741,70.247 C 97.720,68.918 97.873,69.492 97.034,68.597" stroke-width="3.125" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 97.034,68.597 C 95.625,68.597 95.958,68.094 94.216,68.597" stroke-width="2.942" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 94.216,68.597 C 91.987,68.597 91.987,68.597 89.757,68.597" stroke-width="2.749" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 89.757,68.597 C 87.208,68.166 87.296,68.597 84.836,68.597" stroke-width="2.655" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 84.836,68.597 C 82.763,69.046 82.928,68.944 81.197,70.153" stroke-width="2.713" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 81.197,70.153 C 79.823,71.114 80.062,70.955 79.434,72.415" stroke-width="2.815" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 79.434,72.415 C 79.434,74.234 78.942,74.065 79.434,76.054" stroke-width="2.791" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 79.434,76.054 C 79.301,77.594 79.434,77.581 79.434,79.107" stroke-width="2.840" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 79.434,79.107 C 79.551,80.294 79.537,80.266 79.906,81.398" stroke-width="2.912" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 79.906,81.398 C 80.129,82.248 80.155,82.174 80.641,82.868" stroke-width="3.026" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 80.641,82.868 C 81.316,83.602 81.245,83.601 82.139,84.103" stroke-width="3.028" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 82.139,84.103 C 83.353,84.741 83.300,84.808 84.609,85.281" stroke-width="2.924" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 84.609,85.281 C 85.828,86.003 85.851,85.815 87.135,86.252" stroke-width="2.915" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 87.135,86.252 C 88.426,86.252 88.382,86.489 89.717,86.252" stroke-width="2.926" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 89.717,86.252 C 90.745,86.252 90.745,86.252 91.772,86.252" stroke-width="2.971" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 91.772,86.252 C 92.330,86.397 92.300,86.252 92.828,86.252" stroke-width="3.113" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 115.358,65.589 C 114.595,65.772 114.623,65.839 113.888,66.089" stroke-width="3.044" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 113.888,66.089 C 112.022,66.903 112.041,66.917 110.249,67.880" stroke-width="2.813" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 110.249,67.880 C 108.926,68.376 109.115,68.505 108.072,69.293" stroke-width="2.876" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 108.072,69.293 C 107.395,70.250 107.338,70.082 107.073,71.291" stroke-width="2.935" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 107.073,71.291 C 106.858,71.970 106.895,71.867 107.073,72.526" stroke-width="3.080" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 107.073,72.526 C 107.440,73.882 107.490,73.601 108.336,74.552" stroke-width="2.995" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 108.336,74.552 C 109.625,74.804 109.306,75.277 110.806,75.316" stroke-width="2.949" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 110.806,75.316 C 112.471,76.147 112.504,76.053 114.095,77.050" stroke-width="2.798" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 114.095,77.050 C 115.123,77.612 115.115,77.617 116.093,78.256" stroke-width="2.915" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 116.093,78.256 C 116.951,78.526 116.607,78.597 117.064,79.020" stroke-width="3.064" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 117.064,79.020 C 117.079,79.960 117.201,79.615 116.593,80.433" stroke-width="3.183" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 116.593,80.433 C 115.716,80.736 115.991,81.020 114.887,81.140" stroke-width="3.085" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 114.887,81.140 C 113.527,81.918 113.482,81.824 112.125,82.610" stroke-width="2.897" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 112.125,82.610 C 111.330,83.104 111.322,83.007 110.476,83.317" stroke-width="2.992" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 110.476,83.317 C 109.566,83.638 109.916,83.457 109.298,83.317" stroke-width="3.176" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 109.298,83.317 C 109.250,82.607 108.977,82.931 109.298,81.904" stroke-width="3.218" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 109.298,81.904 C 109.195,80.813 109.368,80.902 109.534,79.905" stroke-width="3.061" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 109.534,79.905 C 109.979,79.252 109.798,79.197 110.505,78.671" stroke-width="3.091" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 135.496,56.197 C 134.936,57.822 135.024,57.842 134.553,59.487" stroke-width="3.057" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 134.553,59.487 C 134.173,61.029 134.201,61.022 134.025,62.598" stroke-width="2.886" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 134.025,62.598 C 134.002,65.419 133.763,65.395 133.733,68.218" stroke-width="2.632" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 133.733,68.218 C 133.408,71.216 133.445,71.214 132.913,74.187" stroke-width="2.503" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 132.913,74.187 C 132.300,76.987 132.442,77.011 131.800,79.807" stroke-width="2.490" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 131.800,79.807 C 131.646,81.651 131.480,81.616 131.272,83.445" stroke-width="2.683" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 131.272,83.445 C 130.970,84.609 131.029,84.615 130.566,85.736" stroke-width="2.870" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 130.566,85.736 C 130.064,86.530 130.263,86.579 129.859,87.385" stroke-width="2.983" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 125.948,72.229 C 126.431,71.050 126.654,71.404 127.361,70.579" stroke-width="3.201" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 127.361,70.579 C 129.296,69.895 129.104,69.698 131.292,69.524" stroke-width="2.826" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 131.292,69.524 C 133.654,69.075 133.633,69.088 136.035,68.967" stroke-width="2.663" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 136.035,68.967 C 139.807,68.967 139.797,68.797 143.579,68.967" stroke-width="2.427" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 143.579,68.967 C 146.739,68.967 146.739,68.967 149.898,68.967" stroke-width="2.450" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 163.170,73.029 C 163.571,74.573 163.434,74.584 163.698,76.140" stroke-width="2.942" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 163.698,76.140 C 163.698,77.841 163.834,77.830 163.698,79.543" stroke-width="2.869" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 163.698,79.543 C 163.698,80.980 163.698,80.980 163.698,82.418" stroke-width="2.863" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 163.698,82.418 C 163.814,83.085 163.698,83.064 163.698,83.709" stroke-width="3.057" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 173.030,78.529 C 172.468,80.248 172.530,80.263 172.031,81.997" stroke-width="3.113" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 172.031,81.997 C 171.765,83.317 171.704,83.302 171.503,84.637" stroke-width="2.953" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 171.503,84.637 C 171.250,85.899 171.251,85.900 171.003,87.163" stroke-width="2.921" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 171.003,87.163 C 170.819,88.412 170.882,87.780 170.767,88.398" stroke-width="3.081" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 170.767,88.398 C 170.747,87.750 170.715,88.383 170.796,87.106" stroke-width="3.228" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 170.796,87.106 C 170.898,85.839 170.893,85.841 171.060,84.580" stroke-width="3.001" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 171.060,84.580 C 171.010,82.662 171.294,82.757 171.588,80.942" stroke-width="2.817" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 171.588,80.942 C 172.650,78.833 172.330,78.731 173.699,76.718" stroke-width="2.666" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 173.699,76.718 C 174.212,74.990 174.455,75.195 175.198,73.664" stroke-width="2.767" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 175.198,73.664 C 175.995,73.029 175.786,72.874 176.847,72.486" stroke-width="2.936" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 176.847,72.486 C 177.407,71.817 177.290,72.204 177.789,72.015" stroke-width="3.101" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 177.789,72.015 C 178.690,72.759 178.599,72.435 179.231,73.721" stroke-width="3.147" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 179.231,73.721 C 179.863,75.242 180.029,75.139 180.466,76.775" stroke-width="2.895" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 180.466,76.775 C 181.310,78.371 181.111,78.414 181.729,80.065" stroke-width="2.803" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 181.729,80.065 C 181.751,81.461 182.059,81.397 181.964,82.826" stroke-width="2.854" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 181.964,82.826 C 182.335,83.869 182.132,83.898 182.492,84.938" stroke-width="2.935" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 182.492,84.938 C 182.492,85.673 182.599,85.660 182.492,86.408" stroke-width="3.042" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 182.492,86.408 C 182.165,87.470 182.492,87.143 182.492,87.878" stroke-width="3.172" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 182.492,87.878 C 183.104,87.996 182.754,88.205 183.670,87.878" stroke-width="3.232" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 203.314,76.775 C 201.542,76.323 201.551,76.290 199.789,75.804" stroke-width="3.101" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 199.789,75.804 C 197.664,75.184 197.667,75.177 195.565,74.485" stroke-width="2.766" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 195.565,74.485 C 193.949,74.198 194.143,74.010 192.747,73.457" stroke-width="2.819" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 192.747,73.457 C 192.381,72.222 192.304,73.185 192.276,72.458" stroke-width="3.136" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 192.276,72.458 C 192.096,73.747 192.028,73.014 192.040,75.041" stroke-width="3.131" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 192.040,75.041 C 191.934,76.485 191.978,76.476 192.040,77.916" stroke-width="2.937" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 192.040,77.916 C 192.098,80.081 192.198,80.034 192.568,82.139" stroke-width="2.789" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 192.568,82.139 C 192.762,83.694 192.875,83.484 193.596,84.722" stroke-width="2.866" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 193.596,84.722 C 194.601,85.774 194.393,85.706 195.829,86.164" stroke-width="2.867" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 195.829,86.164 C 197.356,86.406 197.245,86.613 198.883,86.400" stroke-width="2.862" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 198.883,86.400 C 200.791,86.595 200.702,86.392 202.522,86.136" stroke-width="2.803" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 202.522,86.136 C 204.074,85.365 204.166,85.699 205.633,84.609" stroke-width="2.803" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 205.633,84.609 C 206.872,84.030 206.864,84.012 208.102,83.431" stroke-width="2.891" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 208.102,83.431 C 209.101,82.931 209.106,82.942 210.100,82.432" stroke-width="2.955" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 210.100,82.432 C 210.783,81.688 210.571,82.196 211.042,81.961" stroke-width="3.100" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 211.042,81.961 C 211.553,83.045 211.622,82.569 211.778,84.194" stroke-width="3.135" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 211.778,84.194 C 212.153,86.299 212.184,86.274 212.306,88.418" stroke-width="2.817" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 212.306,88.418 C 212.360,89.975 212.417,89.966 212.306,91.528" stroke-width="2.842" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 212.306,91.528 C 212.538,94.239 212.214,94.165 212.013,96.799" stroke-width="2.591" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 212.013,96.799 C 211.324,99.652 211.439,99.599 210.109,102.249" stroke-width="2.566" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 210.109,102.249 C 209.203,104.351 209.184,104.225 207.733,105.944" stroke-width="2.623" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 207.733,105.944 C 206.002,108.007 206.036,107.783 203.774,109.112" stroke-width="2.607" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 203.774,109.112 C 200.890,110.007 201.123,110.426 197.975,110.780" stroke-width="2.524" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 197.975,110.780 C 195.703,111.396 195.705,111.383 193.403,111.865" stroke-width="2.607" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 193.403,111.865 C 191.718,112.071 191.744,112.202 190.056,112.393" stroke-width="2.782" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 188.994,166.615 C 189.202,167.936 188.994,167.907 188.994,169.198" stroke-width="2.933" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 188.994,169.198 C 188.462,171.013 188.688,171.047 187.966,172.837" stroke-width="2.788" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 187.966,172.837 C 187.289,175.386 187.274,175.382 186.618,177.937" stroke-width="2.636" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 186.618,177.937 C 186.115,179.906 186.101,179.902 185.590,181.868" stroke-width="2.675" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 185.590,181.868 C 185.198,183.307 185.205,183.309 184.799,184.743" stroke-width="2.825" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 184.799,184.743 C 184.454,186.169 184.406,186.154 184.007,187.562" stroke-width="2.845" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 184.007,187.562 C 183.627,188.528 183.690,188.549 183.272,189.503" stroke-width="2.957" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 183.272,189.503 C 182.847,190.240 182.995,190.262 182.744,191.030" stroke-width="3.032" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 182.744,191.030 C 182.872,192.308 182.583,192.266 182.744,193.556" stroke-width="2.981" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 182.744,193.556 C 182.582,194.609 182.637,194.598 182.273,195.611" stroke-width="2.996" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 181.952,177.920 C 183.807,177.693 183.804,177.670 185.656,177.421" stroke-width="3.244" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 185.656,177.421 C 187.377,177.075 187.389,177.165 189.116,176.864" stroke-width="2.896" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 189.116,176.864 C 192.103,176.594 192.092,176.504 195.085,176.280" stroke-width="2.572" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 195.085,176.280 C 197.389,176.113 197.374,176.038 199.657,175.752" stroke-width="2.652" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 199.657,175.752 C 200.674,175.400 200.703,175.585 201.712,175.224" stroke-width="2.873" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 201.712,175.224 C 202.308,175.418 202.229,175.136 202.768,175.224" stroke-width="3.178" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 202.768,175.224 C 203.539,174.878 203.425,174.947 203.946,174.281" stroke-width="3.221" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 205.944,162.999 C 205.624,163.594 205.709,163.617 205.473,164.234" stroke-width="3.250" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 205.473,164.234 C 205.200,165.609 205.153,165.592 205.002,166.996" stroke-width="2.995" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 205.002,166.996 C 204.696,169.103 204.701,169.102 204.474,171.219" stroke-width="2.782" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 204.474,171.219 C 204.352,174.168 204.168,174.142 203.946,177.074" stroke-width="2.554" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 203.946,177.074 C 203.434,179.169 203.649,179.203 203.069,181.289" stroke-width="2.627" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 203.069,181.289 C 202.790,184.220 202.571,184.176 202.220,187.088" stroke-width="2.544" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 202.220,187.088 C 201.702,188.906 201.852,188.939 201.193,190.727" stroke-width="2.671" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 201.193,190.727 C 200.577,192.439 200.939,191.635 200.693,192.546" stroke-width="2.929" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 214.124,176.175 C 214.124,176.764 214.124,176.764 214.124,177.353" stroke-width="3.253" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 214.124,177.353 C 214.198,179.293 214.124,179.290 214.124,181.227" stroke-width="2.858" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 214.124,181.227 C 214.118,182.775 214.066,182.757 213.860,184.281" stroke-width="2.859" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 213.860,184.281 C 213.086,186.947 213.590,185.858 213.068,187.392" stroke-width="2.825" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 171.243,313.983 C 171.014,315.102 171.007,315.100 170.772,316.217" stroke-width="3.180" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 170.772,316.217 C 170.613,317.362 170.529,317.335 170.272,318.451" stroke-width="3.017" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 170.272,318.451 C 169.882,319.732 169.878,319.713 169.302,320.920" stroke-width="2.991" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 169.302,320.920 C 168.485,322.142 168.662,322.229 167.831,323.446" stroke-width="2.912" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 167.831,323.446 C 167.212,324.815 167.160,324.786 166.653,326.208" stroke-width="2.863" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 166.653,326.208 C 166.291,327.175 166.269,327.166 165.947,328.149" stroke-width="2.950" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 165.947,328.149 C 165.679,328.879 165.688,328.881 165.447,329.619" stroke-width="3.037" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 170.272,313.172 C 170.045,314.448 170.272,314.406 170.272,315.641" stroke-width="3.202" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 170.272,315.641 C 170.632,316.931 170.516,316.918 171.215,318.110" stroke-width="3.000" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 171.215,318.110 C 171.784,319.194 171.749,319.193 172.506,320.165" stroke-width="2.951" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 172.506,320.165 C 173.371,321.207 173.311,321.249 174.269,322.220" stroke-width="2.939" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 174.269,322.220 C 174.674,323.168 174.620,322.617 175.004,322.984" stroke-width="3.173" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 175.004,322.984 C 175.828,322.040 175.776,322.551 176.474,320.985" stroke-width="3.149" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 176.474,320.985 C 177.280,319.644 177.284,319.661 177.916,318.224" stroke-width="2.915" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 177.916,318.224 C 178.558,316.229 178.765,316.326 179.443,314.350" stroke-width="2.769" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 179.443,314.350 C 180.162,312.716 180.189,312.765 181.177,311.296" stroke-width="2.768" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 181.177,311.296 C 182.323,310.071 182.146,309.940 183.411,308.798" stroke-width="2.804" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 183.411,308.798 C 183.962,307.497 183.793,308.351 184.117,307.856" stroke-width="3.033" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 184.117,307.856 C 184.385,310.054 184.698,309.199 184.881,312.201" stroke-width="3.061" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 184.881,312.201 C 185.581,314.658 185.455,314.688 186.257,317.123" stroke-width="2.719" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 186.257,317.123 C 186.891,319.126 186.811,319.142 187.342,321.167" stroke-width="2.711" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 187.342,321.167 C 187.524,322.677 187.668,322.646 187.813,324.164" stroke-width="2.816" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 187.813,324.164 C 188.156,325.152 188.009,325.174 188.312,326.163" stroke-width="2.936" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 188.312,326.163 C 187.976,327.290 188.406,326.768 188.312,327.397" stroke-width="3.155" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 198.848,321.272 C 199.434,320.848 199.465,320.919 200.083,320.565" stroke-width="3.039" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 200.083,320.565 C 200.943,320.536 200.787,320.259 201.553,320.094" stroke-width="3.066" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 201.553,320.094 C 202.781,319.056 202.809,319.184 203.815,317.860" stroke-width="2.907" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 203.815,317.860 C 204.306,317.137 204.383,317.204 204.757,316.390" stroke-width="3.001" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 204.757,316.390 C 205.794,315.453 205.248,315.578 205.700,314.741" stroke-width="3.135" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 205.700,314.741 C 205.130,314.021 205.619,314.129 204.408,313.742" stroke-width="3.191" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 204.408,313.742 C 203.763,313.742 203.838,313.521 203.117,313.742" stroke-width="3.153" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 203.117,313.742 C 202.446,313.601 202.471,313.742 201.826,313.742" stroke-width="3.132" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 201.826,313.742 C 200.788,313.992 200.829,313.969 199.884,314.477" stroke-width="3.170" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 199.884,314.477 C 199.034,314.802 199.200,314.845 198.650,315.448" stroke-width="3.102" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 198.650,315.448 C 198.186,316.570 198.063,316.433 197.943,317.738" stroke-width="2.983" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 197.943,317.738 C 197.938,318.879 197.715,318.833 197.707,319.972" stroke-width="2.967" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 197.707,319.972 C 197.457,321.134 197.467,321.113 197.000,322.206" stroke-width="2.966" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 197.000,322.206 C 196.488,323.044 196.618,323.104 196.030,323.912" stroke-width="3.008" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 196.030,323.912 C 195.051,324.778 195.649,324.632 195.323,325.382" stroke-width="3.046" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 195.323,325.382 C 196.272,326.652 195.814,326.470 197.557,327.295" stroke-width="3.088" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 197.557,327.295 C 199.432,327.663 199.208,328.122 201.195,328.322" stroke-width="2.852" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 201.195,328.322 C 202.469,329.123 202.572,328.837 203.835,329.642" stroke-width="2.850" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 203.835,329.642 C 204.635,329.664 204.552,329.915 205.362,329.906" stroke-width="3.016" stroke="black" fill="none" stroke-linecap="round"></path><path d="M 205.362,329.906 C 206.166,330.178 206.133,330.163 206.832,330.641" stroke-width="3.059" stroke="black" fill="none" stroke-linecap="round"></path></svg>'

                ticket = Ticket(
                    recipient=recipient,
                    item_type=ticket_code.item_type,
                    is_handwritten=is_handwritten,
                    template=1,
                    code=ticket_code
                )

                # If special serenade, randomly set a period for it
                if ticket.item_type == "Special Serenade":
                    ticket.ss_period = random.choice([1, 2, 3, 4])

                ticket.save()

                # create the ticket file
                with open(f'{DirectoryLocations.REDEEMED_TICKETS}/{ticket.pk}.svg', 'wb') as file:
                    file.write(bytes(message, 'utf-8'))

                # mark the ticket code as consumed
                ticket_code.is_unconsumed = False
                ticket_code.save()


@admin.register(SortedTicket)
class SortedTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'delivery_group', 'period', 'classroom', 'sort_request')

    @admin.display(description="Chosen Classroom")
    def classroom(self, obj):
        if obj.period is not None:
            return getattr(obj, f'p{obj.period}')
        else:
            return None


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'item_type', 'is_handwritten', 'template')
    actions = ('delete_tickets_and_ticket_codes',)
    date_hierarchy = "date"

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


@admin.register(SortTicketsRequest)
class SortTicketAdmin(admin.ModelAdmin):
    list_display = ('pk', 'num_serenaders', 'num_non_serenaders', 'url', 'date')
    actions = ('delete_queryset_and_children',)
    date_hierarchy = "date"

    @admin.display(description='URL')
    def url(self, obj):
        url = reverse("ticketing:tickets", args=[obj.pk])
        return format_html("<a href='{url}'>{url}</a>", url=url)

    def save_model(self, request, obj: SortTicketsRequest, form, change):
        super().save_model(request=request, obj=obj, form=form, change=change)

        # Sort tickets
        TicketSorter(Ticket.objects.all(), obj, obj.num_serenaders, obj.num_non_serenaders)

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


@admin.register(DeliveryGroup)
class DeliveryGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'percentage_printed', 'num_serenades', 'num_non_serenades',
                    'num_tickets', 'sort_request',)
    readonly_fields = ('parts_printed',)
    actions = ('unprint',)
    date_hierarchy = "date"

    @admin.display(description='Number of Serenade Tickets')
    def num_serenades(self, obj):
        return obj.tickets.filter(Q(item_type="Serenade") | Q(item_type="Special Serenade")).count()

    @admin.display(description='Number of Non-serenade Tickets')
    def num_non_serenades(self, obj):
        return obj.tickets.filter(Q(item_type="Chocolate") | Q(item_type="Rose")).count()

    @admin.display(description='Total Number of Tickets')
    def num_tickets(self, obj):
        return obj.tickets.count()

    @admin.display(description='Percentage of Tickets Printed')
    def percentage_printed(self, obj: DeliveryGroup):
        num_tickets = obj.sortedticket_set.count()

        if num_tickets > 0:
            num_printed_tickets = 0
            for part in obj.parts_printed:

                if part == num_tickets // NUM_TICKETS_PER_PDF + 1:
                    # If the last part, might not be a multiple of NUM_TICKETS_PER_PDF
                    # so calculate remainder
                    num_printed_tickets += num_tickets - (part - 1) * NUM_TICKETS_PER_PDF
                else:
                    # If not the last part, it's just the NUM_TICKETS_PER_PDF
                    num_printed_tickets += NUM_TICKETS_PER_PDF
            return f"{min(100, round(num_printed_tickets / num_tickets * 100))}%"
        else:
            return "100%"

    @admin.action(description="Undo printing of delivery group tickets (delete its PDF).")
    def unprint(self, request, queryset):
        for obj in queryset:
            sort_request = obj.sort_request
            for part in range(math.ceil(obj.tickets.count() / NUM_TICKETS_PER_PDF)):
                pdf_path = f"{DirectoryLocations().SORTED_TICKETS}/{sort_request.pk}/{obj.code}_{part + 1}.pdf"

                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

        queryset.update(parts_printed=[])

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


admin.site.site_header = f"{ORG_NAME} Valentine's Day Ticketing System"
admin.site.site_title = ORG_NAME
