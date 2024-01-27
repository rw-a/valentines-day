from __future__ import annotations

import csv
import re
from typing import TypedDict


"""Settings"""
NAME_HALF = r"([a-zA-Z\s\'\(\)-]+)"
NAME_FORMAT = fr"{NAME_HALF},\s{NAME_HALF},"
TEACHER_NAME_FORMAT = r"[A-Z 0]{5,6} - " + NAME_FORMAT[:-1]

NORMAL_ROOM_FORMAT = r"[A-Z][G\d].?[\d]{1,2}\Z"
BAD_ROOM_FORMAT = r"OVAL[A-D]\Z|OVLJ\Z|POOL\Z"    # rooms which are annoying and shouldn't be chosen
SPECIAL_ROOM_FORMAT = r"LIB[A-D]Y?\Z"             # rooms which don't follow the normal regex
ROOM_FORMAT = NORMAL_ROOM_FORMAT + r"|" + SPECIAL_ROOM_FORMAT + r"|" + BAD_ROOM_FORMAT

ARC_CLASS_FORMAT = r"([7-9]|10|11|12)[A-Z]"

PERIOD_COLUMNS = 1, 3, 5, 7


def get_periods(person: dict, rows: list, row_index: int):
    row = rows[row_index]
    for period, period_column in enumerate(PERIOD_COLUMNS):
        period = period + 1
        room = re.search(ROOM_FORMAT, row[period_column])
        if room:
            person[f"p{period}"] = room.group(0)
        else:
            # print(row[period_column])
            person[f"p{period}"] = None
            # if a person's class got split across two rows, try to find the class in the next row
            next_row = rows[row_index + 1]
            if next_row[0] == "":
                # checks if the next row is the second half of this row and not a new person
                room = re.search(ROOM_FORMAT, next_row[period_column])
                if room:
                    person[f"p{period}"] = room.group(0)
                    # print(person)
                else:
                    # print("NO ROOM")
                    pass


def add_person(people: list, person: dict):
    if (person["p1"] is None and person["p2"] is None
            and person["p3"] is None and person["p4"] is None):
        # print(person)
        del person
    else:
        people.append(person)


class RecipientType(TypedDict):
    first_name: str
    last_name: str
    full_name: str
    arc: str
    grade: int
    recipient_id: str
    p1: str | None
    p2: str | None
    p3: str | None
    p4: str | None


def get_recipient_classes(files) -> list[RecipientType]:
    people: list[RecipientType] = []

    rows = []
    for file in files:
        for row in file:
            if row != ['', '', '', '', '', '', '', '', '']:
                rows.append(row)
    # print(rows)
    for row_index in range(len(rows)):
        # do a traditional for loop so that the next row can be found
        row = rows[row_index]

        name = re.match(NAME_FORMAT, row[0])

        if name:
            # If a student row

            full_name = f"{name.group(2)} {name.group(1)}"
            arc = re.search(ARC_CLASS_FORMAT, row[0]).group(0)
            grade = int(re.match(r"\d+", arc).group(0))

            student = {
                'first_name': name.group(2),
                'last_name': name.group(1),
                'full_name': full_name,
                'arc': arc,
                'recipient_id': f"{full_name} [{arc}]",
                'grade': grade
            }

            get_periods(student, rows, row_index)
            add_person(people, student)
        else:
            # Perhaps it's a teacher - try again with teacher format
            name = re.match(TEACHER_NAME_FORMAT, row[0])

            if name:
                full_name = f"{name.group(2)} {name.group(1)}"
                arc = "TEACHER"
                grade = 0

                teacher = {
                    'first_name': name.group(2),
                    'last_name': name.group(1),
                    'full_name': full_name,
                    'arc': arc,
                    'recipient_id': f"{full_name} [{arc}]",
                    'grade': grade
                }

                get_periods(teacher, rows, row_index)
                add_person(people, teacher)

    return people


def load_csvs_in_folder(folder_dir: str):
    from glob import glob
    for file_name in glob(f"{folder_dir}/*.csv"):
        with open(file_name) as file:
            yield csv.reader(file)


def main():
    from constants import DirectoryLocations
    files = load_csvs_in_folder(DirectoryLocations.TIMETABLES_INPUT)
    students = get_recipient_classes(files)
    with open(f"{DirectoryLocations.DEV_STUFF}/people.csv", 'w') as file:
        writer = csv.DictWriter(file, fieldnames=[
            'id', 'full_name', 'first_name', 'last_name', 'arc', 'p1', 'p2', 'p3', 'p4'])
        writer.writeheader()
        writer.writerows(students)


if __name__ == "__main__":
    main()
