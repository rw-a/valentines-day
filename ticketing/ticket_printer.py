from pdfrw import PdfReader, PdfWriter, PdfDict, PdfObject
# from .constants import FileNames
import re


class TickerPrinter:
    def __init__(self, tickets: list):
        """Constants"""
        self.ANNOT_KEY = '/Annots'
        self.ANNOT_FIELD_KEY = '/T'
        self.ANNOT_VAL_KEY = '/V'
        self.ANNOT_RECT_KEY = '/Rect'
        self.SUBTYPE_KEY = '/Subtype'
        self.WIDGET_SUBTYPE_KEY = '/Widget'

        """Options"""
        self.TICKETS_PER_PAGE = 6

        self.fields_odd = ['Name', 'P1', 'P2', 'P3', 'P4', 'IsP2', 'IsP3', 'IsP4', 'IsP1',
                           'Rose', 'Serenade', 'SpecialSerenade', 'Chocolate']
        self.fields_even = ['IWe would like to wish you', 'Happy Valentines Day', 'and say 1', 'and say 2', 'From']

        # PDF names
        # self.input_pdf_name = FileNames.TICKET_TEMPLATE
        # self.output_pdf_name = FileNames.TICKETS_PRINTED
        self.input_pdf_name = "pdf_templates/ticket_template.pdf"
        # self.input_pdf_name = "pdf_templates/Ticket Template Images Single Form.pdf"
        self.output_pdf_name = "OUTPUT.pdf"

        """Variables"""
        # note: these are tickets from ticket_sorter.py, not the SQL Ticket Models
        # it is assumed that these tickets are already sorted
        self.tickets = tickets

        """Methods"""
        self.fill_pdf()

    def fill_pdf(self):
        input_pdf = PdfReader(self.input_pdf_name)
        for ticket_number, ticket in enumerate(self.tickets):
            page = input_pdf.pages[ticket_number // self.TICKETS_PER_PAGE]
            ticket_number_in_page = ticket_number % self.TICKETS_PER_PAGE
            annotations = page[self.ANNOT_KEY]
            for annotation in annotations:
                if annotation[self.SUBTYPE_KEY] == self.WIDGET_SUBTYPE_KEY:
                    if annotation[self.ANNOT_FIELD_KEY]:
                        key = annotation[self.ANNOT_FIELD_KEY][1:-1]
                        key_number = re.search(r"_\d+", key).group(0)
                        print(key_number)
                        # write to the annotation
                        annotation.update(PdfDict(V='{}'.format("ASHG2340O0932")))
                        annotation.update(PdfDict(AP=''))

        input_pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfObject('true')))
        PdfWriter().write(self.output_pdf_name, input_pdf)


if __name__ == "__main__":
    TickerPrinter(["Hi", "Bye"])
