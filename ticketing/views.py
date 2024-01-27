import os
import csv
import json
import datetime
from typing import Literal
from io import StringIO
from django.http import HttpResponseRedirect, FileResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from vdaywebsite.settings import CONTACT_EMAIL, NUM_TICKETS_PER_PDF
from .models import Recipient, SortTicketsRequest, Ticket, TicketCode, Classroom
from .forms import CSVFileForm
from .constants import DirectoryLocations, TEMPLATES, FONTS
from .ticket_printer import TicketsToPDF
from .ticket_sorter import get_parts
from .timetable_parser import get_recipient_classes


def page_index(request):
    return HttpResponseRedirect(reverse('ticketing:redeem'))


class FormTimetables(FormView):
    form_class = CSVFileForm
    template_name = "ticketing/timetables.html"
    success_url = reverse_lazy("ticketing:timetables_done")

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        files = form.cleaned_data["files"]

        # Load uploaded timetables to get recipients
        recipients_json = get_recipient_classes(
            [csv.reader(StringIO(file.read().decode())) for file in files])

        # Parse students and save them to the database
        # Create classrooms if required
        for recipient_json in recipients_json:
            recipient, created = Recipient.objects.get_or_create(
                recipient_id=recipient_json["recipient_id"],
                first_name=recipient_json["first_name"],
                last_name=recipient_json["last_name"],
                full_name=recipient_json["full_name"],
                arc=recipient_json["arc"],
                grade=recipient_json["grade"],
            )

            # If user already exists
            if not created:
                continue

            # Set classroom for recipient (create if required)
            for period in ("p1", "p2", "p3", "p4"):
                period: Literal["p1", "p2", "p3", "p4"]
                classroom_original_name = recipient_json[period]

                classroom, created = Classroom.objects.get_or_create(
                    period=period[1:],
                    original_name=classroom_original_name
                )

                setattr(recipient, period, classroom)

            recipient.save()

        # Write files to disk
        for file in files:
            with open(f"{DirectoryLocations.TIMETABLES_INPUT}/{file}", 'wb') as csv_file:
                for chunk in file.chunks():
                    csv_file.write(chunk)

        return super().form_valid(form)


@staff_member_required
def page_timetables_loaded(request):
    return render(request, 'ticketing/timetables_done.html')


@staff_member_required
def page_stats(request):
    return render(request, 'ticketing/stats.html')


class ApiCount(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    @staticmethod
    def get(request: Request):
        data = {}

        # For each item type in a ticket
        for choice in Ticket.item_type.field.choices:
            item_type = choice[0]
            item_type_name = item_type.lower().replace(' ', '_')

            # Get total ticket codes created
            created = TicketCode.objects.filter(item_type=item_type).count()
            data[f'{item_type_name}s_created'] = created

            # Gets total redeemed ticket codes
            # (actually the number of tickets, in case some were manually added)
            redeemed = Ticket.objects.filter(item_type=item_type).count()
            data[f'{item_type_name}s_redeemed'] = redeemed

        # Get number of tickers per grade
        for grade in Recipient.grade.field.choices:
            data[f"grade_{grade}"] = Ticket.objects.filter(recipient__grade=grade).count()

        return Response(data=data, status=status.HTTP_200_OK)


class ApiGraph(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    @staticmethod
    def get(request: Request, *args, **kwargs):
        """
        Returns a histogram with time in the x-axis (in hourly intervals)
        and number of tickets redeemed in y-axis
        """
        # Not enough tickets to make a useful graph
        if Ticket.objects.count() <= 2:
            return Response(data={"success": "false"}, status=status.HTTP_200_OK)

        oldest_redeem = Ticket.objects.earliest('date').date + datetime.timedelta(hours=10)     # add 10 hours for timezone
        newest_redeem = Ticket.objects.latest('date').date + datetime.timedelta(hours=10)

        times = []  # x-axis
        num_tickets = []    # y-axis
        while oldest_redeem < newest_redeem:
            times.append(oldest_redeem.replace(microsecond=0, second=0, minute=0).strftime("%Y-%m-%d %H:%M:%S"))
            num_tickets.append(Ticket.objects.filter(date__date=oldest_redeem.date(), date__hour=oldest_redeem.hour).count())
            oldest_redeem += datetime.timedelta(hours=1)

        return Response(
            data={"success": "true", "xData": times, "yData": num_tickets},
            status=status.HTTP_200_OK
        )


@staff_member_required
def file_codepdf(request, pk):
    return FileResponse(open(f'{DirectoryLocations.GENERATED_TICKET_CODES}/{pk}.pdf', 'rb'))


@staff_member_required
def page_tickets(request, pk):
    sort_tickets_request = SortTicketsRequest.objects.get(pk=pk)
    group_data = {}
    for group in sort_tickets_request.deliverygroup_set.all():
        group_data[group.code] = {}
        group_data[group.code]["num_tickets"] = group.tickets.count()
        group_data[group.code]["parts"] = get_parts(group)

    return render(request, 'ticketing/tickets.html', {
        'pk': pk,
        'num_tickets_per_pdf': NUM_TICKETS_PER_PDF,
        'date': sort_tickets_request.date,
        'group_data': json.dumps(group_data)
    })


@staff_member_required
def file_delivery_group(request, pk, group_id, part):
    return FileResponse(open(f'{DirectoryLocations.SORTED_TICKETS}/{pk}/{group_id}_{part}.pdf', 'rb'))


def page_redeem_done(request):
    return render(request, 'ticketing/redeemed.html')


def page_redeem(request):
    templates = TEMPLATES
    return render(
        request,
        'ticketing/redeem.html',
        {
            'templates': templates,
            'students': list(Recipient.objects.all().values_list('recipient_id', flat=True)),
            'contact_email': CONTACT_EMAIL,
            'fonts': FONTS
        }
    )


class ApiRedeem(APIView):
    @staticmethod
    def get(request: Request):
        """
        Endpoint for users to check if a code is valid
        """
        code = request.query_params.get('inputted_code').upper()

        # If the code exists, get what item it is. if it doesn't leave it blank
        exists = TicketCode.objects.filter(code=code).exists()
        unconsumed = exists and TicketCode.objects.get(code=code).is_unconsumed
        item_type = TicketCode.objects.get(code=code).item_type if exists else ""

        data = {
            'is_exists': exists,
            'is_unconsumed': unconsumed,
            'item_type': item_type
        }

        return Response(data=data, status=status.HTTP_200_OK)

    @staticmethod
    def post(request: Request):
        """
        Endpoint for users to redeem a ticket
        """
        data = request.data

        # Validate code
        try:
            ticket_code = TicketCode.objects.get(code=data['code'])
        except TicketCode.DoesNotExist:
            return Response(data={"success": "false", "error": "This is not a valid code."},
                            status=status.HTTP_200_OK)

        if not ticket_code.is_unconsumed:
            return Response(data={"success": "false", "error": "This code has already been used."},
                            status=status.HTTP_200_OK)

        # Validate recipient
        try:
            recipient = Recipient.objects.get(recipient_id=data['recipient_id'])
        except Recipient.DoesNotExist:
            return Response(data={"success": "false", "error": "This recipient does not exist."},
                            status=status.HTTP_200_OK)

        # Create the ticket
        ticket = Ticket(
            recipient=recipient,
            item_type=ticket_code.item_type,
            is_handwritten=(data['is_handwritten'] == "True"),
            template=data['template'],
            code=ticket_code,
        )
        if ticket.item_type == "Special Serenade":
            ticket.ss_period = data['period']
        ticket.save()

        # Create the ticket file
        with open(f'{DirectoryLocations.REDEEMED_TICKETS}/{ticket.pk}.svg', 'wb') as file:
            file.write(bytes(data['message'], 'utf-8'))

        # Mark the ticket code as consumed
        ticket_code.is_unconsumed = False
        ticket_code.save()

        # Redirect to the purchased screen
        return Response(data={"success": "true"}, status=status.HTTP_200_OK)


class ApiPrintTicket(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    @staticmethod
    def post(request: Request):
        pk = request.data['pk']
        group_code = request.data['group']
        part = int(request.data['part'])
        padding = int(request.data['padding'])
        enforce_boundaries = request.data['boundary'] == "true"

        group = SortTicketsRequest.objects.get(pk=pk).deliverygroup_set.get(code=group_code)

        if not os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{pk}"):
            os.mkdir(f"{DirectoryLocations().SORTED_TICKETS}/{pk}")

        TicketsToPDF(group.tickets.all()[(part - 1) * NUM_TICKETS_PER_PDF:
                                         min(part * NUM_TICKETS_PER_PDF, group.tickets.count())],
                     f"{DirectoryLocations().SORTED_TICKETS}/{pk}/{group_code}_{part}.pdf",
                     group_code,
                     starting_index=(part - 1) * NUM_TICKETS_PER_PDF,
                     padding=padding,
                     enforce_boundaries=enforce_boundaries)

        group.parts_printed += f",{part}"
        group.save()

        return Response(data={"success": "true"}, status=status.HTTP_200_OK)
