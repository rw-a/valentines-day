import csv
from .constants import FileNames


def get_students() -> dict:
    """This should be a dict with ID as key, and another dict as value which contains info like name and ARC class
    {"872658275W": {'Name': 'Gamer', 'ARC': '7A'}}"""
    students = {}
    with open(FileNames.STUDENT_LIST) as file:
        reader = csv.reader(file)
        for line in reader:
            students[line[0]] = {'Name': line[1], 'ARC': line[2]}
    return students


def get_classes_lookup() -> dict:
    """This should be a dict with ID as key and a list of classes as values
    {"129334477T": ["EG10", "I2.47", "F101", "A2.03"]}"""
    classes_lookup = {}
    with open(FileNames.STUDENT_CLASSES) as file:
        reader = csv.reader(file)
        for line in reader:
            """This part will need to be tweaked once the actual format is figured out"""
            student_id = line[0]
            classes = line[1:5]
            classes_lookup[student_id] = classes
    return classes_lookup


STUDENTS = get_students()
STUDENT_CLASSES = get_classes_lookup()
