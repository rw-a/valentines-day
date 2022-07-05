import random
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus.tables import Table, TableStyle


class TicketsToPDF:
    def __init__(self, ticket_codes: list, item_type: str, pdf_output_name: str):
        self.ticket_codes = ticket_codes
        self.item_type = item_type
        self.pdf_output_name = pdf_output_name

        """Constants"""
        self.NUM_COLUMNS = 5
        self.NUM_ROWS = 20
        self.NUM_CODES_PER_PAGE = self.NUM_COLUMNS * self.NUM_ROWS

        self.MARGIN = 1 * cm
        self.WIDTH, self.HEIGHT = A4

        self.generate_pdf()

    def generate_pdf(self):
        doc = SimpleDocTemplate(self.pdf_output_name, pageSize=A4,
                                rightMargin=self.MARGIN, leftMargin=self.MARGIN,
                                topMargin=self.MARGIN, bottomMargin=self.MARGIN)

        # split the list into pages
        pages = []
        for codes in self.split_list(self.ticket_codes, self.NUM_CODES_PER_PAGE):     # for each page of codes
            # calculate table dimensions
            width = self.WIDTH - 2 * self.MARGIN - cm
            height = self.HEIGHT - 2 * self.MARGIN - cm
            col_width = width / self.NUM_COLUMNS
            row_height = height / self.NUM_ROWS

            # split the list again into rows
            data = self.split_list(self.add_itemtype_to_codes(codes), self.NUM_COLUMNS)

            table = Table(data, colWidths=col_width, rowHeights=row_height)
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
            ]))
            pages.append(table)
        doc.build(pages)

    def add_itemtype_to_codes(self, ticket_codes: list):
        return [f"{code}\n{self.item_type}" for code in ticket_codes]

    @staticmethod
    def split_list(ticket_codes: list, split_size: int):
        # splits a list into smaller lists of a given size
        return [ticket_codes[i: i + split_size] for i in range(0, len(ticket_codes), split_size)]


def main():
    tickets = []
    TicketsToPDF(tickets, 'export.pdf')


if __name__ == "__main__":
    main()