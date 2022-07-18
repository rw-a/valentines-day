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
from constants import DirectoryLocations, FileNames
# from .ticket_sorter import TicketToSort


class TicketsToPDF:
    def __init__(self, tickets: list,  pdf_output_name: str):
        self.tickets = tickets
        self.pdf_output_name = pdf_output_name

        """Constants and Settings"""
        # flip the order of the cells in the back page
        # required for double-sided printing of tickets flipped along the long edge
        self.HORIZONTAL_FLIP = True

        self.NUM_COLUMNS = 2
        self.NUM_ROWS = 5
        self.NUM_CODES_PER_PAGE = self.NUM_COLUMNS * self.NUM_ROWS

        self.MARGIN = 1 * cm      # an additional 0.5cm will be added to the table
        self.PADDING = 0          # the padding for each cell in the table
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
        with open(FileNames.PICKUP_LINES) as file:
            self.PICKUP_LINES = [line.replace("\n", "") for line in file]

        """Templates"""
        pdfmetrics.registerFont(TTFont('VDay', f'{DirectoryLocations.STATIC}/font.ttf'))

        self.CLASSIC_TEMPLATE = PIL.Image.open(io.BytesIO(cairosvg.svg2png(
            url=f"{DirectoryLocations.STATIC}/templates/classic_template.svg", write_to=None,
            output_width=self.CANVAS_WIDTH * self.RATIO, output_height=self.CANVAS_HEIGHT * self.RATIO)))

        self.generate_pdf()

    def generate_pdf(self):
        doc = SimpleDocTemplate(self.pdf_output_name, pageSize=A4,
                                rightMargin=self.MARGIN, leftMargin=self.MARGIN,
                                topMargin=self.MARGIN, bottomMargin=self.MARGIN)

        # split the list into pages
        pages = []
        for tickets in self.split_list(self.tickets, self.NUM_CODES_PER_PAGE):     # for each page of codes
            """Front of tickets"""
            # split the list again into rows
            data = self.split_list(self.create_images(tickets), self.NUM_COLUMNS)
            pages.append(self.create_table(data))

            pages.append(PageBreak())

            """Back of tickets"""
            if self.HORIZONTAL_FLIP:
                data = self.split_list(self.create_delivery_info(tickets), self.NUM_COLUMNS, reverse=True)
            else:
                data = self.split_list(self.create_delivery_info(tickets), self.NUM_COLUMNS)
            pages.append(self.create_table(data))
        doc.build(pages)

    def create_images(self, tickets: list) -> list:
        images = []
        for ticket in tickets:
            # resize the canvas
            with open(f"{DirectoryLocations().REDEEMED_TICKETS}/{ticket.id}.svg") as file:
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

    def create_delivery_info(self, tickets: list) -> list:
        stylesheet = getSampleStyleSheet()
        default_style = ParagraphStyle(name="Default", parent=stylesheet['Normal'], fontSize=9, leading=10,
                                       fontName="VDay")
        centre_align = ParagraphStyle(name="Center", parent=default_style, alignment=1)
        right_align = ParagraphStyle(name="Right", parent=default_style, alignment=2)
        large_style = ParagraphStyle(name="Large", parent=default_style, alignment=1, fontSize=15, leading=17)

        ticket_backs = []
        for ticket in tickets:
            """Top Left: Periods"""
            p1 = f"<b>P1: {ticket.p1} |</b>" if ticket.is_p1 else f"P1: {ticket.p1}"
            p2 = f"<b>P2: {ticket.p2} |</b>" if ticket.is_p2 else f"P2: {ticket.p2}"
            p3 = f"<b>P3: {ticket.p3} |</b>" if ticket.is_p3 else f"P3: {ticket.p3}"
            p4 = f"<b>P4: {ticket.p4} |</b>" if ticket.is_p4 else f"P4: {ticket.p4}"
            periods = Paragraph(f"{p1}<br/>{p2}<br/>{p3}<br/>{p4}", default_style)

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
            item_type = Paragraph(ticket.item_type, centre_align)
            item_type_table = self.create_div([[item_type_image], [item_type]], colWidths=self.CELL_WIDTH / 5)

            """Top Side: Recipient Name"""
            recipient_name_and_pickup = Paragraph(f"* Hey {ticket.recipient_name} *<br/>"
                                                  f"{random.choice(self.PICKUP_LINES)}", large_style)

            vertically_separated_table = self.create_div([[periods], [recipient_name_and_pickup], [item_type_table]],
                                                         ('VALIGN', (0, 0), (0, -1), 'TOP'),
                                                         ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
                                                         ('VALIGN', (0, -1), (-1, -1), 'BOTTOM'),
                                                         rowHeights=[self.CELL_HEIGHT * 0.3,
                                                                     self.CELL_HEIGHT * 0.4,
                                                                     self.CELL_HEIGHT * 0.3])

            ticket_backs.append(vertically_separated_table)
        return ticket_backs

    @staticmethod
    def split_list(ticket_codes: list, split_size: int, reverse: bool = False) -> list:
        # splits a list into smaller lists of a given size
        if reverse:
            return [list(reversed(ticket_codes[i: i + split_size])) for i in range(0, len(ticket_codes), split_size)]
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
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
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
        def __init__(self, id, template: int):
            self.id = id
            self.template = template

            self.item_type = random.choice(["Chocolate", "Rose", "Serenade", "Special Serenade"])
            self.recipient_name = "Wade Haynes"

            self.p1 = "F101"
            self.p2 = "F202"
            self.p3 = "F303"
            self.p4 = "F404"

            # whether the algorithm has chosen this period. don't rename or else setattr() will break
            self.is_p1 = False
            self.is_p2 = True
            self.is_p3 = False
            self.is_p4 = False

    tickets = [Ticket(file.split("/")[-1].split(".svg")[0], 1) for file in glob(f"{DirectoryLocations().REDEEMED_TICKETS}/*.svg")]

    TicketsToPDF(tickets, 'export.pdf')


if __name__ == "__main__":
    main()
