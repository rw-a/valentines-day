import cairosvg
import io
import PIL
import random
from lxml import etree
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak, Paragraph
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus.tables import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

if __name__ == "__main__":
    STUDENTS = {"89273498237A": {"Name": "Jeff Bezos"}}
    from constants import DirectoryLocations
else:
    from .constants import DirectoryLocations
    from .class_lookup import STUDENTS


class TicketsToPDF:
    def __init__(self, tickets, pdf_output_path: str, pdf_name: str, padding: int = 0):
        self.tickets = tickets
        self.pdf_output_path = pdf_output_path
        self.pdf_name = pdf_name

        """Constants and Settings"""
        # flip the order of the cells in the back page
        # required for double-sided printing of tickets flipped along the long edge
        self.HORIZONTAL_FLIP = True

        self.NUM_COLUMNS = 2
        self.NUM_ROWS = 5
        self.NUM_CODES_PER_PAGE = self.NUM_COLUMNS * self.NUM_ROWS

        self.MARGIN = 1 * cm            # an additional 0.5cm will be added to the table
        self.PADDING = padding          # the padding for each cell in the table
        self.PAGE_WIDTH, self.PAGE_HEIGHT = A4

        self.TABLE_WIDTH = self.PAGE_WIDTH - 2 * self.MARGIN - cm
        self.TABLE_HEIGHT = self.PAGE_HEIGHT - 2 * self.MARGIN - cm
        self.CELL_WIDTH = self.TABLE_WIDTH / self.NUM_COLUMNS
        self.CELL_HEIGHT = self.TABLE_HEIGHT / self.NUM_ROWS

        self.ITEM_TYPE_IMAGE_SIZE = 20      # in pts

        # dimensions of canvas from signature pad in pixels
        self.CANVAS_WIDTH = 602
        self.CANVAS_HEIGHT = 358
        self.RATIO = 2      # increases DPI by this ratio

        """Pickup Lines"""
        with open(f'{DirectoryLocations.STATIC}/pickup_lines.txt') as file:
            self.PICKUP_LINES = [line.replace("\n", "") for line in file]

        """Templates"""
        pdfmetrics.registerFont(TTFont('VDay', f'{DirectoryLocations.STATIC}/fonts/Chasing Hearts.ttf'))

        self.CLASSIC_TEMPLATE = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
            url=f"{DirectoryLocations.STATIC}/templates/classic_template.svg", write_to=None,
            output_width=self.CANVAS_WIDTH * self.RATIO, output_height=self.CANVAS_HEIGHT * self.RATIO)))

        self.generate_pdf()

    def generate_pdf(self):
        doc = SimpleDocTemplate(self.pdf_output_path, pageSize=A4,
                                rightMargin=self.MARGIN, leftMargin=self.MARGIN,
                                topMargin=self.MARGIN, bottomMargin=self.MARGIN)

        # split the list into pages
        pages = []
        for page_index, tickets in enumerate(self.split_list(self.tickets, self.NUM_CODES_PER_PAGE)):
            """Front of tickets"""
            # split the list again into rows
            data = self.split_list(self.create_images(tickets), self.NUM_COLUMNS)
            pages.append(self.create_table(data))

            pages.append(PageBreak())

            """Back of tickets"""
            if self.HORIZONTAL_FLIP:
                data = self.split_list(self.create_delivery_info(tickets, page_index), self.NUM_COLUMNS, reverse=True)
            else:
                data = self.split_list(self.create_delivery_info(tickets, page_index), self.NUM_COLUMNS)
            pages.append(self.create_table(data))
        doc.build(pages)

    def create_images(self, tickets: list) -> list:
        images = []
        for ticket in tickets:
            # resize the canvas
            with open(f"{DirectoryLocations().REDEEMED_TICKETS}/{ticket.pk}.svg") as file:
                xml_file = etree.parse(file).getroot()
                # change the view box to the dimensions of the canvas
                xml_file.set('viewBox', f'0 0 {self.CANVAS_WIDTH} {self.CANVAS_HEIGHT}')

            # add the template if required
            if ticket.template > 0:
                handwritten_image = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
                    bytestring=etree.tostring(xml_file), write_to=None,
                    output_width=self.CANVAS_WIDTH * self.RATIO, output_height=self.CANVAS_HEIGHT * self.RATIO)))
                combined_image = PIL.Image.new(
                    'RGBA', (handwritten_image.width, handwritten_image.height), (255, 255, 255, 0))

                if ticket.template == 1:
                    combined_image.alpha_composite(self.CLASSIC_TEMPLATE)
                else:
                    raise KeyError(f"Template number {ticket.template} does not exist.")

                combined_image.alpha_composite(handwritten_image)

                # save as bytes
                img_bytes = io.BytesIO()
                combined_image.save(img_bytes, format='PNG')
            else:
                img_bytes = io.BytesIO(cairosvg.svg2png(bytestring=etree.tostring(xml_file), write_to=None))

            image = Image(img_bytes)
            self.scale_image(image, self.CELL_WIDTH - 2 * self.PADDING, self.CELL_HEIGHT - 2 * self.PADDING)

            images.append(image)
        return images

    def create_delivery_info(self, tickets: list, page_index: int) -> list:
        stylesheet = getSampleStyleSheet()
        default_style = ParagraphStyle(name="Default", parent=stylesheet['Normal'], fontSize=10, leading=11,
                                       fontName="VDay")
        left_align_small = ParagraphStyle(name="Left Small", parent=default_style, fontSize=7, leading=8)
        centre_align = ParagraphStyle(name="Center", parent=default_style, alignment=1)
        centre_align_small = ParagraphStyle(name="Center Small", parent=default_style, alignment=1, fontSize=8, leading=9)
        # right_align = ParagraphStyle(name="Right", parent=default_style, alignment=2)
        large_style = ParagraphStyle(name="Large", parent=default_style, alignment=1,
                                     fontSize=max(12, round(16 - self.PADDING / 3)),
                                     leading=max(13, round(18 - self.PADDING / 3)))

        ticket_backs = []
        for index, ticket in enumerate(tickets):
            """Top Left: Periods"""
            period_classes = [f"P1: {ticket.p1}", f"P2: {ticket.p2}", f"P3: {ticket.p3}", f"P4: {ticket.p4}"]
            period_classes[ticket.period - 1] += " *"
            periods = Paragraph("<br/>".join(period_classes), default_style)
            periods = self.create_div([[periods]],
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('LEFTPADDING', (0, 0), (-1, -1), 3 + self.PADDING),
                                      colWidths=self.CELL_WIDTH / 4)

            """Bottom Right: Item Type (including image)"""
            if ticket.item_type == "Chocolate":
                item_type_image = self.scale_image(Image(f'{DirectoryLocations.STATIC}/item_types/chocolate.png'),
                                                   self.ITEM_TYPE_IMAGE_SIZE, self.ITEM_TYPE_IMAGE_SIZE)
            elif ticket.item_type == "Rose":
                item_type_image = self.scale_image(Image(f'{DirectoryLocations.STATIC}/item_types/rose.png'),
                                                   self.ITEM_TYPE_IMAGE_SIZE, self.ITEM_TYPE_IMAGE_SIZE)
            elif ticket.item_type == "Serenade":
                item_type_image = self.scale_image(Image(f'{DirectoryLocations.STATIC}/item_types/serenade.png'),
                                                   self.ITEM_TYPE_IMAGE_SIZE, self.ITEM_TYPE_IMAGE_SIZE)
            elif ticket.item_type == "Special Serenade":
                item_type_image = self.scale_image(Image(f'{DirectoryLocations.STATIC}/item_types/special_serenade.png'),
                                                   self.ITEM_TYPE_IMAGE_SIZE, self.ITEM_TYPE_IMAGE_SIZE)
            else:
                raise KeyError("Unknown item type")
            if ticket.item_type == "Special Serenade":
                item_type = Paragraph(ticket.item_type, centre_align_small)
            else:
                item_type = Paragraph(ticket.item_type, centre_align)
            item_type_table = self.create_div([[item_type_image], [item_type]], colWidths=self.CELL_WIDTH / 5)

            """Bottom Left: Delivery Group and Ticket Number"""
            ticket_number = Paragraph(f"{self.pdf_name}: {page_index * self.NUM_CODES_PER_PAGE + index + 1}", left_align_small)

            bottom_row = self.create_div([[ticket_number, item_type_table]],
                                         ('LEFTPADDING', (0, 0), (-1, -1), 3 + self.PADDING),
                                         ('RIGHTPADDING', (0, 0), (-1, -1), 3 + self.PADDING),
                                         ('BOTTOMPADDING', (-1, 0), (-1, -1), 3),
                                         ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                                         ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                                         ('VALIGN', (0, 0), (1, -1), 'BOTTOM'),
                                         colWidths=self.CELL_WIDTH / 2)

            """Middle: Recipient Name"""
            recipient_name_and_pickup = Paragraph(f"* Hey {STUDENTS[ticket.recipient_id]['Name']} *<br/>"
                                                  f"{random.choice(self.PICKUP_LINES)}", large_style)
            recipient_name_and_pickup = self.create_div([[recipient_name_and_pickup]],
                                                        ('LEFTPADDING', (0, 0), (-1, -1), 5 + self.PADDING),
                                                        ('RIGHTPADDING', (0, 0), (-1, -1), 5 + self.PADDING),
                                                        colWidths=self.CELL_WIDTH)

            vertically_separated_table = self.create_div([[periods], [recipient_name_and_pickup], [bottom_row]],
                                                         ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                                         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                                         ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
                                                         ('VALIGN', (0, -1), (-1, -1), 'BOTTOM'),
                                                         ('BOTTOMPADDING', (0, 0), (-1, -1), 3 + self.PADDING),
                                                         ('TOPPADDING', (0, 0), (-1, -1), 3 + self.PADDING),
                                                         ('LEFTPADDING', (0, 0), (-1, -1), 3),
                                                         ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                                                         rowHeights=[self.CELL_HEIGHT * 0.3,
                                                                     self.CELL_HEIGHT * 0.4,
                                                                     self.CELL_HEIGHT * 0.3])

            ticket_backs.append(vertically_separated_table)
        return ticket_backs

    @staticmethod
    def split_list(ticket_codes: list, split_size: int, reverse: bool = False) -> list:
        # splits a list into smaller lists of a given size
        if reverse:
            list_split_by_size = []
            for i in range(0, len(ticket_codes), split_size):
                list_slice = ticket_codes[i: i + split_size]
                if split_size == 2 and len(list_slice) < split_size:
                    # if an odd number of pages, add a placeholder to ensure front/back side alignment
                    list_slice_reversed = ["", *list_slice]
                else:
                    list_slice_reversed = list(reversed(list_slice))
                list_split_by_size.append(list_slice_reversed)
            return list_split_by_size
        else:
            return [ticket_codes[i: i + split_size] for i in range(0, len(ticket_codes), split_size)]

    @staticmethod
    def scale_image(image: Image, width: float, height: float = None) -> Image:
        # scale image to desired dimensions (in pts)
        # scale using the smallest amount (out of width or height) so that it fits while preserving aspect ratio
        if height is None:
            height = width
        scale_width = width / image.drawWidth
        scale_height = height / image.drawHeight
        scale = min(scale_width, scale_height)
        image.drawWidth *= scale
        image.drawHeight *= scale
        return image

    def create_table(self, data: list, *table_styles) -> Table:
        table = Table(data, colWidths=self.CELL_WIDTH, rowHeights=self.CELL_HEIGHT)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            *table_styles
        ]))
        return table

    @staticmethod
    def create_div(data: list, *table_styles, **kwargs) -> Table:
        table = Table(data, **kwargs)
        table.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                # ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                *table_styles
            ]))
        return table


def main():
    from glob import glob

    class Ticket:
        def __init__(self, pk, template: int):
            self.pk = pk
            self.template = template

            self.item_type = random.choice(["Chocolate", "Rose", "Serenade", "Special Serenade"])
            self.recipient_id = "89273498237A"

            self.period = 2
            self.p1 = "F101"
            self.p2 = "F202"
            self.p3 = "F303"
            self.p4 = "F404"

    # tickets = [Ticket(file.split("/")[-1].split(".svg")[0], 1) for file in glob(f"{DirectoryLocations().REDEEMED_TICKETS}/*.svg")]
    tickets = []
    for index, file in enumerate(glob(f"{DirectoryLocations().REDEEMED_TICKETS}/*.svg")):
        if index >= 100:
            break
        tickets.append(Ticket(file.split("/")[-1].split(".svg")[0], 1))

    TicketsToPDF(tickets, 'export.pdf', 'S1')


if __name__ == "__main__":
    main()
