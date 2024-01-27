from __future__ import annotations
from typing import Literal
from django.db.models import QuerySet
from .models import Ticket, Classroom, SortedTicket

# Tells the algorithm what order the classrooms are physically located in
# (only linear unfortunately)
CLASSROOM_GEOGRAPHIC_ORDER = "LBCDAEFGOPTJHIRX" # noqa


ItemType = Literal["Special Serenade", "Serenade", "Rose", "Chocolate"]
PeriodType = Literal[1, 2, 3, 4]


# noinspection DuplicatedCode
class TicketSorter:
    def __init__(self, tickets: QuerySet[Ticket], num_serenading_groups: int,
                 num_non_serenading_groups: int) -> None:
        self.num_serenading_groups = num_serenading_groups
        self.num_non_serenading_groups = num_non_serenading_groups

        # Actually a list of SortedTickets (not Tickets)
        self.tickets: list[SortedTicket] = SortedTicket.objects.bulk_create(
            SortedTicket(
                ticket=ticket,
                p1=ticket.recipient.p1,
                p2=ticket.recipient.p2,
                p3=ticket.recipient.p3,
                p4=ticket.recipient.p4
            )
            for ticket in tickets.prefetch_related("recipient")
        )

        self.separate_special_serenades()
        self.distribute_tickets()

    def separate_special_serenades(self) -> None:
        """
        For each special serenade, removes regular serenades from the classroom, so the person
        receiving the special serenade is the only one.

        This is not enforced in any of these conditions:
        - There are multiple special serenades for the same class in the same period.
        - There is a regular serenade where all of its classes contain a special serenade, so it
            must be shared with at least one of them.

        It is possible to do a separate visit for each special serenade, so this is always
        guaranteed. However, this is too inefficient and multiple visits per class would be too
        disruptive.
        """
        for ticket in self.tickets:
            if ticket.ticket.item_type != "Special Serenade":
                continue

            period = ticket.ticket.ss_period
            classroom: Classroom = getattr(ticket, f"p{period}")

            # Choose the period of the special serenade
            ticket.choose_period(period)

            # Remove any serenades in the same class
            for other_ticket in classroom.tickets:
                if other_ticket.ticket.item_type != "Serenade":
                    continue

                # If possible, remove the serenade
                if not other_ticket.has_no_choice:
                    setattr(other_ticket, f"p{period}", None)

    def distribute_tickets(self) -> None:
        # Group tickets based on the recipient
        tickets_by_recipient = {}
        for ticket in self.tickets:
            recipient_id = ticket.ticket.recipient.recipient_id
            if recipient_id in tickets_by_recipient:
                tickets_by_recipient[recipient_id].append(ticket)
            else:
                tickets_by_recipient[recipient_id] = [ticket]

        period_distribution = self.PeriodDistribution(self.tickets)

        # For each person, go through their tickets (favouring ones with no choice first),
        # and choose their tickets so that the periods with the least tickets are chosen first.
        for recipient_id, tickets in tickets_by_recipient.items():
            # Cache the periods and remove from the cache so that a person will not end up getting
            # multiple items in the same period (unless unavoidable).
            periods_available = period_distribution.by_num_tickets

            # Go through each ticket (favouring ones with little choice first)
            for ticket in sorted(
                    filter(lambda t: t.num_periods_available > 1, tickets),
                    key=lambda t: t.num_periods_available):

                for period in periods_available:
                    if hasattr(ticket, f"p{period}"):
                        ticket.choose_period(period)
                        period_distribution[period] += 1
                        periods_available.remove(period)

                        # If person had more than 4 tickets and exhausted all of them,
                        # reset and do an additional pass
                        if len(periods_available) == 0:
                            periods_available = period_distribution.by_num_tickets

                        break

    class PeriodDistribution(dict):
        """
        A dict where each key is a period, and the value is the number of tickets in that period.

        If you construct it using a list of tickets, it computes the period distribution of those
        tickets on instantiation.
        """
        def __init__(self, tickets: list[SortedTicket]):
            period_distribution: dict[PeriodType, int] = {1: 0, 2: 0, 3: 0, 4: 0}

            for ticket in tickets:
                if ticket.has_no_choice:
                    period_distribution[ticket.chosen_period] += 1

            super().__init__(period_distribution)

        @property
        def by_num_tickets(self):
            """
            :return: A list of periods in order of how many tickets are within that period
            (emptiest first). If a tie, get the period with the lowest number
            (i.e., period 1 first, period 4 last).
            """
            return sorted(self.keys(), key=lambda k: (self[k], k))

        def __repr__(self):
            return super().__repr__()
