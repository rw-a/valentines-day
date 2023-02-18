from django.http import HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from vdaywebsite.settings import CONTACT_EMAIL, NUM_TICKETS_PER_PDF
from .models import Ticket, TicketCode, SortTicketsRequest
from .forms import CSVFileForm
from .input_validation import is_code_exists, is_code_unconsumed, is_recipient_exists
from .constants import DirectoryLocations, FileNames, STUDENTS, TEMPLATES, STUDENTS_LIST, FONTS
from .ticket_printer import TicketsToPDF
from .timetable_parser import get_student_classes
import os
import re
import csv
import json
import datetime
from io import StringIO


def page_index(request):
    return HttpResponseRedirect(reverse('ticketing:redeem'))


@staff_member_required
def form_timetables(request):
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
                with open(f"{DirectoryLocations.TIMETABLES_INPUT}/{file}", 'wb') as csv_file:
                    for chunk in file.chunks():
                        csv_file.write(chunk)
            return HttpResponseRedirect(reverse("ticketing:timetables_done"))
    else:
        form = CSVFileForm()
    return render(request, 'ticketing/timetables.html', {'form': form})


@staff_member_required
def page_timetables_loaded(request):
    return render(request, 'ticketing/timetables_done.html')


@staff_member_required
def page_stats(request):
    return render(request, 'ticketing/stats.html')


@staff_member_required
def api_count(request):
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


@staff_member_required
def api_graph(request):
    """Returns a histogram with time in the x-axis (in hourly intervals) and number of tickets redeemed in y-axis"""
    # not enough tickets to make a useful graph
    if Ticket.objects.count() <= 2:
        return JsonResponse({"success": "false"})

    oldest_redeem = Ticket.objects.earliest('date').date + datetime.timedelta(hours=10)     # add 10 hours for timezone
    newest_redeem = Ticket.objects.latest('date').date + datetime.timedelta(hours=10)

    times = []  # x-axis
    num_tickets = []    # y-axis
    while oldest_redeem < newest_redeem:
        times.append(oldest_redeem.replace(microsecond=0, second=0, minute=0).strftime("%Y-%m-%d %H:%M:%S"))
        num_tickets.append(Ticket.objects.filter(date__date=oldest_redeem.date(), date__hour=oldest_redeem.hour).count())
        oldest_redeem += datetime.timedelta(hours=1)
    return JsonResponse({"success": "true", "xData": times, "yData": num_tickets})


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
        group_data[group.code]["num_tickets_printed"] = group.num_tickets_printed

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
    students = STUDENTS_LIST
    return render(request, 'ticketing/redeem.html', {'templates': templates, 'students': students,
                                                     'contact_email': CONTACT_EMAIL, 'fonts': FONTS})


@csrf_exempt
def api_redeem(request):
    if request.method == 'POST':
        data = json.loads(request.read())

        # validate code
        if is_code_exists(data['code']):
            ticket_code = TicketCode.objects.get(code=data['code'])
        else:
            return JsonResponse({"success": "false", "error": "This is not a valid code."})
        if not is_code_unconsumed(data['code']):
            return JsonResponse({"success": "false", "error": "This code has already been used."})

        # validate recipient
        if not is_recipient_exists(data['recipient_id']):
            return JsonResponse({"success": "false", "error": "This recipient does not exist."})

        # make the ticket
        ticket = Ticket(
            recipient_id=data['recipient_id'],
            item_type=ticket_code.item_type,
            is_handwritten=(data['is_handwritten'] == "True"),
            template=data['template'],
            code=ticket_code,
        )
        if ticket.item_type == "Special Serenade":
            ticket.ss_period = data['period']
        ticket.save()

        # create the ticket file
        with open(f'{DirectoryLocations.REDEEMED_TICKETS}/{ticket.pk}.svg', 'wb') as file:
            file.write(bytes(data['message'], 'utf-8'))

        # mark the ticket code as consumed
        ticket_code.is_unconsumed = False
        ticket_code.save()

        # redirect to the purchased screen
        return JsonResponse({"success": "true"})


def api_validate_code(request):
    code = request.GET['inputted_code'].upper()

    data = {
        'is_exists': is_code_exists(code),
        'is_unconsumed': is_code_unconsumed(code),
        'item_type': TicketCode.objects.get(code=code).item_type if is_code_exists(code) else ""
        # if the code exists, get what item it is. if it doesn't leave it blank
    }

    return JsonResponse(data)


@staff_member_required
def api_print_tickets(request):
    pk = request.GET['pk']
    group_code = request.GET['group']
    part = request.GET['part']

    group = SortTicketsRequest.objects.get(pk=pk).deliverygroup_set.get(code=group_code)

    if not os.path.exists(f"{DirectoryLocations().SORTED_TICKETS}/{pk}"):
        os.mkdir(f"{DirectoryLocations().SORTED_TICKETS}/{pk}")

    TicketsToPDF(group.tickets.all(), f"{DirectoryLocations().SORTED_TICKETS}/{pk}/{group_code}_{part}.pdf", group_code)

    group.num_tickets_printed += NUM_TICKETS_PER_PDF
    group.save()

    return JsonResponse({"success": "true"})
