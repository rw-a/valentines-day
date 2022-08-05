from .class_lookup import get_classes_lookup, STUDENTS
import random
import re
import csv
from itertools import groupby


def convert_tickets(tickets) -> list:
    # converts: tickets -> tickets_to_sort
    # tickets: list of tickets following the SQL Ticket class in model.py
    # tickets_to_sort: list of tickets following the TicketToSort class in sort_tickets.py
    classes_lookup = get_classes_lookup()
    tickets_to_sort = []
    for ticket in tickets:
        recipient_id = ticket.recipient_id
        p1 = classes_lookup[ticket.recipient_id][0]
        p2 = classes_lookup[ticket.recipient_id][1]
        p3 = classes_lookup[ticket.recipient_id][2]
        p4 = classes_lookup[ticket.recipient_id][3]
        ticket_to_sort = TicketToSort(recipient_id, ticket.item_type, p1, p2, p3, p4)
        if ticket.item_type == "Special Serenade":
            ticket_to_sort.choose_period(ticket.period)
        tickets_to_sort.append(ticket_to_sort)
    return tickets_to_sort


def sort_tickets(tickets: list, num_serenading_groups: int, num_non_serenading_groups: int,
                 max_serenades_per_class: int, max_non_serenades_per_serenading_class: int,
                 extra_special_serenades: bool) -> dict:
    # input in argument: tickets = Ticket.objects.all()
    tickets_to_sort = convert_tickets(tickets)
    ticket_sorter = TicketSorter(tickets_to_sort, num_serenading_groups, num_non_serenading_groups,
                                 max_serenades_per_class, max_non_serenades_per_serenading_class,
                                 extra_special_serenades)
    # groups = {"Serenaders": ticket_sorter.output_serenading_groups_tickets,
    #           "Non-Serenaders": ticket_sorter.output_non_serenading_groups_tickets}
    groups = {True: ticket_sorter.output_serenading_groups_tickets,
              False: ticket_sorter.output_non_serenading_groups_tickets}
    return groups


class TicketToSort:
    def __init__(self, recipient_id, item_type: str, p1: str, p2: str, p3: str, p4: str):
        # ticket info
        self.recipient_id = recipient_id
        self.item_type = item_type

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

        if self.recipient_id is None:
            self.recipient_id = f"<{self.recipient_nickname}: {self.p1} {self.p2} {self.p3} {self.p4}>"

    @property
    def chosen_period(self) -> int:
        # if a ticket only has 1 period it can go to, return what it is
        if self.has_no_choice():
            for period in range(1, 5):
                if getattr(self, f"is_p{period}"):
                    return period
        else:
            raise Exception(f"Tried to get only_period when there were multiple periods possible {self}")

    @property
    def chosen_classroom(self):
        if self.has_no_choice():
            return getattr(self, f"p{self.chosen_period}")

    def choose_period(self, chosen_period: int):  # takes period as a number (1, 2, 3, 4) not as p1, p2, p3, p4
        for period in range(1, 5):  # generates 1, 2, 3, 4 (corresponding to period numbers)
            if period is not chosen_period:  # set every period to false except the chosen one
                setattr(self, f'is_p{period}', False)
        setattr(self, f'is_p{chosen_period}', True)  # sets chosen period as true

    def has_no_choice(self) -> bool:
        has_one_choice = False
        for period in range(1, 5):
            if getattr(self, f'is_p{period}'):
                if has_one_choice:
                    return False
                else:
                    has_one_choice = True
        return True

    def __repr__(self):
        # for dev purposes only
        p1 = '' if self.is_p1 else '\''
        p2 = '' if self.is_p2 else '\''
        p3 = '' if self.is_p3 else '\''
        p4 = '' if self.is_p4 else '\''
        special = "SS" if self.item_type == "Special Serenade" else self.item_type[0]
        # return f"<{self.recipient_nickname}: {self.p1}{p1} {self.p2}{p2} {self.p3}{p3} {self.p4}{p4} {special}>"
        return f"<{self.chosen_period}-{self.chosen_classroom} {special}>"


class ClassroomNameProcessor:
    def __init__(self):
        # the REGEX used to determine what is a valid classroom name
        # if invalid, classroom will not be visited
        self.classroom_pattern = r"[A-Z]\d{3}"

        """Note: these two dicts have their key/value the other way for original/new"""
        # Dictionary with original name as key and new name as value
        self.ORIGINAL_TO_NEW = {
            'LIBA': 'B101',
            'LIBB': 'B102',
            'LIBC': 'B103',
            'LIBD': 'B104'
        }

        # Dictionary with new name as key and original as value
        self.lookup = {}

    def get_new_name(self, original_name: str, period: int):
        if original_name in self.ORIGINAL_TO_NEW:
            new_name = self.ORIGINAL_TO_NEW[original_name]
        else:
            new_name = original_name.replace('.', '')
            new_name = re.sub("([A-Z])G", r"\g<1>0", new_name)

        self.lookup[new_name] = original_name  # adds it to the dict so that it's easier to go back

        return f"{period}-{new_name}"  # add the period prefix (very important)

    def is_accepted_classroom(self, classroom_name: str) -> bool:
        if re.match(rf"\d-{self.classroom_pattern}", classroom_name) is not None:
            return True
        else:
            print(f"{classroom_name} has been rejected.")
            return False

    def get_original_name(self, new_name: str):
        new_name = new_name[2:]  # remove the period_prefix
        original_name = self.lookup[new_name]  # use lookup to find original name
        return original_name


class TicketSorter:
    def __init__(self, tickets: list, serenading_groups: int, non_serenading_groups: int,
                 max_serenades_per_class: int = 5, max_non_serenades_per_serenading_class: int = 10,
                 extra_special_serenades: bool = True):
        """Options"""
        # if true, special serenades will not be grouped with regular serenades (ignores non-serenades)
        # if true, more classes need to be visited (not significantly) but periods are more evenly distributed (usually)
        # not guaranteed. sometimes there is no choice
        self.EXTRA_SPECIAL_SERENADES = extra_special_serenades

        # increasing these values increases the efficiency (decreases class visits required)
        # however, too a high a value make class visits fat (more than 20 items to hand out per class)
        # the max number of serenades in a class (ignores non-serenades)
        self.MAX_SERENADES_PER_CLASS = max_serenades_per_class

        # the max number of non-serenade items in a class (only for classes with at least one serenade)
        # if too much work for serenading groups, and not enough for non-serenading groups decrease this number
        # and vice versa
        self.MAX_NON_SERENADES_PER_SERENADING_CLASS = max_non_serenades_per_serenading_class

        """Constants"""
        # these two are mutually exclusive (you cannot be both a serenading group AND a non-serenading group)
        self.NUM_SERENADING_GROUPS = serenading_groups  # the number of serenading groups
        self.NUM_NON_SERENADING_GROUPS = non_serenading_groups  # the number of groups which are NOT serenading

        # the ASCII code corresponding to the letter G
        # letters before this will be considered UPPER CAMPUS, and the other letters LOWER CAMPUS
        # i.e. G block is upper campus but H block is lower campus
        self.LAST_UPPER_CAMPUS_BLOCK_ASCII_CODE = ord('G')

        """Variables"""
        # List of every ticket
        self.tickets = tickets
        # Key: every classroom separate by the period (e.g. 1-I1.17)
        # Value: a list of every Ticket object in that classroom
        self.classrooms = {}
        # tickets which have been moved in self.distribute_doubleups()
        # keeps track to prevent them from being moved again in self.balance_periods()
        self.distributed_tickets = []

        """Output"""
        # a list where each element represents a group
        # each group is a list of tickets in order
        self.output_serenading_groups_tickets = []
        self.output_non_serenading_groups_tickets = []

        """Utility"""
        # Used to convert between new and original names
        self.classroom_name_processor = ClassroomNameProcessor()

        """Methods"""
        # Critical methods must be kept or else the algorithm will fail
        # Important methods improve the algorithm but you could live without them
        # Recommended methods don't have a meaningful impact but are nice to have
        # Optional methods usually reduce efficiency but make it better for the recipients and delivery groups
        # You may turn off optional methods if you wish to improve efficiency
        self.pre_process_classroom_names()                      # important
        self.get_all_classrooms()                               # critical
        if self.EXTRA_SPECIAL_SERENADES:
            self.make_special_serenades_extra_special()         # optional
        self.limit_serenades_per_class()                        # optional
        self.limit_non_serenades_per_serenading_class()         # optional
        self.eliminate_classrooms()                             # critical
        self.distribute_doubleups()                             # optional
        self.balance_periods()                                  # optional
        self.assign_tickets_to_groups()                         # important
        self.post_process_classroom_names()                     # recommended

        """
        How the algorithm works
        1. Assume that classes in different periods are just completely different classes
           (i.e. flatten temporal dimension into spatial dimension)
        2. Assume that every person is at all four of their classes at once (at every period simultaneously)
        3. Sort the classes by the number of tickets in that class
        4. For each class, starting from those with the least tickets, do one of two things:
           LOCK: If there is a ticket in this class that has no other choice (e.g. special serenade), it must be 
                 visited. Therefore, every other ticket in that class should stay there. Delete every other class for 
                 these people.
           DELETE: If there is a class where everyone inside could be in a different class, delete this classroom and
                   move on.
        5. As step 4 continues for more classes, the number of choices decreases until everyone is only at one class.
        
        Note: There are also additional steps like limiting serenades per class, enabling extra special serenades and 
            period balancing
        
        
        Strengths:
        -Minimises the number of class visits required
        -Each class is interrupted max 1 time per period
        -Fairly even distribution of items between periods (<5% disparity between emptiest and fullest period)
        
        Weaknesses:
        -For people who receive multiple items, about 40% receive all of them at once, 
            and about 50% receive them across 2 periods.
        -Each class visit is very big, averaging about 6 items per class
        -Most of the handing out is done by serenading groups
        
        Note: numbers were based on 2022 practice dataset of 931 tickets
        
        Possible Future Improvements:
        -limit_serenades_per_class, limit_non_serenades_per_serenading_class, and balance_periods are arbitrary in the
            order that they go through the tickets. this could be made less intelligent by doing it in an order which
            ensures a more balanced distribution or more efficiency
        -the additional steps (distribute_doubleups, limit_serenades_per_class, 
            limit_non_serenades_per_serenading_class, and balance_periods) are all done separately and could be more 
            efficient if a more holistic approach is used, which lets them communicate which each other
        """

    @property
    def classrooms_sorted_by_length(self):
        return sorted(self.classrooms.keys(), key=lambda classroom: len(self.classrooms[classroom]))

    @property
    def classrooms_grouped_by_length(self) -> dict:
        """
        Key: number of tickets in a given classroom
        Value: list of classrooms with that many tickets
        E.g. {0: ["1-A204", "3-I115"], 1: ["1-F101", "2-G101"]}

        Note:
            this is a getter function, so it will re-evaluate everytime it is called
            this is less efficient, but it means only self.classrooms needs to be updated
        """
        classrooms_by_length = {}
        for classroom, tickets in self.classrooms.items():
            length = len(tickets)
            if length in classrooms_by_length:
                classrooms_by_length[length].append(classroom)
            else:
                classrooms_by_length[length] = [classroom]
        return classrooms_by_length

    def pre_process_classroom_names(self):
        """
        See the class: ClassroomNameProcessor
        Changes classroom names to something more manageable
        Classroom names that aren't recognised by ClassroomNameProcessor will be disabled
        Adds the period number as a prefix to the classrooms
        E.g. F101 -> 1-F101
        E.g. LIBA -> 4-B101
        """
        for ticket in self.tickets:
            for period in range(1, 5):
                name = getattr(ticket, f'p{period}')
                name = self.classroom_name_processor.get_new_name(name, period)
                setattr(ticket, f'p{period}', name)

                # if it doesn't recognise the classroom name, even after it has been changed, it disables it (e.g. OVAL)
                if not self.classroom_name_processor.is_accepted_classroom(name):
                    setattr(ticket, f'is_p{period}', False)

    def get_all_classrooms(self):
        """
        Goes through every ticket and adds its classrooms to a dict
        Key: classroom_name
        Value: list of tickets that have that classroom
        E.g. {"1-F101": [TICKET, TICKET, TICKET]}
        """
        # first sort the tickets by the recipient's ID
        # self.tickets.sort(key=lambda a: a.recipient_id)

        for ticket in self.tickets:
            for period in range(1, 5):
                is_period = getattr(ticket, f'is_p{period}')
                classroom = getattr(ticket, f'p{period}')
                if is_period:
                    if classroom not in self.classrooms:
                        self.classrooms[classroom] = [ticket]
                    else:
                        self.classrooms[classroom].append(ticket)
                else:
                    if classroom not in self.classrooms:
                        self.classrooms[classroom] = []

    def make_special_serenades_extra_special(self):
        # ensures that special serenades are not grouped with regular serenades
        for ticket in self.tickets:
            if ticket.item_type == "Special Serenade":
                classroom = getattr(ticket, f"p{ticket.chosen_period}")
                for other_ticket in self.classrooms[classroom][:]:
                    if other_ticket.item_type == "Serenade":
                        if not other_ticket.has_no_choice():
                            setattr(other_ticket, f"is_p{ticket.chosen_period}", False)
                            self.classrooms[classroom].remove(other_ticket)
                        else:
                            # print(f"{ticket.recipient} cannot have an extra special serenade :(")
                            pass

    def limit_serenades_per_class(self):
        # ensures that each class doesn't have more than x number of serenades
        classrooms = reversed(self.classrooms_sorted_by_length)
        for classroom in classrooms:
            period = int(classroom[0])
            tickets = self.classrooms[classroom]
            serenade_count = self.items_per_classroom(tickets, ['Serenade', 'Special Serenade'])
            if serenade_count > self.MAX_SERENADES_PER_CLASS:
                for ticket in tickets:
                    if ticket.item_type == "Serenade":
                        if not ticket.has_no_choice():
                            setattr(ticket, f"is_p{period}", False)
                            self.classrooms[classroom].remove(ticket)
                            serenade_count -= 1
                            if serenade_count <= self.MAX_SERENADES_PER_CLASS:
                                break

    def limit_non_serenades_per_serenading_class(self):
        # only happens if a class has serenades (unlimited non-serenades per class for non-serenading groups)
        # limits the number of non-serenading items in these classes
        classrooms = reversed(self.classrooms_sorted_by_length)
        for classroom in classrooms:
            period = int(classroom[0])
            tickets = self.classrooms[classroom]
            if self.has_item_type(tickets, ['Serenade', 'Special Serenade']):
                non_serenade_count = self.items_per_classroom(tickets, ['Chocolate', 'Rose'])
                if non_serenade_count > self.MAX_NON_SERENADES_PER_SERENADING_CLASS:
                    for ticket in tickets:
                        if ticket.item_type in ['Chocolate', 'Rose']:
                            if not ticket.has_no_choice():
                                setattr(ticket, f"is_p{period}", False)
                                self.classrooms[classroom].remove(ticket)
                                non_serenade_count -= 1
                                if non_serenade_count <= self.MAX_NON_SERENADES_PER_SERENADING_CLASS:
                                    break

    @staticmethod
    def items_per_classroom(tickets: list, items: list) -> int:
        # returns the number of serenades (including special) in a list of tickets
        count = 0
        for ticket in tickets:
            if ticket.item_type in items:
                count += 1
        return count

    def eliminate_classrooms(self):
        for length, classrooms in self.classrooms_grouped_by_length.items():
            # ensures that if classrooms have equal length, the classrooms in full periods are removed first
            classrooms_sorted_by_period_serenades = \
                sorted(classrooms,
                       key=lambda class_room: self.get_items_per_period(['Serenade', 'Special Serenade'])
                       [int(class_room[0])], reverse=True)

            # systematically removes tickets from classes, starting from the emptiest classes first
            for classroom in classrooms_sorted_by_period_serenades:
                period = int(classroom[0])
                tickets = self.classrooms[classroom]

                # determines if at least one ticket in this class must be at this classroom
                must_keep_classroom = self.must_keep_classroom(tickets)

                if must_keep_classroom:
                    # if classroom must be kept, make every other ticket stay in this class
                    for ticket in tickets:
                        ticket.choose_period(period)
                        self.choose_classroom(ticket, classroom)
                else:
                    # if classroom can be destroyed, remove tickets associated with it
                    # (destroy the actual classroom later)
                    for ticket in tickets[:]:
                        setattr(ticket, f'is_p{period}', False)
                        tickets.remove(ticket)

        self.cleanup_classrooms()

    def choose_classroom(self, ticket: TicketToSort, chosen_classroom: str):
        for period in range(1, 5):
            classroom = getattr(ticket, f"p{period}")
            if classroom != chosen_classroom:
                if ticket in self.classrooms[classroom]:
                    self.classrooms[classroom].remove(ticket)

    @staticmethod
    def must_keep_classroom(tickets: list) -> bool:  # takes a list of tickets and determines if any has no other choice
        for ticket in tickets:
            if ticket.has_no_choice():
                return True
        return False

    def cleanup_classrooms(self):
        # delete empty classrooms from the dict
        for classroom in self.classrooms_sorted_by_length[:]:
            if len(self.classrooms[classroom]) < 1:
                del (self.classrooms[classroom])

    def sort_tickets_within_classroom_by_person(self):
        # ensures that within a classroom, the tickets are sorted
        # sorts by person, then by item type if same person
        for tickets in self.classrooms.values():
            # sort by person, then item type if same person
            tickets.sort(key=lambda a: a.item_type)
            tickets.sort(key=lambda a: a.recipient_id)

    def distribute_doubleups(self):
        # if a person is getting multiple things at once,
        # try to distribute their items WITHOUT increasing the number of classrooms to visit

        self.sort_tickets_within_classroom_by_person()
        for classroom in self.classrooms_sorted_by_length:
            tickets = self.classrooms[classroom]
            # group tickets based on the person
            # requires that the tickets be in order first (tickets of the same people are consecutive)
            for person, same_person in groupby(tickets, lambda a: a.recipient_id):
                tickets_of_same_person = list(same_person)
                if len(tickets_of_same_person) > 1:  # if someone is receiving more than 1 ticket
                    # group the person's tickets based on their item type
                    tickets_of_same_person.sort(key=lambda a: a.item_type)
                    # get all the possible classrooms that the person could be at
                    possible_classrooms = self.get_possible_classrooms(tickets_of_same_person[0])

                    # if there are valid alternative classrooms, move some tickets there
                    if len(possible_classrooms) > 1:
                        for ticket_num, ticket in enumerate(tickets_of_same_person):
                            # loops through the possible classrooms and evenly distributes among them
                            original_classroom = ticket.chosen_classroom
                            chosen_classroom = possible_classrooms[(ticket_num % len(possible_classrooms))]
                            if chosen_classroom != original_classroom:  # if not the same class
                                # change the period of the ticket
                                chosen_period = int(chosen_classroom[0])
                                ticket.choose_period(chosen_period)
                                # change the class of the ticket
                                self.classrooms[chosen_classroom].append(ticket)
                                self.classrooms[original_classroom].remove(ticket)
                                self.distributed_tickets.append(ticket)
                                # print(f"Distributed {ticket} from {original_classroom} to {chosen_classroom}")
        # do this again because distributing probs messed it up
        self.sort_tickets_within_classroom_by_person()

    def get_possible_classrooms(self, ticket: TicketToSort):
        # gets all the classrooms that the ticket has that are also still available (haven't been deleted)
        possible_classrooms = []
        for period in range(1, 5):
            possible_classroom = getattr(ticket, f"p{period}")
            if possible_classroom in self.classrooms_sorted_by_length:
                possible_classrooms.append(possible_classroom)
        # random.shuffle(possible_classrooms)
        return possible_classrooms

    def get_items_per_period(self, items=None):
        """
        Gets the number of a given item per period
        E.g. items = ["Serenades", "Special Serenades"] and function returns how many of those items per period
        Key: period
        Value: number of that given item(s)
        """
        if items is None:
            items = ['Chocolate', 'Rose', 'Serenade', 'Special Serenade']  # default to all of them

        items_per_period = {1: 0, 2: 0, 3: 0, 4: 0}
        for classroom, tickets in self.classrooms.items():
            period = int(classroom[0])
            for ticket in tickets:
                if ticket.item_type in items:
                    items_per_period[period] += 1
        # sorts in ascending order
        items_per_period = {period: items_per_period[period] for period in
                            sorted(items_per_period.keys(), key=lambda a: items_per_period[a])}
        return items_per_period

    def balance_periods(self):
        # first balance by serenades
        items = ['Serenade', 'Special Serenade']
        while True:
            original_period_sizes = self.get_items_per_period(items)
            self.balance_periods_by_items(items, items)
            new_period_sizes = self.get_items_per_period(items)
            # repeat until there is no change
            if original_period_sizes == new_period_sizes:
                break

        # do the same but for non-serenades
        items = ['Chocolate', 'Rose', 'Serenade', 'Special Serenade']
        while True:
            original_period_sizes = self.get_items_per_period(items)
            self.balance_periods_by_items(['Chocolate', 'Rose'], items)
            new_period_sizes = self.get_items_per_period(items)
            # print(original_period_sizes)
            # repeat until there is no change
            if original_period_sizes == new_period_sizes:
                break

        self.sort_tickets_within_classroom_by_person()

    def balance_periods_by_items(self, items_to_move: list, items_to_count: list):
        # items to move: which items can be moved
        # items to count: which items are considered when determining the fullest period
        period_sizes = self.get_items_per_period(items_to_count)
        # reversed so people are moved from the fullest classes first
        classrooms_sorted = reversed(self.classrooms_sorted_by_length)

        # fix the disparity
        for classroom in classrooms_sorted:
            # calculate how much disparity there is between periods, and break if there is none
            period_sizes = self.get_items_per_period(items_to_count)
            fullest_period = max(period_sizes, key=lambda a: period_sizes[a])
            emptiest_period = min(period_sizes, key=lambda a: period_sizes[a])
            difference = period_sizes[fullest_period] - period_sizes[emptiest_period]
            if difference <= 1:
                break

            emptier_periods = []
            for period, period_size in period_sizes.items():
                if period_size < period_sizes[fullest_period]:
                    emptier_periods.append(period)

            fullest_periods = []
            for period, period_size in period_sizes.items():
                if period_size >= period_sizes[fullest_period]:
                    fullest_periods.append(period)

            period = int(classroom[0])
            if period in fullest_periods:
                # if the fullest period, take from that one, otherwise don't
                tickets = self.classrooms[classroom]
                for ticket in tickets:  # for every ticket that is in the fullest period
                    if ticket.item_type in items_to_move:  # if ticket is specified item
                        if ticket not in self.distributed_tickets:  # don't touch already moved tickets
                            # if the ticket can be moved
                            possible_classrooms = self.get_possible_classrooms(ticket)
                            if len(possible_classrooms) > 1:
                                # get a list of possible periods the ticket could be moved to (Um9iIDIwMjI=)
                                possible_periods = {int(a[0]): a for a in possible_classrooms}
                                # try moving the ticket to the emptiest periods first
                                for emptier_period in emptier_periods:
                                    if emptier_period in possible_periods:
                                        new_classroom = possible_periods[emptier_period]

                                        if self.EXTRA_SPECIAL_SERENADES and \
                                                ticket.item_type == "Serenade" and self.has_item_type(
                                                self.classrooms[new_classroom], ['Special Serenade']):
                                            continue   # don't allow serenades to be moved into special serenade classes

                                        # move the ticket
                                        original_classroom = ticket.chosen_classroom
                                        ticket.choose_period(emptier_period)
                                        self.classrooms[original_classroom].remove(ticket)
                                        self.classrooms[new_classroom].append(ticket)
                                        # print(f"Moved {ticket} from {original_classroom} to {new_classroom}")
                                        break
                    if not self.is_biggest_period(fullest_period, items_to_count):
                        break

        self.cleanup_classrooms()

    def is_biggest_period(self, biggest_period: int, items: list = None) -> bool:
        # determines if the given period has more items than every other period

        # items defines which items are counted when determining the biggest period
        if items is None:
            items = ['Chocolate', 'Rose', 'Serenade', 'Special Serenade']

        period_sizes = self.get_items_per_period(items)
        for period in period_sizes:
            if period != biggest_period:
                if period_sizes[period] >= period_sizes[biggest_period]:
                    return False
        return True

    def assign_tickets_to_groups(self):  # sort by special serenades, then alphabetically
        # sort by whether a class has any serenades or not
        classrooms_sorted_by_has_serenade = \
            sorted(self.classrooms_sorted_by_length,
                   key=lambda class_room: not self.has_item_type(self.classrooms[class_room]))

        # keeps track of at what point the serenades stop
        no_serenade_index = 0
        for classroom in classrooms_sorted_by_has_serenade:
            if not self.has_item_type(self.classrooms[classroom], ['Serenade', 'Special Serenade']):
                break
            no_serenade_index += 1

        # Divides the classrooms into categories: whether a classroom has serenades or not
        classrooms_with_serenades = classrooms_sorted_by_has_serenade[:no_serenade_index]
        classrooms_without_serenades = classrooms_sorted_by_has_serenade[no_serenade_index:]
        serenading_groups_per_period = self.get_distributed_classrooms_by_period(classrooms_with_serenades, True)
        non_serenading_groups_per_period = \
            self.get_distributed_classrooms_by_period(classrooms_without_serenades, False)

        # gives each group a set of classrooms from each period
        self.output_serenading_groups_tickets = \
            self.assign_tickets_to_groups_by_period(serenading_groups_per_period, self.NUM_SERENADING_GROUPS)
        self.output_non_serenading_groups_tickets = \
            self.assign_tickets_to_groups_by_period(non_serenading_groups_per_period, self.NUM_NON_SERENADING_GROUPS)

    def assign_tickets_to_groups_by_period(self, groups_per_period: dict, num_groups: int):
        # assign classes to groups by randomly picking a set of classes from each period
        groups_tickets = []
        groups_classrooms = []

        # for period 1, it doesn't matter how it's chosen so just copy it over
        groups_classrooms.extend(groups_per_period[1])

        # for periods 2-4, give the emptiest group the biggest sets
        for period in range(2, 5):
            for group_index in range(num_groups):
                emptiest_existing_group = min(groups_classrooms, key=lambda a: self.get_group_size(a))
                fullest_possible_group = max(groups_per_period[period], key=lambda a: self.get_group_size(a))
                emptiest_existing_group.extend(fullest_possible_group)
                groups_per_period[period].remove(fullest_possible_group)

        # convert classrooms into tickets
        for group in groups_classrooms:
            group_tickets = []
            for classroom in group:
                group_tickets.extend([ticket for ticket in self.classrooms[classroom]])
            groups_tickets.append(group_tickets)

        return groups_tickets

    def get_distributed_classrooms_by_period(self, classrooms: list, has_serenades: bool) -> dict:
        classrooms = sorted(classrooms)
        num_groups = self.NUM_SERENADING_GROUPS if has_serenades else self.NUM_NON_SERENADING_GROUPS
        # tickets = [ticket for classroom in classrooms for ticket in self.classrooms[classroom]]

        groups_per_period = {1: [], 2: [], 3: [], 4: []}

        # for each period
        for period, (key, classrooms_in_period) in enumerate(groupby(classrooms, key=lambda classroom: classroom[0])):
            period = period + 1
            classrooms_in_period = list(classrooms_in_period)
            num_tickets_in_period = len(
                    [ticket for classroom in classrooms_in_period for ticket in self.classrooms[classroom]])

            # splits the classrooms into two groups based on if they are upper or lower campus
            upper_lower_classrooms = [list(classrooms_in_campus) for key, classrooms_in_campus in
                                      groupby(classrooms_in_period, key=lambda classroom:
                                      ord(classroom[2].upper()) > self.LAST_UPPER_CAMPUS_BLOCK_ASCII_CODE)]

            for campus, classrooms_in_campus in enumerate(upper_lower_classrooms):
                # if campus == 0, upper campus
                # if campus == 1, lower campus
                classrooms_in_campus = list(classrooms_in_campus)

                # gets the number of tickets in this campus
                num_tickets_in_campus = len(
                    [ticket for classroom in classrooms_in_campus for ticket in self.classrooms[classroom]])

                # allocates a number of groups to this campus based on the number of tickets
                num_groups_in_campus = round(num_tickets_in_campus / num_tickets_in_period * num_groups)

                groups_per_period[period].extend(self.split(classrooms_in_campus, num_groups_in_campus))

        return groups_per_period

    @staticmethod
    def split(a, n):
        k, m = divmod(len(a), n)
        return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))

    def get_group_size(self, group):
        return sum([len(self.classrooms[classroom]) for classroom in group])

    @staticmethod
    def has_item_type(tickets: list, items=None) -> bool:
        # checks if a list of tickets contains any ticket with a given item type(s)
        if items is None:
            items = ['Serenade', 'Special Serenade']

        for ticket in tickets:
            if ticket.item_type in items:
                return True
        return False

    def post_process_classroom_names(self):
        for ticket in self.tickets:
            for period in range(1, 5):
                name = getattr(ticket, f'p{period}')
                setattr(ticket, f'p{period}', self.classroom_name_processor.get_original_name(name))


def main():
    random.seed(2)
    classes = {}
    with open('students.csv') as file:
        reader = csv.reader(file)
        for line in reader:
            classes[line[0]] = {1: line[2], 2: line[3], 3: line[4], 4: line[5]}
    tickets = []
    with open('tickets.csv') as file:
        reader = csv.reader(file)
        for line in reader:
            name = line[1]
            if len(name) < 1:
                continue

            # get the item type
            items = line[3:6]
            item_type = ""
            if int(items[0]) >= 1:
                item_type = "Chocolate"
            elif int(items[1]) >= 1:
                item_type = "Rose"
            elif int(items[2]) == 1:
                item_type = "Serenade"

            ticket = TicketToSort(None, name, name, name, name, item_type,
                                  classes[name][1], classes[name][2], classes[name][3], classes[name][4])

            # randomly convert serenades to special serenades
            if random.random() < 0.02:
                ticket.item_type = "Special Serenade"
                ticket.choose_period(random.choice([1, 2, 3, 4]))

            tickets.append(ticket)

    tickets_sorted = TicketSorter(tickets, 10, 10, extra_special_serenades=False)

    for group in tickets_sorted.output_serenading_groups_tickets:
        print(group)
        print()
    print("-----------------------------\n")
    for group in tickets_sorted.output_non_serenading_groups_tickets:
        print(group)
        print()
    print(tickets_sorted.get_items_per_period(['Serenade', 'Special Serenade']))
    print(tickets_sorted.get_items_per_period(['Chocolate', 'Rose']))
    print(tickets_sorted.get_items_per_period(['Chocolate', 'Rose', 'Serenade', 'Special Serenade']))


if __name__ == "__main__":
    main()
