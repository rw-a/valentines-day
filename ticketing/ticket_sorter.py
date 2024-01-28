from __future__ import annotations
from typing import Literal
from datetime import datetime
from django.db.models import QuerySet
from .models import Ticket, Classroom, SortedTicket, SortTicketsRequest

# Tells the algorithm what order the classrooms are physically located in
# (only linear unfortunately)
CLASSROOM_GEOGRAPHIC_ORDER = "LBCDAEFGOPTJHIRX" # noqa

NON_SERENADES = ('Rose', 'Chocolate')


ItemType = Literal["Special Serenade", "Serenade", "Rose", "Chocolate"]
PeriodType = Literal[1, 2, 3, 4]


# noinspection DuplicatedCode
class PeriodGroup:
    """A DeliveryGroup but for a specific period. Each DeliveryGroup is made of 4 period groups.
    Mostly a virtual object for intermediate use only"""
    def __init__(self, classrooms: list[Classroom], sort_request: SortTicketsRequest):
        self.classrooms = classrooms
        self.request = sort_request

        self.num_tickets = self.count_num_tickets()

    def __repr__(self):
        return f"<PeriodGroup {self.classrooms} N={self.num_tickets}>"

    def count_num_tickets(self) -> int:
        num_tickets = 0
        for classroom in self.classrooms:
            num_tickets += classroom.tickets(self.request).count()
        return num_tickets


# noinspection DuplicatedCode
class PeriodGroupList(list):
    def __init__(self, classrooms: list[Classroom], sort_request: SortTicketsRequest,
                 num_groups: int):
        super().__init__(self)

        self.request = sort_request

        # Create a list of period groups
        for period_group_classrooms in self.split(classrooms, num_groups):
            self.append(PeriodGroup(period_group_classrooms, sort_request))

        # If some groups will get more than 1 classroom each, try to ensure it's evenly distributed
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
            # Get the emptiest and fullest groups
            fullest_group = self.fullest_group
            emptiest_group = self.emptiest_group
            fullest_group_index = self.index(fullest_group)
            emptiest_group_index = self.index(emptiest_group)

            # Calculate the difference between the emptiest and fullest group
            if min_group_ticket_range == 0:
                min_group_ticket_range = fullest_group.num_tickets - emptiest_group.num_tickets

            # Shuffle a class down, from the fullest to the emptiest group
            if fullest_group_index < emptiest_group_index:
                for index in range(fullest_group_index, emptiest_group_index):
                    # Shuffle a class up
                    period_group: PeriodGroup = self[index]
                    last_classroom = period_group.classrooms.pop()
                    self[index + 1].classrooms.insert(0, last_classroom)

                    # Update the number of tickets
                    last_classroom_num_tickets = last_classroom.tickets(self.request).count()
                    period_group.num_tickets -= last_classroom_num_tickets
                    self[index + 1].num_tickets += last_classroom_num_tickets
            elif emptiest_group_index < fullest_group_index:
                for index in range(fullest_group_index, emptiest_group_index, -1):
                    # Shuffle a class down
                    period_group = self[index]
                    last_classroom = period_group.classrooms.pop(0)
                    self[index - 1].classrooms.append(last_classroom)

                    # Update the number of tickets
                    last_classroom_num_tickets = last_classroom.tickets(self.request).count()
                    period_group.num_tickets -= last_classroom_num_tickets
                    self[index - 1].num_tickets += last_classroom_num_tickets
            else:
                # If emptiest and fullest groups are equal (i.e. all groups are same sized)
                return

            fullest_group = self.fullest_group
            emptiest_group = self.emptiest_group

            # the difference in the number of tickets between the fullest and emptiest group
            new_group_ticket_range = fullest_group.num_tickets - emptiest_group.num_tickets

            if new_group_ticket_range < min_group_ticket_range:
                # If the reshuffle improved the evenness of the distribution

                # Update values and try again to improve evenness
                min_group_ticket_range = new_group_ticket_range
                search_depth = 0

                # Save state so that any further iterations don't mess it up
                state = [tuple(group.classrooms) for group in self]
            else:
                # If the reshuffle didn't help the evenness of the distribution

                # Algorithm will keep searching for 7 iterations after it has found a local min
                search_depth += 1
                if search_depth >= 7:
                    break

        # restore from state
        if len(state) > 0:
            for index, period_group in enumerate(self):
                period_group.classrooms = list(state[index])

    @property
    def fullest_group(self):
        return max(self, key=lambda period_group: period_group.num_tickets)

    @property
    def emptiest_group(self):
        return min(self, key=lambda period_group: period_group.num_tickets)


# noinspection DuplicatedCode
class DeliveryGroup:
    def __init__(self, number: int, is_serenading: bool, sort_request: SortTicketsRequest):
        self.is_serenading = is_serenading
        self.number = number
        self._request = sort_request

        self.p1 = []
        self.p2 = []
        self.p3 = []
        self.p4 = []

    def get_num_tickets_in_period(self, period: PeriodType) -> int:
        classrooms = getattr(self, f"p{period}")
        return sum(map(lambda classroom: classroom.tickets(self._request).count(), classrooms))

    def get_num_tickets(self) -> int:
        total = 0
        for period in (1, 2, 3, 4):
            period: PeriodType
            total += self.get_num_tickets_in_period(period)

        return total


# noinspection DuplicatedCode
class DeliveryGroupList(list):
    def update(self, period_groups: PeriodGroupList, period: int):
        if len(period_groups) > len(self):
            raise OverflowError(
                "Length of PeriodGroupList must not be more than length of DeliveryGroupList")

        unassigned_delivery_groups = self.filter_unassigned_delivery_groups(period)

        # Assign the delivery groups a period group
        for i in range(len(unassigned_delivery_groups)):
            # Assign the emptiest period group to the fullest delivery group for even distribution
            emptiest_period_group = period_groups.emptiest_group
            fullest_delivery_group = unassigned_delivery_groups.fullest_group

            setattr(fullest_delivery_group, f"p{period}", emptiest_period_group.classrooms)

            period_groups.remove(emptiest_period_group)
            unassigned_delivery_groups.remove(fullest_delivery_group)

    def filter_unassigned_delivery_groups(self, period: int):
        return DeliveryGroupList([delivery_group for delivery_group in self
                                  if len(getattr(delivery_group, f"p{period}")) == 0])

    @property
    def fullest_group(self) -> DeliveryGroup:
        if len(self) > 1:
            return max(self, key=lambda group: group.get_num_tickets())
        elif len(self) == 1:
            return self[0]
        else:
            raise KeyError("Cannot return max of blank.")

    @property
    def emptiest_group(self) -> DeliveryGroup:
        if len(self) > 1:
            return min(self, key=lambda group: group.get_num_tickets())
        elif len(self) == 1:
            return self[0]
        else:
            raise KeyError("Cannot return min of blank.")


# noinspection DuplicatedCode
class TicketSorter:
    def __init__(self, tickets: QuerySet[Ticket], sort_request: SortTicketsRequest,
                 num_serenading_groups: int, num_non_serenading_groups: int) -> None:
        self.serenading_groups = None
        self.non_serenading_groups = None

        self._request = sort_request
        self._num_serenading_groups = num_serenading_groups
        self._num_non_serenading_groups = num_non_serenading_groups

        start_time = datetime.now()

        self.classrooms = Classroom.objects.all()

        self._serenades: list[SortedTicket] = self._create_sorted_tickets(
            tickets.filter(item_type__in=["Serenade", "Special Serenade"]))
        self._non_serenades: list[SortedTicket] = self._create_sorted_tickets(
            tickets.filter(item_type__in=["Rose", "Chocolate"]))

        init_time = datetime.now()

        # Sort serenades
        self._separate_special_serenades()
        self._remove_bad_classrooms()
        self._distribute_serenades()

        # Sort non-serenades
        self._distribute_non_serenades()

        sort_time = datetime.now()

        # for ticket in self._serenades:
        #     if not ticket.has_no_choice:
        #         print(ticket)
        # for ticket in self._non_serenades:
        #     if not ticket.has_no_choice:
        #         print(ticket)

        # Distribute tickets into groups
        self._assign_tickets_to_groups()

        distribute_time = datetime.now()

        print(f"Create: {init_time - start_time} Sort: {sort_time - init_time} Distribute: {distribute_time - sort_time}")

    def _create_sorted_tickets(self, tickets: QuerySet[Ticket]) -> list[SortedTicket]:
        return SortedTicket.objects.bulk_create(
            SortedTicket(
                ticket=ticket,
                sort_request=self._request,
                p1=ticket.recipient.p1,
                p2=ticket.recipient.p2,
                p3=ticket.recipient.p3,
                p4=ticket.recipient.p4
            )
            for ticket in tickets.prefetch_related("recipient")
        )

    def _separate_special_serenades(self) -> None:
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
        for ticket in self._serenades:
            if ticket.ticket.item_type != "Special Serenade":
                continue

            period = ticket.ticket.ss_period
            classroom: Classroom = getattr(ticket, f"p{period}")

            # Choose the period of the special serenade
            ticket.choose_period(period)
            ticket.save()

            # Remove any serenades in the same class
            for other_ticket in classroom.tickets(self._request):
                if other_ticket.ticket.item_type != "Serenade":
                    continue

                # If possible, remove the serenade
                if not other_ticket.has_no_choice:
                    setattr(other_ticket, f"p{period}", None)
                    other_ticket.save()

    def _remove_bad_classrooms(self) -> None:
        """
        For all bad classrooms (in a bad position like the OVAL or POOL), remove all tickets in that
        classroom (except special serenades)
        """
        # For each bad classroom
        for classroom in self.classrooms:
            if not classroom.is_bad:
                continue

            period = classroom.period

            # For each ticket in the classroom (that has choice)
            for ticket in classroom.tickets(self._request):
                if ticket.has_no_choice:
                    continue

                # Remove the ticket from the bad classroom
                setattr(ticket, f"p{period}", None)
                ticket.save()

    def _distribute_serenades(self) -> None:
        """
        Distribute serenades as evenly as possible across periods. There are two reasons:
        1. So an individual receives serenades separately and don't miss out on a serenade.
        2. Distribute evenly across periods so delivery groups have an equal workload regardless of
            which period it is.

        The logic is as follows:
        1. For each recipient, get their tickets (those with the least number of choices first).
        2. For each ticket, pick the period with the least number of total tickets.
        3. However, once a period has been chosen, it cannot be chosen again (but if the recipient
            has 4 or more tickets, then the period options reset).
        """
        tickets_by_recipient = self._group_tickets_by_recipient(self._serenades)
        period_distribution = self.PeriodDistribution(self._serenades)

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
                        ticket.save()

                        period_distribution[period] += 1
                        periods_available.remove(period)

                        # If person had more than 4 tickets and exhausted all of them,
                        # reset and do an additional pass
                        if len(periods_available) == 0:
                            periods_available = period_distribution.by_num_tickets

                        break

    @staticmethod
    def _group_tickets_by_recipient(tickets: list[SortedTicket]) -> dict[str, list[SortedTicket]]:
        # Group serenades based on the recipient
        tickets_by_recipient = {}
        for ticket in tickets:
            recipient_id = ticket.ticket.recipient.recipient_id
            if recipient_id in tickets_by_recipient:
                tickets_by_recipient[recipient_id].append(ticket)
            else:
                tickets_by_recipient[recipient_id] = [ticket]

        return tickets_by_recipient

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

        @property
        def emptiest_period(self) -> PeriodType:
            """
            :return: The period with the least number of tickets in that period.
            If a tie, the period with the lowest number (i.e., period 1 first, period 4 last)
            is chosen.
            """
            return min(self.keys(), key=lambda k: (self[k], k))

        def __repr__(self):
            return super().__repr__()

    def _assign_tickets_to_groups(self):
        self._serenading_groups = DeliveryGroupList([
            DeliveryGroup(i + 1, True, self._request)
            for i in range(self._num_serenading_groups)
        ])
        self._non_serenading_groups = DeliveryGroupList([
            DeliveryGroup(i + 1, False, self._request)
            for i in range(self._num_non_serenading_groups)
        ])

        for period in (1, 2, 3, 4):
            classrooms_in_period = self.classrooms.filter(period=period)

            serenading_period_groups = PeriodGroupList(classrooms_in_period, self._request, self._num_serenading_groups)
            self._serenading_groups.update(serenading_period_groups, period)

    def _distribute_non_serenades(self):
        """
        Distribute the non-serenades into classes. Unlike for serenades, the goal in this step is
        to keep the non-serenades as tightly distributed as possible (as few classroom visits as
        possible).

        The process is as follows:
        1. Choose the period with the least number of tickets.
        2. Within the period, order the classrooms in order how many non-serenades are in them.
        3. Starting from the emptiest classroom, try to remove all non-serenades in that classroom.
        4. If it's not possible to eliminate the classroom (a ticket in there has no other choice),
            the classroom is locked-in and all other tickets in that classroom are moved to that
            classroom.
        5. Repeat by choosing the emptiest period and the emptiest classroom in that period again.
        """
        # Create an empty period distribution
        # (since non-serenades haven't been touched yet, so no need to compute it)
        period_distribution = self.PeriodDistribution([])

        classrooms_to_check = self.classrooms
        while classrooms_to_check:
            emptiest_period = period_distribution.emptiest_period
            classrooms_in_period = classrooms_to_check.filter(period=emptiest_period)

            # If no more classrooms in this period
            if not classrooms_in_period:
                del period_distribution[emptiest_period]
                continue

            # Get the emptiest classroom of the period
            emptiest_classroom: Classroom = min(
                classrooms_in_period,
                key=lambda c: c.num_tickets(self._request, ticket__item_type__in=NON_SERENADES)
            )

            # If classroom must be kept, make every other ticket stay in this class
            if emptiest_classroom.must_keep:
                for ticket in emptiest_classroom.tickets(self._request):
                    ticket.choose_period(emptiest_period)
                    ticket.save()

                    period_distribution[emptiest_period] += 1

            # If classroom can be eliminated, remove tickets associated with it
            else:
                for ticket in emptiest_classroom.tickets(self._request, ticket__item_type__in=NON_SERENADES):
                    setattr(ticket, f'p{emptiest_period}', None)
                    ticket.save()

                    # Update period distribution
                    if ticket.has_no_choice:
                        period_distribution[ticket.chosen_period] += 1

            # Remove the classroom from the list to check
            classrooms_to_check = classrooms_to_check.exclude(pk=emptiest_classroom.pk)
