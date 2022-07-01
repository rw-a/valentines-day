from pdfrw import PdfWriter, PdfReader, PdfDict, PdfObject, PdfString
import random
from .constants import FileNames


def split_dict(dictionary: dict, split_size: int):
    output = []
    keys = list(dictionary.keys())
    for i in range(0, len(keys), split_size):
        output.append([(k, dictionary[k]) for k in keys[i: i + split_size]])
    return output


def generate_codes(num_codes: int, code_length: int = 10):
    # generates a list of random codes
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    codes = []
    for i in range(num_codes):
        codes.append("".join(random.choices(characters, k=code_length)))
    return codes


class CodesToPDF:
    # generates PDFs out of a dictionary of codes
    def __init__(self, ticket_codes: dict, pdf_output_name: str,):
        # constants
        self.ANNOT_KEY = '/Annots'
        self.ANNOT_FIELD_KEY = '/T'
        self.ANNOT_VAL_KEY = '/V'
        self.ANNOT_RECT_KEY = '/Rect'
        self.SUBTYPE_KEY = '/Subtype'
        self.WIDGET_SUBTYPE_KEY = '/Widget'
        self.FONT = PdfString.encode('/Courier 0 Tf 0 g')   # this font will only appear if PDF opened with Acrobat

        self.CODES_PER_PAGE = 100    # pdf should ideally have enough pages for at least 3000 items
        self.COLUMNS_PER_ROW = 5    # how many columns are in the table

        self.ticket_codes = ticket_codes  # e.g. {'10HAJ4O420': 'Special Serenade'}
        self.pdf = PdfReader(FileNames.TICKET_CODE_TEMPLATE)
        self.pdf_output_name = pdf_output_name  # should end with .pdf

        self.fill_pdf()

    def fill_pdf(self):
        # splits the list into chunks based on CODES_PER_PAGE
        # note: returns a list with tuples instead of dict
        ticket_code_split = split_dict(self.ticket_codes, self.CODES_PER_PAGE)

        # check there's enough pages for every code
        if len(self.ticket_codes) > self.pdf.numPages * self.CODES_PER_PAGE:
            raise Exception('Not enough pages for every code.')

        page_index = 0
        for page in self.pdf.pages:
            # stop once there's enough pages for every code
            if page_index >= len(ticket_code_split):
                break

            items = ticket_code_split[page_index]

            # ensure not out of range by filling the rest of the page with empty stuff
            items.extend([("", "") for i in range(self.CODES_PER_PAGE - len(items))])

            item_index = 0
            code_or_item = 0    # 0 = code, 1 = item

            # go through every item and write it to page
            annotations = page[self.ANNOT_KEY]
            for annotation in annotations:
                if annotation[self.SUBTYPE_KEY] == self.WIDGET_SUBTYPE_KEY:
                    if annotation[self.ANNOT_FIELD_KEY]:
                        # change the font first (doesn't work for some reason)
                        annotation.update(PdfDict(DA=self.FONT))
                        # make annotation centred
                        annotation.update(PdfDict(Q=PdfObject(1)))
                        # write tha actual item
                        annotation.update(PdfDict(V='{}'.format(items[item_index][code_or_item]), AP=''))

                # keeps track of whether it is a code or an item
                item_index += 1
                if (item_index % self.COLUMNS_PER_ROW) == 0:
                    if code_or_item == 0:
                        code_or_item = 1
                        item_index -= self.COLUMNS_PER_ROW
                    else:
                        code_or_item = 0

                # once done with all items in page, stop
                if item_index > len(items):
                    break

            page_index += 1

        self.pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfObject('true')))
        PdfWriter().write(self.pdf_output_name, self.pdf)


"""For debugging/testing only"""


def random_item_type():
    # gets a random item type. should only be used for testing
    items = [
        'Chocolate',
        'Rose',
        'Serenade',
        'Special Serenade'
    ]
    return random.choice(items)


def generate_ticket_codes(num_tickets: int):
    # generates ticket with a code and an item type. should only be used for testing since items aren't random
    return {code: random_item_type() for code in generate_codes(num_tickets)}


def main():
    CodesToPDF(generate_ticket_codes(123), "Generated Codes.pdf")


if __name__ == "__main__":
    main()
