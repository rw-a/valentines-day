"""Settings Files"""
import os
import json


class DirectoryLocations:
    """Directory Locations"""
    STATIC = "ticketing/static"                 # the folder containing all the static assets
    GENERATED_TICKET_CODES = "generated_codes"  # the folder containing filled PDFs of ticket codes
    REDEEMED_TICKETS = "redeemed_tickets"       # the folder containing the handwritten messages of redeemed tickets
    SORTED_TICKETS = "sorted_tickets"           # the folder containing the PDFs of the tickets to print
    TIMETABLES = "timetables"                   # the folder containing the CSV with all the people data
    TIMETABLES_INPUT = f"{TIMETABLES}/uploaded_timetables"  # the folder containing the timetable CSVs of each grade
    DEV_STUFF = "dev"                           # the folder containing files for development/testing

    """All methods need to end with __ or else dir(self) will think it's an attribute"""
    def verify_dirs__(self):
        # verifies that every directory listed in DirectoryLocations exists, and creates them if it doesn't
        for attribute in dir(self):
            if not attribute.endswith('__'):   # removes random other attributes
                directory = getattr(self, attribute)
                if not os.path.exists(directory):
                    print(f"{directory} folder doesn't exist yet. Creating {directory}...")
                    os.mkdir(directory)


class MaxLengths:
    """WARNING: Changing these values will require migrating the SQL Database afterwards"""
    TICKET_CODE = 10       # the length of the ticket codes (exact value, not just max)


"""Verify that the files required exist"""
DirectoryLocations().verify_dirs__()


"""Commonly loaded static files"""

# Pick-up lines
with open(f'{DirectoryLocations.STATIC}/pickup_lines.txt') as file:
    PICKUP_LINES = [line.replace("\n", "") for line in file]

# Ticket templates
with open(f"{DirectoryLocations.STATIC}/templates/templates.json") as file:
    TEMPLATES = json.load(file)

# Ticket fonts
with open(f"{DirectoryLocations.STATIC}/fonts/fonts.json") as file:
    FONTS = json.load(file)
