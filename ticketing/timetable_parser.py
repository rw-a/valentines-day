import csv
import re

"""Settings"""
name_half = r"([a-zA-Z\s\'\(\)-]+)"
name_format = fr"{name_half},\s{name_half},"
room_format = r"[A-Z][G\d].?\d\d\Z|LIB[A-D]\Z|OVAL[A-D]\Z|OVLJ|POOL"
arc_class_format = r"([7-9]|10|11|12)[A-Z]"
period_columns = 1, 3, 5, 7


def get_student_classes(files):
    students = []

    rows = []
    for file in files:
        for row in file:
            if row != ['', '', '', '', '', '', '', '', '']:
                rows.append(row)

    for row_index in range(len(rows)):
        # do a traditional for loop so that the next row can be found
        row = rows[row_index]

        name = re.match(name_format, row[0])
        if name:
            student = {'First Name': name.group(2),
                       'Last Name': name.group(1),
                       'Name': f"{name.group(2)} {name.group(1)}",
                       'ARC': re.search(arc_class_format, row[0]).group(0)}
            student['ID'] = f"{student['Name']} [{student['ARC']}]"

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
        else:
            # print(row)
            pass
    return students


def load_csvs_in_folder(folder_dir: str):
    from glob import glob
    for file_name in glob(f"{folder_dir}/*.csv"):
        with open(file_name) as file:
            yield csv.reader(file)


def main():
    from constants import DirectoryLocations, FileNames
    files = load_csvs_in_folder(DirectoryLocations.TIMETABLES)
    students = get_student_classes(files)
    with open(FileNames.STUDENTS, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=['ID', 'Name', 'First Name', 'Last Name',
                                                  'ARC', 'P1', 'P2', 'P3', 'P4'])
        writer.writeheader()
        writer.writerows(students)


if __name__ == "__main__":
    main()
