import csv
import math
import operator
import re

print("//===================================================================//")
print("//                                                                   //")
print("// BSHS PREFECTS                                                     //")
print("// CUPID  v0.1.0                                                     //")
print("//                                                                   //")
print("// legend has it that saint valentine himself wrote this program     //")
print("//                                                                   //")
'''
print("// see README.txt for instructions                                   //")
# TODO: readme
print("// if it wasn't there before, it is now                              //")
print("//                                                                   //")
'''
print("//===================================================================//")
print("")

print("  # INPUT REQUIRED")
num_groups_can_serenade = int(input("    How many groups can serenade?    "))
num_groups_cant_serenade = int(input("    How many groups can't serenade?  "))
total_num_groups = num_groups_can_serenade + num_groups_cant_serenade
print("    " + str(total_num_groups) + " total groups")
print("")

students = dict()
tickets = list()

# this could eventually need updating
# room_name_format = '[A-Z]\d\d\d'
room_name_format = r"[A-Z][G\d].?[\d]{1,2}\Z|LIB[A-D]Y?\Z|OVAL[A-D]\Z|OVLJ\Z|POOL\Z"

period_one_room_names = set()
period_two_room_names = set()
period_three_room_names = set()
period_four_room_names = set()

print("  # INPUT")

print("    Attempting to read ./students.csv . . .")
with open('people.csv', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        students[row['ID']] = row
print("    Success!", len(students), 'students loaded')

print("    Attempting to read ./tickets.csv . . .")
with open('tickets.csv', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        s_id = row['ID']
        if s_id == '':
            continue
        row['StudentName'] = students[s_id]['Name']
        row['Period1Room'] = students[s_id]['P1']
        row['Period2Room'] = students[s_id]['P2']
        row['Period3Room'] = students[s_id]['P3']
        row['Period4Room'] = students[s_id]['P4']

        # get all distinct rooms that are potentially valid for each period
        if re.fullmatch(room_name_format, row['Period1Room']) is not None:
            period_one_room_names.add(row['Period1Room'])
        if re.fullmatch(room_name_format, row['Period2Room']) is not None:
            period_two_room_names.add(row['Period2Room'])
        if re.fullmatch(room_name_format, row['Period3Room']) is not None:
            period_three_room_names.add(row['Period3Room'])
        if re.fullmatch(room_name_format, row['Period4Room']) is not None:
            period_four_room_names.add(row['Period4Room'])

        # add to list
        tickets.append(row)
print("    Success!", len(tickets), 'tickets loaded')

print("")

periods = 1, 2, 3, 4
period_room_costs = dict(), dict(), dict(), dict()
period_room_serenade_count = dict(), dict(), dict(), dict()
period_room_item_count = dict(), dict(), dict(), dict()

for room_name in period_one_room_names:
    period_room_costs[0][room_name] = 0
    period_room_serenade_count[0][room_name] = 0
    period_room_item_count[0][room_name] = 0

for room_name in period_two_room_names:
    period_room_costs[1][room_name] = 0
    period_room_serenade_count[1][room_name] = 0
    period_room_item_count[1][room_name] = 0

for room_name in period_three_room_names:
    period_room_costs[2][room_name] = 0
    period_room_serenade_count[2][room_name] = 0
    period_room_item_count[2][room_name] = 0

for room_name in period_four_room_names:
    period_room_costs[3][room_name] = 0
    period_room_serenade_count[3][room_name] = 0
    period_room_item_count[3][room_name] = 0

print("")


# get room for chosen period
def period_room(x):
    return {
        1: ticket['Period1Room'],
        2: ticket['Period2Room'],
        3: ticket['Period3Room'],
        4: ticket['Period4Room'],
    }.get(x, '?')


# split list into two halves
# if list has an uneven length, the first returned list will be the longest
def split_list(a_list):
    half = math.ceil(len(a_list) / 2)
    return a_list[:half], a_list[half:]


i = 0
for ticket in tickets:
    # the modulo trick
    # works best if input is ordered alphabetically by recipient
    i += 1  # for loop iterations   (i.e. current ticket number)
    j = i  # while loop iterations (i.e. attempts)
    period = 0
    # try to assign a period where we definitely know where the recipient is
    # i.e. does the room name start with a letter, followed by three numbers
    while True:
        period = (j - 1) % 4 + 1
        if re.fullmatch(room_name_format, period_room(period)) is not None:
            break
        elif j == i + 4:  # we tried four times, no dice
            period = 0
            break
        j += 1
    ticket['Period'] = period
    # print(ticket['Period'])
    ticket['PeriodRoom'] = period_room(ticket['Period'])
    # print(ticket['PeriodRoom'])

    if period == 0 or ticket['PeriodRoom'] == '?':
        del ticket
        continue

    num_Rose = int(ticket['Rose'])
    num_Chocolate = int(ticket['Chocolate'])

    period_room_serenade_count[ticket['Period'] - 1][ticket['PeriodRoom']] += \
        int(ticket['Serenade'])
    period_room_item_count[ticket['Period'] - 1][ticket['PeriodRoom']] += \
        (num_Rose + num_Chocolate)

    # ticket -> room cost function
    serenade_cost = int(ticket['Serenade']) * 7
    ticket_cost = num_Rose + num_Chocolate + serenade_cost
    period_room_costs[ticket['Period'] - 1][ticket['PeriodRoom']] += ticket_cost

# print(period_room_costs)

period_room_costs_sorted = [list(), list(), list(), list()]
period_rooms_sorted = list(), list(), list(), list()
period_blocks = set(), set(), set(), set()
period_blocks_sorted = [list(), list(), list(), list()]
period_block_rooms = dict(), dict(), dict(), dict()
period_block_room_count = dict(), dict(), dict(), dict()
period_room_count = [0, 0, 0, 0]
period_room_only_serenades = dict(), dict(), dict(), dict()

period_room_assigned_serenaders = dict(), dict(), dict(), dict()
period_room_assigned_others = dict(), dict(), dict(), dict()

# the business end...
# this is where it gets messy
for period in periods:
    period_room_costs_sorted[period - 1] = \
        sorted(period_room_costs[period - 1].items(), key=operator.itemgetter(1))

    # throw away costs because we know it's ordered from low to high cost
    # the cost itself doesn't matter, only the order
    for kvpair in period_room_costs_sorted[period - 1]:
        # also throw away rooms with a cost value of 0 (i.e. no tickets)
        if kvpair[1] > 0:
            period_rooms_sorted[period - 1].append(kvpair[0])

    # blocks
    for room in period_rooms_sorted[period - 1]:
        if period_room_item_count[period - 1][room] == 0 and \
                period_room_serenade_count[period - 1][room] > 0:
            period_room_only_serenades[period - 1][room] = True
        else:
            period_room_only_serenades[period - 1][room] = False

        period_blocks[period - 1].add(room[0])

    for block in period_blocks[period - 1]:
        period_block_rooms[period - 1][block] = list()

    for room in period_rooms_sorted[period - 1]:
        period_block_rooms[period - 1][room[0]].append(room)

    for block in period_blocks[period - 1]:
        period_block_room_count[period - 1][block] = \
            len(period_block_rooms[period - 1][block])
        period_room_count[period - 1] += \
            period_block_room_count[period - 1][block]

        # sort blocks alphabetically for geographical reasons
    period_blocks_sorted[period - 1] = sorted(period_blocks[period - 1])

    # serenaders
    last_fraction = 0
    for block in period_blocks_sorted[period - 1]:
        fraction = period_block_room_count[period - 1][block] / \
                   period_room_count[period - 1]
        minimum = last_fraction
        maximum = last_fraction + fraction
        last_fraction = maximum

        serenade_base = num_groups_can_serenade - 1

        serenade_group_range = \
            round(serenade_base * minimum) + 1, \
            round(serenade_base * maximum) + 1
        serenade_group_count = \
            serenade_group_range[1] - serenade_group_range[0] + 1

        low_cost, high_cost = split_list(period_block_rooms[period - 1][block])
        high_cost = list(reversed(high_cost))  # order high to low

        # pair off high and low cost rooms to serenading groups
        i = 0
        while i < len(low_cost):  # low cost will always be the longest list
            group_serenaders = \
                serenade_group_range[0] + (i % serenade_group_count)

            period_room_assigned_serenaders[period - 1][low_cost[i]] = \
                group_serenaders

            if not (i > len(high_cost) - 1):
                period_room_assigned_serenaders[period - 1][high_cost[i]] = \
                    group_serenaders

            i += 1

    # the other groups
    last_fraction = 0
    for block in period_blocks_sorted[period - 1]:
        fraction = period_block_room_count[period - 1][block] / \
                   period_room_count[period - 1]
        minimum = last_fraction
        maximum = last_fraction + fraction
        last_fraction = maximum

        others_base = num_groups_cant_serenade - 1

        other_group_range = \
            num_groups_can_serenade + round(others_base * minimum) + 1, \
            num_groups_can_serenade + round(others_base * maximum) + 1
        other_group_count = \
            other_group_range[1] - other_group_range[0] + 1

        low_cost, high_cost = split_list(period_block_rooms[period - 1][block])
        high_cost = list(reversed(high_cost))  # order high to low

        # now do the other groups
        i = 0  # room iterator
        j = 0  # group iterator
        while i < len(low_cost):
            group_others = \
                other_group_range[0] + (j % other_group_count)

            if not (i > len(high_cost) - 1):
                if not period_room_only_serenades[period - 1][high_cost[i]]:
                    period_room_assigned_others[period - 1][high_cost[i]] = \
                        group_others

            if not period_room_only_serenades[period - 1][low_cost[i]]:
                period_room_assigned_others[period - 1][low_cost[i]] = \
                    group_others
                j += 1

            i += 1

group_totals = dict()
i = 1
while i < total_num_groups + 1:
    group_totals[i] = 0
    i += 1

# 1st pass
print('  # 1ST PASS')
i = 0
for ticket in tickets:
    print(ticket)
    if ticket['Serenade'] == '1' or i % 3 == 0:
        ticket['GroupNumber'] = period_room_assigned_serenaders[ticket['Period'] - 1][ticket['PeriodRoom']]
    else:
        ticket['GroupNumber'] = period_room_assigned_others[ticket['Period'] - 1][ticket['PeriodRoom']]
    group_totals[ticket['GroupNumber']] += 1
    i += 1
i = 1
while i < total_num_groups + 1:
    line_ending = ''
    if i < total_num_groups:
        line_ending = ' . . .'
    print('    ' + str(group_totals[i]) + ' tickets assigned to group ' + str(i) + line_ending)
    i += 1
print('')

# csv output
print('  # OUTPUT')
print('    Attempting to write ./output.csv . . .')
with open('output.csv', 'w', newline='') as f:
    writer = csv.writer(f)

    # write header
    writer.writerow(['GroupNumber', 'Period', 'ID', 'Rose', 'Chocolate', 'Serenade', 'Room',
                     'Period1Room', 'Period2Room', 'Period3Room', 'Period4Room'])

    i = 0
    # loop through tickets
    for ticket in tickets:
        t = ticket
        writer.writerow([t['GroupNumber'], t['Period'], t['ID'], t['Rose'], t['Chocolate'], t['Serenade'],
                         t['PeriodRoom'], t['Period1Room'], t['Period2Room'], t['Period3Room'], t['Period4Room']])
        i += 1
print('    Success!', i, 'tickets written to output.csv')
print('')

"""Get number of rooms"""
rooms = []
groups = {}
for ticket in tickets:
    period = ticket['Period']
    chosen_room = str(period) + ticket[f"Period{period}Room"]
    if chosen_room not in rooms:
        rooms.append(chosen_room)

    group = int(ticket['GroupNumber'])
    if ticket['Serenade'] == "1":
        item_type = "Serenade"
    elif ticket['Rose'] == "1" or ticket['Chocolate'] == "1":
        item_type = "Non-Serenade"

    if group not in groups:
        groups[group] = {"Serenade": 0, "Non-Serenade": 0}
    else:
        groups[group][item_type] += 1

groups = {num: groups[num] for num in sorted(groups.keys())}

print(len(rooms))

for group_num, items in groups.items():
    print(f"{group_num}: {items['Serenade']} Serenades + {items['Non-Serenade']} non-serenades")

# ADDED
chosen_classrooms = []
for ticket in tickets:
    classroom = f"{ticket['Period']}-{ticket['PeriodRoom']}"
    if classroom not in chosen_classrooms:
        chosen_classrooms.append(classroom)
print(len(chosen_classrooms), chosen_classrooms)

input("    Press enter to exit . . . ")
