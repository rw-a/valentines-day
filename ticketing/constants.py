"""Settings Files"""
import os
import csv
import json


class DirectoryLocations:
    """Directory Locations"""
    STATIC = "ticketing/static"                 # the folder containing all the static assets
    GENERATED_TICKET_CODES = "generated_codes"  # the folder containing filled PDFs of ticket codes
    REDEEMED_TICKETS = "redeemed_tickets"       # the folder containing the handwritten messages of redeemed tickets
    SORTED_TICKETS = "sorted_tickets"           # the folder containing the PDFs of the tickets to print
    TIMETABLES = "timetables"                   # the folder containing the CSV with all the people data
    TIMETABLES_INPUT = f"{TIMETABLES}/uploaded_timetables"  # the folder containing the timetable CSVs of each grade

    """All methods need to end with __ or else dir(self) will think it's an attribute"""
    def verify_dirs__(self):
        # verifies that every directory listed in DirectoryLocations exists, and creates them if it doesn't
        for attribute in dir(self):
            if not attribute.endswith('__'):   # removes random other attributes
                directory = getattr(self, attribute)
                if not os.path.exists(directory):
                    print(f"{directory} folder doesn't exist yet. Creating {directory}...")
                    os.mkdir(directory)


class FileNames:
    # format: ID, Name, ARC_Class, P1_class, P2_class, P3_class, P4_class
    PEOPLE = f"{DirectoryLocations.TIMETABLES}/people.csv"

    """All methods need to end with __ or else dir(self) will think it's an attribute"""
    def verify_files__(self):
        for attribute in dir(self):
            if not attribute.endswith('__'):      # removes random other attributes
                directory = getattr(self, attribute)
                without_file_type = directory.split('.')[0]
                if without_file_type.isupper():
                    continue
                if not os.path.exists(directory):
                    raise Exception(f"{directory} is missing.")


class MaxLengths:
    """WARNING: Changing these values will require migrating the SQL Database afterwards"""
    TICKET_CODE = 10       # the length of the ticket codes (exact value, not just max)


"""Verify that the files required exist"""
DirectoryLocations().verify_dirs__()
# FileNames().verify_files__()


"""Commonly loaded static files"""

"""
Students
This should be a dict with ID as key, and another dict as value which contains info like name and ARC class
{'Gamer [7A]': {'ID': 'Gamer [7A]', 'Name': 'Gamer', 'ARC': '7A',
'P1': 'E3.04', 'P2': 'E2.07', 'P3': 'F102', 'P4': 'A2.08'}}
"""
STUDENTS = {}
try:
    with open(FileNames.PEOPLE) as file:
        reader = csv.DictReader(file)
        for row in reader:
            STUDENTS[row['ID']] = row
except FileNotFoundError:
    print(f"ERROR: {FileNames.PEOPLE} not found.")

STUDENTS_LIST = list(STUDENTS.keys())

"""Pickup Lines"""
with open(f'{DirectoryLocations.STATIC}/pickup_lines.txt') as file:
    PICKUP_LINES = [line.replace("\n", "") for line in file]

"""Templates"""
with open(f"{DirectoryLocations.STATIC}/templates/templates.json") as file:
    TEMPLATES = json.load(file)
