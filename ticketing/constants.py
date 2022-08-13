"""Settings Files"""
import os


class DirectoryLocations:
    """Directory Locations"""
    STATIC = "ticketing/static"     # the static folder
    INPUTS = "INPUTS"           # the folder containing files that prefects should be able to easily modify
    GENERATED_TICKET_CODES = "generated_codes"  # the folder containing filled PDFs of ticket codes
    REDEEMED_TICKETS = "redeemed_tickets"       # the folder containing the handwritten messages of redeemed tickets
    SORTED_TICKETS = "sorted_tickets"     # the folder containing the PDFs of the tickets to print

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
    # input files (all_lowercase)
    STUDENT_LIST = f"{DirectoryLocations.INPUTS}/student_list.csv"           # format: ID, Name, ARC_Class
    STUDENT_CLASSES = f"{DirectoryLocations.INPUTS}/student_classes.csv"     # format: ID, P1_class, P2_class, P3_class, P4_class
    PICKUP_LINES = f"{DirectoryLocations.INPUTS}/pickup_lines.txt"

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

    # attributes of a Ticket
    TICKET_RECIPIENT_FIRST_NAME = 20    # 15 is the actual max but just to be safe
    TICKET_RECIPIENT_NICKNAME = 30
    TICKET_MESSAGE = 80
    TICKET_SENDER = 25


"""Verify that the files required exist"""
DirectoryLocations().verify_dirs__()
FileNames().verify_files__()
