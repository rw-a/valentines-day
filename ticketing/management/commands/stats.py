from django.core.management.base import BaseCommand
from ticketing.models import Ticket


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('top', nargs='?', type=int, default=5)

    def handle(self, *args, **options):
        people = {}
        for ticket in Ticket.objects.all():
            if ticket.recipient_id in people:
                people[ticket.recipient_id].append(str(ticket.pk))
            else:
                people[ticket.recipient_id] = [str(ticket.pk)]
        people_sorted = sorted(people.keys(), key=lambda person: len(people[person]), reverse=True)

        output_string = "Recipients by Frequency:\n"
        for index, person in enumerate(people_sorted):
            output_string += f"{person}: {', '.join(people[person])}\n"
            if index > options['top']:
                break

        histogram = {}
        print(histogram)
        output_string += "\nStatistics:\n"
        for tickets in people.values():
            num_tickets = len(tickets)
            if num_tickets in histogram:
                histogram[num_tickets] += 1
            else:
                histogram[num_tickets] = 1
        for num_tickets in sorted(histogram):
            output_string += f"{num_tickets}: {histogram[num_tickets]}\n"

        self.stdout.write(self.style.SUCCESS(output_string))
