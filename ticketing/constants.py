"""Settings Files"""
import os
import csv


class DirectoryLocations:
    """Directory Locations"""
    STATIC = "ticketing/static"     # the static folder
    GENERATED_TICKET_CODES = "generated_codes"  # the folder containing filled PDFs of ticket codes
    REDEEMED_TICKETS = "redeemed_tickets"       # the folder containing the handwritten messages of redeemed tickets
    SORTED_TICKETS = "sorted_tickets"     # the folder containing the PDFs of the tickets to print
    STUDENT_DATA = "student_data"
    TIMETABLES = f"{STUDENT_DATA}/timetables"  # the folder containing the timetable CSVs of each grade

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
    STUDENT_LIST = f"{DirectoryLocations.STUDENT_DATA}/student_list.csv"
    STUDENT_CLASSES = f"{DirectoryLocations.STUDENT_DATA}/student_classes.csv"

    # format: ID, Name, ARC_Class, P1_class, P2_class, P3_class, P4_class
    STUDENTS = f"{DirectoryLocations.STUDENT_DATA}/students.csv"

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
