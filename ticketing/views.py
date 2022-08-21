from django.http import HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from .models import Ticket, TicketCode, SortTicketsRequest
from .forms import TicketForm, CSVFileForm
from .input_validation import is_code_exists, is_code_unconsumed, is_recipient_exists
from .constants import DirectoryLocations, FileNames
from .class_lookup import STUDENTS
from .ticket_printer import TicketsToPDF
from .timetable_parser import get_student_classes
import os
import re
import csv
import json
from io import StringIO


def index(request):
    return HttpResponseRedirect(reverse('ticketing:redeem'))


@staff_member_required
def load_timetables(request):
    if request.method == 'POST':
        form = CSVFileForm(request.POST, request.FILES)
        if form.is_valid():
            files = [csv.reader(StringIO(file.read().decode())) for file in request.FILES.getlist('files')]
            with open(FileNames.PEOPLE, 'w') as file:
                students = get_student_classes(files)
                writer = csv.DictWriter(file, fieldnames=['ID', 'Name', 'First Name', 'Last Name', 'ARC',
                                                          'P1', 'P2', 'P3', 'P4'])
                writer.writeheader()
                writer.writerows(students)

            for file in request.FILES.getlist('files'):
                print(file)
                with open(f"{DirectoryLocations.INPUT_TIMETABLES}/{file}", 'wb') as csv_file:
                    for chunk in file.chunks():
                        csv_file.write(chunk)
            return HttpResponseRedirect(reverse("ticketing:timetables_done"))
    else:
        form = CSVFileForm()
    return render(request, 'ticketing/timetables.html', {'form': form})


@staff_member_required
def timetables_loaded(request):
    return render(request, 'ticketing/timetables_done.html')


@staff_member_required
def stats(request):
    if "count" in request.GET:
        # if refreshing the item count
        data = {}

        # get number of tickets per item type
        for choice in Ticket.item_type.field.choices:
            item_type = choice[0]
            item_type_name = item_type.lower().replace(' ', '_')
            # get total ticket codes created
            created = TicketCode.objects.filter(item_type=item_type).count()
            data[f'{item_type_name}s_created'] = created
            # gets total redeemed ticket codes (actually the number of tickets, in case some were manually added)
            redeemed = Ticket.objects.filter(item_type=item_type).count()
            data[f'{item_type_name}s_redeemed'] = redeemed

        # get number of tickers per grade
        for grade in range(7, 13):
            data[f"grade_{grade}"] = 0
        for ticket in Ticket.objects.all():
            recipient_arc = STUDENTS[ticket.recipient_id]['ARC']
            recipient_grade = re.match(r"\d+", recipient_arc)
            if recipient_grade is not None and f"grade_{recipient_grade[0]}" in data:
                data[f"grade_{recipient_grade[0]}"] += 1
            else:
                print(f"Stats: Error getting grade of {STUDENTS[ticket.recipient_id]}")
        return JsonResponse(data)
    else:
        return render(request, 'ticketing/stats.html')


@staff_member_required
def codepdf(request, pk):
    return FileResponse(open(f'{DirectoryLocations.GENERATED_TICKET_CODES}/{pk}.pdf', 'rb'))


@staff_member_required
def tickets(request, pk):
    sort_tickets_request = SortTicketsRequest.objects.get(pk=pk)
    group_data = {}
    for group in sort_tickets_request.deliverygroup_set.all():
        group_data[group.code] = {}
        group_data[group.code]["num_tickets"] = group.tickets.count()
        group_data[group.code]["is_printed"] = group.is_printed

    return render(request, 'ticketing/tickets.html', {
        'pk': pk, 'date': sort_tickets_request.date, 'group_data': json.dumps(group_data)})


@staff_member_required
def delivery_group(request, pk, group_id):
    return FileResponse(open(f'{DirectoryLocations.SORTED_TICKETS}/{pk}/{group_id}.pdf', 'rb'))


@staff_member_required
def print_tickets(request):
    pk = request.GET['pk']
    group_code = request.GET['group']
    group = SortTicketsRequest.objects.get(pk=pk).deliverygroup_set.get(code=group_code)
    if not os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{pk}"):
        os.mkdir(f"{DirectoryLocations().SORTED_TICKETS}/{pk}")
    TicketsToPDF(group.tickets.all(), f"{DirectoryLocations().SORTED_TICKETS}/{pk}/{group_code}.pdf", group_code)
    group.is_printed = True
    group.save()
    return JsonResponse({"success": "true"})


def redeemed(request):
    return render(request, 'ticketing/redeemed.html')


def redeem(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = TicketForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            ticket_code = TicketCode.objects.get(code=form.cleaned_data['code'])
            is_handwritten = form.cleaned_data['is_handwritten']
            if is_handwritten:
                template = form.cleaned_data['handwriting_template']
            else:
                template = form.cleaned_data['typed_template']

            # make the ticket
            ticket = Ticket(
                recipient_id=form.cleaned_data['recipient_id'],
                item_type=ticket_code.item_type,
                is_handwritten=is_handwritten,
                template=template,
                message=form.cleaned_data['message'],
                code=ticket_code
                )
            if ticket.item_type == "Special Serenade":
                ticket.ss_period = form.cleaned_data['period']
            ticket.save()

            # create the ticket file
            with open(f'{DirectoryLocations.REDEEMED_TICKETS}/{ticket.pk}.svg', 'wb') as file:
                file.write(bytes(form.cleaned_data['message'], 'utf-8'))

            # mark the ticket code as consumed
            ticket_code.is_unconsumed = False
            ticket_code.save()

            # redirect to the purchased screen
            return HttpResponseRedirect(reverse('ticketing:redeemed'))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = TicketForm()

    return render(request, 'ticketing/redeem.html', {'form': form})


def validate_code(request):
    code = request.GET['inputted_code'].upper()

    data = {
        'is_exists': is_code_exists(code),
        'is_unconsumed': is_code_unconsumed(code),
        'item_type': TicketCode.objects.get(code=code).item_type if is_code_exists(code) else ""
        # if the code exists, get what item it is. if it doesn't leave it blank
    }

    return JsonResponse(data)


def validate_recipient(request):
    recipient = request.GET['recipient']
    data = {'is_exists': is_recipient_exists(recipient)}
    return JsonResponse(data)
