import csv
from .constants import FileNames


def get_students() -> dict:
    """This should be a dict with ID as key, and another dict as value which contains info like name and ARC class
    {'872658275W': {'ID': '872658275W', 'Name': 'Gamer', 'ARC': '7A',
    'P1': 'E3.04', 'P2': 'E2.07', 'P3': 'F102', 'P4': 'A2.08'}}"""
    students = {}
    try:
        with open(FileNames.PEOPLE) as file:
            reader = csv.DictReader(file)
            for row in reader:
                students[row['ID']] = row
        return students
    except FileNotFoundError:
        return students


STUDENTS = get_students()
