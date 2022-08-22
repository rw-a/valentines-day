import csv
import random
import re

"""Settings"""
name_half = r"([a-zA-Z\s\'\(\)-]+)"
name_format = fr"{name_half},\s{name_half},"
teacher_name_format = r"[A-Z 0]{5,6} - " + name_format[:-1]

normal_room_format = r"[A-Z][G\d].?[\d]{1,2}\Z"
bad_room_format = r"OVAL[A-D]\Z|OVLJ\Z|POOL\Z"    # rooms which are annoying and shouldn't be chosen
special_room_format = r"LIB[A-D]Y?\Z"             # rooms which don't follow the normal regex
room_format = normal_room_format + r"|" + special_room_format + r"|" + bad_room_format

arc_class_format = r"([7-9]|10|11|12)[A-Z]"

period_columns = 1, 3, 5, 7


def get_periods(person: dict, rows: list, row_index: int):
    row = rows[row_index]
    for period, period_column in enumerate(period_columns):
        period = period + 1
        room = re.search(room_format, row[period_column])
        if room:
            person[f"P{period}"] = room.group(0)
        else:
            # print(row[period_column])
            person[f"P{period}"] = "NONE"
            # if a person's class got split across two rows, try to find the class in the next row
            next_row = rows[row_index + 1]
            if next_row[0] == "":
                # checks if the next row is the second half of this row and not a new person
                room = re.search(room_format, next_row[period_column])
                if room:
                    person[f"P{period}"] = room.group(0)
                    # print(person)
                else:
                    # print("NO ROOM")
                    pass


def add_person(people: list, person: dict):
    if person["P1"] == "NONE" and person["P2"] == "NONE" and person["P3"] == "NONE" and person["P4"] == "NONE":
        # print(person)
        del person
    else:
        people.append(person)


def get_student_classes(files):
    people = []

    rows = []
    for file in files:
        for row in file:
            if row != ['', '', '', '', '', '', '', '', '']:
                rows.append(row)
    # print(rows)
    for row_index in range(len(rows)):
        # do a traditional for loop so that the next row can be found
        row = rows[row_index]

        name = re.match(name_format, row[0])
        if name:
            # if a student row
            student = {'First Name': name.group(2),
                       'Last Name': name.group(1),
                       'Name': f"{name.group(2)} {name.group(1)}",
                       'ARC': re.search(arc_class_format, row[0]).group(0)}
            student['ID'] = f"{student['Name']} [{student['ARC']}]"

            get_periods(student, rows, row_index)
            add_person(people, student)
        else:
            # perhaps it's a teacher instead
            name = re.match(teacher_name_format, row[0])
            if name:
                teacher = {'First Name': name.group(2),
                           'Last Name': name.group(1),
                           'Name': f"{name.group(2)} {name.group(1)}",
                           'ARC': "TEACHER"}
                teacher['ID'] = f"{teacher['Name']} [{teacher['ARC']}]"

                get_periods(teacher, rows, row_index)
                add_person(people, teacher)

    return people


def load_csvs_in_folder(folder_dir: str):
    from glob import glob
    for file_name in glob(f"{folder_dir}/*.csv"):
        with open(file_name) as file:
            yield csv.reader(file)


def main():
    from constants import DirectoryLocations, FileNames
    files = load_csvs_in_folder(DirectoryLocations.TIMETABLES_INPUT)
    students = get_student_classes(files)
    with open(FileNames.PEOPLE, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=['ID', 'Name', 'First Name', 'Last Name',
                                                  'ARC', 'P1', 'P2', 'P3', 'P4'])
        writer.writeheader()
        writer.writerows(students)


if __name__ == "__main__":
    main()
