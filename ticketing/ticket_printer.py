import cairosvg
import io
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
from svglib.svglib import svg2rlg
from pypdf import PdfReader, PdfWriter, Transformation


if __name__ == "__main__":
    STUDENTS = {"Jeff Bezos [7A]": {"Name": "Jeff Bezos"}}
    from constants import DirectoryLocations, PICKUP_LINES, TEMPLATES
    random.seed(0)
else:
    from .constants import DirectoryLocations, STUDENTS, PICKUP_LINES, TEMPLATES


class TicketsToPDF:
    def __init__(self, tickets, pdf_output_path: str, pdf_name: str, padding: int = 0):
        self.tickets = tickets
        self.pdf_output_path = pdf_output_path  # supports str for filepath or BytesIO
        self.pdf_name = pdf_name
        self.background_pdf = None
        self.foreground_pdf = None          # only if vector messages is false
        self.message_pdfs = []              # only if vector messages is true

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

        # dimensions of canvas from signature pad in pixels
        self.CANVAS_WIDTH = 602
        self.CANVAS_HEIGHT = 358

        self.VECTOR_MESSAGES = True     # render ticket messages as svg files instead of being rasterized (slower)
        self.RATIO = 4                  # increases DPI by this ratio. only used if vector messages is false

        """Load Fonts"""
        pdfmetrics.registerFont(TTFont("Chasing Hearts", f'{DirectoryLocations.STATIC}/fonts/Chasing Hearts.ttf'))

        """Load Templates"""
        self.TEMPLATES = {}

        for template_name, template_info in TEMPLATES.items():
            template = svg2rlg(f"{DirectoryLocations.STATIC}/templates/{template_info['filename']}")
            scale_factor = min(1 - (self.PADDING * 2 / self.CELL_WIDTH), 1 - (self.PADDING * 2 / self.CELL_HEIGHT))
            template.setProperties({"hAlign": "CENTER", "vAlign": "MIDDLE", "renderScale": scale_factor})
            self.TEMPLATES[template_name] = template

        """Load Item Images"""
        self.ITEM_IMAGES = {}

        chocolate_image = svg2rlg(f'{DirectoryLocations.STATIC}/item_types/chocolate.svg')
        chocolate_image.setProperties({"renderScale": 0.033})
        self.ITEM_IMAGES["Chocolate"] = chocolate_image

        rose_image = svg2rlg(f'{DirectoryLocations.STATIC}/item_types/rose.svg')
        rose_image.setProperties({"renderScale": 0.043})
        self.ITEM_IMAGES["Rose"] = rose_image

        serenade_image = svg2rlg(f'{DirectoryLocations.STATIC}/item_types/serenade.svg')
        serenade_image.setProperties({"renderScale": 0.025})
        self.ITEM_IMAGES["Serenade"] = serenade_image

        special_serenade_image = svg2rlg(f'{DirectoryLocations.STATIC}/item_types/special_serenade.svg')
        special_serenade_image.setProperties({"renderScale": 0.09})
        self.ITEM_IMAGES["Special Serenade"] = special_serenade_image

        """Build PDF"""
        self.generate_background_pdf()
        self.generate_foreground_pdf()
        self.combine_pdfs()

    def combine_pdfs(self):
        pdf = PdfWriter()
        for index, page in enumerate(self.background_pdf.pages):
            if index % 2 == 0:
                page_num = index // 2
                if self.VECTOR_MESSAGES:
                    for message_index, message_pdf in enumerate(self.message_pdfs[page_num * self.NUM_CODES_PER_PAGE: (page_num + 1) * self.NUM_CODES_PER_PAGE]):
                        if message_pdf is None:
                            continue

                        message_index = message_index % self.NUM_CODES_PER_PAGE
                        message_page = PdfReader(message_pdf).pages[0]
                        transformation = Transformation()\
                            .translate(self.MARGIN * 1.5, self.MARGIN * 1.79)\
                            .translate((message_index % self.NUM_COLUMNS) * self.CELL_WIDTH + self.PADDING,
                                       self.TABLE_HEIGHT - ((message_index // 2 + 1) * self.CELL_HEIGHT) + self.PADDING)
                        page.merge_transformed_page(message_page, transformation)
                else:
                    page.merge_page(self.foreground_pdf.pages[page_num])
            page.compress_content_streams()
            pdf.add_page(page)

        if type(self.pdf_output_path) == str:
            with open(self.pdf_output_path, 'wb') as file:
                pdf.write(file)
        elif isinstance(self.pdf_output_path, io.BytesIO):
            pdf.write(self.pdf_output_path)
        else:
            print(f"[Ticket Printer] Error: unknown type of self.pdf_output_path {self.pdf_output_path}")

    def generate_foreground_pdf(self):
        foreground_pdf_stream = io.BytesIO()
        doc = SimpleDocTemplate(foreground_pdf_stream, pageSize=A4,
                                rightMargin=self.MARGIN, leftMargin=self.MARGIN,
                                topMargin=self.MARGIN, bottomMargin=self.MARGIN)

        # split the list into pages
        pages = []
        for page_index, tickets in enumerate(self.split_list(self.tickets, self.NUM_CODES_PER_PAGE)):
            """Front of tickets"""
            # split the list again into rows
            data = self.split_list(self.create_images(tickets), self.NUM_COLUMNS)
            pages.append(self.create_table(data))
        doc.build(pages)

        self.foreground_pdf = PdfReader(foreground_pdf_stream)

    def generate_background_pdf(self):
        background_pdf_stream = io.BytesIO()
        doc = SimpleDocTemplate(background_pdf_stream, pageSize=A4,
                                rightMargin=self.MARGIN, leftMargin=self.MARGIN,
                                topMargin=self.MARGIN, bottomMargin=self.MARGIN)

        # split the list into pages
        pages = []
        for page_index, tickets in enumerate(self.split_list(self.tickets, self.NUM_CODES_PER_PAGE)):
            """Front of tickets"""
            # split the list again into rows
            data = self.split_list(self.create_templates(tickets), self.NUM_COLUMNS)
            pages.append(self.create_table(data))

            pages.append(PageBreak())

            """Back of tickets"""
            if self.HORIZONTAL_FLIP:
                data = self.split_list(self.create_delivery_info(tickets, page_index), self.NUM_COLUMNS, reverse=True)
            else:
                data = self.split_list(self.create_delivery_info(tickets, page_index), self.NUM_COLUMNS)
            pages.append(self.create_table(data))
        doc.build(pages)

        self.background_pdf = PdfReader(background_pdf_stream)

    def create_images(self, tickets: list) -> list:
        images = []
        for ticket in tickets:
            # resize the canvas
            with open(f"{DirectoryLocations().REDEEMED_TICKETS}/{ticket.pk}.svg") as file:
                xml_file = etree.parse(file).getroot()
                # change the view box to the dimensions of the canvas
                xml_file.set('viewBox', f'0 0 {self.CANVAS_WIDTH} {self.CANVAS_HEIGHT}')

            # check if message is blank
            if float(xml_file.get('width')) > 0 and float(xml_file.get('height')):
                if self.VECTOR_MESSAGES:
                    xml_file.set('width', str(self.CELL_WIDTH))
                    xml_file.set('height', str(self.CELL_HEIGHT))

                    img_bytes = io.BytesIO(cairosvg.svg2pdf(
                        bytestring=etree.tostring(xml_file), write_to=None,
                        output_width=4 / 3 * (self.CELL_WIDTH - 2 * self.PADDING),
                        output_height=4 / 3 * (self.CELL_HEIGHT - 2 * self.PADDING)))
                    # padding shrinks message at 4/3x faster rate than back of tickets

                    self.message_pdfs.append(img_bytes)

                    image = ""   # just return a blank image and add it later by merging pdfs
                else:
                    img_bytes = io.BytesIO(cairosvg.svg2png(
                        bytestring=etree.tostring(xml_file), write_to=None,
                        output_width=self.CANVAS_WIDTH * self.RATIO, output_height=self.CANVAS_HEIGHT * self.RATIO))

                    image = Image(img_bytes)
                    self.scale_image(image, self.CELL_WIDTH - 2 * self.PADDING, self.CELL_HEIGHT - 2 * self.PADDING)
            else:
                print(f"[Ticket Printer] Warning: Ticket {ticket.pk} is blank.")
                image = ""

                # add a placeholder
                if self.VECTOR_MESSAGES:
                    self.message_pdfs.append(None)

            images.append(image)

        return images

    def create_templates(self, tickets: list) -> list:
        images = []
        for ticket in tickets:
            if ticket.template == "Blank":
                image = ""
            else:
                image = self.TEMPLATES[ticket.template]
            images.append(image)
        return images

    def create_delivery_info(self, tickets: list, page_index: int) -> list:
        stylesheet = getSampleStyleSheet()
        default_style = ParagraphStyle(name="Default", parent=stylesheet['Normal'], fontSize=10, leading=11,
                                       fontName="Chasing Hearts")
        centre_align = ParagraphStyle(name="Center", parent=default_style, alignment=1)
        centre_align_small = ParagraphStyle(name="Center Small", parent=default_style, alignment=1, fontSize=8,
                                            leading=9)
        large_style = ParagraphStyle(name="Large", parent=default_style, alignment=1,
                                     fontSize=max(12, round(16 - self.PADDING / 3)),
                                     leading=max(13, round(18 - self.PADDING / 3)))

        ticket_backs = []
        for index, ticket in enumerate(tickets):
            """Top Left: Periods"""
            period_classes = [f"P1: {ticket.p1}", f"P2: {ticket.p2}", f"P3: {ticket.p3}", f"P4: {ticket.p4}"]
            period_classes[ticket.period - 1] += " *"   # this is a heart in the Chasing Hearts font
            periods = Paragraph("<br/>".join(period_classes), default_style)
            periods = self.create_div([[periods]],
                                      ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                      ('LEFTPADDING', (0, 0), (-1, -1), 6 + self.PADDING),
                                      colWidths=self.CELL_WIDTH / 4)

            """Bottom Right: Item Type (including image)"""
            if ticket.item_type in self.ITEM_IMAGES:
                item_type_image = self.ITEM_IMAGES[ticket.item_type]
            else:
                raise KeyError("Unknown item type")

            if ticket.item_type == "Special Serenade":
                item_type = Paragraph(ticket.item_type, centre_align_small)
            else:
                item_type = Paragraph(ticket.item_type, centre_align)
            item_type_table = self.create_div([[item_type_image], [item_type]], colWidths=self.CELL_WIDTH / 5)

            """Bottom Left: Delivery Group and Ticket Number"""
            ticket_number = Paragraph(f"{self.pdf_name}: {page_index * self.NUM_CODES_PER_PAGE + index + 1}", default_style)

            bottom_row = self.create_div([[ticket_number, item_type_table]],
                                         ('LEFTPADDING', (0, 0), (-1, -1), 6 + self.PADDING),
                                         ('RIGHTPADDING', (0, 0), (-1, -1), 3 + self.PADDING),
                                         ('BOTTOMPADDING', (-1, 0), (-1, -1), 3),
                                         ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                                         ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                                         ('VALIGN', (0, 0), (1, -1), 'BOTTOM'),
                                         colWidths=self.CELL_WIDTH / 2)

            """Middle: Recipient Name"""
            recipient_name_and_pickup = Paragraph(f"* Hey {STUDENTS[ticket.recipient_id]['Name']} *<br/>"
                                                  f"{random.choice(PICKUP_LINES)}", large_style)
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

    def split_list(self, ticket_codes: list, split_size: int, reverse: bool = False) -> list:
        # splits a list into smaller lists of a given size
        list_split_by_size = []
        for i in range(0, len(ticket_codes), split_size):
            list_slice = ticket_codes[i: i + split_size]

            if split_size == self.NUM_COLUMNS and (len(list_slice) % self.NUM_COLUMNS) != 0:
                # if split size equals NUM_COLUMNS, it's splitting into rows, otherwise it's into pages
                # not enough tickets to fill row, add placeholders to ensure front/back side alignment
                list_slice = [*list_slice, *[""] * (self.NUM_COLUMNS - (len(list_slice) % self.NUM_COLUMNS))]

            if reverse:
                list_slice = list(reversed(list_slice))

            list_split_by_size.append(list_slice)
        return list_split_by_size

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
        def __init__(self, pk):
            self.pk = pk
            self.template = random.choice(["Blank", "Classic Template"])

            self.item_type = random.choice(["Chocolate", "Rose", "Serenade", "Special Serenade"])
            self.recipient_id = "Jeff Bezos [7A]"

            self.period = 2
            self.p1 = "F101"
            self.p2 = "F202"
            self.p3 = "F303"
            self.p4 = "F404"

    tickets = []
    for index, file in enumerate(glob(f"{DirectoryLocations().REDEEMED_TICKETS}/*.svg")):
        if index >= 50:
            break
        tickets.append(Ticket(file.split("/")[-1].split(".svg")[0]))

    TicketsToPDF(tickets, 'export.pdf', 'S1', padding=0)


if __name__ == "__main__":
    main()
