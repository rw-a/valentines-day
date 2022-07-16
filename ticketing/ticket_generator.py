import cairosvg
import io
import PIL
from lxml import etree
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Image
from reportlab.platypus.tables import Table, TableStyle
from constants import DirectoryLocations


class TicketsToPDF:
    def __init__(self, tickets: list,  pdf_output_name: str):
        self.tickets = tickets
        self.pdf_output_name = pdf_output_name

        """Constants"""
        self.NUM_COLUMNS = 2
        self.NUM_ROWS = 5
        self.NUM_CODES_PER_PAGE = self.NUM_COLUMNS * self.NUM_ROWS

        self.MARGIN = 1 * cm      # an additional 0.5cm will be added to the table
        self.PADDING = 0          # the padding for each cell in the table
        self.WIDTH, self.HEIGHT = A4

        # dimensions of canvas from signature pad in pixels
        self.CELL_WIDTH = 602
        self.CELL_HEIGHT = 358
        self.RATIO = 2      # increases DPI by this ratio

        self.generate_pdf()

    def generate_pdf(self):
        doc = SimpleDocTemplate(self.pdf_output_name, pageSize=A4,
                                rightMargin=self.MARGIN, leftMargin=self.MARGIN,
                                topMargin=self.MARGIN, bottomMargin=self.MARGIN)

        # split the list into pages
        pages = []
        for tickets in self.split_list(self.tickets, self.NUM_CODES_PER_PAGE):     # for each page of codes
            # calculate table dimensions
            width = self.WIDTH - 2 * self.MARGIN - cm
            height = self.HEIGHT - 2 * self.MARGIN - cm
            col_width = width / self.NUM_COLUMNS
            row_height = height / self.NUM_ROWS

            # split the list again into rows
            data = self.split_list(self.create_images(
                tickets, col_width - 2 * self.PADDING, row_height - 2 * self.PADDING), self.NUM_COLUMNS)

            table = Table(data, colWidths=col_width, rowHeights=row_height)
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
            ]))
            pages.append(table)
        doc.build(pages)

    def create_images(self, tickets: list, width: float, height: float):
        # get templates
        classic_template = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
            url="ticketing/static/classic_template.svg", write_to=None,
            output_width=self.CELL_WIDTH * self.RATIO, output_height=self.CELL_HEIGHT * self.RATIO)))

        images = []
        for ticket in tickets:
            # resize the canvas
            with open(f"{DirectoryLocations().REDEEMED_TICKETS}/{ticket}.svg") as file:
                xml_file = etree.parse(file).getroot()
                # change the view box to the dimensions of the canvas
                xml_file.set('viewBox', f'0 0 {self.CELL_WIDTH} {self.CELL_HEIGHT}')

            # add the template if required
            if True:
                handwritten_image = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
                    bytestring=etree.tostring(xml_file), write_to=None,
                    output_width=self.CELL_WIDTH * self.RATIO, output_height=self.CELL_HEIGHT * self.RATIO)))
                combined_image = PIL.Image.new('RGBA', (handwritten_image.width, handwritten_image.height), (255, 255, 255, 0))
                combined_image.alpha_composite(handwritten_image)

                if True:
                    combined_image.alpha_composite(classic_template)

                # save as bytes
                img_bytes = io.BytesIO()
                combined_image.save(img_bytes, format='PNG')
            else:
                img_bytes = io.BytesIO(cairosvg.svg2png(bytestring=etree.tostring(xml_file), write_to=None))

            image = Image(img_bytes)
            scale_width = width / image.drawWidth
            scale_height = height / image.drawHeight
            scale = min(scale_width, scale_height)  # scales it so that the image always fits and aspect ratio the same
            image.drawWidth *= scale
            image.drawHeight *= scale

            images.append(image)
        return images

    @staticmethod
    def split_list(ticket_codes: list, split_size: int):
        # splits a list into smaller lists of a given size
        return [ticket_codes[i: i + split_size] for i in range(0, len(ticket_codes), split_size)]


def main():
    tickets = ["1", "2", "3", "4"]
    TicketsToPDF(tickets, 'export.pdf')


if __name__ == "__main__":
    main()
