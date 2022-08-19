import csv
import re
from .constants import FileNames

"""Settings"""
name_half = r"([a-zA-Z\s\'\(\)-]+)"
name_format = fr"{name_half},\s{name_half},"
room_format = r"[A-Z][G\d].?\d\d\Z|LIB[A-D]\Z|OVAL[A-D]\Z|OVLJ|POOL"
arc_class_format = r"([7-9]|10|11|12)[A-Z]"
period_columns = 1, 3, 5, 7

students = []

for file_name in glob(f"{Folders.timetables}*.csv"):
    with open(file_name) as file:
        reader = csv.reader(file)
        rows = [row for row in reader if row != ['', '', '', '', '', '', '', '', '']]

        for row_index in range(len(rows)):
            # do a traditional for loop so that the next row can be found
            row = rows[row_index]

            name = re.match(name_format, row[0])
            if name:
                student = {}

                student_name = f"{name.group(2)} {name.group(1)}"
                arc_class = re.search(arc_class_format, row[0]).group(0)
                student_id = f"{student_name} [{arc_class}]"

                student['StudentName'] = student_id

                # print(student_name, arc_class)
                for period, period_column in enumerate(period_columns):
                    period = period + 1
                    room = re.search(room_format, row[period_column])
                    if room:
                        student[f"P{period}"] = room.group(0)
                    else:
                        # print("NO CLASS", row)
                        student[f"P{period}"] = "NONE"
                        # if a person's class got split across two rows, try to find the class in the next row
                        next_row = rows[row_index + 1]
                        if next_row[0] == "":
                            # checks if the next row is the second half of this row and not a new person
                            room = re.search(room_format, next_row[period_column])
                            if room:
                                student[f"P{period}"] = room.group(0)
                                # print(room.group(0))
                            else:
                                # print("NO ROOM")
                                pass

                students.append(student)
                print(student)
