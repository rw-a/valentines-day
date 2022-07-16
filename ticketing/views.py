from django.http import HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from .models import Ticket, TicketCode
from .forms import TicketForm, GeneratorForm
from .input_validation import is_code_exists, is_code_unconsumed, is_recipient_exists
from .constants import DirectoryLocations
from .code_generator import generate_codes
from .ticket_sorter import sort_tickets


def index(request):
    return HttpResponseRedirect(reverse('ticketing:purchase'))


@staff_member_required
def stats(request):
    if "count" in request.GET:
        # if refreshing the item count
        data = {}
        for choice in Ticket.item_type.field.students:
            item_type = choice[0]
            item_type_name = item_type.lower().replace(' ', '_')
            # get total ticket codes created
            created = TicketCode.objects.filter_by_item_type(item_type=item_type).count()
            data[f'{item_type_name}s_created'] = created
            # gets total redeemed ticket codes (actually the number of tickets, in case some were manually added)
            redeemed = Ticket.objects.filter_by_item_type(item_type=item_type).count()
            data[f'{item_type_name}s_redeemed'] = redeemed
        return JsonResponse(data)
    else:
        return render(request, 'ticketing/stats.html')


@staff_member_required
def sorted_tickets(request):
    return FileResponse(open(f'sorted_tickets.pdf', 'rb'))


@staff_member_required
def codepdf(request, pk):
    return FileResponse(open(f'{DirectoryLocations.GENERATED_TICKET_CODES}/{pk}.pdf', 'rb'))


@staff_member_required
def generator(request, code: str = ""):
    if request.method == 'POST':
        form = GeneratorForm(request.POST)
        if form.is_valid():
            code = generate_codes(1)[0]
            ticket_code = TicketCode(code=code, item_type=form.cleaned_data['item_type'])
            ticket_code.save()
            return HttpResponseRedirect(f"{reverse('ticketing:generator')}{code}/")
    else:
        form = GeneratorForm()

    return render(request, 'ticketing/generator.html', {'form': form, 'code': code})


def purchased(request):
    return render(request, 'ticketing/purchased.html')


def purchase(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = TicketForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            ticket_code = TicketCode.objects.filter(code=form.cleaned_data['code'])[0]
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
                code=ticket_code
                )
            if ticket.item_type == "Special Serenade":
                ticket.period = form.cleaned_data['period']
            if is_handwritten:
                ticket.handwritten_message = form.cleaned_data['handwritten_message']
            else:
                ticket.recipient_nickname = form.cleaned_data['recipient_nickname']
                ticket.message = form.cleaned_data['message']
                ticket.sender = form.cleaned_data['sender']
            ticket.save()

            if is_handwritten:
                with open(f'{DirectoryLocations.REDEEMED_TICKETS}/{ticket.pk}.svg', 'wb') as file:
                    file.write(bytes(form.cleaned_data['handwritten_message'], 'utf-8'))
            else:
                pass

            # mark the ticket code as consumed
            ticket_code.is_unconsumed = False
            ticket_code.save()

            # redirect to the purchased screen
            return HttpResponseRedirect(reverse('ticketing:purchased'))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = TicketForm()

    return render(request, 'ticketing/purchase.html', {'form': form})


def validate_code(request):
    code = request.GET['inputted_code'].upper()

    data = {
        'is_exists': is_code_exists(code),
        'is_unconsumed': is_code_unconsumed(code),
        'item_type': TicketCode.objects.filter(code=code)[0].item_type if is_code_exists(code) else ""
        # if the code exists, get what item it is. if it doesn't leave it blank
    }

    return JsonResponse(data)


def validate_recipient(request):
    recipient = request.GET['recipient']
    data = {'is_exists': is_recipient_exists(recipient)}
    return JsonResponse(data)
