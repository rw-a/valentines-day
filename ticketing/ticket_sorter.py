from __future__ import annotations

import re
import csv
import json
import random
import math
from datetime import datetime
from typing import Literal, Any, Sequence, Generator

# Tells the algorithm what order the classrooms are physically located in
# (only linear unfortunately)
CLASSROOM_GEOGRAPHIC_ORDER = "LBCDAEFGOPTJHIRX"


ItemType = Literal["Special Serenade", "Serenade", "Rose", "Chocolate"]
PeriodType = Literal[1, 2, 3, 4]


if __name__ == "__main__":
    from constants import DirectoryLocations
    from timetable_parser import room_format, bad_room_format

    # Can't import so use a dummy class
    class Ticket:
        pass
    class DeliveryGroupModel:
        pass

    random.seed(56)
else:
    from .constants import STUDENTS
    from .timetable_parser import room_format, bad_room_format
    from .models import Ticket
    from .models import DeliveryGroup as DeliveryGroupModel


def sort_tickets(tickets: list[Ticket], num_serenading_groups: int, num_non_serenading_groups: int,
                 max_serenades_per_class: int, max_non_serenades_per_serenading_class: int,
                 extra_special_serenades: bool, enforce_distribution: bool) \
        -> dict[bool, DeliveryGroupList[Any]]:
    ticket_sorter = TicketSorter(
        TicketList.from_sql_ticket_list(tickets), num_serenading_groups, num_non_serenading_groups,
        max_serenades_per_class=max_serenades_per_class,
        max_non_serenades_per_serenading_class=max_non_serenades_per_serenading_class,
        extra_special_serenades=extra_special_serenades,
        enforce_distribution=enforce_distribution
    )

    groups = {
        True: ticket_sorter.output_serenading_groups,
        False: ticket_sorter.output_non_serenading_groups
    }
    return groups


def get_parts(group: DeliveryGroupModel) -> list:
    """Receives a DeliveryGroup obj and returns the parts that have already been printed"""
    return list(filter(lambda part: len(part) > 0, group.parts_printed.split(",")))


class TicketToSort:
    def __init__(self, pk: int, recipient_id: str, item_type: ItemType,
                 p1: str, p2: str, p3: str, p4: str, ss_period: PeriodType | None = None):
        # Ticket info
        self.pk = pk
        self.recipient_id = recipient_id
        self.item_type = item_type
        self.ss_period = ss_period  # the period chosen by the special serenade (if applicable)

        # Where the recipient's classes are for each period
        # Don't rename the variable or else getattr()/setattr() will break
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4

        # Whether the algorithm has chosen this period.
        # Don't rename or else getattr()/setattr() will break
        self.is_p1 = True
        self.is_p2 = True
        self.is_p3 = True
        self.is_p4 = True

        if item_type == "Special Serenade" and self.ss_period is None:
            raise AssertionError("SS_period must be specified for special serenades.")

    @classmethod
    def from_sql_ticket(cls, sql_ticket: Ticket):
        """
        Converts a Ticket (the object stored in the SQL database, i.e. the Django model Ticket)
        into a TicketToSort
        """
        recipient_id = sql_ticket.recipient_id

        p1 = STUDENTS[sql_ticket.recipient_id]["P1"]
        p2 = STUDENTS[sql_ticket.recipient_id]["P2"]
        p3 = STUDENTS[sql_ticket.recipient_id]["P3"]
        p4 = STUDENTS[sql_ticket.recipient_id]["P4"]

        if sql_ticket.item_type == "Special Serenade":
            ticket_to_sort = cls(
                sql_ticket.pk, recipient_id, sql_ticket.item_type,
                p1, p2, p3, p4, sql_ticket.ss_period)
        else:
            ticket_to_sort = cls(
                sql_ticket.pk, recipient_id, sql_ticket.item_type, p1, p2, p3, p4)

        return ticket_to_sort

    @property
    def chosen_period(self) -> int:
        # if a ticket only has 1 period it can go to, return what it is
        if self.has_no_choice:
            for period in range(1, 5):
                if getattr(self, f"is_p{period}"):
                    return period
        else:
            raise Exception(f"Tried to get only_period when there were multiple periods possible "
                            f"{str(self)}")

    @property
    def chosen_classroom(self) -> str:
        if self.has_no_choice:
            return getattr(self, f"p{self.chosen_period}")

    def choose_period(self, chosen_period: int):
        # remove this ticket from the non-chosen classrooms
        for period in range(1, 5):  # generates 1, 2, 3, 4 (corresponding to period numbers)
            if period is not chosen_period:
                setattr(self, f'is_p{period}', False)    # set every period to false except the chosen one
                classroom = getattr(self, f"p{period}")
                if self in classroom.tickets:
                    classroom.tickets.remove(self)
        # add this ticket to the chosen classroom (if not already)
        setattr(self, f'is_p{chosen_period}', True)  # sets chosen period as true
        chosen_classroom = getattr(self, f"p{chosen_period}")
        if self not in chosen_classroom.tickets:
            chosen_classroom.tickets.append(self)

    @property
    def num_periods_available(self) -> int:
        num_periods = 0
        for period in range(1, 5):
            if getattr(self, f"is_p{period}"):
                num_periods += 1
        return num_periods

    @property
    def has_no_choice(self) -> bool:
        return self.num_periods_available <= 1

    @property
    def available_classrooms(self) -> list[str]:
        return [getattr(self, f"p{period}") for period in range(1, 5) if getattr(self, f"is_p{period}")]

    @property
    def available_periods(self) -> list[PeriodType]:
        return [period for period in range(1, 5) if getattr(self, f"is_p{period}")]

    def semi_available_periods(
            self, available_classrooms: ClassroomList,
            exclude_chosen_period: bool = True):
        """
        exclude_chosen_period: don't include the chosen period of the ticket (assumes it exists)
        Returns a list of periods where the period's classroom exists.
        Means that this ticket can be chucked into these classrooms without decreasing efficiency.
        """
        semi_available_periods: list[PeriodType] = []

        for period in range(1, 5):
            period: PeriodType

            if exclude_chosen_period and period == self.chosen_period:
                continue
            classroom = getattr(self, f"p{period}")
            if classroom in available_classrooms:
                semi_available_periods.append(period)

        return semi_available_periods

    def __repr__(self):
        # for dev purposes only
        p1 = '' if self.is_p1 else '\''
        p2 = '' if self.is_p2 else '\''
        p3 = '' if self.is_p3 else '\''
        p4 = '' if self.is_p4 else '\''
        item = "SS" if self.item_type == "Special Serenade" else self.item_type[0]
        return f"<{self.pk} {STUDENTS[self.recipient_id]['Name']} " \
               f"{self.p1}{p1} {self.p2}{p2} {self.p3}{p3} {self.p4}{p4} {item}>"


class TicketList(list):
    @classmethod
    def from_sql_ticket_list(cls, sql_ticket_list: list[Ticket]):
        return cls(TicketToSort.from_sql_ticket(sql_ticket) for sql_ticket in sql_ticket_list)

    def has_item_type(self, items=None) -> bool:
        # checks if a list of tickets contains any ticket with a given item type(s)
        for ticket in self:
            if ticket.item_type in items:
                return True
        return False

    @property
    def has_serenades(self):
        return self.has_item_type(('Serenade', 'Special Serenade'))

    @property
    def has_non_serenades(self):
        return self.has_item_type(('Chocolate', 'Rose'))

    def num_items(self, items: Sequence[ItemType]) -> int:
        # Returns the number of tickets that are a specified type of item(s)
        count = 0
        for ticket in self:
            if ticket.item_type in items:
                count += 1
        return count

    @property
    def num_serenades(self):
        return self.num_items(("Serenade", "Special Serenade"))

    @property
    def num_non_serenades(self):
        return self.num_items(("Chocolate", "Rose"))

    def sort_by_item_type(self):
        self.sort(key=lambda ticket: ticket.item_type)
        return self

    def filter_by_item_type(self, items: Sequence[ItemType]):
        """
        Returns a copy of self but only containing tickets of the specified item type
        """
        cls = self.__class__
        filtered = cls()
        for ticket in self:
            if ticket.item_type in items:
                filtered.append(ticket)
        return filtered

    @property
    def filter_serenades(self):
        return self.filter_by_item_type(("Serenade", "Special Serenade"))

    @property
    def period_distribution(self):
        """
        Gets how many tickets each period has (ignores tickets which haven't been allocated yet)
        """
        distribution: dict[PeriodType, int] = {1: 0, 2: 0, 3: 0, 4: 0}
        for ticket in self:
            if ticket.has_no_choice:
                period = ticket.chosen_period
                distribution[period] += 1
        return distribution

    @property
    def filter_has_no_choice(self):
        cls = self.__class__
        return cls([ticket for ticket in self if ticket.has_no_choice])

    @property
    def grouped_by_num_periods_available(self):
        """
        A dict grouping tickets by the number of periods that are still available to them
        \nKey: number of periods available
        \nValue: the tickets with that many periods available
        :return: Dict
        """
        cls = self.__class__
        num_periods_available_distribution: dict[PeriodType, TicketList] = {
            1: cls(), 2: cls(), 3: cls(), 4: cls()
        }

        for ticket in self:
            num_periods_available_distribution[ticket.num_periods_available].append(ticket)

        return num_periods_available_distribution

    @property
    def grouped_by_num_periods_available_reversed(self):
        cls = self.__class__
        num_periods_available_distribution: dict[PeriodType, TicketList] = {
            4: cls(), 3: cls(), 2: cls(), 1: cls()
        }

        for ticket in self:
            num_periods_available_distribution[ticket.num_periods_available].append(ticket)

        return num_periods_available_distribution


class Classroom:
    # the REGEX used to determine what is a valid classroom name
    # if invalid, classroom will not be visited
    # classroom_pattern = r"[A-Z]\d{3}"
    classroom_pattern = room_format
    bad_classroom_pattern = bad_room_format

    def __init__(self, original_name: str, period: PeriodType):
        """Variables"""
        self.period = period
        self.original_name = original_name       # the name as it appears on the timetable
        self.clean_name = self.get_clean_name()

        self.tickets = TicketList()
        self.is_valid = self.verify_classroom_name()
        self._is_special = False  # if a duplicate class solely for a special serenade

    def __repr__(self):
        return self.extended_name

    @property
    def extended_name(self):
        if self.is_special:
            return f"{self.period}-{self.clean_name}-S"
        else:
            return f"{self.period}-{self.clean_name}"

    def get_clean_name(self):
        dotless_name = self.original_name.replace('.', '')
        clean_name = re.sub("([A-Z])G", r"\g<1>0", dotless_name)
        return clean_name

    @property
    def is_special(self):
        return self._is_special

    @is_special.setter
    def is_special(self, value: bool):
        self._is_special = value

        if value:
            original_block = self.original_name[0]
            original_block_index = CLASSROOM_GEOGRAPHIC_ORDER.index(original_block)

            new_block_index = (original_block_index + math.floor(len(CLASSROOM_GEOGRAPHIC_ORDER) / 2)) \
                              % len(CLASSROOM_GEOGRAPHIC_ORDER)
            new_block = CLASSROOM_GEOGRAPHIC_ORDER[new_block_index]

            self.clean_name = new_block + self.clean_name[1:]

    def verify_classroom_name(self) -> bool:
        return re.match(self.classroom_pattern, self.clean_name) is not None \
               and re.match(self.bad_classroom_pattern, self.clean_name) is None  # must be a valid AND not a bad class

    @property
    def is_bad(self) -> bool:
        return re.match(self.bad_classroom_pattern, self.clean_name)

    @property
    def must_keep(self):
        for ticket in self.tickets:
            if ticket.has_no_choice and ticket.chosen_period == self.period:
                return True
        return False

    def limit_serenades(self, max_num_serenades: int):
        # limits the number of serenading tickets in this classroom
        # IMPORTANT: must be externally checked to ensure that there are enough classrooms left for remaining serenades
        num_serenades = self.tickets.num_serenades
        if num_serenades <= max_num_serenades:
            return
        for num_periods, tickets in self.tickets.grouped_by_num_periods_available_reversed.items():
            for ticket in tickets:
                if ticket.item_type == "Serenade":
                    if not ticket.has_no_choice:
                        setattr(ticket, f"is_p{self.period}", False)
                        self.tickets.remove(ticket)
                        num_serenades -= 1
                        if num_serenades <= max_num_serenades:
                            return

    def limit_non_serenades(self, max_num_non_serenades: int):
        # limits the number of non_serenading tickets in this classroom
        # IMPORTANT: must be externally checked to ensure that there are enough classrooms left for the remaining items

        # only if this classrooms has a serenade
        if not self.tickets.has_serenades:
            return

        num_non_serenades = self.tickets.num_non_serenades
        if num_non_serenades <= max_num_non_serenades:
            return
        for num_periods, tickets in self.tickets.grouped_by_num_periods_available_reversed.items():
            for ticket in tickets:
                if ticket.item_type == "Chocolate" or ticket.item_type == "Rose":
                    if not ticket.has_no_choice:
                        setattr(ticket, f"is_p{self.period}", False)
                        self.tickets.remove(ticket)
                        num_non_serenades -= 1
                        if num_non_serenades <= max_num_non_serenades:
                            return


class ClassroomList(list):
    def __contains__(self, classroom: Classroom) -> bool:
        return classroom.extended_name in map(lambda existing_classroom: existing_classroom.extended_name, self)

    @classmethod
    def from_tickets(cls, tickets: TicketList, existing_tickets: TicketList = None):
        self = cls()
        if existing_tickets is not None:
            for ticket in existing_tickets:
                for period in range(1, 5):
                    classroom = getattr(ticket, f"p{period}")
                    if classroom not in self:
                        self.append(classroom)

        for ticket in tickets:
            if existing_tickets is not None and ticket in existing_tickets:
                continue
            for period in range(1, 5):
                classroom_name = getattr(ticket, f"p{period}")
                new_classroom = Classroom(classroom_name, period)

                if new_classroom in self:
                    existing_classroom = self.get_existing_classroom(new_classroom)
                    existing_classroom.tickets.append(ticket)
                    setattr(ticket, f"p{period}", existing_classroom)
                else:
                    new_classroom.tickets.append(ticket)
                    setattr(ticket, f"p{period}", new_classroom)
                    self.append(new_classroom)

                # prevent non-existent or bad classes from being chosen
                if not new_classroom.is_valid:
                    setattr(ticket, f"is_p{period}", False)

        # remove non-existent classrooms
        for classroom in self[:]:
            if not classroom.is_valid:
                self.remove(classroom)
        return self

    def get_existing_classroom(self, new_classroom: Classroom):
        # gets an existing classroom in the list, given a new Classroom object with the same name
        for classroom in self:
            if classroom.extended_name == new_classroom.extended_name:
                return classroom
        raise KeyError("Classroom not found.")

    @property
    def sorted_by_length(self):
        return sorted(self, key=lambda classroom: len(classroom.tickets))

    @property
    def sorted_by_length_reversed(self):
        return sorted(self, key=lambda classroom: len(classroom.tickets), reverse=True)

    @property
    def filter_has_serenades(self):
        # classrooms that contain at least one serenade
        cls = self.__class__
        return cls([classroom for classroom in self if classroom.tickets.has_serenades])

    @property
    def filter_has_non_serenades(self):
        # classrooms that have at least one non-serenade
        cls = self.__class__
        return cls([classroom for classroom in self if classroom.tickets.has_non_serenades])

    @property
    def filter_has_no_serenades(self):
        # classrooms that contain ZERO serenades
        cls = self.__class__
        return cls([classroom for classroom in self if not classroom.tickets.has_serenades])

    @property
    def num_tickets(self) -> int:
        num_tickets = 0
        for classroom in self:
            num_tickets += len(classroom.tickets)
        return num_tickets

    @property
    def grouped_by_length(self):
        """
        Key: number of tickets in a given classroom
        Value: list of classrooms with that many tickets
        E.g. {0: ["1-A204", "3-I115"], 1: ["1-F101", "2-G101"]}
        """
        classrooms_by_length = {}

        for classroom in self:
            tickets = classroom.tickets
            length = len(tickets)
            if length in classrooms_by_length:
                classrooms_by_length[length].append(classroom)
            else:
                cls = self.__class__
                classrooms_by_length[length] = cls([classroom])

        classrooms_by_length = {length: classrooms_by_length[length] for length in sorted(classrooms_by_length.keys())}

        return classrooms_by_length

    @property
    def grouped_by_length_reversed(self):
        classrooms_by_length = {}

        for classroom in self:
            tickets = classroom.tickets
            length = len(tickets)
            if length in classrooms_by_length:
                classrooms_by_length[length].append(classroom)
            else:
                cls = self.__class__
                classrooms_by_length[length] = cls([classroom])

        classrooms_by_length = {length: classrooms_by_length[length]
                                for length in sorted(classrooms_by_length.keys(), reverse=True)}

        return classrooms_by_length

    @staticmethod
    def split(a, n: int):
        k, m = divmod(len(a), n)
        return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))

    @property
    def grouped_by_period(self):
        """
        :return: Returns a dict with key=period and value=ClassroomList of classrooms in that period
        """
        cls = self.__class__
        classrooms_by_period: dict[PeriodType, ClassroomList] = {
            1: cls(), 2: cls(), 3: cls(), 4: cls()
        }

        for classroom in self:
            classrooms_by_period[classroom.period].append(classroom)

        return classrooms_by_period

    @property
    def grouped_by_geography(self):
        """
        :return: Returns a dict where key is a classroom block and values are a ClassroomList in that block.
        Classrooms physically next to each other appear adjacent in the list.
        """
        # group classrooms in blocks, with the blocks in correct oder
        classrooms_by_geography = {block: ClassroomList() for block in CLASSROOM_GEOGRAPHIC_ORDER}
        for classroom in self:
            block = classroom.clean_name[0]
            if block in classrooms_by_geography:
                classrooms_by_geography[classroom.clean_name[0]].append(classroom)
            else:
                raise KeyError(f"Class block '{block}' could not be found.")

        # sort alphabetically within each block
        for classroom_list in classrooms_by_geography.values():
            classroom_list.sort(key=lambda classroom1: classroom1.clean_name)

        return classrooms_by_geography

    @property
    def sorted_by_geography(self):
        """
        :return: Flattens grouped_by_geography into a list
        """
        classrooms_by_geography = ClassroomList()
        for classrooms in self.grouped_by_geography.values():
            classrooms_by_geography.extend(classrooms)
        return classrooms_by_geography

    def sorted_by_period_distribution(self, tickets: TicketList) -> Generator[Classroom]:
        """
        Sorts self by order of ticket distribution (fullest first),
        then distribution of destroyed classes.

        Recalculates the smallest period after each yield so that modifications to the period
        distribution between yields are considered.

        Tickets input is the TicketList which the period distribution is derived from
        (should be a list of every ticket).
        """
        classroom_copy = self.copy()
        for i in range(len(classroom_copy)):
            if len(classroom_copy) > 1:  # don't bother if only 1 class in list
                ticket_period_distribution = tickets.period_distribution
                chosen_classroom = max(
                    classroom_copy,
                    key=lambda classroom: ticket_period_distribution[classroom.period]
                )
                classroom_copy.remove(chosen_classroom)
                yield chosen_classroom
            else:
                yield classroom_copy[0]

    def sorted_by_eliminated_period_distribution_then_length(
            self, period_distribution: dict[PeriodType, int]) -> Generator[Classroom]:
        """
        Sorts by order of periods which have the least number of tickets eliminated from, then by length
        """
        classroom_copy = self.copy()
        for i in range(len(classroom_copy)):
            emptiest_period = min(period_distribution, key=lambda period: period_distribution[period])
            classrooms_in_period = [classroom for classroom in classroom_copy if classroom.period == emptiest_period]
            if len(classrooms_in_period) > 0:
                chosen_classroom = min(classrooms_in_period,
                                       key=lambda classroom: (not classroom.tickets.has_serenades,
                                                              len(classroom.tickets), random.random()))
                classroom_copy.remove(chosen_classroom)
                yield chosen_classroom
            else:
                del period_distribution[emptiest_period]
                emptiest_period = min(period_distribution, key=lambda period: period_distribution[period])
                classrooms_in_period = [classroom for classroom in classroom_copy if
                                        classroom.period == emptiest_period]
                chosen_classroom = min(classrooms_in_period,
                                       key=lambda classroom: (not classroom.tickets.has_serenades,
                                                              len(classroom.tickets), random.random()))
                classroom_copy.remove(chosen_classroom)
                yield chosen_classroom


class Person:
    def __init__(self, student_id):
        self.id = student_id
        self.tickets = TicketList()

    def __repr__(self):
        return STUDENTS[self.id]['Name']

    def num_items(self, items: tuple) -> int:
        num_items = 0
        for ticket in self.tickets:
            if ticket.item_type in items:
                num_items += 1
        return num_items


class People(list):
    def __init__(self, tickets: TicketList):
        super().__init__(self)
        for ticket in tickets:
            new_person = Person(ticket.recipient_id)
            if new_person in self:
                existing_person = self.get_existing_person(new_person)
                existing_person.tickets.append(ticket)
            else:
                new_person.tickets.append(ticket)
                self.append(new_person)

    def __contains__(self, person: Person):
        return person.id in map(lambda existing_person: existing_person.id, self)

    def get_existing_person(self, new_person: Person) -> Person:
        # gets an existing person in the list, given a new Person object with the same name
        for existing_person in self:
            if existing_person.id == new_person.id:
                return existing_person
        raise KeyError("Person not found")

    def grouped_by_num_items(
            self, items: Sequence[ItemType] | None = None, reverse: bool = True):
        """
        Groups people with x number of items of specified type
        Key: number of items of the specified type
        Value: list of people with that number of items of specified type
        Also sorted by ascending order (can be reversed to descending)
        """
        people_grouped_by_num_items: dict[int, list[Person]] = {}

        for person in self:
            if items is None:
                num_items = len(person.tickets)
            else:
                num_items = person.num_items(items)

            if num_items in people_grouped_by_num_items:
                people_grouped_by_num_items[num_items].append(person)
            else:
                people_grouped_by_num_items[num_items] = [person]

        people_grouped_by_num_items = {
            num_items: people_grouped_by_num_items[num_items]
            for num_items in sorted(people_grouped_by_num_items.keys(), reverse=reverse)}

        return people_grouped_by_num_items


class PeriodGroup:
    """A group but for a specific period. Each delivery group is made of 4 period groups.
    Mostly a virtual object for intermediate use only"""
    def __init__(self, classrooms: ClassroomList):
        self.classrooms = classrooms

    def __repr__(self):
        return f"<PeriodGroup {self.classrooms} s={self.num_serenades} N={self.num_tickets}>"

    @property
    def num_tickets(self) -> int:
        num_tickets = 0
        for classroom in self.classrooms:
            num_tickets += len(classroom.tickets)
        return num_tickets

    @property
    def num_serenades(self) -> int:
        num_serenades = 0
        for classroom in self.classrooms:
            num_serenades += classroom.tickets.num_serenades
        return num_serenades


class PeriodGroupList(list):
    def __init__(self, classrooms: ClassroomList, num_groups: int):
        super().__init__(self)
        # create a list of period groups
        for period_group_classrooms in self.split(classrooms, num_groups):
            self.append(PeriodGroup(period_group_classrooms))

        # if some groups will get more than 1 classroom each, try to ensure it's evenly distributed
        if len(classrooms) > num_groups:
            self.distribute_classrooms()

        self.sort_tickets_by_person()

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
                # print("TicketSorter: Fullest group and emptiest group are the same size.")
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
                period_group.classrooms = ClassroomList(state[index])

    def sort_tickets_by_person(self):
        for period_group in self:
            for classroom in period_group.classrooms:
                classroom.tickets.sort(key=lambda ticket: ticket.recipient_id)

    @property
    def as_classroom_sizes(self) -> list:
        """
        :return: Returns itself but all of the PeriodGroups have been converted into lists of its classroom lengths
        """
        return [list(map(lambda classroom: len(classroom.tickets), period_group.classrooms)) for period_group in self]

    @property
    def as_classroom_sizes_serenades(self) -> list:
        return [list(map(lambda classroom: classroom.tickets.num_serenades, period_group.classrooms))
                for period_group in self]

    @property
    def fullest_group(self):
        return max(self, key=lambda period_group: period_group.num_tickets)

    @property
    def emptiest_group(self):
        return min(self, key=lambda period_group: period_group.num_tickets)


class DeliveryGroup:
    def __init__(self, number: int, is_serenading: bool):
        self.is_serenading = is_serenading
        self.number = number
        self.p1 = ClassroomList()
        self.p2 = ClassroomList()
        self.p3 = ClassroomList()
        self.p4 = ClassroomList()

    def __repr__(self):
        return f"<DeliveryGroup:{self.name} " \
               f"{len(self.p1)} {len(self.p2)} {len(self.p3)} {len(self.p4)} " \
               f"s={self.tickets.num_serenades} N={len(self.tickets)}>"

    @property
    def name(self):
        initial = "S" if self.is_serenading else "N"
        return f"{initial}{self.number}"

    @property
    def tickets(self) -> TicketList:
        tickets = TicketList()
        for period in range(1, 5):
            classrooms = getattr(self, f"p{period}")
            for classroom in classrooms:
                tickets.extend(classroom.tickets)
        return tickets

    @property
    def num_classrooms(self) -> int:
        return len(self.p1) + len(self.p2) + len(self.p3) + len(self.p4)


class DeliveryGroupList(list):
    def update(self, period_groups: PeriodGroupList, period: int):
        if len(period_groups) > len(self):
            raise OverflowError("Length of PeriodGroupList must not be more than length of DeliveryGroupList")

        empty_delivery_groups = self.filter_empty_delivery_groups(period)
        for i in range(len(empty_delivery_groups)):
            emptiest_period_group = period_groups.emptiest_group
            fullest_delivery_group = empty_delivery_groups.fullest_group
            setattr(fullest_delivery_group, f"p{period}", emptiest_period_group.classrooms)
            period_groups.remove(emptiest_period_group)
            empty_delivery_groups.remove(fullest_delivery_group)

    def filter_empty_delivery_groups(self, period: int):
        return DeliveryGroupList([delivery_group for delivery_group in self
                                  if len(getattr(delivery_group, f"p{period}")) == 0])

    @property
    def fullest_group(self) -> DeliveryGroup:
        if len(self) > 1:
            return max(self, key=lambda group: len(group.tickets))
        elif len(self) == 1:
            return self[0]
        else:
            raise KeyError("Cannot return max of blank.")

    @property
    def emptiest_group(self) -> DeliveryGroup:
        if len(self) > 1:
            return min(self, key=lambda group: len(group.tickets))
        elif len(self) == 1:
            return self[0]
        else:
            raise KeyError("Cannot return min of blank.")


class TicketSorter:
    def __init__(self, tickets: list, serenading_groups: int, non_serenading_groups: int,
                 max_serenades_per_class: int = 2, max_non_serenades_per_serenading_class: int = 3,
                 extra_special_serenades: bool = True, enforce_distribution: bool = True):
        """Options (Disclaimer: enabling an option does not guarantee that it is always true)"""
        # special serenades will not be grouped with regular serenades (ignores non-serenades)
        # less efficient but nicer for those who receive special serenades
        # puts more stress on serenading groups
        self.EXTRA_SPECIAL_SERENADES = extra_special_serenades

        # the algorithm will try to ensure that a person will have each of their items done separately
        # this is normally done if it is possible without decreasing efficiency (pretty rarely)
        # this enforces it to happen whenever possible, which decreases efficiency but items are more evenly distributed
        self.ENFORCE_DISTRIBUTION = enforce_distribution

        # the max number of serenades in a class (ignores non-serenades)
        # increasing these values increases the efficiency (decreases class visits required)
        # however, too a high a value make class visits fat
        # set to 0 to disable limiting
        self.MAX_SERENADES_PER_CLASS = max_serenades_per_class

        # the max number of non-serenade items in a class
        # increasing these values increases the efficiency (decreases class visits required)
        # set to 0 to disable limiting
        self.MAX_NON_SERENADES_PER_SERENADING_CLASS = max_non_serenades_per_serenading_class

        """Constants"""
        # these two are mutually exclusive (you cannot be both a serenading group AND a non-serenading group)
        self.NUM_SERENADING_GROUPS = serenading_groups  # the number of serenading groups
        self.NUM_NON_SERENADING_GROUPS = non_serenading_groups  # the number of groups which are NOT serenading

        """Output"""
        # a list of groups (both serenading and non-serenading), with their assigned tickets as attributes
        self.output_serenading_groups = DeliveryGroupList()
        self.output_non_serenading_groups = DeliveryGroupList()

        """Methods"""
        self.all_tickets = TicketList(tickets)
        self.bad_classrooms = ClassroomList()    # classrooms which are bad but have special serenade so must be visited
        self.special_classrooms = ClassroomList()       # duplicate classrooms because extra_special_serenades

        # first pass with only serenades
        self.tickets = self.all_tickets.filter_serenades
        self.classrooms = ClassroomList.from_tickets(self.tickets)
        self.initialise_special_serenades()
        if self.EXTRA_SPECIAL_SERENADES:
            self.make_special_serenades_extra_special()
        self.distribute_tickets(("Serenade",))
        if not self.ENFORCE_DISTRIBUTION:
            self.eliminate_classrooms(True)

        # second pass with all item types
        self.classrooms = ClassroomList.from_tickets(self.all_tickets, self.tickets)
        if self.EXTRA_SPECIAL_SERENADES:
            self.classrooms.extend(self.special_classrooms)
        self.classrooms.extend(self.bad_classrooms)
        self.tickets = self.all_tickets
        # self.distribute_tickets(("Chocolate", "Rose"))        # optional. massively decreases efficiency (~2x)
        self.eliminate_classrooms(False)
        if self.EXTRA_SPECIAL_SERENADES:
            self.fill_special_classrooms()

        self.assign_tickets_to_groups()
        self.print_statistics()

    def initialise_special_serenades(self):
        for ticket in self.tickets:
            if ticket.item_type != "Special Serenade":
                continue

            classroom = getattr(ticket, f"p{ticket.ss_period}")

            if classroom.is_valid:
                ticket.choose_period(ticket.ss_period)

            elif classroom.is_bad:
                ticket.choose_period(ticket.ss_period)

                if classroom in self.bad_classrooms:
                    continue

                self.classrooms.append(classroom)
                self.bad_classrooms.append(classroom)
            else:
                print(f"ERROR: Classroom name unknown: {classroom.extended_name}")

    def make_special_serenades_extra_special(self):
        # removes regular serenades from classrooms that have special serenades
        for ticket in self.tickets:
            if ticket.item_type != "Special Serenade":
                continue

            period = ticket.chosen_period
            classroom = getattr(ticket, f"p{period}")

            for other_ticket in classroom.tickets:
                if other_ticket.item_type != "Serenade":
                    continue

                if not other_ticket.has_no_choice:
                    # If still more than one choice
                    setattr(other_ticket, f"is_p{period}", False)
                    classroom.tickets.remove(other_ticket)
                elif other_ticket.chosen_period != period:
                    classroom.tickets.remove(other_ticket)
                else:
                    # If a special serenade cannot be made extra special,
                    # create a special classroom for it

                    special_classroom = Classroom(classroom.original_name, period)

                    if special_classroom not in self.special_classrooms:
                        self.classrooms.append(special_classroom)
                        self.special_classrooms.append(special_classroom)
                    else:
                        special_classroom = self.special_classrooms.get_existing_classroom(special_classroom)

                    if ticket not in special_classroom.tickets:
                        classroom.tickets.remove(ticket)
                        setattr(ticket, f"p{period}", special_classroom)
                        ticket.choose_period(period)

        for classroom in self.special_classrooms:
            classroom.is_special = True

    def distribute_tickets(self, items: Sequence[ItemType]):
        """
        Distributes each person's tickets so that they receive them all over many periods instead of
        all at once

        :param items: Only tickets of these item types are considered
        :return: None
        """
        period_distribution = self.tickets.period_distribution
        item_period_distribution = {1: 0, 2: 0, 3: 0, 4: 0}
        for num_tickets, people in People(self.tickets).grouped_by_num_items(items).items():
            # num_tickets is the number of total tickets the person has
            if num_tickets <= 0:
                continue

            for person in people:
                person_tickets = person.tickets.filter_by_item_type(items)
                if self.ENFORCE_DISTRIBUTION:
                    for ticket in person_tickets:
                        if ticket.has_no_choice:
                            item_period_distribution[ticket.chosen_period] += 1
                    for ticket in person_tickets:
                        if not ticket.has_no_choice:
                            self.choose_emptiest_period(ticket, item_period_distribution, period_distribution)
                else:
                    for num_periods_available, tickets in person_tickets.grouped_by_num_periods_available.items():
                        # num_periods_available is how many free periods each ticket has
                        if not 1 < num_periods_available <= num_tickets:
                            continue

                        for ticket in tickets:
                            self.choose_emptiest_period(ticket, item_period_distribution, period_distribution)
        self.cleanup_classrooms()

    @staticmethod
    def choose_emptiest_period(ticket: TicketToSort, item_period_distribution: dict, period_distribution: dict):
        available_periods = ticket.available_periods
        # evenly distribute the tickets among the available classes
        # if already even, try to keep the global distribution even
        chosen_period = min(available_periods,
                            key=lambda period: (item_period_distribution[period],
                                                period_distribution[period]))
        ticket.choose_period(chosen_period)
        period_distribution[chosen_period] += 1
        item_period_distribution[chosen_period] += 1

    def eliminate_classrooms(self, serenade_only_pass: bool):
        eliminated_period_distribution: dict[PeriodType, int] = {1: 0, 2: 0, 3: 0, 4: 0}

        for classroom in self.classrooms.sorted_by_eliminated_period_distribution_then_length(
                eliminated_period_distribution):
            period = classroom.period
            tickets = classroom.tickets

            if classroom.must_keep:
                if serenade_only_pass:
                    if self.MAX_SERENADES_PER_CLASS > 0:   # no limit if set to 0
                        classroom.limit_serenades(self.MAX_SERENADES_PER_CLASS)
                else:
                    if self.MAX_NON_SERENADES_PER_SERENADING_CLASS > 0:    # no limit if set to 0
                        classroom.limit_non_serenades(self.MAX_NON_SERENADES_PER_SERENADING_CLASS)

                # if classroom must be kept, make every other ticket stay in this class
                for ticket in tickets:
                    ticket.choose_period(period)
            else:
                # if classroom can be destroyed, remove tickets associated with it
                # (destroy the actual classroom later)
                for ticket in tickets[:]:
                    setattr(ticket, f'is_p{period}', False)
                    tickets.remove(ticket)
                    eliminated_period_distribution[period] += 1
        self.cleanup_classrooms()

    def cleanup_classrooms(self):
        # delete empty classrooms
        for classroom in self.classrooms[:]:
            if len(classroom.tickets) < 1:
                self.classrooms.remove(classroom)

    def fill_special_classrooms(self):
        # adds non-serenades to special classrooms so it's not just a single special serenade
        for special_classroom in self.special_classrooms:
            for classroom in self.classrooms:
                if len(special_classroom.tickets) >= \
                        self.MAX_SERENADES_PER_CLASS + self.MAX_NON_SERENADES_PER_SERENADING_CLASS:
                    break

                if classroom.period == special_classroom.period and \
                        classroom.clean_name == special_classroom.clean_name:       # if the same class

                    people = People(classroom.tickets.filter_by_item_type(("Chocolate", "Rose")))

                    for num_tickets, people in people.grouped_by_num_items().items():
                        for person in people:
                            if len(special_classroom.tickets) >= \
                                    self.MAX_SERENADES_PER_CLASS + self.MAX_NON_SERENADES_PER_SERENADING_CLASS:
                                break

                            # Pick random ticket (doesn't really matter since non-serenade)
                            ticket = person.tickets[0]

                            if len(special_classroom.tickets) >= \
                                    self.MAX_SERENADES_PER_CLASS + self.MAX_NON_SERENADES_PER_SERENADING_CLASS:
                                break
                            else:
                                classroom.tickets.remove(ticket)
                                special_classroom.tickets.append(ticket)

    def assign_tickets_to_groups(self):
        self.output_serenading_groups = DeliveryGroupList(
            [DeliveryGroup(i + 1, True) for i in range(self.NUM_SERENADING_GROUPS)]
        )
        self.output_non_serenading_groups = DeliveryGroupList(
            [DeliveryGroup(i + 1, False) for i in range(self.NUM_NON_SERENADING_GROUPS)]
        )

        for period, classrooms_in_period in self.classrooms.grouped_by_period.items():
            serenade_classes = classrooms_in_period.filter_has_serenades
            no_serenade_classes = classrooms_in_period.filter_has_no_serenades

            serenading_period_groups = self.get_period_groups(
                serenade_classes, True)
            self.output_serenading_groups.update(serenading_period_groups, period)

            non_serenading_period_groups = self.get_period_groups(
                no_serenade_classes, False)
            self.output_non_serenading_groups.update(non_serenading_period_groups, period)

    def get_period_groups(self, classrooms: ClassroomList, is_serenading_group: bool):
        num_groups = self.NUM_SERENADING_GROUPS if is_serenading_group \
            else self.NUM_NON_SERENADING_GROUPS

        classrooms = classrooms.sorted_by_geography
        return PeriodGroupList(classrooms, num_groups)

    def print_statistics(self):
        print("\nNumber of Classroom Visits Per Period:")
        classrooms_per_period = {1: 0, 2: 0, 3: 0, 4: 0}
        for classroom in self.classrooms:
            classrooms_per_period[classroom.period] += 1
        for period, number in classrooms_per_period.items():
            print(f"\tPeriod {period}: {number}")
        print(f"Total: {len(self.classrooms)}")

        print("\nNumber of Tickets Per Item Type:")
        item_type_distribution = {"Chocolate": 0, "Rose": 0, "Serenade": 0, "Special Serenade": 0}
        for ticket in self.tickets:
            item_type_distribution[ticket.item_type] += 1
        for item_type, number in item_type_distribution.items():
            print(f"\t{item_type}: {number}")
        print(f"Total: {len(self.tickets)}")

        print("\nNumber of items per classroom visit:")
        total_tickets = 0
        for size, classrooms in self.classrooms.grouped_by_length.items():
            print(f"\t{size}: {len(classrooms)}\t{'|' * len(classrooms)}")
            total_tickets += size * len(classrooms)
        average_classroom_size = round(total_tickets / len(self.classrooms), 3)
        print(f"Average: {average_classroom_size}")

        print("\nTickets per serenading group:")
        total_serenading_groups = 0
        for group in self.output_serenading_groups:
            print(f"\tClassrooms: {group.num_classrooms} \t| "
                  f"Serenades: {group.tickets.num_serenades}\t+ Non-serenades: {group.tickets.num_non_serenades} "
                  f"= Total: {group.tickets.num_serenades + group.tickets.num_non_serenades}")
            total_serenading_groups += group.tickets.num_serenades + group.tickets.num_non_serenades
        print(f"Total: {total_serenading_groups}")

        print("\nTickets per non-serenading group:")
        total_non_serenading_groups = 0
        for group in self.output_non_serenading_groups:
            print(f"\tClassrooms: {group.num_classrooms} \t| Non-serenades: {group.tickets.num_non_serenades}")
            total_non_serenading_groups += group.tickets.num_non_serenades
        print(f"Total: {total_non_serenading_groups}")
        print(f"\nTotal (both types): {total_serenading_groups + total_non_serenading_groups}")

        if len(self.special_classrooms) > 0:
            print("\nSpecial Classrooms:")
            for classroom in self.special_classrooms:
                print(f"\t{classroom} ({classroom.clean_name})")

        if len(self.bad_classrooms) > 0:
            print("\nBad Classrooms:")
            for classroom in self.bad_classrooms:
                print(f"\t{classroom}")

        delivered_tickets = []
        for group in self.output_serenading_groups:
            for ticket in group.tickets:
                delivered_tickets.append(ticket)
        for group in self.output_non_serenading_groups:
            for ticket in group.tickets:
                delivered_tickets.append(ticket)
        print_header = True
        for ticket in self.all_tickets:
            if ticket not in delivered_tickets:
                if print_header:
                    print("\nUndelivered Tickets:")
                    print_header = False
                print(f"\t{ticket}")


"""Dev/Testing Stuff"""


def load_tickets() -> TicketList:
    tickets = TicketList()

    # Load student timetables
    students = {}
    with open(f"{DirectoryLocations.DEV_STUFF}/people_2023.csv") as file:
        reader = csv.DictReader(file)
        for row in reader:
            students[row['ID']] = row

    # Create tickets from file
    with open(f"{DirectoryLocations.DEV_STUFF}/tickets_2023.json") as tickets_file:
        data = json.load(tickets_file)

        for ticket in data:
            fields = ticket["fields"]
            recipient_id = fields["recipient_id"]

            ticket = TicketToSort(
                pk=ticket["pk"],
                recipient_id=recipient_id,
                item_type=fields["item_type"],
                p1=students[recipient_id]["P1"],
                p2=students[recipient_id]["P2"],
                p3=students[recipient_id]["P3"],
                p4=students[recipient_id]["P4"],
                ss_period=fields["ss_period"]
            )

            tickets.append(ticket)

    return tickets


def main():
    start_time = datetime.now()

    # Load dummy data for testing
    tickets = load_tickets()

    loaded_time = datetime.now()

    ticket_sorter = TicketSorter(
        tickets, 10, 10,
        max_serenades_per_class=2,
        max_non_serenades_per_serenading_class=3,
        extra_special_serenades=True,
        enforce_distribution=True
    )

    end_time = datetime.now()

    print(f"Done! Loading: {loaded_time - start_time} Sorting: {end_time - loaded_time}")


if __name__ == "__main__":
    main()
