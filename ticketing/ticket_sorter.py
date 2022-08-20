import re
import csv
import random

# tells the algorithm what order the classrooms are physically located in (only linear unfortunately)
CLASSROOM_GEOGRAPHIC_ORDER = "LBCDAEFGOPTJHIRX"

if __name__ == "__main__":
    from constants import FileNames, DirectoryLocations
    from timetable_parser import room_format

    random.seed(56)

    STUDENTS = {}
    with open(FileNames.STUDENTS) as file:
        reader = csv.DictReader(file)
        for row in reader:
            STUDENTS[row['ID']] = row
else:
    from .class_lookup import STUDENTS
    from .timetable_parser import room_format


def convert_tickets(tickets) -> list:
    # converts: tickets -> tickets_to_sort
    # tickets: list of tickets following the SQL Ticket class in model.py
    # tickets_to_sort: list of tickets following the TicketToSort class in sort_tickets.py
    tickets_to_sort = []
    for ticket in tickets:
        recipient_id = ticket.recipient_id
        p1 = STUDENTS[ticket.recipient_id]["P1"]
        p2 = STUDENTS[ticket.recipient_id]["P2"]
        p3 = STUDENTS[ticket.recipient_id]["P3"]
        p4 = STUDENTS[ticket.recipient_id]["P4"]
        if ticket.item_type == "Special Serenade":
            ticket_to_sort = TicketToSort(ticket.pk, recipient_id, ticket.item_type, p1, p2, p3, p4, ticket.ss_period)
        else:
            ticket_to_sort = TicketToSort(ticket.pk, recipient_id, ticket.item_type, p1, p2, p3, p4)
        tickets_to_sort.append(ticket_to_sort)
    return tickets_to_sort


def sort_tickets(tickets: list, num_serenading_groups: int, num_non_serenading_groups: int,
                 max_serenades_per_class: int, max_non_serenades_per_serenading_class: int,
                 extra_special_serenades: bool, enforce_distribution: bool) -> dict:
    # input in argument: tickets = Ticket.objects.all()
    tickets_to_sort = convert_tickets(tickets)
    ticket_sorter = TicketSorter(tickets_to_sort, num_serenading_groups, num_non_serenading_groups,
                                 max_serenades_per_class=max_serenades_per_class,
                                 max_non_serenades_per_serenading_class=max_non_serenades_per_serenading_class,
                                 extra_special_serenades=extra_special_serenades,
                                 enforce_distribution=enforce_distribution)
    groups = {True: ticket_sorter.output_serenading_groups,
              False: ticket_sorter.output_non_serenading_groups}
    return groups


class TicketToSort:
    def __init__(self, pk: int, recipient_id: str, item_type: str, p1: str, p2: str, p3: str, p4: str,
                 ss_period: int = None):
        # ticket info
        self.pk = pk
        self.recipient_id = recipient_id
        self.item_type = item_type
        self.ss_period = ss_period  # the period chosen by the special serenade (if applicable)

        # where the recipient's classes are for each period don't rename or else setattr() will break
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4

        # whether the algorithm has chosen this period. don't rename or else setattr() will break
        self.is_p1 = True
        self.is_p2 = True
        self.is_p3 = True
        self.is_p4 = True

        if item_type == "Special Serenade" and self.ss_period is None:
            raise AssertionError("SS_period must be specified for special serenades.")

    @property
    def chosen_period(self) -> int:
        # if a ticket only has 1 period it can go to, return what it is
        if self.has_no_choice:
            for period in range(1, 5):
                if getattr(self, f"is_p{period}"):
                    return period
        else:
            raise Exception(f"Tried to get only_period when there were multiple periods possible {self}")

    @property
    def chosen_classroom(self):
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
    def available_classrooms(self) -> list:
        return [getattr(self, f"p{period}") for period in range(1, 5) if getattr(self, f"is_p{period}")]

    @property
    def available_periods(self) -> list:
        return [period for period in range(1, 5) if getattr(self, f"is_p{period}")]

    def semi_available_periods(self, available_classrooms, exclude_chosen_period: bool = True) -> list:
        """
        exclude_chosen_period: don't include the chosen period of the ticket (assumes it exists)
        Returns a list of periods where the period's classroom exists. Means that this ticket can be chucked into
        these classrooms without decreasing efficiency.
        """
        semi_available_periods = []
        for period in range(1, 5):
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

    def num_items(self, items: tuple) -> int:
        # returns the number of serenades (including special) in a list of tickets
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

    def filter_by_item_type(self, items: tuple):
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
    def period_distribution(self) -> dict:
        """Gets how many tickets each period has (ignores tickets which haven't been allocated yet)"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0}
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
    def grouped_by_num_periods_available(self) -> dict:
        """
        A dict grouping tickets by the number of periods that are still available to them
        \nKey: number of periods available
        \nValue: the tickets with that many periods available
        :return: Dict
        """
        cls = self.__class__
        num_periods_available_distribution = {1: cls(), 2: cls(), 3: cls(), 4: cls()}
        for ticket in self:
            num_periods_available_distribution[ticket.num_periods_available].append(ticket)
        return num_periods_available_distribution

    @property
    def grouped_by_num_periods_available_reversed(self) -> dict:
        cls = self.__class__
        num_periods_available_distribution = {4: cls(), 3: cls(), 2: cls(), 1: cls()}
        for ticket in self:
            num_periods_available_distribution[ticket.num_periods_available].append(ticket)
        return num_periods_available_distribution


class Classroom:
    # the REGEX used to determine what is a valid classroom name
    # if invalid, classroom will not be visited
    # classroom_pattern = r"[A-Z]\d{3}"
    classroom_pattern = room_format

    # Lookup dict used to substitute names when cleaning
    SUBSTITUTIONS = {
        'LIBA': 'B101',
        'LIBB': 'B102',
        'LIBC': 'B103',
        'LIBD': 'B104'
    }

    def __init__(self, original_name: str, period: int):
        """Variables"""
        self.tickets = TicketList()

        self.period = period

        self.original_name = original_name       # the name as it appears on the timetable
        self.clean_name = self.get_clean_name()
        self.extended_name = f"{self.period}-{self.clean_name}"

        self.is_valid = self.verify_classroom_name()

        self.has_been_chosen = False

    def __repr__(self):
        return self.extended_name

    def get_clean_name(self):
        if self.original_name in self.SUBSTITUTIONS:
            clean_name = self.SUBSTITUTIONS[self.original_name]
        else:
            dotless_name = self.original_name.replace('.', '')
            clean_name = re.sub("([A-Z])G", r"\g<1>0", dotless_name)
        return clean_name

    def verify_classroom_name(self):
        return re.match(self.classroom_pattern, self.clean_name) is not None

    def choose(self):
        """Make every ticket in this classroom pick this classroom"""
        for ticket in self.tickets:
            ticket.choose_classroom(self)
        self.has_been_chosen = True

    def reset(self):
        # sets the classroom as not chosen and makes every ticket think the classroom is free
        self.has_been_chosen = False
        for ticket in self.tickets:
            setattr(ticket, f"is_p{self.period}", True)

    @property
    def is_upper_campus(self):
        block = self.clean_name[0]
        return ord(block.upper()) <= ord('G')

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
                if new_classroom.is_valid:
                    if new_classroom in self:
                        existing_classroom = self.get_existing_classroom(new_classroom)
                        existing_classroom.tickets.append(ticket)
                        setattr(ticket, f"p{period}", existing_classroom)
                    else:
                        new_classroom.tickets.append(ticket)
                        setattr(ticket, f"p{period}", new_classroom)
                        self.append(new_classroom)
                else:
                    raise NameError(f"Classroom name is invalid: {new_classroom.clean_name}")
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
    def grouped_by_length(self) -> dict:
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
    def grouped_by_length_reversed(self) -> dict:
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
    def split(a, n):
        k, m = divmod(len(a), n)
        return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))

    @property
    def grouped_by_period(self) -> dict:
        """
        :return: Returns a dict with key=period and value=ClassroomList of classrooms in that period
        """
        classrooms_by_period = {1: ClassroomList(), 2: ClassroomList(), 3: ClassroomList(), 4: ClassroomList()}
        for classroom in self:
            classrooms_by_period[classroom.period].append(classroom)
        return classrooms_by_period

    @property
    def grouped_by_geography(self) -> dict:
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

    def sorted_by_period_distribution(self, tickets: TicketList):
        """
        Sorts self by order of ticket distribution (fullest first), then distribution of destroyed classes.
        Recalculates the smallest period after each yield so that modifications to the period distribution between
            yields are considered
        Tickets input is the TicketList which the period distribution is derived from (should be a list of every ticket)
        """
        classroom_copy = self.copy()
        for i in range(len(classroom_copy)):
            if len(classroom_copy) > 1:  # don't bother if only 1 class in list
                ticket_period_distribution = tickets.period_distribution
                chosen_classroom = max(classroom_copy,
                                       key=lambda classroom: ticket_period_distribution[classroom.period])
                classroom_copy.remove(chosen_classroom)
                yield chosen_classroom
            else:
                yield classroom_copy[0]

    def sorted_by_eliminated_period_distribution_then_length(self, period_distribution: dict):
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

    def get_existing_person(self, new_person: Person):
        # gets an existing person in the list, given a new Person object with the same name
        for existing_person in self:
            if existing_person.id == new_person.id:
                return existing_person
        raise KeyError("Person not found")

    def with_x_num_tickets(self, num_tickets: int) -> dict:
        # filters the list to only be people with the specified number of tickets
        people_with_x_num_tickets = {}
        for person in self:
            if len(self[person]) == num_tickets:
                people_with_x_num_tickets[person] = self[person]
        return people_with_x_num_tickets

    def grouped_by_num_items(self, items: tuple, reverse: bool = True) -> dict:
        """
        Groups people with x number of items of specified type
        Key: number of items of the specified type
        Value: list of people with that number of items of specified type
        Also sorted by ascending order (can be reversed to descending)
        """
        people_grouped_by_num_items = {}
        for person in self:
            num_items = person.num_items(items)
            if num_items in people_grouped_by_num_items:
                people_grouped_by_num_items[num_items].append(person)
            else:
                people_grouped_by_num_items[num_items] = [person]
        people_grouped_by_num_items = {num_items: people_grouped_by_num_items[num_items]
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
    def split(a, n):
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
    def fullest_group(self):
        if len(self) > 1:
            return max(self, key=lambda group: len(group.tickets))
        elif len(self) == 1:
            return self[0]
        else:
            raise KeyError("Cannot return max of blank.")

    @property
    def emptiest_group(self):
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

        # first pass with only serenades
        self.tickets = self.all_tickets.filter_serenades
        self.classrooms = ClassroomList.from_tickets(self.tickets)
        self.initialise_special_serenades()
        self.make_special_serenades_extra_special()
        self.distribute_tickets(("Serenade",))
        if not self.ENFORCE_DISTRIBUTION:
            self.eliminate_classrooms(True)

        # second pass with all item types
        self.classrooms = ClassroomList.from_tickets(self.all_tickets, self.tickets)
        self.tickets = self.all_tickets
        # self.distribute_tickets(("Chocolate", "Rose"))        # optional. massively decreases efficiency (~2x)
        self.eliminate_classrooms(False)

        self.assign_tickets_to_groups()
        self.print_statistics()

    def initialise_special_serenades(self):
        for ticket in self.tickets:
            if ticket.item_type == "Special Serenade":
                ticket.choose_period(ticket.ss_period)

    def make_special_serenades_extra_special(self):
        # removes regular serenades from classrooms that have special serenades
        for ticket in self.tickets:
            if ticket.item_type == "Special Serenade":
                classroom = getattr(ticket, f"p{ticket.chosen_period}")
                for other_ticket in classroom.tickets:
                    if other_ticket.item_type == "Serenade":
                        if not other_ticket.has_no_choice:
                            setattr(other_ticket, f"is_p{ticket.chosen_period}", False)
                            classroom.tickets.remove(other_ticket)

    def distribute_tickets(self, items: tuple):
        """
        Distributes each person's tickets so that they receive them all over many periods instead of all at once
        :param items: Only tickets of these item types are considered
        :return: NONE
        """
        period_distribution = self.tickets.period_distribution
        item_period_distribution = {1: 0, 2: 0, 3: 0, 4: 0}
        for num_tickets, people in People(self.tickets).grouped_by_num_items(items).items():
            # num_tickets is the number of total tickets the person has
            if num_tickets > 0:
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
                            if 1 < num_periods_available <= num_tickets:
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
        eliminated_period_distribution = {1: 0, 2: 0, 3: 0, 4: 0}
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

    def assign_tickets_to_groups(self):
        self.output_serenading_groups = \
            DeliveryGroupList([DeliveryGroup(i + 1, True) for i in range(self.NUM_SERENADING_GROUPS)])
        self.output_non_serenading_groups = \
            DeliveryGroupList([DeliveryGroup(i + 1, False) for i in range(self.NUM_NON_SERENADING_GROUPS)])

        for period, classrooms_in_period in self.classrooms.grouped_by_period.items():
            serenade_classes = classrooms_in_period.filter_has_serenades
            no_serenade_classes = classrooms_in_period.filter_has_no_serenades

            serenading_period_groups = self.get_period_groups(serenade_classes, True)
            self.output_serenading_groups.update(serenading_period_groups, period)

            non_serenading_period_groups = self.get_period_groups(no_serenade_classes, False)
            self.output_non_serenading_groups.update(non_serenading_period_groups, period)

    def get_period_groups(self, classrooms: ClassroomList, is_serenading_group: bool):
        num_groups = self.NUM_SERENADING_GROUPS if is_serenading_group else self.NUM_NON_SERENADING_GROUPS
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
        total = 0
        for size, classrooms in self.classrooms.grouped_by_length.items():
            print(f"\t{size}: {len(classrooms)}\t{'|' * len(classrooms)}")
            total += size * len(classrooms)
        average_classroom_size = round(total / len(self.classrooms), 3)
        print(f"Average: {average_classroom_size}")

        print("\nTickets per serenading group:")
        for group in self.output_serenading_groups:
            print(f"\tClassrooms: {group.num_classrooms} \t| "
                  f"Serenades: {group.tickets.num_serenades}\t+ Non-serenades: {group.tickets.num_non_serenades} "
                  f"= Total: {group.tickets.num_serenades + group.tickets.num_non_serenades}")

        print("\nTickets per non-serenading group:")
        for group in self.output_non_serenading_groups:
            print(f"\tClassrooms: {group.num_classrooms} \t| Non-serenades: {group.tickets.num_non_serenades}")


def load_tickets() -> dict:
    tickets_data = {}
    with open(f"{DirectoryLocations.STUDENT_DATA}/tickets.csv") as file:
        reader = csv.reader(file)
        for index, line in enumerate(reader):
            recipient_id = line[0]
            if line[1] == "1":
                item_type = "Chocolate"
            elif line[2] == "1":
                item_type = "Rose"
            elif line[3] == "1":
                if random.random() < 0.70:
                    item_type = "Serenade"
                else:
                    item_type = "Special Serenade"
            if item_type == "Special Serenade":
                period = random.choice([1, 2, 3, 4])
            else:
                period = ""
            tickets_data[index] = {"Recipient ID": recipient_id, "Item Type": item_type, "Period": period}
    return tickets_data


def create_tickets(tickets_data: dict):
    tickets = []
    for ticket_number, values in tickets_data.items():
        recipient_id = values['Recipient ID']
        recipient_classes = STUDENTS[recipient_id]
        item_type = values['Item Type']
        ticket = TicketToSort(ticket_number, recipient_id, item_type, recipient_classes['P1'],
                              recipient_classes['P2'], recipient_classes['P3'], recipient_classes['P4'],
                              ss_period=values['Period'])
        tickets.append(ticket)
    return tickets


def main():
    # load data
    tickets_data = load_tickets()
    tickets = create_tickets(tickets_data)

    ticket_sorter = TicketSorter(tickets, 10, 10,
                                 max_serenades_per_class=2, max_non_serenades_per_serenading_class=3,
                                 extra_special_serenades=True, enforce_distribution=True)
    print("Done")


if __name__ == "__main__":
    main()
