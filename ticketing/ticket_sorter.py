from __future__ import annotations
from typing import Literal
from datetime import datetime
from django.db.models import QuerySet
from .models import Ticket, Classroom, SortedTicket, SortTicketsRequest

# Tells the algorithm what order the classrooms are physically located in
# (only linear unfortunately)
CLASSROOM_GEOGRAPHIC_ORDER = "LBCDAEFGOPTJHIRX" # noqa


ItemType = Literal["Special Serenade", "Serenade", "Rose", "Chocolate"]
PeriodType = Literal[1, 2, 3, 4]


# noinspection DuplicatedCode
class PeriodGroup:
    """A DeliveryGroup but for a specific period. Each DeliveryGroup is made of 4 period groups.
    Mostly a virtual object for intermediate use only"""
    def __init__(self, classrooms: list[Classroom], sort_request: SortTicketsRequest):
        self.classrooms = classrooms
        self.request = sort_request

    def __repr__(self):
        return f"<PeriodGroup {self.classrooms} s={self.num_serenades} N={self.num_tickets}>"

    @property
    def num_tickets(self) -> int:
        num_tickets = 0
        for classroom in self.classrooms:
            num_tickets += classroom.tickets(self.request).count()
        return num_tickets

    @property
    def num_serenades(self) -> int:
        num_serenades = 0
        for classroom in self.classrooms:
            num_serenades += classroom.tickets(self.request).filter(ticket__item_type_in=["Serenade", "Special Serenade"]).count()
        return num_serenades


# noinspection DuplicatedCode
class PeriodGroupList(list):
    def __init__(self, classrooms: list[Classroom], sort_request: SortTicketsRequest,
                 num_groups: int):
        super().__init__(self)
        # create a list of period groups
        for period_group_classrooms in self.split(classrooms, num_groups):
            self.append(PeriodGroup(period_group_classrooms, sort_request))

        # if some groups will get more than 1 classroom each, try to ensure it's evenly distributed
        if len(classrooms) > num_groups:
            self.distribute_classrooms()

        # self.sort_tickets_by_person()

    @staticmethod
    def split(a, n: int):
        k, m = divmod(len(a), n)
        return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))

    def distribute_classrooms(self):
        search_depth = 0
        min_group_ticket_range = 0
        state = []

        while True:
            fullest_group = self.fullest_group
            emptiest_group = self.emptiest_group

            fullest_group_index = self.index(fullest_group)
            emptiest_group_index = self.index(emptiest_group)

            if min_group_ticket_range == 0:
                min_group_ticket_range = fullest_group.num_tickets - emptiest_group.num_tickets

            if fullest_group_index < emptiest_group_index:
                for index in range(fullest_group_index, emptiest_group_index):
                    period_group = self[index]
                    last_classroom = period_group.classrooms.pop()
                    self[index + 1].classrooms.insert(0, last_classroom)
            elif emptiest_group_index < fullest_group_index:
                for index in range(fullest_group_index, emptiest_group_index, -1):
                    period_group = self[index]
                    last_classroom = period_group.classrooms.pop(0)
                    self[index - 1].classrooms.append(last_classroom)
            else:
                return

            fullest_group = self.fullest_group
            emptiest_group = self.emptiest_group

            # the difference in the number of tickets between the fullest and emptiest group
            new_group_ticket_range = fullest_group.num_tickets - emptiest_group.num_tickets

            if new_group_ticket_range < min_group_ticket_range:
                min_group_ticket_range = new_group_ticket_range
                search_depth = 0
                # save state so that any further iterations don't mess it up
                state = [tuple(group.classrooms) for group in self]
            else:
                # algorithm will keep searching 7 iterations after it has found a local min
                search_depth += 1
                if search_depth >= 7:
                    break

        # restore from state
        if len(state) > 0:
            for index, period_group in enumerate(self):
                period_group.classrooms = list(state[index])

    # def sort_tickets_by_person(self):
    #     for period_group in self:
    #         for classroom in period_group.classrooms:
    #             classroom.tickets.sort(key=lambda ticket: ticket.recipient_id)

    @property
    def as_classroom_sizes(self) -> list:
        """
        :return: Returns itself but all its PeriodGroups have been mapped into a list of their
            classroom lengths.
        """
        return [
            [len(classroom.tickets) for classroom in period_group.classrooms]
            for period_group in self
        ]

    @property
    def as_classroom_sizes_serenades(self) -> list:
        return [
            [classroom.tickets.num_serenades for classroom in period_group.classrooms]
            for period_group in self
        ]

    @property
    def fullest_group(self):
        return max(self, key=lambda period_group: period_group.num_tickets)

    @property
    def emptiest_group(self):
        return min(self, key=lambda period_group: period_group.num_tickets)


# noinspection DuplicatedCode
class TicketSorter:
    def __init__(self, tickets: QuerySet[Ticket], sort_request: SortTicketsRequest,
                 num_serenading_groups: int, num_non_serenading_groups: int) -> None:
        self.request = sort_request

        start_time = datetime.now()

        # Actually a list of SortedTickets (not Tickets)
        self.serenades: list[SortedTicket] = self.create_sorted_tickets(
            tickets.filter(item_type__in=["Serenade", "Special Serenade"]))
        self.non_serenades: list[SortedTicket] = self.create_sorted_tickets(
            tickets.filter(item_type__in=["Rose", "Chocolate"]))
        init_time = datetime.now()

        # Sort serenades
        self.separate_special_serenades()
        self.distribute_serenades()
        sort_time = datetime.now()

        # Sort non-serenades

        # Distribute tickets into groups
        self.serenading_groups = PeriodGroupList(Classroom.objects.all(), sort_request,
                                                 num_serenading_groups)
        distribute_time = datetime.now()

        print(f"Create: {init_time - start_time} Sort: {sort_time - init_time} Distribute: {distribute_time - sort_time}")

    def create_sorted_tickets(self, tickets: QuerySet[Ticket]) -> list[SortedTicket]:
        return SortedTicket.objects.bulk_create(
            SortedTicket(
                ticket=ticket,
                sort_request=self.request,
                p1=ticket.recipient.p1,
                p2=ticket.recipient.p2,
                p3=ticket.recipient.p3,
                p4=ticket.recipient.p4
            )
            for ticket in tickets.prefetch_related("recipient")
        )

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
        for ticket in self.serenades:
            if ticket.ticket.item_type != "Special Serenade":
                continue

            period = ticket.ticket.ss_period
            classroom: Classroom = getattr(ticket, f"p{period}")

            # Choose the period of the special serenade
            ticket.choose_period(period)

            # Remove any serenades in the same class
            for other_ticket in classroom.tickets(self.request):
                if other_ticket.ticket.item_type != "Serenade":
                    continue

                # If possible, remove the serenade
                if not other_ticket.has_no_choice:
                    setattr(other_ticket, f"p{period}", None)

    def distribute_serenades(self) -> None:
        """
        Distribute serenades as evenly as possible across periods. There are two reasons:
        1. So an individual receives serenades separately and don't miss out on a serenade.
        2. Distribute evenly across periods so delivery groups have an equal workload regardless of
            which period it is.
        """
        # Group serenades based on the recipient
        tickets_by_recipient = {}
        for ticket in self.serenades:
            recipient_id = ticket.ticket.recipient.recipient_id
            if recipient_id in tickets_by_recipient:
                tickets_by_recipient[recipient_id].append(ticket)
            else:
                tickets_by_recipient[recipient_id] = [ticket]

        period_distribution = self.PeriodDistribution(self.serenades)

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
